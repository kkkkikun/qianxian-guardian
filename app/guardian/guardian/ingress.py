"""入站幂等 + bot 自排除 + 事件分发（G1：分发 = 落审计/case_events，分诊留 G2）。
蓝图 v0.7.1：处理与记录同事务提交；bot 自身事件在 ingress 层丢弃；状态事件仅分类。"""
import json

from .db import DB, now

MESSAGE_TYPE = "m.room.message"


class Ingress:
    def __init__(self, db: DB, bot_user_id: str):
        self.db = db
        self.bot_user_id = bot_user_id

    def process_sync(self, sync_body: dict) -> dict:
        """处理一次 sync 响应的 join 房间时间线。返回统计。可对同一 payload 重放验证幂等。"""
        stats = {"messages": 0, "skipped_self": 0, "skipped_type": 0,
                 "duplicates": 0, "processed": 0}
        for room_id, joined in (sync_body.get("rooms", {}).get("join") or {}).items():
            for event in (joined.get("timeline", {}).get("events") or []):
                etype = event.get("type")
                sender = event.get("sender", "")
                event_id = event.get("event_id", "")

                # 分类：非消息事件仅计数（状态事件如 m.room.member 不入分诊）
                if etype != MESSAGE_TYPE:
                    stats["skipped_type"] += 1
                    continue
                # bot 自身事件直接丢弃（防自触发闭环）
                if sender == self.bot_user_id:
                    stats["skipped_self"] += 1
                    self.db.audit("guardian", "ingress.skip_self", event_id)
                    continue

                self.db.conn.execute("BEGIN")
                try:
                    if self.db.seen_event(event_id):
                        stats["duplicates"] += 1
                        self.db.conn.execute("ROLLBACK")
                        continue
                    # G1 分发桩：只落库（case_events 无 Case 时 case_id=NULL）+ 审计
                    self.db.conn.execute(
                        "INSERT INTO case_events(matrix_event_id, type, actor, created_at)"
                        " VALUES (?,?,?,?)",
                        (event_id, etype, sender, now()),
                    )
                    body = (event.get("content") or {}).get("body", "")
                    self.db.conn.execute(
                        "INSERT INTO audit(ts, actor, action, evidence_ref)"
                        " VALUES (?,?,?,?)",
                        (now(), "guardian", f"ingress.message: {body[:80]}", event_id),
                    )
                    self.db.mark_event(event_id, room_id, sender, etype)
                    self.db.conn.execute("COMMIT")
                    stats["processed"] += 1
                    stats["messages"] += 1
                except Exception:
                    self.db.conn.execute("ROLLBACK")
                    raise

        next_batch = sync_body.get("next_batch")
        if next_batch:
            self.db.set_state("last_sync_token", next_batch)
        self.db.conn.commit()
        return stats

    def last_sync_token(self) -> str | None:
        return self.db.get_state("last_sync_token")

    @staticmethod
    def dump_timeline(sync_body: dict) -> list[dict]:
        """提取消息事件（供冒烟/测试断言）。"""
        out = []
        for room_id, joined in (sync_body.get("rooms", {}).get("join") or {}).items():
            for event in (joined.get("timeline", {}).get("events") or []):
                if event.get("type") == MESSAGE_TYPE:
                    out.append({"room_id": room_id, "event_id": event.get("event_id"),
                                "sender": event.get("sender"),
                                "body": (event.get("content") or {}).get("body")})
        return out

    @staticmethod
    def pending_invites(sync_body: dict) -> list[str]:
        return list((sync_body.get("rooms", {}).get("invite") or {}).keys())

    @staticmethod
    def join_room(client, room_id: str) -> None:
        st, body = client._req("POST", f"/_matrix/client/v3/rooms/{room_id}/join", {})
        if st != 200:
            raise RuntimeError(f"join failed: HTTP {st} {body}")

    @staticmethod
    def to_json(sync_body: dict) -> str:
        return json.dumps(sync_body, ensure_ascii=False)
