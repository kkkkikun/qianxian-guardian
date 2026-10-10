#!/usr/bin/env python3
"""演示视频 v3 生成器：以 agent 驱动为主线的幻灯帧合成（PIL 帧 + ffmpeg 合成）。

帧源全部真实：
  - 内核直连真实输出（/tmp/s4-mock.out / /tmp/s4-real.out，tools/qx-kernel-turn.py 产物）
  - app 界面帧（evidence/shots-v3/，控件树重绘如实标注）
  - Rinx 真宿主运行帧（s5）
诚实标注：界面帧为控件树重绘（非宿主像素）；Rinx turn 端到端因宿主×内核
peer 记账不兼容 blocked（官方 standalone_local 测试同错定性，evidence/s4 文档）。
"""
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

OUT = "/home/kikun/MyProject/Agentic-octos/my-entry/evidence/demo-v3-frames"
SHOTS = "/home/kikun/MyProject/Agentic-octos/my-entry/evidence/shots-v3"
VIDEO = "/home/kikun/MyProject/Agentic-octos/my-entry/evidence/finals-demo-v3.mp4"
W, H = 1280, 800
BG = (247, 242, 236)
INK = (43, 39, 34)
ACCENT = (199, 64, 47)
SECOND = (110, 103, 94)
GREEN = (47, 125, 79)
CARD = (241, 236, 228)

FFMPEG = "/home/kikun/.local/lib/python3.10/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"


def font(sz, bold=False):
    for p in ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def base(title, subtitle=""):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((48, 36), title, fill=INK, font=font(34, True))
    if subtitle:
        d.text((48, 86), subtitle, fill=SECOND, font=font(18))
    d.text((W - 340, H - 40), "github.com/kkkkikun/qianxian-guardian", fill=SECOND, font=font(14))
    return img, d


def wrap(d, xy, text, f, fill, maxw, lh):
    x, y = xy
    line = ""
    for ch in text:
        if d.textlength(line + ch, font=f) > maxw:
            d.text((x, y), line, fill=fill, font=f)
            y += lh
            line = ch
        else:
            line += ch
    if line:
        d.text((x, y), line, fill=fill, font=f)
    return y


def frame_title(i):
    img, d = base("牵线 · 聚会筹办守护 v0.3.0", "决赛迭代：agent 驱动全流程，人只做最终拍板")
    d.text((48, 170), "把群消息丢给管家 —— 管家分诊、查冲突、出提案，你只点「拍板」", fill=INK, font=font(26))
    d.text((48, 220), "本片全部证据来自真实运行：octos 内核直连 ×2 + card-host 回归 16/16 + Rinx 真宿主", fill=SECOND, font=font(18))
    img.save(f"{OUT}/{i:03d}.png")


def frame_plan(i):
    img, d = base("管家协议：PLAN 提案 → 人拍板 → 白名单动作", "LLM 不直接碰状态机（评审红线）——agent 提案，UI 拥有确认权")
    rows = [
        ("① 用户", "粘贴群消息，点「交给管家」（octos.turn.start，单参数 text）", INK),
        ("② 管家(agent)", "按提示词抽取字段 + 查冲突，回复尾部输出单行机器提案：", INK),
        ("PLAN{...}", 'PLAN{"op":"create","text":"原文","activity":"骑车","slot_day":"周六","slot_part":"上午","place":"深圳湾",...}', ACCENT),
        ("③ 提案卡", "app 解析进提案卡（槽位词表归一，编造时间进不了状态机）", INK),
        ("④ 拍板", "人点「拍板执行」→ 复用 9 个白名单动作（建/确认/改期/取消/加人/记账）", GREEN),
        ("ops", "create / confirm / reschedule / cancel / add_people / set_bill", SECOND),
    ]
    y = 160
    for k, v, c in rows:
        d.text((48, y), k, fill=c, font=font(20, True))
        y = wrap(d, (260, y), v, font(18), c, 960, 26) + 26
    img.save(f"{OUT}/{i:03d}.png")


def frame_term(i, title, sub, path, tail=6, hl="PLAN{"):
    img, d = base(title, sub)
    lines = open(path, errors="replace").read().splitlines()
    # 取含 PLAN 的行与其前后
    idx = next((n for n, l in enumerate(lines) if hl in l), 0)
    seg = lines[max(0, idx - 1): idx + tail]
    d.rounded_rectangle([36, 140, W - 36, 640], radius=12, fill=(30, 28, 25))
    y = 158
    for l in seg:
        c = (140, 220, 160) if hl in l else (222, 216, 205)
        y = wrap(d, (56, y), l[:400], font(15), c, 1160, 21) + 6
        if y > 610:
            break
    img.save(f"{OUT}/{i:03d}.png")


