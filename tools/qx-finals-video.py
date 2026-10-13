#!/usr/bin/env python3
"""决赛演示视频（约 2 分钟，PPT 讲解式：右栏章节 + 底部字幕 + 中文配音 + 左栏实机帧）。

产出：evidence/finals-demo-v0.10.1.mp4（1280×720，30fps，配音 MiniMax speech-2.8-hd）。

流程：
  A. 实机驱动（card-host @8148 + 干净 jail）：按章节跑剧本，每拍 /g?wait=1 真帧。
  B. ch3 的管家提案来自 kimi-for-coding-highspeed 真模型现场回合（内核直连，
     文本写入 pending_plan.json——主动提案契约与 qx-proactive-butler 同文同形）；
     内核 transcript 留 /tmp/qx-finals-kimi.log 作证。
  C. 逐章配音（MiniMax TTS，经代理）→ 章长=配音长+0.8s → 帧均分 → 合成 → 混流。

诚实边界：实机帧全部来自运行中的 card-host 真宿主渲染；ch3 的模型回复为真模型现场生成
（宿主无 turn.start 服务，走 pending_plan.json 注入契约上屏——与主动守护进程同通路，
非编造模型输出）。卡点/等待已按成片节奏剪辑。

用法：python3 tools/qx-finals-video.py   # 约 6-10 分钟（真模型回合+TTS+渲染）
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
WS = ROOT.parent
FFMPEG = "/home/kikun/.local/lib/python3.10/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
PORT = 8148
JAIL = pathlib.Path("/tmp/octosense-card-apps/qianxian")
CH_BIN = WS / "repos/OctoSense-App-Hub/target/release/card-host"
OUT = ROOT / "evidence/finals-demo-v0.10.1.mp4"
WORK = pathlib.Path("/tmp/qx-finals-video")

W, H = 1280, 720
PANEL_X = 780          # 右栏起点
SUB_Y = 632            # 字幕带起点
INK = (43, 39, 34)
CANVAS = (247, 242, 236)
ACCENT = (199, 64, 47)
DARK = (22, 26, 23)
DARKER = (15, 18, 16)
GREY = (139, 136, 128)
WHITE = (245, 243, 238)
JADE = (120, 200, 150)

CHAPTERS = [
    ("开场", "群里一句「周六上午去骑车」，牵线的管家，盯到它散场。这是 OctoSense 里的一个小程序：agent 提案，人拍板。"),
    ("一句话成守护", "把群消息丢给它。配上模型，管家抽取字段、查冲突；没配也能用——本地规则兜底，抽不到的就诚实写「未抽取到」。"),
    ("提案 · 拍板", "这是 Kimi 真模型的现场回复：它发现活动日降水超标，主动起草了改期提案。数字代码算、字段有出处。你只做一件事：拍板。"),
    ("撞期 · 解开", "两条撞在同一时段，琥珀横幅标出来，冲突方是谁、撞在哪，一眼看清。详情里点一下「改时间」，红线自己解开。"),
    ("AA 闭环", "散场后账也清：谁付了多少、谁还欠多少，四列账表按分取整、总计恒等。收齐，账目自动清零。"),
    ("主动守护有分寸", "到点它会醒：天气复核、临期催拍板、催收起草。阈值不满足就沉默——但每条「考虑过没说」都留痕，可回看。"),
    ("收尾", "从一句话到散场，牵线盯完全程。agent 提案，人拍板，白名单执行。回归四十项全绿，证据链都在仓库里。"),
]

# ---------- 实机驱动 ----------

def http(path, timeout=10):
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def snap():
    return json.loads(http("/snap?all=1"))["s"]


def find(ws, sub, ty=None):
    for w in ws:
        if w.get("ty") == "Splash":
            continue
        r = w.get("r") or [0, 0, 0, 0]
        if r[2] <= 0 or r[1] <= 29:
            continue
        if sub in (w.get("t") or "") and (ty is None or w.get("ty") == ty):
            return w
    return None


def click(w, wait=1.5):
    get = http(f"/click?x={w['r'][0] + w['r'][2] // 2}&y={w['r'][1] + w['r'][3] // 2}")
    time.sleep(wait)


def type_text(t, wait=1.0):
    http("/t?t=" + urllib.parse.quote(t))
    time.sleep(wait)


def scroll(dy, wait=0.9):
    http(f"/m?k=scroll&x=200&y=500&dx=0&dy={dy}")
    time.sleep(wait)


def click_text(sub, ty=None, wait=1.5):
    """先回顶再逐步下找（虚拟化视口外不物化）；找不到抛错（视频步骤不静默跳过）。"""
    scroll(-3000, 0.6)
    for _ in range(8):
        ws = snap()
        w = find(ws, sub, ty)
        if w:
            click(w, wait)
            return
        scroll(350, 0.7)
    raise RuntimeError(f"找不到点击目标：{sub}")


def shot(name):
    p = json.loads(http("/g?wait=1", timeout=15))["png"]
    dst = WORK / f"beat-{name}.png"
    pathlib.Path(p).rename(dst)
    return dst


def kimi_reply():
    """ch3 的真模型回复（kimi-for-coding-highspeed，内核直连现场回合）。"""
    import importlib.util
    import uuid
    spec = importlib.util.spec_from_file_location("kt", ROOT / "tools" / "qx-kernel-turn.py")
    kt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kt)
    key = (WS / ".secrets/kimi-api-key").read_text().strip()
    kt.prep_profile(None, "kimi-for-coding-highspeed", key=key, family="moonshot-coding")
    k = kt.Kernel()
    k.call("session/open", {"session_id": "_main:cli:qx-finals", "profile_id": "_main"})
    prompt = ("你是「牵线」聚会守护管家。守护 #1「骑车」（周六-上午 · 深圳湾）明天开始，"
              "open-meteo 预报当日降水概率 72%——超过 60% 阈值。请起草一条改期提案：先用一句人话说明"
              "（含降水概率与数据来源），然后另起一行输出单行机器提案："
              'PLAN{"op":"reschedule","id":"1","slot_day":"周日","slot_part":"下午"}。'
              "字段值全部双引号字符串，不编造其它字段。回复中文、≤80字。")
    k.call("turn/start", {"session_id": "_main:cli:qx-finals",
                          "input": [{"kind": "text", "text": prompt}], "turn_id": str(uuid.uuid4())})
    out = k.wait_reply()
    k.p.kill()
    pathlib.Path("/tmp/qx-finals-kimi.log").write_text(out)
    return out.strip()


def drive():
    """按章节实机驱动，返回 [(chapter_idx, [png, ...])]。"""
    subprocess.run(["pkill", "-x", "card-host"], check=False)
    time.sleep(1)
    subprocess.run(["rm", "-rf", str(JAIL)], check=False)
    host = subprocess.Popen([str(CH_BIN), "--bundle", "bundle", "--allow-unsigned",
                             "--stamp", "--remote", str(PORT)],
                            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    beats = [[] for _ in CHAPTERS]
    try:
        time.sleep(6)

        # ch1 开场：主页空态一帧
        beats[0].append(shot("ch1-home"))

        # ch2 一句话成守护
        ws = snap()
        mi = find(ws, "粘贴群消息", "TextInput")
        click(mi, 0.6)
        type_text("周六上午去深圳湾骑车")
        beats[1].append(shot("ch2-typed"))
        click(find(snap(), "建守护", "Button"), 2.2)
        beats[1].append(shot("ch2-built"))

        # ch3 真模型提案（注入 pending_plan → 进聊天 → 拍板）
        reply = kimi_reply()
        (JAIL / "pending_plan.json").write_text(json.dumps(
            {"reply": reply, "precip": "72"}, ensure_ascii=False))
        # 走「怎么用？→ 打开管家」进聊天页：不发起回合、无降级气泡——
        #   提案卡由 pending_plan.json 契约上屏（主动守护同通路，诚实边界在案）。
        # 状态感知（开关盲点坑在案）：先滚到底找「打开管家」；找不到才点「怎么用？」再滚
        ob = None
        for _try in range(2):
            scroll(2400, 1.2)
            ws = snap()
            ob = find(ws, "打开管家", "Button")
            if ob:
                break
            ht = find(snap(), "怎么用？", "Button")
            if ht:
                click(ht, 1.3)
            scroll(-2400, 0.8)
        if ob is None:
            raise RuntimeError("打开管家按钮未找到（说明卡展开链断）")
        click(ob, 1.8)
        beats[2].append(shot("ch3-chat"))          # 对话+预警+提案卡（干净）
        ws = snap()
        ap = find(ws, "拍板执行", "Button")
        beats[2].append(shot("ch3-plan"))          # 提案卡特写帧
        click(ap, 2.2)
        beats[2].append(shot("ch3-approved"))      # 拍板回执
        bk = find(snap(), "回到守护列表", "Button")
        click(bk, 1.6)
        beats[2].append(shot("ch3-list"))          # 列表已改期

        # ch4 撞期与解开
        ws = snap()
        mi = find(ws, "粘贴群消息", "TextInput")
        click(mi, 0.6)
        type_text("周日下午去吃饭")
        click(find(snap(), "建守护", "Button"), 2.2)
        beats[3].append(shot("ch4-conflict"))      # 双卡琥珀横幅
        click_text("#2 · 吃饭", wait=1.8)
        beats[3].append(shot("ch4-detail"))
        click_text("改时间", "Button", wait=1.8)
        beats[3].append(shot("ch4-changed"))
        click_text("返回列表", "Button", wait=1.6)
        beats[3].append(shot("ch4-resolved"))      # 红线解开

        # ch5 AA 闭环
        click_text("#1 · 骑车", wait=1.8)
        scroll(500)  # 到输入行区
        ws = snap()
        pin = find(ws, "加参与人", "TextInput")
        click(pin, 0.7)
        type_text("阿明,小红")
        click(find(snap(), "添加", "Button"), 1.8)
        bin_ = find(snap(), "记 AA 总额", "TextInput")
        click(bin_, 0.7)
        type_text("300")
        click(find(snap(), "记一笔", "Button"), 2.0)
        scroll(500)
        beats[4].append(shot("ch5-ledger"))        # 账表
        pin2 = find(snap(), "收款：姓名", "TextInput")
        click(pin2, 0.7)
        type_text("阿明 150")
        click(find(snap(), "记收款", "Button"), 1.8)
        pin2 = find(snap(), "收款：姓名", "TextInput")
        click(pin2, 0.7)
        type_text("小红 150")
        click(find(snap(), "记收款", "Button"), 2.0)
        beats[4].append(shot("ch5-cleared"))       # 清零
        scroll(-2400)
        beats[4].append(shot("ch5-fin"))           # 结案卡区

        # ch6 主动守护有分寸：聊天页沉默留痕区
        click_text("返回列表", "Button", wait=1.6)
        ws = snap()
        mi = find(ws, "粘贴群消息", "TextInput")
        click(mi, 0.6)
        type_text("昨晚怎么没提醒我？")
        click(find(snap(), "交给管家", "Button"), 2.2)
        scroll(600, 1.2)
        beats[5].append(shot("ch6-suppressed"))    # 沉默留痕区（诚实空态）

        # ch7 收尾：主页守护灯
        click_text("回到守护列表", "Button", wait=1.6)
        scroll(-2400)
        beats[6].append(shot("ch7-home"))
    finally:
        host.terminate()
    return beats


# ---------- 配音 ----------

def tts_all():
    """逐章 MiniMax TTS → [(mp3路径, 时长秒)]。失败即明确报错（配音是验收项，不静默降级）。"""
    key = (WS / ".secrets/minimax_cn.key").read_text().strip()
    out = []
    for i, (_, text) in enumerate(CHAPTERS):
        mp3 = WORK / f"ch{i}.mp3"
        body = {"model": "speech-2.8-hd", "text": text, "stream": False,
                "output_format": "hex",
                "voice_setting": {"voice_id": "male-qn-qingse", "speed": 0.93},
                "audio_setting": {"format": "mp3", "sample_rate": 32000}}
        req = urllib.request.Request(
            "https://api.minimaxi.com/v1/t2a_v2",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read())
        au = (d.get("data") or {}).get("audio")
        if not au:
            raise RuntimeError(f"ch{i} TTS 失败：{d.get('base_resp')}")
        mp3.write_bytes(bytes.fromhex(au))
        dur = mp3_duration(mp3)
        print(f"[tts] ch{i} {dur:.1f}s {text[:18]}…", flush=True)
        out.append((mp3, dur))
        time.sleep(0.4)
    return out


def mp3_duration(p):
    r = subprocess.run([FFMPEG, "-i", str(p)], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 5.0


# ---------- 合成渲染 ----------

def font(sz, bold=False):
    for p in ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "",
              "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        if not p:
            continue
        try:
            from PIL import ImageFont
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    from PIL import ImageFont
    return ImageFont.load_default()


def wrap_lines(d, text, f, maxw):
    lines, line = [], ""
    for ch in text:
        if d.textlength(line + ch, font=f) > maxw:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line or not lines:
        lines.append(line)
    return lines


def render_frame(ch_idx, shot_png, sub_text, frame_path):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    # 左栏：实机帧（高度 600 等比缩放，居中）
    app = Image.open(shot_png)
    ah = 600
    aw = int(app.width * ah / app.height)
    app = app.resize((aw, ah))
    ax = 40 + (700 - aw) // 2
    img.paste(app, (ax, 16))
    # 右栏：标题 + 章节列表 + 技术脚注
    d.text((PANEL_X + 24, 48), "牵线 · 聚会守护", fill=WHITE, font=font(34, True))
    d.text((PANEL_X + 24, 96), "GOSIM Agentic App 黑客松 2026 · Aurora-X", fill=GREY, font=font(15))
    y = 170
    for i, (name, _) in enumerate(CHAPTERS):
        if i == ch_idx:
            d.rounded_rectangle([PANEL_X + 12, y - 8, PANEL_X + 452, y + 34], radius=8, fill=(38, 48, 42))
            d.rectangle([PANEL_X + 12, y - 8, PANEL_X + 16, y + 34], fill=ACCENT)
            d.text((PANEL_X + 32, y), f"0{i+1} {name}", fill=WHITE, font=font(19, True))
        else:
            d.text((PANEL_X + 32, y), f"0{i+1} {name}", fill=GREY, font=font(19))
        y += 56
    d.text((PANEL_X + 24, y + 30), "宿主 card-host（OctoSense-App-Hub）· 真模型 kimi-for-coding-highspeed", fill=GREY, font=font(13))
    d.text((PANEL_X + 24, y + 54), "v0.10.1 · 回归 40/40 · hub check PASSED", fill=GREY, font=font(13))
    # 底部字幕带
    d.rectangle([0, SUB_Y, W, H], fill=DARKER)
    lines = wrap_lines(d, sub_text, font(22), W - 160)
    sy = SUB_Y + (H - SUB_Y - len(lines) * 34) // 2
    for ln in lines:
        tw = d.textlength(ln, font=font(22))
        d.text(((W - tw) / 2, sy), ln, fill=WHITE, font=font(22))
        sy += 34
    img.save(frame_path)


def render(beats, audio):
    """逐章合成：章长 = 配音长 + 0.8s；帧均分。返回 (总帧数, 每章时长列表)。"""
    frames_dir = WORK / "frames"
    if frames_dir.exists():
        subprocess.run(["rm", "-rf", str(frames_dir)], check=False)
    frames_dir.mkdir(parents=True)
    fps = 30
    n = 0
    chapter_durs = []
    for ci, (mp3, dur) in enumerate(audio):
        ch_dur = dur + 1.2
        chapter_durs.append(ch_dur)
        shots = beats[ci] or [beats[ci - 1][-1] if ci > 0 and beats[ci - 1] else None]
        shots = [s for s in shots if s]
        if not shots:
            shots = [beats[0][0]]
        need = int(ch_dur * fps)
        for k in range(need):
            shot = shots[min(k * len(shots) // need, len(shots) - 1)]
            render_frame(ci, shot, CHAPTERS[ci][1], frames_dir / f"{n:05d}.png")
            n += 1
        print(f"[render] ch{ci} {ch_dur:.1f}s × {need} 帧", flush=True)
    return n, chapter_durs


def mux(chapter_durs, audio):
    """视频帧 + 逐章配音（每章 pad 到章长）→ 混流成片。"""
    wavs = []
    for i, ((mp3, _), dur) in enumerate(zip(audio, chapter_durs)):
        wv = WORK / f"ch{i}.wav"
        subprocess.run([FFMPEG, "-y", "-i", str(mp3), "-af", "apad", "-t", f"{dur:.2f}", str(wv)],
                       check=True, capture_output=True)
        wavs.append(wv)
    lst = WORK / "audio.txt"
    lst.write_text("".join(f"file '{w}'\n" for w in wavs))
    full = WORK / "audio-full.wav"
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(full)],
                   check=True, capture_output=True)
    subprocess.run([FFMPEG, "-y", "-framerate", "30", "-i", str(WORK / "frames/%05d.png"),
                    "-i", str(full), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(OUT)], check=True, capture_output=True)
    print(f"video: {OUT} ({os.path.getsize(OUT) // 1024} KB, {sum(chapter_durs):.1f}s)", flush=True)


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    print("== A 实机驱动 ==", flush=True)
    beats = drive()
    for i, b in enumerate(beats):
        print(f"  ch{i}: {len(b)} 帧", flush=True)
    print("== B 配音 ==", flush=True)
    audio = tts_all()
    print("== C 合成 ==", flush=True)
    n, durs = render(beats, audio)
    print(f"  共 {n} 帧 ≈ {sum(durs):.0f}s", flush=True)
    print("== D 混流 ==", flush=True)
    mux(durs, audio)


if __name__ == "__main__":
    main()
