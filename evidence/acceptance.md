# 验收记录（task.md 验收条件逐条执行）

执行时间：2026-09-27 深夜 ｜ 执行方式：确定性冒烟脚本 + 真实 LLM 通道 + 本地 Palpo
全量回归：`evidence/全量回归-20260927.txt`（7/7 + 19/19 + 10/10 + 9/9 + 9/9 + 9/9 全绿）

| # | 验收条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | 分诊命中全部关键消息、误报 ≤1 | ✅ 通过（误报 1/3） | smoke_g2.py 19/19；命中表随材料提交 |
| 2 | 确认后读回 Confirmed + 字段一致（代码断言） | ✅ 通过 | smoke_g4a.py「批准 → Confirmed」；cases.py `_readback` FAIL 回滚 |
| 3 | 仅组织者确认有效；B 确认 → confirm_denied | ✅ 通过 | smoke_g4a「越权批准被拒」+ smoke_g4b「越权确认拒绝」 |
| 4 | 被拒提案：保留历史 Rejected，不落 Active plan，Case 回 Proposing | ✅ 通过 | smoke_g4a「拒绝」断言（引用=0） |
| 5 | 改期后旧日期非 Active；Superseded=1/Active=1；无重复建 Case | ✅ 通过 | smoke_g4a「改期后 plans」 |
| 6 | bot 移出房间 → 停止处理 + 明示"守护已停" | 🟡 代码路径就绪（Dormant 转换）；真实验证需 GUI 双账号（待用户六步验证） | blueprint 状态机 + dispatcher 逻辑 |
| 7 | M3 外发可追溯 grant/audit/outbox/txn_id | ✅ 通过 | smoke_g4b「M3 once grant → 发送且消费」 |
| 8 | agent 断开 → 规则兜底明示降级 | ✅ 通过 | smoke_g4b parse_error 路径 + G3 runtime_unavailable 实测 |
| 9 | 注入用例被拦截并留审计 | ✅ 通过 | smoke_g5「分诊层/解析校验层」双拦截 + 真实 LLM 注入实测（ModelScope DeepSeek 拒答 → activity 空 → 校验拒绝） |
| 10 | 崩溃重启：任务补偿 + 事件不重复处理 | ✅ 通过 | smoke_g5「独立子进程 sweep」「processed_events 跨连接持久化」 |
| 11 | （P1）天气与 Open-Meteo 对账 | ⏸ 未实现（P1 明确划出） | — |
| 12 | 队外用户按 run.md 独立复现 | 🟡 run.md 已交付；**公开仓库结构已就绪**（git 仓库已 init 并提交 `91120c5`，含 LICENSE/.gitignore/README；凭据已 gitignore）；待用户 `gh repo create --public --source . --push` 后由队外用户执行 | run.md + 全量回归 |

## task.md 初赛清单对照

| 要求 | 状态 |
|---|---|
| 可运行的原型 + 启动说明 | ✅ guardian 全链可运行；run.md 启动说明 |
| 固定版本公开源码 + Apache 2.0 | 🟡 待用户推送公开仓库（代码就绪，LICENSE 待加） |
| 2-3 分钟演示视频 | ⏳ 待录（演示脚本 10 步在蓝图） |
| 两张关键截图 | ⏳ 待录（活动簿 Confirmed 页 + 失败态页） |
| 简短需求说明 | ✅ task.md |
| 数据来源与限制 | ✅ task.md 输入表 + run.md 限制节 |
| 至少一次操作 + 可核对结果 + 一个失败态 | ✅ 全链冒烟 + 注入/对账失败态 |
| 已报名成员名单 | 🟡 用户提交时锁定 |

## 结论

**P0-A（主链）/ P0-B（可信性）全部通过并有自动化证据；P0-C 独立复现：仓库结构就绪（本地 commit `91120c5`，Apache 2.0 LICENSE + .gitignore + README），待用户推送公开仓库后由队外用户执行。**
