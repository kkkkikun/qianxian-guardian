"""guardian 常驻循环：sync long-poll + 入站幂等 + durable scheduler 占位。
G1 阶段分发桩只落库；分诊/LLM/动作执行由 G2/G3 接入。"""
import time

from .config import load
from .db import DB, now
from .ingress import Ingress
from .matrix import MatrixClient


def sweep_scheduler(db: DB) -> int:
    """到期任务补偿：条件 UPDATE claim（防双 worker）→ 补偿 → Completed。
    返回本次 claim 并补偿的任务数。"""
    due = db.reload_due_tasks()
    claimed = 0
    for t in due:
        cur = db.conn.execute(
            "UPDATE scheduled_tasks SET status='Running' WHERE id=? AND status IN ('Pending','NeedsRecovery')",
            (t["id"],))
        if cur.rowcount != 1:
            continue  # 已被其他 worker claim
        db.audit("guardian", f"scheduler.compensate:{t['kind']}", t["id"])
        db.conn.execute("UPDATE scheduled_tasks SET status='Completed' WHERE id=?", (t["id"],))
        claimed += 1
    db.conn.commit()
    return claimed


def run() -> None:
    cfg = load()
    db = DB(cfg["db_path"])
    client = MatrixClient(cfg["homeserver"], cfg["bot_user_id"], cfg["bot_password"])
    client.login()
    print(f"[guardian] logged in as {cfg['bot_user_id']} @ {cfg['homeserver']}")

    # durable scheduler：启动重载（Crash → Recovery → Continue）
    due = sweep_scheduler(db)
    future = db.future_tasks()
    print(f"[guardian] scheduler: {len(due)} 逾期待补偿, {len(future)} 个未来任务已装载")

    ingress = Ingress(db, cfg["bot_user_id"])
    since = ingress.last_sync_token()
    print(f"[guardian] sync loop start (since={'saved token' if since else 'now'})")

    while True:
        try:
            body = client.sync(since=since, timeout_ms=cfg["poll_timeout_ms"])

            # 邀请处理（bot 被拉进新房间 → 自动加入，审计）
            for room_id in Ingress.pending_invites(body):
                Ingress.join_room(client, room_id)
                db.audit("guardian", f"room.joined:{room_id}", room_id)
                db.conn.commit()
                print(f"[guardian] joined invited room {room_id}")

            stats = ingress.process_sync(body)
            since = ingress.last_sync_token()
            if any(stats.values()):
                print(f"[guardian] ingress {stats}")
            sweep_scheduler(db)
        except KeyboardInterrupt:
            print("[guardian] bye")
            break
        except Exception as e:  # 网络抖动不退出：退避后重试
            print(f"[guardian] loop error: {e}; retry in 5s")
            time.sleep(5)


if __name__ == "__main__":
    run()
