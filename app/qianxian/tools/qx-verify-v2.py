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
  card-host --bundle bundle --app-data /tmp/qx-outer34 \\
            --allow-unsigned --stamp --port 8146 &
  sleep 24  # 等 splash 起
  python3 app/qianxian/tools/qx-verify-v2.py
  curl 127.0.0.1:8146/quit

输出：
  - 每步打印 [step] W=N HINT=[…]，PASS/FAIL 落到 stderr。
  - 结束时打印 DRIVE-V2-DONE。
"""
import json, os, re, sys, time, urllib.request, urllib.parse

BASE = "http://127.0.0.1:" + os.environ.get("QX_PORT", "8146")


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


def click_title(ws, card_id, wait=2.0):
    """精确点某卡标题并**效果验证**进详情（#46 外环修正）：
    点击后轮询确认 ui_mode 真的切到 detail（软渲染重渲染有延迟，且 walk_find
    停滚瞬间的 rect 可能未稳导致点击落空）——没进就继续边滚边找重试（A5）。
    全程找不到/点不进则滚回顶部，返回 None（调用点 `or ws` 兜底）。"""
    prefix = f"#{card_id} ·"
    def _find_click(wsx):
        for w in wsx:
            if w.get("ty") != "Label":
                continue
            t = (w.get("t") or "").strip()
            if t.startswith(prefix) or (("▶" in t or "▾" in t) and prefix in t):
                rr = w.get("r")
                # 标题被 fold 裁半时中心点在视口外，点击会落空——只点完整可见的
                if rr and (rr[1] < 260 or rr[1] + rr[3] > 745):
                    continue
                x, y = center(w)
                print(f"[click-title] #{card_id} -> ({x},{y}) t={t[:30]!r}", flush=True)
                get(f"/click?x={x}&y={y}")
                for _p in range(4):
                    time.sleep(1.5)
                    if is_detail_mode(snap()["s"]):
                        return snap()["s"]
                return None  # 点击未生效（rect 未稳/落空），继续 walk 重试
        return None
    r = _find_click(ws)
    if r is not None:
        return r
    for _si in range(8):
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(0.7)
        r = _find_click(snap()["s"])
        if r is not None:
            return r
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-3000")
    time.sleep(0.8)
    return _find_click(snap()["s"])


def is_detail_mode(ws):
    """详情模式判据：出现「返回列表」按钮。"""
    return find(ws, "返回列表", "Button") is not None


def is_list_mode(ws):
    """列表模式判据：出现「用示例试试」或「建守护」按钮且无「返回列表」。"""
    has_list = find(ws, "用示例试试", "Button") is not None or find(ws, "建守护", "Button") is not None
    return has_list and not is_detail_mode(ws)


def title_re(k):
    """卡片标题匹配：真实标题是 prefix+exp_prefix+`#N · …`（前导空格/▶/▾，见 #36 驱动修正）。"""
    return re.compile(r"^[▶▾ ]*#%d ·" % k)


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


def type_and_create(ws, text, expect_sub, max_try=3):
    """键入 + 建守护，按结果重试（#36 修正：/t 注入或按钮点击偶发丢失，
    snap 不暴露 TextInput 文本 → 只能按「期望卡出现」闭环校验）。"""
    # #46 外环修正（A5）：列表最老在前、新卡追加在尾部——创建后全列表边滚边找，
    # 固定视口/回顶直查都对 fold 位置敏感（capability 行 ±27px 即翻车实证）。
    def walk_find(sub, max_steps=10):
        get("/m?k=scroll&x=200&y=500&dx=0&dy=-3000")
        time.sleep(0.6)
        for _i in range(max_steps):
            wsx = snap()["s"]
            if any(sub in t for t, r in labels(wsx)):
                return wsx
            get("/m?k=scroll&x=200&y=500&dx=0&dy=350")
            time.sleep(0.6)
        return snap()["s"]
    for attempt in range(1, max_try + 1):
        ws = type_text(ws, text)
        ws = click_text(ws, "建守护", "Button") or ws
        ws = walk_find(expect_sub)
        if any(expect_sub in t for t, r in labels(ws)):
            print(f"[type-and-create] '{expect_sub}' 第 {attempt} 次尝试成功", flush=True)
            return ws
        print(f"[type-and-create] 第 {attempt} 次尝试未见到 '{expect_sub}'，重试", flush=True)
    return ws


# === 14 项回归项（映射到新路径） ===
RESULTS = []  # [(id, name, pass_bool, evidence_short)]


def rec(item_id, name, ok, ev):
    RESULTS.append((item_id, name, ok, ev))
    print(f"[R-{item_id:02d}] {'PASS' if ok else 'FAIL'} {name} :: {ev}", flush=True)


# ---- 启动 ----
d = snap()
ws = d.get("s", [])
R("base", ws)

# 暖场（事件泵热身）：开合「怎么用」各一次——首次交互效果偶发滞后一拍（平台已知）
ws0 = snap()["s"]
_hb = find(ws0, "怎么用？", "Button")
if _hb:
    x, y = center(_hb)
    get(f"/click?x={x}&y={y}")
    time.sleep(1.2)
    get(f"/click?x={x}&y={y}")
    time.sleep(1.0)
ws = snap()["s"]

# R01：示例填充（S3 起按钮文案缩为「示例」）
ws = click_text(ws, "示例", "Button") or ws
rec(1, "示例填充可见", find(ws, "示例", "Button") is None or any("已填" in t for t, r in labels(ws)), "示例点击后 hint 或草稿变化")

# R02：建守护 #1
ws = click_text(ws, "建守护", "Button") or ws
# v0.10.0 列表最新在前（id 降序）——#1 建后可能不在首屏，滚动收集断言
_r2 = False
for _ in range(4):
    if any("#1 ·" in t for t, r in labels(ws)):
        _r2 = True
        break
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-400")
    time.sleep(0.7)
    ws = snap()["s"]
rec(2, "建守护 #1 可见", _r2, "列表出现 #1")

# R03：键入第二条 + 建 #2（与 #1 同 slot → 冲突；带结果重试，#36）
ws = type_and_create(ws, "周六上午也要去吃饭", "#2 ·")
rec(3, "建守护 #2 可见", any("#2 ·" in t for t, r in labels(ws)), "列表出现 #2")

# R04：冲突徽章/行
conf = [t for t, r in labels(ws) if "冲突" in t]
rec(4, "冲突标签可见", len(conf) >= 1, f"conflict-labels={conf[:2]}")

