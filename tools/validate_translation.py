"""Mechanical checks for translation assets (not language quality).

For every entry with a non-empty target:
  - control-token sequence (<NAME:args>) identical to the source, in order
  - brace-token multiset ({BLK1}, {A}, ...) identical to the source
  - message ends with the same terminator token as the source (<END> or <NEXT>)
  - each page (split at <PAGE>/<PAGE2>) has at most 2 visible lines, each at most 18 cells
    (one Hangul syllable, punctuation mark, space or {TOKEN} = 1 cell)
  - every character has a glyph (Galmuri11 BDF or the original glyph table)
  - state is one of the known states
usage: python tools/validate_translation.py [--strict]  (exit 1 on any failure)
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textcodec import load_glyph_table  # noqa: E402
from bdffont import BdfFont  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STATES = {"untranslated", "in_progress", "translated", "needs_review", "needs_human_review", "reviewed", "approved"}
CTRL_RE = re.compile(r"<([A-Z0-9_]+)(?::([0-9a-fA-F]*))?>")
BRACE_RE = re.compile(r"\{[A-Za-z0-9?]+\}")


def cells(line):
    return len(BRACE_RE.sub("X", line))


def check_entry(e, font, txt2code):
    errs = []
    src, tgt = e["source"], e["target"]
    if CTRL_RE.findall(src) != CTRL_RE.findall(tgt):
        errs.append("control tokens differ: %s vs %s" % (CTRL_RE.findall(src), CTRL_RE.findall(tgt)))
    if sorted(BRACE_RE.findall(src)) != sorted(BRACE_RE.findall(tgt)):
        errs.append("brace tokens differ")
    for pg in re.split(r"<PAGE2?>", tgt):
        plain = CTRL_RE.sub("", pg)
        lines = plain.split("\n")
        if lines and lines[-1] == "":
            lines = lines[:-1]
        if len(lines) > 2:
            errs.append("page has %d lines" % len(lines))
        for ln in lines:
            if cells(ln) > 18:
                errs.append("line too long (%d): %r" % (cells(ln), ln))
    for ch in BRACE_RE.sub("", CTRL_RE.sub("", tgt)):
        if ch == "\n":
            continue
        if not (font.has(ch) or ch in txt2code):
            errs.append("no glyph for %r" % ch)
    for tok in BRACE_RE.findall(tgt):
        if tok not in txt2code:
            errs.append("unknown brace token %s" % tok)
    if e.get("state") not in STATES:
        errs.append("unknown state %r" % e.get("state"))
    return errs


def main():
    spec = json.load(open(os.path.join(ROOT, "config", "build.json"), encoding="utf-8"))
    font = BdfFont(os.path.join(ROOT, spec["font"]["path"]))
    _, txt2code = load_glyph_table()
    index = json.load(open(os.path.join(ROOT, "assets", "translation", "index.json"), encoding="utf-8"))
    total = bad = translated = 0
    for seg in index["segments"]:
        path = os.path.join(ROOT, "assets", "translation", seg["file"])
        data = json.load(open(path, encoding="utf-8"))
        for e in data["entries"]:
            total += 1
            if not e.get("target"):
                continue
            translated += 1
            errs = check_entry(e, font, txt2code)
            if errs:
                bad += 1
                print("%s %s: %s" % (seg["file"], e["id"], "; ".join(errs)))
    print("entries %d translated %d failing %d" % (total, translated, bad))
    sys.exit(1 if bad and "--strict" in sys.argv else 0)


if __name__ == "__main__":
    main()
