#!/usr/bin/env python3
"""牵线成员端自治守护进程（WP1 旗舰）：群里的时间收敛投票卡 → 本端确定性自治投票。

链路：sync 读房 → 识别投票卡（📋 时间收敛投票：#N …）→ 读本端 jail cases.json
查同时段冲突 → 确定性策略投票（数字与冲突判定全由代码算，模型零参与）：
  - 首选（A）无冲突 → 投 A；
  - 首选撞期 → 投顺延的首个无冲突项，房内说明理由一句；
  - 全部撞期 → 不投任何字母（房内如实说「都撞了」——归票器只认字母票，此句不计票）。
改票：本端 cases 变化后重评估，结论变了就再发一条字母（归票 latest-wins 幂等）。
出件（jail）：member-vote.json（当前我的票+理由，app 内可视）；member-revote.json
是 app 侧「改投」按钮的 Outbox 请求文件，本进程消费后即删。

用法：
  python3 tools/qx-member-agent.py --jail <成员jail目录> --room '<!roomid:server>' \
      [--account 1] [--once] [--interval 15]
凭据读工作区 test-accounts.json（不入库不入日志）。
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app" / "guardian"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from guardian.matrix import MatrixClient  # noqa: E402

CARD_HEAD = "📋 时间收敛投票：#"
CAND_RE = re.compile(r"([A-E])\.\s*([^\s，,]+)")  # 「A. 周六-上午」对
ACTIVE = ("Proposing", "Confirmed")


def beijing_now():
    return datetime.utcnow() + timedelta(hours=8)


def fetch_messages(client, room, limit=50):
    code, r = client._req("GET", f"/_matrix/client/v3/rooms/{room}/messages",
                          None, {"dir": "b", "limit": str(limit)})
    if code != 200:
        raise RuntimeError(f"read messages {code}: {r}")
    out = []
    for e in r.get("chunk", []):
        if e.get("type") != "m.room.message":
            continue
        body = (e.get("content") or {}).get("body")
        if not isinstance(body, str):
            continue
        out.append({"sender": (e.get("sender") or "").split(":")[0].lstrip("@"),
                    "body": body, "ts": e.get("origin_server_ts", 0)})
    return out


def find_cards(msgs):
    """房间里最近一张投票卡（body + 候选 {letter: slot} + key 内容哈希）。"""
    for m in msgs:  # dir=b 已是新→旧
        body = m["body"]
        if body.startswith(CARD_HEAD):
            cands = dict(CAND_RE.findall(body))
            if cands:
                key = hashlib.sha256(body.encode()).hexdigest()[:16]
                return {"key": key, "body": body, "cands": cands, "ts": m["ts"]}
    return None


def load_my_cases(jail):
    f = jail / "cases.json"
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text()).get("cases", [])
    except Exception:
        return []


def my_busy_slots(cases):
    out = set()
    for c in cases:
        if c.get("status") in ACTIVE:
            d, p = (c.get("slot_day") or ""), (c.get("slot_part") or "")
            if d and p:
                out.add(f"{d}-{p}")
    return out


def decide_vote(cands, busy):
    """确定性自治策略（纯函数，可单测）：
    返回 (letter 或 "", reason, chosen_slot)。letter 为空 = 全部撞期不投票。"""
    if not cands:
        return "", "投票卡里没有候选时段", ""
    order = [L for L in "ABCDE" if L in cands]
    for i, letter in enumerate(order):
        slot = cands[letter]
        if slot not in busy:
            if i == 0:
                return letter, "首选无冲突", slot
            return letter, f"首选撞期（{cands[order[0]]}），顺延到 {slot}", slot
    return "", "候选时段全与我现有守护撞期", ""


def card_key_of(revote):
    return "" if not revote else revote.get("card_key", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jail", required=True)
    ap.add_argument("--room", required=True)
    ap.add_argument("--account", type=int, default=1)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=15)
    args = ap.parse_args()

    jail = pathlib.Path(args.jail)
    jail.mkdir(parents=True, exist_ok=True)
    acc = json.loads(pathlib.Path("/home/kikun/MyProject/Agentic-octos/test-accounts.json").read_text())
    a = acc["accounts"][args.account]
    me = a["username"]
    client = MatrixClient(acc["homeserver"], me, a["password"],
                          token_path=f"/tmp/qx-matrix-token-{me}.cache")
    client.login()
    print(f"[member-agent] 已登录 {me}；room={args.room}", flush=True)

    while True:
        try:
            msgs = fetch_messages(client, args.room, limit=50)
            card = find_cards(msgs)
            state_f = jail / "member-vote.json"
            state = {}
            if state_f.exists():
                try:
                    state = json.loads(state_f.read_text())
                except Exception:
                    state = {}

            # Outbox：app 侧「改投」请求（member-revote.json {letter, reason}）
            revote_f = jail / "member-revote.json"
            if revote_f.exists() and card:
                try:
                    rv = json.loads(revote_f.read_text())
                except Exception:
                    rv = {}
                letter = (rv.get("letter") or "").strip().upper()
                if letter in card["cands"]:
                    reason = rv.get("reason") or "手动改投"
                    client.send_message(args.room, letter,
                                        txn_id="revote-" + card["key"] + "-" + letter)
                    state = {"card_key": card["key"], "letter": letter,
                             "slot": card["cands"][letter], "reason": reason,
                             "cands": card["cands"],
                             "at": beijing_now().isoformat(), "auto": False}
                    state_f.write_text(json.dumps(state, ensure_ascii=False, indent=1))
                    print(f"[member-agent] 改投 {letter}（{reason}）", flush=True)
                revote_f.unlink(missing_ok=True)

            elif card and state.get("card_key") != card["key"]:
                # 新卡：确定性自治评估并投票
                busy = my_busy_slots(load_my_cases(jail))
                letter, reason, slot = decide_vote(card["cands"], busy)
                if letter:
                    client.send_message(args.room, letter,
                                        txn_id="vote-" + card["key"] + "-" + me)
                    if reason != "首选无冲突":
                        client.send_message(args.room, f"（{me}：{reason}）",
                                            txn_id="vote-why-" + card["key"] + "-" + me)
                    print(f"[member-agent] 投 {letter}（{slot}）：{reason}", flush=True)
                else:
                    client.send_message(args.room, f"（{me}：{reason}，这票弃权）",
                                        txn_id="vote-none-" + card["key"] + "-" + me)
                    print(f"[member-agent] 弃权：{reason}", flush=True)
                state = {"card_key": card["key"], "letter": letter,
                         "slot": slot, "reason": reason,
                         "at": beijing_now().isoformat(), "auto": True}
                state_f.write_text(json.dumps(state, ensure_ascii=False, indent=1))
            elif card and state.get("auto", True):
                # 同一张卡且当前票是自治投出的：本端日历变了就重评估（撤回改票=再发字母，归票幂等）。
                #   手动改投（auto=false）不被自治回滚——人的覆盖优先于规则。
                busy = my_busy_slots(load_my_cases(jail))
                letter, reason, slot = decide_vote(card["cands"], busy)
                if letter != state.get("letter", ""):
                    if letter:
                        client.send_message(args.room, letter,
                                            txn_id="vote-re-" + card["key"] + "-" + me + "-" + letter)
                        print(f"[member-agent] 改票 {state.get('letter')}→{letter}（{reason}）", flush=True)
                    else:
                        client.send_message(args.room, f"（{me}：情况变了，{reason}，撤回我的字母票）",
                                            txn_id="vote-re-none-" + card["key"] + "-" + me)
                        print(f"[member-agent] 撤票：{reason}", flush=True)
                    state = {"card_key": card["key"], "letter": letter,
                             "slot": slot, "reason": reason, "cands": card["cands"],
                             "at": beijing_now().isoformat(), "auto": True}
                    state_f.write_text(json.dumps(state, ensure_ascii=False, indent=1))
        except Exception as e:
            print(f"[member-agent] 本轮失败（下轮重试）：{e}", flush=True)
        if args.once:
            return
        time.sleep(args.interval)


def _selftest():
    """确定性自治策略纯函数自测（不进 Matrix）。"""
    cands = {"A": "周六-上午", "B": "周六-下午", "C": "周六-晚上"}
    # 1 首选无冲突 → A
    assert decide_vote(cands, set()) == ("A", "首选无冲突", "周六-上午")
    # 2 首选撞期 → 顺延 B + 理由
    l, r, sl = decide_vote(cands, {"周六-上午"})
    assert (l, sl) == ("B", "周六-下午") and "顺延" in r, (l, r, sl)
    # 3 全部撞期 → 不投票（空字母）
    l, r, sl = decide_vote(cands, {"周六-上午", "周六-下午", "周六-晚上"})
    assert l == "" and "全" in r, (l, r)
    # 4 前二撞期 → C
    l, r, sl = decide_vote(cands, {"周六-上午", "周六-下午"})
    assert l == "C" and sl == "周六-晚上" and "顺延" in r, (l, r, sl)
    # 5 空候选 → 不投票
    assert decide_vote({}, set())[0] == ""
    # 附：投票卡识别
    body = "📋 时间收敛投票：#1 骑车 · 深圳湾\n候选时段（回复对应字母即投票）：\nA. 周六-上午    B. 周六-下午\n回复如「A」。"
    card = find_cards([{"sender": "org", "body": body, "ts": 1}])
    assert card and card["cands"] == {"A": "周六-上午", "B": "周六-下午"}, card
    # 附：忙碌槽位只收活跃态
    busy = my_busy_slots([{"status": "Confirmed", "slot_day": "周六", "slot_part": "上午"},
                          {"status": "Cancelled", "slot_day": "周日", "slot_part": "下午"}])
    assert busy == {"周六-上午"}, busy
    print("qx-member-agent selftest: 7/7 PASS")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
