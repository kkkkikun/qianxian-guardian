#!/usr/bin/env python3
"""演示视频后半段：筛选/搜索/AI降级/两段式清空/空状态。"""
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, "app/qianxian/tools")
PORT = 8150
OUT = "/tmp/qx-video-frames"
BASE = f"http://127.0.0.1:{PORT}"


def get(path):
    return urllib.request.urlopen(BASE + path, timeout=10).read()


def snap():
    return json.loads(get("/snap"))["s"]


def btn(ws, txt):
    for w in ws:
        if w.get("ty") == "Button" and str(w.get("t", "")) == txt:
            return w


def click(w, wait=1.6):
    r = w["r"]
    get(f"/m?k=click&x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
    time.sleep(wait)


def type_in(text, wait=0.8):
    get("/t?t=" + urllib.parse.quote(text))
    time.sleep(wait)


def frame(title, name):
    subprocess.run([sys.executable, "app/qianxian/tools/snap-to-png.py",
                    "--port", str(PORT), "--out", f"{OUT}/{name}.png"], check=True)
    from PIL import Image, ImageDraw, ImageFont
    font = small = None
    for p in ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        try:
            font = ImageFont.truetype(p, 22)
            small = ImageFont.truetype(p, 13)
            break
        except OSError:
            continue
    img = Image.open(f"{OUT}/{name}.png").convert("RGB")
    d = ImageDraw.Draw(img)
    W, H = img.size
    d.rectangle([0, H - 56, W, H], fill=(43, 39, 34))
    d.text((14, H - 46), title, fill=(255, 250, 244), font=font)
    d.text((14, 6), "牵线 · 初赛演示（真实运行控件树重绘，非宿主像素）",
           fill=(43, 39, 34), font=small)
    d.text((W - 320, H - 42), "github.com/kkkkikun/qianxian-guardian",
           fill=(200, 190, 178), font=small)
    img.save(f"{OUT}/{name}.png")
    print("frame:", name, title, flush=True)


def scroll_top():
    get("/m?k=scroll&x=200&y=500&dx=0&dy=-5000")
    time.sleep(1.2)


def main():
    # ⑪ 筛选：回顶 → 点「已确认」chip
    scroll_top()
    ws = snap()
    yz = [w for w in ws if w.get("ty") == "Label" and str(w.get("t", "")) == "已确认"]
    if yz:
        click(yz[0])
        frame("⑪ 筛选「已确认」——名单只留拍过板的", "f12")
    else:
        print("chip 已确认 not found", flush=True)

    # ⑫ 搜索
    ws = snap()
    mi = [w for w in ws if w.get("ty") == "TextInput" and "搜活动" in str(w.get("t", ""))]
    if mi:
        r = mi[0]["r"]
        get(f"/click?x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
        time.sleep(0.8)
        type_in("吃饭")
        time.sleep(1.2)
        frame("⑫ 搜索「吃饭」——标题/地点/原文全文匹配", "f13")
    else:
        print("search box not found", flush=True)

    # ⑬ AI：回顶 → 清搜索 → 展开说明卡 → AI 解析（输入框有示例文案）
    scroll_top()
    ws = snap()
    xf = [w for w in ws if w.get("ty") == "TextInput" and "搜活动" in str(w.get("t", ""))]
    if xf:
        r = xf[0]["r"]
        get(f"/click?x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
        time.sleep(0.6)
        get("/t?t=")
        time.sleep(0.6)
    h = btn(ws, "怎么用？")
    if h:
        click(h)
    ai = None
    for _ in range(10):
        ws = snap()
        ai = btn(ws, "AI 解析")
        if ai:
            break
        get("/m?k=scroll&x=200&y=500&dx=0&dy=250")
        time.sleep(0.9)
    if ai:
        # 输入框先补一条消息（AI 解析需要非空输入）
        scroll_top()
        ws = snap()
        mi = [w for w in ws if w.get("i") == "msg_input"]
        if mi:
            r = mi[0]["r"]
            get(f"/click?x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
            time.sleep(0.8)
            type_in("周日晚上去唱K")
        # 回到 AI 解析键
        ws = snap()
        h = btn(ws, "怎么用？")
        state_open = [w for w in ws if w.get("i") == "hint" and "展开" in str(w.get("t", ""))]
        if not state_open and h:
            click(h)
        ai = None
        for _ in range(10):
            ws = snap()
            ai = btn(ws, "AI 解析")
            if ai:
                break
            get("/m?k=scroll&x=200&y=500&dx=0&dy=250")
            time.sleep(0.9)
        if ai:
            click(ai)
            time.sleep(1.5)
            frame("⑬ AI 解析：能力可见；无活后端时诚实降级为本地规则（提示在屏）", "f14")

    # ⑭⑮ 清空全部两段式（说明卡内）
    ws = snap()
    cb = btn(ws, "清空全部")
    if not cb:
        h = btn(ws, "怎么用？")
        cur = [w for w in ws if w.get("i") == "hint" and "收起" in str(w.get("t", ""))]
        if not cur and h:
            click(h)
        for _ in range(10):
            ws = snap()
            cb = btn(ws, "清空全部")
            if cb:
                break
            get("/m?k=scroll&x=200&y=500&dx=0&dy=250")
            time.sleep(0.8)
    if cb:
        click(cb)
        frame("⑭ 清空全部：两段式确认（第一次点只进入待确认，5 秒内可放弃）", "f15")
        ws = snap()
        cb2 = btn(ws, "清空全部")
        if cb2:
            click(cb2)
            time.sleep(1.5)

    # ⑯ 真空状态
    scroll_top()
    frame("⑯ 清空后空状态如实呈现——数据可导出、可清空，人始终在掌控", "f16")
    print("CONT-DONE", flush=True)


if __name__ == "__main__":
    main()
