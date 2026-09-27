"""活动簿网页卡（MVP：绑 127.0.0.1，单机演示）。
GET /           活动簿 HTML（Case/Plan/Proposal/审计摘要）
GET /api/state  全量 JSON（供 smoke 断言）
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .db import DB


def collect_state(db: DB) -> dict:
    cases = [dict(r) for r in db.conn.execute("SELECT * FROM cases ORDER BY created_at")]
    for c in cases:
        cid = c["id"]
        c["plans"] = [dict(r) for r in db.conn.execute(
            "SELECT plan_id, revision, start_at, end_at, place, activity, status"
            " FROM plans WHERE case_id=? ORDER BY revision", (cid,))]
        c["proposals"] = [dict(r) for r in db.conn.execute(
            "SELECT id, based_on_revision, content, status FROM proposals"
            " WHERE case_id=? ORDER BY created_at", (cid,))]
        c["audit_count"] = db.conn.execute(
            "SELECT count(*) c FROM audit WHERE evidence_ref=?", (cid,)).fetchone()["c"]
        c["pending_outbox"] = db.conn.execute(
            "SELECT count(*) c FROM outbox WHERE case_id=? AND status='Pending'",
            (cid,)).fetchone()["c"]
    return {"cases": cases}


def render_html(state: dict) -> str:
    rows = []
    for c in state["cases"]:
        active = [p for p in c["plans"] if p["status"] == "Active"]
        superseded = [p for p in c["plans"] if p["status"] == "Superseded"]
        plan_html = ""
        if active:
            p = active[0]
            plan_html = (f"<b>{p['activity'] or '活动'}</b> · {p['start_at']} ~ {p['end_at']}"
                         f" · {p['place'] or '待定'} (rev {p['revision']})")
        else:
            plan_html = "暂无生效方案"
        props = "".join(
            f"<li> prop {p['id'][-6:]} · rev{p['based_on_revision']} · {p['status']}"
            f" · {p['content'][:40]}</li>" for p in c["proposals"])
        rows.append(f"""
        <div class="case {c['status']}">
          <h3>{c['id']} <span class="badge">{c['status']}</span> rev {c['revision']}</h3>
          <p>组织者: {c['organizer_id']} ｜ 审计 {c['audit_count']} 条 ｜ 待发 M2/M3: {c['pending_outbox']}</p>
          <p>当前方案: {plan_html}</p>
          <p>历史方案: {f"Superseded ×{len(superseded)}" if superseded else "无"}</p>
          <ul>{props}</ul>
        </div>""")
    body = "".join(rows) or "<p>暂无 Case</p>"
    return f"""<!doctype html><html><head><meta charset="utf-8">
    <title>牵线 · 活动簿</title><style>
    body{{font-family:system-ui;max-width:760px;margin:24px auto;color:#1c1c1c}}
    .case{{border:1px solid #ddd;border-radius:10px;padding:12px 16px;margin:12px 0}}
    .badge{{background:#0a7d6f;color:#fff;border-radius:6px;padding:2px 8px;font-size:13px}}
    .case.Cancelled .badge{{background:#888}} .case.Rescheduling .badge{{background:#c77b00}}
    li{{margin:2px 0}} small{{color:#888}}
    </style></head><body>
    <h2>牵线 · 活动簿</h2><small>数据源：guardian SQLite（唯一事实源）· 127.0.0.1 仅本机</small>
    {body}</body></html>"""


class Handler(BaseHTTPRequestHandler):
    db_path: str = None  # 每请求独立连接（SQLite 跨线程限制）

    def do_GET(self):
        if self.path == "/api/state":
            state = collect_state(DB(self.db_path))
            body = json.dumps(state, ensure_ascii=False).encode()
            ctype = "application/json; charset=utf-8"
        elif self.path in ("/", "/index.html"):
            body = render_html(collect_state(DB(self.db_path))).encode()
            ctype = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # 静默访问日志
        pass


def serve(db_path: str, host: str = "127.0.0.1", port: int = 8129) -> HTTPServer:
    Handler.db_path = db_path
    srv = HTTPServer((host, port), Handler)
    return srv


def run_forever(db_path: str, port: int = 8129):
    srv = serve(db_path, port=port)
    print(f"[activity-book] http://127.0.0.1:{port}/")
    srv.serve_forever()
