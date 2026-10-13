#!/usr/bin/env python3
"""WP1 双实例牵线 e2e（palpo 双账号真实房）：agent × agent 群体协调全链。

组织者端（card-host app 真驱动 UI）建守护→确认→发投票到群（card-host 无 matrix 服务，
按 WP3-A 降级设计：app 把投票卡文案填进输入框，本脚本读回文案由客户端真发入房——
协议文案与 app 同源）→ 成员端伴生进程（qx-member-agent.py）自治投票（含顺延理由）
→ 组织端归票桥（qx-converge-bridge.py）写 converge.json → app「刷新计票」→「管家收敛」
→ 改期 diff 提案卡 → 拍板 → cases.json 落盘新时段。
追加：成员手动改投（Outbox）→ 归票 latest-wins 幂等，胜项翻转断言。
全链无人类输入字符（拍板点击除外）。

前置：palpo 在线（./palpo-ctl.sh start）+ test-accounts.json 双账号。
用法：python3 tools/qx-wp1-e2e.py  （自带 card-host 生命周期；端口 8147 防冲突）
退出码 0=全过。证据落 /tmp/qx-wp1-*/ 与控制台输出。
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
WS = ROOT.parent
sys.path.insert(0, str(ROOT / "app" / "guardian"))
sys.path.insert(0, str(ROOT / "tools"))
from guardian.matrix import MatrixClient  # noqa: E402

PORT = 8147
# card-host 的 jail 是按 app id 固定的（无 --jail 旗标）——与回归同路径
ORG_JAIL = pathlib.Path("/tmp/octosense-card-apps/qianxian")
MEM_JAIL = pathlib.Path("/tmp/qx-wp1-member")
CH = WS / "repos/OctoSense-App-Hub/target/release/card-host"

ACC = json.loads((WS / "test-accounts.json").read_text())
HS = ACC["homeserver"]
A = ACC["accounts"][0]  # 组织者
B = ACC["accounts"][1]  # 成员

FAILS = []


def ok(name, cond, ev=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" :: {ev}" if ev else ""), flush=True)
    if not cond:
        FAILS.append(name)


def http(path, timeout=8):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def snap():
    return json.loads(http("/snap?all=1"))["s"]


def find(ws, sub, ty=None):
    for w in ws:
        if w.get("ty") == "Splash":
            continue
        r = w.get("r") or [0, 0, 0, 0]
        if r[2] <= 0:
            continue
        if sub in (w.get("t") or "") and (ty is None or w.get("ty") == ty):
            return w
    return None


def click(w, wait=1.4):
    x = w["r"][0] + w["r"][2] // 2
    y = w["r"][1] + w["r"][3] // 2
    http(f"/click?x={x}&y={y}")
    time.sleep(wait)


def type_text(text):
    q = urllib.parse.quote(text)
    http(f"/t?t={q}")
    time.sleep(0.8)


def main():
    for d in (ORG_JAIL, MEM_JAIL):
        subprocess.run(["rm", "-rf", str(d)], check=False)
        d.mkdir(parents=True, exist_ok=True)

    # 成员端日历：周六-上午已有确认守护（逼出「首选撞期→顺延 B」用例）
    (MEM_JAIL / "cases.json").write_text(json.dumps({"seq": 1, "cases": [
        {"id": 1, "text": "周六上午我自己的羽毛球", "activity": "羽毛球", "place": "",
         "status": "Confirmed", "people": "", "bill_total": "", "receipt_activity": "",
         "receipt_place": "", "receipt_text": "", "receipt_done": "", "slot_day": "周六",
         "slot_part": "上午", "conflict": "no", "slot_init_asked": "", "bill_cleared": "no"}
    ]}, ensure_ascii=False))

    # palpo 登录限流（429 最长 4 分钟/账号）——token 持久化缓存（AGENTS.md 纪律）
    ca = MatrixClient(HS, A["username"], A["password"],
                      token_path=f"/tmp/qx-matrix-token-{A['username']}.cache")
    ca.login()
    cb = MatrixClient(HS, B["username"], B["password"],
                      token_path=f"/tmp/qx-matrix-token-{B['username']}.cache")
    cb.login()

    # 建房间 + B 加入
    code, r = ca._req("POST", "/_matrix/client/v3/createRoom",
                      {"name": "qianxian-wp1-e2e", "is_direct": False})
    assert code == 200, f"createRoom {code}: {r}"
    room = r["room_id"]
    # server_name 以 whoami 为准（palpo 本机是 host:port 形态，不是 localhost）
    _, me_a = ca._req("GET", "/_matrix/client/v3/account/whoami", None)
    server_name = me_a["user_id"].split(":", 1)[1]
    code, r = ca._req("POST", f"/_matrix/client/v3/rooms/{room}/invite",
                      {"user_id": f"@{B['username']}:{server_name}"})
    assert code == 200, f"invite {code}: {r}"
    code, r = cb._req("POST", f"/_matrix/client/v3/rooms/{room}/join", {})
    assert code == 200, f"join {code}: {r}"
    print(f"[wp1] 房间就绪 {room}", flush=True)

    # 端口独占：先杀残留 card-host（调试实例/上次失败残留会抢 8147——实锤踩过）
    subprocess.run(["pkill", "-x", "card-host"], check=False)
    time.sleep(1)

    # 组织端 app（card-host，干净 jail）
    host = subprocess.Popen([str(CH), "--bundle", "bundle", "--allow-unsigned",
                             "--stamp", "--remote", str(PORT)],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(6)
        # 建守护 + 确认（全 UI 真驱动）
        # 按结果重试（/t 注入或按钮点击偶发丢失——回归同款闭环，#36 修正同源）
        built = False
        for _try in range(3):
            ws = snap()
            mi = find(ws, "粘贴群消息", "TextInput")
            if mi is None:
                time.sleep(1.0)
                continue
            click(mi, 0.6)
            type_text("周六上午去深圳湾骑车")
            bt = find(snap(), "建守护", "Button")
            if bt:
                click(bt, 2.2)
            jf = ORG_JAIL / "cases.json"
            if jf.exists() and "骑车" in jf.read_text():
                built = True
                break
            # 诊断：打印 hint 与输入框残留（一次失败即可定位）
            _ws2 = snap()
            _hints = [(w.get("t") or "")[:60] for w in _ws2 if w.get("ty") == "Label" and ("守护" in (w.get("t") or "") or "输入" in (w.get("t") or "") or "澄清" in (w.get("t") or ""))]
            _mi = [w.get("val") for w in _ws2 if w.get("ty") == "TextInput"]
            print(f"[wp1-dbg] 第{_try+1}次建守护未果：inputs={_mi} hint={_hints[:2]}", flush=True)
            time.sleep(1.0)
        ws = snap()
        ok("组织者建守护 #1", built and find(ws, "#1 · 骑车") is not None)
        click(find(ws, "#1 · 骑车"), 1.8)
        ws = snap()
        click(find(ws, "确认这条守护", "Button"), 2.2)
        cj = json.loads((ORG_JAIL / "cases.json").read_text())
        ok("组织者守护已确认", cj["cases"][0]["status"] == "Confirmed", cj["cases"][0]["status"])

        # 发投票到群（card-host 降级：文案进输入框 → 读回由客户端真发——协议文案 app 同源）
        ws = snap()
        for _ in range(6):
            bt = find(ws, "发投票到群", "Button")
            if bt:
                break
            get_scrolled = http("/m?k=scroll&x=200&y=600&dx=0&dy=300")
            time.sleep(0.7)
            ws = snap()
        ok("发投票到群按钮可见", bt is not None)
        click(bt, 1.5)
        ws = snap()
        # TextInput 的 val 是原始文本——降级后输入框里就是投票卡文案。
        # v0.10.2 起详情态 composer 隐藏（HTML 02 复刻）：控件在树但零矩形，按 val 读不过滤 rect。
        vote_body = None
        for w in ws:
            if w.get("ty") == "TextInput" and w.get("val") and "时间收敛投票" in w["val"]:
                vote_body = w["val"]
                break
        ok("投票卡文案已从 app 取回（降级通路）", bool(vote_body and vote_body.startswith("📋 时间收敛投票")),
           (vote_body or "")[:40])
        if not vote_body:
            print("[wp1] 无投票卡文案，中止（不进房间）", flush=True)
            sys.exit(1)
        ca.send_message(room, vote_body, txn_id="wp1-card-" + str(int(time.time())))

        # 成员端自治投票（--once：一轮即出结果；首选撞期 → 顺延 B + 理由）
        pr = subprocess.run([sys.executable, str(ROOT / "tools/qx-member-agent.py"),
                             "--jail", str(MEM_JAIL), "--room", room,
                             "--account", "1", "--once"],
                            capture_output=True, text=True, timeout=90)
        print(pr.stdout.strip(), flush=True)
        mv = json.loads((MEM_JAIL / "member-vote.json").read_text())
        ok("成员端自治投票 B（顺延）+ 理由",
           mv.get("letter") == "B" and "顺延" in mv.get("reason", ""),
           f"{mv.get('letter')} {mv.get('reason')}")
        # 房内确证字母票真达
        code, r = ca._req("GET", f"/_matrix/client/v3/rooms/{room}/messages",
                          None, {"dir": "b", "limit": "10"})
        bodies = [(e.get("content") or {}).get("body", "") for e in r.get("chunk", [])
                  if e.get("type") == "m.room.message"]
        ok("字母票 B 真达房间", any(b.strip() == "B" for b in bodies))
        ok("顺延理由真达房间", any("顺延" in b for b in bodies))

        # 归票桥（组织端 jail → converge.json）
        pr = subprocess.run([sys.executable, str(ROOT / "tools/qx-converge-bridge.py"),
                             "--jail", str(ORG_JAIL), "--room", room,
                             "--case-id", "1", "--once"],
                            capture_output=True, text=True, timeout=90)
        print(pr.stdout.strip(), flush=True)
        cv = json.loads((ORG_JAIL / "converge.json").read_text())
        ok("归票：winner=B（顺延票被归入）", cv.get("winner") == "B", cv.get("summary", ""))

        # app：刷新计票 → 管家收敛 → 拍板
        ws = snap()
        for _ in range(6):
            rf = find(ws, "刷新计票", "Button")
            if rf:
                break
            http("/m?k=scroll&x=200&y=600&dx=0&dy=300")
            time.sleep(0.7)
            ws = snap()
        ok("刷新计票按钮可见", rf is not None)
        click(rf, 1.8)
        ws = snap()
        labs = [w.get("t") or "" for w in ws if w.get("ty") == "Label"]
        ok("计票显示（已报 1/1）", any("已报" in t for t in labs),
           "|".join(t for t in labs if "报" in t)[:60])
        cnv = find(ws, "管家收敛", "Button")
        ok("管家收敛按钮可见", cnv is not None)
        click(cnv, 2.2)
        ws = snap()
        ap = find(ws, "拍板执行", "Button")
        ok("收敛提案卡出现（拍板键）", ap is not None)
        click(ap, 2.2)
        cj = json.loads((ORG_JAIL / "cases.json").read_text())
        c0 = cj["cases"][0]
        ok("拍板落盘：改期为周六-下午且仍已确认",
           c0["slot_day"] == "周六" and c0["slot_part"] == "下午" and c0["status"] == "Confirmed",
           f"{c0['slot_day']}-{c0['slot_part']} {c0['status']}")

        # 改票幂等：成员手动改投 C（Outbox）→ 归票 latest-wins 胜项翻转
        (MEM_JAIL / "member-revote.json").write_text(json.dumps(
            {"letter": "C", "reason": "手动改投试试晚场"}, ensure_ascii=False))
        pr = subprocess.run([sys.executable, str(ROOT / "tools/qx-member-agent.py"),
                             "--jail", str(MEM_JAIL), "--room", room,
                             "--account", "1", "--once"],
                            capture_output=True, text=True, timeout=90)
        pr = subprocess.run([sys.executable, str(ROOT / "tools/qx-converge-bridge.py"),
                             "--jail", str(ORG_JAIL), "--room", room,
                             "--case-id", "1", "--once"],
                            capture_output=True, text=True, timeout=90)
        cv = json.loads((ORG_JAIL / "converge.json").read_text())
        ok("改投幂等：归票 latest-wins 胜项翻转为 C",
           cv.get("winner") == "C", f"winner={cv.get('winner')} counts={cv.get('counts')}")
        mv = json.loads((MEM_JAIL / "member-vote.json").read_text())
        ok("成员端显示手动改投（auto=false 不被自治回滚）",
           mv.get("letter") == "C" and mv.get("auto") is False,
           f"{mv.get('letter')} auto={mv.get('auto')}")
        # 再跑一轮成员进程：手动票不被回滚
        subprocess.run([sys.executable, str(ROOT / "tools/qx-member-agent.py"),
                        "--jail", str(MEM_JAIL), "--room", room,
                        "--account", "1", "--once"],
                       capture_output=True, text=True, timeout=90)
        mv = json.loads((MEM_JAIL / "member-vote.json").read_text())
        ok("手动票稳定（自治重评估不回滚）", mv.get("letter") == "C")

    finally:
        host.terminate()

    print()
    if FAILS:
        print(f"WP1-E2E FAIL {len(FAILS)}: {FAILS}", flush=True)
        sys.exit(1)
    print("WP1-E2E ALL PASS", flush=True)


if __name__ == "__main__":
    main()
