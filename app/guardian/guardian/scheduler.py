"""durable scheduler 真实动作（#37，外环 2026-10-02 批准的越界增强）：
到期 reminder 任务 → 真发 Matrix 房间消息。

- 幂等：txn_id = "sched-<task_id>" 与任务绑定；NeedsRecovery 重试 / 崩溃后
  重放（Running 也可被回收）都复用同一 txn —— homeserver 按 txn 去重，不重复投递。
- 失败语义：发送抛错 = 不确定是否已发出 → status='NeedsRecovery'，同 txn 下轮重试。
- matrix_client=None 时退化为 G5 补偿语义（claim → Completed），smoke_g5 兼容。
- due 锚定：reminder_due() 优先 start_at-24h（ISO 可解析时），否则创建时刻+24h；
  这是调度决策不是事实声明，提醒正文自带守护号供追溯（no-facts 纪律）。"""
import uuid
from datetime import datetime, timedelta

from .db import now


def reminder_due(start_at: str | None) -> str:
    """T-24h 提醒的到期时刻：优先 start_at-24h，解析失败则创建时刻+24h。"""
    try:
        base = datetime.fromisoformat(start_at)
        if base.tzinfo is not None:
            base = base.astimezone().replace(tzinfo=None)  # 落库统一朴素本地时刻
        return (base - timedelta(hours=24)).isoformat(timespec="seconds")
    except (ValueError, TypeError):
        return (datetime.fromisoformat(now()) + timedelta(hours=24)).isoformat(timespec="seconds")


def schedule_reminder(db, case_id: str, room_id: str, due_at: str) -> str:
    """批准/确认动作的事务内调用：登记 T-24h 提醒任务。返回 task_id。"""
    task_id = f"sched-{uuid.uuid4().hex[:12]}"
    db.conn.execute(
        "INSERT INTO scheduled_tasks(id, case_id, kind, due_at, status, txn_id, created_at)"
        " VALUES (?,?, 'reminder', ?, 'Pending', NULL, ?)",
        (task_id, case_id, due_at, now()),
    )
    db.audit("guardian", f"scheduler.scheduled:{task_id} due:{due_at}", case_id)
    return task_id


def reminder_text_for(db, task) -> str:
    """提醒正文：读 Active plan 当前值（activity/place/start_at），带守护号溯源；
    缺失字段不编造（no-facts 纪律）。"""
    row = db.conn.execute(
        "SELECT activity, place, start_at FROM plans WHERE case_id=? AND status='Active'",
        (task["case_id"],),
    ).fetchone()
    head = "聚会"
    when = ""
    if row is not None:
        head = row["activity"] or row["place"] or "聚会"
        when = f" {row['start_at']} " if row["start_at"] else " "
    return f"⏰ T-24h 提醒：{head}{when}将至（守护 {task['case_id']}）。请组织者确认时间地点与参与人。"


def sweep(db, matrix_client=None) -> int:
    """到期任务执行：claim（含 Running 崩溃回收）→ reminder 真发 / 其余补偿 → Completed。
    返回本次处理的任务数。"""
    due = db.reload_due_tasks()
    claimed = 0
    for t in due:
        cur = db.conn.execute(
            "UPDATE scheduled_tasks SET status='Running'"
            " WHERE id=? AND status IN ('Pending','NeedsRecovery','Running')",
            (t["id"],),
        )
        if cur.rowcount != 1:
            continue  # 已被其他 worker 处理
        db.audit("guardian", f"scheduler.claim:{t['kind']}", t["id"])
        if t["kind"] == "reminder" and matrix_client is not None:
            txn = t["txn_id"] or f"sched-{t['id']}"
            room = db.conn.execute(
                "SELECT room_id FROM cases WHERE id=?", (t["case_id"],)
            ).fetchone()
            try:
                matrix_client.send_message_with_retry(
                    room["room_id"], reminder_text_for(db, t), txn
                )
                db.conn.execute(
                    "UPDATE scheduled_tasks SET status='Completed', txn_id=? WHERE id=?",
                    (txn, t["id"]),
                )
                db.audit("guardian", f"scheduler.reminder_sent txn:{txn}", t["case_id"])
            except Exception as e:
                db.conn.execute(
                    "UPDATE scheduled_tasks SET status='NeedsRecovery', txn_id=? WHERE id=?",
                    (txn, t["id"]),
                )
                db.audit("guardian", f"scheduler.reminder_failed:{e} txn:{txn}", t["id"])
                claimed += 1
                continue
        else:
            db.conn.execute(
                "UPDATE scheduled_tasks SET status='Completed' WHERE id=?", (t["id"],)
            )
        claimed += 1
    db.conn.commit()
    return claimed
