"""G4a 核心：Case 状态机事务层（蓝图 v0.7.1）。
原则落地：
  - 一次状态迁移 = 一个可追踪事务（revision++ + audit + case_events）
  - 本地动作 = DB 事务 + 读回断言（PASS 才 COMMIT，FAIL 回退）
  - organizer 权限 + proposal.based_on_revision 批准校验
  - plans 历史（Active/Superseded）
"""
import json
import uuid
from datetime import datetime, timezone

from .db import now

ACTIVE_STATUSES = (
    "Parsing", "Clarifying", "Collecting", "Proposing", "AwaitingConfirm",
    "Confirmed", "Armed", "Rescheduling", "Settling", "Unstable",
)

# 允许出提案的 Case 状态（蓝图状态机：Proposing/Rescheduling 为主，解析类状态可直接带方案）
PROPOSABLE = ("Parsing", "Collecting", "Proposing", "Rescheduling")
# 可取消的状态
CANCELLABLE = ("Confirmed", "Armed")


class CaseError(Exception):
    """业务规则拒绝（权限/状态/版本）。"""


class ReadbackError(Exception):
    """读回断言失败（事务已回滚）。"""


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


def _case(db, case_id):
    row = db.conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    if row is None:
        raise CaseError(f"Case {case_id} 不存在")
    return dict(row)


def _readback(db, expected: dict) -> None:
    """读回断言：expected = {sql, params, check(row)->bool}；FAIL 抛 ReadbackError（调用方回滚）。"""
    row = db.conn.execute(expected["sql"], expected["params"]).fetchone()
    if row is None or not expected["check"](dict(row)):
        raise ReadbackError(f"readback FAIL: {expected['sql']} {expected['params']}")


# ---------------- Proposal（M1） ----------------

def create_proposal(db, case_id: str, content: str, selected_slot: str | None = None,
                    basis_fact_ids: list | None = None) -> dict:
    """从解析结果创建提案（M1）。Case → AwaitingConfirm，revision++（提案进入权威快照）。"""
    case = _case(db, case_id)
    if case["status"] not in PROPOSABLE:
        raise CaseError(f"状态 {case['status']} 不可出提案")
    pid = f"prop-{_uuid()}"
    db.conn.execute("BEGIN")
    try:
        new_rev = case["revision"] + 1
        # based_on_revision = 提案进入权威快照后的版本（批准时与 current.revision 比对）
        db.conn.execute(
            "INSERT INTO proposals(id, case_id, based_on_revision, request_id,"
            " selected_slot_id, content, basis_fact_ids, status, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, case_id, new_rev, f"req-{_uuid()}", selected_slot,
             content, json.dumps(basis_fact_ids or []), "Pending", now()),
        )
        db.conn.execute("UPDATE cases SET status='AwaitingConfirm', revision=? WHERE id=?",
                        (new_rev, case_id))
        db.audit("guardian", f"proposal.created:{pid}", case_id)
        db.conn.execute(
            "INSERT INTO case_events(case_id, matrix_event_id, revision, type, actor, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (case_id, f"local:{pid}", new_rev, "proposal.created", "guardian", now()),
        )
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"proposal_id": pid, "based_on_revision": new_rev, "new_revision": new_rev}


# ---------------- Approval（组织者 + 版本校验 + 读回） ----------------

