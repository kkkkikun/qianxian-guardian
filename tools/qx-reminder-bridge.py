#!/usr/bin/env python3
"""牵线守护伴生服务 v0.8.0：三级提醒 + 天气主动复核 + 沉默留痕 + 催收档位守护。

app 任何宿主都不能自醒（makepad timer 随 isolate 销毁；无宿主 cron）——真定时行为
由本进程承担（宿主侧场外组件，同 guardian 定位）。guardian 的 durable scheduler
（smoke_g6 12/12）是同一方案的 DB 版；本桥是文件版，专供 script-app 联动演示。

v0.8.0 四件事（调研报告 P0/P1 的进程侧落点）：
  1. 三级提醒节奏（Partiful/R1 同款）：T-7d 邀请确认 / T-24h 提醒 / 活动日晨 08:00 出发。
  2. 天气主动复核（Proactive，官方哲学第三条）：T-24h 触发时先查 open-meteo——
     降水概率 ≥60% 才在提醒里附预警（附数据来源与日期，no-facts）；无雨则不打扰，
     但写沉默留痕（"考虑过、决定不说"也要在案，arXiv 2605.06717）。
  3. 沉默留痕写端：suppressed.json（jail 内，app 聊天视图「🤫 沉默留痕」区回读）。
  4. 催收档位守护：活动过后 bill 未清 → T+1 系统口吻不点名 / T+7 最后一催（与 app 内
     梯度催收同口径；永不公示名单）。

用法：
  python3 tools/qx-reminder-bridge.py --jail <jail目录> --room '<!roomid:server>' \
      [--interval 60] [--account 0] [--dry-run] [--proxy http://127.0.0.1:10808]
凭据读工作区 test-accounts.json（不入库不入日志）。
"""
import argparse
import json
import pathlib
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app" / "guardian"))

STATE_FILE = "qx-reminders-sent.json"
SUPPRESSED_FILE = "suppressed.json"   # app 端 load_suppressed() 回读同一文件
SUPPRESSED_CAP = 50

# 户外活动词（天气预警只对户外聚会追加——室内聚餐下雨不是事，防过度打扰）
OUTDOOR_HINTS = ("骑车", "骑行", "爬山", "徒步", "野餐", "露营", "跑步", "球", "公园", "湾", "山", "湖")


def load_cases(jail: pathlib.Path):
    f = jail / "cases.json"
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text()).get("cases", [])
    except Exception as e:
        print(f"[bridge] cases.json 解析失败：{e}", flush=True)
        return []


def load_state(jail: pathlib.Path):
    f = jail / STATE_FILE
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            pass
    return {}


def save_state(jail: pathlib.Path, state):
    (jail / STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=1))


def record_suppressed(jail: pathlib.Path, kind: str, detail: str):
    """沉默留痕：追加式写 suppressed.json（对象包裹 {"entries":[…]}——app 端 parse_json
    与 cases.json 同范式只吃对象；截尾保最近 CAP 条；按 detail 去重防轮询刷屏——
    同一条"考虑过没说"只记一次，变化了才再记）。失败不致命（best-effort）。"""
    f = jail / SUPPRESSED_FILE
    entries = []
    if f.exists():
        try:
            entries = json.loads(f.read_text()).get("entries") or []
        except Exception:
            entries = []
    if any(e.get("detail") == detail for e in entries):
        return
    entries.append({
        "ts": (datetime.utcnow() + timedelta(hours=8)).strftime("%m-%d %H:%M"),
        "kind": kind,
        "detail": detail,
    })
    entries = entries[-SUPPRESSED_CAP:]
    try:
        f.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=1))
    except Exception as e:
        print(f"[bridge] suppressed.json 写失败：{e}", flush=True)


def beijing_now():
    return datetime.utcnow() + timedelta(hours=8)


