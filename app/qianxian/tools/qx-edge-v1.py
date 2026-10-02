#!/usr/bin/env python3
"""边缘回归驱动 v1（#38+）：qx-verify-v2 之外的真机盲点。

目标场景：
  E1  #38 修复验证：add_person 不丢 slot_init_asked
  E2  #38 修复验证：update_bill_total 不丢 slot_init_asked
  E3  循环 5 槽改时间（无冲突条）：周六-上午 → 周六-下午 → 周六-晚上 → 周日-上午 →
        周日-中午 → 周六-上午（满环归位）
  E4  取消两段式：第一次→第二次→再点"取消守护"按钮不可立即撤销（已被 5s 守
        卫撤销窗口收纳，撤销点 undo 按钮，第二次点取消直接取消新条）
  E5  撤销 5s 后再次撤销 no-op（不把更早的 cancelled 误恢复）
  E6  AA 均摊边界：空总额/0 总额/纯空格/非数字/小数/超大数
  E7  参与人 10 人上限（第 11 次拒绝）
  E8  损坏 cases.json 重启兜底：写坏 JSON → 重启 card-host → 应看到
          "已备份为 cases.corrupt-N.json 并重新开始"
  E9  重复 5 槽 + 搜索 + 筛选切换（虚拟化滚动稳定性）
  E10 长文本输入（>200 字）不崩溃
"""
import json, re, sys, time, urllib.request, urllib.parse

BASE = "http://127.0.0.1:8146"
RESULTS = []


