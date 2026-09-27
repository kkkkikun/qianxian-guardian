"""G4a 确定性冒烟：P0 全状态可达（无网络，纯 DB 事务）。
覆盖：P0-A 主链（消息→Case→Proposal→organizer 批准→Confirmed→读回）
     + P0-B（based_on_revision 拒旧快照 / 越权拒绝 / 拒绝不落 plan / 改期 Superseded / 取消级联）
"""
import sys

sys.path.insert(0, ".")
from guardian.cases import (CaseError, approve_proposal, cancel_case,
                            create_proposal, mark_rescheduling,
                            reject_proposal)
from guardian.db import DB

results = []
ok = lambda n, cond: results.append(cond) or print(f"{'✅' if cond else '❌ FAIL'} {n}")

db = DB("/tmp/gosim/g4a-smoke.db")
ROOM = "!g4a:127.0.0.1:8128"
ORG = "@rinx_test_a:127.0.0.1:8128"   # 组织者
B = "@rinx_test_b:127.0.0.1:8128"     # 普通成员

# --- Case 建立进 Confirmed 前置态 ---
db.create_case("case-g4a", ROOM, ORG, "ev-src", "Asia/Shanghai")

# --- 1. Proposal 创建（M1）→ AwaitingConfirm + revision++ ---
r = create_proposal(db, "case-g4a", "方案A：周六 09:00 深圳湾骑行", selected_slot="slot_01")
case = dict(db.conn.execute("SELECT * FROM cases WHERE id='case-g4a'").fetchone())
ok(f"提案创建 → AwaitingConfirm（rev {case['revision']} == based_on {r['based_on_revision']}）",
   case["status"] == "AwaitingConfirm" and case["revision"] == r["based_on_revision"])
prop_id = r["proposal_id"]

# --- 2. 越权批准拒绝 ---
try:
    approve_proposal(db, "case-g4a", prop_id, B, "2026-10-03T09:00:00+08:00",
                     "2026-10-03T11:00:00+08:00", place="深圳湾", activity="骑行")
    ok("越权批准被拒", False)
except CaseError as e:
    ok(f"越权批准被拒（{str(e)[:28]}…）", "不是组织者" in str(e))

# --- 3. 组织者批准 → Confirmed + 读回 + M2 回执 + plans Active ---
r = approve_proposal(db, "case-g4a", prop_id, ORG, "2026-10-03T09:00:00+08:00",
                     "2026-10-03T11:00:00+08:00", place="深圳湾", activity="骑行")
case = dict(db.conn.execute("SELECT * FROM cases WHERE id='case-g4a'").fetchone())
plan = dict(db.conn.execute("SELECT * FROM plans WHERE case_id='case-g4a' AND status='Active'").fetchone())
receipt = db.conn.execute("SELECT * FROM outbox WHERE case_id='case-g4a' AND kind='M2'").fetchone()
ok(f"批准 → Confirmed（plan {plan['plan_id'][:9]}… Active，rev {case['revision']}）",
   case["status"] == "Confirmed" and plan["status"] == "Active"
   and plan["source_proposal_id"] == prop_id and receipt is not None)
ok("提案状态 → Approved", dict(db.conn.execute(
    "SELECT status FROM proposals WHERE id=?", (prop_id,)).fetchone())["status"] == "Approved")

# --- 4. 改期流：Rescheduling → 新提案 → 批准 → 旧 plan Superseded ---
mark_rescheduling(db, "case-g4a", ORG)
r2 = create_proposal(db, "case-g4a", "方案B：周日 09:00 深圳湾骑行", selected_slot="slot_02")
prop2 = r2["proposal_id"]
r = approve_proposal(db, "case-g4a", prop2, ORG, "2026-10-04T09:00:00+08:00",
                     "2026-10-04T11:00:00+08:00", place="深圳湾", activity="骑行")
plans = db.conn.execute("SELECT status, count(*) c FROM plans WHERE case_id='case-g4a'"
                        " GROUP BY status").fetchall()
