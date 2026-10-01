#!/usr/bin/env python3
"""外环独立真机复验：覆盖内环#27未验证项 + 两个附带发现。
端口 8143，全新 jail（/tmp/qx-outer），与 8141 基线隔离。
用法：由 bash 单命令内启动 card-host 后运行本脚本，最后 /quit。
"""
import json, sys, time, urllib.request, urllib.parse

BASE = "http://127.0.0.1:8143"

def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def snap():
    for _ in range(5):
        try:
            return json.loads(get("/snap"))
        except Exception:
            time.sleep(1.5)
    raise RuntimeError("snap 不可用")

def labels(ws):
    return [(w.get("t") or "", w.get("r")) for w in ws if w.get("ty") == "Label" and (w.get("t") or "").strip()]

def find(ws, sub, ty=None):
    for w in ws:
        if ty and w.get("ty") != ty:
            continue
        t = w.get("t") or ""
        if sub in t:
            return w
    return None

def center(w):
    x, y, ww, hh = w["r"]
    return x + ww // 2, y + hh // 2

def click_text(ws, sub, ty=None, wait=1.6):
    w = find(ws, sub, ty)
    if not w:
        return None
    x, y = center(w)
    print(f"[click] '{sub}' -> ({x},{y}) ty={w.get('ty')} r={w.get('r')}", flush=True)
    get(f"/click?x={x}&y={y}")
    time.sleep(wait)
    return snap()["s"]

def click_title(ws, card_id, wait=1.6):
    """精确点某卡标题：找以 '#N ·' 开头的 Label（避免点中冲突行里的引用）。"""
    prefix = f"#{card_id} ·"
    for w in ws:
        if w.get("ty") != "Label":
            continue
        t = (w.get("t") or "").strip()
        if t.startswith(prefix) or ("▶" in t and prefix in t) or ("▾" in t and prefix in t):
            x, y = center(w)
            print(f"[click-title] #{card_id} -> ({x},{y}) t={t[:30]!r}", flush=True)
            get(f"/click?x={x}&y={y}")
            time.sleep(wait)
            return snap()["s"]
    print(f"[click-title] #{card_id} NOT FOUND", flush=True)
    return None

def click_gesture(ws, idx, wait=1.6):
    """按 GestureView 顺序点（筛选胶囊：0=all,1=Proposing,2=Confirmed,3=Cancelled）。
    不按 Label 文字点——Label 无独立命中区，会误中全屏 Splash。"""
    gs = [w for w in ws if w.get("ty") == "GestureView"]
    if idx >= len(gs):
        print(f"[click-gesture] idx={idx} OOB (n={len(gs)})", flush=True)
        return None
    w = gs[idx]
    x, y = center(w)
    print(f"[click-gesture] idx={idx} -> ({x},{y}) r={w.get('r')}", flush=True)
    get(f"/click?x={x}&y={y}")
    time.sleep(wait)
    return snap()["s"]

def receipts(ws):
    return [t for t, r in labels(ws) if "↳" in t]

def hint_of(ws):
    out = []
    for t, r in labels(ws):
        if any(k in t for k in ("已建", "已确认", "已取消", "已撤销", "筛选", "再点一次", "已清空",
                                "改时间", "时段", "已载入", "已填示例", "已展开", "已折叠", "回执",
                                "清空确认", "清空未完成", "撤销窗口")):
            out.append(t)
    return out

def R(step, ws):
    print(f"[{step}] W={len(ws)} HINT={hint_of(ws)}", flush=True)

def type_text(ws, text, wait=2.0):
    """点输入框聚焦 + /t 键入（messages 端点语义为追加 OR 替换均可，返回后重抓 snap 并报告输入框内容）。"""
    mi = find(ws, "粘贴群消息", "TextInput") or find(ws, "搜活动", "TextInput")
    boxes = [w for w in ws if w.get("ty") == "TextInput"]
    box = boxes[0] if boxes else None
    if box:
        x, y = center(box)
        get(f"/click?x={x}&y={y}"); time.sleep(0.8)
    q = urllib.parse.quote(text)
    try:
        resp = get(f"/t?t={q}")
    except Exception as e:
        print("[/t-FAIL]", e, flush=True)
        return snap()["s"]
    time.sleep(wait)
    return snap()["s"]

