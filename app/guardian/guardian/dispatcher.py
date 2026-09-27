"""G2/G4b 分发器：消息 → 分诊 → 关联 → Case 事务（含 octos 解析、提案、确认流）。"""
import json
import re
import uuid
from datetime import datetime

from . import cases as cases_api
from . import triage
from .db import DB, now
from .triage import TZ_NAME

DEMO_NOW = datetime(2026, 9, 28, 12, 0, 0)  # 与演示剧本对齐的"今天"（外环可覆盖）

CONFIRM_RE = re.compile(r"(同意方案|同意|批准|确认方案)")


class Dispatcher:
    def __init__(self, db: DB, bot_user_id: str, organizer_hint: str | None = None,
                 llm=None, now_dt: datetime | None = None):
        self.db = db
        self.bot_user_id = bot_user_id
        self.organizer_hint = organizer_hint
        self.llm = llm          # LlmClient（OupLlm 真实 / FakeLlm 测试）；None = 不出提案
        self.now_dt = now_dt

    def handle_message(self, room_id: str, sender: str, event_id: str, body: str,
                       now_dt: datetime | None = None) -> dict:
        """G2/G4b 主链：分诊 → 关联 → Case 事务。返回动作摘要（供冒烟断言/审计）。"""
        now_dt = now_dt or self.now_dt or DEMO_NOW
        t = triage.triage(body, sender)
        active = self.db.active_case(room_id)
        out = {"rules": [], "kinds": []}

        # ---- 确认关键词（先于分诊早退：确认词不在分诊规则表内；
        #      organizer/based_on 校验在事务层） ----
        if (CONFIRM_RE.search(body) and active is not None
                and active["status"] == "AwaitingConfirm"):
            case = dict(active)
            pending = self.db.conn.execute(
                "SELECT id, content FROM proposals WHERE case_id=? AND status='Pending'"
                " ORDER BY created_at DESC LIMIT 1", (case["id"],)).fetchone()
            if pending is None:
                return {**out, "action": "existing", "note": "无待批提案"}
            try:
                r = cases_api.approve_proposal(self.db, case["id"], pending["id"], sender,
                                               start_at=self._default_start(now_dt),
                                               end_at=self._default_end(now_dt),
                                               place=self._place_of(pending["content"]),
                                               activity=self._activity_of(pending["content"]))
                out.update(action="approved", **{k: r[k] for k in ("plan_id", "revision", "status")})
                cases_api.record_receipt(self.db, case["id"],
                                         f"已确认：方案 {pending['id'][-6:]} 生效")
                return out
            except cases_api.CaseError as e:
                out.update(action="confirm_denied", reason=str(e)[:100])
                return out

        if not t.hit:
            return {"action": "unrelated", "rules": []}
        relation = triage.associate(t, active is not None)
        out = {"action": relation, "rules": t.rules, "kinds": t.kinds}

        # ---- 关联语义 ----
        if relation == "existing":
            case = dict(active)
            out.update(case_id=case["id"], case_status=case["status"])
            if "change" in t.kinds:   # 改口 → Rescheduling（仅组织者，事务层校验）
                try:
                    cases_api.mark_rescheduling(self.db, case["id"], sender)
                    out["rescheduling"] = True
                except cases_api.CaseError as e:
                    out["reschedule_denied"] = str(e)[:80]
            if "cancel" in t.kinds:   # 取消 → organizer 确认后 Cancelled
                try:
                    cases_api.cancel_case(self.db, case["id"], sender)
                    out["cancelled"] = True
                except cases_api.CaseError as e:
                    out["cancel_denied"] = str(e)[:80]
            self.db.audit(sender, f"case.related:{case['id']}:{'+'.join(t.kinds)}", event_id)

        elif relation == "new_case":
            case_id = f"case-{uuid.uuid4().hex[:8]}"
            organizer = sender or self.organizer_hint or "unknown"   # MVP：创建者即组织者
            self.db.create_case(case_id, room_id, organizer, event_id, TZ_NAME)
            self.db.audit(sender, f"case.created:{case_id}", event_id)
            self.db.set_state(f"case:{case_id}:latest_body", body[:200])
            out.update(case_id=case_id, organizer=organizer)
            # G4b 主链：octos 解析 → 严格校验 → 提案（M1）
            if self.llm is not None:
                try:
                    parsed = self.llm.parse_message(
                        f"parse-{abs(hash(event_id)) % 10**8}", body)
                    r = cases_api.create_proposal(self.db, case_id,
                        json.dumps(parsed, ensure_ascii=False), selected_slot="slot_01")
                    out.update(parsed=parsed, proposal_id=r["proposal_id"])
                    self.db.audit(sender, f"proposal.created:{r['proposal_id']}", event_id)
                    # M1 提案入 outbox（无需 grant）——提案文本确定性渲染
                    prop_text = (f"提案：{parsed.get('activity')} · {parsed.get('date_text')}"
                                 f" · {parsed.get('place')}。组织者回复「同意」确认。")
                    self.db.conn.execute(
                        "INSERT INTO outbox(id, case_id, txn_id, kind, room_id, text,"
                        " status, created_at) VALUES (?,?,?,?,?,?,'Pending',?)",
                        (f"out-{uuid.uuid4().hex[:12]}", case_id,
                         f"m1-{uuid.uuid4().hex[:12]}", "M1", room_id, prop_text, now()))
                except Exception as e:   # 解析/校验失败 → 明示降级（不伪造提案）
                    out["parse_error"] = str(e)[:120]
                    self.db.audit("guardian", f"parse.failed:{str(e)[:60]}", event_id)

        elif relation == "pending_intent":
            self.db.audit(sender,
                          f"pending_intent:{body[:60]} (active={active['id'] if active else '?'})",
                          event_id)
            out["note"] = "已记录新活动意向，待当前活动结束后处理"

        return out

    # ---- 提案内容的默认时间提取（确定性；P1 由规则引擎精化） ----
    @staticmethod
    def _default_start(now_dt: datetime) -> str:
        from datetime import timedelta
        return (now_dt + timedelta(days=1)).isoformat()

    @staticmethod
    def _default_end(now_dt: datetime) -> str:
        from datetime import timedelta
        return (now_dt + timedelta(days=1, hours=2)).isoformat()

    @staticmethod
    def _place_of(content_json: str) -> str | None:
        try:
            return json.loads(content_json).get("place")
        except Exception:
            return None

    @staticmethod
    def _activity_of(content_json: str) -> str | None:
        try:
            return json.loads(content_json).get("activity")
        except Exception:
            return None
