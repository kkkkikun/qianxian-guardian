# PLAN ops 覆盖矩阵（v0.9.0 · WP1）

> 目标：把「100% agent 可操」变成评审可自行核对的证据——遍历 `bundle/main.splash` 的
> **每一个状态变更入口**，标注手动 UI 路径、对应 PLAN op、白名单前置校验、危险级、
> 撤销窗、回归编号与真机证据。**任何一行 PLAN op 列为空即为缺口**；纯 UI 偏好行必须写明理由。

## 一、状态变更函数全覆盖表

| 函数 | 手动入口 | PLAN op | 参数 schema | 前置校验（白名单） | 危险级 | 撤销窗 | 回归 | 真机证据 |
|---|---|---|---|---|---|---|---|---|
| create_case_from_plan | 管家提案→拍板 | `create` | {text*, activity, slot_day, slot_part, place, people, bill_total} | text 非空（溯源）且活动/时间/地点至少一非空；槽位词表归一 | 低 | 可 cancel | R-15/R-24 | [v080 五](../evidence/v080-features-20261012.md) |
| add_case / build_case_from_text | 「建守护」按钮 | `create`（同上，本地规则为无 AI 兜底路径） | 同上 | 同上 | 低 | 可 cancel | R-02/R-14 | 回归台账 |
| confirm_case | 详情·「确认这条守护」 | `confirm` | {id*} | id 存在且状态=Proposing；重复确认幂等提示 | 低 | — | R-07 | 回归台账 |
| set_slot / cycle_slot / reschedule_case | 详情·「重新收敛」/低频「改时间」 | `reschedule` | {id*, slot_day, slot_part} | id 存在；词表归一（norm_day/norm_part 拒词表外值）；冲突全量重算；提案卡带冲突预演 | 低 | 可再改期 | R-19 轮（diff 卡） | [v080 五：ROUND2 diff 卡](../evidence/v080-features-20261012.md) |
| cancel_case | 详情·「取消守护」（两段式） | `cancel` | {id*} | id 存在非 Cancelled；两段式（确认取消 5s） | 中 | 5s undo 窗 | R-13（两段式） | 回归台账 |
| undo_cancel | 「撤销」按钮（取消后 5s 内） | `undo` | {id*} | 目标=刚取消那条（cancelled_last_id）且窗内；**窗口外提案被拒** | 中 | — | Rinx e2e（v0.9.0） | [v090-features](v090-features-20261012.md) |
| add_person | 详情·参与人行「添加」 | `add_people` | {id*, people*} | people 非空；重建数组保留 slot_init_asked（#38） | 低 | — | R-06/E-01 | 回归台账 |
| update_bill_total | 详情·「记一笔」 | `set_bill` | {id*, bill_total*} | 金额 >0 | 低 | — | R-18/R-21 | 回归台账 |
| add_payment | 详情·「记收款」 | `mark_paid` | {id*, who*, amount*} | who 在参与人名单、amount>0；按分取整对账重算；收齐自动清待收尾 | 低 | — | R-21/R-24 + Rinx e2e | [v090](v090-features-20261012.md) |
| set_completed | 详情·「标记完成」 | `complete` | {id*} | 目标为 Confirmed | 低 | — | R-20 | 回归台账 |
| set_bill_cleared | 详情·「AA 已收齐」 | 覆盖路径=`mark_paid` 收齐自动清零；本按钮为**人工兜底**（derived 字段强制覆盖） | — | 幂等 | 低 | 可再记收款翻回 | R-18 | 回归台账 |
| clear_all_data | 低频·「清空全部」（两段式） | `clear` | {}（无 id，全量） | 空表拒；**两段拍板**（第一次确认 5s 内第二次执行；过期如实重挂） | **高** | 不可 | R-13 + Rinx e2e | [v090](v090-features-20261012.md) |
| export_data | 低频·「导出数据」 | `export`（不带 id） | {} | 只读导出，不改状态 | 低 | — | Rinx e2e | [v090](v090-features-20261012.md) |
| export_evidence | 详情·「导出证据」 | `export`（带 id） | {id} | id 存在；确定性断言随包 | 低 | — | R-22 | 回归台账 |
| draft_dunning（拍板执行） | 管家提案→拍板 | `draft_dunning` | {id*} | 有账未清；**金额/差额由 app 计算**，模型零参与 | 低 | — | v0.6.0 台账 | [v040 S6](v040-features-20261011.md) |
| post_confirm_actions（ICS+群分享+日历写） | confirm 的派生动作 | 随 `confirm` 链自动执行（无独立 op——派生副作用，不是独立意图） | — | ICS 纯本地；matrix/device_calendar 按能力门检+诚实降级 | 低 | — | R-17/R-19 | [v040/v080](v080-features-20261012.md) |
| mark_conflicts / rebuild_selected_ledger（bill_cleared 自动推导） | 派生重算 | 无 op（**确定性推导**，非用户意图——数字由代码算，agent 与人都不直接改） | — | 全量重算幂等 | — | — | R-04/R-21 | 回归台账 |
| calendar_write_case | confirm 派生（device_calendar） | 同 post_confirm_actions 行 | — | 日期未解析不写；每步真实错误透出 | 低 | — | v0.8.0 台账 | [v080 一](v080-features-20261012.md) |

## 二、纯 UI / 偏好类（不改状态机，无 op 的理由）

| 函数 | 入口 | 理由 |
|---|---|---|
| toggle_case / toggle_howto / set_filter / set_query | 卡片展开、说明卡、筛选、搜索 | 纯视图态，不落盘、不影响 cases |
| set_receipt_style | 「风格」按钮 | 个人偏好（pref.json），与守护状态无关 |
| enter_chat / back_from_chat / back_to_list / on_tap_card | 视图切换 | 导航 |
| save / load / rebuild_lines / write_agent_brief | 基础设施 | 持久化与扁平化，非用户意图 |
| butler_decline 家族 | 提案卡「放弃」+理由 chips | 拒绝路径（反馈注入下轮 turn），本身不变更状态 |
| load_suppressed | 进聊天视图 | 只读回看 |
| undo_cancel 窗口外的重复调用 | — | 内置守卫提示，无副作用 |

## 三、否定用例（非法提案必拒——白名单闸门的证据）

| 场景 | 结果 | 证据 |
|---|---|---|
| reschedule 缺 id（真模型两次） | 「目标 # 不存在——拒绝执行」 | [v080 五](v080-features-20261012.md) |
| mark_paid who 不在名单 | 「X 不在 #N 的参与人名单——拒绝执行」 | [v090](v090-features-20261012.md) |
| mark_paid amount ≤ 0 | 「金额要大于 0——拒绝执行」 | [v090](v090-features-20261012.md) |
| undo 窗口外 | 「撤销窗口已过——拒绝执行」 | [v090](v090-features-20261012.md) |
| create 缺原文 | 「提案缺消息原文——拒绝执行」 | 回归/代码路径 |
| 槽位词表外值 | norm_day/norm_part 清空→后续校验拒 | R-19 代码路径 |

> 维护纪律：新增任何状态变更函数时必须同步本表；PLAN op 列**空格即缺口**。
