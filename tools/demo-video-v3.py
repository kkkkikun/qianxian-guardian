#!/usr/bin/env python3
"""演示视频 v3 生成器（重排版）：干净双栏演示风。

帧源全部真实：
  - 内核直连转写：运行时解析 /tmp/s4-mock.out（tools/qx-kernel-turn.py 产物），
    只取 assistant_delta 累积文本（无 JSON-RPC 噪声）
  - 真模型实况：Rinx 真宿主 × MiniMax-M3 e2e 第 3 轮逐字实录（运行输出留档，
    见 evidence/s4-real-host-20261010.md 翻案段）
  - app 界面帧：evidence/shots-v3/（控件树重绘，如实标注）
诚实标注：界面帧为控件树重绘（非宿主像素）；对话帧文本逐字取自真实运行。
"""
import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

OUT = "/home/kikun/MyProject/Agentic-octos/my-entry/evidence/demo-v3-frames"
SHOTS = "/home/kikun/MyProject/Agentic-octos/my-entry/evidence/shots-v3"
VIDEO = "/home/kikun/MyProject/Agentic-octos/my-entry/evidence/finals-demo-v3.mp4"
MOCK_OUT = "/tmp/s4-mock.out"
W, H = 1280, 800
BG = (247, 242, 236)
INK = (43, 39, 34)
ACCENT = (199, 64, 47)
SECOND = (110, 103, 94)
GREEN = (47, 125, 79)
ORANGE = (163, 95, 0)
CARD = (241, 236, 228)
LINE = (223, 216, 205)
DARK = (30, 28, 25)

FFMPEG = "/home/kikun/.local/lib/python3.10/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"


def font(sz, bold=False):
    for p in ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_lines(d, text, f, maxw):
    """预计算换行（返回行列表）——用于先量高度再画底。"""
    lines, line = [], ""
    for ch in text:
        if d.textlength(line + ch, font=f) > maxw:
            lines.append(line); line = ch
        else:
            line += ch
    if line or not lines:
        lines.append(line)
    return lines


def wrap(d, xy, text, f, fill, maxw, lh):
    """逐字换行绘制；返回最后一行下方（调用点直接接着排）。"""
    x, y = xy
    for ln in wrap_lines(d, text, f, maxw):
        d.text((x, y), ln, fill=fill, font=f)
        y += lh
    return y


def base(title, subtitle=""):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((48, 34), title, fill=INK, font=font(32, True))
    if subtitle:
        d.text((48, 84), subtitle, fill=SECOND, font=font(17))
    d.text((W - 340, H - 38), "github.com/kkkkikun/qianxian-guardian", fill=SECOND, font=font(13))
    return img, d


def frame_phone(n, step, title, bullets, png, data_label=None, data_text=None):
    """双栏演示帧：左手机（描边+投影）+ 右步骤叙事。"""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((W - 340, H - 38), "github.com/kkkkikun/qianxian-guardian", fill=SECOND, font=font(13))
    src = Image.open(png).convert("RGB")
    ph = 600
    pw = int(src.width * ph / src.height)
    src = src.resize((pw, ph), Image.LANCZOS)
    px, py = 96, 128
    d.rounded_rectangle([px - 6, py - 6, px + pw + 6, py + ph + 6], radius=22, fill=(228, 222, 212))
    d.rounded_rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], radius=20, fill=(255, 255, 255))
    img.paste(src, (px, py))
    d.rounded_rectangle([px - 3, py - 3, px + pw + 3, py + ph + 3], radius=20, outline=LINE, width=2)
    cx = px + pw + 56
    cw = W - cx - 60
    d.rounded_rectangle([cx, 128, cx + 96, 160], radius=8, fill=ACCENT)
    d.text((cx + 20, 133), step, fill=(255, 255, 255), font=font(17, True))
    y = wrap(d, (cx, 182), title, font(26, True), INK, cw, 36) + 18
    for b in bullets:
        d.ellipse([cx + 2, y + 9, cx + 10, y + 17], fill=ACCENT)
        y = wrap(d, (cx + 22, y), b, font(17), INK, cw - 22, 26) + 12
    if data_text:
        y += 10
        d.rounded_rectangle([cx, y, cx + cw, y + 116], radius=12, fill=CARD)
        d.text((cx + 20, y + 12), data_label or "实况", fill=SECOND, font=font(13, True))
        wrap(d, (cx + 20, y + 38), data_text, font(14), SECOND, cw - 40, 22)
    img.save(f"{OUT}/{n:03d}.png")


