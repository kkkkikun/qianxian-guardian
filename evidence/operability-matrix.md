# agent 可操性矩阵（WP2）：12 op × 五入口，逐格证据

> 冻结版本 v0.10.1。「✅」= 有实证链接；「◐」= 部分/协议层；「— 平台限制」= 如实标注的缺口。
> 回归复核：`python3 app/qianxian/tools/qx-verify-v2.py`（当前 36/36 全绿，含 R-35/R-36 内核 op 链）。

| op | UI 手动 | app 内管家 | 宿主 Ask 牵线 | 主动回合守护 | 群消息协议 |
|---|---|---|---|---|---|
| create | ✅ R-02（点卡建守护落盘断言） | ✅ R-26/27（提案卡拍板）+ R-35 内核链 | ◐ [s4 真宿主轮次](s4-real-host-20261010.md)（Rinx 面板=内核通道薄封装） | — 设计限制（主动回合只起草不执行，WP4 纪律） | ✅ [WP1](finals-wp1-agent2agent-20261013.md)（成员端自治建守护语义无——收敛仅 reschedule；建卡走组织端） |
| confirm | ✅ R-07（详情确认生效） | ✅ R-35 + s4 真模型 confirm 轮 | ◐ 同上 | — 同上 | — 协议不含 confirm |
| reschedule | ✅ 详情「改时间」（cycle_slot 落盘断言，v0.10.1 动作坞补位） | ✅ R-27（收敛提案拍板改期落盘） | ◐ s4 reschedule 轮 | ✅ [WP4 主动预警改期提案](v100-wp4-proactive-20261012.md)（天气复核） | ✅ [WP1 收敛改期全链](finals-wp1-agent2agent-20261013.md) |
| cancel | ✅ 两段式取消（R-13 清空链路同源） | ✅ R-35 | ◐ s4 | — 设计限制 | — 协议不含 |
| add_people | ✅ 详情「添加」（R-06 参与人行断言链） | ✅ R-35 | ◐ s4 | — | — |
| set_bill | ✅ 详情「记一笔」（R-18 待收尾徽章链） | ✅ R-35 | ◐ s4 | — | — |
| complete | ✅ 详情「标记完成」（R-20） | ✅ R-35 | ◐ s4 | — | — |
| draft_dunning | — 无 UI 按钮（管家/主动回合起草） | ✅ R-35 | ◐ s4 | ◐ [WP5 主动催收起草](v100-wp4-proactive-20261012.md)（梯度起草，人审后发） | — |
| mark_paid | ✅ 详情「记收款」（R-21 两笔收款闭环） | ✅ R-35 | ◐ s4 | — | — |
| undo | ✅ 取消后 5s 撤销窗（R-13 链） | ✅ R-35 | ◐ s4 | — | ✅ [WP1 改票幂等](finals-wp1-agent2agent-20261013.md)（同语义：latest-wins） |
| clear | ✅ 两段式清空（R-13） | ✅ R-35（mock 链）+ v100 真模型 clear 两段拍板 | ◐ s4 | — 永不主动（安全红线） | — |
| export | ✅ 说明卡「导出数据」+ 详情「导出证据」（R-22 离线校验） | ✅ R-35 | ◐ s4 | — | — |

## 结论（写进 README/提交 issue 的口径）

- **12/12 op 全部 agent 可表达**（R-35 真内核 × 剧本 mock 全绿；Kimi 真模型轮次证据在
  [v100-wp4](v100-wp4-proactive-20261012.md)）+ **全部 UI 可达**（回归 36/36 逐 op 落盘断言）。
- 宿主 Ask 牵线列：Rinx 面板=内核通道薄封装，s4 真宿主四轮实证；card-host 无该服务——
  如实标 ◐（平台限制），不冒充。
- 主动回合列：纪律性收窄——守护进程只起草不执行（拍板权在人），仅 reschedule/dunning
  两 op 有主动语义，其余标「设计限制」而非缺口。
- 群消息协议列（WP1 新增）：收敛改期全链双实例实证；成员端自治投票确定性规则。

## 复核入口

- R-35/R-36：`python3 tools/qx-dialog-chain.py`（缺省两链全跑，期望 `DIALOG-CHAIN ALL PASS`）
- 逐 op UI 链：`python3 app/qianxian/tools/qx-verify-v2.py`（期望 `PASS 36/36`）
- 真宿主面板侧：`evidence/s4-real-host-20261010.md` 内复现命令
- 双实例群消息链：`python3 tools/qx-wp1-e2e.py`（期望 `WP1-E2E ALL PASS`）
