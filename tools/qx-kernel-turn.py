#!/usr/bin/env python3
"""S4-a 内核直连证明：真实 `octos serve --stdio` 内核 × mock LLM × 管家提示词。

不经过任何宿主 UI——直接对内核说 NDJSON JSON-RPC：
  session/open → turn/start(input=build_agent_turn 同款提示词) → 收流式事件 → 断言
回复含 PLAN{...}。用于证明「提示词 → 内核 → 模型 → PLAN 形态回包」这一段在真内核上成立
（Rinx 宿主侧的 peer 记账问题见 evidence；该断点已用官方 standalone_local 测试定性）。

用法：python3 qx-kernel-turn.py [--real]   # --real 切 MiniMax 真模型（读 ~/.secrets）
"""
import json
import os
import subprocess
import sys
import uuid
import threading
import time

KERNEL = "/home/kikun/MyProject/Agentic-octos/repos/octos/target/release/octos"
DATA = "/tmp/qx-kernel-data"
MOCK_PORT = 8181

PREAMBLE = ("你是「牵线」聚会守护管家，帮组织者把群消息变成照顾到收尾的聚会。依据【当前守护】与"
            "【用户消息】工作。规则：1)只从消息原文抽取字段，抽不到就留空并说明「未抽取到」，绝不编造"
            "时间/地点/人物；2)你没有执行权——凡涉及新建/确认/改期/取消/加人/记账，先用一两句人话说明，"
            "然后另起一行输出机器提案，格式固定单行：PLAN{\"op\":\"create\",\"text\":\"消息原文\","
            "\"activity\":\"\",\"slot_day\":\"\",\"slot_part\":\"\",\"place\":\"\",\"people\":\"\","
            "\"bill_total\":\"\"}。op 全集：create(text 必填原文)/confirm/reschedule(+slot_day+slot_part)/"
            "cancel/add_people(+people)/set_bill(+bill_total)/complete/draft_dunning/mark_paid(+who+amount)/"
            "undo（撤销刚取消的，5 秒窗）/clear（清空全部，危险，两段确认）/export（导出，可带 id）——"
            "除 create/clear/export 外都必须包含 \"id\":\"<目标守护数字>\"（例 "
            "{\"op\":\"confirm\",\"id\":\"2\"}），缺 id 会被拒，字段值全部双引号字符串，"
            "值内禁用双引号与换行，未抽取到留空，每次回复最多一个 PLAN；3)绝不声称已改状态，用户点"
            "「拍板」后才算数；4)答疑直接回答不带 PLAN；5)发现同时段冲突要提醒。回复中文、简短（≤120字）。")


def turn_text(user_msg):
    return PREAMBLE + "\n\n【当前守护】\n（还没有守护）\n\n【用户消息】\n" + user_msg


def prep_profile(base_url, model, key="", family=None):
    os.makedirs(f"{DATA}/profiles", exist_ok=True)
    now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    if base_url:
        family = "local"
        route = {"api_key_env": "LOCAL_API_KEY", "base_url": base_url}
        env_vars = {"LOCAL_API_KEY": key} if key else {}
    else:
        # family 由调用方显式指定：minimax-cn / moonshot-coding（Kimi Coding Plan，
        # registry/moonshot_coding.rs：https://api.kimi.com/coding/v1，OpenAI 兼容）
        if family == "moonshot-coding":
            route = {"api_key_env": "KIMI_CODING_API_KEY"}
            env_vars = {"KIMI_CODING_API_KEY": key}
        else:
            route = {"api_key_env": "MINIMAX_CN_API_KEY"}
            env_vars = {}
    prof = {"id": "_main", "name": "test", "enabled": True, "created_at": now, "updated_at": now,
            "config": {"llm": {"primary": {"family_id": family, "model_id": model, "route": route}},
                       "env_vars": env_vars}}
    json.dump(prof, open(f"{DATA}/profiles/_main.json", "w"), indent=2)


class Kernel:
    def __init__(self):
        self.p = subprocess.Popen([KERNEL, "serve", "--stdio", "--data-dir", DATA],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.rid = 0
        self.events = []
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.p.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self.events.append(json.loads(line))
            except Exception:
                pass

    def call(self, method, params):
        self.rid += 1
        # 该内核要求字符串 id（数字 id 直接报 -32700）
        req = {"jsonrpc": "2.0", "id": "r%d" % self.rid, "method": method, "params": params}
        self.p.stdin.write(json.dumps(req) + "\n")
        self.p.stdin.flush()
        # 等 id 匹配的 result
        deadline = time.time() + 90
        while time.time() < deadline:
            for e in list(self.events):
                if e.get("id") == "r%d" % self.rid:
                    self.events.remove(e)
                    return e
            time.sleep(0.2)
        raise TimeoutError(method)

    def wait_reply(self, secs=120):
        """收集 assistant_delta 累积文本；见到 PLAN 后再等静默期排空剩余分片。"""
        deadline = time.time() + secs
        text = ""
        seen_plan_at = None
        while time.time() < deadline:
            cur = ""
            for e in list(self.events):
                p = (e.get("params") or {}).get("payload") or {}
                if e.get("method") == "projection/envelope" and p.get("type") == "assistant_delta":
                    cur += p.get("data", {}).get("text", "")
            if cur and cur != text:
                text = cur
                seen_plan_at = time.time() if "PLAN{" in text else None
            elif seen_plan_at and time.time() - seen_plan_at > 5:
                break  # 5s 静默：分片已排空
            time.sleep(0.4)
        return text


def main():
    real = "--real" in sys.argv
    kimi = "--kimi" in sys.argv
    if kimi:
        # Kimi Coding Plan 真模型（用户提供 key，.secrets/ 不入库；2026-10-11 实测
        # PLAN 协议合规 + get_weather function calling，5-10s 出全量回复）。
        # 注意：key 只进 profile env_vars——ambient 环境变量会让内核把 kimi-* 模型
        # 误探测到普通 moonshot family（api.moonshot.ai），coding key 被拒 → 启动失败。
        key = open("/home/kikun/MyProject/Agentic-octos/.secrets/kimi-api-key").read().strip()
        prep_profile(None, "kimi-for-coding", key=key, family="moonshot-coding")
    elif real:
        # 内环同款：内核原生 minimax-cn provider（scripts/qx-dispatch.sh 通路，网络实测可达）
        key = open("/home/kikun/MyProject/Agentic-octos/.secrets/minimax_cn.key").read().strip()
        os.environ["MINIMAX_CN_API_KEY"] = key
        prep_profile(None, "MiniMax-M3")
    else:
        prep_profile(f"http://127.0.0.1:{MOCK_PORT}/v1", "qx-mock")
    k = Kernel()
    r = k.call("session/open", {"session_id": "_main:cli:qx", "profile_id": "_main"})
    print("[open]", str(r)[:120])
    r2 = k.call("turn/start", {"session_id": "_main:cli:qx",
                               "input": [{"kind": "text", "text": turn_text("周六上午去深圳湾骑车")}], "turn_id": str(uuid.uuid4())})
    print("[turn/start]", str(r2)[:120])
    out = k.wait_reply()
    print("=== 回包含 PLAN ===" if "PLAN{" in out else "=== 无 PLAN（超时）===")
    print("ASSISTANT_TEXT_BEGIN")
    print(out)
    print("ASSISTANT_TEXT_END")
    time.sleep(1)
    k.p.kill()


if __name__ == "__main__":
    main()
