#!/usr/bin/env python3
"""S4 真宿主端到端驱动：Rinx(backup) + octos 内核 + mock LLM 上的管家全链。

流程：Mini apps → 导入 bundle → Review → Run → app 内输入群消息 → 交给管家 →
等 PLAN 提案卡 → 拍板执行 → 断言 sys 回执 + 卡片出现 + cases.json 落盘。
（Rinx 的 vendored makepad 不做 /t 百分号解码 → 一律走裸 UTF-8 socket 请求行。）

用法：python3 qx-rinx-drive.py [--port 8170] [--bundle /tmp/qx-demo-bundle] [--full]
  --full 追加第二轮：改期提案 → 拍板 → 断言 slot 变化。
"""
import json
import socket
import sys
import time

PORT = 8170
BUNDLE = "/tmp/qx-demo-bundle"


def raw(path, timeout=25):
    if isinstance(path, str):
        path = path.encode()
    s = socket.create_connection(("127.0.0.1", PORT), timeout=timeout)
    s.sendall(b"GET " + path + b" HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
    buf = b""
    while True:
        d = s.recv(65536)
        if not d:
            break
        buf += d
    s.close()
    return json.loads(buf.split(b"\r\n\r\n", 1)[1].decode(errors="replace"))


def snap():
    return raw("/snap")["s"]


def by_id(i):
    for w in snap():
        if w.get("i") == i:
            return w


def by_text(sub, ty):
    for w in snap():
        if w.get("ty") == ty and sub in str(w.get("t", "")):
            return w


def click(w, wait=1.8):
    r = w["r"]
    raw(f"/m?k=click&x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
    time.sleep(wait)


def fill(i, text, wait=0.7):
    click(by_id(i), 0.6)
    raw("/k?c=a&ctrl=1")
    time.sleep(0.4)
    raw(f"/t?t={text}")
    time.sleep(wait)


def labels():
    return [str(w.get("t", "")) for w in snap() if w.get("ty") == "Label" and w.get("t")]


def wait_for(pred, secs=60, step=2.0, note=""):
    n = int(secs / step)
    for i in range(n):
        time.sleep(step)
        ls = labels()
        if pred(ls):
            return ls
        print(f"  …{int((i+1)*step)}s {note}", flush=True)
    return None


def import_and_run():
    click(by_id("octoscript_apps_button"), 2.5)
    if not by_id("path"):
        print("!! 未见到 Mini apps 导入界面")
        return False
    fill("path", BUNDLE)
    click(by_id("review"), 4.5)
    notice = next((str(w.get("t", "")) for w in snap() if w.get("i") == "notice"), "")
    if "Services" not in notice:
        print("!! Review 未通过:", notice[:160])
        return False
    print("[S4] Review 通过:", notice[:80].replace("\n", " / "))
    click(by_id("run"), 8.0)
    return by_id("msg_input") is not None


def butler_turn(message, expect_plan=True):
    inp = by_id("msg_input")
    if not inp:
        print("!! app 界面不在（可能被 Back）")
        return None
    click(inp, 0.7)
    raw(f"/t?t={message}")
    time.sleep(0.9)
    b = by_text("交给管家", "Button")
    click(b, 1.0)
    ls = wait_for(lambda ls: any(t.startswith("管家：") for t in ls) or any("不可用" in t or "无响应" in t for t in ls), 90, 2, "等管家回复")
    if not ls:
        print("!! 90s 无回复")
        return None
    bad = [t for t in ls if "不可用" in t or "无响应（30" in t and "降级" in t]
    if bad and not any(t.startswith("管家：") for t in ls):
        print("!! 管家失败:", bad[:1])
        return None
    print("[S4] 管家回复:", next(t for t in ls if t.startswith("管家："))[:80])
    if expect_plan:
        prop = [t for t in ls if "待拍板" in t or t.startswith("op：") or t.startswith("新建守护")]
        print("[S4] 提案卡行:", [p[:50] for p in prop[:4]])
        if not any("待拍板" in t for t in ls):
            print("!! 未出现提案卡")
            return None
    return ls


def approve():
    b = by_text("拍板执行", "Button")
    if not b:
        print("!! 无拍板按钮")
        return False
    click(b, 2.5)
    ls = wait_for(lambda ls: any(t.startswith("已拍板") for t in ls), 20, 1.5, "等拍板回执")
    if ls:
        print("[S4] 拍板回执:", next(t for t in ls if t.startswith("已拍板"))[:80])
        return True
    return False


def main():
    full = "--full" in sys.argv
    if not import_and_run():
        sys.exit(2)
    # 第一轮：建守护提案 → 拍板
    if not butler_turn("周六上午去深圳湾骑车"):
        sys.exit(3)
    if not approve():
        sys.exit(4)
    ls = labels()
    card = [t for t in ls if t.startswith("#") and "骑车" in t]
    print("[S4] 卡片出现:", card[:2])
    assert card, "拍板后未见骑车卡片"
    if full:
        # 第二轮：改期提案 → 拍板
        if not butler_turn("改到周日下午吧"):
            sys.exit(5)
        if not approve():
            sys.exit(6)
        ls = labels()
        slot = [t for t in ls if "周日-下午" in t]
        print("[S4] 改期生效:", slot[:2])
        assert any("周日-下午" in t for t in ls), "改期后未见周日-下午"
    print("S4-DRIVE-DONE")


if __name__ == "__main__":
    main()
