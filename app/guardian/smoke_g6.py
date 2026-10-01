"""G6 真实提醒动作冒烟（确定性，无网络；#37 外环批准的越界增强）：
批准提案 →（同事务）登记 T-24h 提醒任务 → 到期 sweep → 真发 Matrix 房间消息
+ 发送失败 → NeedsRecovery（同 txn 重试，不重复投递）
+ 发送后崩溃窗口（Running）→ 重扫 → 同 txn 幂等重放，仍只投递一次
+ matrix=None 退化补偿语义（smoke_g5 兼容）
"""
import sys

sys.path.insert(0, ".")
from guardian.cases import approve_proposal, create_proposal
from guardian.config import load
from guardian.db import DB
from guardian.main import sweep_scheduler
from guardian.scheduler import reminder_due

results = []
ok = lambda n, cond: results.append(bool(cond)) or print(f"{'✅' if cond else '❌ FAIL'} {n}")


class FakeMatrix:
    """记录发送；可按 txn 注入失败；txn 幂等（同 txn 只投递一次）。"""
    def __init__(self, fail_txns=None):
        self.sent = []
        self.seen_txns = set()
        self.fail_txns = set(fail_txns or ())

    def send_message_with_retry(self, room_id, text, txn_id, attempts=3):
        if txn_id in self.seen_txns:
            return txn_id
        if txn_id in self.fail_txns:
            raise RuntimeError("模拟网络失败（不确定是否已发出）")
        self.seen_txns.add(txn_id)
        self.sent.append((room_id, text, txn_id))
        return txn_id


cfg = load()
import pathlib
pathlib.Path("/tmp/gosim/g6-smoke.db").unlink(missing_ok=True)  # 重跑幂等：每次冒烟从空库起
db = DB("/tmp/gosim/g6-smoke.db")
ROOM = "!g6:127.0.0.1:8128"
ORG = "@rinx_test_a:127.0.0.1:8128"
START = "2026-10-04T09:00:00+08:00"

# --- t1: 批准提案 → 同事务登记提醒任务（due = start_at - 24h） ---
db.create_case("case-g6", ROOM, ORG, "ev-src", "Asia/Shanghai")
r = create_proposal(db, "case-g6", "方案：周六 09:00 深圳湾骑行", selected_slot="slot_01")
approve_proposal(db, "case-g6", r["proposal_id"], ORG, START,
                 "2026-10-04T11:00:00+08:00", place="深圳湾", activity="骑行")
task = db.conn.execute(
    "SELECT * FROM scheduled_tasks WHERE case_id='case-g6' AND kind='reminder'").fetchone()
ok("t1 批准同事务登记 reminder 任务", task is not None and task["status"] == "Pending")
ok("t1 due = start_at-24h（2026-10-03T09）",
   task is not None and task["due_at"].startswith("2026-10-03T09"))

# --- t2: 强制到期 → sweep 真发，正文含活动/时段/守护号 ---
bot = FakeMatrix()
db.conn.execute("UPDATE scheduled_tasks SET due_at='2000-01-01T00:00:00' WHERE id=?", (task["id"],))
db.conn.commit()
sent_n = sweep_scheduler(db, bot)
t2 = db.conn.execute("SELECT * FROM scheduled_tasks WHERE id=?", (task["id"],)).fetchone()
ok("t2 到期 sweep 发送 1 条", sent_n == 1 and len(bot.sent) == 1)
ok("t2 任务 Completed + txn 落库",
   t2["status"] == "Completed" and t2["txn_id"] == f"sched-{task['id']}")
ok("t2 正文含 活动/时间/守护号（no-facts 溯源）",
   bot.sent and "骑行" in bot.sent[0][1] and "2026-10-04T09:00" in bot.sent[0][1]
   and "case-g6" in bot.sent[0][1])
ok("t2 发送房间 = case 房间", bot.sent and bot.sent[0][0] == ROOM)
ok("t2 审计留痕", db.conn.execute(
    "SELECT count(*) c FROM audit WHERE action LIKE 'scheduler.reminder_sent%'").fetchone()["c"] >= 1)

# --- t3: 发送失败 → NeedsRecovery → 同 txn 重试成功，仅投递一次 ---
ROOM_B = "!g6b:127.0.0.1:8128"
db.create_case("case-g6b", ROOM_B, ORG, "ev-src2", "Asia/Shanghai")
r2 = create_proposal(db, "case-g6b", "方案：周日 10:00 聚餐", selected_slot="slot_02")
approve_proposal(db, "case-g6b", r2["proposal_id"], ORG, "2026-10-05T10:00:00+08:00",
                 "2026-10-05T12:00:00+08:00", place="海岸城", activity="聚餐")
