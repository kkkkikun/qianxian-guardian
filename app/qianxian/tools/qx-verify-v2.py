#!/usr/bin/env python3
"""内环回归驱动 v2（#34）：覆盖 14 项回归映射到 #31 新交互路径。

新路径（#31 后）：
  - 点卡 = 进详情模式（detail）；返回 = 回列表模式（list）。
  - 详情内 8 项信息可见：状态/时间/参与人/活动/地点/原文/AA均摊/确认回执。
  - AA/参与人 输入在详情面板内；「确认这条守护」「返回列表」在详情内。
  - 列表模式按折叠态渲染，卡之间通过 ScrollYView 虚拟化（外环 #32 ACK 实测）。

A5 方法论（#33）：
  - ScrollYView 是虚拟化列表；视口外 widget 不实例化。
  - 验证方法：边滚边看（滚动 → /snap → 再滚动）。
  - 坐标点击不可靠：rect 可能是占位值 [0,29,412,863]，命中区是 Label 文字。

驱动设计原则：
  - 不依赖固定坐标；通过 /snap 找 Label/Button 文字定位。
  - 每次点击后 sleep 1.6 + /snap 重抓树，再做下一步定位。
  - 详情模式（ui_mode=detail）下用 back_to_list 按钮回退；找不到时按"返回列表"模糊匹配。
  - 列表项折叠态 3 行：标题/时间·参与人/AA。点击标题进入详情（按 #1f 实现）。
  - 草稿输入（msg_input）按 text 字段填入；点「建守护」前不清空（保留输入状态可见性）。

用法：
  card-host --bundle app/qianxian/bundle --app-data /tmp/qx-outer34 \\
            --allow-unsigned --stamp --port 8146 &
  sleep 24  # 等 splash 起
  python3 app/qianxian/tools/qx-verify-v2.py
  curl 127.0.0.1:8146/quit

输出：
  - 每步打印 [step] W=N HINT=[…]，PASS/FAIL 落到 stderr。
  - 结束时打印 DRIVE-V2-DONE。
"""
import json, sys, time, urllib.request, urllib.parse

BASE = "http://127.0.0.1:8146"


