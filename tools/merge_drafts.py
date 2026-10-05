"""Merge translation drafts (assets/translation/drafts/*.json, {"id": "target", ...}) into segments.

Only entries whose id exists are updated; protected fields are never touched. State becomes
"translated" unless the draft file name ends with ".reviewed.json" (then "reviewed").
Conflicting drafts for one id (different targets) are reported and left untouched.
"""
import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def main():
    drafts = {}
    conflicts = set()
    for path in sorted(glob.glob(os.path.join(ROOT, "assets", "translation", "drafts", "*.json"))):
        state = "reviewed" if path.endswith(".reviewed.json") else "translated"
        for k, v in json.load(open(path, encoding="utf-8")).items():
            if not isinstance(v, str) or not v:
                continue
            if k in drafts and drafts[k][0] != v:
                conflicts.add(k)
            drafts[k] = (v, state, os.path.basename(path))
    index = json.load(open(os.path.join(ROOT, "assets", "translation", "index.json"), encoding="utf-8"))
    applied = 0
    for seg in index["segments"]:
        p = os.path.join(ROOT, "assets", "translation", seg["file"])
        data = json.load(open(p, encoding="utf-8"))
        changed = False
        for e in data["entries"]:
            if e["id"] in drafts and e["id"] not in conflicts:
                v, state, src = drafts[e["id"]]
                if e.get("target") != v or e.get("state") != state:
                    e["target"] = v; e["state"] = state; e["notes"] = "draft:" + src
                    changed = True; applied += 1
        if changed:
            json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("drafts", len(drafts), "applied", applied, "conflicts", sorted(conflicts))
    sys.exit(1 if conflicts else 0)

if __name__ == "__main__":
    main()
