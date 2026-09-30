# 牵线 · 聚会筹办守护（Agentic Event Case Guardian）

> **一条群消息，长成一个被照顾到收尾的完整活动。**
> 本作品是**活动生命周期守护**（Case 状态机），不是聊天增强——聊天只是意图的入口和结果的回执通道。

- **主场景**：日历（时间收敛、冲突检测、待定 vs 已确认）
- **联动**：即时消息 · Rinx（入口与回执）、天气（决策依据，Open-Meteo）
- **比赛**：GOSIM Agentic App 黑客松 2026

## 它做什么

群里一句"周六上午去深圳湾骑车，大概两小时？"之后：

```
群消息 → 规则分诊 → Octos 解析（严格 JSON）→ 防编造校验 → Case 诞生
  → 提案发回群里（M1，无需授权） → 组织者回复「同意」（仅组织者有效）
  → 执行：plans 历史（旧 Superseded / 新 Active）→ DB 读回断言 PASS
  → M2 回执回群 → 后续：改口重收敛 / T-24h 提醒 / AA 台账 → 账目清零归档
```

**四条最高法则**：
1. SQLite Case 状态是唯一事实源；Octos 会话只是一次性推理上下文
2. Agent 负责理解与规划（严格 JSON，无工具）；Guardian 负责确定性执行与验证
3. 一次状态迁移 = 一个可追踪事务（revision + proposal_id + event_id + txn_id + 审计）
4. 本地动作事务回滚；外部副作用 Outbox + txn 对账（不伪造成功）

失败不掩盖：agent 不可用→规则兜底、地点歧义→澄清卡、越权确认→拒绝、提案过期→作废、
重复确认→"已确认未重复"、外发失败→UNKNOWN 对账、注入尝试→拦截+审计。

## 快速开始

见 **[run.md](run.md)**（版本锁定、启动命令、双账号复现步骤）。
确定性冒烟（无需外部服务即可验证核心链路）：

```sh
cd app/guardian
python3 smoke_g4b.py   # 主链缝合 9/9
python3 smoke_g5.py    # 注入拦截 + 崩溃补偿 9/9
```

## 架构一览

```
Rinx（宿主，零修改）── 群聊（双账号 + bot）＋ 活动簿网页卡
        │ Matrix Client-Server API（bot sync）
Guardian（本仓库，OUP 客户端）
  ingress 幂等 → 分诊/关联 → 规则引擎 → octos serve（短会话）
  → 严格 JSON 校验 → 白名单动作 → 本地事务 / Outbox 对账
  → SQLite（唯一事实源：cases/plans/proposals/ledger/scheduled_tasks/case_events/outbox/audit）
```

完整设计（状态机、防编造校验链、消息三级权限、隐私三规则、四轮对抗评审记录）：
**[blueprint-gpt.md](blueprint-gpt.md)** v0.7.1。

## 目录

```
app/guardian/          guardian 守护进程（场外链路证明，G1–G5 冒烟证据）
  guardian/            核心模块（db/triage/dispatcher/cases/oup/outbox_sender/parser/activity_book）
  schema.sql           唯一事实源 schema
  smoke_g1..g5.py      六套确定性冒烟（70+ 断言）
app/qianxian/          script-app 主提交物（A 路线，hub check PASSED）
  bundle/              THE SUBMISSION（manifest/listing/main.splash/icon/截图）
  build/               hub scan review 包 + 7 问作答（gitignore，副本见 evidence/qianxian/）
app/miniapp-qianxian/  旧 Rinx spike（已归档，被 app/qianxian 取代）
evidence/              验收记录与全量回归留档（含 qianxian review 包副本）
PRIVACY.md             隐私政策（对齐 hosts 无网络 + 本机存储）
task.md                任务说明与验收条件
blueprint-gpt.md       设计蓝图（v0.7.1 冻结）
run.md                 复现步骤（含 script-app 复现节）
GOAL.md                执行总纲（内环任务书）
```

## 许可证

Apache License 2.0 — 见 [LICENSE](LICENSE)。
