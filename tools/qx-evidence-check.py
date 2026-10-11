#!/usr/bin/env python3
"""Evidence Pack 离线校验：评审拿到 evidence/case-*.json 后可独立验真。

校验三件事：
  1. 确定性断言：outstanding == bill_total - paid_total（金额全部可由
     people/bill_total/payments 重算，无需信任 app）；
  2. 审计链完整：每条 audit 行格式合法、时间戳单调递增、actor ∈ {user, agent}；
  3. 状态一致：case.bill_cleared 与 outstanding（>0 → no，==0 → yes）互洽。

用法：python3 qx-evidence-check.py <evidence/case-1.json> [更多.json...]
退出码 0 = 全部通过。
"""
import json
import sys
from datetime import datetime

failures = []


def check(path):
    ok = True
    ev = json.loads(open(path).read())
    case = ev["case"]
    led = ev["ledger"]
    cid = case["id"]

    # 1. 确定性断言重算
    people = [p.strip() for p in (case.get("people") or "").split(",") if p.strip()]
    total = float(case.get("bill_total") or 0)
    n = len(people)
    due = total / n if n else 0.0
    outstanding = total - (float(led["paid_total"]) if led.get("paid_total") else 0.0)
    if abs(due - float(led["due_per_person"])) > 0.005:
        failures.append(f"case-{cid}: 应付不符 {due} != {led['due_per_person']}")
        ok = False
    if abs(outstanding - float(led["outstanding"])) > 0.005:
        failures.append(f"case-{cid}: 差额不符 {outstanding} != {led['outstanding']}")
        ok = False
    # 审计里的 payment 记录与 paid_total 互洽
    pay_sum = 0.0
    for line in ev.get("audit", []):
        if "| payment |" in line and f"#{cid} " in line:
            try:
                pay_sum += float(line.rsplit("¥", 1)[1])
            except (ValueError, IndexError):
                pass
    if abs(pay_sum - float(led["paid_total"])) > 0.005:
        failures.append(f"case-{cid}: 审计收款合计 {pay_sum} != paid_total {led['paid_total']}")
        ok = False

    # 2. 审计链
    ts_list = []
    for line in ev.get("audit", []):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 4:
            failures.append(f"case-{cid}: 审计行格式非法: {line[:60]}")
            ok = False
            continue
        ts, actor, action, detail = parts
        if actor not in ("user", "agent"):
            failures.append(f"case-{cid}: actor 非法: {actor}")
            ok = False
        try:
            ts_list.append(datetime.fromisoformat(ts.replace("Z+8", "")))
        except ValueError:
            failures.append(f"case-{cid}: 时间戳非法: {ts}")
            ok = False
    if ts_list != sorted(ts_list):
        failures.append(f"case-{cid}: 审计时间戳非单调递增")
        ok = False

    # 3. 清零一致性
    cleared = case.get("bill_cleared")
    if total > 0 and n > 0:
        want = "yes" if outstanding <= 0.005 else "no"
        if cleared != want:
            failures.append(f"case-{cid}: bill_cleared={cleared} 与 outstanding={outstanding} 不一致（应为 {want}）")
            ok = False

    print(("PASS " if ok else "FAIL ") + path)
    return ok


if __name__ == "__main__":
    paths = sys.argv[1:]
    if not paths:
        print(__doc__)
        sys.exit(2)
    all_ok = all(check(p) for p in paths)
    if failures:
        print("\n".join("  - " + f for f in failures))
    sys.exit(0 if all_ok else 1)