def frame_shot(i, title, sub, png, note=""):
    img, d = base(title, sub)
    src = Image.open(png)
    scale = min(1.0, (H - 220) / src.height, (W - 120) / src.width)
    src = src.resize((int(src.width * scale), int(src.height * scale)))
    img.paste(src, ((W - src.width) // 2, 140))
    if note:
        wrap(d, (48, H - 90), note, font(16), SECOND, 1180, 22)
    img.save(f"{OUT}/{i:03d}.png")


def frame_close(i):
    img, d = base("收尾", "验证级别如实标注")
    rows = [
        ("verified", "内核直连 PLAN：mock + MiniMax-M3 真模型（tools/qx-kernel-turn.py）", GREEN),
        ("verified", "card-host 回归 16/16（14 步原路径 + 管家降级 2 步）", GREEN),
        ("verified", "Rinx 真宿主 e2e：mock create/reschedule + MiniMax-M3 create/confirm 四轮落盘", GREEN),
        ("verified", "hub check PASSED：qianxian 0.3.0，agent read-only 最小权限", GREEN),
        ("boundary", "旧宿主同上下文第二回合事件偶丢→每 Run 一回合；演示用去 agent 块同源变体（提交包完整契约）", ACCENT),
        ("", "证据：evidence/s4-real-host-20261010.md · 回归：app/qianxian/tools/qx-verify-v2.py", SECOND),
    ]
    y = 160
    for k, v, c in rows:
        if k:
            d.rounded_rectangle([48, y - 2, 48 + d.textlength(k, font=font(15, True)) + 20, y + 26], radius=6, fill=c)
            d.text((58, y + 1), k, fill=(255, 255, 255), font=font(15, True))
        wrap(d, (240, y), v, font(18), INK, 1000, 25)
        y += 52
    img.save(f"{OUT}/{i:03d}.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    n = 0
    frame_title(n); n += 1
    frame_plan(n); n += 1
    frame_term(n, "证据①：真实 octos 内核 × mock 模型", "octos serve --stdio 内核直连，提示词=app 内管家同款（tools/qx-kernel-turn.py）", "/tmp/s4-mock.out"); n += 1
    frame_term(n, "证据②：MiniMax-M3 真模型理解 PLAN 协议", "同一提示词，真 LLM（内环同款 minimax-cn 通路）回复中生成 PLAN", "/tmp/s4-real.out", tail=8); n += 1
    frame_shot(n, "app：把群消息丢给管家（主入口）", "card-host 实跑控件树重绘（本机 WSLg 无头 /g 抓帧超时，如实标注非宿主像素）", f"{SHOTS}/s1-main.png"); n += 1
    frame_shot(n, "无 AI 宿主时的诚实降级", "card-host 无 octos 服务 → 明示降级本地规则；「建守护」路径完整可用", f"{SHOTS}/s2-chat.png"); n += 1
    frame_shot(n, "Rinx 真宿主 × MiniMax-M3：真模型提案卡", "「跟现有 #1 撞时段了」——真模型读守护快照主动预警冲突，并按协议给出 PLAN 提案卡", f"{SHOTS}/s6-realmodel-proposal.png",
               "真机链路：交给管家 → octos 内核真回合 → MiniMax-M3 → PLAN 提案卡 → 人点「拍板执行」；宿主为 Rinx(Mini apps)，完整四轮矩阵见 evidence/s4"); n += 1
    frame_shot(n, "拍板之后：真模型 confirm 轮落盘", "#1 status=Confirmed、回执就位——六操作白名单动作全部由 agent 提案驱动", f"{SHOTS}/s7-after-approve.png",
               "四轮实测：mock create/reschedule + 真模型 create/confirm，全部「提案→拍板→cases.json 落盘断言」通过"); n += 1
    frame_shot(n, "守护状态机：冲突检测", "两条同时段守护互标冲突（规则分诊同样服务降级路径）", f"{SHOTS}/s3-conflict.png"); n += 1
    frame_shot(n, "拍板后的回执", "组织者确认 → 回执快照 + T-24h 提醒文案（no-facts：未抽取到明示）", f"{SHOTS}/s4-receipt.png"); n += 1
    frame_close(n); n += 1
    # 合成（每帧 7s）
    cmd = [FFMPEG, "-y", "-framerate", "1/7", "-i", f"{OUT}/%03d.png",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", VIDEO]
    subprocess.run(cmd, check=True, capture_output=True)
    print("video:", VIDEO, os.path.getsize(VIDEO) // 1024, "KB,", n, "帧 ≈", n * 7, "秒")


if __name__ == "__main__":
    main()
