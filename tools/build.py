"""Primary product build: original ROM + adopted spec + translation assets -> patched ROM + IPS + report.

Every byte change is planned as an Expected Write (offset, expected source bytes, new bytes, writer),
verified against the immutable source before application, checked for overlap, and the final diff is
audited against the union of writes. The 8 MiB source is expanded to 16 MiB; all new data lives in the
expansion area so the source extent only changes at registered pointer/literal sites.

usage: python tools/build.py [--policy development|release] [--only-ids id,id,...]
"""
import argparse
import collections
import hashlib
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textcodec import CTRL_NAMES, load_glyph_table, text_to_bytes, tokenize  # noqa: E402
from bdffont import BdfFont, pack_glyph  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROMBASE = 0x08000000


def load_spec():
    return json.load(open(os.path.join(ROOT, "config", "build.json"), encoding="utf-8"))


class WritePlan:
    def __init__(self, src):
        self.src = src
        self.writes = []  # (offset, expected, new, writer)

    def add(self, offset, expected, new, writer):
        if len(expected) != len(new):
            raise ValueError("%s: width mismatch at %x" % (writer, offset))
        actual = self.src[offset:offset + len(expected)]
        if actual != expected:
            raise ValueError("%s: expected source bytes mismatch at %x: %s != %s" % (writer, offset, actual.hex(), expected.hex()))
        self.writes.append((offset, bytes(expected), bytes(new), writer))

    def verify_no_overlap(self):
        ivs = sorted((o, o + len(e), w) for o, e, n, w in self.writes)
        for (a0, a1, wa), (b0, b1, wb) in zip(ivs, ivs[1:]):
            if b0 < a1:
                raise ValueError("overlapping writers %s and %s at %x" % (wa, wb, b0))

    def apply(self, img):
        for o, e, n, w in self.writes:
            img[o:o + len(n)] = n
        return img


