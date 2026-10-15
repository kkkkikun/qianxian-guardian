#!/usr/bin/env python3
"""
牵线（Qianxian）端侧内置大模型评估基准运行器 (eval_runner.py)
核心评测目标：「稳定、快速、可靠」
"""

import json
import os
import re
import sys
import time
import argparse
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "test_dataset.json")

PREAMBLE = ("你是「牵线」聚会守护管家，帮组织者把群消息变成照顾到收尾的聚会。依据【当前守护】与"
            "【用户消息】工作。规则：1)只从消息原文抽取字段，抽不到就留空并说明「未抽取到」，绝不编造"
            "时间/地点/人物；2)你没有执行权——凡涉及新建/确认/改期/取消/加人/记账，先用一两句人话说明，"
            "然后另起一行输出机器提案，格式固定单行：PLAN{\"op\":\"create\",\"text\":\"消息原文\","
            "\"activity\":\"\",\"slot_day\":\"\",\"slot_part\":\"\",\"place\":\"\",\"people\":\"\","
            "\"bill_total\":\"\"}。op 全集：create(text 必填原文)/confirm/reschedule(+slot_day+slot_part)/"
            "cancel/add_people(+people)/set_bill(+bill_total)/complete/draft_dunning/mark_paid(+who+amount)/"
            "undo（撤销刚取消的，5 秒窗）/clear（清空全部，危险，两段确认）/export（导出，可带 id）——"
            "除 create/clear/export 外都必须包含 \"id\":\"<目标守护数字>\"，缺 id 会被拒，字段值全部双引号字符串，"
            "值内禁用双引号与换行，未抽取到留空，每次回复最多一个 PLAN；3)绝不声称已改状态，用户点"
            "「拍板」后才算数；4)答疑直接回答不带 PLAN；5)发现同时段冲突要提醒。回复中文、简短（≤120字）。")

def build_prompt(user_msg, current_cases="(还没有守护)"):
    return f"{PREAMBLE}\n\n【当前守护】\n{current_cases}\n\n【用户消息】\n{user_msg}"

