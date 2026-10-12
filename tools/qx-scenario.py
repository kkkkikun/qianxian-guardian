#!/usr/bin/env python3
"""牵线剧本化模拟测试 + 录制引擎（Playwright 风格）。

一个「剧本」是一串步骤（declarative steps），引擎逐步执行：
  - 动作：click / type / scroll / wait / goto_chat / back_list / snap_shot
  - 断言：expect_text / expect_no_text / expect_jail（cases.json 字段）
每步边跑边把当前 /snap 控件树渲染成帧（snap-to-png 复用），最后 ffmpeg 串成视频。

帧 = snap-to-png 渲染器按真实控件树重绘（非宿主像素，诚实标注）。
用法：
  python3 tools/qx-scenario.py --port 8146 --scenario scenarios/01-agentic-line.py \
      --frames /tmp/qx-scen-01 --video /tmp/qx-scen-01.mp4 [--check-only]
  --check-only 只跑断言不录帧/视频（回归模式）。
"""
import argparse
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:"
JAIL = pathlib.Path("/tmp/octosense-card-apps/qianxian")
FFMPEG = "/home/kikun/.local/lib/python3.10/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"


def mk_opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Ctx:
    def __init__(self, port, frames_dir=None, check_only=False):
        self.port = port
        self.base = BASE + str(port)
        self.opener = mk_opener()
        self.frames_dir = frames_dir
        self.check_only = check_only
        self.n = 0
        self.failures = []

    def get(self, path, timeout=8):
        return json.loads(self.opener.open(self.base + path, timeout=timeout).read())

    def snap(self):
        return self.get("/snap?all=1")["s"]

    def labels(self, ws=None):
        ws = ws if ws is not None else self.snap()
        return [w.get("t") or "" for w in ws if isinstance(w.get("t"), str)]

    def find(self, sub, ty=None, ws=None):
        ws = ws if ws is not None else self.snap()
        for w in ws:
            r = w.get("r") or [0, 0, 0, 0]
            # ScrollY 虚拟化：?all=1 会带出视口外控件的占位 rect [0,0,0,0]——
            #   过滤（点它会点到左上角错误位置，A5 在案坑）
            if r[2] <= 0 or r[3] <= 0:
                continue
            if sub in (w.get("t") or "") and (ty is None or w.get("ty") == ty):
                return w
        return None

    def center(self, w):
        x, y, ww, hh = w["r"]
        return x + ww // 2, y + hh // 2

    def click(self, w, wait=1.2):
        x, y = self.center(w)
        self.get(f"/m?k=click&x={x}&y={y}")
        time.sleep(wait)

    def scroll(self, dy, times=1, wait=0.6):
        for _ in range(times):
            self.get(f"/m?k=scroll&x=200&y=500&dx=0&dy={dy}")
            time.sleep(wait)

    def type_text(self, text, wait=0.9):
        self.get("/t?t=" + urllib.parse.quote(text))
        time.sleep(wait)

    def shot(self, note=""):
        """渲染当前控件树成一帧（check-only 跳过）。"""
        if self.check_only or not self.frames_dir:
            return
        os.makedirs(self.frames_dir, exist_ok=True)
        # 复用 snap-to-png 渲染器
        spec = importlib.util.spec_from_file_location(
            "s2p", str(pathlib.Path(__file__).resolve().parents[1] / "app" / "qianxian" / "tools" / "snap-to-png.py"))
        s2p = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(s2p)
        out = f"{self.frames_dir}/{self.n:03d}.png"
        sys.argv = ["snap-to-png", "--port", str(self.port), "--out", out]
        try:
            s2p.main()
        except SystemExit:
            pass
        # 步骤标注条
        self._annotate(out, note)
        self.n += 1

    def _annotate(self, png, note):
        if not note:
            return
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.open(png).convert("RGB")
            d = ImageDraw.Draw(img)
            for fp in ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                       "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
                try:
                    f = ImageFont.truetype(fp, 13)
                    break
                except Exception:
                    f = ImageFont.load_default()
            tw = d.textlength(note, font=f)
            d.rounded_rectangle([8, 8, 16 + tw, 32], radius=6, fill=(43, 39, 34))
            d.text((12, 12), note, fill=(247, 242, 236), font=f)
            img.save(png)
        except Exception:
            pass

    def expect(self, name, ok, ev=""):
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}" + (f" :: {ev}" if (ev and not ok) else ""), flush=True)
        if not ok:
            self.failures.append((name, ev))


# ---------- 步骤执行 ----------