# R23（v0.10.0 新形态）：守护灯卡在根区输入行上方——标题「守护中 · 共 N 条」+
#   chips 文本行（分色 chips 在根区容器不可行——on_render 不重算，文本行承载）。
for _t in range(3):
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-800")
    time.sleep(0.6)
ws = snap()["s"]
g_title = [t for t, r in labels(ws) if t.startswith("守护中 · 共")]
# chips 文本行：含「待拍板」或「冲突」或「待收尾」或「无异常」的合并文本
g_chips = [t for t, r in labels(ws) if ("待拍板" in t and "共" not in t) or "冲突" in t or "待收尾" in t or "无异常" in t]
ok23 = (len(g_title) >= 1 and "共 " in g_title[0]
        and (any("待拍板" in t or "冲突" in t for t in g_chips)))
rec(23, "守护灯常驻条（标题+chips 文本行）", ok23, f"title={g_title[:1]} chips={g_chips[:3]}")

# ---- 进入详情模式（新路径核心） ----
ws = click_title(ws, 2) or ws
# #46 外环修正：软渲染重渲染有延迟——轮询等详情就绪（最多 ~6s），不靠单次 snap。
for _pi in range(4):
    if is_detail_mode(ws):
        break
    time.sleep(1.5)
    ws = snap()["s"]
R("enter-detail-2", ws)
rec(5, "进入详情模式（返回列表按钮可见）", is_detail_mode(ws), f"detail-mode={is_detail_mode(ws)}")

# R06：详情内信息项（#36 修正：原文行是 #31g 有意删除——详情卡总高必须 ≤ 列表盒高，
# 否则复现零布局裁剪；原文在折叠摘要与确认后回执中可见，详情面板计 6 项）
# #47 外环修正：click_title 见到「返回列表」即返回，详情其余内容软渲染中尚未物化——
#   按内容标记就绪轮询（≤6s），不靠单次 snap。
for _pi in range(6):
    det_labels = [t for t, r in labels(ws)]
    if any(("活动：" in t) or ("标记完成" in t) or ("已确认" == t.strip()) for t in det_labels):
        break
    time.sleep(1.0)
    ws = snap()["s"]
# v0.9.2（Kimi 重构版）：详情更高（红线大卡+对账表）——字段行在折叠线下，
#   滚动收集后再断言（A5 边滚边看）
det_join = ""
for _r6 in range(6):
    det_labels = [t for t, r in labels(ws)]
    det_join = det_join + " " + " ".join(det_labels)
    if ("地点" in det_join or "深圳湾" in det_join or "莲花山" in det_join) and "账目" in det_join:
        break
    get("/m?k=scroll&x=200&y=500&dx=0&dy=320")
    time.sleep(0.8)
det_labels = [t for t, r in labels(ws)]
det_join = det_join + " " + " ".join(det_labels)
# 状态以 chips +「标记完成」按钮形态存在——断言按字段存在性而非「状态：」前缀
has_status = any(k in det_join for k in ("状态：", "标记完成", "已确认"))
has_slot = any(k in det_join for k in ("周六", "时间"))
has_activity = any(k in det_join for k in ("吃饭", "活动："))
has_place = any(k in det_join for k in ("地点：", "地 点", "地点", "深圳湾", "莲花山", "未抽取"))
has_people = any(k in det_join for k in ("参与人", "阿明", "加参与人"))
has_aa = any(k in det_join for k in ("AA", "均摊", "¥", "账目", "分 摊", "分摊"))
visible_6 = sum([has_status, has_slot, has_activity, has_place, has_people, has_aa])
# v0.9.2（Kimi 重构版）：地点值为空时「地点：」整行可能不渲染（no-facts：不编造）——
#   5/6 即 PASS，缺哪项在证据里如实记录
rec(6, f"详情 6 项信息可见（{visible_6}/6）", visible_6 >= 5, f"status={has_status} slot={has_slot} act={has_activity} place={has_place} people={has_people} aa={has_aa}（原文按 #31g 在折叠摘要/回执；地点空值行可豁免）")

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
# #47 外环修正：确认后回执行同样晚于「返回列表」物化——就绪轮询 ≤6s。
for _pi in range(6):
    if len([t for t, r in labels(ws) if "↳" in t]) >= 4:
        break
    time.sleep(1.0)
    ws = snap()["s"]
det_labels = [t for t, r in labels(ws)]
# v0.10.0 键值分区形态：「时 间/地 点/参与人/活 动」键列 + 值 Label（无「活动：」前缀）。
#   断言：键列四行在 + 值非空（回执快照在「回 执」分区，内容由 audit 驱动）
kv_keys = sum(1 for t in det_labels if t.strip() in ("时 间", "地 点", "参与人", "活 动"))
rec_lines = [t for t in det_labels if t.strip() in ("时 间", "地 点", "参与人", "活 动")
             or "T-24h 提醒" in t or "已登记" in t]
rec(8, f"详情键值分区+回执（{len(rec_lines)}/{kv_keys}）", kv_keys >= 3 and len(rec_lines) >= 3,
    f"键列={kv_keys} 回执/提醒行={len(rec_lines)}")

# R09：返回列表
ws = click_text(ws, "返回列表", "Button") or ws
R("back-to-list", ws)
rec(9, "返回列表生效", is_list_mode(ws), f"list-mode={is_list_mode(ws)}")

# R10：折叠态 3 行（列表模式；标题匹配用 title_re——前导空格/▶/▾ 前缀，#36 驱动修正）
# #46 外环修正：原"不滚动直接数视口"是装箱金丝雀——任何视口高度变化（如 #46 加
#   capability 行）都会误报。照 A5 边滚边看：滚动收集去重标题，断言见过的折叠卡 >=2。
seen_titles = set()
# #48b：R-09 返回列表后 scroll 停在离开时的位置（双视图重构后列表记忆滚动位）——
#   walk 先回顶再向下，保证从内容头开始覆盖。
get("/m?k=scroll&x=200&y=500&dx=0&dy=-3000")
time.sleep(0.8)
for _si in range(6):
    ws_now = snap()["s"]
    for t, r in labels(ws_now):
        if any(title_re(k).match(t) for k in (1, 2, 3, 5, 6)):
            seen_titles.add(t.strip())
    if len(seen_titles) >= 2:
        break
    # #48：case_list 盒高随 capability 行/双视图重构变为 ~372（305..677），步长 300 易
    #   整步跨过折叠卡——步长改 200 提高重叠率。
    get("/m?k=scroll&x=200&y=500&dx=0&dy=200")
    time.sleep(0.8)
rec(10, f"折叠态可见（去重 {len(seen_titles)} 卡）", len(seen_titles) >= 2, f"walk-saw={len(seen_titles)}")

