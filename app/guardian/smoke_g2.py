"""G2 冒烟：分诊/时间归一化/关联判定/台账解析 — 全部纯函数，无网络。"""
import sys
from datetime import datetime

sys.path.insert(0, ".")
from guardian.triage import triage, normalize_time, associate, parse_ledger

NOW = datetime(2026, 9, 28, 12, 0, 0)  # 周一（演示基准）
results = []
ok = lambda n, cond: results.append(cond) or print(f"{'✅' if cond else '❌ FAIL'} {n}")

# --- 分诊命中表（演示剧本） ---
script = [
    ("周六上午去深圳湾骑车，大概两小时？", ["intent", "time"]),
    ("改周日吧", ["change", "time"]),
    ("取消吧，下雨了", ["cancel"]),
    ("我可以，算我一个", ["rsvp"]),
    ("我垫了 88", ["ledger"]),
    ("今天天气不错", ["time"]),
    ("哈哈哈哈", []),
]
for body, want in script:
    t = triage(body)
    got = [k for k in ("intent", "change", "cancel", "rsvp", "ledger") if k in t.kinds]
    got += ["time"] if "time_word" in t.rules else []
    hit_ok = (set(got) == set(want)) and (t.hit == bool(want))
    ok(f"分诊 '{body[:16]}…' → {got or ['未命中']}", hit_ok)

# --- 误报检查（验收 1：误报 ≤1） ---
noise = ["哈哈哈哈这游戏太好笑了", "今天股市怎么样", "这周要交作业"]
fp = sum(1 for b in noise if triage(b).hit)
ok(f"噪声误报 {fp}/3（≤1）", fp <= 1)

# --- 时间归一化 ---
r = normalize_time("周六上午去深圳湾骑车，大概两小时？", NOW)
ok(f"'周六上午…两小时' → {r[0].isoformat() if r else None}（应为下周六 09:00+08:00, +2h）",
   r and r[0].weekday() == 5 and r[0].hour == 9 and (r[1] - r[0]).total_seconds() == 2 * 3600)
r2 = normalize_time("改周日吧", NOW)
ok(f"'改周日吧' → 周日 {r2[0].date()}", r2 and r2[0].weekday() == 6)
r3 = normalize_time("晚上8点吃饭", NOW)
ok(f"'晚上8点' → 20:00", r3 and r3[0].hour == 20)
ok("无可解析时间 → None", normalize_time("随便什么时候都行", NOW) is None)

# --- Case 关联判定 ---
t_intent = triage("下周找个时间看电影？")
ok("新意图 + 已有 Case → pending_intent", associate(t_intent, True) == "pending_intent")
ok("新意图 + 无 Case → new_case", associate(t_intent, False) == "new_case")
t_change = triage("改周日吧")
ok("改口 + 已有 Case → existing", associate(t_change, True) == "existing")
ok("改口 + 无 Case → unrelated（变更语义对无 Case 无意义）",
   associate(t_change, False) == "unrelated")
t_noise = triage("哈哈哈哈")
ok("噪声 → unrelated", associate(t_noise, True) == "unrelated")

# --- 台账确定性解析 ---
p = parse_ledger("我垫了 88", ["@rinx_test_b:127.0.0.1:8128"])
ok(f"'我垫了 88' → payer=sender, amount_cents={p[1] if p else None}（8800）",
   p and p[1] == 8800)
ok("非台账文本 → None", parse_ledger("今天天气不错", []) is None)

print(f"\n=== G2 冒烟结果: {sum(results)}/{len(results)} PASS ===")
sys.exit(0 if all(results) else 1)
