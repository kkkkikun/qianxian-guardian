"""SQLite：唯一事实源。WAL 模式；schema 全量见 schema.sql。"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA = Path(__file__).resolve().parents[1] / "schema.sql"

ACTIVE_STATUSES = (
    "Parsing", "Clarifying", "Collecting", "Proposing", "AwaitingConfirm",
    "Confirmed", "Armed", "Rescheduling", "Settling", "Unstable",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DB:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        # isolation_level=None：显式事务模式（cases.py 用 BEGIN/COMMIT 控制原子性）
        self.conn = sqlite3.connect(path, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(_SCHEMA.read_text(encoding="utf-8"))

    # ---- 审计（只追加） ----
    def audit(self, actor: str, action: str, evidence_ref: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO audit(ts, actor, action, evidence_ref) VALUES (?,?,?,?)",
            (now(), actor, action, evidence_ref),
        )

    # ---- 入站幂等（蓝图 v0.7.1：处理与记录同事务提交） ----
    def seen_event(self, event_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM processed_events WHERE event_id=?", (event_id,)
        ).fetchone()
        return row is not None

    def mark_event(self, event_id: str, room_id: str, sender: str, type_: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO processed_events(event_id, room_id, sender, type, processed_at)"
            " VALUES (?,?,?,?,?)",
            (event_id, room_id, sender, type_, now()),
        )

    def get_state(self, key: str) -> str | None:
        row = self.conn.execute(
            "SELECT value FROM ingress_state WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def set_state(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO ingress_state(key, value) VALUES (?,?)"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    # ---- Case / revision（蓝图：每次改变权威快照的已提交事务 revision+1） ----
    def create_case(self, case_id: str, room_id: str, organizer_id: str,
                    created_from_msg_id: str, timezone: str) -> None:
        self.conn.execute(
            "INSERT INTO cases(id, room_id, organizer_id, organizer_source,"
            " created_from_msg_id, status, revision, timezone, created_at)"
            " VALUES (?, ?, ?, 'first_message', ?, 'Parsing', 1, ?, ?)",
            (case_id, room_id, organizer_id, created_from_msg_id, timezone, now()),
        )

    def active_case(self, room_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM cases WHERE room_id=? AND status IN"
            f" ({','.join('?' * len(ACTIVE_STATUSES))})",
            (room_id, *ACTIVE_STATUSES),
        ).fetchone()

    # ---- durable scheduler（启动重载 + 过期补偿） ----
    def reload_due_tasks(self) -> list[sqlite3.Row]:
        """启动恢复：NeedsRecovery 重载；到期未执行的返回给补偿队列。"""
        return self.conn.execute(
            "SELECT * FROM scheduled_tasks"
            " WHERE status IN ('Pending','NeedsRecovery') AND due_at <= ?",
            (now(),),
        ).fetchall()

    def future_tasks(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM scheduled_tasks WHERE status IN ('Pending','Claimed')"
            " AND due_at > ? ORDER BY due_at",
            (now(),),
        ).fetchall()