def frame_transcript(n, title, sub, rows):
    """干净转写帧：深色面板 + 角色/文本/PLAN 高亮（无 JSON 噪声）。"""
    img, d = base(title, sub)
    d.rounded_rectangle([40, 132, W - 40, 700], radius=14, fill=DARK)
    y = 158
    for role, text, color in rows:
        if role:
            f = font(16)
            nlines = len(wrap_lines(d, text, f, W - 280))
            d.rounded_rectangle([64, y - 1, 64 + d.textlength(role, font=font(14, True)) + 22, y + 24], radius=6, fill=color)
            d.text((75, y + 1), role, fill=(255, 255, 255), font=font(14, True))
            wrap(d, (180, y), text, f, (222, 216, 205), W - 280, 24)
            y += 24 * nlines + 16
        else:
            f = font(15)
            nlines = len(wrap_lines(d, text, f, W - 140))
            wrap(d, (64, y), text, f, color, W - 140, 22)
            y += 22 * nlines + 12
    img.save(f"{OUT}/{n:03d}.png")


def frame_chat(n, title, sub, bubbles, tag):
    """真模型实况：按 app 聊天样式重绘的对话气泡（文本逐字真实）。"""
    img, d = base(title, sub)
    d.rounded_rectangle([150, 128, W - 150, 686], radius=18, fill=(253, 250, 245), outline=LINE, width=2)
    y = 152
    for role, text in bubbles:
        if role == "me":
            f = font(16)
            lines = wrap_lines(d, "我：" + text, f, 340)
            bh = 20 + 24 * len(lines)
            bx = W - 400
            d.rounded_rectangle([bx, y, W - 196, y + bh], radius=12, fill=(233, 226, 214))
            wrap(d, (bx + 14, y + 10), "我：" + text, f, INK, 320, 24)
            y += bh + 14
        elif role == "ai":
            f = font(16)
            lines = wrap_lines(d, "管家：" + text, f, W - 460)
            bh = 20 + 24 * len(lines)
            d.rounded_rectangle([172, y, W - 380, y + bh], radius=12, fill=(238, 243, 234))
            wrap(d, (188, y + 10), "管家：" + text, f, INK, W - 480, 24)
            y += bh + 14
        elif role == "plan":
            f = font(14)
            lines = wrap_lines(d, text, f, W - 480)
            bh = 18 + 20 * len(lines)
            d.rounded_rectangle([172, y, W - 196, y + bh], radius=8, fill=DARK)
            wrap(d, (190, y + 9), text, f, (140, 220, 160), W - 470, 20)
            y += bh + 12
        else:
            f = font(15)
            lines = wrap_lines(d, text, f, W - 420)
            wrap(d, (186, y), text, f, ACCENT, W - 420, 22)
            y += 22 * len(lines) + 10
    d.text((170, 660), tag, fill=SECOND, font=font(12))
    img.save(f"{OUT}/{n:03d}.png")


