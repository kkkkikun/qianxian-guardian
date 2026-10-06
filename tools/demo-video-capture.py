#!/usr/bin/env python3
"""初赛演示视频帧采集：从空数据真机驱动完整演示剧本，每步渲染一帧。

诚实声明：帧 = snap-to-png 渲染器按 card-host /snap 真实控件树重绘
（文字/层级/坐标来自实际运行），非宿主像素；每帧底部标注步骤说明。
"""
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request

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


def label(ws, sub):
    for w in ws:
        if w.get("ty") == "Label" and sub in str(w.get("t", "")):
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
    # 底部字幕条
    from PIL import Image, ImageDraw, ImageFont
    font = None
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


def tap_title_effectVerified(card_sub, tries=8):
    """点卡标题进详情，效果验证（返回列表按钮出现），失败换位重试。"""
    for _ in range(tries):
        ws = snap()
        hits = [w for w in ws if w.get("ty") == "Label"
                and card_sub in str(w.get("t", "")) and 305 <= w["r"][1] <= 677]
        if hits:
            r = hits[0]["r"]
            get(f"/m?k=click&x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
            time.sleep(2.0)
            ws = snap()
            if btn(ws, "← 返回列表"):
                return True
        get("/m?k=scroll&x=200&y=500&dx=0&dy=250")
        time.sleep(1.0)
    return False


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    # 清数据重启由外层完成；这里从空状态开始
    frame("牵线——群里说好的聚会，盯到人人到场、账目清零（空状态与说明卡）", "f01")

    ws = snap()
    click(btn(ws, "用示例试试"))
    frame("① 粘贴群里那条聚会消息（示例一键填充，不覆盖手打稿）", "f02")

    ws = snap()
    click(btn(ws, "建守护"))
    frame("② 点「建守护」——本地分诊命中时间/约定，生成守护提案 #1", "f03")

    ws = snap()
    mi = [w for w in ws if w.get("i") == "msg_input"][0]
    r = mi["r"]
    get(f"/click?x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
    time.sleep(0.8)
    type_in("周六上午也要去吃饭")
    ws = snap()
    click(btn(ws, "建守护"))
    frame("③ 第二条消息也要去——建守护 #2，同一时段立即被看见", "f04")

    frame("④ 冲突检测：「待拍板·冲突」徽章 + 时间冲突警示行，宁示其疑", "f05")

    if tap_title_effectVerified("#2 ·"):
        frame("⑤ 点卡片进详情：状态/参与人/活动一目了然", "f06")

        ws = snap()
        mi = [w for w in ws if w.get("ty") == "TextInput"
              and "加参与人" in str(w.get("t", ""))]
        if mi:
            r = mi[0]["r"]
            get(f"/click?x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
            time.sleep(0.8)
            type_in("小明, 小红")
            ws = snap()
            click(btn(ws, "添加"))
        frame("⑥ 参与人收进来（逗号分隔，草稿即输即存）", "f07")

        ws = snap()
        mi = [w for w in ws if w.get("ty") == "TextInput"
              and "记 AA" in str(w.get("t", ""))]
        if mi:
            r = mi[0]["r"]
            get(f"/click?x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
            time.sleep(0.8)
            type_in("300")
            ws = snap()
            click(btn(ws, "记一笔"))
        frame("⑦ AA 记账 300——均摊自动算给每个人", "f08")

        ws = snap()
        click(btn(ws, "确认这条守护"))
        frame("⑧ 组织者拍板：确认这条守护 → 回执立即生成", "f09")

        frame("⑨ 回执四行：活动/地点/原文/T-24h 提醒，可核对的结果", "f10")

        ws = snap()
        click(btn(ws, "← 返回列表"))
        frame("⑩ 返回列表——回到离开时的位置", "f11")
    else:
        print("detail tap failed; continue in list", flush=True)

    ws = snap()
    yz = [w for w in ws if w.get("ty") == "Label" and str(w.get("t", "")) == "已确认"]
    if yz:
        click(yz[0])
        frame("⑪ 筛选「已确认」——名单只留拍过板的", "f12")

    ws = snap()
    mi = [w for w in ws if w.get("i") == "search_input"]
    if not mi:
        mi = [w for w in ws if w.get("ty") == "TextInput" and "搜活动" in str(w.get("t", ""))]
    if mi:
        r = mi[0]["r"]
        get(f"/click?x={r[0]+r[2]//2}&y={r[1]+r[3]//2}")
        time.sleep(0.8)
        type_in("吃饭")
        time.sleep(1.0)
        frame("⑫ 搜索「吃饭」——标题/地点/原文全文匹配", "f13")

    # AI 能力可见性 + 诚实降级（无需真 AI 服务）
    ws = snap()
    ai = btn(ws, "AI 解析")
    if not ai:
        get("/m?k=scroll&x=200&y=500&dx=0&dy=-4000")
        time.sleep(1.0)
        if tap_title_effectVerified("#2 ·"):
            pass
        for _ in range(8):
            ws = snap()
            ai = btn(ws, "AI 解析")
            if ai:
                break
            get("/m?k=scroll&x=200&y=500&dx=0&dy=250")
            time.sleep(0.9)
    if ai:
        click(ai)
        frame("⑬ AI 解析：能力可见；本机无活后端时诚实降级为本地规则", "f14")

    # 清空全部两段式
    ws = snap()
    cb = btn(ws, "清空全部")
    if not cb:
        ws = snap()
        h = btn(ws, "怎么用？")
        if h:
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
        frame("⑭ 清空全部：两段式确认（第一次点只进入待确认）", "f15")
        ws = snap()
        cb2 = btn(ws, "清空全部")
        if cb2:
            click(cb2)
            frame("⑮ 第二次点才真删——危险操作留退路，5 秒内可放弃", "f16")

    frame("⑯ 空状态如实呈现——数据可导出、可清空，人始终在掌控", "f17")
    print("ALL-FRAMES-DONE", flush=True)


if __name__ == "__main__":
    main()