task2 = db.conn.execute(
    "SELECT * FROM scheduled_tasks WHERE case_id='case-g6b' AND kind='reminder'").fetchone()
db.conn.execute("UPDATE scheduled_tasks SET due_at='2000-01-01T00:00:00' WHERE id=?", (task2["id"],))
db.conn.commit()
bot_fail = FakeMatrix(fail_txns={f"sched-{task2['id']}"})
sweep_scheduler(db, bot_fail)
t3 = db.conn.execute("SELECT * FROM scheduled_tasks WHERE id=?", (task2["id"],)).fetchone()
ok("t3 失败 → NeedsRecovery，未投递", t3["status"] == "NeedsRecovery" and len(bot_fail.sent) == 0)
bot_fail.fail_txns.clear()          # 网络恢复 → 同 txn 重试（smoke_g4b 对账语义）
n3 = sweep_scheduler(db, bot_fail)
t3b = db.conn.execute("SELECT * FROM scheduled_tasks WHERE id=?", (task2["id"],)).fetchone()
ok("t3 重试同 txn 成功 → Completed，仅投递一次",
   t3b["status"] == "Completed" and len(bot_fail.sent) == 1
   and bot_fail.sent[0][2] == f"sched-{task2['id']}")

# --- t4: 发送后崩溃窗口（Running + 已投递）→ 重扫同 txn 重放，不重复 ---
ROOM_C = "!g6c:127.0.0.1:8128"
db.create_case("case-g6c", ROOM_C, ORG, "ev-src3", "Asia/Shanghai")
r3 = create_proposal(db, "case-g6c", "方案：周一 19:00 夜跑", selected_slot="slot_03")
approve_proposal(db, "case-g6c", r3["proposal_id"], ORG, "2026-10-06T19:00:00+08:00",
                 "2026-10-06T20:00:00+08:00", place="人才公园", activity="夜跑")
task3 = db.conn.execute(
    "SELECT * FROM scheduled_tasks WHERE case_id='case-g6c' AND kind='reminder'").fetchone()
db.conn.execute(
    "UPDATE scheduled_tasks SET due_at='2000-01-01T00:00:00', status='Running', txn_id=? WHERE id=?",
    (f"sched-{task3['id']}", task3["id"]))
db.conn.commit()
bot_crash = FakeMatrix()
bot_crash.seen_txns.add(f"sched-{task3['id']}")   # 模拟：崩溃前已投递成功
bot_crash.sent.append((ROOM, "（崩溃前已发出）", f"sched-{task3['id']}"))
sweep_scheduler(db, bot_crash)
t4 = db.conn.execute("SELECT * FROM scheduled_tasks WHERE id=?", (task3["id"],)).fetchone()
ok("t4 崩溃窗口回收：Running → Completed，无重复投递",
   t4["status"] == "Completed" and len(bot_crash.sent) == 1)

# --- t5: matrix=None → G5 补偿语义（reminder 也不发，直接 Completed） ---
ROOM_D = "!g6d:127.0.0.1:8128"
db.create_case("case-g6d", ROOM_D, ORG, "ev-src4", "Asia/Shanghai")
r4 = create_proposal(db, "case-g6d", "方案：周二 14:00 读书会", selected_slot="slot_04")
approve_proposal(db, "case-g6d", r4["proposal_id"], ORG, "2026-10-07T14:00:00+08:00",
                 "2026-10-07T16:00:00+08:00", place="书房", activity="读书会")
task4 = db.conn.execute(
    "SELECT * FROM scheduled_tasks WHERE case_id='case-g6d' AND kind='reminder'").fetchone()
db.conn.execute("UPDATE scheduled_tasks SET due_at='2000-01-01T00:00:00' WHERE id=?", (task4["id"],))
db.conn.commit()
bot_none = FakeMatrix()
sweep_scheduler(db)  # 无客户端（smoke_g5 兼容路径）
t5 = db.conn.execute("SELECT * FROM scheduled_tasks WHERE id=?", (task4["id"],)).fetchone()
ok("t5 无客户端退化补偿：Completed 且零发送", t5["status"] == "Completed" and len(bot_none.sent) == 0)

# --- t6: reminder_due 回退路径（不可解析 start_at → now+24h） ---
from guardian.db import now as db_now
due_fb = reminder_due("不是日期")
ok("t6 不可解析 start_at → 创建时刻+24h 兜底",
   due_fb > db_now() and "T" in due_fb)

print(f"\n=== G6 真实提醒冒烟结果: {sum(results)}/{len(results)} PASS ===")
sys.exit(0 if all(results) else 1)