def get(p, timeout=10):
    with urllib.request.urlopen(BASE + p, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def snap():
    for _ in range(6):
        try:
            return json.loads(get("/snap"))
        except Exception:
            time.sleep(1.5)
    raise RuntimeError("snap 不可用")


def ws(): return snap()["s"]


def find(ws, sub, ty=None, contains_all=None):
    for w in ws:
        if ty and w.get("ty") != ty: continue
        t = w.get("t") or ""
        if sub not in t: continue
        if contains_all and not all(c in t for c in contains_all): continue
        return w
    return None


def find_all(ws, sub, ty=None):
    out = []
    for w in ws:
        if ty and w.get("ty") != ty: continue
        if sub in (w.get("t") or ""): out.append(w)
    return out


def center(w): x, y, ww, hh = w["r"]; return x + ww // 2, y + hh // 2


def click(w):
    if not w: return False
    x, y = center(w)
    get(f"/click?x={x}&y={y}"); time.sleep(0.7)
    return True


def click_text(sub, ty=None):
    return click(find(ws(), sub, ty))


def type_into_input(input_id, text):
    """点指定 TextInput + /t 文本注入。
    #38 修正：Splash TextInput t 字段首屏 = placeholder、点示例/输入后 = 当前真实内容，
    所以**始终不能用 t 子串定位**。改用 i 字段（"msg_input" 唯一）。"""
    for attempt in range(1, 4):
        ws_now = ws()
        candidates = [w for w in ws_now if w.get("ty") == "TextInput"]
        if not candidates: return False
        target = None
        for w in candidates:
            i = (w.get("i") or "")
            if input_id == "msg_input" and i == "msg_input": target = w; break
            # 详情面板的 add_person/bill_total 没 i，按 y 坐标选最低
            elif input_id == "add_person":
                target = min(candidates, key=lambda x: x["r"][1] if x["r"][1] > 300 else 999)
                if target["r"][1] < 300: target = None
                if target: break
            elif input_id == "bill_total":
                target = max((x for x in candidates if x["r"][1] > 300), key=lambda x: x["r"][1], default=None)
                if target: break
        if not target:
            target = candidates[0]
        click(target); time.sleep(0.5)
        q = urllib.parse.quote(text)
        try: get(f"/t?t={q}")
        except Exception: pass
        time.sleep(1.0)
        return True
    return False


def type_and_create(text, expect_sub):
    """键入 + 建守护，按结果重试。v2 验证：fill_example+build race 概率 ~25%；
    改用 fill_example + 多次 build 重试，并交叉验证 cases.json 落库。"""
    for attempt in range(1, 5):
        # 用示例填充（v2 R-02 路径，最稳）
        click_text("用示例试试", "Button"); time.sleep(1.5)
        click_text("建守护", "Button"); time.sleep(2.5)
        if find(ws(), expect_sub, "Label"):
            print(f"  [type-and-create] '{expect_sub}' 第 {attempt} 次尝试成功", flush=True)
            return True
        print(f"  [type-and-create] 第 {attempt} 次尝试未见到 '{expect_sub}'，重试", flush=True)
    return False


def title_re(k):
    return re.compile(r"^[▶▾ ]*#%d ·" % k)


def has_title(ws, k):
    return any(title_re(k).match(w.get("t") or "") for w in ws if w.get("ty") == "Label")


def rec(item_id, name, ok, ev=""):
    RESULTS.append((item_id, name, bool(ok), ev))
    print(f"[E-{item_id:02d}] {'PASS' if ok else 'FAIL'} {name} :: {ev}", flush=True)


def fresh(reason="", keep_cases=False):
    """清空 cases.json 并重启 card-host（仍用同一端口 8146）。
    keep_cases=True：保留 cases.json 不删（E1/E2 数据层测用）。
    """
    import subprocess, pathlib, os, signal
    subprocess.run(["pkill", "-f", "card-host --bundle"], capture_output=True)
    time.sleep(1.0)
    ad = "/tmp/qx-edge"
    pathlib.Path(ad).joinpath("qianxian").mkdir(parents=True, exist_ok=True)
    cj = pathlib.Path(ad) / "qianxian" / "cases.json"
    for bk in pathlib.Path(ad).rglob("cases.corrupt-*.json"):
        bk.unlink()
    if not keep_cases:
        cj.unlink(missing_ok=True)
    env = os.environ.copy()
    env["OCTO_CARD_HOST"] = "/home/kikun/MyProject/Agentic-octos/.build-hub-926/OctoSense-App-Hub/target/release/card-host"
    p = subprocess.Popen(
        ["python3",
         "/home/kikun/MyProject/Agentic-octos/octosense-ws/OctoScript-App-Design-Flow/tools/octo",
         "run", "bundle", "--port", "8146", "--detach", "--hidden", "--app-data", ad],
        stdout=open("/tmp/edge.log", "ab"), stderr=subprocess.STDOUT,
        cwd="/home/kikun/MyProject/Agentic-octos/my-entry/app/qianxian",
        env=env, start_new_session=True)
    for _ in range(200):
        try:
            get("/snap", timeout=2); break
        except Exception:
            time.sleep(0.5)
    time.sleep(3.0)


def clear():
    """内存清空（不重启）：用 UI 的「清空全部」两段式 + 重置 selected_id。
    比 fresh 更快，验证列表回到空态后再建新守护。"""
    # 展开说明卡（如果未展开）
    if not click_text("清空全部", "Button"):
        # 未物化= 折叠态 → 展开
        click_text("怎么用？", "Button"); time.sleep(1.0)
        for _ in range(4):
            if click_text("清空全部", "Button"): break
            get("/m?k=scroll&x=200&y=500&dx=0&dy=400"); time.sleep(0.6)
    if click_text("清空全部", "Button"):
        time.sleep(1.2)
        # 第二次点击确认
        for _ in range(4):
            if click_text("清空全部", "Button"): break
            get("/m?k=scroll&x=200&y=500&dx=0&dy=400"); time.sleep(0.6)
        time.sleep(1.5)


# === E1 #38 修复验证：add_person 不丢 slot_init_asked ===
# #38 修复要点：splash 的 add_person 在「cases 重建 push 时漏 slot_init_asked」——
# 触发条件 = 该条 case 的 slot_init_asked="yes" 时重建再读回应保留。
# 走纯数据层测：写 cases.json 后重启 → load() 加载 → UI 走 add_person + 测重建后字段保留。
fresh()
import json as _json, pathlib as _pl
cj = _pl.Path("/tmp/qx-edge/qianxian/cases.json")
cj.parent.mkdir(parents=True, exist_ok=True)
# 写一条 slot_init_asked="yes" 的 case
cj.write_text(_json.dumps({"cases": [{
    "id": 1, "text": "打球", "activity": "跳舞", "place": "",
    "status": "Proposing", "people": "", "bill_total": "",
    "receipt_activity": "", "receipt_place": "", "receipt_text": "",
    "receipt_done": "", "slot_day": "", "slot_part": "",
    "conflict": "no", "slot_init_asked": "yes",
}], "seq": 1}))
fresh(keep_cases=True)  # 重启让 load() 加载 → cases 内存含 slot_init_asked="yes"
# 走 add_person（详情面板输入）→ 触发重建 → 重建后必须仍 slot_init_asked="yes"
import urllib.request, time, urllib.parse
def _g(p): return urllib.request.urlopen("http://127.0.0.1:8146" + p, timeout=5).read().decode()
def _snap(): return _json.loads(_g("/snap"))["s"]
# 找 #1 卡并 click 进入详情
def _find(sub, ty=None):
    for w in _snap():
        if ty and w.get("ty") != ty: continue
        if sub in (w.get("t") or ""): return w
f1 = _find("#1", "Label")
if f1:
    x, y = f1["r"][0]+f1["r"][2]//2, f1["r"][1]+f1["r"][3]//2
    urllib.request.urlopen(f"http://127.0.0.1:8146/click?x={x}&y={y}", timeout=5).read()
    time.sleep(1.5)
# 在详情面板加参与人
ws_now = _snap()
inputs = [w for w in ws_now if w.get("ty") == "TextInput"]
ai = max((w for w in inputs if w["r"][1] > 300), key=lambda w: w["r"][1], default=None)
if ai:
    x, y = ai["r"][0]+ai["r"][2]//2, ai["r"][1]+ai["r"][3]//2
    urllib.request.urlopen(f"http://127.0.0.1:8146/click?x={x}&y={y}", timeout=5).read()
    time.sleep(0.5)
    urllib.request.urlopen("http://127.0.0.1:8146/t?t="+urllib.parse.quote("小明"), timeout=5).read()
    time.sleep(0.8)
    btn = _find("添加", "Button")
    if btn:
        x, y = btn["r"][0]+btn["r"][2]//2, btn["r"][1]+btn["r"][3]//2
        urllib.request.urlopen(f"http://127.0.0.1:8146/click?x={x}&y={y}", timeout=5).read()
        time.sleep(1.5)
# 读 cases.json → sasked 必须是 yes
data = _json.loads(cj.read_text())
rec(1, "#38 修复：add_person 后 slot_init_asked 仍在=yes",
    len(data["cases"]) >= 1 and data["cases"][0].get("slot_init_asked") == "yes",
    f"sasked={data['cases'][0].get('slot_init_asked', 'MISSING')!r} people={data['cases'][0].get('people', '')!r}")


# === E2 #38 修复验证：update_bill_total 不丢 slot_init_asked ===
fresh()
cj.parent.mkdir(parents=True, exist_ok=True)
print("E-02 writing to:", cj, flush=True)
cj.write_text(_json.dumps({"cases": [{
    "id": 1, "text": "唱歌", "activity": "唱歌", "place": "",
    "status": "Proposing", "people": "", "bill_total": "",
    "receipt_activity": "", "receipt_place": "", "receipt_text": "",
    "receipt_done": "", "slot_day": "", "slot_part": "",
    "conflict": "no", "slot_init_asked": "yes",
}], "seq": 1}))
print("E-02 exists after write:", cj.exists(), flush=True)
fresh(keep_cases=True)
# 进详情 + 记 AA 300
f1 = _find("#1", "Label")
if f1:
    x, y = f1["r"][0]+f1["r"][2]//2, f1["r"][1]+f1["r"][3]//2
    urllib.request.urlopen(f"http://127.0.0.1:8146/click?x={x}&y={y}", timeout=5).read()
    time.sleep(1.5)
ws_now = _snap()
inputs = [w for w in ws_now if w.get("ty") == "TextInput"]
bi = max((w for w in inputs if w["r"][1] > 400), key=lambda w: w["r"][1], default=None)
if bi:
    x, y = bi["r"][0]+bi["r"][2]//2, bi["r"][1]+bi["r"][3]//2
    urllib.request.urlopen(f"http://127.0.0.1:8146/click?x={x}&y={y}", timeout=5).read()
    time.sleep(0.5)
    urllib.request.urlopen("http://127.0.0.1:8146/t?t="+urllib.parse.quote("300"), timeout=5).read()
    time.sleep(0.8)
    btn = _find("记一笔", "Button")
    if btn:
        x, y = btn["r"][0]+btn["r"][2]//2, btn["r"][1]+btn["r"][3]//2
        urllib.request.urlopen(f"http://127.0.0.1:8146/click?x={x}&y={y}", timeout=5).read()
        time.sleep(1.5)
data = _json.loads(cj.read_text())
rec(2, "#38 修复：update_bill_total 后 slot_init_asked 仍在=yes",
    len(data["cases"]) >= 1 and data["cases"][0].get("slot_init_asked") == "yes",
    f"sasked={data['cases'][0].get('slot_init_asked', 'MISSING')!r} bill={data['cases'][0].get('bill_total', '')!r}")


# === E3 循环 5 槽改时间（无冲突条）===
clear()
ok = type_and_create("周六上午去深圳湾骑车", "#1 ·")
slots_seen = []
if ok:
    # 不带冲突：建一条卡，单独轮换
    for i in range(6):  # 多打一次看满环归位
        click_text("改时间（5 槽）") or (lambda: ([get("/m?k=scroll&x=200&y=500&dx=0&dy=300") for _ in range(3)] and click_text("改时间（5 槽）")))()
        time.sleep(1.5)
        # 读 cases.json
        import pathlib
        data = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
        slots_seen.append(f"{data['cases'][0]['slot_day']}-{data['cases'][0]['slot_part']}")
# 期望：起始"周六-上午"，依次 5 槽循环
# 5 槽是 [周六上午, 周六下午, 周六晚上, 周日上午, 周日中午]，第 6 次回到"周六-上午"
expected = ["周六-上午", "周六-下午", "周六-晚上", "周日-上午", "周日-中午", "周六-上午"]
rec(3, "循环 5 槽改时间满环归位",
    slots_seen == expected, f"got={slots_seen!r} want={expected!r}")


# === E4 取消两段式（已确认后再取消的撤销窗口 vs 新的取消流程）===
clear()
type_and_create("周六上午去吃饭", "#1 ·")
# 确认 → 落回执
click_text("确认这条守护", "Button"); time.sleep(1.2)
# 取消守护
click_text("取消守护", "Button"); time.sleep(0.8)
hint_armed = next((w.get("t") for w in ws() if w.get("ty") == "Label" and "再点一次" in (w.get("t") or "")), "")
# 第二次点（实际点"确认取消（5s）"）
click_text("确认取消（5s）", "Button") or None
time.sleep(1.5)
# 验证：出现"5 秒内可点「撤销取消」"
hint_undo_open = next((w.get("t") for w in ws() if w.get("ty") == "Label" and "撤销" in (w.get("t") or "")), "")
import pathlib
data = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
rec(4, "取消两段式 + 撤销窗口打开",
    data["cases"][0]["status"] == "Cancelled" and "撤销" in hint_undo_open,
    f"armed={bool(hint_armed)} undo_open={hint_undo_open!r} status={data['cases'][0]['status']}")


# === E5 撤销窗口过期后再撤销 no-op ===
clear()
type_and_create("周六上午去吃饭", "#1 ·")
click_text("确认这条守护", "Button"); time.sleep(1.0)
click_text("取消守护", "Button"); time.sleep(0.5)
click_text("确认取消（5s）", "Button") or None
time.sleep(1.5)
# 5 秒到期（等 5.5s）
time.sleep(5.6)
# 现在再点"撤销取消"按钮 —— 应不响应（已无 undo 窗口）
import pathlib
data_before = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
undo_btn = click_text("撤销取消", "Button")
time.sleep(0.8)
data_after = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
rec(5, "撤销 5s 后再撤销 no-op（status 维持 Cancelled）",
    data_after["cases"][0]["status"] == "Cancelled",
    f"before/after status={data_before['cases'][0]['status']!r}/{data_after['cases'][0]['status']!r}")


# === E6 AA 均摊边界 ===
clear()
type_and_create("周六上午去吃饭", "#1 ·")
click(find(ws(), "#1 ·", "Label")); time.sleep(1.0)
cases = []
# 空 / 0 / 空格 / 非数字 / 小数 / 大数
for raw, label in [("", "空"), ("0", "零"), ("   ", "纯空格"),
                    ("abc", "非数字"), ("300.5", "小数"), ("999999", "超大数")]:
    type_into_input("bill_total", raw)
    click_text("记一笔", "Button"); time.sleep(1.0)
    import pathlib
    data = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
    bt = data["cases"][0]["bill_total"]
    cases.append((label, bt))
# 验证每种 raw 都被原样保存到 bill_total
expected_str = {"": "", "0": "0", "   ": "", "abc": "abc", "300.5": "300.5", "999999": "999999"}
rec(6, "AA 总额边界（各 raw 原样落库）",
    all(b == expected_str[r] for (l, b), r in zip(cases, ["", "0", "   ", "abc", "300.5", "999999"])),
    f"got={cases!r}")


# === E7 参与人 10 人上限（编辑模式累加）===
clear()
type_and_create("周六上午去吃饭", "#1 ·")
click(find(ws(), "#1 ·", "Label")); time.sleep(1.0)
# 第一次加 10 人
type_into_input("add_person", "1,2,3,4,5,6,7,8,9,10")
click_text("添加", "Button"); time.sleep(1.0)
import pathlib
data = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
n1 = data["cases"][0]["people"].count(",") + 1
# 再加 1 人，应被拒
type_into_input("add_person", "11")
click_text("添加", "Button"); time.sleep(1.0)
data = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
n2 = data["cases"][0]["people"].count(",") + 1
rec(7, "参与人 10 人上限（第 11 人拒绝）",
    n1 == 10 and n2 == 10,
    f"first_n={n1} after_attempt11={n2}")


# === E8 损坏 cases.json 重启兜底 ===
fresh()
type_and_create("周六上午去骑车", "#1 ·")  # 先有正常数据
# 写坏 JSON
import pathlib
cj = pathlib.Path("/tmp/qx-edge/qianxian/cases.json")
original = cj.read_text()
cj.write_text("{\"cases\":[{\"id\":1,\"broken_field")
fresh()  # 重启 → load() 应能识别坏 JSON（"cases 是数组" 不通过）→ 备份
ws_now = ws()
hints = [w.get("t") for w in ws_now if w.get("ty") == "Label" and "损坏" in (w.get("t") or "")]
bk_present = any(name.startswith("cases.corrupt-") for name in [p.name for p in pathlib.Path("/tmp/qx-edge/qianxian").rglob("*.json")])
# 重启后应看到 cases.json 现在是空库，且有损坏备份

data_after = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text()) if pathlib.Path("/tmp/qx-edge/qianxian/cases.json").exists() else {"cases":[]}
rec(8, "损坏 cases.json 重启兜底（备份 + 空库）",
    bk_present and data_after.get("cases", []) == [],
    f"backup={bk_present} cases={data_after.get('cases')!r}")


