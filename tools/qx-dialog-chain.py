#!/usr/bin/env python3
"""WP2 纯对话全链 + op 覆盖链：真内核（octos serve --stdio）× 剧本 mock × 管家提示词。

两条链：
  --ops       12 个 PLAN op 全集：逐意图发话 → 断言回复含对应 PLAN{"op":...}
              （agent 能正确表达每个 op——执行端白名单校验的 app 侧覆盖在回归 R-35）。
  --lifecycle 全生命周期多轮：create → confirm → reschedule → add_people → set_bill
              → mark_paid → complete → draft_dunning → cancel → undo → export → clear，
              每回合断言 PLAN 合规且 op 顺序正确（纯对话，无 UI；拍板等价物=剧本推进）。

诚实边界：本链验证「提示词→内核→模型→PLAN 回包」段；PLAN→白名单执行段由
card-host 回归（R-26/27 拍板链）与 Rinx 真宿主 e2e（s4 证据）覆盖。
mock 是剧本化 OpenAI 兼容服务（tools/qx-mock-llm.py），真模型轮次见 --kimi 变体
（tools/qx-kernel-turn.py --kimi 的历史证据在 evidence/v100-wp4-proactive）。

用法：python3 tools/qx-dialog-chain.py [--ops|--lifecycle]   # 缺省两条都跑
"""
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import time
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("qx_kernel_turn", ROOT / "tools" / "qx-kernel-turn.py")
kt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kt)

MOCK = ROOT / "tools" / "qx-mock-llm.py"

OPS_CHAIN = [  # (发话意图文本, 期望 op)
    ("周六上午去深圳湾骑车", "create"),
    ("第 1 条信息齐了，确认吧", "confirm"),
    ("改到周日下午吧", "reschedule"),
    ("加人：阿明、小红也来", "add_people"),
    ("记 AA 总额 300", "set_bill"),
    ("阿明已付款 100", "mark_paid"),
    ("办完了，标记完成", "complete"),
    ("催一下还没交的人", "draft_dunning"),
    ("取消这条吧", "cancel"),
    ("撤销刚才的取消", "undo"),
    ("导出数据", "export"),
    ("清空全部", "clear"),
]

LIFECYCLE = ["create", "confirm", "reschedule", "add_people", "set_bill",
             "mark_paid", "complete", "draft_dunning", "cancel", "undo",
             "export", "clear"]


def plan_op_of(reply):
    # 多轮累积文本里可能有多条 PLAN（尾随和拼接行都会撞 JSON 解析）——取最后一条合法 PLAN
    op = ""
    for line in reply.splitlines():
        line = line.strip()
        if "PLAN{" in line:
            seg = line[line.index("PLAN{") + 4:]  # 从 { 起截（PLAN{ 的 { 是 JSON 起点）
            # 行尾可能粘着下一段文本：逐个右括号回退找可解析前缀
            while seg:
                try:
                    return json.loads(seg).get("op", "") or op
                except Exception:
                    i = seg.rfind("}")
                    seg = seg[:i + 1] if i > 0 else ""
    return op


def run_chain(k, label, failfast=False):
    fails = []
    seen = []
    for text, want in OPS_CHAIN:
        k.events.clear()  # 多轮累积：wait_reply 从事件列表重建全文，逐回合清空防串台
        k.call("turn/start", {"session_id": "_main:cli:qxchain",
                              "input": [{"kind": "text", "text": kt.turn_text(text)}],
                              "turn_id": str(uuid.uuid4())})
        reply = k.wait_reply()
        got = plan_op_of(reply)
        okk = got == want
        seen.append(got)
        print(f"  [{'PASS' if okk else 'FAIL'}] 「{text[:14]}…」→ op={got or '（无）'}（期望 {want}）", flush=True)
        if not okk:
            fails.append((text, want, got))
            if failfast:
                break
        time.sleep(0.3)
    if label == "lifecycle":
        # 顺序断言：全链 op 序列必须等于剧本生命周期序
        order_ok = seen == LIFECYCLE
        print(f"  [{'PASS' if order_ok else 'FAIL'}] 生命周期 op 顺序 = {LIFECYCLE}", flush=True)
        if not order_ok:
            fails.append(("order", LIFECYCLE, seen))
    return fails


def main():
    which = set()
    if "--ops" in sys.argv:
        which.add("ops")
    if "--lifecycle" in sys.argv:
        which.add("lifecycle")
    if not which:
        which = {"ops", "lifecycle"}

    mock = subprocess.Popen([sys.executable, str(MOCK), "8181"],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        time.sleep(1.0)  # 等端口起来（首行打印端口号）
        # 内核 profile 指向 mock（local family + base_url；key 无所谓）
        kt.prep_profile("http://127.0.0.1:8181/v1", "qx-mock", key="", family=None)
        # 代理 hijack 防护：内核子进程继承本进程 env——127.0.0.1 的 mock 不能走代理
        for _v in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
            os.environ.pop(_v, None)
        k = kt.Kernel()
        # session/open（协议形状照 qx-kernel-turn 实测：caller 选 session_id）
        r = k.call("session/open", {"session_id": "_main:cli:qxchain", "profile_id": "_main"})
        print("[open]", str(r)[:100], flush=True)
        k.events.clear()

        all_fails = []
        if "ops" in which:
            print("== op 覆盖链（12 op 全集）==", flush=True)
            all_fails += run_chain(k, "ops")
        if "lifecycle" in which:
            print("== 纯对话全生命周期链 ==", flush=True)
            all_fails += run_chain(k, "lifecycle")
        k.p.terminate()

        print()
        if all_fails:
            print(f"DIALOG-CHAIN FAIL {len(all_fails)}: {all_fails[:3]}", flush=True)
            sys.exit(1)
        print("DIALOG-CHAIN ALL PASS", flush=True)
    finally:
        mock.terminate()


if __name__ == "__main__":
    main()
