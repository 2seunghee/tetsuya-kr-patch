"""Text engine codec for Gambler Densetsu Tetsuya (ATYJ). Shared by extractor, encoder, build.

Stream grammar (byte oriented, from the interpreter at 0x080325e0):
  0xFF            end of message (stop)                         -> token <END>
  0xFD            end of message (auto-continue to next index)  -> token <NEXT>
  0xFE            line break (column := 18)                     -> newline in text
  control bytes with fixed argument widths (CTRL table)         -> <NAME:hexargs>
  any other byte  = high byte of a 2-byte big-endian glyph code (hi 0..3, lo 0..255)
"""
import json
import os
import re

CTRL = {0x10: 0, 0x11: 1, 0x12: 0, 0x13: 0, 0x20: 2, 0x21: 2, 0x30: 2, 0x31: 0, 0x32: 1, 0x33: 1,
        0x40: 1, 0x41: 1, 0x42: 0, 0x50: 1, 0x51: 1, 0x70: 1, 0x71: 2, 0x72: 2, 0x73: 2, 0x80: 0,
        0x90: 0, 0xa0: 1, 0xa1: 0, 0xb0: 1, 0xb1: 1, 0xb2: 1, 0xc0: 1, 0xc1: 1, 0xd0: 1, 0xd1: 0}
CTRL_NAMES = {0x10: "CLR", 0x11: "WAIT", 0x12: "PAGE", 0x13: "PAGE2", 0x20: "PORTL", 0x21: "PORTR",
              0x30: "WIN", 0x31: "C31", 0x32: "C32", 0x33: "C33", 0x40: "SE", 0x41: "BGM", 0x42: "C42",
              0x50: "FLAG", 0x51: "UNFLAG", 0x70: "JUMP", 0x71: "JIF", 0x72: "CHOICE", 0x73: "JIF2",
              0x80: "RESET", 0x90: "C90", 0xa0: "FACE", 0xa1: "NOFACE", 0xb0: "C_B0", 0xb1: "SETF",
              0xb2: "C_B2", 0xc0: "C_C0", 0xc1: "C_C1", 0xd0: "C_D0", 0xd1: "C_D1"}
NAME_TO_CTRL = {v: k for k, v in CTRL_NAMES.items()}
LINE_WIDTH = 18
HERE = os.path.dirname(os.path.abspath(__file__))


def load_glyph_table(path=None):
    path = path or os.path.join(HERE, "..", "config", "glyph_table.json")
    j = json.load(open(path, encoding="utf-8"))
    code2txt = {int(k, 16): v["text"] for k, v in j["codes"].items()}
    txt2code = {}
    for c, t in sorted(code2txt.items()):
        txt2code.setdefault(t, c)  # first code wins for duplicated glyphs
    return code2txt, txt2code


def tokenize(data, off):
    """Return (tokens, end_offset). tokens: ('CH',code) | ('C',byte,args) | ('BR',) | ('END',byte)."""
    toks = []
    p = off
    n = len(data)
    while p < n:
        b = data[p]
        if b in (0xff, 0xfd):
            toks.append(("END", b))
            return toks, p + 1
        if b == 0xfe:
            toks.append(("BR",))
            p += 1
            continue
        if b in CTRL:
            w = CTRL[b]
            toks.append(("C", b, bytes(data[p + 1:p + 1 + w])))
            p += 1 + w
            continue
        if p + 1 >= n:
            raise ValueError("truncated glyph code at %x" % p)
        toks.append(("CH", (b << 8) | data[p + 1]))
        p += 2
        if p - off > 8192:
            raise ValueError("runaway message at %x" % off)
    raise ValueError("unterminated message at %x" % off)


def tokens_to_text(toks, code2txt):
    out = []
    for t in toks:
        if t[0] == "CH":
            out.append(code2txt.get(t[1], "{?%03x}" % t[1]))
        elif t[0] == "BR":
            out.append("\n")
        elif t[0] == "C":
            name = CTRL_NAMES[t[1]]
            out.append("<%s%s>" % (name, (":" + t[2].hex()) if t[2] else ""))
        elif t[0] == "END":
            out.append("<END>" if t[1] == 0xff else "<NEXT>")
    return "".join(out)


TOKEN_RE = re.compile(r"<([A-Z0-9_]+)(?::([0-9a-fA-F]*))?>|\{([A-Za-z0-9?]+)\}|(\n)|(.)", re.S)


def text_to_bytes(text, txt2code):
    """Inverse of tokens_to_text. Raises KeyError on an unmapped character."""
    out = bytearray()
    for m in TOKEN_RE.finditer(text):
        name, arg, brace, nl, ch = m.groups()
        if name:
            if name == "END":
                out.append(0xff)
            elif name == "NEXT":
                out.append(0xfd)
            else:
                b = NAME_TO_CTRL[name]
                a = bytes.fromhex(arg or "")
                if len(a) != CTRL[b]:
                    raise ValueError("bad arg width for %s" % name)
                out.append(b)
                out += a
        elif brace:
            code = txt2code["{%s}" % brace]
            out += bytes([code >> 8, code & 0xff])
        elif nl:
            out.append(0xfe)
        else:
            if ch not in txt2code:
                raise KeyError(ch)
            code = txt2code[ch]
            out += bytes([code >> 8, code & 0xff])
    return bytes(out)


def visible_lines(text):
    """Split text into display lines (control tokens removed), for width checks."""
    plain = re.sub(r"<[A-Z0-9_]+(?::[0-9a-fA-F]*)?>", "", text)
    return plain.split("\n")
