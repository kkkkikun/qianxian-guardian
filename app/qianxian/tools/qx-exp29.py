#!/usr/bin/env python3
"""#29 最小实验驱动：建1条 -> 展开 -> 断言 时间/活动/地点/原文 四section是否出现。
端口由 BASE 环境变量决定（默认8142）。输出 EXP-[PASS|FAIL] + Label清单。
"""
import json, sys, os, time, urllib.request, urllib.parse
BASE = os.environ.get("QX_BASE", "http://127.0.0.1:8142")
def get(path, timeout=12):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")
def snap():
    for _ in range(6):
        try: return json.loads(get("/snap"))
        except Exception: time.sleep(1.5)
    raise RuntimeError("snap unavailable")
def labels(ws):
    return [(w.get("t") or "", w.get("r")) for w in ws if w.get("ty") == "Label" and (w.get("t") or "").strip()]
def find(ws, sub, ty=None):
    for w in ws:
        if ty and w.get("ty") != ty: continue
        if sub in (w.get("t") or ""): return w
    return None
def center(w):
    x,y,ww,hh = w["r"]; return x+ww//2, y+hh//2
def click(ws, sub, ty=None, wait=1.6):
    w = find(ws, sub, ty)
    if not w:
        print(f"[click] '{sub}' NOT FOUND", flush=True); return snap()["s"]
    x,y = center(w)
    print(f"[click] '{sub}' -> ({x},{y})", flush=True)
    get(f"/click?x={x}&y={y}"); time.sleep(wait)
    return snap()["s"]
def click_title(ws, cid, wait=1.6):
    prefix = f"#{cid} ·"
    for w in ws:
        if w.get("ty") != "Label": continue
        t = (w.get("t") or "").strip()
        if t.startswith(prefix) or ("▶" in t and prefix in t) or ("▾" in t and prefix in t):
            x,y = center(w)
            print(f"[click-title] #{cid} -> ({x},{y}) t={t[:40]!r}", flush=True)
            get(f"/click?x={x}&y={y}"); time.sleep(wait)
            return snap()["s"]
    print(f"[click-title] #{cid} NOT FOUND", flush=True); return ws

d = snap(); ws = d["s"]
print(f"[base] W={len(ws)}", flush=True)
ws = click(ws, "用示例试试", "Button") or ws
ws = click(ws, "建守护", "Button") or ws
ws = click_title(ws, 1) or ws
time.sleep(1.0); ws = snap()["s"]
ts = [t for t,r in labels(ws)]
print("[LABELS]", flush=True)
for t,r in labels(ws): print(f"  - {t[:60]!r} r={r}", flush=True)
print(f"[W] total={len(ws)}", flush=True)
need = ["时间","活动","地点","原文"]
got = {k: any(k==t.strip() or t.strip()==k for t,r in labels(ws)) for k in need}
print("[SECTIONS]", got, flush=True)
missing = [k for k,v in got.items() if not v]
if not missing:
    print("EXP-PASS: 四section全出现", flush=True)
else:
    print(f"EXP-FAIL: 缺 {missing}", flush=True)
print("DRIVE-DONE", flush=True)
