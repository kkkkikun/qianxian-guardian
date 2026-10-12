#!/usr/bin/env python3
"""牵线群智收敛（WP3 降级路径）：文字投票卡的归票与确定性计数。

规划 §2 WP3 降级分支（宿主不支持 m.replace → 文字投票卡 + 手动刷新；降级设计
evidence/wp3-fallback-design-20261012.md）。本模块是纯函数件，不碰 Matrix 网络：
输入房间消息列表（[{sender, body, ts}]），输出确定性计票结果——可单测。

归票规则（确定性，零 AI）：
- 成员回复字母（A-E，大小写不敏感；允许连写如「AB」= 多选，Telegram Multiple Answers 语义）；
- 只认整票：消息**全部内容**去除空白/标点后必须是 1..5 个 A-E 字母（防把闲聊误计为票）；
- 一人一票：同 sender 以**时间最新的一条**为准（改票幂等）；
- 非成员（不在参与人名单的 sender 显示名）票数不计，名单外标记 non_member；
- 平票/零票如实输出，不编造最优。

时段映射（与 app 内 5 槽轮换同源）：
  A=周六-上午  B=周六-下午  C=周六-晚上  D=周日-上午  E=周日-下午
"""
import re
from dataclasses import dataclass, field

SLOTS = {"A": "周六-上午", "B": "周六-下午", "C": "周六-晚上", "D": "周日-上午", "E": "周日-下午"}


@dataclass
class VoteResult:
    counts: dict = field(default_factory=dict)      # letter -> 票数
    voted_senders: list = field(default_factory=list)  # 有效投票者（去重）
    non_member_senders: list = field(default_factory=list)  # 名单外表态者
    total_members: int = 0                           # 参与人名单数 M
    winner: str = ""                                 # 票数最高字母（平票/零票为空）
    tie: bool = False                                # 是否平票
    summary: str = ""                                # 确定性摘要文本

    def as_dict(self):
        return {"counts": self.counts, "voted": self.voted_senders,
                "non_member": self.non_member_senders, "total_members": self.total_members,
                "winner": self.winner, "tie": self.tie, "summary": self.summary}


_TICKET = re.compile(r"^[A-Ea-e]{1,5}$")


def parse_ticket(body: str):
    """消息内容 → 合法字母票集合（set of letters）或 None（非整票）。"""
    t = (body or "").strip()
    # 去常见标点与空白（「A, B」「a；b」也认）
    t = re.sub(r"[\s，,;；、.。!！?？~～]+", "", t)
    if not _TICKET.match(t):
        return None
    return set(t.upper())


def count_votes(messages, member_names):
    """归票。messages: [{sender, body, ts}]（任意顺序）；member_names: [str]。
    sender 用显示名（与参与人名单同词表）。"""
    members = {m.strip() for m in member_names if m and m.strip()}
    # 按 sender 取最新票
    latest = {}
    for msg in messages:
        sender = (msg.get("sender") or "").strip()
        body = msg.get("body") or ""
        ts = msg.get("ts") or 0
        letters = parse_ticket(body)
        if letters is None:
            continue
        if sender not in latest or ts >= latest[sender][0]:
            latest[sender] = (ts, letters)

    res = VoteResult(total_members=len(members))
    counts = {L: 0 for L in SLOTS}
    for sender, (_ts, letters) in latest.items():
        if members and sender not in members:
            res.non_member_senders.append(sender)
            continue
        res.voted_senders.append(sender)
        for L in letters:
            counts[L] += 1
    res.counts = {L: c for L, c in counts.items() if c > 0}

    valid_total = sum(counts.values())
    if valid_total == 0:
        res.summary = f"已报 0/{len(members)}——还没有有效票"
        res.winner = ""
        return res

    top = max(counts.values())
    winners = [L for L, c in counts.items() if c == top]
    res.tie = len(winners) > 1
    res.winner = winners[0] if not res.tie else ""
    parts = " ".join(f"{L}:{counts[L]}" for L in SLOTS if counts[L] > 0)
    res.summary = f"已报 {len(res.voted_senders)}/{len(members)}（{parts}）"
    if res.non_member_senders:
        res.summary += f"；名单外 {len(res.non_member_senders)} 人表态不纳入"
    if res.tie:
        res.summary += f"；平票（{'/'.join(winners)}），请人工定夺"
    return res


# ---------------- 自测（python3 qx-converge.py） ----------------

def _selftest():
    M = ["阿明", "阿花", "张三"]
    # ① 基础归票 + 改票幂等（张三 A→B 取最新）
    msgs = [
        {"sender": "阿明", "body": "A", "ts": 1},
        {"sender": "阿花", "body": "ab", "ts": 2},
        {"sender": "张三", "body": "A", "ts": 3},
        {"sender": "张三", "body": "B", "ts": 4},
    ]
    r = count_votes(msgs, M)
    # 阿明 A；阿花 AB（A+B 各 1）；张三 A→B 改票取最新只算 B → A:2 B:2
    assert r.counts == {"A": 2, "B": 2}, r.counts
    assert r.tie and r.winner == ""
    assert len(r.voted_senders) == 3
    # ② 非成员拒收
    msgs2 = msgs + [{"sender": "路人", "body": "C", "ts": 5}]
    r2 = count_votes(msgs2, M)
    assert r2.non_member_senders == ["路人"], r2.non_member_senders
    assert r2.counts.get("C") is None
    # ③ 平票
    r3 = count_votes([{"sender": "阿明", "body": "A", "ts": 1},
                      {"sender": "阿花", "body": "B", "ts": 2}], M)
    assert r3.tie and r3.winner == ""
    assert "平票" in r3.summary
    # ④ 零票（闲聊不计）
    r4 = count_votes([{"sender": "阿明", "body": "好的没问题", "ts": 1}], M)
    assert r4.counts == {} and "已报 0/3" in r4.summary
    # ⑤ 整票守卫（「A 方案不错」不是票）
    assert parse_ticket("A 方案不错") is None
    assert parse_ticket("A,B") == {"A", "B"}
    assert parse_ticket("F") is None
    print("qx-converge selftest: 5/5 PASS")


if __name__ == "__main__":
    _selftest()
