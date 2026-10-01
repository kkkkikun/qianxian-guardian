"""guardian 常驻循环：sync long-poll + 入站幂等 + durable scheduler 占位。
G1 阶段分发桩只落库；分诊/LLM/动作执行由 G2/G3 接入。"""
import time

from .config import load
from .db import DB, now
from .ingress import Ingress
from .matrix import MatrixClient


def sweep_scheduler(db: DB, matrix_client=None) -> int:
    """到期任务执行（#37 升级）：委托 scheduler.sweep。
    matrix_client=None → G5 补偿语义（smoke_g5 兼容）；
    传入客户端 → reminder 任务真发 Matrix 房间消息（txn 绑定任务，幂等重试）。"""
    from .scheduler import sweep as _sweep
    return _sweep(db, matrix_client)


def run() -> None:
    cfg = load()
    db = DB(cfg["db_path"])
    client = MatrixClient(cfg["homeserver"], cfg["bot_user_id"], cfg["bot_password"])
    client.login()
    print(f"[guardian] logged in as {cfg['bot_user_id']} @ {cfg['homeserver']}")

    # durable scheduler：启动重载（Crash → Recovery → Continue；reminder 真发）
    due = sweep_scheduler(db, client)
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
            sweep_scheduler(db, client)
        except KeyboardInterrupt:
            print("[guardian] bye")
            break
        except Exception as e:  # 网络抖动不退出：退避后重试
            print(f"[guardian] loop error: {e}; retry in 5s")
            time.sleep(5)


if __name__ == "__main__":
    run()