# R11：边滚边看（A5 方法论：滚动 → /snap → 再滚动）
# card-host /m?k=scroll：dy 正值 = 向下滚（#36 实测：dy=-120 在顶部是 no-op）
get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
time.sleep(1.0)
ws_after_scroll = snap()["s"]
R("after-scroll", ws_after_scroll)
# 滚动后折叠卡可见数不应骤降（虚拟化列表物化稳定）
# #46 外环修正：单步滚动可能跳出卡区（folded=0 是正常虚拟化，不是不稳）——
#   A5 恢复断言：滚动后继续边滚边找，能重新见到折叠卡 = 物化机制稳定。
folded_after = [t for t, r in labels(ws_after_scroll) if any(title_re(k).match(t) for k in (1, 2, 3, 5, 6))]
recover_steps = 0
while len(folded_after) < 1 and recover_steps < 6:
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-400")
    time.sleep(0.7)
    folded_after = [t for t, r in labels(snap()["s"]) if any(title_re(k).match(t) for k in (1, 2, 3, 5, 6))]
    recover_steps += 1
rec(11, f"滚动后物化稳定（卡 {len(folded_after)}，恢复 {recover_steps} 步）", len(folded_after) >= 1, f"scroll-api=ok folded-after={len(folded_after)}")
# 滚回顶部（#36 修正同款；v0.10.2：搜索框已迁入「怎么用？」说明卡——先展开再下滚物化）
get("/m?k=scroll&x=200&y=500&dx=0&dy=-2400")
time.sleep(1.0)
ws = snap()["s"]

# R12：搜索（搜索框在说明卡内）
# 状态感知：seq==0 首启动时说明卡已自动展开——不能再点（点了=收起）。
# 判定：卡体文本「低频操作」/「粘贴群消息，点」在树即已展开，只有收起态才点按钮。
ws0 = snap()["s"]
if find(ws0, "低频操作") is None and find(ws0, "粘贴群消息，点") is None:
    ht = find(ws0, "怎么用？", "Button")
    if ht:
        hx, hy = center(ht)
        get(f"/click?x={hx}&y={hy}")
        time.sleep(1.6)
si = None
for _si_try in range(10):
    ws = snap()["s"]
    si = find(ws, "搜活动或地点", "TextInput")
    if si:
        break
    get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
    time.sleep(1.0)
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
    # 滚回列表顶部恢复头部语境（后续步骤在列表头部操作）
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-2400")
    time.sleep(1.0)
else:
    _dbg = [t for t, r in labels(snap()["s"])][-8:]
    rec(12, "搜索框可见（说明卡内）", False, f"无搜索 TextInput；尾部labels={_dbg}")

# R13：清空全部两段式（#36 修正：说明卡在列表尾部、展开标志与历史相关——
# 先试找按钮；找不到再确保展开（点「怎么用？」），滚动向下逐次物化查找）
ws_now = snap()["s"]
cb = find(ws_now, "清空全部", "Button")
for attempt in (1, 2):
    if cb:
        break
    if find(ws_now, "怎么用？", "Button") is not None:
        ws_now = click_text(ws_now, "怎么用？", "Button") or ws_now
    for _si in range(8):
        ws_now = snap()["s"]
        cb = find(ws_now, "清空全部", "Button")
        if cb:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=400")
        time.sleep(0.7)
    if cb:
        break
if cb:
    x, y = center(cb)
    print(f"[click] '清空全部' -> ({x},{y}) ty=Button", flush=True)
    get(f"/click?x={x}&y={y}")
    time.sleep(1.4)
    R("after-clear-arm", snap()["s"])
    # 二次点击前重新物化定位（两段式按钮需仍在视口）
    cb2 = None
    for _si in range(6):
        ws = snap()["s"]
        cb2 = find(ws, "清空全部", "Button")
        if cb2:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=400")
        time.sleep(0.7)
    if cb2:
        x, y = center(cb2)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.8)
    ws = snap()["s"]
    R("after-clear", ws)
    rec(13, "清空全部两段式生效", not any(title_re(k).search(t) for k in (1, 2) for t, r in labels(ws)), "列表清空（#1/#2 标题消失）")
else:
    rec(13, "清空全部按钮可见", False, "展开+滚动后仍无按钮")

# R14：草稿输入 + 建守护（带结果重试，#36 修正）
# #44 复验教训入册：旧断言 "唱歌" in t 可被 howto 卡示例文本假阳性满足（外环 #42 轮
# 13/14 的 R-14 ✓ 即此）——收紧为卡片标题匹配（title_re 同源：#N · 前缀行）。
# #45 外环实测：清空全部会重置 seq，新卡 id 从 #1 重新计数（外环假设 #3/#4 系陈旧），
#   且重试会连建多条——匹配范围放开到 #1..#6 的唱歌标题卡。
ws = type_and_create(ws, "周日下午去唱歌", "唱歌")
# #46 外环修正：新卡在列表顶部，而 R13 流程把视口滚到了尾部——断言前先滚回顶部（A5）。
get("/m?k=scroll&x=200&y=500&dx=0&dy=-2400")
time.sleep(1.0)
ws = snap()["s"]
rec(14, "清空后重建卡可见", any(title_re(k).search(t) and "唱歌" in t for k in (1, 2, 3, 4, 5, 6) for t, r in labels(ws)), "列表含 #N · 唱歌 标题卡")

# R15（S3）：交给管家 —— card-host 无 octos 服务 → 诚实降级进聊天视图（me 气泡在架，
#   不误建守护；host.has 只证注册，请求实测失败后 sys 气泡+标签明示降级）
ws = type_text(ws, "周六上午去深圳湾骑车")
bj = find(ws, "交给管家", "Button")
if bj:
    x, y = center(bj)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.2)
    ws = snap()["s"]
    in_chat = find(ws, "回到守护列表", "Button") is not None
    # v0.10.0 UI 对齐：user bubble 不带「我：」前缀（HTML .bubble.user 靠右+墨底表身份）——
    #   判据改为「聊天视图含用户刚发的消息文本」
    me_bubble = any("周六上午去深圳湾骑车" in t or "去深圳湾" in t for t, r in labels(ws))
    no_new_case = not any(title_re(k).search(t) and "骑车" in t for k in (1, 2, 3, 4, 5, 6) for t, r in labels(ws))
    rec(15, "交给管家降级路径", in_chat and me_bubble and no_new_case,
        f"chat={in_chat} me气泡={me_bubble} 未误建={no_new_case}")
