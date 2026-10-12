#!/usr/bin/env python3
"""牵线主动守护进程（WP4）：T-24h 到点主动发起 octos.turn.start 回合。

与 tools/qx-reminder-bridge.py（只发提醒）的关系：本进程是「到点醒来干活」的决策环——
到点先查天气（确定性规则 + open-meteo，不编造），再把**机器提案**写进 app jail
（pending_plan.json）；app 进聊天视图读入提案卡，人拍板后走既有白名单链落地。
这是对 RFC octos#2768「宿主应支持 agent 按时间/事件自驱唤醒」的参考实现闭环：
app 任何宿主都不能自醒（makepad timer 随 isolate 销毁；无宿主 cron），
真实定时行为由宿主侧场外进程承担（同 guardian 定位）。

两种模型通路（--mode）：
  direct  —— 直连 Kimi API（api.kimi.com/coding/v1，OpenAI 兼容；agent 语义在进程内，
             key 只经 env，无 ambient 注入陷阱）；本机无内核依赖，最稳。
  kernel  —— octos serve --stdio 内核 JSON-RPC（session/open + turn/start；
             真 octos 内核原生 moonshot-coding family；RFC 闭环证据）。

用法：
  python3 tools/qx-proactive-butler.py --jail <jail目录> [--room '<!roomid:server>']
      [--mode direct|kernel] [--interval 300] [--dry-run] [--proxy http://127.0.0.1:10808]
      [--kimi-key-file <path>] [--octos-bin <path>] [--data-dir <path>]
凭据：Kimi key 读工作区 .secrets/kimi-api-key（600，不入库不入日志）；
     Matrix 凭据读 test-accounts.json（仅当给 --room 时才发群消息，可省）。
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app" / "guardian"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

STATE_FILE = "qx-proactive-sent.json"
PENDING_PLAN_FILE = "pending_plan.json"      # app 端 enter_chat 读入提案卡的契约文件
SUPPRESSED_FILE = "suppressed.json"

DEFAULT_JAIL_HINT = "/tmp/octosense-card-apps/qianxian"


def beijing_now():
    return datetime.utcnow() + timedelta(hours=8)


def resolve_target_date(case):
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
    return today + timedelta(days=(wd - today.weekday()) % 7)


def load_cases(jail: pathlib.Path):
    f = jail / "cases.json"
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text()).get("cases", [])
    except Exception as e:
        print(f"[proactive] cases.json 解析失败：{e}", flush=True)
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
    """与 qx-reminder-bridge 同款：对象包裹+按 detail 去重。"""
    f = jail / SUPPRESSED_FILE
    entries = []
    if f.exists():
        try:
            entries = json.loads(f.read_text()).get("entries") or []
        except Exception:
            entries = []
    if any(e.get("detail") == detail for e in entries):
        return
    entries.append({"ts": beijing_now().strftime("%m-%d %H:%M"), "kind": kind, "detail": detail})
    try:
        f.write_text(json.dumps({"entries": entries[-50:]}, ensure_ascii=False, indent=1))
    except Exception as e:
        print(f"[proactive] suppressed.json 写失败：{e}", flush=True)


# ---------------- 天气（确定性，不编造；与 bridge 同款 open-meteo） ----------------

_geo_cache = {}


def weather_precip_for(place: str, day, proxy: str):
    """返回 (降水概率 0-100 或 None, 原因串)。"""
    import requests
    px = {"http": None, "https": None} if not proxy else {"http": proxy, "https": proxy}
    if place not in _geo_cache:
        try:
            r = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                             params={"name": place, "count": 1, "language": "zh"},
                             proxies=px, timeout=8)
            hits = (r.json() or {}).get("results") or []
            _geo_cache[place] = (hits[0]["latitude"], hits[0]["longitude"],
                                 hits[0].get("name", place)) if hits else None
        except Exception as e:
            return None, f"地理编码查询失败：{type(e).__name__}"
    geo = _geo_cache[place]
    if geo is None:
        return None, "地点未匹配到坐标"
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": geo[0], "longitude": geo[1],
                                 "daily": "precipitation_probability_max",
                                 "timezone": "Asia/Shanghai"},
                         proxies=px, timeout=8)
        daily = (r.json() or {}).get("daily") or {}
        dates = daily.get("time") or []
        if day.isoformat() not in dates:
            return None, "预报窗口不含活动日（>16 天）"
        i = dates.index(day.isoformat())
        p = (daily.get("precipitation_probability_max") or [None] * len(dates))[i]
        if p is None:
            return None, "预报缺降水概率字段"
        return float(p), f"{geo[2]} {day.isoformat()}"
    except Exception as e:
        return None, f"天气查询失败：{type(e).__name__}"


OUTDOOR_HINTS = ("骑车", "骑行", "爬山", "徒步", "野餐", "露营", "跑步", "球", "公园", "湾", "山", "湖")


def is_outdoor(case):
    text = f"{case.get('activity', '')}{case.get('place', '')}{case.get('text', '')}"
    return any(h in text for h in OUTDOOR_HINTS)


# ---------------- 模型通路 ----------------

def kimi_direct_turn(prompt: str, key: str, timeout=90):
    """direct 模式：Kimi Coding Plan chat completions（OpenAI 兼容）。"""
    import requests
    r = requests.post(
        "https://api.kimi.com/coding/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "kimi-for-coding",
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 4000},
        proxies={"http": None, "https": None},
        timeout=timeout,
    )
    r.raise_for_status()
    msg = r.json()["choices"][0]["message"]
    return (msg.get("content") or ""), (msg.get("reasoning_content") or "")


class KernelRPC:
    """kernel 模式：octos serve --stdio JSON-RPC（与 qx-kernel-turn.py 同款协议）。"""

    def __init__(self, bin_path: str, data_dir: str):
        self.p = subprocess.Popen([bin_path, "serve", "--stdio", "--data-dir", data_dir],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.rid = 0
        self.events = []
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.p.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self.events.append(json.loads(line))
            except Exception:
                pass

    def call(self, method, params, timeout=90):
        self.rid += 1
        rid = f"r{self.rid}"
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": rid, "method": method,
                                       "params": params}) + "\n")
        self.p.stdin.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            for e in list(self.events):
                if e.get("id") == rid:
                    self.events.remove(e)
                    return e
            time.sleep(0.2)
        raise TimeoutError(method)

    def wait_reply(self, secs=120):
        deadline = time.time() + secs
        text = ""
        seen_at = None
        while time.time() < deadline:
            cur = ""
            for e in list(self.events):
                p = (e.get("params") or {}).get("payload") or {}
                if e.get("method") == "projection/envelope" and p.get("type") == "assistant_delta":
                    cur += p.get("data", {}).get("text", "")
            if cur and cur != text:
                text = cur
                seen_at = time.time() if "PLAN{" in text else None
            elif seen_at and time.time() - seen_at > 5:
                break
            time.sleep(0.4)
        return text

    def close(self):
        try:
            self.p.kill()
        except Exception:
            pass


# ---------------- 主动回合主流程 ----------------

def build_proactive_turn(case, day, precip, weather_why, new_day, new_part):
    """给管家的主动回合输入：让模型起草改期提案（用确定性推断的候选时段，
    模型只组装 PLAN，不允许发明其它值）。"""
    cid = case.get("id")
    act = case.get("activity") or "聚会"
    slot = f"{case.get('slot_day', '')}-{case.get('slot_part', '')}"
    place = case.get("place") or ""
    return (
        "你是「牵线」聚会守护管家。当前时刻触发了一次主动复核："
        f"守护 #{cid}「{act}」（原定 {slot} · {place or '地点未抽取到'}）明天开始，"
        f"open-meteo 预报当日降水概率 {precip:.0f}%（{weather_why}）——超过 60% 阈值。"
        "请起草一条改期提案：先用一句人话说明（天气原因+建议），然后另起一行输出单行"
        "机器提案，格式固定：PLAN{\"op\":\"reschedule\",\"id\":\"" + str(cid) + "\","
        f"\"slot_day\":\"{new_day}\",\"slot_part\":\"{new_part}\"}}。"
        "字段值全部双引号字符串，值内禁双引号与换行；不编造其它字段。"
        "说明文字 ≤80 字，含降水概率与数据来源（open-meteo）。"
    )


def pick_new_slot(case):
    """确定性候选：顺延一天同时段（目标日已解析 → 下一同名周几）。
    slot_day 词表顺延一周同一天（防编造——只能推「下一个同名词」）。"""
    day = case.get("slot_day", "")
    part = case.get("slot_part", "")
    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    if day not in days:
        day = "周六"
    if part not in ("上午", "中午", "下午", "晚上"):
        part = "上午"
    return day, part


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jail", required=True)
    ap.add_argument("--room", default="", help="Matrix 房间（可选；给了才发群消息）")
    ap.add_argument("--mode", choices=["direct", "kernel"], default="direct")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--proxy", default="")
    ap.add_argument("--kimi-key-file", default="/home/kikun/MyProject/Agentic-octos/.secrets/kimi-api-key")
    ap.add_argument("--octos-bin", default="/home/kikun/MyProject/Agentic-octos/repos/octos/target/release/octos")
    ap.add_argument("--data-dir", default="/tmp/qx-proactive-kernel-data")
    args = ap.parse_args()

    jail = pathlib.Path(args.jail)
    key = pathlib.Path(args.kimi_key_file).read_text().strip()
    kernel = None
    if args.mode == "kernel":
        # 内核 profile 指到 moonshot-coding（key 只进 env_vars，无 ambient 陷阱）
        os.makedirs(f"{args.data_dir}/profiles", exist_ok=True)
        now = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
        prof = {"id": "_main", "name": "proactive", "enabled": True,
                "created_at": now, "updated_at": now,
                "config": {"llm": {"primary": {"family_id": "moonshot-coding",
                                               "model_id": "kimi-for-coding",
                                               "route": {"api_key_env": "KIMI_CODING_API_KEY"}}},
                           "env_vars": {"KIMI_CODING_API_KEY": key}}}
        json.dump(prof, open(f"{args.data_dir}/profiles/_main.json", "w"), indent=2)
        kernel = KernelRPC(args.octos_bin, args.data_dir)
        kernel.call("session/open", {"session_id": "_main:cli:qx-proactive",
                                     "profile_id": "_main"})
        print("[proactive] kernel mode：session 已开（moonshot-coding/kimi-for-coding）", flush=True)

    matrix_client = None
    if args.room:
        from guardian.matrix import MatrixClient
        acc = json.loads(pathlib.Path("/home/kikun/MyProject/Agentic-octos/test-accounts.json").read_text())
        a = acc["accounts"][0]
        matrix_client = MatrixClient(acc["homeserver"], a["username"], a["password"])
        matrix_client.login()
        print(f"[proactive] matrix：已登录 {a['username']}，群消息将发到 {args.room}", flush=True)

    print(f"[proactive] 启动 jail={jail} mode={args.mode} interval={args.interval}s "
          f"weather={'proxy' if args.proxy else 'direct'}", flush=True)

    while True:
        state = load_state(jail)
        today = beijing_now().date()
        for case in load_cases(jail):
            cid = case.get("id")
            act = case.get("activity") or "聚会"
            day = resolve_target_date(case)
            if day is None or case.get("status") != "Confirmed":
                continue
            days_to = (day - today).days
            if days_to != 1:  # T-24h 到点
                continue
            slot = f"{case.get('slot_day', '')}-{case.get('slot_part', '')}"
            place = case.get("place") or ""
            mark = f"{cid}:{day.isoformat()}:proactive"

            # 已出过提案就不再重复决策（幂等）
            if mark in state:
                continue

            # ① 天气复核（确定性；不编造）
            precip, why = (None, "室内活动/未抽取到地点") if not place else weather_precip_for(place, day, args.proxy)
            outdoor = is_outdoor(case)
            if precip is None:
                record_suppressed(jail, "weather_unknown" if outdoor else "weather_ok",
                                  f"#{cid} {act}：天气未查到（{why}），不发起主动回合" if outdoor
                                  else f"#{cid} {act}：室内活动，跳过主动回合")
                state[mark] = beijing_now().isoformat()
                save_state(jail, state)
                continue
            if precip < 60:
                record_suppressed(jail, "weather_ok",
                                  f"#{cid} {act}：降水 {precip:.0f}%（{why}）<60%，不发起主动回合")
                state[mark] = beijing_now().isoformat()
                save_state(jail, state)
                continue

            # ② ≥60%：主动发起回合（模型起草改期提案；候选时段由确定性 pick 给出）
            new_day, new_part = pick_new_slot(case)
            prompt = build_proactive_turn(case, day, precip, why, new_day, new_part)
            reply = ""
            try:
                if args.mode == "kernel":
                    kernel.call("turn/start", {
                        "session_id": "_main:cli:qx-proactive",
                        "input": [{"kind": "text", "text": prompt}],
                        "turn_id": str(uuid.uuid4())})
                    reply = kernel.wait_reply()
                else:
                    reply, _reason = kimi_direct_turn(prompt, key)
            except Exception as e:
                record_suppressed(jail, "proactive_fail",
                                  f"#{cid} {act}：主动回合失败（{type(e).__name__}：{e}），提醒桥照常")
                state[mark] = beijing_now().isoformat()
                save_state(jail, state)
                continue

            if "PLAN{" not in reply:
                record_suppressed(jail, "proactive_fail",
                                  f"#{cid} {act}：模型未给出合规 PLAN（回复 {len(reply)} 字），不写入提案卡")
                state[mark] = beijing_now().isoformat()
                save_state(jail, state)
                continue

            # ③ 写 pending_plan.json（app 进聊天视图读入提案卡；幂等覆盖到拍板/放弃）
            pending = {"id": cid, "trigger": "proactive_weather",
                       "precip": precip, "weather": why, "day": new_day, "part": new_part,
                       "reply": reply, "at": beijing_now().isoformat()}
            if args.dry_run:
                print(f"[proactive][dry] #{cid} 将写提案卡：{reply[:90]}", flush=True)
            else:
                (jail / PENDING_PLAN_FILE).write_text(
                    json.dumps(pending, ensure_ascii=False, indent=1))
                # ④ 可选：发一条群消息提示（若给 --room）
                if matrix_client:
                    try:
                        matrix_client.send_message_with_retry(
                            args.room,
                            f"⛈ 牵线主动预警：#{cid} {act}（{slot} · {place or '地点未抽取到'}）"
                            f"明天降水概率 {precip:.0f}%（open-meteo·{why}）——"
                            f"已在 app 内备好改期提案（→ {new_day}-{new_part}），请打开牵线拍板。",
                            f"qx-proactive-{mark}", attempts=3)
                    except Exception as e:
                        print(f"[proactive] 群消息发送失败（不影响提案卡）：{e}", flush=True)
                print(f"[proactive] #{cid} 提案卡已写（降水 {precip:.0f}%）", flush=True)
            state[mark] = beijing_now().isoformat()
            save_state(jail, state)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