def approve_proposal(db, case_id: str, proposal_id: str, sender: str,
                     start_at: str, end_at: str, place: str | None = None,
                     activity: str | None = None) -> dict:
    """组织者批准提案：plans 历史（旧 Superseded → 新 Active）、Case → Confirmed、读回断言。"""
    case = _case(db, case_id)
    if sender != case["organizer_id"]:
        raise CaseError(f"越权：{sender} 不是组织者 {case['organizer_id']}")
    if case["status"] != "AwaitingConfirm":
        raise CaseError(f"状态 {case['status']} 不可批准")
    prop = db.conn.execute("SELECT * FROM proposals WHERE id=? AND case_id=?",
                           (proposal_id, case_id)).fetchone()
    if prop is None:
        raise CaseError(f"提案 {proposal_id} 不存在")
    prop = dict(prop)
    if prop["status"] != "Pending":
        raise CaseError(f"提案状态 {prop['status']} 不可批准")
    if prop["based_on_revision"] != case["revision"]:
        # 快照已变化 → 提案过期
        db.conn.execute("UPDATE proposals SET status='Superseded' WHERE id=?", (proposal_id,))
        db.conn.execute("UPDATE cases SET status='Proposing', revision=revision+1 WHERE id=?",
                        (case_id,))
        db.audit("guardian", f"proposal.superseded:{proposal_id} (stale revision)", case_id)
        db.conn.commit()
        raise CaseError("提案基于旧快照（based_on_revision 不匹配），已标记 Superseded，请重新出方案")

    db.conn.execute("BEGIN")
    try:
        # 旧 plan 全部 Superseded，新 plan Active
        db.conn.execute("UPDATE plans SET status='Superseded' WHERE case_id=? AND status='Active'",
                        (case_id,))
        plan_id = f"plan-{_uuid()}"
        new_rev = case["revision"] + 1
        db.conn.execute(
            "INSERT INTO plans(plan_id, case_id, revision, start_at, end_at, timezone,"
            " place, activity, members, source_proposal_id, status)"
            " VALUES (?,?,?,?,?,?,?,?,?,?, 'Active')",
            (plan_id, case_id, new_rev, start_at, end_at, case["timezone"],
             place, activity, json.dumps([]), proposal_id),
        )
        db.conn.execute("UPDATE proposals SET status='Approved' WHERE id=?", (proposal_id,))
        db.conn.execute("UPDATE cases SET status='Confirmed', revision=? WHERE id=?",
                        (new_rev, case_id))
        # M2 回执进入 outbox（无需 grant——刚执行动作的系统回声）
        receipt = f"已确认：{activity or place or '活动'}（{start_at}）。方案 {proposal_id} 已生效。"
        db.conn.execute(
            "INSERT INTO outbox(id, case_id, txn_id, kind, room_id, text, status, created_at)"
            " VALUES (?,?,?,?,?,?, 'Pending', ?)",
            (f"out-{_uuid()}", case_id, f"rcpt-{_uuid()}", "M2", case["room_id"],
             receipt, now()),
        )
        db.audit(sender, f"proposal.approved:{proposal_id} -> plan:{plan_id}", case_id)
        db.conn.execute(
            "INSERT INTO case_events(case_id, matrix_event_id, revision, type, actor, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (case_id, f"local:{proposal_id}", new_rev, "case.confirmed", sender, now()),
        )
        # 读回断言（本地动作：FAIL 则整体回滚）
        _readback(db, {
            "sql": "SELECT status, revision FROM cases WHERE id=?",
            "params": (case_id,),
            "check": lambda r: r["status"] == "Confirmed" and r["revision"] == new_rev,
        })
        _readback(db, {
            "sql": "SELECT plan_id, status FROM plans WHERE case_id=? AND status='Active'",
            "params": (case_id,),
            "check": lambda r: r["plan_id"] == plan_id,
        })
        db.conn.commit()
    except ReadbackError as e:
        db.conn.rollback()
        db.audit("system", f"readback.FAIL:{case_id}:{e}", case_id)
        db.conn.commit()
        raise
    except Exception:
        db.conn.rollback()
        raise
    return {"plan_id": plan_id, "revision": new_rev, "status": "Confirmed"}


