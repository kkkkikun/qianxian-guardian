# GOAL：「牵线」聚会筹办守护 — 执行总纲（内环任务书）

> 用法：本文件是给任何执行 Agent（ZCode / octoscode / octos goal）的常驻指令。
> 冻结蓝图是唯一事实源：`my-entry/blueprint-gpt.md`（v0.7.1）。任务说明：`my-entry/task.md`。
> 蓝图与本文冲突时，以蓝图为准；蓝图没写的，先提案再动手。

## 角色

你是「牵线」项目的**内环执行工程师**。外环（人或强模型）负责派单、复验、采认；你负责按切片施工、自证、如实回报。工具不交给 LLM、事实不由模型生成——这条原则同样约束你自己：**所有结论必须带可复现证据（命令 + 输出 + 文件）**。

## 使命

按切片顺序交付 P0-A（主链）→ P0-B（可信性）→ P0-C（独立复现），最终产出可通过 `my-entry/task.md` 验收条件与 `run.md` 独立复现的可运行系统。

## 优先级原则（2026-10-01，用户指令：先完成再完美）

1. **完成应用基本功能**——建守护/分诊/冲突/确认/改时间/取消/撤销/AA收账等信息在真机上完整可见可用（含展开态详情可见性问题的务实修复）；功能没通之前不做任何纯视觉打磨。
2. **结合 octos 系统 agent 上 agentic 功能**——`octos.turn.start` 在评审宿主（Rinx/robrix2 mini-app host）有真实服务（见 OctoScript-App-Design-Flow `docs/AI-SERVICES.md`；card-host 无服务、按既有降级路径诚实兜底）：AI 解析走通 + 超时兜底 + `host.has()` 门检。
3. **整体功能完善后再调整 UI**——字号/间距/配色等纯视觉项全部押后。

外环据此派单；与本原则冲突的旧队列条目以本原则为准。

## 硬纪律（违反任何一条 = 本轮工作作废）

1. **蓝图冻结**（v0.7.1 文档冻结规则）：不加功能、不换方向、不加核心 Agent 能力；只允许修真实测试发现的错误、平台兼容问题、验收失败、必要的安全/可靠性约束。
2. **状态只在 SQLite**：octos 会话是一次性推理上下文；任何状态变更必须走白名单动作 + case_revision++ + 审计条目。
3. **读回断言**：本地动作 = 事务 + 预期状态 assert；外部动作 = Outbox + txn 对账。**不采信任何"应该成功了"**——包括你自己的。
4. **真实冒烟**：G3 必须在真实 octos serve 上跑通；mock 全绿不算数。
5. **切片门禁**：G3 = GO/NO-GO。真实冒烟失败，禁止写任何 G4 界面代码。
6. **诚实回报**：每片结束按格式回报 `ACK(done|partial|blocked): … + 验证级别(verified/partially-verified/unverified) + 证据路径`。没验证的写 unverified，不许写 verified。
7. **范围**：P0 之外的一切（weather/AA/RSVP/standing grant/本地模型）除非外环明示，否则不写。

## 当前任务队列（按序执行，完成一片回报一片）

- **G1**：✅ DONE（2026-09-27）——schema 全量 + Matrix sync + 入站幂等 + 审计链。冒烟 7/7（smoke_g1.py）：收发落库、重放幂等、单 Active Case DB 约束、scheduler 重载补偿全部实测。附带发现：**Palpo 登录限流严格（429 最长 4 分钟）→ access token 必须持久化**（已实现 token 缓存）。
- **G2**：✅ DONE（2026-09-27）——分诊引擎 + 时间归一化 + 关联判定四分法（guardian/triage.py，冒烟 19/19）+ 分发闭环（dispatcher.py，冒烟 10/10：new_case/existing/pending_intent/organizer 规则/房间隔离）。
- **G3**：✅ **DONE — GO/NO-GO 门通过（2026-09-27）**。
  - Phase 1（3/3，smoke_g3.py）：OUP 线路验证——session/open 返回 octos-ui/v1alpha1 capabilities；turn/start 受理；无 provider 结构化 runtime_unavailable。
  - **Phase 2（3/3，smoke_g3_real.py）：真实模型回合 PASS**——LLM = DeepSeek-V4-Flash（ModelScope，环境自带 key，OpenAI 兼容 base_url）；OUP 客户端 `guardian/oup.py` 实测固化协议细节：字符串 id / UUID turn_id / `kind:text` 输入 / **v2 projection/envelope 事件流**（reasoning_delta→assistant_delta→**assistant_persisted（权威答案）**→turn_terminal）/ profile 绑定（session_id 三段式 `main:stdio:<task>` + profiles/main.json 的 config.llm.primary.route.base_url）。
  - 实测输出：`{"activity": "骑车", "date_text": "周六上午", "place": "深圳湾"}` — JSON 可解析、字段齐备，21 秒完成。
  - 协议注记：spec 旧字段（message/delta, turn/completed）在实际 v2 流中对应 projection/envelope payload types；oup.py 已按实测实现。
