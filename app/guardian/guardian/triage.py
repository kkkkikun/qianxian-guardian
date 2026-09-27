"""G2 分诊引擎：命中检测 + 时间归一化 + Case 关联判定（蓝图 v0.7.1 / G2 验收口径）。
纯函数、无 IO —— guardian 与未来 Splash 移植共用同一套规则定义。"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

TZ_NAME = "Asia/Shanghai"

# ---- 分诊规则表（命中规则名随证据提交，验收 1：误报 ≤1） ----
RULES = {
    "intent_activity": r"(聚(一?下|餐|会)?|约(饭|球|会)?|吃(饭|个饭)|骑车|骑行|爬山|看电影|唱歌|打球|桌游|露营|野餐)",
    "time_word":       r"(周[一二三四五六日天]|礼拜[一二三四五六日天]|明天|后天|今天|今晚|明晚|\d{1,2}\s*[日号]|\d{1,2}\s*[点时]|上午|下午|晚上|中午|周末)",
    "change_word":     r"(改(到|成|期|周[一二三四五六日天]|[一二三四五六日天])|换个?时间|不是周六|延期|推迟|提前)",
    "cancel_word":     r"(取消|不去了|去不了|算了吧|解散)",
    "rsvp_word":       r"(我可以|我去|算我一个|我也(去|来)|带我一个|来不了|去不了)",
    "ledger_word":     r"(垫了|付了|花了|一共|AA|转你|收你)",
    "at_bot":          r"@guardian_bot",
}
_RULE_RE = {k: re.compile(v) for k, v in RULES.items()}

WEEKDAY = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "六天": 5, "日": 6, "天": 6, "末": None}


@dataclass
class TriageResult:
    hit: bool
    kinds: list = field(default_factory=list)      # intent|change|cancel|rsvp|ledger|at_bot
    rules: list = field(default_factory=list)      # 命中的规则名（证据）
    body: str = ""
    sender: str = ""


def triage(body: str, sender: str = "") -> TriageResult:
    kinds, rules = [], []
    for name, rex in _RULE_RE.items():
        if rex.search(body):
            rules.append(name)
            if name == "intent_activity":
                kinds.append("intent")
            elif name in ("change_word",):
                kinds.append("change")
            elif name in ("cancel_word",):
                kinds.append("cancel")
            elif name in ("rsvp_word",):
                kinds.append("rsvp")
            elif name in ("ledger_word",):
                kinds.append("ledger")
    hit = bool(rules)
    return TriageResult(hit=hit, kinds=kinds, rules=rules, body=body, sender=sender)


# ---- 时间归一化（固定时区 Asia/Shanghai；蓝图：可控显式约束） ----
TIME_OF_DAY = {"上午": (9, 0), "早上": (8, 0), "中午": (12, 0), "下午": (14, 0),
               "晚上": (19, 0), "今晚": (19, 0), "明晚": (19, 0)}


def next_weekday(base: datetime, wd: int) -> datetime:
    days = (wd - base.weekday()) % 7
    if days == 0:
        days = 7  # "周六"指下一个周六
    return base + timedelta(days=days)


def normalize_time(body: str, now_dt: datetime):
    """从文本提取 (start_at, end_at) 估计值；返回 None 表示无可解析时间。
    精度规则：日期=周词/明天/后天/今天；时段=上午/下午/晚上/数字点；默认 2 小时时长。"""
    date_part = None
    m = re.search(r"(周|礼拜)([一二三四五六日天])", body)
    if m and m.group(2) in WEEKDAY and WEEKDAY.get(m.group(2)) is not None:
        date_part = next_weekday(now_dt, WEEKDAY[m.group(2)])
    elif re.search(r"明天|明晚", body):
        date_part = now_dt + timedelta(days=1)
    elif re.search(r"后天", body):
        date_part = now_dt + timedelta(days=2)
    elif re.search(r"今天|今晚", body):
        date_part = now_dt

    hour = None
    period = None
    m = re.search(r"(上午|下午|晚上|中午|早上)?\s*(\d{1,2})\s*[点时]", body)
    if m:
        hour = int(m.group(2))
        period = m.group(1)
        if period in ("下午", "晚上") and hour < 12:
            hour += 12
    elif (pm := re.search(r"上午|下午|晚上|中午|早上|今晚|明晚", body)):
        period = {"今晚": "晚上", "明晚": "晚上"}.get(pm.group(0), pm.group(0))
    if date_part is None and hour is None and period is None:
        return None
    base_day = date_part.date() if date_part else now_dt.date()
    if hour is not None:
        h, minute = hour, 0                     # 显式小时优先于时段默认
    else:
        h, minute = TIME_OF_DAY.get(period, (9, 0))
    start = datetime(base_day.year, base_day.month, base_day.day, h, minute,
                     tzinfo=now_dt.tzinfo)
    dur = re.search(r"(\d+(?:\.\d+)?)\s*(小时|个?小时|h)", body)
    hours = float(dur.group(1)) if dur else 2.0
    end = start + timedelta(hours=hours)
    return start, end


# ---- Case 关联判定（蓝图 v0.6 修订：四分法，不硬塞） ----
def associate(t: TriageResult, has_active_case: bool) -> str:
    """返回: existing(关联现有 Case) | pending_intent(新意图,已有 Case) |
    new_case(新 Case，无 Active) | unrelated(未命中)
    优先级：生命周期操作（改/取消/报名/台账）> 新意图。"""
    if not t.hit:
        return "unrelated"
    lifecycle = bool(set(t.kinds) & {"change", "cancel", "rsvp", "ledger"})
    if lifecycle:
        return "existing" if has_active_case else "unrelated"
    if "intent" in t.kinds or "at_bot" in t.kinds:
        return "pending_intent" if has_active_case else "new_case"
    return "unrelated"


# ---- 台账确定性解析（LLM 只给 candidate_ledger_text） ----
def parse_ledger(text: str, room_members: list[str]):
    """从 '我垫了 88' 类文本解析 (payer, amount_cents)。失败返回 None。"""
    m = re.search(r"(垫|付|花)了\s*(\d+(?:\.\d{1,2})?)", text)
    if not m:
        return None
    amount = round(float(m.group(2)) * 100)
    payer = None
    for mem in room_members:
        if mem in text:
            payer = mem
            break
    if payer is None:
        payer = "sender"  # 由调用方以 sender 补齐
    return payer, amount
