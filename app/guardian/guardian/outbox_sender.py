"""Outbox 发送器（G4b）：M2 回执自动发送、M3 校验 grant 后发送、UNKNOWN 对账。
蓝图 v0.7.1：M1/M2 无需 grant；M3 必须 approve-once/standing；同 txn_id 重试不产生第二条消息。"""
from datetime import datetime, timedelta, timezone

from .db import now


class OutboxSender:
    def __init__(self, db, matrix_client, clock=None):
        self.db = db
        self.client = matrix_client
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # ---- grant 工具 ----
    def issue_grant(self, case_id: str, room_id: str, kind: str, mode: str,
                    created_by: str, ttl_minutes: int = 60) -> str:
        gid = f"grant-{uuid_hex()}"
        expiry = None
        if mode == "once":
            expiry = None  # once 按次数消费
        else:
            expiry = (self._clock() + timedelta(minutes=ttl_minutes)).isoformat()
        self.db.conn.execute(
            "INSERT INTO grants(id, case_id, room_id, kind, mode, expiry, created_by, created_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (gid, case_id, room_id, kind, mode, expiry, created_by, now()),
        )
        self.db.conn.commit()
        return gid

    def _check_grant(self, case_id: str, room_id: str, kind: str) -> str | None:
        row = self.db.conn.execute(
            "SELECT id, mode, expiry FROM grants WHERE case_id=? AND room_id=? AND kind=?"
            " ORDER BY created_at DESC LIMIT 1", (case_id, room_id, kind)).fetchone()
        if row is None:
            return None
        if row["expiry"] and row["expiry"] < now():
            return None
        return row["id"]

    def _consume_grant(self, grant_id: str) -> None:
        row = self.db.conn.execute("SELECT mode FROM grants WHERE id=?", (grant_id,)).fetchone()
        if row and row["mode"] == "once":
            self.db.conn.execute("DELETE FROM grants WHERE id=?", (grant_id,))
            self.db.conn.commit()

    # ---- 发送主循环 ----
    def drain(self) -> dict:
        stats = {"sent": 0, "refused": 0, "unknown": 0, "reconciled": 0}
        rows = self.db.conn.execute(
            "SELECT * FROM outbox WHERE status IN ('Pending','UNKNOWN','NEED_RECONCILIATION')"
            " ORDER BY created_at").fetchall()
        for row in rows:
            o = dict(row)
            if o["status"] in ("UNKNOWN", "NEED_RECONCILIATION"):
                # 对账：同 txn_id 重试（Matrix 幂等）
                try:
                    self.client.send_message_with_retry(o["room_id"], o["text"], txn_id=o["txn_id"])
                    self.db.conn.execute("UPDATE outbox SET status='Sent', updated_at=? WHERE id=?",
                                         (now(), o["id"]))
                    stats["reconciled"] += 1
                except RuntimeError:
                    self.db.conn.execute("UPDATE outbox SET status='NEED_RECONCILIATION',"
                                         " updated_at=? WHERE id=?", (now(), o["id"]))
                    stats["unknown"] += 1
                self.db.conn.commit()
                continue
            if o["kind"] == "M3":
                grant_id = self._check_grant(o["case_id"], o["room_id"], "outreach")
                if grant_id is None:
                    stats["refused"] += 1
                    self.db.audit("guardian", f"outbox.refused_no_grant:{o['id']}", o["case_id"])
                    self.db.conn.commit()
                    continue
                self._consume_grant(grant_id)
            try:
                self.client.send_message_with_retry(o["room_id"], o["text"], txn_id=o["txn_id"])
                self.db.conn.execute("UPDATE outbox SET status='Sent', updated_at=? WHERE id=?",
                                     (now(), o["id"]))
                stats["sent"] += 1
            except RuntimeError:
                # 发送不确定 → 不假装失败也不假装成功，进对账态
                self.db.conn.execute("UPDATE outbox SET status='UNKNOWN', updated_at=? WHERE id=?",
                                     (now(), o["id"]))
                stats["unknown"] += 1
            self.db.conn.commit()
        return stats


def uuid_hex() -> str:
    import uuid
    return uuid.uuid4().hex[:12]
