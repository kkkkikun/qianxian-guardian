#!/usr/bin/env python3
"""演示视频 v0.9.2：规划 §4 六幕骨架 × 真实运行素材。

素材来源（如实）：
- 手机帧：card-host 实机 /snap 控件树重绘（v0.9.2 新 UI；非宿主像素，入档声明）；
- Rinx 帧：真宿主×Kimi 真模型回合的聊天录帧（transcript 按本日真实运行记录逐字）。
产出：evidence/demo-v092-frames/*.png → evidence/finals-demo-v092.mp4（~90 秒）。
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
BG = (247, 242, 236)
CARD = (241, 236, 228)
INK = (43, 39, 34)
SECOND = (110, 103, 94)
ACCENT = (199, 64, 47)
GREEN = (47, 125, 79)
AMBER = (168, 117, 22)
LINE = (233, 223, 210)
FFMPEG = "ffmpeg"
ROOT = "/home/kikun/MyProject/Agentic-octos/my-entry"
SHOTS = f"{ROOT}/bundle/screenshots"
OUT = f"{ROOT}/evidence/demo-v092-frames"
VIDEO = f"{ROOT}/evidence/finals-demo-v092.mp4"


def font(sz, bold=False):
    for p in ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/usr/share/fonts/truetype/arphic/uming.ttc"):
        try:
            return ImageFont.truetype(p, sz, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


def wrap_lines(d, text, f, maxw):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n" or d.textlength(cur + ch, font=f) > maxw:
            lines.append(cur)
            cur = ""
            if ch != "\n":
                cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def wrap(d, xy, text, f, fill, maxw, lh):
    x, y = xy
    for ln in wrap_lines(d, text, f, maxw):
        d.text((x, y), ln, fill=fill, font=f)
        y += lh
    return y


def base(title, subtitle=""):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((W - 380, H - 38), "github.com/kkkkikun/qianxian-guardian · v0.9.2", fill=SECOND, font=font(13))
    d.text((48, 60), title, fill=INK, font=font(34, True))
    if subtitle:
        d.text((48, 112), subtitle, fill=SECOND, font=font(18))
    return img, d


def frame_phone(n, step, title, bullets, png, data_label=None, data_text=None):
    """双栏演示帧：左手机 + 右步骤叙事。"""
    img, d = base("", "")
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
    d.rounded_rectangle([cx, 128, cx + 108, 160], radius=8, fill=ACCENT)
    d.text((cx + 20, 133), step, fill=(255, 255, 255), font=font(17, True))
    y = wrap(d, (cx, 182), title, font(26, True), INK, cw, 36) + 18
    for b in bullets:
        d.ellipse([cx + 2, y + 9, cx + 10, y + 17], fill=ACCENT)
        y = wrap(d, (cx + 22, y), b, font(17), INK, cw - 22, 26) + 12
    if data_text:
        y += 8
        d.rounded_rectangle([cx, y, cx + cw, y + 128], radius=12, fill=CARD)
        d.text((cx + 20, y + 12), data_label or "实况", fill=SECOND, font=font(13, True))
        wrap(d, (cx + 20, y + 40), data_text, font(14), SECOND, cw - 40, 22)
    img.save(f"{OUT}/{n:03d}.png")


def frame_transcript(n, title, sub, bubbles, note):
    img, d = base(title, sub)
    y = 180
    for who, text, accent in bubbles:
        if who == "me":
            d.rounded_rectangle([700, y, 1230, y + 30 + 24 * (len(text) // 30)], radius=14, fill=(250, 245, 238))
            wrap(d, (720, y + 12), "我：" + text, font(16), INK, 500, 24)
            y += 44 + 24 * (len(text) // 30)
        else:
            d.rounded_rectangle([48, y, 620, y + 44 + 24 * (len(text) // 34)], radius=14,
                                fill=(238, 243, 234) if not accent else (252, 246, 236))
            wrap(d, (68, y + 12), "管家：" + text, font(16), INK, 540, 24)
            y += 58 + 24 * (len(text) // 34)
    d.rounded_rectangle([48, H - 120, W - 48, H - 48], radius=12, fill=CARD)
    wrap(d, (72, H - 104), note, font(15), SECOND, W - 144, 24)
    img.save(f"{OUT}/{n:03d}.png")


def frame_table(n, title, sub, header, rows, colw, rowcolors=None):
    img, d = base(title, sub)
    y = 172
    x = 48
    for i, h in enumerate(header):
        d.text((x, y), h, fill=SECOND, font=font(16, True))
        x += colw[i]
    y += 34
    for ri, row in enumerate(rows):
        d.line([48, y - 8, W - 48, y - 8], fill=LINE, width=1)
        x = 48
        for i, c in enumerate(row):
            col = INK
            if rowcolors:
                col = rowcolors[ri][i]
            wrap(d, (x, y), str(c), font(16), col, colw[i] - 16, 22)
            x += colw[i]
        y += 46
    img.save(f"{OUT}/{n:03d}.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        os.remove(os.path.join(OUT, f))
    n = 0

    # 000 标题
    img, d = base("牵线 · 聚会筹办守护 v0.9.2", "agent 驱动全流程 · 人只做最终拍板")
    d.text((48, 200), "一句话丢给管家，守护到人人到场、账目清零", fill=INK, font=font(40, True))
    d.text((48, 268), "Kimi 真模型 × Rinx 真宿主 × 红线生命周期 UI", fill=ACCENT, font=font(24))
    d.text((48, 336), "以下帧来自真实运行：手机帧=card-host 实机控件树重绘；对话=真宿主×真模型逐字实录", fill=SECOND, font=font(17))
    img.save(f"{OUT}/{n:03d}.png"); n += 1

    # 001 幕一：群消息 → 管家 → diff 提案 → 拍板（列表+协议）
    frame_table(n, "幕一 · agentic 主线（10 秒立住）", "PLAN 提案 → 人拍板 → 白名单动作；LLM 自身无执行权",
                ["阶段", "发生什么"],
                [["① 用户", "粘贴群消息点「交给管家」（octos.turn.start 真回合）"],
                 ["② 管家(agent)", "抽取字段 + 查冲突 + 真工具（天气/时间），回复尾部输出单行 PLAN{...}"],
                 ["③ diff 提案卡", "旧值 ──▶ 新值 + 冲突预演（纯试算）；出处【】高亮；字段不归一/无 id 一律拒"],
                 ["④ 拍板", "12 个白名单 op：create/confirm/reschedule/cancel/add_people/set_bill/complete/draft_dunning/mark_paid/undo/clear/export"],
                 ["⑤ 拒绝并改写", "放弃时选理由（时间不对/地点不对/理解错了），理由注入下一轮——拒绝是改道入口"]],
                [210, 1010]); n += 1

    # 002 幕一配图：提案对话（真模型逐字，本轮真实记录）
    frame_transcript(n, "幕一 · 实机对话（Rinx×Kimi 逐字实录）", "改期回合：信息不足时模型先问，带 id 后白名单放行",
                     [("me", "把1号守护改到周日下午吧", 0),
                      ("ai", "好的，拟把 #1 改到周日下午；地点消息未提及，维持原守护（深圳湾）。\nPLAN{\"op\":\"reschedule\",\"id\":\"1\",\"slot_day\":\"周日\",\"slot_part\":\"下午\"}", 0)],
                     "diff 提案卡渲染：「时间：周六-上午 ──▶ 周日-下午」+「冲突预演：✓ 改后无冲突」→ 拍板 → cases.json 落盘 周日-下午。此前两次无 id 提案被白名单正确拒绝（「目标 # 不存在——拒绝执行」）。"); n += 1

    # 003 幕二：列表（红线状态线+守护灯+冲突横幅）= 01-main.png
    frame_phone(n, "幕二", "一句话长成一个被守护的生命",
                ["红线生命周期：待拍板→已确认→已完成→已收尾",
                 "实心朱砂=已过 · 晕环=当前 · 空心描边=未到——冲突解开，红线肉眼可见地推进",
                 "守护灯常驻条：待拍板/⚡冲突/待收尾确定性摘要（主动信息的「家」）",
                 "冲突琥珀横幅：「与 #N·爬山 同占「周六-上午」，改个时段即解开」"],
                f"{SHOTS}/01-main.png", "实机控件树重绘", "每卡三段：标题行+语义 chips → 元信息行 → 迷你红线；原文 faint 引行"); n += 1

    # 004 幕三：主动守护（天气预警）——转录帧
    frame_transcript(n, "幕三 · 主动守护：T-24h 到点，先查天气再决定说不说",
                     "伴生守护进程三级提醒（T-7d / T-24h / 活动日晨）；≥60% 降水才预警",
                     [("ai", "⏰ 牵线提醒（T-24h）：#1 骑车（周六-上午 · 深圳湾）明天开始！参与人：阿明,小红。AA记得收尾。", 0)],
                     "天气复核链：open-meteo 查活动日降水概率 ≥60% → 提醒里附预警（来源+日期）；无雨/查不到 → 不打扰——但写「沉默留痕」：「考虑过但没说的事，你都能回看」（全场独有）。发送通路：palpo Matrix 真投递（b 账号断言入房 5/5）。"); n += 1

    # 005 幕四：冲突裁决（03-conflict.png）
    frame_phone(n, "幕四", "改一个时段，红线自动解开",
                ["同时段两守护互标冲突（确定性全量重算，零 AI 参与数字）",
                 "管家出改期提案：diff 卡附冲突预演「⚡改后与 #2 撞」或「✓ 无冲突」",
                 "拍板落地 → 冲突标记随 mark_conflicts 全量重算即时清除"],
                f"{SHOTS}/03-conflict.png", "实机控件树重绘", "时间收敛/冲突检测/待定 vs 已确认——官方日历场景三动词逐条实现"); n += 1

    # 006 幕五：AA 对账（02-expanded.png）
    frame_phone(n, "幕五", "账目清零闭环 + 梯度催收（永不公示名单）",
                ["全员余额表：成员 | 已付 | 欠(琥珀)/清✓(玉绿)/多垫",
                 "按分取整舍入写死：base+尾差，合计恒等于总额 ✓",
                 "「谁该付下一笔」事前消解（垫付最少者优先收款）",
                 "梯度催收：事前/T+1 系统口吻/T+3 私发名单/T+7 最后一催——数字全由代码算"],
                f"{SHOTS}/02-expanded.png", "实机控件树重绘", "agent 只提议发起催收；金额/差额永不参与模型输出"); n += 1

    # 007 幕六：守护灯+沉默留痕（转录帧收尾）
    frame_transcript(n, "幕六 · 信任与审计：会自证的 app",
                     "Evidence Pack：快照+审计链（UTC+8 时间戳|actor(user/agent)|action）+回放统计+沉默留痕，离线校验器 PASS",
                     [("ai", "🤫 沉默留痕：\n· 10-12 09:00 ｜ ☁ 天气复核：未查到（地点未匹配到坐标），提醒照发不带天气\n· 10-12 09:00 ｜ 💰 催收未到档（T+1/T+7 才开口）", 1)],
                     "别的 agent 炫耀做了什么——牵线的 agent 能交代「为什么没做」。系统日历写链（RC2 device_calendar）：确认拍板后原生面板物理确认，用户只点确认；Linux 宿主诚实降级 ICS。"); n += 1

    # 008 验证级别
    img, d = base("验证级别（如实标注）", "全部证据可复现：evidence/v090-features-20261012.md · v080-features-20261012.md")
    rows = [("verified", "回归 25/25（+守护灯/垫付建议/沉默留痕/ops 新形态断言），渲染错误 0", GREEN),
            ("verified", "Rinx×Kimi 真机 e2e：create/mark_paid(正+否定)/export/clear 两段/改期 diff 卡——cases.json 落盘断言全过", GREEN),
            ("verified", "hub check PASSED（0.9.2，含 device_calendar 能力声明）；桥进程 e2e 五条提醒真发入房", GREEN),
            ("boundary", "Rinx 变体 manifest 剥新契约字段（宿主 contract 旧）；手机帧为控件树重绘非宿主像素；undo 正例 8s 窗<模型延迟", AMBER)]
    y = 180
    for k, v, c in rows:
        d.rounded_rectangle([48, y - 2, 48 + d.textlength(k, font=font(15, True)) + 20, y + 26], radius=6, fill=c)
        d.text((58, y + 1), k, fill=(255, 255, 255), font=font(15, True))
        y = wrap(d, (250, y), v, font(18), INK, 990, 25) + 30
    img.save(f"{OUT}/{n:03d}.png"); n += 1

    cmd = [FFMPEG, "-y", "-framerate", "1/10", "-i", f"{OUT}/%03d.png",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", VIDEO]
    subprocess.run(cmd, check=True, capture_output=True)
    print("video:", VIDEO, os.path.getsize(VIDEO) // 1024, "KB,", n, "帧 ≈", n * 10, "秒")


if __name__ == "__main__":
    main()