d = snap(); R("base", d.get("s", []))
ws = d["s"]

# 1. 示例 -> 建守护 #1
ws = click_text(ws, "用示例试试", "Button") or ws; R("fill-ex", ws)
ws = click_text(ws, "建守护", "Button") or ws; R("add1", ws)

# 2. 键入第二条不同文本 -> 建 #2（与 #1 同 slot 周六-上午 -> 互标冲突）
ws = type_text(ws, "周六上午也要去吃饭"); R("typed2", ws)
ws = click_text(ws, "建守护", "Button") or ws; R("add2", ws)

# 3. 冲突检查：徽章与冲突行
conf = [t for t, r in labels(ws) if "冲突" in t]
print("[conflict-labels]", conf, flush=True)

# 4. 精确展开 #2（click_title 按标题前缀，避免点中冲突行引用）
ws = click_title(ws, 2) or ws; R("expand2", ws)

# 5. 确认（作用于最新/选中 = #2）
ws = click_text(ws, "确认这条守护", "Button") or ws; R("confirm", ws)

# 6. 切筛选 -> 已确认（制造 i!=j 条件：filtered=[1], i=0, j=1）
# 注意：筛选胶囊是 GestureView，按顺序点 idx=2（0=all,1=Proposing,2=Confirmed,3=Cancelled）
ws = click_gesture(ws, 2) or ws; R("filter-conf", ws)
# 筛选后卡片为折叠态（W 会掉）——必须先点开 #2 再查回执，否则检查失格
ws = click_title(ws, 2) or ws; R("expand2-under-conf", ws)
rec = receipts(ws)
print("[receipt-under-confirmed-filter]", rec if rec else "MISSING", flush=True)

# 7. 对照：切回全部，查回执
ws = click_gesture(ws, 0) or ws; R("filter-all", ws)
# 若 #2 未展开则精确点开
if not any("▾" in t and "#2" in t for t, r in labels(ws)):
    ws = click_title(ws, 2) or ws; R("re-expand2", ws)
rec2 = [t for t, r in labels(ws) if "↳" in t or "回执" in t]
print("[receipt-under-all-filter]", rec2 if rec2 else "MISSING", flush=True)

# 8. 怎么用？展开 -> 改时间按钮是否可达
ws = click_text(ws, "怎么用？", "Button") or ws; R("howto", ws)
has_slot_btn = find(ws, "改时间") is not None
print("[slot-btn-visible]", has_slot_btn, flush=True)
if has_slot_btn:
    ws = click_text(ws, "改时间", "Button") or ws; R("cycle-slot", ws)

# 9. 搜索键入：点搜索框 -> /t
si = find(ws, "搜活动或地点", "TextInput")
print("[search-input]", bool(si), flush=True)
if si:
    x, y = center(si)
    get(f"/click?x={x}&y={y}"); time.sleep(1.0)
    try:
        q = urllib.parse.quote("骑车")
        print("[/t-resp]", get(f"/t?t={q}")[:200], flush=True)
    except Exception as e:
        print("[/t-FAIL]", e, flush=True)
    time.sleep(1.5)
    ws = snap()["s"]; R("search-typed", ws)

# 10. 清空全部两段式（附带发现 case_counts）
cb = find(ws, "清空全部", "Button")
print("[clear-btn-visible]", bool(cb), flush=True)
if cb:
    ws = click_text(ws, "清空全部", "Button") or ws; R("clear-1st", ws)
    ws = click_text(ws, "清空全部", "Button") or ws; R("clear-2nd", ws)

print("DRIVE-DONE", flush=True)