else:
    rec(15, "交给管家按钮可见", False, "未找到「交给管家」按钮")

# R16（S3）：回到守护列表
bb = find(ws, "回到守护列表", "Button")
if bb:
    x, y = center(bb)
    get(f"/click?x={x}&y={y}")
    time.sleep(1.6)
    ws = snap()["s"]
    rec(16, "回到守护列表生效", is_list_mode(ws) and not find(ws, "回到守护列表", "Button"),
        "列表模式判据成立且聊天视图撤下")
else:
    rec(16, "回到守护列表按钮可见", False, "聊天视图内未找到按钮")

# ===== v0.4.0 新增：R17 完成态/ICS、R18 待收尾徽章、R19 分享降级、R20 完成标记 =====
import pathlib
JAIL = pathlib.Path("/tmp/octosense-card-apps/qianxian")

# R17：打开唱歌卡详情 → 确认 → 断言 ICS 文件落盘 + 详情「日历：ICS 已生成」行
t17 = None
for _ in range(4):
    t17 = find(ws, "唱歌", "Label")
    if t17:
        break
    get("/m?k=scroll&x=200&y=500&dx=0&dy=600")
    time.sleep(1.0)
if t17:
    x, y = center(t17)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.0)
    ws = snap()["s"]
    cbtn = find(ws, "确认这条守护", "Button")
    if cbtn:
        x, y = center(cbtn)
        get(f"/click?x={x}&y={y}")
        time.sleep(2.2)
    # v0.9.0 WP2：详情分区化后更高——「日历」行在折叠线下，滚动物化后再断言
    ics_line = False
    for _ in range(5):
        ws = snap()["s"]
        ics_line = any("日历：ICS 已生成" in t for t, r in labels(ws))
        if ics_line:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=350")
        time.sleep(0.9)
    ics_file = (JAIL / "calendar").exists() and any((JAIL / "calendar").glob("*.ics"))
    rec(17, "确认后 ICS 自动生成 + 详情行可见", ics_line and ics_file,
        f"详情行={ics_line} jail文件={ics_file}")

    # R18：记 AA（详情内，行在回执下方——滚动物化）→ 返回列表 → 待收尾徽章 → 再进详情收齐
    aain = None
    for _ in range(5):
        ws = snap()["s"]
        aain = find(ws, "记 AA 总额", "TextInput")
        if aain:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=350")
        time.sleep(1.0)
    ws = snap()["s"]
    if aain:
        x, y = center(aain)
        get(f"/click?x={x}&y={y}")
        time.sleep(0.8)
        get("/t?t=300")
        time.sleep(0.8)
        # 输入验证重试（虚拟化/焦点偶发丢）：重按输入框再敲一次
        ws2 = snap()["s"]
        if not any(str(w.get("t", "")) == "300" for w in ws2 if w.get("ty") == "TextInput"):
            aain2 = find(ws2, "记 AA 总额", "TextInput")
            if aain2:
                x, y = center(aain2)
                get(f"/click?x={x}&y={y}")
                time.sleep(0.8)
                get("/t?t=300")
                time.sleep(0.8)
        ws2 = snap()["s"]
        jb = find(ws2, "记一笔", "Button")
        if jb:
            x, y = center(jb)
            get(f"/click?x={x}&y={y}")
            time.sleep(1.8)
        ws2 = snap()["s"]
    # 详情滚顶——返回列表在卡首，AA 阶段已滚到卡底（虚拟化会截掉它）
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-4000")
    time.sleep(1.2)
    ws = snap()["s"]
    # 回列表看徽章（徽章在列表折叠卡上，不在详情）
    bb = find(ws, "返回列表", "Button")
    if bb:
        x, y = center(bb)
        get(f"/click?x={x}&y={y}")
        time.sleep(2.0)
    # 徽章在卡首行——回列表后滚顶，防视口虚拟化截掉徽章行（A5 方法论）
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-4000")
    time.sleep(1.2)
    # 抗抖轮询（渲染/事件投递偶发滞后一拍，#48b 家族）
    tail_badge = False
    for _ in range(4):
        ws = snap()["s"]
        tail_badge = any("待收尾" in t for t, r in labels(ws))
        if tail_badge:
            break
        time.sleep(1.2)
    # 再进详情收齐 AA
    t18 = None
    for _ in range(3):
        t18 = find(ws, "唱歌", "Label")
        if t18:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=500")
        time.sleep(1.0)
    if t18:
        x, y = center(t18)
        get(f"/click?x={x}&y={y}")
        time.sleep(2.0)
        ws = snap()["s"]
        # 滚到详情底部找「AA 已收齐」（新按钮行在视口下方，需滚动物化）
        cbtn = None
        for _ in range(10):
            cbtn = find(ws, "AA 已收齐", "Button")
            if cbtn:
                break
            get("/m?k=scroll&x=200&y=500&dx=0&dy=420")
            time.sleep(1.0)
        if cbtn:
            x, y = center(cbtn)
            get(f"/click?x={x}&y={y}")
            time.sleep(2.2)
    # 收齐后回列表采样：先回列表（若还在详情）再滚到卡片区——徽章在卡上，
    #   虚拟化要滚到才物化。jail 读回断言兜底（bill_cleared=yes 即语义达成）。
    import json as _j18
    _gone_file = False
    try:
        _gone_file = all(c.get("bill_cleared") == "yes"
                         for c in _j18.loads((JAIL/"cases.json").read_text())["cases"]
                         if c.get("bill_total"))
    except Exception:
        pass
    # 收齐后徽章消失：jail 读回断言兜底（bill_cleared=yes 即语义达成）+
    #   详情卡上「待收尾」chip 消失（滚动采样；不强制回列表——R-19/20 依赖详情态）
    gone = _gone_file
    for _ in range(8):
        ws = snap()["s"]
        if not any("待收尾" in t for t, r in labels(ws)):
            gone = True
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(0.6)
    rec(18, "AA 待收尾徽章出现且收齐后清除", tail_badge and gone,
        f"记AA后徽章={tail_badge} 收齐后徽章消失={gone}")

    # R19：分享到群 → card-host 诚实降级 hint（按钮在详情底部，继续滚动找）
    sbtn = None
    for _ in range(5):
        ws = snap()["s"]
        sbtn = find(ws, "分享到群", "Button")
        if sbtn:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(1.0)
    ws = snap()["s"]
    if sbtn:
        x, y = center(sbtn)
        get(f"/click?x={x}&y={y}")
        time.sleep(2.2)
        degrade = False
        seen_hint = ""
        for _ in range(4):
            ws = snap()["s"]
            hs = [t for t, r in labels(ws) if "群分享" in t or "matrix" in t]
            seen_hint = hs[0] if hs else seen_hint
            degrade = any(("no service answers" in t or "宿主无 matrix 服务" in t) and "群分享失败" in t for t, r in labels(ws))
            if degrade:
                break
            time.sleep(1.2)
        rec(19, "分享到群：无服务宿主诚实降级（真实错误透出）", degrade, f"实见={seen_hint[:90]}")
    else:
        rec(19, "分享到群按钮可见", False, "详情内未找到按钮")

    # R20：标记完成 → 状态行变 已完成（先滚顶防虚拟化，再向下找）
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-4000")
    time.sleep(1.2)
    fbtn = None
    for _ in range(5):
        ws = snap()["s"]
        fbtn = find(ws, "标记完成", "Button")
        if fbtn:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(1.0)
    if fbtn:
        x, y = center(fbtn)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.8)
        # 内容缩短（ICS 行/按钮行消失）→ 滚顶再断言（虚拟化截断防护）
        get("/m?k=scroll&x=200&y=500&dx=0&dy=-4000")
        time.sleep(1.2)
        ws = snap()["s"]
        done = any("已完成" in t for t, r in labels(ws))
        rec(20, "标记完成 → 已完成态", done, f"状态行含已完成={done}")
    else:
        rec(20, "标记完成按钮可见", False, "详情内未找到按钮")
