#!/usr/bin/env python3
"""qx-edge-runner: 起 card-host + 跑 qx-edge-v1 + 终止。"""
import os
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)
os.environ["OCTO_CARD_HOST"] = "/home/kikun/MyProject/Agentic-octos/.build-hub-926/OctoSense-App-Hub/target/release/card-host"
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import subprocess, time, urllib.request, sys, pathlib

subprocess.run(["pkill", "-f", "card-host --bundle"], capture_output=True)
time.sleep(1.0)
ad = "/tmp/qx-edge"
pathlib.Path(ad).joinpath("qianxian").mkdir(parents=True, exist_ok=True)
cj = pathlib.Path(ad) / "qianxian" / "cases.json"
for bk in pathlib.Path(ad).rglob("cases.corrupt-*.json"):
    bk.unlink()
cj.unlink(missing_ok=True)

log = open("/tmp/edge-runner.log", "ab")
p = subprocess.Popen(
    ["python3",
     "/home/kikun/MyProject/Agentic-octos/octosense-ws/OctoScript-App-Design-Flow/tools/octo",
     "run", "bundle", "--port", "8146", "--detach", "--hidden", "--app-data", ad],
    stdout=log, stderr=subprocess.STDOUT,
    cwd="/home/kikun/MyProject/Agentic-octos/my-entry/app/qianxian",
    env=os.environ, start_new_session=True)
print(f"card-host pid={p.pid}", flush=True)

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
print(f"card-host ready: {ready}", flush=True)

if not ready:
    log.close()
    print("ABORT", open("/tmp/edge-runner.log").read()[-2000:], flush=True)
    p.terminate(); sys.exit(1)

try:
    rc = subprocess.call(
        ["python3", "tools/qx-edge-v1.py"],
        cwd="/home/kikun/MyProject/Agentic-octos/my-entry/app/qianxian",
        env=os.environ)
    print(f"\nqx-edge-v1 exit: {rc}", flush=True)
finally:
    p.terminate()
    try: p.wait(timeout=3)
    except Exception: p.kill()
    log.close()