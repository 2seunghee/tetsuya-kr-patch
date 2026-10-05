"""Render GBA BG/OBJ layers from emucap dumps (VRAM, palette, OAM, IO) for graphics-text investigation."""
import os, struct, sys
from PIL import Image

def rgb15(v): return ((v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3)

def load(prefix):
    vram = open(prefix + "_gbaVideoRam.bin", "rb").read(); pal = open(prefix + "_gbaPaletteRam.bin", "rb").read()
    oam = open(prefix + "_gbaSpriteRam.bin", "rb").read(); io = open(prefix + "_io.bin", "rb").read()
    return vram, pal, oam, io

def tile4(vram, base, idx, pal, palbank, flipx=False, flipy=False):
    off = base + idx * 32; px = []
    for y in range(8):
        row = []
        for x in range(8):
            b = vram[off + y * 4 + x // 2]; v = (b & 15) if x % 2 == 0 else (b >> 4)
            row.append(v)
        px.append(row)
    if flipx: px = [r[::-1] for r in px]
    if flipy: px = px[::-1]
    return px

def tile8(vram, base, idx, flipx=False, flipy=False):
    off = base + idx * 64
    px = [[vram[off + y * 8 + x] for x in range(8)] for y in range(8)]
    if flipx: px = [r[::-1] for r in px]
    if flipy: px = px[::-1]
    return px

def render_bg(vram, pal, io, n):
    dispcnt = struct.unpack_from("<H", io, 0)[0]; mode = dispcnt & 7
    bgcnt = struct.unpack_from("<H", io, 8 + 2 * n)[0]
    if mode != 0 and (mode == 1 and n == 3 or mode == 2 and n < 2 or mode >= 3):
        return None, {"mode": mode, "skipped": True}
    charbase = ((bgcnt >> 2) & 3) * 0x4000; scrbase = ((bgcnt >> 8) & 31) * 0x800; c256 = (bgcnt >> 7) & 1; size = bgcnt >> 14
    w = 256 if size in (0, 2) else 512; h = 256 if size in (0, 1) else 512
    hofs = struct.unpack_from("<H", io, 0x10 + 4 * n)[0] & 511; vofs = struct.unpack_from("<H", io, 0x12 + 4 * n)[0] & 511
    img = Image.new("RGB", (w, h), (0, 0, 0)); used = {}
    for ty in range(h // 8):
        for tx in range(w // 8):
            sb = scrbase + ((ty // 32) * (w // 256) + (tx // 32)) * 0x800 + ((ty % 32) * 32 + (tx % 32)) * 2
            e = struct.unpack_from("<H", vram, sb)[0]; idx = e & 1023; fx = (e >> 10) & 1; fy = (e >> 11) & 1; pb = e >> 12
            px = tile8(vram, charbase, idx, fx, fy) if c256 else tile4(vram, charbase, idx, pal, pb, fx, fy)
            used.setdefault(idx, 0); used[idx] += 1
            for y in range(8):
                for x in range(8):
                    v = px[y][x]
                    if v: img.putpixel((tx * 8 + x, ty * 8 + y), rgb15(struct.unpack_from("<H", pal, (v if c256 else pb * 16 + v) * 2)[0]))
    return img, {"mode": mode, "charbase": hex(charbase), "scrbase": hex(scrbase), "c256": c256, "size": (w, h), "hofs": hofs, "vofs": vofs, "enabled": bool(dispcnt & (0x100 << n)), "tiles_used": len(used)}

def render_obj(vram, pal, oam, io):
    dispcnt = struct.unpack_from("<H", io, 0)[0]; mapping1d = (dispcnt >> 6) & 1
    img = Image.new("RGB", (240, 160), (0, 0, 0)); ents = []
    sizes = {(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),(1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),(2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}
    for i in range(128):
        a0, a1, a2 = struct.unpack_from("<HHH", oam, i * 8)
        if (a0 >> 8) & 3 == 2: continue  # disabled
        y = a0 & 255; x = a1 & 511; shape = a0 >> 14; sz = a1 >> 14; c256 = (a0 >> 13) & 1; tid = a2 & 1023; pb = a2 >> 12
        w, h = sizes[(shape, sz)]
        if y >= 160: y -= 256
        if x >= 240: x -= 512
        ents.append((i, x, y, w, h, tid, c256, pb))
        for ty in range(h // 8):
            for tx in range(w // 8):
                if mapping1d: t = tid + (ty * (w // 8) + tx) * (2 if c256 else 1)
                else: t = tid + ty * 32 + tx * (2 if c256 else 1)
                px = tile8(vram, 0x10000, t // 2) if c256 else tile4(vram, 0x10000, t, pal, pb)
                for yy in range(8):
                    for xx in range(8):
                        v = px[yy][xx]
                        if v and 0 <= x + tx*8+xx < 240 and 0 <= y + ty*8+yy < 160:
                            img.putpixel((x + tx*8+xx, y + ty*8+yy), rgb15(struct.unpack_from("<H", pal, 512 + (v if c256 else pb*16+v) * 2)[0]))
    return img, ents

if __name__ == "__main__":
    prefix = sys.argv[1]; vram, pal, oam, io = load(prefix)
    dispcnt = struct.unpack_from("<H", io, 0)[0]
    print("DISPCNT %04x mode %d bg0-3 %s obj %d 1d %d" % (dispcnt, dispcnt & 7, [(dispcnt >> (8+i)) & 1 for i in range(4)], (dispcnt >> 12) & 1, (dispcnt >> 6) & 1))
    for n in range(4):
        img, info = render_bg(vram, pal, io, n); print("BG%d" % n, info)
        if img: img.save(prefix + "_bg%d.png" % n)
    img, ents = render_obj(vram, pal, oam, io); img.save(prefix + "_obj.png")
    print("OBJ count", len(ents)); print([e for e in ents[:40]])
