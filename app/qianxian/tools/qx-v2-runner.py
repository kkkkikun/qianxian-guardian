#!/usr/bin/env python3
"""qx-v2-runner: 起 card-host + 跑 qx-verify-v2 三轮 + 终止。"""
import os
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)
os.environ["OCTO_CARD_HOST"] = "/home/kikun/MyProject/Agentic-octos/.build-hub-926/OctoSense-App-Hub/target/release/card-host"
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import subprocess, time, urllib.request, sys, pathlib

def start_card_host(ad):
    subprocess.run(["pkill", "-f", "card-host --bundle"], capture_output=True)
    time.sleep(1.0)
    pathlib.Path(ad).joinpath("qianxian").mkdir(parents=True, exist_ok=True)
    cj = pathlib.Path(ad) / "qianxian" / "cases.json"
    cj.unlink(missing_ok=True)
    p = subprocess.Popen(
        ["python3",
          "/home/kikun/MyProject/Agentic-octos/octosense-ws/OctoScript-App-Design-Flow/tools/octo",
          "run", "bundle", "--port", "8146", "--detach", "--hidden", "--app-data", ad],
        stdout=open("/tmp/v2-runner.log", "ab"), stderr=subprocess.STDOUT,
        cwd="/home/kikun/MyProject/Agentic-octos/my-entry/app/qianxian",
        env=os.environ, start_new_session=True)
    ready = False
    for _ in range(60):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8146/snap", timeout=2) as r:
                if r.status == 200:
                    ready = True
                    break
        except Exception:
            pass
        time.sleep(1.0)
    return p, ready

ad = "/tmp/qx-outer34"
p, ready = start_card_host(ad)
print(f"card-host ready={ready} pid={p.pid}", flush=True)
if not ready:
    p.terminate(); sys.exit(1)

try:
    for r in (1, 2, 3):
        print(f"\n=== v2 round {r} ===", flush=True)
        rc = subprocess.call(
            ["python3", "tools/qx-verify-v2.py"],
            cwd="/home/kikun/MyProject/Agentic-octos/my-entry/app/qianxian",
            env=os.environ)
        print(f"round {r} exit={rc}", flush=True)
        if r < 3:
            p.terminate(); time.sleep(1.5)
            p, ready = start_card_host(ad)
            print(f"  restart ready={ready}", flush=True)
            if not ready: break
finally:
    p.terminate()
    try: p.wait(timeout=3)
    except Exception: p.kill()