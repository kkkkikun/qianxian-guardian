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
            "\"bill_total\":\"\"}。op 可选 create(text 必填原文)/confirm(id)/reschedule(id+slot_day+"
            "slot_part)/cancel(id)/add_people(id+people)/set_bill(id+bill_total)，字段值全部双引号字符串，"
            "值内禁用双引号与换行，未抽取到留空，每次回复最多一个 PLAN；3)绝不声称已改状态，用户点"
            "「拍板」后才算数；4)答疑直接回答不带 PLAN；5)发现同时段冲突要提醒。回复中文、简短（≤120字）。")


def turn_text(user_msg):
    return PREAMBLE + "\n\n【当前守护】\n（还没有守护）\n\n【用户消息】\n" + user_msg


def prep_profile(base_url, model, key=""):
    os.makedirs(f"{DATA}/profiles", exist_ok=True)
    now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    family = "local" if base_url else "minimax-cn"
    route = {"api_key_env": "MINIMAX_CN_API_KEY"} if not base_url else {"api_key_env": "LOCAL_API_KEY", "base_url": base_url}
    prof = {"id": "_main", "name": "test", "enabled": True, "created_at": now, "updated_at": now,
            "config": {"llm": {"primary": {"family_id": family, "model_id": model, "route": route}},
                       "env_vars": ({"LOCAL_API_KEY": key} if key else {})}}
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
        deadline = time.time() + secs
        while time.time() < deadline:
            for e in list(self.events):
                s = json.dumps(e, ensure_ascii=False)
                if "PLAN{" in s:
                    return s
            time.sleep(0.5)
        return None


def main():
    real = "--real" in sys.argv
    if real:
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
    print("=== 回包含 PLAN ===" if out else "=== 无 PLAN（超时）===")
    if out:
        print(out[:600])
    k.p.kill()


if __name__ == "__main__":
    main()