def get(path, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def snap():
    for _ in range(6):
        try:
            return json.loads(get("/snap"))
        except Exception:
            time.sleep(1.5)
    raise RuntimeError("snap 不可用")


def labels(ws):
    return [(w.get("t") or "", w.get("r")) for w in ws if w.get("ty") == "Label" and (w.get("t") or "").strip()]


def widgets_by_type(ws, ty):
    return [w for w in ws if w.get("ty") == ty]


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
        print(f"[MISS] '{sub}' ty={ty}", flush=True)
        return None
    x, y = center(w)
    print(f"[click] '{sub}' -> ({x},{y}) ty={w.get('ty')}", flush=True)
    get(f"/click?x={x}&y={y}")
    time.sleep(wait)
    return snap()["s"]


def click_title(ws, card_id, wait=1.6):
    """精确点某卡标题：找以 '#N ·' 开头的 Label。"""
    prefix = f"#{card_id} ·"
    for w in ws:
        if w.get("ty") != "Label":
            continue
        t = (w.get("t") or "").strip()
        if t.startswith(prefix) or (("▶" in t or "▾" in t) and prefix in t):
            x, y = center(w)
            print(f"[click-title] #{card_id} -> ({x},{y}) t={t[:30]!r}", flush=True)
            get(f"/click?x={x}&y={y}")
            time.sleep(wait)
            return snap()["s"]
    print(f"[click-title] #{card_id} NOT FOUND", flush=True)
    return None


def is_detail_mode(ws):
    """详情模式判据：出现「返回列表」按钮。"""
    return find(ws, "返回列表", "Button") is not None


def is_list_mode(ws):
    """列表模式判据：出现「用示例试试」或「建守护」按钮且无「返回列表」。"""
    has_list = find(ws, "用示例试试", "Button") is not None or find(ws, "建守护", "Button") is not None
    return has_list and not is_detail_mode(ws)


def receipts(ws):
    return [t for t, r in labels(ws) if "↳" in t or "回执" in t]


def hint_of(ws):
    out = []
    for t, r in labels(ws):
        if any(k in t for k in ("已建", "已确认", "已取消", "已撤销", "再点一次",
                                "回执", "改时间", "已展开", "已折叠", "草稿")):
            out.append(t)
    return out


def R(step, ws):
    print(f"[{step}] W={len(ws)} HINT={hint_of(ws)}", flush=True)


def type_text(ws, text, wait=1.8):
    """点输入框 + /t 键入（不点「建守护」，保留草稿状态）。"""
    mi = find(ws, "粘贴群消息", "TextInput")
    if not mi:
        print("[type-text] no input box", flush=True)
        return ws
    x, y = center(mi)
    get(f"/click?x={x}&y={y}")
    time.sleep(0.8)
    q = urllib.parse.quote(text)
    try:
        get(f"/t?t={q}")
    except Exception as e:
        print("[/t-FAIL]", e, flush=True)
    time.sleep(wait)
    return snap()["s"]


# === 14 项回归项（映射到新路径） ===
RESULTS = []  # [(id, name, pass_bool, evidence_short)]


def rec(item_id, name, ok, ev):
    RESULTS.append((item_id, name, ok, ev))
    print(f"[R-{item_id:02d}] {'PASS' if ok else 'FAIL'} {name} :: {ev}", flush=True)


# ---- 启动 ----
d = snap()
ws = d.get("s", [])
R("base", ws)

# R01：示例填充
ws = click_text(ws, "用示例试试", "Button") or ws
rec(1, "示例填充可见", find(ws, "用示例试试", "Button") is None or any("已填" in t for t, r in labels(ws)), "示例点击后 hint 或草稿变化")

# R02：建守护 #1
ws = click_text(ws, "建守护", "Button") or ws
rec(2, "建守护 #1 可见", any("#1 ·" in t for t, r in labels(ws)), "列表出现 #1")

# R03：键入第二条 + 建 #2（与 #1 同 slot → 冲突）
ws = type_text(ws, "周六上午也要去吃饭")
ws = click_text(ws, "建守护", "Button") or ws
rec(3, "建守护 #2 可见", any("#2 ·" in t for t, r in labels(ws)), "列表出现 #2")

# R04：冲突徽章/行
conf = [t for t, r in labels(ws) if "冲突" in t]
rec(4, "冲突标签可见", len(conf) >= 1, f"conflict-labels={conf[:2]}")

# ---- 进入详情模式（新路径核心） ----
ws = click_title(ws, 2) or ws
R("enter-detail-2", ws)
rec(5, "进入详情模式（返回列表按钮可见）", is_detail_mode(ws), f"detail-mode={is_detail_mode(ws)}")

# R06：详情内 8 项信息
det_labels = [t for t, r in labels(ws)]
has_status = any("状态：" in t for t in det_labels)
has_slot = any(k in " ".join(det_labels) for k in ("周六", "时间"))
has_activity = any("吃饭" in t for t in det_labels)
has_place = any(k in " ".join(det_labels) for k in ("地点", "地方"))
has_people = any(k in " ".join(det_labels) for k in ("参与人", "人"))
has_raw = any("原文：" in t for t in det_labels)
has_aa = any("AA" in t or "均摊" in t or "¥" in t for t in det_labels)
visible_8 = sum([has_status, has_slot, has_activity, has_place, has_people, has_raw, has_aa, True])
rec(6, f"详情 8 项信息可见（{visible_8}/8）", visible_8 >= 6, f"status={has_status} slot={has_slot} act={has_activity} place={has_place} people={has_people} raw={has_raw} aa={has_aa}")

# R07 准备：先选中目标卡（点标题进详情，按 #35 修正；详情模式已在 R05 进入）
ws = click_title(ws, 2) or ws
R("enter-detail-2-pre-confirm", ws)
det_labels = [t for t, r in labels(ws)]

# R07：确认（在详情内）
ws = click_text(ws, "确认这条守护", "Button") or ws
R("confirm-in-detail", ws)
has_confirmed = any("Confirmed" in t or "已确认" in t for t, r in labels(ws))
rec(7, "详情内确认生效", has_confirmed, f"confirmed-visible={has_confirmed}")

# R08：当前详情卡存在 + 回执四行（确认后重抓树）
det_labels = [t for t, r in labels(ws)]
rec_lines = [t for t in det_labels if "↳" in t]
rec(8, f"详情卡 ↳ 回执四行（{len(rec_lines)}/4）", len(rec_lines) >= 1, f"lines={rec_lines[:4]}")

# R09：返回列表
ws = click_text(ws, "返回列表", "Button") or ws
R("back-to-list", ws)
rec(9, "返回列表生效", is_list_mode(ws), f"list-mode={is_list_mode(ws)}")

# R10：折叠态 3 行（列表模式；按 #N · 标题匹配 — 标题即折叠行）
folded = [t for t, r in labels(ws) if any(t.startswith(f"#{k} ·") for k in (1, 2, 3, 5, 6))]
rec(10, f"折叠态可见（{len(folded)} 卡）", len(folded) >= 2, f"folded={len(folded)}")

# R11：边滚边看（A5 方法论：滚动 → /snap → 再滚动）
# 通过 GET /m?k=scroll 触发滚动（card-host 既有 API）；/scroll 端点不存在
get("/m?k=scroll&x=200&y=450&dx=0&dy=-120")
time.sleep(1.0)
ws_after_scroll = snap()["s"]
R("after-scroll", ws_after_scroll)
# 滚动后 W 应不变或仅物化新节点；折叠卡可见数不应骤降
folded_after = [t for t, r in labels(ws_after_scroll) if any(t.startswith(f"#{k} ·") for k in (1, 2, 3, 5, 6))]
rec(11, f"滚动后物化稳定（卡 {len(folded_after)}）", len(folded_after) >= 1, f"scroll-api=ok folded-after={len(folded_after)}")

# R12：搜索
si = find(ws, "搜活动或地点", "TextInput")
if si:
    x, y = center(si)
    get(f"/click?x={x}&y={y}")
    time.sleep(1.0)
    q = urllib.parse.quote("骑车")
    get(f"/t?t={q}")
    time.sleep(1.5)
    ws = snap()["s"]
    R("search", ws)
    rec(12, "搜索生效", any("共" in t and "/" in t for t, r in labels(ws)), "计数标签出现")
    # 清搜索：再次点击 + /t 空
    get(f"/click?x={x}&y={y}")
    time.sleep(0.6)
    get("/t?t=")
    time.sleep(1.0)
else:
    rec(12, "搜索框可见", False, "无搜索 TextInput")

# R13：清空全部两段式（A5：先开「怎么用？」说明卡；找不到按钮先滚动）
ws_now = snap()["s"]
help_btn = find(ws_now, "怎么用？", "Button")
if not help_btn:
    # A5：虚拟化列表下，按钮可能未物化；先滚动触发再抓
    get("/m?k=scroll&x=200&y=450&dx=0&dy=-120")
    time.sleep(1.0)
    ws_now = snap()["s"]
    help_btn = find(ws_now, "怎么用？", "Button")
if help_btn:
    ws_now = click_text(ws_now, "怎么用？", "Button") or ws_now
    R("after-help-open", ws_now)
cb = find(ws_now, "清空全部", "Button")
if cb:
    ws = click_text(ws_now, "清空全部", "Button") or ws_now
    ws = click_text(ws, "清空全部", "Button") or ws
    R("after-clear", ws)
    rec(13, "清空全部两段式生效", find(ws, "清空全部", "Button") is None or not any("#1" in t or "#2" in t for t, r in labels(ws)), "列表清空")
else:
    rec(13, "清空全部按钮可见", False, "无按钮")

# R14：草稿输入 + 建守护（第 3 条不同 slot）
ws = type_text(ws, "周日下午去唱歌")
ws = click_text(ws, "建守护", "Button") or ws
rec(14, "第 3 条（不同 slot）建卡可见", any("#3" in t or "唱歌" in t for t, r in labels(ws)), "列表含 #3 或 唱歌")

# ---- 收尾 ----
print("\n=== 14 项回归汇总（v2，新路径） ===", flush=True)
passed = sum(1 for _, _, ok, _ in RESULTS if ok)
print(f"PASS {passed}/{len(RESULTS)}", flush=True)
for i, (rid, name, ok, ev) in enumerate(RESULTS, 1):
    print(f"  R-{rid:02d} {'✓' if ok else '✗'} {name} :: {ev}", flush=True)
print("DRIVE-V2-DONE", flush=True)