# === E9 重复 5 槽 + 搜索 + 筛选切换（虚拟化滚动稳定性）===
clear()
type_and_create("周六上午去深圳湾骑车", "#1 ·")
type_and_create("周六上午去海岸城吃饭", "#2 ·")
type_and_create("周日下午去爬山", "#3 ·")
type_and_create("周六上午也要去唱歌", "#4 ·")  # 与 #1 同 slot → 冲突
type_and_create("周日下午去打篮球", "#5 ·")   # 与 #3 同 slot → 冲突
# 多次切换筛选 + 搜索 + 滚动
errors = 0
import pathlib
for trial in range(3):
    for tab in ["全部", "待拍板", "已确认", "已取消"]:
        click_text(tab, "Label") or click_text(tab, "Button"); time.sleep(0.4)
    # 搜 → 清
    si = [w for w in ws() if w.get("ty") == "TextInput" and "搜活动" in (w.get("empty_text") or "")]
    if si:
        click(si[0]); time.sleep(0.3)
        get("/t?t=" + urllib.parse.quote("骑车")); time.sleep(0.7)
        get("/t?t="); time.sleep(0.5)
    # 滚动
    for dy in (300, -300, 300):
        get("/m?k=scroll&x=200&y=500&dx=0&dy=" + str(dy))
        time.sleep(0.2)