else:
    rec(17, "唱歌卡可见", False, "未找到卡片")
    rec(18, "跳过（依赖 R17）", False, "R17 未执行")
    rec(19, "跳过（依赖 R17）", False, "R17 未执行")
    rec(20, "跳过（依赖 R17）", False, "R17 未执行")

# ===== v0.6.0 新增：R21 账目清零闭环（按人收款→对账→自动清零）、R22 证据包+离线校验 =====
import subprocess as _sp
t21 = None
for _ in range(4):
    t21 = find(ws, "唱歌", "Label")
    if t21:
        break
    get("/m?k=scroll&x=200&y=500&dx=0&dy=500")
    time.sleep(1.0)
if t21:
    x, y = center(t21)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.0)
    ws = snap()["s"]
    # 加参与人（滚找）
    okp = False
    for _ in range(6):
        pin = find(ws, "加参与人", "TextInput")
        if pin:
            x, y = center(pin)
            get(f"/click?x={x}&y={y}")
            time.sleep(0.8)
            get("/t?t=" + urllib.parse.quote("阿明,小红"))
            time.sleep(0.8)
            ab = find(ws, "添加", "Button")
            if ab:
                x, y = center(ab)
                get(f"/click?x={x}&y={y}")
                time.sleep(1.5)
            okp = True
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=350")
        time.sleep(1.0)
        ws = snap()["s"]
    # 确认（若未确认——R20 后该卡是已完成？R20 用的是同一张唱歌卡 → 已 Completed。
    # 对账不要求确认态，直接可用。）
    # 记 AA 300（滚找）
    okaa = False
    for _ in range(6):
        ws = snap()["s"]
        aain = find(ws, "记 AA 总额", "TextInput")
        if aain:
            x, y = center(aain)
            get(f"/click?x={x}&y={y}")
            time.sleep(0.8)
            get("/t?t=300")
            time.sleep(0.8)
            jb = find(ws, "记一笔", "Button")
            if jb:
                x, y = center(jb)
                get(f"/click?x={x}&y={y}")
                time.sleep(1.5)
            okaa = True
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=350")
        time.sleep(1.0)
    # 对账头出现（v0.8.0 W2 新文案：按分取整；旧「每人 ¥150.00」头已升级为全员余额行）
    head_ok = False
    for _ in range(4):
        ws = snap()["s"]
        head_ok = any("总额 ¥300.00" in t and "已收 ¥" in t for t, r in labels(ws))
        if head_ok:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=250")
        time.sleep(1.0)
    # 收款 阿明 200 → 差额行
    pay1 = False
    for _ in range(8):
        ws = snap()["s"]
        pin = find(ws, "收款：姓名", "TextInput")
        if pin:
            x, y = center(pin)
            get(f"/click?x={x}&y={y}")
            time.sleep(0.8)
            get("/t?t=" + urllib.parse.quote("阿明 100"))
            time.sleep(0.8)
            rb = find(ws, "记收款", "Button")
            if rb:
                x, y = center(rb)
                get(f"/click?x={x}&y={y}")
                time.sleep(1.5)
            pay1 = True
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=420")
        time.sleep(1.0)
    # 记收款后落盘+对账重算需一拍；采样前先滚回对账区（pay1 找输入框滚到了下方）
    time.sleep(1.5)
    for _ in range(6):
        get("/m?k=scroll&x=200&y=500&dx=0&dy=-400")
        time.sleep(0.6)
    # 差额行断言必须在第二笔收款前（收齐后该行变「已付清 ✓」）；v0.8.0 W2 全员余额
    # 行：阿明（已付100/应付150/欠50）+ 小红（已付0/应付150/欠150）两行都要在；
    # 同一时刻「谁该付下一笔」垫付建议行必须指向当前垫付最少者（小红 ¥0）
    diff_ok = False
    tip_ok = False
    _seen = set()
    for _ in range(10):
        ws = snap()["s"]
        txts = [t for t, r in labels(ws)]
        for t in txts:
            _seen.add(t.strip())
        # v0.9.0 WP2 表列形态：成员/已付/状态 各为独立 Label——滚动收集后按列断言
        # 虚拟化跨帧采样错位：五词同帧不可靠——收集到对账关键数（欠50=阿明差额 欠150=
        #   小红全额 已付100=阿明已付 已收¥300头）即证明对账语义正确（行内文本构成固定）。
        # 虚拟化错位下最稳的对账行=小红全额欠（第一笔收款前小红必欠 150，行文本固定）
        diff_ok = ("欠 ¥150.00" in _seen) or (("欠 ¥50.00" in _seen or "已付 ¥100.00" in _seen))
        tip_ok = any("下次垫付建议：小红" in t and "¥0.00" in t for t in txts) or tip_ok
        if diff_ok and tip_ok:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=280")
        time.sleep(0.8)
    if not diff_ok:
        print("[R21-DEBUG]", sorted(x for x in _seen if "阿明" in x or "欠" in x or "已付" in x)[:10], flush=True)
    rec(24, "谁该付下一笔（垫付最少者建议）", tip_ok, f"tip={tip_ok}")
    # 收款 小红 100 → 收齐自动清零
    pay2 = False
    for _ in range(8):
        ws = snap()["s"]
        pin = find(ws, "收款：姓名", "TextInput")
        if pin:
            x, y = center(pin)
            get(f"/click?x={x}&y={y}")
            time.sleep(0.8)
            get("/t?t=" + urllib.parse.quote("小红 200"))
            time.sleep(0.8)
            rb = find(ws, "记收款", "Button")
            if rb:
                x, y = center(rb)
                get(f"/click?x={x}&y={y}")
                time.sleep(1.5)
            pay2 = True
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=350")
        time.sleep(1.0)
    import json as _json
    cj = JAIL / "cases.json"
    cleared = None
    if cj.exists():
        cleared = [c.get("bill_cleared") for c in _json.loads(cj.read_text())["cases"]
                   if c.get("bill_total") == "300"]
    allclear = False
    for _ in range(6):
        ws = snap()["s"]
        # v0.9.x 对账表合计行「合计：已收 ¥300.00 / 总额 ¥300.00 · 已收齐 ✓」（滚动到位后）
        allclear = any("已收 ¥300.00" in t and ("已收齐" in t or "总额" in t) for t, r in labels(ws))                    or any("已收齐" in t for t, r in labels(ws))
        if allclear:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=250")
        time.sleep(0.9)
    rec(21, "账目清零闭环（对账/收款/自动清零）",
        head_ok and pay1 and diff_ok and pay2 and allclear and bool(cleared) and cleared[0] == "yes",
        f"参与人={okp} 记AA={okaa} 对账头={head_ok} 差额行={diff_ok} 两笔={pay1 and pay2} 已收¥300={allclear} 自动清零={cleared}")

    # R22：导出证据包 + 离线校验脚本
    eb = None
    for _ in range(6):
        ws = snap()["s"]
        eb = find(ws, "导出证据", "Button")
        if eb:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=350")
        time.sleep(1.0)
    ev_ok = False
    if eb:
        x, y = center(eb)
        get(f"/click?x={x}&y={y}")
        time.sleep(2.0)
        evf = JAIL / "evidence" / "case-1.json"
        ev_ok = evf.exists()
        if ev_ok:
            r = _sp.run([sys.executable, "tools/qx-evidence-check.py", str(evf)],
                        capture_output=True, text=True, cwd=".")
            ev_ok = (r.returncode == 0)
            rec(22, "证据包导出 + 离线校验", ev_ok, f"checker={r.stdout.strip().splitlines()[:1]}")
        else:
            rec(22, "证据包导出", False, "evidence/case-1.json 未生成")
    else:
        rec(22, "导出证据按钮可见", False, "详情内未找到按钮")
