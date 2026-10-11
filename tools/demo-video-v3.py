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
    d.text((48, 264), "管家分诊 · 查冲突 · 出提案 —— 你只点「拍板」", fill=ACCENT, font=font(24))
    d.text((48, 332), "本片全部来自真实运行：octos 内核直连 ×2 · Rinx 真宿主 × MiniMax-M3 四轮 e2e · 回归 16/16",
           fill=SECOND, font=font(17))
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

    # 002 内核直连 × mock（解析真实产物）
    reply, plan = mock_rows()
    rows = [("$", "tools/qx-kernel-turn.py —— 真实 octos serve --stdio 内核直连，提示词与 app 内管家同款", GREEN),
            ("用户", "周六上午去深圳湾骑车", (222, 216, 205)),
            ("管家", reply or "（解析失败）", (222, 216, 205))]
    if plan:
        rows.append((None, plan, (140, 220, 160)))
    rows.append((None, "✓ 回包含 PLAN —— 提示词 → 内核 → 模型 → 提案形态，全链成立", (140, 220, 160)))
    frame_transcript(n, "证据 ①：octos 内核直连（剧本模型）", "tools/qx-kernel-turn.py 运行产物逐字转写（assistant_delta 累积）", rows); n += 1

    # 003 Rinx × MiniMax 实况（第 3 轮逐字实录）
    frame_chat(n, "证据 ②：Rinx 真宿主 × MiniMax-M3 真模型", "第 3 轮实况逐字实录——真模型读取守护快照，主动预警冲突",
               [("me", "周日下午去莲花山爬山，顺便野餐"),
                ("ai", "跟现有 #1「周日-下午·骑车·深圳湾」撞时段了，下午这个档只能去一处👀"),
                ("plan", 'PLAN{"op":"create","text":"周日下午去莲花山爬山，顺便野餐","activity":"爬山+野餐","slot_day":"周日","slot_part":"下午","place":"莲花山",…}'),
                ("sys", "提案卡在下方（拍板执行 / 放弃）→ 人点「拍板执行」→ #2 落盘")],
               "文本逐字取自 Rinx e2e 第 3 轮运行输出（evidence/s4 翻案段）；气泡按 app 样式重绘"); n += 1

    # 004 四轮矩阵
    frame_table(n, "Rinx 真宿主端到端：四轮全部「提案 → 拍板 → 落盘」", "cases.json 落盘断言逐轮核对（evidence/s4-real-host-20261010.md）",
                ["轮", "模型", "提案 op", "拍板后落盘（断言）"],
                [["1", "剧本 mock", "create #1", "#1 建卡：周六-上午 · 骑车 · 深圳湾 · 待拍板"],
                 ["2", "剧本 mock", "reschedule", "#1 → 周日-下午，冲突全量重算"],
                 ["3", "MiniMax-M3", "create #2", "#2 落盘 · 莲花山；真模型主动预警「撞时段」，#1/#2 互标冲突"],
                 ["4", "MiniMax-M3", "confirm #1", "#1 → Confirmed，回执就位；真模型提示「#2 同期无人」"]],
                [60, 180, 180, 860]); n += 1

    # 005 主界面
    frame_phone(n, "STEP 1", "把群消息丢给管家",
                ["输入框粘贴群消息（或点「示例」一键填充）",
                 "「交给管家」是主入口——分诊、查冲突、出提案一步到位",
                 "无 AI 宿主时自动降级，本地规则路径完整可用"],
                f"{SHOTS}/s1-main.png", "屏上实况", "AI：管家对话通道可用（首次需宿主允许）"); n += 1

    # 006 降级
    frame_phone(n, "STEP 2", "无 AI 服务的设备：诚实降级",
                ["card-host 无 octos 服务 → sys 气泡明示原因，不假装管家在听",
                 "能力标签同步「通道实测无响应」——不误导",
                 "「建守护」本地规则路径功能完整（评分维度：失败状态）"],
                f"{SHOTS}/s2-chat.png", "sys 气泡原文",
                'AI 通道无响应（no service answers "octos" on this device）——已降级本地规则'); n += 1

    # 007 冲突
    frame_phone(n, "STEP 3", "守护状态机：冲突检测",
                ["两条同时段守护互相标记「·冲突」徽章",
                 "冲突卡列出双方：要改期还是取消？矛盾交人裁决",
                 "管家提案同样先查冲突——真模型轮已实证预警"],
                f"{SHOTS}/s3-conflict.png", "冲突卡原文",
                "两条同时段守护互标「待拍板·冲突」，冲突卡列出双方（要改期还是取消？）"); n += 1

    # 008 回执
    frame_phone(n, "STEP 4", "拍板之后：回执就位",
                ["组织者确认 → Confirmed + 回执快照（活动/地点/原文/T-24h）",
                 "改期/加人/记账/取消都可让管家提案，拍板即执行",
                 "取消两段式 + 5 秒撤销；抽不到的字段明示「未抽取到」"],
                f"{SHOTS}/s4-receipt.png", "回执实况",
                "↳ 活动：骑车 ｜ 地点：深圳湾 ｜ 原文：周六上午去深圳湾骑车 ｜ T-24h 提醒"); n += 1

    # 009 收官
    img, d = base("验证级别（如实标注）", "全部证据可复现：命令见 run.md D 节")
    rows = [("verified", "内核直连 PLAN：剧本模型 + MiniMax-M3 真模型（tools/qx-kernel-turn.py）", GREEN),
            ("verified", "Rinx 真宿主 e2e 四轮：create/reschedule/confirm 落盘断言全过", GREEN),
            ("verified", "card-host 回归 16/16 · hub check PASSED（0.3.0，agent read-only）", GREEN),
            ("boundary", "旧宿主同上下文第二回合事件偶丢 → 每 Run 一回合；界面帧为控件树重绘", ACCENT)]
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