by = {row["status"]: row["c"] for row in plans}
ok(f"改期后 plans：Superseded={by.get('Superseded', 0)}, Active={by.get('Active', 0)}（无重复建 Case）",
   by.get("Superseded") == 1 and by.get("Active") == 1
   and db.conn.execute("SELECT count(*) c FROM cases").fetchone()["c"] == 1)

# --- 5. based_on_revision 不匹配 → 提案 Superseded ---
mark_rescheduling(db, "case-g4a", ORG)
r3 = create_proposal(db, "case-g4a", "方案C：下周六 09:00")
rev_before = db.conn.execute("SELECT revision FROM cases WHERE id='case-g4a'").fetchone()["revision"]
# 模拟快照变化（其他事务推进 revision）
db.conn.execute("UPDATE cases SET revision=revision+1 WHERE id='case-g4a'")
db.conn.commit()
try:
    approve_proposal(db, "case-g4a", r3["proposal_id"], ORG, "2026-10-10T09:00:00+08:00",
                     "2026-10-10T11:00:00+08:00")
    ok("旧快照提案批准被拒", False)
except CaseError as e:
    ok(f"旧快照提案 → Superseded（{str(e)[:24]}…）", "based_on_revision" in str(e))
st = dict(db.conn.execute("SELECT status FROM proposals WHERE id=?", (r3["proposal_id"],)).fetchone())["status"]
ok(f"旧快照提案状态 = {st}", st == "Superseded")

# --- 6. 拒绝流：Proposal=Rejected 历史保留，不落 Active plan ---
# 当前 Case 处于 Proposing（方案C 已 Superseded），可直接出方案 D
r4 = create_proposal(db, "case-g4a", "方案D：雨天室内方案")
r = reject_proposal(db, "case-g4a", r4["proposal_id"], ORG)
pst = dict(db.conn.execute("SELECT status FROM proposals WHERE id=?", (r4["proposal_id"],)).fetchone())["status"]
active_from_rej = db.conn.execute("SELECT count(*) c FROM plans WHERE source_proposal_id=?"
                                  " AND status='Active'", (r4["proposal_id"],)).fetchone()["c"]
case = dict(db.conn.execute("SELECT status FROM cases WHERE id='case-g4a'").fetchone())
ok(f"拒绝 → Proposal={pst}（历史保留），Active plan 引用={active_from_rej}，Case 回 {case['status']}",
   pst == "Rejected" and active_from_rej == 0 and case["status"] == "Proposing")

# --- 7. 取消级联：Cancelled + 任务/待发清理 + 历史保留 ---
db.conn.execute("UPDATE cases SET status='Confirmed' WHERE id='case-g4a'")
db.conn.execute("INSERT INTO scheduled_tasks(id, case_id, kind, due_at, status, created_at)"
                " VALUES ('t-c1', 'case-g4a', 'reminder', '2026-10-02T09:00:00+08:00', 'Pending', '2026-09-27T00:00:00+00:00')")
db.conn.execute("UPDATE plans SET status='Active' WHERE case_id='case-g4a' AND source_proposal_id=?", (prop2,))
db.conn.commit()
r = cancel_case(db, "case-g4a", ORG)
tasks = dict(db.conn.execute("SELECT status, count(*) c FROM scheduled_tasks WHERE case_id='case-g4a'"
                             " GROUP BY status").fetchall().__iter__().__next__()) if False else \
    [dict(x) for x in db.conn.execute("SELECT status, count(*) c FROM scheduled_tasks"
                                      " WHERE case_id='case-g4a' GROUP BY status")]
tasks_cancelled = all(t["status"] == "Cancelled" for t in tasks)
case = dict(db.conn.execute("SELECT status, revision FROM cases WHERE id='case-g4a'").fetchone())
audit_n = db.conn.execute("SELECT count(*) c FROM audit WHERE evidence_ref='case-g4a'").fetchone()["c"]
ok(f"取消 → Cancelled（rev {case['revision']}），未来任务全清={tasks_cancelled}，审计 {audit_n} 条保留",
   case["status"] == "Cancelled" and tasks_cancelled and audit_n >= 5)

print(f"\n=== G4a 冒烟结果: {sum(results)}/{len(results)} PASS ===")
sys.exit(0 if all(results) else 1)