def frame_table(n, title, sub, header, rows, colw, rowcolors=None):
    img, d = base(title, sub)
    x0, y0 = 60, 150
    rh = 64
    x = x0
    d.rounded_rectangle([x0, y0, x0 + sum(colw), y0 + 46], radius=10, fill=INK)
    for wcol, htxt in zip(colw, header):
        d.text((x + 16, y0 + 12), htxt, fill=(255, 255, 255), font=font(16, True))
        x += wcol
    y = y0 + 56
    for i, cells in enumerate(rows):
        colors = rowcolors[i] if rowcolors else [INK] * len(cells)
        if i % 2 == 0:
            d.rounded_rectangle([x0, y - 6, x0 + sum(colw), y + rh - 12], radius=8, fill=(252, 248, 242))
        x = x0
        for wcol, cell, col in zip(colw, cells, colors):
            f = font(15, True) if col == ACCENT else font(15)
            wrap(d, (x + 16, y), cell, f, col, wcol - 28, 21)
            x += wcol
        y += rh
    img.save(f"{OUT}/{n:03d}.png")



# === Rinx 实机演示帧渲染（app-only 过滤 + 宽幅原样呈现）===
CHROME = {"Welcome to Rinx!", "Chats", "File Transfer", "Found no\njoined spaces.",
          "No joined or invited rooms found.", "Mini apps", "R",
          "Filter rooms & spaces..."}

def load_live(name):
    return json.load(open(f"/tmp/qx-live-{name}.json"))

def filter_app(ws):
    out = []
    for w in ws:
        t = str(w.get("t", "") or "")
        r = w.get("r", [0, 0, 0, 0])
        if r[1] < 32 or r[0] < 6 or r[0] > 1272:
            continue
        if t in CHROME or t.startswith("Running · Back closes"):
            continue
        if len(t) > 160:  # splash 源码查看器大 Label
            continue
        out.append(w)
    return out

