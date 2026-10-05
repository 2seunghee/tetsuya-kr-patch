"""Extract all dialogue messages from the ROM into assets/translation/segments/*.json.

Population: root bank table at 0x082188ec (11 banks), each bank = array of sub-table pointers,
each sub-table = array of message pointers (ascending), message = byte stream (see textcodec).
Stable ID = source offset of the message (hex). refs records every (bank, sub, msg) index path.
"""
import collections
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textcodec import tokenize, tokens_to_text, load_glyph_table  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ROM = os.path.join(ROOT, "originals", "Gambler Densetsu Tetsuya - Yomigaeru Densetsu (Japan).gba")
EXPECT_SHA256 = "65e8eb749a88c18c02ea8bf783b62f0cd7a39f0e38f550e7be124172016c08bd"
BANK_ROOT = 0x2188ec
N_BANKS = 11
ROMBASE = 0x08000000


def enumerate_tables(d):
    u32 = lambda o: struct.unpack_from("<I", d, o)[0]  # noqa: E731
    isrom = lambda v: ROMBASE <= v < ROMBASE + len(d)  # noqa: E731
    banks = [u32(BANK_ROOT + 4 * i) - ROMBASE for i in range(N_BANKS)]
    out = []
    for bi, b in enumerate(banks):
        subs = []
        j = 0
        while isrom(u32(b + 4 * j)):
            subs.append(u32(b + 4 * j) - ROMBASE)
            j += 1
        for si, s in enumerate(subs):
            ptrs = []
            k = 0
            while isrom(u32(s + 4 * k)):
                v = u32(s + 4 * k) - ROMBASE
                if ptrs and v < ptrs[-1]:
                    break
                ptrs.append(v)
                k += 1
            out.append((bi, si, s, ptrs))
    return out


def main():
    d = open(ROM, "rb").read()
    assert hashlib.sha256(d).hexdigest() == EXPECT_SHA256, "source ROM hash mismatch"
    code2txt, _ = load_glyph_table()
    msgs = {}
    tables = []
    for bi, si, s, ptrs in enumerate_tables(d):
        tables.append({"bank": bi, "sub": si, "table_offset": "0x%06x" % s, "count": len(ptrs)})
        for mi, m in enumerate(ptrs):
            nxt = ptrs[mi + 1] if mi + 1 < len(ptrs) else None
            if m == s:  # self-pointing empty table (0x200b44)
                continue
            toks, end = tokenize(d, m)
            if nxt is not None and end != nxt:
                raise SystemExit("boundary mismatch bank %d sub %d msg %d @%x end %x next %x" % (bi, si, mi, m, end, nxt))
            e = msgs.setdefault("%06x" % m, {"id": "%06x" % m, "offset": "0x%06x" % m, "length": end - m,
                                           "raw": d[m:end].hex(), "source": tokens_to_text(toks, code2txt),
                                           "refs": []})
            e["refs"].append([bi, si, mi])
    ids = sorted(msgs, key=lambda k: int(k, 16))
    gaps = []
    for a, b2 in zip(ids, ids[1:]):
        ea = int(a, 16) + msgs[a]["length"]
        if ea != int(b2, 16):
            gaps.append((a, "0x%06x" % ea, b2))
    outdir = os.path.join(ROOT, "assets", "translation", "segments")
    os.makedirs(outdir, exist_ok=True)
    by_bank = collections.defaultdict(list)
    for k in ids:
        by_bank[msgs[k]["refs"][0][0]].append(msgs[k])
    nchars = 0
    for k in ids:
        nchars += sum(1 for t in tokenize(d, int(k, 16))[0] if t[0] == "CH")
    index = {"source_sha256": EXPECT_SHA256, "bank_root": "0x%06x" % BANK_ROOT, "banks": N_BANKS,
             "tables": tables, "segments": [], "message_count": len(ids), "char_count": nchars,
             "gaps": gaps[:50], "gap_count": len(gaps)}
    for bi in sorted(by_bank):
        fn = "bank%02d.json" % bi
        entries = [{"id": e["id"], "offset": e["offset"], "length": e["length"], "raw": e["raw"],
                    "refs": e["refs"], "source": e["source"], "target": "", "state": "untranslated",
                    "notes": ""} for e in by_bank[bi]]
        json.dump({"bank": bi, "entries": entries}, open(os.path.join(outdir, fn), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        index["segments"].append({"file": "segments/" + fn, "bank": bi, "count": len(entries)})
    json.dump(index, open(os.path.join(ROOT, "assets", "translation", "index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("messages", len(ids), "chars", nchars, "gaps", len(gaps))
    unmapped = collections.Counter()
    for k in ids:
        for t in tokenize(d, int(k, 16))[0]:
            if t[0] == "CH" and t[1] not in code2txt:
                unmapped[t[1]] += 1
    print("unmapped codes:", {hex(k): v for k, v in unmapped.items()})


if __name__ == "__main__":
    main()