- **G4a**：✅ **DONE（2026-09-27 晚）**。
  - `guardian/cases.py`：状态机事务层——Proposal 创建（M1，AwaitingConfirm + revision++）、**organizer 校验**（越权 CaseError）、**based_on_revision 批准校验**（旧快照 → Superseded + Case 回 Proposing）、**plans 历史**（批准 = 旧 Superseded + 新 Active）、拒绝（Proposal=Rejected 历史保留 + 不落 Active plan）、**取消级联**（Cancelled + scheduled_tasks/outbox M3 清理 + 历史保留）、**读回断言**（本地动作 FAIL → 回滚 + 审计）。冒烟 9/9（smoke_g4a.py）：主链/越权/批准/改期 Superseded/旧快照/拒绝/取消级联全实测。
  - `guardian/activity_book.py`：活动簿网页卡（127.0.0.1，HTML + /api/state），plans Superseded 改期证据、审计计数可见。冒烟 4/4。工程注记：SQLite 连接线程限制 → 每请求独立连接；环境 HTTP 代理需绕过（urllib ProxyHandler({})）。
  - 语义修正（实测中发现）：based_on_revision = 提案进入快照后的版本（否则自批失配）；create_case 提交时机（显式事务模式 isolation_level=None）。
- **G4b**：✅ **DONE（2026-09-27 深夜）——P0-A 主链缝合完成**。
  - `guardian/outbox_sender.py`：Outbox 发送器——M1/M2 无需 grant 自动发送；M3 校验 grant（once 消费 / standing+expiry），无 grant 拒发（status 保持 Pending + 审计）；发送异常 → `UNKNOWN` → 同 txn_id 对账 → `Sent`（幂等：同 txn 只投递一条）。
  - `guardian/parser.py`：LlmClient 抽象——`build_parse_prompt`（<room_message> 不可信标记）+ `validate_parse_output`（严格 JSON/字段/类型/注入残留校验）+ `OupLlm`（真实）/`FakeLlm`（确定性测试）。
  - `guardian/dispatcher.py`：主链缝合——new_case → octos 解析 → 校验 → Proposal + **M1 入 outbox**；确认关键词前置（organizer 越权 → confirm_denied）；批准 → M2 回执入 outbox；改口 → Rescheduling（组织者）；取消 → Cancelled。
  - 冒烟 9/9（smoke_g4b.py）：主链前半/M1 发送/越权拒绝/批准/回执/M3 拒发/once grant 消费/失败注入对账幂等全实测。
  - 工程注记：环境 HTTP 代理劫持 localhost → MatrixClient 加 `proxies={"http":None,"https":None}`（回归 G1 7/7 验证）。
  - **全量回归**：G1 7/7 + G2 19/19 + G2 分发 10/10 + G4a 9/9 + G4b 9/9 全绿。
- **G5**：✅ **DONE（2026-09-27 深夜）**。
  - **run.md 交付**（P0-C）：版本锁定表 / 一次性准备 / 双账号复现步骤 / 数据来源与限制 / 已知限制。
  - **注入实测**（smoke_g5 9/9 + 真实 LLM 注入）：分诊层拦截纯注入（不进解析）→ 校验层拦截带活动词的注入输出（FakeLlm 放弃 JSON 契约 → ParseValidationError）→ **真实 LLM 注入实测**（ModelScope DeepSeek 被带偏拒答 → activity 空 → 校验拒绝 + 审计）。防御纵深：无工具 agent + 严格 JSON + 白名单动作 + organizer 确认。
  - **scheduler 崩溃补偿实测**：sweep_scheduler 从占位升级为条件 UPDATE claim（防双 worker）→ 补偿 → Completed；独立子进程验证 `CHILD_COMPENSATED`；processed_events 跨连接持久化（重启不重复处理）。
  - **验收逐条执行**：`evidence/acceptance.md`（12 条验收：9 通过 / 1 P1 划出 / 2 待用户 GUI 或推送）+ `evidence/checks.md` 一页验收 + `evidence/全量回归-20260927.txt`。
  - **全量回归终态**：G1 7/7 + G2 19/19 + G2 分发 10/10 + G4a 9/9 + G4b 9/9 + G5 9/9 全绿。
