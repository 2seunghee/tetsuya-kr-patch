"""Drive a launched ROM through a scripted input sequence and save screenshots.

usage: python tools/emucap_nav.py <rom> <outdir> <script>
script: semicolon-separated steps, each `wait:N` | `tap:btn[+btn]:press:after` | `shot:name` | `save:name` | `load:path`
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emucap_client import EmucapClient

def run(rom, outdir, script, keep=False):
    rom = os.path.abspath(rom); outdir = os.path.abspath(outdir); os.makedirs(outdir, exist_ok=True)
    c = EmucapClient(env={"EMUCAP_GBA_BIOS": os.path.abspath("work/bios/gba_bios.bin")}); c.start()
    c.call("launch_plan", {"content_path": rom, "system": "gba"})
    l = c.call("launch", {"content_path": rom, "system": "gba", "start_frozen": True}, timeout=300)
    if l.get("isError") or not l["text"] or not l["text"][0].get("connected"):
        print("LAUNCH FAILED", json.dumps(l, ensure_ascii=False)[:800]); c.close(); return
    lid = l["text"][0]["launch_id"]
    log = []
    for step in [s.strip() for s in script.split(";") if s.strip()]:
        parts = step.split(":")
        if parts[0] == "wait":
            r = c.call("step", {"count": int(parts[1]), "unit": "frames"}, timeout=180)
            log.append((step, r["text"][0].get("frame") if r["text"] else r))
        elif parts[0] == "tap":
            btns = parts[1].split("+"); press = int(parts[2]) if len(parts) > 2 else 4; after = int(parts[3]) if len(parts) > 3 else 30
            r = c.call("tap", {"buttons": btns, "press_frames": press, "after_frames": after}, timeout=180)
            log.append((step, (r["text"][0].get("frame") if r["text"] and isinstance(r["text"][0], dict) else str(r)[:120])))
        elif parts[0] == "shot":
            p = os.path.join(outdir, parts[1] + ".png"); r = c.call("screenshot", {"save_path": p}); log.append((step, p if not r.get("isError") else r))
        elif parts[0] == "save":
            p = os.path.join(outdir, parts[1] + ".mss"); r = c.call("save_state", {"path": p}); log.append((step, str(r.get("text"))[:160]))
        elif parts[0] == "load":
            r = c.call("load_state", {"path": os.path.abspath(parts[1])}); log.append((step, str(r.get("text"))[:160]))
        elif parts[0] == "mem":
            r = c.call("read_memory", {"memory_type": parts[1], "address": int(parts[2], 16), "length": int(parts[3], 16)}); log.append((step, str(r.get("text"))[:400]))
    for s, r in log: print(s, "->", r)
    if not keep: c.call("stop", {"launch_id": lid})
    c.close()

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3], keep=(len(sys.argv) > 4 and sys.argv[4] == "keep"))