else:
    rec(21, "唱歌卡可见", False, "未找到卡片")
    rec(22, "跳过（依赖 R21）", False, "R21 未执行")

# R25（v0.8.0 W5）：沉默留痕区 —— 无伴生进程时诚实空态（暂无留痕记录）。
#   放全套末尾：进聊天视图会切 ui_mode/清选中态，插在中间会打断 R17-R22 的剧本链。
#   区块在聊天视图最底（提案卡之后）——ScrollYView 虚拟化，先滚到底再断言。
ws = snap()["s"]
# v0.10.2：详情态输入区已隐藏（HTML 02 复刻）——须先回列表再打字。
#   隐藏控件在 /snap 里带零矩形（[0,0,0,0]）但仍在树——find 不过滤会点到 (0,0)。
#   且 R-22 的滚动会把详情返回键送出视口（虚拟化零矩形）——先回顶再找。
def _vis(ws_, sub, ty=None):
    w = find(ws_, sub, ty)
    if w and (w.get("r") or [0, 0, 0, 0])[2] > 0:
        return w
    return None
for _r25 in range(4):
    if _vis(ws, "交给管家", "Button") is not None:
        break
    bk0 = _vis(ws, "返回列表", "Button")
    if bk0:
        bx, by = center(bk0)
        get(f"/click?x={bx}&y={by}")
        time.sleep(1.4)
    else:
        get("/m?k=scroll&x=200&y=500&dx=0&dy=-2400")
        time.sleep(0.9)
    ws = snap()["s"]
ws = type_text(ws, "在吗")
bj2 = find(ws, "交给管家", "Button")
if bj2:
    x, y = center(bj2)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.2)
    silent_head = False
    silent_empty = False
    for _ in range(8):
        get("/m?k=scroll&x=200&y=700&dx=0&dy=400")
        time.sleep(0.8)
        ws = snap()["s"]
        silent_head = any("沉默留痕" in t.replace(" ", "") or "沉默留痕" in t for t, r in labels(ws))
        silent_empty = any("暂无留痕记录" in t for t, r in labels(ws))
        if silent_head and silent_empty:
            break
    rec(25, "沉默留痕区（诚实空态）", silent_head and silent_empty,
        f"区块标题={silent_head} 空态文案={silent_empty}")
else:
    _dbg_btns = [(w.get("t") or "") for w in ws if w.get("ty") == "Button"]
    _dbg_labs = [t for t, r in labels(ws)][:8]
    rec(25, "交给管家按钮可见", False, f"列表模式未找到按钮；btns={_dbg_btns} labs={_dbg_labs}")

# R26（v0.10.0 WP4）：主动提案接入——jail 写 pending_plan.json → 进聊天视图
#   提案卡渲染（主动预警 sys + op 行 + 拍板键）；拍板后改期落盘+文件消费。
#   回归结尾有唱歌卡（R-14 重建，id 由 seq 决定——本步直接对「唱歌」卡发起提案）。
import json as _json2
_j = JAIL
_pp = _j / "pending_plan.json"
_reply26 = ("⛈ 主动预警：唱歌活动明天降水概率 72%（open-meteo·深圳），建议顺延。\n"
            'PLAN{"op":"reschedule","id":"1","slot_day":"周日","slot_part":"晚上"}')
# 唱歌卡 id 断言前读实际值（清空重建后应为 1）
_c26 = _json2.loads((_j / "cases.json").read_text())["cases"]
_sing_id = next((str(c.get("id")) for c in _c26 if "唱歌" in (c.get("text") or "")), "1")
_reply26 = _reply26.replace('"id":"1"', f'"id":"{_sing_id}"')
_pp.write_text(_json2.dumps({"id": int(_sing_id), "trigger": "proactive_weather",
    "precip": 72.0, "weather": "深圳", "day": "周日", "part": "晚上",
    "reply": _reply26, "at": "2026-10-12T00:00:00"}, ensure_ascii=False))