def resolve_target_date(case):
    """活动日（北京时区 date）或 None。target_date 优先；旧数据按 slot_day 解析最近未来同名日。"""
    d = case.get("target_date") or ""
    if d:
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            return None
    wd_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
    wd = wd_map.get(case.get("slot_day", ""))
    if wd is None:
        return None
    today = beijing_now().date()
    delta = (wd - today.weekday()) % 7  # python Monday=0
    return today + timedelta(days=delta)


# ---------------- 天气主动复核（open-meteo；no-facts：查不到就明说，绝不编） ----------------

_geo_cache = {}


def weather_precip_for(place: str, day, proxy: str):
    """返回 (降水概率 0-100 或 None, 原因)。open-meteo geocoding + daily precipitation_probability_max。"""
    import requests
    px = {"http": None, "https": None}
    if proxy:
        px = {"http": proxy, "https": proxy}
    if place not in _geo_cache:
        try:
            r = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": place, "count": 1, "language": "zh"},
                proxies=px, timeout=8,
            )
            hits = (r.json() or {}).get("results") or []
            if not hits:
                _geo_cache[place] = None
            else:
                _geo_cache[place] = (hits[0]["latitude"], hits[0]["longitude"], hits[0].get("name", place))
        except Exception as e:
            return None, f"地理编码查询失败：{type(e).__name__}"
    geo = _geo_cache[place]
    if geo is None:
        return None, "地点未匹配到坐标"
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": geo[0], "longitude": geo[1],
                    "daily": "precipitation_probability_max", "timezone": "Asia/Shanghai"},
            proxies=px, timeout=8,
        )
        daily = (r.json() or {}).get("daily") or {}
        dates = daily.get("time") or []
        if day.isoformat() not in dates:
            return None, "预报窗口不含活动日（>16 天）"
        i = dates.index(day.isoformat())
        probs = (daily.get("precipitation_probability_max") or [None] * len(dates))
        p = probs[i]
        if p is None:
            return None, "预报缺降水概率字段"
        return float(p), f"{geo[2]} {day.isoformat()}"
    except Exception as e:
        return None, f"天气查询失败：{type(e).__name__}"


def is_outdoor(case):
    text = f"{case.get('activity', '')}{case.get('place', '')}{case.get('text', '')}"
    return any(h in text for h in OUTDOOR_HINTS)