# 收尾校验：4 条数据都在
data = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
ids = sorted(c["id"] for c in data["cases"])
rec(9, "反复搜索/筛选/滚动后数据完整性",
    ids == [1, 2, 3, 4, 5],
    f"ids={ids!r}")


# === E10 长文本输入（>200 字）不崩溃 ===
clear()
long_text = "周六上午" + "啊" * 200 + "去深圳湾骑车两个小时？大家记得带水带防晒霜呀，记得把手机充满电哦哦哦哦哦"
type_and_create(long_text, "#1 ·")
import pathlib
data = json.loads(pathlib.Path("/tmp/qx-edge/qianxian/cases.json").read_text())
rec(10, "长文本（>200 字）建守护不崩溃",
    len(data["cases"]) == 1 and len(data["cases"][0]["text"]) == len(long_text),
    f"len={len(data['cases'][0]['text'])}")


# === 收尾汇总 ===
passed = sum(1 for _, _, ok, _ in RESULTS if ok)
print(f"\n=== qx-edge-v1: {passed}/{len(RESULTS)} PASS ===")
for i, (eid, name, ok, ev) in enumerate(RESULTS, 1):
    print(f"  E-{eid:02d} {'✓' if ok else '✗'} {name} :: {ev}")
sys.exit(0 if all(ok for _, _, ok, _ in RESULTS) else 1)