def plain_chars(text):
    """Characters in a translation target that need glyphs (control tokens and brace tokens removed)."""
    t = re.sub(r"<[A-Z0-9_]+(?::[0-9a-fA-F]*)?>", "", text)
    t = re.sub(r"\{[A-Za-z0-9?]+\}", "", t)
    return [c for c in t if c != "\n"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="development", choices=["development", "release"])
    ap.add_argument("--only-ids", default="")
    args = ap.parse_args()
    spec = load_spec()
    rom_path = os.path.join(ROOT, spec["source"]["path"])
    src = open(rom_path, "rb").read()
    sha = hashlib.sha256(src).hexdigest()
    if sha != spec["source"]["sha256"] or len(src) != spec["source"]["size"]:
        raise SystemExit("source ROM identity mismatch: %s %d" % (sha, len(src)))
    code2txt, txt2code = load_glyph_table()
    font = BdfFont(os.path.join(ROOT, spec["font"]["path"]))
    if font.sha256 != spec["font"]["sha256"]:
        raise SystemExit("font identity mismatch: %s" % font.sha256)

    # --- translation inputs ---
    index = json.load(open(os.path.join(ROOT, "assets", "translation", "index.json"), encoding="utf-8"))
    if index["source_sha256"] != sha:
        raise SystemExit("translation index extracted from a different source")
    only = set(args.only_ids.split(",")) if args.only_ids else None
    eligible_states = {"release": {"approved"}, "development": {"translated", "reviewed", "approved"}}[args.policy]
    selected = []
    skipped = collections.Counter()
    for seg in index["segments"]:
        data = json.load(open(os.path.join(ROOT, "assets", "translation", seg["file"]), encoding="utf-8"))
        for e in data["entries"]:
            if only is not None and e["id"] not in only:
                continue
            if e.get("target") and e.get("state") in eligible_states:
                selected.append(e)
            else:
                skipped[e.get("state", "untranslated")] += 1
    if args.policy == "release" and skipped:
        raise SystemExit("release policy: ineligible entries remain: %s" % dict(skipped))
    # protected-field check: raw bytes must still match the source at the recorded offset
    for e in selected:
        off = int(e["offset"], 16)
        if src[off:off + e["length"]].hex() != e["raw"]:
            raise SystemExit("protected source bytes changed for %s" % e["id"])
        for ref in e["refs"]:
            if not any(t["bank"] == ref[0] and t["sub"] == ref[1] and ref[2] < t["count"] for t in index["tables"]):
                raise SystemExit("reference %s not in table catalog for %s" % (ref, e["id"]))

    # --- glyph demand and mapping ---
    need = sorted(set(c for e in selected for c in plain_chars(e["target"])))
    new_codes = {}
    missing = []
    code = spec["glyphs"]["first_new_code"]
    for ch in need:
        if font.has(ch):
            new_codes[ch] = code
            code += 1
        elif ch in txt2code:
            pass  # reuse original glyph
        else:
            missing.append(ch)
    if missing:
        raise SystemExit("unmapped characters (no glyph in font or original table): %r" % "".join(missing))
    if code > spec["glyphs"]["max_code"] + 1:
        raise SystemExit("glyph budget exceeded: %d codes needed" % (code - spec["glyphs"]["first_new_code"]))
    enc_map = dict(txt2code)
    enc_map.update(new_codes)  # new font glyphs win over original Japanese glyphs for shared chars

    # --- expansion image layout ---
    exp_base = spec["expansion"]["base"]
    total_size = spec["expansion"]["total_size"]
    exp = bytearray()

    def align(n):
        while len(exp) % n:
            exp.append(0xff)

    bank_table_off = exp_base + len(exp)
    n_banks = (max(new_codes.values()) >> 8) + 1 if new_codes else 4
    exp += b"\0" * (16 * 4)
    align(4)
    bank_tables = {}
    for hi in range(4, n_banks):
        bank_tables[hi] = exp_base + len(exp)
        exp += b"\0" * (256 * 4)
    glyph_ptrs = {}
    for ch, c in sorted(new_codes.items(), key=lambda kv: kv[1]):
        px = font.pixels(ch, x_shift=spec["font"].get("x_shift", 0), y_shift=spec["font"].get("y_shift", 0))
        glyph_ptrs[c] = exp_base + len(exp)
        exp += pack_glyph(px)
    # fill bank table and bank pointer tables
    orig_bank_ptrs = [struct.unpack_from("<I", src, spec["glyphs"]["bank_table"] + 4 * i)[0] for i in range(4)]
    bt = bytearray()
    for hi in range(16):
        if hi < 4:
            bt += struct.pack("<I", orig_bank_ptrs[hi])
        elif hi in bank_tables:
            bt += struct.pack("<I", ROMBASE + bank_tables[hi])
        else:
            bt += struct.pack("<I", orig_bank_ptrs[0])  # unused hi bytes fall back to bank 0 (never emitted)
    exp[bank_table_off - exp_base:bank_table_off - exp_base + 64] = bt
    for hi, toff in bank_tables.items():
        tbl = bytearray()
        for lo in range(256):
            c = (hi << 8) | lo
            tbl += struct.pack("<I", ROMBASE + glyph_ptrs.get(c, glyph_ptrs[min(glyph_ptrs)]))
        exp[toff - exp_base:toff - exp_base + 1024] = tbl

    # --- messages ---
    plan = WritePlan(src)
    msg_locs = {}
    for e in selected:
        data = text_to_bytes(e["target"], enc_map)
        if not data.endswith((b"\xff", b"\xfd")):
            raise SystemExit("message %s does not end with <END>/<NEXT>" % e["id"])
        msg_locs[e["id"]] = (exp_base + len(exp), len(data))
        exp += data
    tables = {(t["bank"], t["sub"]): t for t in index["tables"]}
    for e in selected:
        new_ptr = struct.pack("<I", ROMBASE + msg_locs[e["id"]][0])
        old_ptr = struct.pack("<I", ROMBASE + int(e["offset"], 16))
        for bank, sub, mi in e["refs"]:
            toff = int(tables[(bank, sub)]["table_offset"], 16) + 4 * mi
            plan.add(toff, old_ptr, new_ptr, "msgptr:%s" % e["id"])
    # --- code literal patches for the relocated glyph bank table ---
    for site in spec["glyphs"]["bank_table_literal_sites"]:
        plan.add(site, struct.pack("<I", ROMBASE + spec["glyphs"]["bank_table"]),
                 struct.pack("<I", ROMBASE + bank_table_off), "literal:glyph_bank_table")
    plan.verify_no_overlap()
    # pointer sites may be written by several logical changes only if identical: dedupe exact duplicates
    seen = {}
    for o, ex, nw, w in plan.writes:
        if o in seen and seen[o] != nw:
            raise SystemExit("conflicting writes at %x" % o)
        seen[o] = nw

    if len(exp) > total_size - len(src):
        raise SystemExit("expansion overflow: %d bytes" % len(exp))
    img = bytearray(src)
    plan.apply(img)
    img += exp
    img += b"\xff" * (total_size - len(img))

    # --- final diff audit over the source extent ---
    changed = [i for i in range(len(src)) if img[i] != src[i]]
    covered = set()
    for o, ex, nw, w in plan.writes:
        covered.update(range(o, o + len(nw)))
    unexplained = [i for i in changed if i not in covered]
    if unexplained:
        raise SystemExit("unexplained changes at %s" % [hex(i) for i in unexplained[:10]])
    for o, ex, nw, w in plan.writes:
        if img[o:o + len(nw)] != nw:
            raise SystemExit("write not reflected: %s" % w)
    # protected regions in the expansion: none (whole area is new)
    out_dir = os.path.join(ROOT, "out")
    os.makedirs(out_dir, exist_ok=True)
    out_rom = os.path.join(out_dir, spec["output"]["rom"])
    open(out_rom, "wb").write(img)
    ips = build_ips(src, img)
    open(os.path.join(out_dir, spec["output"]["ips"]), "wb").write(ips)
    report = {
        "policy": args.policy, "non_distribution": args.policy != "release",
        "source_sha256": sha, "output_sha256": hashlib.sha256(img).hexdigest(), "output_size": len(img),
        "ips_sha256": hashlib.sha256(ips).hexdigest(),
        "font": {"path": spec["font"]["path"], "sha256": font.sha256},
        "messages_selected": len(selected), "messages_skipped": dict(skipped),
        "new_glyphs": len(new_codes), "glyph_banks": sorted(bank_tables), "expansion_bytes": len(exp),
        "writes": len(plan.writes), "changed_source_bytes": len(changed),
        "bank_table": "0x%08x" % (ROMBASE + bank_table_off),
        "reused_original_glyph_chars": sorted(set(c for c in need if c not in new_codes)),
    }
    json.dump(report, open(os.path.join(out_dir, "build-report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"glyph_codes": {ch: "%03x" % c for ch, c in new_codes.items()}},
              open(os.path.join(out_dir, "glyph-assignment.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(json.dumps({k: v for k, v in report.items() if k != "reused_original_glyph_chars"}, ensure_ascii=False))


def build_ips(src, dst):
    """IPS with RLE; dst may be longer than src (offsets stay below 16 MiB)."""
    assert len(dst) <= 0x1000000
    out = bytearray(b"PATCH")
    i = 0
    n = len(dst)
    while i < n:
        same = i < len(src) and dst[i] == src[i]
        if same:
            i += 1
            continue
        j = i
        while j < n and not (j < len(src) and dst[j] == src[j]) and j - i < 0xffff:
            j += 1
        chunk = dst[i:j]
        # split long runs of one byte as RLE records
        k = 0
        while k < len(chunk):
            run = 1
            while k + run < len(chunk) and chunk[k + run] == chunk[k] and run < 0xffff:
                run += 1
            off = i + k
            if off == 0x454f46:  # 'EOF' sentinel collision guard: emit one byte earlier
                raise SystemExit("IPS offset collides with EOF marker")
            if run >= 8:
                out += off.to_bytes(3, "big") + b"\0\0" + run.to_bytes(2, "big") + bytes([chunk[k]])
                k += run
            else:
                m = k + 1
                while m < len(chunk) and m - k < 0xffff:
                    r2 = 1
                    while m + r2 < len(chunk) and chunk[m + r2] == chunk[m] and r2 < 8:
                        r2 += 1
                    if r2 >= 8:
                        break
                    m += 1
                out += off.to_bytes(3, "big") + (m - k).to_bytes(2, "big") + chunk[k:m]
                k = m
        i = j
    out += b"EOF"
    return bytes(out)


if __name__ == "__main__":
    main()