# ---------------- 主循环 ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jail", required=True)
    ap.add_argument("--room", required=True)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--account", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--proxy", default="", help="天气查询代理（如 http://127.0.0.1:10808）；空=直连")
    ap.add_argument("--no-weather", action="store_true", help="禁用天气复核（离线演示）")
    args = ap.parse_args()

    jail = pathlib.Path(args.jail)
    acc = json.loads(pathlib.Path("/home/kikun/MyProject/Agentic-octos/test-accounts.json").read_text())
    homeserver = acc["homeserver"]
    a = acc["accounts"][args.account]

    from guardian.matrix import MatrixClient
    client = MatrixClient(homeserver, a["username"], a["password"])
    client.login()
    print(f"[bridge] 已登录 {a['username']} @ {homeserver}；jail={jail} room={args.room} "
          f"weather={'off' if args.no_weather else ('proxy' if args.proxy else 'direct')}", flush=True)

    def send(key, text):
        if args.dry_run:
            print(f"[bridge][dry] 将发送 {key}：{text}", flush=True)
        else:
            txn = f"qx-reminder-{key}"
            client.send_message_with_retry(args.room, text, txn, attempts=3)
            print(f"[bridge] 已发送 {key}", flush=True)

    while True:
        state = load_state(jail)
        now = beijing_now()
        today = now.date()
        dirty = False
        for case in load_cases(jail):
            cid = case.get("id")
            act = case.get("activity") or "聚会"
            slot = f"{case.get('slot_day', '')}-{case.get('slot_part', '')}"
            place = case.get("place") or ""
            people = case.get("people") or "暂无登记"
            day = resolve_target_date(case)
            if day is None:
                continue

            # ---------- 活动前：三级提醒（T-7d / T-24h / 活动日晨） ----------
            if case.get("status") == "Confirmed":
                # ① T-7d：邀请确认（远期核对名单；临期 1 天内 T-24h 会发，不再叠加噪音）
                k7 = f"{cid}:{day.isoformat()}:T7d"
                days_to = (day - today).days
                if k7 not in state and 1 < days_to <= 7:
                    send(k7, f"📋 牵线确认（T-7d）：#{cid} {act}（{slot} · {place or '地点未抽取到'}）"
                              f"下周期内举行。参与人：{people}——名单有变现在说，来得及改。")
                    state[k7] = now.isoformat()
                    dirty = True

                # ② T-24h：主提醒（附天气主动复核——≥60% 降水才预警；无雨=沉默留痕）
                k24 = f"{cid}:{day.isoformat()}:T24h"
                if k24 not in state and 0 < days_to <= 1:
                    weather_line = ""
                    if not args.no_weather and place:
                        if is_outdoor(case):
                            p, why = weather_precip_for(place, day, args.proxy)
                            if p is not None and p >= 60:
                                weather_line = (f" ⛈ 天气预警：降水概率 {p:.0f}%（open-meteo·{day.isoformat()}）"
                                                f"——户外活动建议备伞或考虑改期，找管家出改期提案。")
                            elif p is not None:
                                record_suppressed(jail, "weather_ok",
                                                  f"#{cid} {act}：降水 {p:.0f}%（{why}）<60%，不打扰")
                            else:
                                record_suppressed(jail, "weather_unknown",
                                                  f"#{cid} {act}：天气未查到（{why}），提醒照发不带天气")
                        else:
                            record_suppressed(jail, "weather_ok", f"#{cid} {act}：室内活动，跳过天气复核")
                    send(k24, f"⏰ 牵线提醒（T-24h）：#{cid} {act}（{slot} · {place or '地点未抽取到'}）"
                              f"明天开始！参与人：{people}。"
                              f"AA{'已收齐 ✓' if case.get('bill_cleared') == 'yes' else '记得收尾'}。"
                              f"{weather_line}")
                    state[k24] = now.isoformat()
                    dirty = True

                # ③ 活动日晨（北京 08:00 后）：出发提醒
                km = f"{cid}:{day.isoformat()}:Morning"
                if km not in state and days_to == 0 and now.hour >= 8:
                    send(km, f"🚗 牵线出发提醒：#{cid} {act}（{slot} · {place or '地点未抽取到'}）就是今天！"
                             f"参与人：{people}——路上小心，玩得开心。")
                    state[km] = now.isoformat()
                    dirty = True

            # ---------- 活动后：催收档位守护（T+1 系统口吻 / T+7 最后一催；永不公示名单） ----------
            if case.get("status") in ("Confirmed", "Completed") and case.get("bill_total") \
                    and case.get("bill_cleared") != "yes":
                days_past = (today - day).days
                kd1 = f"{cid}:{day.isoformat()}:DunT1"
                if days_past == 1 and kd1 not in state:
                    send(kd1, f"💰 聚会账单（系统提醒）：#{cid} {act} 的 AA 还没收齐哦——"
                              f"麻烦还没转的伙伴这两天转一下组织者，谢谢～")
                    state[kd1] = now.isoformat()
                    dirty = True
                else:
                    record_suppressed(jail, "dunning",
                                      f"#{cid} 催收未到档（已过 {days_past} 天；T+1/T+7 才开口）")
                kd7 = f"{cid}:{day.isoformat()}:DunT7"
                if days_past == 7 and kd7 not in state:
                    send(kd7, f"💰【最后一催】#{cid} {act} 的 AA 还差一点——今天转一下；"
                              f"实在收不齐就在牵线里点「AA 已收齐」体面结账，差额线下算清。")
                    state[kd7] = now.isoformat()
                    dirty = True

        if dirty:
            save_state(jail, state)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
