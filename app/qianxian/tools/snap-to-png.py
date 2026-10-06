#!/usr/bin/env python3
"""把 card-host 的 /snap 控件树渲染成 PNG（真实运行数据可视化，非截图）。

用途：本环境无头渲染时 /g 抓帧超时（grab timeout），但 /snap 能给出完整的
控件树（类型/文本/矩形）。本脚本据真实数据绘制界面图，用于生成
`bundle/screenshots/01-main.png`。

诚实声明：这不是宿主渲染的像素，而是**按真实控件树与坐标重绘**——
文字内容、层级、位置均来自运行中的应用，不是设计稿。
用法：octo run bundle --port 8190 --detach --hidden
      python3 tools/snap-to-png.py --port 8190 --out bundle/screenshots/01-main.png
"""
import argparse
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H = 412, 892
# #48「红线」设计 tokens（与 main.splash 同源）：暖纸底/墨/朱砂/玉绿/琥珀/赤陶
BG = (247, 242, 236)      # xf7f2ec 暖米白
INK = (43, 39, 34)        # x2b2722 墨
SECOND = (110, 103, 94)   # x6e675e 暖灰
ACCENT = (199, 64, 47)    # xc7402f 朱砂
GREEN = (47, 125, 79)     # x2f7d4f 玉绿
ORANGE = (163, 95, 0)     # xa35f00 琥珀
RED = (161, 77, 60)       # xa14d3c 赤陶
PURPLE = (199, 64, 47)    # x5856d6→朱砂（撤销/AI 徽章已并入红线系）
CARD = (241, 236, 228)    # xf1ece4 控件底
BADGE_BG = (251, 233, 229)  # xfbe9e5 朱砂浅底

FONT_CJK = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]


def load_font(size):
    for p in FONT_CJK:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fetch(port, path):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10) as r:
        return json.load(r)


GLYPH_MAP = {"⚠": "!", "✨": "", "📌": "", "📍": "", "💬": "", "⏰": "", "▶": "> ", "▾": "v ", "↳": " ->"}
def clean(text):
    t = text or ""
    for k, v in GLYPH_MAP.items():
        t = t.replace(k, v)
    return t

def color_of(text):
    t = text or ""
    if "已取消" in t or "取消" in t:
        return RED
    if "已确认" in t:
        return GREEN
    if "待拍板" in t:
        return SECOND
    if "冲突" in t:
        return ORANGE
    if "⚠" in t or "时间冲突" in t:
        return ORANGE
    if "未填写" in t or "未抽取" in t:
        return SECOND
    if "地点" in t or "活动" in t or "时间" in t or "状态" in t or "回执" in t or "参与人" in t:
        return SECOND
    return INK


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    snap = fetch(args.port, "/snap?all=1")
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    f_title = load_font(26)
    f_body = load_font(14)
    f_small = load_font(12)
    f_badge = load_font(12)

    widgets = [w for w in snap.get("s", [])
               if w.get("ty") != "Splash"
               and "Card host [remote]" not in (w.get("t") or "")
               and w.get("r", [0, 0])[1] > 20]
    widgets.sort(key=lambda w: (w.get("r") or [0, 0])[1])

    for w in widgets:
        r = w.get("r") or [0, 0, 0, 0]
        x, y, ww, hh = r
        if ww <= 0 or hh <= 0 or y < 0 or y > H:
            continue
        ty, text = w.get("ty"), (w.get("t") or "").strip()
        if not text:
            continue
        text = clean(text)

        # 标题豁免：大字号标题不套 chip 底（#48 渲染器修）
        is_title = y < 90 and hh >= 26
        if ty == "Button":
            fill = {
                "确认这条守护": GREEN, "重新收敛": ORANGE, "取消守护": RED,
                "建守护": ACCENT, "AI 解析": ACCENT, "改时间（5 槽）": ORANGE,
                "添加": ACCENT, "采纳到输入框": ACCENT, "撤销取消": ACCENT,
            }.get(text)
            if fill:
                d.rounded_rectangle([x, y, x + ww, y + hh], radius=10, fill=fill)
                fg = (255, 255, 255)
            else:
                # flat 文字按钮（用示例试试/怎么用？/风格：X/忽略/导出数据/清空全部）
                d.rounded_rectangle([x, y, x + ww, y + hh], radius=10, fill=CARD)
                fg = ACCENT if text in ("用示例试试", "怎么用？") or text.startswith("风格：") else (
                    RED if text == "清空全部" else SECOND)
            f = f_badge
        elif ty == "TextInput":
            d.rounded_rectangle([x, y, x + ww, y + hh], radius=10, fill=CARD)
            fg, f = SECOND, f_small
        elif not is_title and len(text) <= 12 and ("·" in text or text.startswith("#")):
            d.rounded_rectangle([x, y, x + ww, y + hh], radius=7,
                                fill=BADGE_BG)
            fg, f = ACCENT, f_badge
        elif text.startswith("↳") or text.startswith("⚠"):
            fg, f = ORANGE, f_small
        elif len(text) <= 8 and text in ("状态", "时间", "参与人", "活动", "地点", "原文", "回执"):
            fg, f = SECOND, f_small
        else:
            fg, f = color_of(text), (f_title if hh >= 26 and y < 90 else f_body)

        t_show = text.replace("▾", "v").replace("▶", ">")
        if t_show != text:
            text = t_show
        tx = x + 5
        if ty == "Label" and ww < 90 and hh <= 30 and x > 250:
            tx = x - 4  # 右侧徽章贴右边缘
        d.text((tx, y + max(1, (hh - 12) // 2)), text, fill=fg, font=f)

    # 若内容超出视口（展开态较长），整体缩放到视口高度内，保证不裁切
    maxy = max((w.get("r") or [0, 0, 0, 0])[1] + (w.get("r") or [0, 0, 0, 0])[3]
               for w in widgets) if widgets else 0
    if maxy > H:
        scale = (H - 8) / maxy
        img = img.resize((max(1, int(W * scale)), max(1, int(H * scale))), Image.LANCZOS)
    img.save(args.out)
    print(f"wrote {args.out} from live /snap of port {args.port}")


if __name__ == "__main__":
    main()
