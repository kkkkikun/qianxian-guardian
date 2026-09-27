"""G1 端到端冒烟（蓝图 v0.7.1）：
1. bot 登录 + 组织者建房邀请 + bot 加入
2. 组织者发消息 → guardian ingress 落库（processed_events / audit / case_events）
3. 重放同一 sync payload → duplicates=1, processed=0（入站幂等）
4. 每房间单 Active Case：DB 部分唯一索引生效
5. durable scheduler：未来任务重载 / 逾期任务补偿
"""
import sys, uuid
sys.path.insert(0, ".")

from guardian.config import load
from guardian.db import DB, ACTIVE_STATUSES, now
from guardian.ingress import Ingress
from guardian.matrix import MatrixClient

cfg = load()
ORGANIZER = {"user_id": "@rinx_test_a:127.0.0.1:8128", "password": None}
import json
acc = json.load(open("../../../test-accounts.json"))["accounts"]
ORGANIZER = next(a for a in acc if a["username"] == "rinx_test_a")

ok = lambda n, cond: print(f"{'✅' if cond else '❌ FAIL'} {n}") or cond
results = []

db = DB("/tmp/gosim/g1-smoke.db")
from pathlib import Path
TOKDIR = Path("/tmp/gosim/tokens"); TOKDIR.mkdir(parents=True, exist_ok=True)
bot = MatrixClient(cfg["homeserver"], cfg["bot_user_id"], cfg["bot_password"],
                   token_path=str(TOKDIR / "guardian_bot.token"))
bot.login()
org = MatrixClient(cfg["homeserver"], ORGANIZER["user_id"], ORGANIZER["password"],
                   token_path=str(TOKDIR / "rinx_test_a.token"))
org.login()
ing = Ingress(db, cfg["bot_user_id"])

# --- 1. 建房 + 邀请 + bot 加入 ---
st, room = org._req("POST", "/_matrix/client/v3/createRoom",
                    {"name": "G1 冒烟群", "invite": [cfg["bot_user_id"]], "preset": "private_chat"})
assert st == 200, room
room_id = room["room_id"]
body = bot.sync(timeout_ms=0)
assert room_id in Ingress.pending_invites(body), "bot 未看到邀请"
Ingress.join_room(bot, room_id)
results.append(ok("建房邀请+bot 加入", True))

# --- 2. 首次 sync（基线）→ 组织者发消息 → ingress 处理 ---
base = bot.sync(timeout_ms=0)
msg = "G1 冒烟：周六上午去深圳湾骑车，大概两小时？"
st, _ = org._req("PUT", f"/_matrix/client/v3/rooms/{room_id}/send/m.room.message/g1-{uuid.uuid4()}",
                 {"msgtype": "m.text", "body": msg}, )
assert st == 200
import time; time.sleep(1)
sync1 = bot.sync(since=base["next_batch"], timeout_ms=3000)
stats1 = ing.process_sync(sync1)
msgs = Ingress.dump_timeline(sync1)
results.append(ok(f"消息落库（processed={stats1['processed']}，body='{msgs[0]['body'][:24]}…'）",
                  stats1["processed"] == 1 and any(m["body"] == msg for m in msgs)))
ev_id = msgs[0]["event_id"]

import sqlite3
row = db.conn.execute("SELECT * FROM processed_events WHERE event_id=?", (ev_id,)).fetchone()
a_row = db.conn.execute("SELECT action FROM audit WHERE evidence_ref=? ORDER BY id DESC LIMIT 1", (ev_id,)).fetchone()
ce = db.conn.execute("SELECT matrix_event_id FROM case_events WHERE matrix_event_id=?", (ev_id,)).fetchone()
results.append(ok("processed_events/audit/case_events 三表齐备", bool(row and a_row and ce)))

# --- 3. 重放同一 payload → 幂等 ---
stats2 = ing.process_sync(sync1)
results.append(ok(f"重放幂等（duplicates={stats2['duplicates']}, processed={stats2['processed']}）",
                  stats2["duplicates"] >= 1 and stats2["processed"] == 0))

# --- 4. 单 Active Case：DB 部分唯一索引 ---
cid = f"case-{uuid.uuid4().hex[:8]}"
db.create_case(cid, room_id, ORGANIZER["user_id"], ev_id, cfg["timezone"])
db.conn.commit()  # 第一个 Case 先落库
try:
    db.create_case(cid + "-x", room_id, ORGANIZER["user_id"], ev_id + "-x", cfg["timezone"])
    db.conn.commit()
    results.append(ok("单 Active Case 约束", False))  # 不应走到这
except sqlite3.IntegrityError:
    db.conn.rollback()
    results.append(ok("单 Active Case 约束（DB 部分唯一索引拦截）", True))
still = db.conn.execute("SELECT count(*) c FROM cases WHERE room_id=?", (room_id,)).fetchone()["c"]
results.append(ok(f"Active Case 数量 = {still}", still == 1))

# --- 5. durable scheduler ---
db.conn.execute("INSERT INTO scheduled_tasks(id, case_id, kind, due_at, status, created_at)"
                " VALUES (?,?,?,?,?,?)",
                (f"t-future-{uuid.uuid4().hex[:6]}", cid, "reminder",
                 "2027-01-01T00:00:00+08:00", "Pending", now()))
due_id = f"t-due-{uuid.uuid4().hex[:6]}"
db.conn.execute("INSERT INTO scheduled_tasks(id, case_id, kind, due_at, status, created_at)"
                " VALUES (?,?,?,?,?,?)",
                (due_id, cid, "reminder", "2026-01-01T00:00:00+08:00", "Pending", now()))
db.conn.commit()
from guardian.main import sweep_scheduler
compensated = sweep_scheduler(db)
results.append(ok(f"durable scheduler：逾期补偿 {compensated} 项 + 未来任务在册 {len(db.future_tasks())}",
                  compensated == 1 and len(db.future_tasks()) >= 1))

print("\n=== G1 冒烟结果:", f"{sum(1 for r in results if r)}/{len(results)} PASS ===")
sys.exit(0 if all(results) else 1)