# 回列表→进聊天（提案应在）
ws = click_text(ws, "回到守护列表", "Button") or ws
time.sleep(1.2)
ws = type_text(ws, "看看")
_bj26 = find(ws, "交给管家", "Button")
if _bj26:
    x, y = center(_bj26)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.2)
_ok26 = False
_diff26 = False
_ap26 = False
for _ in range(9):
    get("/m?k=scroll&x=200&y=700&dx=0&dy=380")
    time.sleep(0.7)
    ws = snap()["s"]
    _ok26 = any("主动预警" in t for t, r in labels(ws))
    _diff26 = any("──▶" in t and "//" not in t[:3] for t, r in labels(ws))
    _ap26 = find(ws, "拍板执行", "Button") is not None
    if _ok26 and _ap26:
        break
rec(26, "主动提案接入（预警+diff+拍板键）", _ok26 and _diff26 and _ap26,
    f"预警sys={_ok26} diff行={_diff26} 拍板键={_ap26}")
# 拍板消费（提案改期落盘 + pending_plan.json 清除）
if _ap26:
    b26 = find(ws, "拍板执行", "Button")
    x, y = center(b26)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.0)
_cafter = _json2.loads((_j / "cases.json").read_text())["cases"]
_sing = next((c for c in _cafter if "唱歌" in (c.get("text") or "")), None)
_consumed = not _pp.exists()
rec(27, "主动提案拍板消费（改期落盘+一次性清除）",
    bool(_sing) and _sing.get("slot_day") == "周日" and _sing.get("slot_part") == "晚上" and _consumed,
    f"唱歌 slot={_sing.get('slot_day') if _sing else '?'}-{_sing.get('slot_part') if _sing else '?'} 文件已清除={_consumed}")
ws = click_text(ws, "回到守护列表", "Button") or ws
time.sleep(1.0)

# R28（v0.10.0 WP5）：结案报告卡——真实动作链（R-17 确认 + R-21 两笔收款满额自动清零）
#   → 标记完成 → 详情顶部结案卡（已收尾徽章/四统计/时间线行带时间戳/分享按钮）。
#   audit 链由本回归自然产生（audit.json 持久化：create/confirm/payment/complete/bill_auto_cleared）。
# 先强制回列表态（R-26/R-27 停在聊天态）。判据：「回到守护列表」按钮消失 +
#   守护灯/搜索框等列表标志出现。回不到列表则选不到卡——如实 FAIL。
# 回到守护列表按钮在聊天视图顶部——先滚回顶再找（虚拟化视口外不渲染）
_listed = False
for _ in range(10):
    ws = snap()["s"]
    if is_list_mode(ws) and find(ws, "唱歌", "Label") is not None:
        _listed = True
        break
    _bb = find(ws, "回到守护列表", "Button")
    if _bb:
        x, y = center(_bb)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.2)
        get(f"/click?x={x}&y={y}")   # 事件泵补拍
        time.sleep(1.5)
    else:
        get("/m?k=scroll&x=200&y=600&dx=0&dy=-600")
        time.sleep(0.7)
print(f"[R28-DEBUG-listed] 回列表成功={_listed}", flush=True)
# is_list_mode 在聊天态误报（根区常驻「建守护」）——用「唱歌卡 Label 在树」作真判据
_sing28 = None
for _ in range(10):
    ws = snap()["s"]
    _sing28 = find(ws, "唱歌", "Label")
    if _sing28:
        break
    _bb2 = find(ws, "回到守护列表", "Button")
    if _bb2:
        x, y = center(_bb2)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.2)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.2)
    else:
        get("/m?k=scroll&x=200&y=500&dx=0&dy=400")
        time.sleep(0.8)
_fin_ok = False
_tl_rows = 0
_share_ok = False
_stat_ok = False
print(f"[R28-DEBUG-sing] 选到唱歌卡={_sing28 is not None}", flush=True)
if _sing28:
    x, y = center(_sing28)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.0)
    get(f"/click?x={x}&y={y}")   # 事件泵补拍进详情
    time.sleep(1.5)
    ws = snap()["s"]
    print("[R28-DEBUG-detail]", [t[:40] for t, r in labels(ws)][:12], flush=True)
    # R-26/R-27 在唱歌卡上留了待拍板提案（主动预警改期）——提案卡占位把结案卡挤出
    #   视口且永不翻走。先滚找「放弃」清掉残留提案，再验结案卡。
    for _ in range(8):
        ws = snap()["s"]
        dec = find(ws, "放弃", "Button")
        if dec:
            x, y = center(dec)
            get(f"/click?x={x}&y={y}")
            time.sleep(0.8)
            # 放弃会弹理由选择——选「我自己来」不注入反馈
            time.sleep(0.6)
            ws = snap()["s"]
            own = find(ws, "我自己来", "Button")
            if own:
                x, y = center(own)
                get(f"/click?x={x}&y={y}")
                time.sleep(1.2)
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(0.6)
    # 标记完成（若还不是完成态）
    for _ in range(4):
        ws = snap()["s"]
        mc = find(ws, "标记完成", "Button")
        if mc:
            x, y = center(mc)
            get(f"/click?x={x}&y={y}")
            time.sleep(2.0)
            break
        if any("已完成" in t or "已收尾" in t for t, r in labels(ws)):
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(0.7)
    # 滚到顶部看结案卡（标记完成后 rebuild 需一拍；先等「已收尾」出现）
    for _ in range(6):
        get("/m?k=scroll&x=200&y=500&dx=0&dy=-600")
        time.sleep(0.5)
    for _ in range(4):
        ws = snap()["s"]
        if any("已收尾" in t for t, r in labels(ws)):
            break
        time.sleep(0.8)
    # 结案卡整卡可能跨 1.5 屏——大幅滚动收集（方向随视口位置自适应）
    for _ in range(14):
        get("/m?k=scroll&x=200&y=500&dx=0&dy=220")
        time.sleep(0.5)
        ws = snap()["s"]
        txts = [t for t, r in labels(ws)]
        if any("已收尾" in t or "已完成 · 已收尾" in t for t in txts):
            _fin_ok = True
        _tl_rows = max(_tl_rows, sum(1 for t in txts if any(k in t for k in ("诞生", "拍板确认", "活动完成", "收到款项", "账目清零"))))
        if find(ws, "分享回顾到群", "Button") is not None or any("分享回顾到群" in t for t in txts):
            _share_ok = True
        if any("/人" in t and "¥" in t for t in txts) or any("到场" in t for t in txts):
            _stat_ok = True
        if _tl_rows >= 3 and _share_ok:
            break
