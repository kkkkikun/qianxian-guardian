"""OUP 客户端（octos serve --stdio --solo 的最小 JSON-RPC 客户端）。
协议细节全部来自本地 octos 二进制实测 + api/OCTOS_UI_PROTOCOL_V1_SPEC：
  - JSON-RPC id 必须是字符串（数字 id 报 -32700）
  - session/open 最小参数 {session_id}；turn_id 必须 UUID
  - InputItem = {"kind":"text","text":...}（serde tag=kind snake_case）
  - 会话即弃策略：每推理任务 open 一次、不 hydrate、用后进程退出
"""
import json
import subprocess
import threading
import time
import uuid


class OupClient:
    def __init__(self, octos_bin: str, data_dir: str, timeout: int = 120):
        self.bin = octos_bin
        self.data_dir = data_dir
        self.timeout = timeout
        self.proc: subprocess.Popen | None = None
        self.lock = threading.Lock()
        self._id = 0

    # ---- 进程生命周期（短会话：open → turn → close） ----
    def start(self) -> None:
        if self.proc and self.proc.poll() is None:
            return
        import os
        env = dict(os.environ, OCTOS_HOME=self.data_dir)
        self.proc = subprocess.Popen(
            [self.bin, "serve", "--stdio", "--solo"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, env=env, bufsize=1,
        )

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
        self.proc = None

    # ---- 请求/响应 ----
    def _next_id(self) -> str:
        with self.lock:
            self._id += 1
            return f"g{self._id}"

    def _call(self, method: str, params: dict, timeout: int | None = None) -> dict:
        if not self.proc or self.proc.poll() is not None:
            raise RuntimeError("octos serve 进程未运行")
        rid = self._next_id()
        req = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method,
                          "params": params}, ensure_ascii=False)
        self.proc.stdin.write(req + "\n")
        self.proc.stdin.flush()
        deadline = time.time() + (timeout or self.timeout)
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("octos serve stdout 关闭")
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue  # 非 JSON 行忽略
            if msg.get("id") == rid:
                if "error" in msg:
                    raise RuntimeError(f"OUP {method} error: {msg['error']}")
                return msg.get("result", {})
            # 通知（turn/started, message/delta, turn/completed...）按需消费
        raise TimeoutError(f"OUP {method} 超时 ({timeout or self.timeout}s)")

    # ---- 高层 API（对应蓝图：按推理任务开短会话） ----
    def reasoning_turn(self, task_id: str, prompt: str, timeout: int = 120) -> str:
        """一次完整的短会话推理：open → turn/start → 收集投影流 → 返回文本。
        实测 octos 2.0.3-rc.13 事件流（v2 projection/envelope，非 spec 旧字段）：
          reasoning_delta… → assistant_delta → assistant_persisted → turn_terminal
        profile 固定 main（其 config.llm 持有 provider/base_url/api_key_env）。
        assistant_persisted 是内核保存的权威答案（官方 ADR 0005：persisted 优先于迟到 delta）。"""
        self.start()
        session_id = f"main:stdio:{task_id}"
        self._call("session/open",
                   {"session_id": session_id, "profile_id": "main"}, timeout=15)
        turn_id = str(uuid.uuid4())
        rid = self._next_id()
        req = json.dumps({"jsonrpc": "2.0", "id": rid, "method": "turn/start",
                          "params": {"session_id": session_id, "turn_id": turn_id,
                                     "input": [{"kind": "text", "text": prompt}]}},
                         ensure_ascii=False)
        self.proc.stdin.write(req + "\n")
        self.proc.stdin.flush()
        deadline = time.time() + timeout
        text_parts, persisted, terminal, final_err = [], None, False, None
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            method = msg.get("method") or ""
            if method == "projection/envelope":
                payload = (msg.get("params") or {}).get("payload") or {}
                ptype = payload.get("type")
                if ptype == "assistant_delta":
                    data = payload.get("data") or {}
                    if data.get("text"):
                        text_parts.append(data["text"])
                elif ptype == "assistant_persisted":
                    persisted = (payload.get("data") or {}).get("text") or payload.get("text")
                elif ptype == "turn_terminal":
                    terminal = True
                    break
            elif method == "turn/completed":
                terminal = True
                break
            elif method == "turn/error":
                final_err = json.dumps(msg.get("params") or {}, ensure_ascii=False)
                break
            elif msg.get("id") == rid and "error" in msg:
                final_err = str(msg["error"])
                break
        if final_err:
            raise RuntimeError(f"turn 失败: {final_err}")
        answer = persisted if persisted is not None else "".join(text_parts)
        if not terminal and not answer:
            raise TimeoutError(f"推理超时（{timeout}s）且无部分输出")
        return (answer or "").strip()

