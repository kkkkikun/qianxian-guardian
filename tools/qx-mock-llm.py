#!/usr/bin/env python3
"""S4 真宿主验证用：剧本化 OpenAI 兼容模型（Rinx standalone local + octos 内核）。

照官方 Rinx tests/fixtures/mock_llm.py 的响应形状（非流式 JSON + 流式 SSE 两种都支持），
但回复内容按【用户消息】内容剧本化，用于确定性地驱动「牵线」管家的 PLAN 提案→拍板链：

  含 骑车/深圳湾 → 抽取说明 + PLAN create（周六-上午 骑车 深圳湾）
  含 改到        → 改期说明 + PLAN reschedule（id=1 → 周日-下午）
  含 确认        → PLAN confirm（id=1）
  含 加上.*人/加人 → PLAN add_people（id=1, 阿明,小红）
  含 记.*AA|AA.*300 → PLAN set_bill（id=1, 300）
  含 取消        → PLAN cancel（id=1）
  其余           → ECHO 回显末行（证明通路，无提案）

用法：python3 qx-mock-llm.py [port]   # 缺省自动选端口；stdout 首行打印端口号
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def user_text(body):
    for message in reversed(body.get("messages", [])):
        if message.get("role") == "user":
            content = message.get("content")
            if isinstance(content, list):
                return " ".join(p.get("text", "") for p in content if isinstance(p, dict))
            return content or ""
    return ""


def scripted(text):
    # turn 文本里【用户消息】之后才是用户真正说的话；内核多轮会重建 prompt
    # （prompt_replaced），守护摘要（含活动词）会并入最后一条用户消息——
    # 所以意图词（改期/确认/取消/加人/记账）必须排在活动词（骑车等）之前判定。
    seg = text.split("【用户消息】")
    msg = seg[-1] if len(seg) >= 2 else text
    if "改到" in msg or "改期" in msg:
        return ("好的，改到周日下午——避开周六上午那条，不再撞车。拍板后生效。\n"
                'PLAN{"op":"reschedule","id":"1","slot_day":"周日","slot_part":"下午"}')
    if "确认" in msg:
        return ("第 1 条信息齐了，确认后我出回执并登记 T-24h 提醒。拍板即确认。\n"
                'PLAN{"op":"confirm","id":"1"}')
    if "取消" in msg:
        return ("明白，取消第 1 条。拍板后进入 5 秒撤销窗口，反悔还来得及。\n"
                'PLAN{"op":"cancel","id":"1"}')
    if "加人" in msg or ("阿明" in msg and "小红" in msg):
        return ("收到，把阿明和小红加进第 1 条的参与人（AA 均摊会跟着人头算）。\n"
                'PLAN{"op":"add_people","id":"1","people":"阿明,小红"}')
    if "AA" in msg or "记账" in msg:
        return ("记上了：第 1 条 AA 总额 300，按参与人人数均摊。拍板后入账。\n"
                'PLAN{"op":"set_bill","id":"1","bill_total":"300"}')
    if "骑车" in msg or "深圳湾" in msg:
        return ("消息里抽到：周六上午在深圳湾骑车，活动/时间/地点都齐了。"
                "建议现在建守护盯住这条，拍板即生效。\n"
                'PLAN{"op":"create","text":"周六上午去深圳湾骑车","activity":"骑车",'
                '"slot_day":"周六","slot_part":"上午","place":"深圳湾","people":"","bill_total":""}')
    return "ECHO: " + (msg.strip().splitlines()[-1] if msg.strip() else "")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path.endswith("/models"):
            self._json({"object": "list", "data": [{"id": "qx-mock", "object": "model"}]})
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("content-length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        reply = scripted(user_text(body))
        if body.get("stream"):
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            for chunk in [reply[: len(reply) // 2], reply[len(reply) // 2:]]:
                event = {"id": "c1", "object": "chat.completion.chunk", "model": "qx-mock",
                         "choices": [{"index": 0, "delta": {"role": "assistant", "content": chunk}, "finish_reason": None}]}
                self.wfile.write(b"data: " + json.dumps(event).encode() + b"\n\n")
            done = {"id": "c1", "object": "chat.completion.chunk", "model": "qx-mock",
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
            self.wfile.write(b"data: " + json.dumps(done).encode() + b"\n\n")
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        else:
            self._json({"id": "c1", "object": "chat.completion", "model": "qx-mock",
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": reply}, "finish_reason": "stop"}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}})

    def _json(self, value):
        data = json.dumps(value).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(server.server_address[1], flush=True)
    server.serve_forever()
