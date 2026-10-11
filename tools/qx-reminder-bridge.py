#!/usr/bin/env python3
"""牵线守护伴生服务：T-24h 提醒真投递（宿主侧场外组件，同 guardian 定位）。

app 任何宿主都不能自醒（makepad timer 随 isolate 销毁；无宿主 cron）——真定时提醒
由本进程承担：轮询 card-host jail 的 cases.json，对已确认且有可解析日期的守护，
在活动前 24h 通过 Matrix 真发提醒（幂等标记防重发）。guardian 的 durable scheduler
（smoke_g6 12/12）是同一方案的 DB 版；本桥是文件版，专供 script-app 联动演示。

用法：
  python3 tools/qx-reminder-bridge.py --jail <jail目录> --room '<!roomid:server>' \
      [--interval 60] [--account 0] [--dry-run]
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


def beijing_now():
    return datetime.utcnow() + timedelta(hours=8)


def due_for(case):
    """返回提醒到期时间（北京时间）或 None。T-24h：活动日（all-day）前一天的此刻起。"""
    if case.get("status") != "Confirmed":
        return None
    d = case.get("target_date") or ""
    if not d:
        # 旧数据无 target_date：由 slot_day 每次解析（与 app 内 resolve_slot_date 同义，
        # 这里用 python 重算——槽位词 → 最近未来同名日）
        wd_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
        wd = wd_map.get(case.get("slot_day", ""))
        if wd is None:
            return None
        today = beijing_now().date()
        delta = (wd - today.weekday()) % 7  # python Monday=0
        d = (today + timedelta(days=delta)).isoformat()
    try:
        event_day = datetime.strptime(d, "%Y-%m-%d")
    except ValueError:
        return None
    return event_day - timedelta(hours=24)  # T-24h 起为提醒窗口


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jail", required=True)
    ap.add_argument("--room", required=True)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--account", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    jail = pathlib.Path(args.jail)
    acc = json.loads((jail.parents[2] if False else pathlib.Path("/home/kikun/MyProject/Agentic-octos/test-accounts.json")).read_text())
    homeserver = acc["homeserver"]
    a = acc["accounts"][args.account]

    from guardian.matrix import MatrixClient
    client = MatrixClient(homeserver, a["username"], a["password"])
    client.login()
    print(f"[bridge] 已登录 {a['username']} @ {homeserver}；jail={jail} room={args.room}", flush=True)

    while True:
        state = load_state(jail)
        now = beijing_now()
        for case in load_cases(jail):
            due = due_for(case)
            if due is None:
                continue
            key = f"{case.get('id')}:{case.get('target_date') or case.get('slot_day')}:{case.get('status')}:T24h"
            if key in state:
                continue
            if now < due:
                continue
            act = case.get("activity") or "聚会"
            slot = f"{case.get('slot_day', '')}-{case.get('slot_part', '')}"
            place = case.get("place") or "（地点未抽取到）"
            people = case.get("people") or "暂无登记"
            text = (f"⏰ 牵线提醒（T-24h）：#{case.get('id')} {act}"
                    f"（{slot} · {place}）明天就开始了！参与人：{people}。"
                    f"AA{'已收齐' if case.get('bill_cleared') == 'yes' else '记得收尾'}，"
                    f"需要改期或取消找牵线管家。")
            if args.dry_run:
                print(f"[bridge][dry] 将发送：{text}", flush=True)
            else:
                txn = f"qx-reminder-{key}"
                try:
                    client.send_message_with_retry(args.room, text, txn, max_retries=3)
                    print(f"[bridge] 已发送 {key}", flush=True)
                except Exception as e:
                    print(f"[bridge] 发送失败（下轮重试）{key}: {e}", flush=True)
                    continue
            state[key] = now.isoformat()
            save_state(jail, state)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
