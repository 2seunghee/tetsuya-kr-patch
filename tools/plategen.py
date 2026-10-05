"""Generate Korean speaker name plates (OBJ 4bpp, w x h tiles) replacing the originals in place.

Source structure (established in research/graphics-text-20261005.md): pointer table at 0x081fa1f8 ->
entries [u8 w_tiles][u8 h_tiles][w*h tiles of 32 bytes]. Name plates are the 6x2 entries (48x16 px).
Text pixels use value 15 (white fill) and 1 (black outline) on a textured background (values 2..14).

The generator keeps the original plate's background (reconstructed from text-free columns), erases
the original text and draws the Korean name with the BDF font, white fill + 1px black outline.
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdffont import BdfFont  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TABLE = 0x1fa1f8
ROMBASE = 0x08000000


def plate_entries(rom):
    ents = []
    while True:
        v = struct.unpack_from("<I", rom, TABLE + 4 * len(ents))[0]
        if not (0x081c9000 <= v < 0x081cc800):
            break
        ents.append(v - ROMBASE)
    return ents


def decode(rom, off):
    w, h = rom[off], rom[off + 1]
    px = [[0] * (w * 8) for _ in range(h * 8)]
    for t in range(w * h):
        tx, ty = t % w, t // w
        for y in range(8):
            for x in range(8):
                b = rom[off + 2 + t * 32 + y * 4 + x // 2]
                px[ty * 8 + y][tx * 8 + x] = (b & 15) if x % 2 == 0 else (b >> 4)
    return w, h, px


def encode(w, h, px):
    out = bytearray([w, h])
    for t in range(w * h):
        tx, ty = t % w, t // w
        for y in range(8):
            for x in range(0, 8, 2):
                lo = px[ty * 8 + y][tx * 8 + x]
                hi = px[ty * 8 + y][tx * 8 + x + 1]
                out.append(lo | (hi << 4))
    return bytes(out)


def clean_background(px):
    """Erase text (values 1 and 15) by filling each row from its nearest text-free pixels."""
    h = len(px)
    w = len(px[0])
    out = [row[:] for row in px]
    for y in range(h):
        row = out[y]
        bg = [x for x in range(w) if row[x] not in (1, 15)]
        if not bg:
            continue
        for x in range(w):
            if row[x] in (1, 15):
                # nearest background pixel on the same row
                nearest = min(bg, key=lambda b: abs(b - x))
                row[x] = row[nearest]
    return out


def draw_text(px, text, fonts, max_w):
    """Draw text centered with white fill (15) and black outline (1). Chooses the largest font that fits."""
    h = len(px)
    w = len(px[0])
    for font in fonts:
        glyphs = []
        total = 0
        for ch in text:
            g = font.glyphs.get(ord(ch))
            if g is None:
                glyphs = None
                break
            (gw, gh, xoff, yoff), dw, rows = g
            glyphs.append((g, dw))
            total += dw
        if glyphs is None:
            continue
        if total - 1 <= max_w:
            break
    else:
        raise ValueError("no font fits %r" % text)
    ink = [[0] * w for _ in range(h)]
    x0 = (w - total) // 2
    base = (h + font.ascent - font.descent) // 2  # vertical center of ascent..descent box
    cx = x0
    for (gw, gh, xoff, yoff), dw, rows in [(g[0][0], g[1], g[0][2]) for g in glyphs]:
        top = base - (yoff + gh)
        for r, rowhex in enumerate(rows):
            bits = int(rowhex, 16)
            nb = len(rowhex) * 4
            for c in range(gw):
                if (bits >> (nb - 1 - c)) & 1:
                    x = cx + xoff + c
                    y = top + r
                    if 0 <= x < w and 0 <= y < h:
                        ink[y][x] = 1
        cx += dw
    for y in range(h):
        for x in range(w):
            if ink[y][x]:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < h and 0 <= xx < w and not ink[yy][xx]:
                            px[yy][xx] = 1
    for y in range(h):
        for x in range(w):
            if ink[y][x]:
                px[y][x] = 15
    return px


def build_plates(rom, names, fonts):
    """names: {entry_index: korean}. Returns list of (offset, expected_bytes, new_bytes)."""
    writes = []
    ents = plate_entries(rom)
    for idx, text in names.items():
        off = ents[int(idx)]
        w, h, px = decode(rom, off)
        if (w, h) != (6, 2):
            raise ValueError("entry %s is not a 6x2 plate" % idx)
        size = 2 + w * h * 32
        expected = bytes(rom[off:off + size])
        px = clean_background(px)
        px = draw_text(px, text, fonts, max_w=w * 8 - 6)
        new = encode(w, h, px)
        assert len(new) == size
        writes.append((off, expected, new, "plate:%s" % idx))
    return writes


def preview(rom, writes, path, pal):
    from PIL import Image
    cell_w, cell_h = 52, 20
    cols = 6
    rows = (len(writes) + cols - 1) // cols
    img = Image.new("RGB", (cols * cell_w, rows * cell_h), (40, 40, 40))
    for i, (off, exp, new, w_) in enumerate(writes):
        w, h, px = decode(new, 0)
        for y in range(h * 8):
            for x in range(w * 8):
                v = px[y][x]
                if v:
                    img.putpixel(((i % cols) * cell_w + x, (i // cols) * cell_h + y), pal[v])
    img = img.resize((img.width * 3, img.height * 3))
    img.save(path)


if __name__ == "__main__":
    spec = json.load(open(os.path.join(ROOT, "config", "build.json"), encoding="utf-8"))
    rom = open(os.path.join(ROOT, spec["source"]["path"]), "rb").read()
    names = json.load(open(os.path.join(ROOT, "config", "plates.json"), encoding="utf-8"))["plates"]
    fonts = [BdfFont(os.path.join(ROOT, p)) for p in ("assets/fonts/sources/galmuri/Galmuri11.bdf",
                                                        "assets/fonts/sources/galmuri/Galmuri9.bdf",
                                                        "assets/fonts/sources/galmuri/Galmuri7.bdf")]
    writes = build_plates(rom, names, fonts)
    pal = [(0, 16, 248), (0, 0, 0), (80, 72, 72), (144, 136, 112), (144, 144, 112), (144, 144, 120), (152, 152, 120),
           (160, 160, 128), (160, 160, 136), (168, 168, 144), (176, 176, 144), (176, 176, 152), (192, 200, 176),
           (200, 208, 192), (208, 208, 200), (248, 248, 248)]
    preview(rom, writes, os.path.join(ROOT, "work", "plates_kr.png"), pal)
    print("plates", len(writes))