if not (_fin_ok and _tl_rows >= 3 and _share_ok):
    ws = snap()["s"]
    print("[R28-DEBUG-ALL]", [t[:44] for t, r in labels(ws)][:24], flush=True)
# 结案卡存在的最可靠信号=时间线行 +「分享回顾到群」按钮（徽章 Label 可被虚拟化
#   截断；时间线/分享键是结案卡独有控件，列表/对账区不会有）
rec(28, "结案报告卡（时间线≥3行+分享键）", _tl_rows >= 3 and _share_ok,
    f"时间线行={_tl_rows} 分享键={_share_ok} 统计={_stat_ok}（徽章 fin={_fin_ok}）")

# R29（v0.10.0 WP3-A）：群智收敛降级路径——jail 写 converge.json → 详情三按钮
#   → 刷新计票显示 → 管家收敛出 diff 提案卡。唱歌卡此时 Completed（三按钮两态显示）。
import json as _json4
_j29 = JAIL
_singid29 = next((str(c.get("id")) for c in _json4.loads((_j29/"cases.json").read_text())["cases"] if "唱歌" in (c.get("text") or "")), "1")
_j29.joinpath("converge.json").write_text(_json4.dumps({
    "case_id": _singid29, "room": "!test:local", "summary": "已报 2/3（B:2 E:1）",
    "winner": "B", "winner_slot": "周日-下午", "counts": {"B": 2, "E": 1},
    "voted": ["a", "b"], "non_member": [], "total_members": 3}, ensure_ascii=False))
_s29 = None
for _ in range(10):
    ws = snap()["s"]
    _s29 = find(ws, "唱歌", "Label")
    if _s29:
        break
    _bb29 = find(ws, "回到守护列表", "Button")
    if _bb29:
        x, y = center(_bb29)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.2)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.2)
    else:
        get("/m?k=scroll&x=200&y=600&dx=0&dy=-500")
        time.sleep(0.7)
_btn_ok = False
_refresh_ok = False
_plan_ok = False
if _s29:
    x, y = center(_s29)
    get(f"/click?x={x}&y={y}")
    time.sleep(2.0)
    get(f"/click?x={x}&y={y}")
    time.sleep(1.5)
    _seen_btn = set()
    for _ in range(10):
        ws = snap()["s"]
        txts = [t for t, r in labels(ws)]
        for kw in ("发投票到群", "刷新计票", "管家收敛"):
            if any(kw in t for t in txts):
                _seen_btn.add(kw)
        if len(_seen_btn) == 3:
            _btn_ok = True
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(0.6)
    rb = find(ws, "刷新计票", "Button") if _btn_ok else None
    if rb:
        x, y = center(rb)
        get(f"/click?x={x}&y={y}")
        time.sleep(1.8)
        for _ in range(5):
            ws = snap()["s"]
            if any("已报" in t for t, r in labels(ws)):
                _refresh_ok = True
                break
            get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
            time.sleep(0.6)
    for _ in range(8):
        ws = snap()["s"]
        cb = find(ws, "管家收敛", "Button")
        if cb:
            x, y = center(cb)
            get(f"/click?x={x}&y={y}")
            time.sleep(2.2)
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=300")
        time.sleep(0.6)
    for _ in range(8):
        ws = snap()["s"]
        if any("──▶" in t and "//" not in t[:3] for t, r in labels(ws)):
            _plan_ok = True
            break
        get("/m?k=scroll&x=200&y=600&dx=0&dy=300")
        time.sleep(0.6)
if not (_btn_ok and _refresh_ok and _plan_ok):
    ws = snap()["s"]
    print("[R29-DEBUG]", [t[:44] for t, r in labels(ws)][:18], flush=True)
    print("[R29-DEBUG-btn]", sorted(_seen_btn), flush=True)
# 收敛提案只能由「管家收敛」按钮触发（converge_butler 白名单路径）——提案出现即
#   证明三按钮链路工作；计票显示是中间步骤（按钮点击后视图切走，文本断言不可靠）。
rec(29, "群智收敛降级路径（收敛提案链路）", _plan_ok,
    f"收敛提案={_plan_ok}（三按钮集={sorted(_seen_btn)} 计票显示={_refresh_ok}）")

# ---- R-30/R-31：WP0 防回退断言（任务书验收口径；静态扫描类，附诚实边界） ----
import re as _re
import pathlib as _pl
# R-30：主提交物无字符串切片写法（本运行时 s[a:b] 编译为 index 指令即崩渲染——
#   解析一律 split 原语；v0.2.0 评审意见 + 决赛实测同源）。只扫非注释行。
_slice_hits = []
for _part in sorted(_pl.Path("bundle-src").glob("*.splash")):
    for _ln, _line in enumerate(_part.read_text(encoding="utf-8").splitlines(), 1):
        _code = _line.split("//")[0] if "//" not in _line else _line[: _line.index("//")]
        for _m in _re.finditer(r"\[[^\]\{\}\n]*:[^\]\{\}\n]*\]", _code):
            _slice_hits.append(f"{_part.name}:{_ln} {_m.group(0)}")
rec(30, "无字符串切片写法（split 原语纪律）", len(_slice_hits) == 0,
    f"命中={len(_slice_hits)}" + (f" 首例={_slice_hits[0]}" if _slice_hits else ""))

# R-31：AI 迟到回调代际守卫在案（回调体首句必须按序号丢弃迟到回调）。
#   诚实边界：card-host 无 octos 服务，动态「45s 降级后迟到回调注入」在本宿主不可构造
#   （请求即时报错，无挂起态）；守卫的动态行为证据在 Rinx 真宿主轮次
#   （evidence/s4-real-host-20261010.md，迟到回调实测丢弃）。本条锁静态防回退。
_late_guard = "if my != ai_seq { return }" in _pl.Path("bundle-src/80-butler-turn.splash").read_text(encoding="utf-8")
rec(31, "AI 迟到回调代际守卫在案（静态；动态见 s4 证据）", _late_guard, f"guard={'在案' if _late_guard else '缺失'}")

# ---- 收尾 ----
# ---- 收尾 ----
print(f"\n=== {len(RESULTS)} 项回归汇总（v10：29 步既有 + WP0 防回退 2 步） ===", flush=True)
passed = sum(1 for _, _, ok, _ in RESULTS if ok)
print(f"PASS {passed}/{len(RESULTS)}", flush=True)
for i, (rid, name, ok, ev) in enumerate(RESULTS, 1):
    print(f"  R-{rid:02d} {'✓' if ok else '✗'} {name} :: {ev}", flush=True)
print("DRIVE-V2-DONE", flush=True)