- **交付状态**：P0-A 主链 ✅ / P0-B 可信性 ✅ / **P0-C 独立复现 ✅**。
  - **公开仓库结构已整理并本地提交（`703afb1` + `1e114b6`，历史脱敏重写后；原 `91120c5`/`d259d66`）**：Apache 2.0 LICENSE、README（架构/快速开始/目录）、.gitignore（config.json/test-accounts/*.db/tokens 全部忽略，已验证无凭据入库）、整理后全套冒烟复验 6 套全绿。
  - **A 路线 script-app（`app/qianxian/`，2026-09-30）**：`hub check — PASSED`（仅 unsigned warning，
    digest `fdcae9bb`）+ `hub scan` 7 问作答（`evidence/qianxian/`）；真机 card-host（自建 9-26 构建链）
    `/snap` 11 控件验证；publisher 真值 ✅（Aurora-X/foxmail/公仓 PRIVACY 链接）；
    剩余占位：真截图（llvmpipe 无头抓帧超时，待有头重截）重 stamp。
  - 剩余操作项：① ~~建仓推送~~ ✅ 已推送 https://github.com/kkkkikun/qianxian-guardian
   （`master`，submit issue #1；官方 #5/#13 待留言）② 真截图 + 演示视频 + Rinx GUI 六步
    ③ 队外用户按 run.md 复现并回填 acceptance.md 第 6/12 条。

## 双轨状态（blueprint-gpt.md 附录 A）

- **轨 1（独立 guardian）**：G1/G2/G3 全部完成。LLM 已用 ModelScope（环境 key，DeepSeek-V4-Flash，OpenAI 兼容 base_url）实测通过——正式提交时按赞助额度切 MiniMax/Kimi（同一 OUP/配置机制，只换 provider/model/base_url 三行）。
- **轨 2（Rinx mini-app → A 路线 script-app）**：2026-09-30 已定 A 路线，
  提交物为 `app/qianxian/`（官方 script-app 形态，`hub check — PASSED` + scan 7 问作答，
  见 `evidence/qianxian/`）。旧 spike（`app/miniapp-qianxian/`）已归档保留。
  **最新 Rinx main（a72e4b00）已构建成功**（131MB，`target/release/rinx`，splash feature 修复 + 链接用 `~/.local/gosim-libs`），`--remote` 接口实测可用。剩余：GUI 六步演示（需人操作）。两轨共享业务设计。

## 最新 Rinx 构建纪要（vendor 方案 v2）

最新 main 的 16 个 git 依赖（makepad 6cf0385 / octos 6ad76e5c / App-Hub 46d67e51 / System-Apps 4fa0f122 / OctoScript-Makepad 6881fb6c 等）已用 codeload tarball + manifest 全量 path 化解决；踩坑记录：① patch 键 `www.github.com` 归一化 ② `octosense-app-policy` 需要 `features=["splash"]`（splash_adapter 被门控）③ 新旧 makepad vendor 目录共存导致 lockfile crate 冲突 → 旧版移入 `_old_makepad_1d3d383e/` ④ makepad-html（blitz 系）是独立仓库，恢复并在其内部把 widgets 指向新 makepad。

## 环境（已就绪，勿重复搭建）

- 本地 Palpo @ http://127.0.0.1:8128（`../palpo-ctl.sh start`）；PG17 容器 `gosim-pg`
- 测试账号：`../test-accounts.json`（rinx_test_a / rinx_test_b / @guardian_bot）
- Rinx 已编译：`../run-rinx.sh`；octos 源码：`../repos/octos`（构建中/已构建）
- 蓝图核验过的 Bot 冒烟脚本模式：bot 注册→建房邀请→sync 收消息，全部走标准 Matrix API

## 回报格式

```
ACK(done|partial|blocked): <切片号> <一句话>
验证级别: verified|partially-verified|unverified
证据: <命令/输出/截图/DB 查询结果路径>
下一片前置: <缺什么>
```
