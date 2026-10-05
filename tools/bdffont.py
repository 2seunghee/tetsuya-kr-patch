"""BDF bitmap font loader and 16x16 8bpp glyph rasterizer for the game's glyph format.

Game glyph: 16x16 pixels, 1 byte per pixel, stored as four 8x8 tiles (TL, TR, BL, BR).
Pixel values: 0 transparent, 1 main stroke, 2 shadow (1px right/down), matching the original font.
"""
import hashlib


class BdfFont:
    def __init__(self, path):
        self.path = path
        self.sha256 = hashlib.sha256(open(path, "rb").read()).hexdigest()
        self.glyphs = {}
        self.ascent = 14
        self.descent = 2
        enc = None
        bbx = None
        dw = 0
        bits = None
        name = None
        for line in open(path, encoding="utf-8", errors="ignore"):
            line = line.rstrip("\n")
            if line.startswith("FONT_ASCENT"):
                self.ascent = int(line.split()[1])
            elif line.startswith("FONT_DESCENT"):
                self.descent = int(line.split()[1])
            elif line.startswith("STARTCHAR"):
                name = line.split(" ", 1)[1]
                bits = None
            elif line.startswith("ENCODING"):
                enc = int(line.split()[1])
            elif line.startswith("BBX"):
                bbx = [int(v) for v in line.split()[1:]]
            elif line.startswith("DWIDTH"):
                dw = int(line.split()[1])
            elif line == "BITMAP":
                bits = []
            elif line == "ENDCHAR":
                if enc is not None and enc >= 0:
                    self.glyphs[enc] = (bbx, dw, bits)
                name = None
            elif bits is not None and name is not None:
                bits.append(line)

    def has(self, ch):
        return ord(ch) in self.glyphs

    def pixels(self, ch, x_shift=0, y_shift=0, shadow=True):
        """Return a 16x16 list of pixel values for ch, or None if the glyph is missing."""
        g = self.glyphs.get(ord(ch))
        if g is None:
            return None
        (w, h, xoff, yoff), dw, rows = g
        px = [[0] * 16 for _ in range(16)]
        top = self.ascent - (yoff + h) + y_shift
        if dw < 12:  # half-width glyph: center it in the 12px cell
            x_shift += (12 - dw) // 2
        for r, row in enumerate(rows):
            bitsval = int(row, 16)
            nbits = len(row) * 4
            for cx in range(w):
                if (bitsval >> (nbits - 1 - cx)) & 1:
                    x = xoff + cx + x_shift
                    y = top + r
                    if 0 <= x < 16 and 0 <= y < 16:
                        px[y][x] = 1
        if shadow:
            for y in range(15, -1, -1):
                for x in range(15, -1, -1):
                    if px[y][x] == 1:
                        if x + 1 < 16 and px[y][x + 1] == 0:
                            px[y][x + 1] = 2
                        if y + 1 < 16 and px[y + 1][x] == 0:
                            px[y + 1][x] = 2
                        if x + 1 < 16 and y + 1 < 16 and px[y + 1][x + 1] == 0:
                            px[y + 1][x + 1] = 2
        return px


def pack_glyph(px):
    """16x16 pixel matrix -> 256 bytes in the game's four-tile layout."""
    out = bytearray(256)
    for y in range(16):
        for x in range(16):
            out[(y // 8) * 128 + (x // 8) * 64 + (y % 8) * 8 + (x % 8)] = px[y][x]
    return bytes(out)


def unpack_glyph(data):
    return [[data[(y // 8) * 128 + (x // 8) * 64 + (y % 8) * 8 + (x % 8)] for x in range(16)] for y in range(16)]
