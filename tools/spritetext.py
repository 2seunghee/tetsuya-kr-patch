"""Replace text inside OBJ sprite regions of a 4bpp tile sheet (title menu items) with Korean text.

Region spec: sheet base offset, tile index of top-left, width/height in tiles (2D mapping, 32 tiles per row),
border/background handling: rows keep their left-edge background value; text drawn as fill value + outline value.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bdffont import BdfFont  # noqa: E402


def read_region(rom, base, t0, w, h):
    px = [[0] * (w * 8) for _ in range(h * 8)]
    for r in range(h):
        for c in range(w):
            off = base + (t0 + r * 32 + c) * 32
            for y in range(8):
                for x in range(8):
                    b = rom[off + y * 4 + x // 2]
                    px[r * 8 + y][c * 8 + x] = (b & 15) if x % 2 == 0 else (b >> 4)
    return px


def region_writes(rom, base, t0, w, h, px, writer):
    """Return per-tile Expected Writes for the region."""
    out = []
    for r in range(h):
        for c in range(w):
            off = base + (t0 + r * 32 + c) * 32
            new = bytearray()
            for y in range(8):
                for x in range(0, 8, 2):
                    new.append(px[r * 8 + y][c * 8 + x] | (px[r * 8 + y][c * 8 + x + 1] << 4))
            exp = bytes(rom[off:off + 32])
            if exp != bytes(new):
                out.append((off, exp, bytes(new), writer))
    return out


def retext_box(px, text, font, fill=15, outline=1, inner=(2, 2), bg_col=2):
    """Fill the interior (inside the 2px frame) with each row's background value at column bg_col,
    then draw text centered with fill + outline."""
    h = len(px)
    w = len(px[0])
    for y in range(h):
        bg = px[y][bg_col]
        for x in range(bg_col, w - bg_col):
            px[y][x] = bg
    # measure
    glyphs = []
    total = 0
    for ch in text:
        g = font.glyphs.get(ord(ch))
        if g is None:
            raise KeyError(ch)
        glyphs.append(g)
        total += g[1]
    if total > w - 2 * bg_col - 2:
        raise ValueError("text too wide: %r (%d px)" % (text, total))
    ink = [[0] * w for _ in range(h)]
    cx = (w - total) // 2
    base = (h + font.ascent - font.descent) // 2
    for (gw, gh, xoff, yoff), dw, rows in glyphs:
        top = base - (yoff + gh)
        for r, rowhex in enumerate(rows):
            bits = int(rowhex, 16)
            nb = len(rowhex) * 4
            for c in range(gw):
                if (bits >> (nb - 1 - c)) & 1:
                    x, y = cx + xoff + c, top + r
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
                            px[yy][xx] = outline
    for y in range(h):
        for x in range(w):
            if ink[y][x]:
                px[y][x] = fill
    return px


def retext_clear(px, text, font, fill=15, outline=2, x_pad=0):
    """Transparent sprite text: clear the region, draw text left-aligned at x_pad (or centered if x_pad<0)."""
    h = len(px)
    w = len(px[0])
    for y in range(h):
        for x in range(w):
            px[y][x] = 0
    glyphs = []
    total = 0
    for ch in text:
        g = font.glyphs.get(ord(ch))
        if g is None:
            raise KeyError(ch)
        glyphs.append(g)
        total += g[1]
    if total > w - 2:
        raise ValueError("text too wide: %r (%d px)" % (text, total))
    ink = [[0] * w for _ in range(h)]
    cx = x_pad if x_pad >= 0 else (w - total) // 2
    base = (h + font.ascent - font.descent) // 2
    for (gw, gh, xoff, yoff), dw, rows in glyphs:
        top = base - (yoff + gh)
        for r, rowhex in enumerate(rows):
            bits = int(rowhex, 16)
            nb = len(rowhex) * 4
            for c in range(gw):
                if (bits >> (nb - 1 - c)) & 1:
                    x, y = cx + xoff + c, top + r
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
                            px[yy][xx] = outline
    for y in range(h):
        for x in range(w):
            if ink[y][x]:
                px[y][x] = fill
    return px


def apply_item(px, it, fonts):
    if it.get("mode", "box") == "clear":
        return retext_clear(px, it["text"], fonts[it["font"]], fill=it.get("fill", 15), outline=it.get("outline", 2), x_pad=it.get("x_pad", -1))
    return retext_box(px, it["text"], fonts[it["font"]])


def build_sprite_texts(rom, items, fonts):
    """items: list of {base, tile, w, h, text, font, mode?} ; returns writes."""
    writes = []
    for it in items:
        px = read_region(rom, it["base"], it["tile"], it["w"], it["h"])
        px = apply_item(px, it, fonts)
        writes += region_writes(rom, it["base"], it["tile"], it["w"], it["h"], px, "sprite:%s" % it["id"])
    return writes


def preview(rom, items, fonts, pal, path):
    from PIL import Image
    img = Image.new("RGB", (max(it["w"] for it in items) * 8, sum(it["h"] * 8 + 2 for it in items)), (30, 30, 60))
    y0 = 0
    for it in items:
        px = apply_item(read_region(rom, it["base"], it["tile"], it["w"], it["h"]), it, fonts)
        for y in range(it["h"] * 8):
            for x in range(it["w"] * 8):
                if px[y][x]:
                    img.putpixel((x, y0 + y), pal[px[y][x]])
        y0 += it["h"] * 8 + 2
    img.resize((img.width * 3, img.height * 3)).save(path)
