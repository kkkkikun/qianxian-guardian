"""G4b 主链缝合冒烟（确定性，无网络）：
群消息进 → 分诊/关联 → octos 解析(Fake) → Proposal(M1) → Outbox 发送（M1 无 grant）
→ 组织者确认 → Confirmed → M2 回执 → 发送
+ 越权确认拒绝 / M3 无 grant 拒发 / once grant 消费 / 失败注入 → UNKNOWN → 同 txn 对账（不重复发送）
"""
import sys

sys.path.insert(0, ".")
from guardian.config import load
from guardian.db import DB
from guardian.dispatcher import Dispatcher
from guardian.outbox_sender import OutboxSender
from guardian.parser import FakeLlm

results = []
ok = lambda n, cond: results.append(bool(cond)) or print(f"{'✅' if cond else '❌ FAIL'} {n}")


class FakeMatrix:
    """记录发送；可注入失败；txn 幂等（同 txn 只投递一次）。"""
    def __init__(self, fail_txns=None):
        self.sent = []           # (room, text, txn)
        self.seen_txns = set()
        self.fail_txns = set(fail_txns or ())

    def send_message_with_retry(self, room_id, text, txn_id, attempts=3):
        if txn_id in self.seen_txns:
            return txn_id                       # 幂等：不重复投递
        if txn_id in self.fail_txns:
            raise RuntimeError("模拟网络失败（不确定是否已发出）")
        self.seen_txns.add(txn_id)
        self.sent.append((room_id, text, txn_id))
        return txn_id


cfg = load()
db = DB("/tmp/gosim/g4b-smoke.db")
fake_llm = FakeLlm()
bot = FakeMatrix()
disp = Dispatcher(db, bot_user_id=cfg["bot_user_id"], llm=fake_llm)
sender = OutboxSender(db, bot)

ROOM = "!g4b:127.0.0.1:8128"
A = "@rinx_test_a:127.0.0.1:8128"
B = "@rinx_test_b:127.0.0.1:8128"

# --- 1. 群消息进 → Case + octos 解析 + Proposal ---
r = disp.handle_message(ROOM, A, "ev1", "周六上午去深圳湾骑车，大概两小时？")
ok(f"主链前半：new_case + 解析 + 提案（place={r.get('parsed',{}).get('place')}）",
   r["action"] == "new_case" and r.get("parsed", {}).get("place") == "深圳湾骑车"
   and r.get("proposal_id"))
case_id = r["case_id"]

# --- 2. M1 提案经 Outbox 发送（无需 grant）---
stats = sender.drain()
m1 = [s for s in bot.sent if "方案" in s[1] or "骑行" in s[1] or "聚会" in s[1]]
ok(f"M1 提案已发送（stats={stats}，bot.sent 含提案 {len(m1)} 条）",
   stats["sent"] >= 1 and len(m1) >= 1)

# --- 3. 越权确认 → 拒绝，无状态迁移 ---
r = disp.handle_message(ROOM, B, "ev2", "同意方案A")
ok(f"越权确认拒绝（{r.get('action')}：{r.get('reason','')[:22]}…）",
   r.get("action") == "confirm_denied")

# --- 4. 组织者确认 → Confirmed + M2 回执入 outbox ---
r = disp.handle_message(ROOM, A, "ev3", "同意方案A")
ok(f"组织者确认 → {r.get('action')}（plan {r.get('plan_id','')[:9]}…，rev {r.get('revision')}）",
   r.get("action") == "approved" and r.get("status") == "Confirmed")
receipts = db.conn.execute("SELECT text FROM outbox WHERE kind='M2' AND case_id=?",
                           (case_id,)).fetchall()
ok(f"M2 回执已入 outbox（{receipts[0][0][:24]}…）", len(receipts) >= 1)

# --- 5. 回执发送（M2 无需 grant）---
before = len(bot.sent)
stats = sender.drain()
ok(f"M2 回执发送（新增 {len(bot.sent)-before} 条）", len(bot.sent) > before)

# --- 6. M3 无 grant → 拒发 ---
db.conn.execute(
    "INSERT INTO outbox(id, case_id, txn_id, kind, room_id, text, status, created_at)"
    " VALUES ('o-m3-1', ?, 'txn-m3-1', 'M3', ?, '提醒：明天骑车，记得带水', 'Pending', '2026-09-27')",
    (case_id, ROOM))
db.conn.commit()
stats = sender.drain()
still = db.conn.execute("SELECT status FROM outbox WHERE id='o-m3-1'").fetchone()
ok(f"M3 无 grant → 拒发（status 仍 {still[0] if still else '?'}，refused={stats['refused']}）",
   still and still[0] == "Pending" and stats["refused"] == 1 and
   not any(t[2] == "txn-m3-1" for t in bot.sent))

# --- 7. 签发 once grant → 发送 + grant 消费 ---
sender.issue_grant(case_id, ROOM, "outreach", mode="once", created_by=A)
stats = sender.drain()
m3_sent = [t for t in bot.sent if t[2] == "txn-m3-1"]
grants_left = db.conn.execute("SELECT count(*) c FROM grants WHERE case_id=?", (case_id,)).fetchone()["c"]
ok(f"M3 once grant → 发送且 grant 消费（grants_left={grants_left}）",
   len(m3_sent) == 1 and grants_left == 0)

# --- 8. 失败注入 → UNKNOWN → 同 txn 对账 → 只有一条消息 ---
db.conn.execute(
    "INSERT INTO outbox(id, case_id, txn_id, kind, room_id, text, status, created_at)"
    " VALUES ('o-m3-2', ?, 'txn-m3-2', 'M3', ?, '提醒：集合时间到了', 'Pending', '2026-09-27')",
    (case_id, ROOM))
sender.issue_grant(case_id, ROOM, "outreach", mode="once", created_by=A)
bot.fail_txns.add("txn-m3-2")
sender.drain()  # 第一次：失败 → UNKNOWN
st1 = db.conn.execute("SELECT status FROM outbox WHERE id='o-m3-2'").fetchone()[0]
bot.fail_txns.discard("txn-m3-2")
sender.drain()  # 对账：同 txn 重试 → Sent
st2 = db.conn.execute("SELECT status FROM outbox WHERE id='o-m3-2'").fetchone()[0]
m3_2_count = sum(1 for t in bot.sent if t[2] == "txn-m3-2")
ok(f"失败注入 → {st1} → 对账 → {st2}，同 txn 消息数={m3_2_count}（幂等）",
   st1 in ("UNKNOWN", "NEED_RECONCILIATION") and st2 == "Sent" and m3_2_count == 1)

print(f"\n=== G4b 主链缝合冒烟结果: {sum(results)}/{len(results)} PASS ===")
sys.exit(0 if all(results) else 1)