def step_click(ctx, target, wait=1.4, retries=6, scroll_dy=300):
    """点按钮/标签（含滚动重试——ScrollY 虚拟化）。"""
    for _ in range(retries):
        w = ctx.find(target, "Button") or ctx.find(target)
        if w:
            ctx.click(w, wait)
            return True
        ctx.scroll(scroll_dy)
    return False


def run_scenario(ctx, steps):
    for i, st in enumerate(steps):
        act = st[0]
        if act == "shot":
            ctx.shot(st[1] if len(st) > 1 else "")
        elif act == "click":
            ok = step_click(ctx, st[1], wait=st[2] if len(st) > 2 else 1.4)
            ctx.expect(f"click[{st[1]}]", ok, "按钮未找到")
        elif act == "type":
            ctx.type_text(st[1])
        elif act == "type_into":
            # st = ("type_into", placeholder_sub, text)：先点对应输入框再键入
            inp = None
            for _ in range(6):
                inp = ctx.find(st[1], "TextInput")
                if inp:
                    break
                ctx.scroll(280)
            if inp:
                ctx.click(inp, 0.7)
                ctx.type_text(st[2])
            ctx.expect(f"type_into[{st[1]}]", inp is not None, "输入框未找到")
        elif act == "scroll":
            ctx.scroll(st[1], st[2] if len(st) > 2 else 1)
        elif act == "wait":
            time.sleep(st[1])
        elif act == "expect_text":
            found = False
            for _ in range(st[2] if len(st) > 2 else 6):
                if any(st[1] in t for t in ctx.labels()):
                    found = True
                    break
                ctx.scroll(st[3] if len(st) > 3 else 280)
            ctx.expect(f"expect_text[{st[1]}]", found)
        elif act == "expect_no_text":
            absent = all(st[1] not in t for t in ctx.labels())
            ctx.expect(f"expect_no_text[{st[1]}]", absent)
        elif act == "expect_jail":
            # st = ("expect_jail", key_path, expected) —— cases.json 断言
            key, expected = st[1], st[2]
            ok = False
            try:
                data = json.loads((JAIL / "cases.json").read_text())
                cases = data.get("cases", [])
                for c in cases:
                    v = c
                    for part in key.split("."):
                        v = v.get(part) if isinstance(v, dict) else None
                    if v == expected:
                        ok = True
                        break
            except Exception:
                pass
            ctx.expect(f"expect_jail[{key}={expected}]", ok)
        elif act == "inject":
            # st = ("inject", filename, json_obj_str)：往 jail 写文件（驱动 pending_plan/
            #   converge 等外部进程契约文件；文件内容须与守护进程真实输出形状一致）
            import json as _ij
            obj = _ij.loads(st[2]) if isinstance(st[2], str) else st[2]
            (JAIL / st[1]).write_text(_ij.dumps(obj, ensure_ascii=False, indent=1))
        elif act == "back_list":
            ok = step_click(ctx, "返回列表", wait=1.6, scroll_dy=-400) or \
                 step_click(ctx, "回到守护列表", wait=1.6, scroll_dy=-400)
            ctx.expect("back_list", ok)
        elif act == "goto_chat":
            # 塞一条消息再点交给管家（空输入只给 hint 不进聊天）
            inp = ctx.find("粘贴群消息", "TextInput")
            if inp:
                ctx.click(inp, 0.7)
                ctx.type_text(st[1] if len(st) > 1 else "看看")
            ok = step_click(ctx, "交给管家", wait=2.2)
            ctx.expect("goto_chat", ok)


def make_video(frames_dir, out_mp4, fps_dur=4):
    """把帧目录串成 mp4（每张 fps_dur 秒）。"""
    cmd = [FFMPEG, "-y", "-framerate", f"1/{fps_dur}", "-i", f"{frames_dir}/%03d.png",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", out_mp4]
    subprocess.run(cmd, check=True, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8146)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--frames", default="")
    ap.add_argument("--video", default="")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--fps-dur", type=int, default=4)
    args = ap.parse_args()

    # 载入剧本（python 文件，导出 STEPS）
    spec = importlib.util.spec_from_file_location("scenario", args.scenario)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    steps = mod.STEPS

    frames_dir = args.frames or None
    ctx = Ctx(args.port, frames_dir, check_only=args.check_only)
    print(f"== scenario {mod.__dict__.get('TITLE', args.scenario)}（{len(steps)} 步）==")
    run_scenario(ctx, steps)

    if not args.check_only and args.video and frames_dir:
        make_video(frames_dir, args.video, args.fps_dur)
        print(f"video: {args.video} ({os.path.getsize(args.video)//1024} KB)")

    if ctx.failures:
        print(f"FAIL {len(ctx.failures)} 步")
        sys.exit(1)
    print("SCENARIO PASS")


if __name__ == "__main__":
    main()
