#!/usr/bin/env python3
"""#29 诊断：dump展开态下全部widget类型+文本，看输入行自身是否在树里。"""
import json, os, time, urllib.request, urllib.parse
BASE = os.environ.get("QX_BASE", "http://127.0.0.1:8142")
def get(path, timeout=12):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")
def snap():
    for _ in range(6):
        try: return json.loads(get("/snap"))
        except Exception: time.sleep(1.5)
    raise RuntimeError("snap unavailable")
def find(ws, sub, ty=None):
    for w in ws:
        if ty and w.get("ty") != ty: continue
        if sub in (w.get("t") or ""): return w
    return None
def center(w):
    x,y,ww,hh = w["r"]; return x+ww//2, y+hh//2
def click(ws, sub, ty=None, wait=1.6):
    w = find(ws, sub, ty)
    if not w: print(f"[click] '{sub}' NOT FOUND", flush=True); return snap()["s"]
    x,y = center(w); get(f"/click?x={x}&y={y}"); time.sleep(wait); return snap()["s"]
def click_title(ws, cid, wait=1.6):
    prefix = f"#{cid} ·"
    for w in ws:
        if w.get("ty") != "Label": continue
        t = (w.get("t") or "").strip()
        if t.startswith(prefix) or ("▶" in t and prefix in t) or ("▾" in t and prefix in t):
            x,y = center(w); get(f"/click?x={x}&y={y}"); time.sleep(wait); return snap()["s"]
    print(f"[click-title] #{cid} NOT FOUND", flush=True); return ws
d = snap(); ws = d["s"]
ws = click(ws, "用示例试试", "Button") or ws
ws = click(ws, "建守护", "Button") or ws
ws = click_title(ws, 1) or ws
time.sleep(1.0); ws = snap()["s"]
from collections import Counter
print("[TYPE-COUNTS]", dict(Counter(w.get("ty") for w in ws)), flush=True)
print("[ALL-WIDGETS]", flush=True)
for w in ws:
    print(f"  {w.get('ty'):12s} t={((w.get('t') or '')[:44])!r} r={w.get('r')}", flush=True)
print("DRIVE-DONE", flush=True)
