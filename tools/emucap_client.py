"""Minimal MCP stdio client for emucap-mcp.exe (JSON-RPC over stdin/stdout).

Usage as a library:
    c = EmucapClient(); c.start(); c.call("bootstrap", {}); c.close()
"""
import json, os, subprocess, sys, threading, queue, time

DEFAULT_EXE = r"C:\Users\Administrator\code\emucap\target\release\emucap-mcp.exe"
DEFAULT_REPO = r"C:\Users\Administrator\code\emucap"

class EmucapClient:
    def __init__(self, exe=DEFAULT_EXE, env=None):
        self.exe = exe; self.env = dict(os.environ); self.env.update(env or {})
        self.env.setdefault("EMUCAP_REPO_ROOT", DEFAULT_REPO)
        self.proc = None; self.next_id = 1; self.q = queue.Queue(); self.notes = []
    def start(self):
        self.proc = subprocess.Popen([self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=open(os.devnull if os.environ.get("EMUCAP_QUIET") else "work/emucap-stderr.log","ab"), env=self.env)
        threading.Thread(target=self._reader, daemon=True).start()
        r = self._req("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "kr-patch-client", "version": "0.1"}})
        self._notify("notifications/initialized", {})
        return r
    def _reader(self):
        for line in self.proc.stdout:
            line = line.strip()
            if not line: continue
            try: msg = json.loads(line)
            except Exception: continue
            if "id" in msg: self.q.put(msg)
            else: self.notes.append(msg)
    def _notify(self, method, params):
        self.proc.stdin.write((json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n").encode()); self.proc.stdin.flush()
    def _req(self, method, params, timeout=600):
        mid = self.next_id; self.next_id += 1
        self.proc.stdin.write((json.dumps({"jsonrpc": "2.0", "id": mid, "method": method, "params": params}) + "\n").encode()); self.proc.stdin.flush()
        t0 = time.time()
        while True:
            try: msg = self.q.get(timeout=max(0.1, timeout - (time.time() - t0)))
            except queue.Empty: raise TimeoutError(method)
            if msg.get("id") == mid: return msg
    def list_tools(self):
        return self._req("tools/list", {})
    def call(self, name, args=None, timeout=600):
        r = self._req("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)
        if "error" in r: return {"error": r["error"]}
        res = r.get("result", {})
        out = {"isError": res.get("isError", False), "text": [], "images": []}
        for c in res.get("content", []):
            if c.get("type") == "text":
                t = c["text"]
                try: out["text"].append(json.loads(t))
                except Exception: out["text"].append(t)
            elif c.get("type") == "image": out["images"].append(c)
        if res.get("structuredContent") is not None: out["structured"] = res["structuredContent"]
        return out
    def close(self):
        try: self.proc.stdin.close()
        except Exception: pass
        try: self.proc.wait(timeout=10)
        except Exception: self.proc.kill()

if __name__ == "__main__":
    c = EmucapClient(); print(json.dumps(c.start(), ensure_ascii=False)[:500])
    tl = c.list_tools()
    for t in tl.get("result", {}).get("tools", []):
        print("TOOL", t["name"], json.dumps(t.get("inputSchema", {}).get("properties", {}), ensure_ascii=False)[:600])
    print("BOOTSTRAP", json.dumps(c.call("bootstrap", {"include": ["installation", "systems"]}), ensure_ascii=False)[:3000])
    c.close()