def render_live(n, step, title, sub, name, note=None):
    ws = filter_app(load_live(name))
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((W - 340, H - 38), "github.com/kkkkikun/qianxian-guardian", fill=SECOND, font=font(13))
    # 步题带
    d.rounded_rectangle([40, 24, 40 + d.textlength(step, font=font(15, True)) + 24, 52], radius=8, fill=ACCENT)
    d.text((52, 29), step, fill=(255, 255, 255), font=font(15, True))
    d.text((180, 28), title, fill=INK, font=font(19, True))
    d.text((W - 40 - d.textlength(sub, font=font(14)), 31), sub, fill=SECOND, font=font(14))
    # app 区域：以 app 标题为顶，原样宽幅呈现（Rinx 真窗 1280×800）
    y0 = 118
    for w in ws:
        if str(w.get("t", "")) == "牵线 · 聚会守护":
            y0 = min(y0, w["r"][1] - 12)
    ay = 64
    d.rounded_rectangle([0, ay, W, H], radius=0, fill=BG)
    d.rectangle([0, ay, W, ay + 2], fill=LINE)
    f_body, f_small = font(14), font(12)
    for w in ws:
        ty = w.get("ty")
        t = str(w.get("t", "") or "").strip().replace("📋", "")  # wqy 无该字形
        x, y, ww, hh = w.get("r", [0, 0, 0, 0])
        yy = y - y0 + ay
        if yy < ay + 2 or yy > H - 30 or ww <= 0:
            continue
        if not t:
            continue
        if ty == "Button":
            fill = {"交给管家": ACCENT, "拍板执行": ACCENT, "添加": ACCENT,
                    "确认这条守护": GREEN, "重新收敛": ORANGE}.get(t)
            if fill:
                d.rounded_rectangle([x, yy, x + ww, yy + hh], radius=10, fill=fill)
                col = (255, 255, 255)
            else:
                d.rounded_rectangle([x, yy, x + ww, yy + hh], radius=10, fill=CARD)
                col = ACCENT if t in ("建守护", "用示例试试", "回到守护列表", "返回列表", "怎么用？") or t.startswith("风格：") else SECOND
            d.text((x + min(10, ww // 8), yy + hh // 2 - 9), t[:26], fill=col, font=f_body)
        elif ty == "TextInput":
            d.rounded_rectangle([x, yy, x + ww, yy + hh], radius=10, fill=(255, 255, 255), outline=LINE, width=1)
            val = str(w.get("val", "") or "")
            shown = val if val else t
            d.text((x + 10, yy + hh // 2 - 9), shown[:60], fill=(INK if val else SECOND), font=f_body)
        else:
            if t.startswith(("AI：", "已", "把群消息", "管家思考", "①", "②", "③", "粘贴群消息，点", "改期/", "在宿主", "还没有", "← ")) or t.startswith("把一条群消息"):
                col = SECOND
            elif len(t) <= 16 and ("冲突" in t or "·" in t and t.startswith(("#", "▸", "▶", ">"))):
                col = ACCENT
            elif t.startswith(("时间冲突", "⚠")) or "PLAN{" in t:
                col = GREEN if "PLAN{" in t else ACCENT
            else:
                col = INK
            sz = f_body if hh <= 30 else font(16)
            yy2 = yy
            for ln in wrap_lines(d, t, sz, max(200, ww - 8)):
                if yy2 > H - 30:
                    break
                d.text((x + 4, yy2), ln, fill=col, font=sz)
                yy2 += 22
    if note:
        d.rounded_rectangle([40, H - 64, W - 40, H - 30], radius=8, fill=CARD)
        d.text((56, H - 57), note, fill=SECOND, font=font(14))
    img.save(f"{OUT}/{n:03d}.png")


def mock_rows():
    """从 /tmp/s4-mock.out 解析 ASSISTANT_TEXT 段（tools/qx-kernel-turn.py 完整输出）。"""
    txt = ""
    if os.path.exists(MOCK_OUT):
        lines = open(MOCK_OUT, errors="replace").read().splitlines()
        try:
            b = lines.index("ASSISTANT_TEXT_BEGIN")
            e = lines.index("ASSISTANT_TEXT_END")
            txt = "\n".join(lines[b + 1:e]).strip()
        except ValueError:
            pass
    reply, plan = txt, ""
    if "PLAN{" in txt:
        reply, plan = txt.split("PLAN{", 1)
        plan = "PLAN{" + plan
    return reply.strip(), plan.strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    n = 0

    # 000 标题
    img, d = base("牵线 · 聚会筹办守护 v0.3.0", "决赛迭代：agent 驱动全流程，人只做最终拍板")
    d.text((48, 200), "把群消息丢给管家", fill=INK, font=font(44, True))
    d.text((48, 264), "AI 管家实机演示 —— Rinx 真宿主 × MiniMax-M3 真模型", fill=ACCENT, font=font(24))
    d.text((48, 332), "以下每一帧都是真实运行中的控件树实况：真模型回复 · 提案卡 · 拍板 · 落盘", fill=SECOND, font=font(17))
    img.save(f"{OUT}/{n:03d}.png"); n += 1

    # 001 协议
    frame_table(n, "管家协议：PLAN 提案 → 人拍板 → 白名单动作", "LLM 不直接碰状态机（评审红线）——agent 提案，UI 拥有确认权",
                ["阶段", "发生什么"],
                [["① 用户", "粘贴群消息，点「交给管家」（octos.turn.start 真回合）"],
                 ["② 管家(agent)", "按提示词抽取字段 + 查冲突，回复尾部输出单行机器提案"],
                 ["PLAN{...}", '{"op":"create","text":"原文","activity":"骑车","slot_day":"周六",…}'],
                 ["③ 提案卡", "槽位词表归一（编造的时间进不了状态机），一次至多一个提案"],
                 ["④ 拍板", "「拍板执行」→ 白名单动作：create/confirm/reschedule/cancel/add_people/set_bill"]],
                [210, 1010],
                [[INK, INK], [INK, INK], [ACCENT, ACCENT], [INK, INK], [GREEN, GREEN]]); n += 1

    # 002-007 实机演示（Rinx 真宿主 × MiniMax-M3，每帧 = 运行中 /snap 实况）
    render_live(n, "实机 ①", "Rinx 真宿主内运行「牵线」", "Mini apps 导入 → Review → Run（真模型 MiniMax-M3）", "01-main",
                "宿主原生窗口实况（控件树重绘；App 内界面随窗口宽度自适应拉伸）"); n += 1
    render_live(n, "实机 ②", "粘贴一条群消息", "「周五晚上去大学城吃火锅，然后唱K」—— 只说了周五，没给具体日子", "02-typed",
                "输入框实况（真键盘注入）"); n += 1
    render_live(n, "实机 ③", "点「交给管家」→ 管家思考中", "octos.turn.start 真回合发给内核 → 内核调 MiniMax-M3", "03-thinking",
                "此时 app 已发出回合请求；30 秒无响应会自动降级本地规则（诚实可见）"); n += 1
    render_live(n, "实机 ④", "真模型回复 + PLAN 提案卡", "真模型逐字实录：「只说了周五没给具体日子，对不上日历，先建个草案你拍板？」", "05-proposal",
                "模型主动指出信息不足仍给出可拍板草案——抽取全来自原文，槽位词表归一"); n += 1
    render_live(n, "实机 ⑤", "人点「拍板执行」", "唯一人工确认点——白名单动作 create 落地，LLM 自身无执行权", "06-approved",
                "sys 回执：「已拍板：守护 #1 已建（待拍板态，详情里可确认）」"); n += 1
    render_live(n, "实机 ⑥", "回到守护列表：#1 在册", "cases.json 落盘断言：activity=吃火锅+唱K ｜ slot=周五-晚上 ｜ place=大学城 ｜ Proposing", "07-list",
                "拍板后计数「共 1 / 1 条」——同一状态同时呈现在 UI 与 jail 落盘文件"); n += 1

    # 008 四轮矩阵
    frame_table(n, "同一通路四轮端到端（含本轮）", "cases.json 落盘断言逐轮核对（evidence/s4-real-host-20261010.md）",
                ["轮", "模型", "提案 op", "拍板后落盘（断言）"],
                [["1", "剧本 mock", "create #1", "#1 建卡：周六-上午 · 骑车 · 深圳湾 · 待拍板"],
                 ["2", "剧本 mock", "reschedule", "#1 → 周日-下午，冲突全量重算"],
                 ["3", "MiniMax-M3", "create #2", "#2 落盘 · 莲花山；真模型主动预警撞时段，#1/#2 互标冲突"],
                 ["4", "MiniMax-M3", "confirm #1", "#1 → Confirmed，回执就位；真模型提示「#2 同期无人」"]],
                [60, 180, 180, 860]); n += 1

    # 009 收官
    img, d = base("验证级别（如实标注）", "全部证据可复现：命令见 run.md D 节")
    rows = [("verified", "内核直连 PLAN：剧本模型 + MiniMax-M3 真模型（tools/qx-kernel-turn.py）", GREEN),
            ("verified", "Rinx 真宿主 e2e 五轮：create/reschedule/confirm 落盘断言全过", GREEN),
            ("verified", "card-host 回归 16/16 · hub check PASSED（0.3.0，agent read-only）", GREEN),
            ("boundary", "旧宿主同上下文第二回合事件偶丢 → 每 Run 一回合；实机帧为运行中控件树重绘", ACCENT)]
    y = 180
    for k, v, c in rows:
        d.rounded_rectangle([48, y - 2, 48 + d.textlength(k, font=font(15, True)) + 20, y + 26], radius=6, fill=c)
        d.text((58, y + 1), k, fill=(255, 255, 255), font=font(15, True))
        y = wrap(d, (250, y), v, font(18), INK, 990, 25) + 26
    img.save(f"{OUT}/{n:03d}.png"); n += 1

    cmd = [FFMPEG, "-y", "-framerate", "1/7", "-i", f"{OUT}/%03d.png",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", VIDEO]
    subprocess.run(cmd, check=True, capture_output=True)
    print("video:", VIDEO, os.path.getsize(VIDEO) // 1024, "KB,", n, "帧 ≈", n * 7, "秒")


if __name__ == "__main__":
    main()
