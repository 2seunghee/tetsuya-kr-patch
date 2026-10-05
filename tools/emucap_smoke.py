import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from emucap_client import EmucapClient
rom = os.path.abspath(sys.argv[1]); outdir = os.path.abspath(sys.argv[2]); os.makedirs(outdir, exist_ok=True)
c = EmucapClient(env={"EMUCAP_GBA_BIOS": os.path.abspath("work/bios/gba_bios.bin")}); c.start()
plan = c.call("launch_plan", {"content_path": rom, "system": "gba"})
print("PLAN", json.dumps(plan, ensure_ascii=False)[:1500])
launch = c.call("launch", {"content_path": rom, "system": "gba", "start_frozen": True}, timeout=300)
print("LAUNCH", json.dumps(launch, ensure_ascii=False)[:1500])
st = c.call("status"); print("STATUS keys", list(st["text"][0].keys()) if st["text"] and isinstance(st["text"][0], dict) else st)
s0 = st["text"][0] if st["text"] else {}
print("runtime", json.dumps(s0.get("runtime_instance"), ensure_ascii=False)[:400])
print("buttons", json.dumps(s0.get("input") or s0.get("buttons") or s0.get("button_names"), ensure_ascii=False)[:600])
for i, nframes in enumerate([120, 240, 240, 240]):
    r = c.call("step", {"count": nframes, "unit": "frames"}, timeout=120)
    sc = c.call("screenshot", {"save_path": os.path.join(outdir, f"boot_{i}.png")})
    print("step", i, json.dumps(r.get("text"), ensure_ascii=False)[:200], "shot", json.dumps(sc.get("text"), ensure_ascii=False)[:200])
print("ROMINFO", json.dumps(c.call("get_rom_info"), ensure_ascii=False)[:600])
json.dump(s0, open(os.path.join(outdir, "status.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
lid = (s0.get("runtime_instance") or {}).get("launch_id")
if len(sys.argv) > 3 and sys.argv[3] == "stop" and lid:
    print("STOP", json.dumps(c.call("stop", {"launch_id": lid}), ensure_ascii=False)[:300])
c.close()
