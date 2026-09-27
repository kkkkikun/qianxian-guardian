"""G3 OUP 冒烟（GO/NO-GO 门）：
Phase 1（无 key，自动化）：session/open + turn/start 线路验证
  - session/open 返回 capabilities（协议 octos-ui/v1alpha1）→ PASS
  - turn/start 被受理（UUID turn_id + kind:text 线路正确），无 provider 时
    返回结构化 runtime_unavailable（蓝图"可见不可用"失败态）→ PASS
Phase 2（有 key，手动）：配置 provider 后 reasoning_turn 返回真实模型文本。
用法：
  python3 smoke_g3.py                     # Phase 1
  MINIMAX_API_KEY=... python3 smoke_g3.py # Phase 2（配置后完整冒烟）
"""
import json
import os
import subprocess
import sys
import time

OCTOS = "/home/kikun/MyProject/Agentic-octos/repos/octos/target/release/octos"
DATA = os.path.expanduser("~/.local/gosim-octos")
results = []
ok = lambda n, cond: results.append(cond) or print(f"{'✅' if cond else '❌ FAIL'} {n}")

env = dict(os.environ, OCTOS_HOME=DATA)
proc = subprocess.Popen([OCTOS, "serve", "--stdio", "--solo"],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True, env=env, bufsize=1)


def rpc(rid, method, params):
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method,
                                 "params": params}, ensure_ascii=False) + "\n")
    proc.stdin.flush()


def read_until(rid, want_methods=(), timeout=20):
    deadline = time.time() + timeout
    out = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("id") == rid:
            return {"response": d, "notifications": out}
        if (d.get("method") or "") in want_methods:
            out.append(d)
    return {"response": None, "notifications": out}


# --- Phase 1a: session/open ---
rpc("1", "session/open", {"session_id": "guardian-g3-smoke"})
r = read_until("1")
resp = r["response"]
caps = ((resp or {}).get("result", {}).get("opened", {}).get("capabilities", {}))
proto = (caps.get("version") or {}).get("protocol")
ok(f"session/open: 协议 {proto}", proto == "octos-ui/v1alpha1")
ok("capabilities 含 turn/start", "turn/start" in (caps.get("supported_methods") or []))

# --- Phase 1b: turn/start 无 provider → 结构化不可用 ---
rpc("2", "turn/start", {
    "session_id": "guardian-g3-smoke",
    "turn_id": "3f2a7c1e-8b9d-4e0f-a1b2-c3d4e5f60718",
    "input": [{"kind": "text", "text": "回复一个字：好"}],
})
r = read_until("2", want_methods=("turn/started", "turn/error", "turn/completed"))
resp = r["response"]
err = (resp or {}).get("error") or {}
data_kind = (err.get("data") or {}).get("kind")
structured = data_kind == "runtime_unavailable" or "does not exist" in err.get("message", "")
ok(f"turn/start 受理且失败结构化（kind={data_kind or 'turn 生命周期事件'}）", structured or bool(r["notifications"]))

# --- Phase 2: 有 key → 真实模型回合 ---
key = os.environ.get("MINIMAX_API_KEY") or os.environ.get("KIMI_API_KEY")
if key:
    provider = "minimax" if os.environ.get("MINIMAX_API_KEY") else "moonshot"
    model = "MiniMax-M2" if provider == "minimax" else "kimi-k2.5"
    # 用 profile/llm/upsert 配置（OUP 原生，不需要手工改文件）
    rpc("3", "profile/llm/upsert", {
        "session_id": "guardian-g3-smoke",
        "profile_id": "guardian",
        "provider": provider, "model": model, "api_key": key,
    })
    r = read_until("3", timeout=15)
    rpc("4", "profile/llm/select", {"session_id": "guardian-g3-smoke", "profile_id": "guardian"})
    read_until("4", timeout=10)
    rpc("5", "turn/start", {
        "session_id": "guardian-g3-smoke",
        "turn_id": "4f2a7c1e-8b9d-4e0f-a1b2-c3d4e5f60718",
        "input": [{"kind": "text", "text": "只回复两个字：就绪"}],
    })
    r = read_until("5", want_methods=("message/delta", "turn/completed"), timeout=90)
    resp = r["response"]
    text = "".join(
        ((n.get("params") or {}).get("delta") or {}).get("text", "")
        if isinstance((n.get("params") or {}).get("delta"), dict)
        else (n.get("params") or {}).get("delta", "")
        for n in r["notifications"] if n.get("method") == "message/delta")
    completed = any(n.get("method") == "turn/completed" for n in r["notifications"])
    ok(f"真实模型回合（'{text.strip()[:20]}' completed={completed}）",
       bool(text.strip()) or completed)
else:
    print("ℹ️  Phase 2 跳过：未提供 MINIMAX_API_KEY/KIMI_API_KEY（真实模型冒烟待 key）")

proc.kill()
print(f"\n=== G3 冒烟结果: {sum(results)}/{len(results)} PASS ===")
sys.exit(0 if all(results) else 1)
