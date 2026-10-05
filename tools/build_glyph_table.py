"""Build config/glyph_table.json from the human transcription config/glyph_transcription.txt
and the glyph pointer table in the ROM (0x0821b1b8 -> 4 banks x 256 pointers).

Transcription format: `<hex base> <chars>` per row (32 glyph codes), plus `<hex code>=<token>`
lines for icon/blank glyphs. Every code with a valid glyph pointer must be covered exactly once.
"""
import collections
import json
import os
import struct
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ROM = os.path.join(ROOT, "originals", "Gambler Densetsu Tetsuya - Yomigaeru Densetsu (Japan).gba")
BANK_TABLE = 0x21b1b8
ROMBASE = 0x08000000


def glyph_ptrs(d):
    banks = [struct.unpack_from("<I", d, BANK_TABLE + 4 * i)[0] - ROMBASE for i in range(4)]
    out = {}
    for hi, b in enumerate(banks):
        for lo in range(256):
            p = struct.unpack_from("<I", d, b + 4 * lo)[0]
            if 0x08440000 <= p < 0x084a0000:
                out[(hi << 8) | lo] = p - ROMBASE
    return out


def glyph_pixels(d, off):
    g = d[off:off + 256]
    return [[g[(y // 8) * 128 + (x // 8) * 64 + (y % 8) * 8 + (x % 8)] for x in range(16)] for y in range(16)]


def main():
    d = open(ROM, "rb").read()
    gp = glyph_ptrs(d)
    tab = {}
    for line in open(os.path.join(ROOT, "config", "glyph_transcription.txt"), encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        if "=" in line.split(" ", 1)[0]:
            code, tok = line.split("=", 1)
            tab[int(code, 16)] = tok
            continue
        base, chars = line.split(" ", 1)
        for i, ch in enumerate(chars):
            tab[int(base, 16) + i] = ch
    missing = sorted(set(gp) - set(tab))
    extra = sorted(set(tab) - set(gp))
    if missing or extra:
        raise SystemExit("transcription mismatch: missing %s extra %s" % ([hex(c) for c in missing], [hex(c) for c in extra]))
    dups = collections.defaultdict(list)
    for c, ch in tab.items():
        dups[ch].append("%03x" % c)
    out = {"source": "originals/Gambler Densetsu Tetsuya - Yomigaeru Densetsu (Japan).gba",
           "source_sha256": "65e8eb749a88c18c02ea8bf783b62f0cd7a39f0e38f550e7be124172016c08bd",
           "glyph_bank_table": "0x%08x" % (ROMBASE + BANK_TABLE),
           "glyph_format": "16x16 8bpp, four 8x8 tiles (TL,TR,BL,BR), 256 bytes per glyph, drawn at a 12px pitch",
           "note": "Identity established by visual transcription of rendered glyphs. Tokens in braces are icon/blank glyphs.",
           "duplicates": {ch: cs for ch, cs in dups.items() if len(cs) > 1},
           "codes": {"%03x" % c: {"text": tab[c], "glyph_offset": "0x%06x" % gp[c]} for c in sorted(tab)}}
    json.dump(out, open(os.path.join(ROOT, "config", "glyph_table.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("codes", len(tab), "duplicates", out["duplicates"])


if __name__ == "__main__":
    main()