def reject_proposal(db, case_id: str, proposal_id: str, sender: str) -> dict:
    """组织者拒绝：Proposal=Rejected（历史保留），Case 回 Proposing，revision++。"""
    case = _case(db, case_id)
    if sender != case["organizer_id"]:
        raise CaseError(f"越权：{sender} 不是组织者")
    if case["status"] != "AwaitingConfirm":
        raise CaseError(f"状态 {case['status']} 无待批提案")
    db.conn.execute("BEGIN")
    try:
        cur = db.conn.execute(
            "UPDATE proposals SET status='Rejected' WHERE id=? AND case_id=? AND status='Pending'",
            (proposal_id, case_id))
        if cur.rowcount == 0:
            raise CaseError(f"提案 {proposal_id} 不是 Pending 状态")
        db.conn.execute("UPDATE cases SET status='Proposing', revision=revision+1 WHERE id=?",
                        (case_id,))
        db.audit(sender, f"proposal.rejected:{proposal_id}", case_id)
        # 读回：被拒提案不得成为任何 Active plan 的来源
        _readback(db, {
            "sql": "SELECT count(*) c FROM plans WHERE source_proposal_id=? AND status='Active'",
            "params": (proposal_id,),
            "check": lambda r: r["c"] == 0,
        })
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"rejected": proposal_id, "case_status": "Proposing"}


# ---------------- Reschedule / Cancel ----------------

def mark_rescheduling(db, case_id: str, sender: str) -> dict:
    """改口 → Rescheduling（旧 plan 保持 Active 直到新方案批准）。"""
    case = _case(db, case_id)
    if sender != case["organizer_id"] and sender != "guardian":
        raise CaseError(f"越权：{sender} 不可发起改期")
    if case["status"] not in ("Confirmed", "Armed"):
        raise CaseError(f"状态 {case['status']} 不可改期")
    db.conn.execute("BEGIN")
    db.conn.execute("UPDATE cases SET status='Rescheduling', revision=revision+1 WHERE id=?",
                    (case_id,))
    db.audit(sender, f"case.rescheduling:{case_id}", case_id)
    db.conn.commit()
    return {"case_status": "Rescheduling"}


def cancel_case(db, case_id: str, sender: str) -> dict:
    """取消事务：Case→Cancelled + 级联清理 + 历史保留 + 读回。"""
    case = _case(db, case_id)
    if sender != case["organizer_id"]:
        raise CaseError(f"越权：{sender} 不是组织者")
    if case["status"] not in CANCELLABLE:
        raise CaseError(f"状态 {case['status']} 不可取消")
    db.conn.execute("BEGIN")
    try:
        db.conn.execute("UPDATE cases SET status='Cancelled', revision=revision+1 WHERE id=?",
                        (case_id,))
        db.conn.execute("UPDATE scheduled_tasks SET status='Cancelled'"
                        " WHERE case_id=? AND status IN ('Pending','Claimed')", (case_id,))
        db.conn.execute("UPDATE outbox SET status='Cancelled'"
                        " WHERE case_id=? AND status='Pending' AND kind='M3'", (case_id,))
        db.conn.execute("UPDATE plans SET status='Superseded' WHERE case_id=? AND status='Active'",
                        (case_id,))
        db.audit(sender, f"case.cancelled:{case_id}", case_id)
        _readback(db, {
            "sql": "SELECT status FROM cases WHERE id=?", "params": (case_id,),
            "check": lambda r: r["status"] == "Cancelled",
        })
        db.conn.commit()
    except Exception:
        db.conn.rollback()
        raise
    return {"case_status": "Cancelled"}


def record_receipt(db, case_id: str, text: str) -> str:
    """M2 回执入 outbox（Pending → 由发送器送出 → Sent）。"""
    oid = f"out-{_uuid()}"
    case = _case(db, case_id)
    db.conn.execute(
        "INSERT INTO outbox(id, case_id, txn_id, kind, room_id, text, status, created_at)"
        " VALUES (?,?,?,?,?,?,'Pending',?)",
        (oid, case_id, f"rcpt-{_uuid()}", "M2", case["room_id"], text, now()),
    )
    db.conn.commit()
    return oid
