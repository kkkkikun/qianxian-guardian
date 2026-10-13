#!/usr/bin/env python3
"""牵线群智收敛伴生进程（WP3-A）：读房间消息 → 归票 → 写 jail 的 converge.json。

app 的「刷新计票」读 converge.json 显示；「管家收敛」按 winner_slot 出提案。
与 qx-reminder-bridge 同定位（宿主侧场外组件，Matrix 真通路复用 guardian 客户端）。

用法：
  python3 tools/qx-converge-bridge.py --jail <jail目录> --room '<!roomid:server>' \
      --case-id <N> [--once] [--interval 20] [--account 0]
凭据读工作区 test-accounts.json（不入库不入日志）。
归票逻辑 import 自 tools/qx-converge.py（同仓纯函数，单测 5/5）。
"""
import argparse
import json
import pathlib
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app" / "guardian"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from guardian.matrix import MatrixClient  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "qx_converge", pathlib.Path(__file__).resolve().parent / "qx-converge.py")
qx_converge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qx_converge)

SLOTS = qx_converge.SLOTS


def beijing_now():
    return datetime.utcnow() + timedelta(hours=8)


def load_members(jail: pathlib.Path, case_id: str):
    f = jail / "cases.json"
    if not f.exists():
        return [], None
    try:
        cases = json.loads(f.read_text()).get("cases", [])
    except Exception:
        return [], None
    for c in cases:
        if str(c.get("id")) == str(case_id):
            ppl = (c.get("people") or "").strip()
            members = [x.strip() for x in ppl.split(",") if x.strip()]
            return members, c
    return [], None


def fetch_messages(client, room, limit=50):
    """读房间最近消息（guardian 客户端 _req 直取；返回 [{sender, body, ts}]）。"""
    code, r = client._req("GET", f"/_matrix/client/v3/rooms/{room}/messages",
                          None, {"dir": "b", "limit": str(limit)})
    if code != 200:
        raise RuntimeError(f"read messages {code}: {r}")
    out = []
    for e in r.get("chunk", []):
        if e.get("type") != "m.room.message":
            continue
        content = e.get("content") or {}
        body = content.get("body")
        if not isinstance(body, str):
            continue
        sender = (e.get("sender") or "").split(":")[0].lstrip("@")
        out.append({"sender": sender, "body": body,
                    "ts": e.get("origin_server_ts", 0)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jail", required=True)
    ap.add_argument("--room", required=True)
    ap.add_argument("--case-id", required=True)
    ap.add_argument("--once", action="store_true", help="跑一轮即退出（e2e/手动刷新）")
    ap.add_argument("--interval", type=int, default=20)
    ap.add_argument("--account", type=int, default=0)
    args = ap.parse_args()

    jail = pathlib.Path(args.jail)
    acc = json.loads(pathlib.Path("/home/kikun/MyProject/Agentic-octos/test-accounts.json").read_text())
    a = acc["accounts"][args.account]
    client = MatrixClient(acc["homeserver"], a["username"], a["password"],
                          token_path=f"/tmp/qx-matrix-token-{a['username']}.cache")
    client.login()
    print(f"[converge-bridge] 已登录 {a['username']}；room={args.room} case=#{args.case_id}", flush=True)

    while True:
        members, case = load_members(jail, args.case_id)
        if case is None:
            print(f"[converge-bridge] jail 里找不到 #{args.case_id}", flush=True)
            if args.once:
                return
        else:
            try:
                msgs = fetch_messages(client, args.room, limit=50)
                res = qx_converge.count_votes(msgs, members)
                winner_slot = SLOTS.get(res.winner, "") if res.winner else ""
                payload = {
                    "case_id": str(args.case_id),
                    "room": args.room,
                    "summary": res.summary,
                    "winner": res.winner,
                    "winner_slot": winner_slot,
                    "counts": res.counts,
                    "voted": res.voted_senders,
                    "non_member": res.non_member_senders,
                    "total_members": res.total_members,
                    "at": beijing_now().isoformat(),
                }
                (jail / "converge.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=1))
                print(f"[converge-bridge] 计票：{res.summary}"
                      + (f" → 收敛候选 {winner_slot}" if winner_slot else ""), flush=True)
            except Exception as e:
                print(f"[converge-bridge] 计票失败（下轮重试）：{e}", flush=True)
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
