# 「牵线」guardian（Python）：场外链路证明（A 路线）

> **定位（A 路线，2026-09-30 起）**：本目录是**场外证据**，不是提交物。
> 提交物是 `../qianxian/`（script-app，`bundle/main.splash`）。
> 本目录证明“同一套业务设计（分诊→提案→确认→活动簿）在真实 Matrix + 真实 LLM 通道上跑通过”，
> 与包内 Splash 的本地规则实现共享同一套状态机语义（Proposing/Confirmed/Cancelled），
> 但**不进 Hub 包**（gate 扩展名白名单无 `.py`）。

## 它证明了什么

- G1：schema 全量 + Matrix sync + 入站幂等 + 审计链（`smoke_g1.py` 7/7）。
- G2：分诊引擎 + 时间归一化 + 关联判定四分法（`smoke_g2.py` 19/19）+ 分发闭环（10/10）。
- G3：OUP 真链路 GO/NO-GO——真实模型回合（DeepSeek-V4-Flash，21 秒出
  `{"activity": "骑车", "date_text": "周六上午", "place": "深圳湾"}`）。
- G4a：状态机事务层（Proposal/organizer 校验/改期 Superseded/取消级联/读回断言，9/9）。
- G4b：主链缝合（M1/M2/M3 grant/Outbox 对账，9/9）。
- G5：注入双层拦截 + 真实 LLM 注入实测 + scheduler 崩溃补偿（9/9）。
- 全量回归：`../../evidence/全量回归-20260927.txt`（6 套全绿）。

## 与包内实现的关系

| 环节 | 包内（Splash，无 AI 可用） | 场外（本目录，有 AI 可用） |
|---|---|---|
| 分诊 | `triage()` 本地正则 | `guardian/triage.py` 规则引擎 |
| 解析 | `guess_activity/place()` 关键词呈现 | OUP 真实 LLM + 严格 JSON 校验 |
| 确认 | `confirm_case()` 组织者拍板 | `cases.py` organizer 校验 + revision |
| 持久化 | `cases.json`（storage） | SQLite 唯一事实源 + 审计 |
| 外发 | 无（`hosts: {}`） | Outbox + txn 对账（M1/M2/M3） |

## 运行（复现证据用）

```sh
pip install requests
cp config.example.json config.json   # 填 bot 账号（已 gitignore，不入库）
python3 -m guardian.main             # 常驻（本地 Palpo 127.0.0.1:8128）
python3 smoke_g4b.py                 # 主链 9/9
python3 smoke_g5.py                  # 注入+补偿 9/9
```

详见 `../../run.md`（版本锁定/双账号复现）与 `../../evidence/acceptance.md`（12 条验收）。