def parse_plan(text):
    match = re.search(r'PLAN\s*(\{.*?\})', text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except Exception:
        return {"_parse_error": match.group(1)}

def call_openai_compatible(endpoint, model, prompt, temperature=0.0):
    url = f"{endpoint.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 256
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    # 显式禁用代理，避免 localhost/127.0.0.1 被外部 HTTP_PROXY 劫持
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=30) as resp:
            t1 = time.time()
            res = json.loads(resp.read().decode("utf-8"))
            content = res["choices"][0]["message"]["content"]
            usage = res.get("usage", {})
            total_tokens = usage.get("completion_tokens", len(content) // 2)
            duration = t1 - t0
            tps = total_tokens / duration if duration > 0 else 0
            return {
                "content": content,
                "duration": duration,
                "tokens": total_tokens,
                "tps": tps,
                "success": True
            }
    except Exception as e:
        return {
            "content": "",
            "duration": time.time() - t0,
            "tokens": 0,
            "tps": 0,
            "success": False,
            "error": str(e)
        }


def evaluate_case(case, output_res):
    text = output_res.get("content", "")
    plan = parse_plan(text)
    reasons = []
    passed = True

    expected_op = case.get("expected_op")
    if expected_op is None:
        if plan is not None:
            passed = False
            reasons.append("预期不产出 PLAN（纯问答），但模型输出了 PLAN")
        if "must_not_contain" in case:
            for item in case["must_not_contain"]:
                if item in text:
                    passed = False
                    reasons.append(f"包含禁止字段: {item}")
        return passed, reasons, plan

    if plan is None:
        return False, ["未能提取出合法的 PLAN{...} 结构"], None

    if "_parse_error" in plan:
        return False, [f"PLAN 格式非合法 JSON: {plan['_parse_error']}"], None

    actual_op = plan.get("op")
    if actual_op != expected_op:
        passed = False
        reasons.append(f"op 不匹配: 预期 '{expected_op}', 实际 '{actual_op}'")

    required_fields = case.get("required_fields", {})
    for k, v in required_fields.items():
        actual_val = str(plan.get(k, "")).strip()
        if not actual_val:
            passed = False
            reasons.append(f"缺少必填字段 {k}（预期包含 '{v}'）")
        elif v and v not in actual_val:
            passed = False
            reasons.append(f"字段 {k} 内容偏差: 预期包含 '{v}', 实际为 '{actual_val}'")

    for k in case.get("assert_empty_or_unextracted", []):
        actual_val = str(plan.get(k, "")).strip()
        if actual_val and actual_val != "未抽取到":
            passed = False
            reasons.append(f"违反 no-facts 铁律！字段 {k} 应留空或标记'未抽取到'，实际编造为: '{actual_val}'")

    for item in case.get("forbidden_hallucinations", []):
        if item in text:
            passed = False
            reasons.append(f"检测到虚假编造事实（幻觉词）: '{item}'")

    if "must_contain_warning" in case:
        warning_word = case["must_contain_warning"]
        if warning_word not in text:
            passed = False
            reasons.append(f"未检测到预期的冲突预警词: '{warning_word}'")

    return passed, reasons, plan

def run_suite(endpoint, model, repeat=1):
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"\n=======================================================")
    print(f"  牵线端侧大模型基准测试启动")
    print(f"  评测模型: {model}")
    print(f"  测试终端: {endpoint}")
    print(f"  测试用例数: {len(dataset['cases'])}，重复轮次: {repeat}")
    print(f"=======================================================\n")

    results = []
    total_duration = 0.0
    total_tokens = 0
    pass_count = 0
    total_runs = 0

    for case in dataset["cases"]:
        cid = case["id"]
        desc = case["description"]
        print(f"[{cid}] {desc} ... ", end="", flush=True)

        case_passed = True
        case_durations = []
        case_tps = []
        last_out = None
        last_reasons = []

        for r in range(repeat):
            total_runs += 1
            prompt = build_prompt(case["user_message"], case.get("current_cases", "(还没有守护)"))
            res = call_openai_compatible(endpoint, model, prompt)
            last_out = res
            if not res["success"]:
                case_passed = False
                last_reasons.append(f"网络/服务异常: {res.get('error')}")
                continue

            case_durations.append(res["duration"])
            case_tps.append(res["tps"])
            total_duration += res["duration"]
            total_tokens += res["tokens"]

            p, reasons, plan = evaluate_case(case, res)
            if not p:
                case_passed = False
                last_reasons.extend(reasons)

        if case_passed:
            pass_count += 1
            avg_dur = sum(case_durations) / len(case_durations) if case_durations else 0
            avg_tps = sum(case_tps) / len(case_tps) if case_tps else 0
            print(f"✓ PASS (平均耗时: {avg_dur:.2f}s, 吞吐: {avg_tps:.1f} tps)")
        else:
            print(f"✗ FAIL")
            for reason in last_reasons:
                print(f"    - 原因: {reason}")
            if last_out and last_out["content"]:
                print(f"    - 模型原始输出: {repr(last_out['content'][:120])}")

        results.append({
            "id": cid,
            "desc": desc,
            "passed": case_passed,
            "avg_duration": sum(case_durations) / len(case_durations) if case_durations else 0,
            "avg_tps": sum(case_tps) / len(case_tps) if case_tps else 0,
            "reasons": last_reasons
        })

    pass_rate = (pass_count / len(dataset["cases"])) * 100
    overall_tps = total_tokens / total_duration if total_duration > 0 else 0

    print(f"\n=======================================================")
    print(f"  评测总结报告 (Model: {model})")
    print(f"=======================================================")
    print(f"  可靠性 (Pass Rate) : {pass_rate:.1f}% ({pass_count}/{len(dataset['cases'])})")
    print(f"  生成速度 (Avg TPS) : {overall_tps:.1f} tokens/s")
    print(f"  平均单轮交互延迟   : {total_duration / total_runs:.2f} s")
    print(f"=======================================================\n")

    return results

def main():
    parser = argparse.ArgumentParser(description="牵线端侧大模型基准测试器")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080", help="OpenAI兼容服务地址 (默认 http://127.0.0.1:8080)")
    parser.add_argument("--model", default="qwen2.5-0.5b", help="模型标识符")
    parser.add_argument("--repeat", type=int, default=1, help="单Case重复评测轮数（测试稳定性与方差）")
    args = parser.parse_args()

    run_suite(args.endpoint, args.model, args.repeat)

if __name__ == "__main__":
    main()
