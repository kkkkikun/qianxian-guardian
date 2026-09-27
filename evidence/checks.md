# 一页验收记录（状态：通过 / 未通过 / 未测）

| 检查项 | 实际动作和结果 | 证据 | 状态 |
|---|---|---|---|
| 意图与结果一致 | 群消息"周六骑车"→ Case → 提案 → 确认 → Confirmed | smoke_g4b 9/9 | 通过 |
| 数据来源、关键输入可核对 | 解析 JSON 与消息字段一致；天气未接（P1） | smoke_g4b「主链前半」 | 通过 |
| 一个真实操作改变正确状态 | 组织者"同意"→ Confirmed + plan Active | smoke_g4a「批准」 | 通过 |
| 等待与失败能被理解 | AwaitingConfirm/过期/拒绝各有界面语义；失败态 9 类 | blueprint 状态机 + smoke_g4a | 通过 |
| 这次改动没有破坏正常路径 | 全量回归 6 套冒烟全绿 | evidence/全量回归-20260927.txt | 通过 |
| 第二人可按说明复现 | run.md 全套命令；确定性冒烟不依赖外部服务 | run.md | 通过 |
| 权限拒绝场景有反馈 | B 确认 → confirm_denied；M3 无 grant → 拒发 | smoke_g4a/g4b | 通过 |
| 状态过期场景有反馈 | 提案过期 = min(+48h, start−1h)；Superseded 处理 | smoke_g4a「旧快照」 | 通过 |
| 注入场景有反馈 | 真实 LLM 注入 → 校验拦截 + 审计 | smoke_g5 + 真实通道实测 | 通过 |
| 崩溃恢复 | 子进程 sweep 补偿 + 事件持久化 | smoke_g5「独立子进程」 | 通过 |

（"通过"= 冒烟脚本断言 + 命令输出；详见 acceptance.md 证据表）
