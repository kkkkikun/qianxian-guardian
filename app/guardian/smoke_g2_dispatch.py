"""G2 端到端冒烟：分发器闭环（消息 → 分诊 → 关联 → Case 创建/关联/挂起）。
不依赖网络——直接喂事件数据。覆盖蓝图关联判定四分法 + organizer 规则。"""
import sys
sys.path.insert(0, ".")

from guardian.config import load
from guardian.db import DB
from guardian.dispatcher import Dispatcher

results = []
ok = lambda n, cond: results.append(cond) or print(f"{'✅' if cond else '❌ FAIL'} {n}")

cfg = load()
db = DB("/tmp/gosim/g2-smoke.db")
BOT = cfg["bot_user_id"]
ROOM = "!g2-smoke:127.0.0.1:8128"
A = "@rinx_test_a:127.0.0.1:8128"
B = "@rinx_test_b:127.0.0.1:8128"

d = Dispatcher(db, BOT)

# 1. 噪声不建 Case
r = d.handle_message(ROOM, B, "ev-noise", "哈哈哈哈这游戏真好笑")
ok("噪声 → unrelated，无 Case", r["action"] == "unrelated" and db.active_case(ROOM) is None)

# 2. A 发起聚会 → new_case，A 是组织者
r = d.handle_message(ROOM, A, "ev-1", "周六上午去深圳湾骑车，大概两小时？")
ok(f"新意图 → new_case（{r.get('case_id')}，组织者={r.get('organizer')}）",
   r["action"] == "new_case" and r["organizer"] == A)
case_id = r["case_id"]

# 3. B 同场景跟帖 → existing（生命周期语义）
r = d.handle_message(ROOM, B, "ev-2", "我可以，算我一个")
ok(f"RSVP → existing 关联 Case {r.get('case_id')}", r["action"] == "existing" and r["case_id"] == case_id)

# 4. B 的台账 → existing
r = d.handle_message(ROOM, B, "ev-3", "我垫了 88")
ok("台账 → existing", r["action"] == "existing")

# 5. B 想搞新活动 → pending_intent，不污染现有 Case
r = d.handle_message(ROOM, B, "ev-4", "下周找个时间看电影？")
ok(f"新意图冲突 → pending_intent（{r.get('note','')[:20]}…）", r["action"] == "pending_intent")
still = db.conn.execute("SELECT count(*) c FROM cases WHERE room_id=?", (ROOM,)).fetchone()["c"]
ok(f"Case 数量仍为 {still}", still == 1)

# 6. B 发"同意方案A"——G2 阶段还不是提案确认，只是普通分诊（无 change/cancel 词 → 未命中）
r = d.handle_message(ROOM, B, "ev-5", "同意方案A")
ok("确认类消息 G2 阶段不过度处理（未命中规则）", r["action"] == "unrelated")

# 7. organizer 越权测试的准备：B 想改期 → existing（但 G3 校验 sender==organizer）
r = d.handle_message(ROOM, B, "ev-6", "改周日吧")
ok("B 改口 → existing（G3 将校验发起权）", r["action"] == "existing" and r["case_id"] == case_id)

# 8. 第二个房间互不干扰
ROOM2 = "!g2-room2:127.0.0.1:8128"
r = d.handle_message(ROOM2, B, "ev-7", "周日晚上聚餐？")
ok(f"房间 2 独立建 Case（{r.get('case_id')}）", r["action"] == "new_case" and r["case_id"] != case_id)

total_cases = db.conn.execute("SELECT count(*) c FROM cases").fetchone()["c"]
ok(f"全局 Case 总数 = {total_cases}（每房间一个）", total_cases == 2)

print(f"\n=== G2 分发冒烟结果: {sum(results)}/{len(results)} PASS ===")
sys.exit(0 if all(results) else 1)
