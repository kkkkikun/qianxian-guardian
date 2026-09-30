# 提交形态选型决策（2026-10-01 补记）

> 评审常问「为什么不是网页小程序 / 原生宿主扩展 / Hub 卡片包」。
> 本表把四条官方形态逐一对照，给出**选择与理由**，均有依据可核。
> 依据来源：官方 `docs/app-hub-submission.md`（四形态并列）、官方 Design-Flow 中文 README
> （9-27 状态页）、`hub check` 实际结果、`gh api` 核实记录。

## 官方四条形态与我们的选择

| 形态 | 官方要求 | 我们的评估 | 结论 |
|---|---|---|---|
| **Hub 卡片包 / script-app** | manifest + listing + 入口文件 + 真实截图；`hub check` 通过 | ✅ **选它**。纯解释执行（`main.splash`），无编译产物；`hub check — PASSED`；评审可用 `hub` 独立核验；商店隐私/权限行由 manifest 自动派生，符合我们"最小权限、不联网"的定位 | **采用** |
| 网页小程序（URL 卡片） | 可运行页面 + URL 卡片 + 部署说明 | ⚠️ 可行但更弱：无法在 App Hub 生态内被安装与授权；无 manifest 权限模型（隐私声明靠自己写）；`hosts`/存储配额无平台强制 | 未选 |
| 原生宿主扩展（Rinx） | 含扩展的可构建宿主 + 提交号 + 运行说明 | ❌ **本轮不可行**：需改 Rinx 源码并重编 131MB 二进制；课堂包锁定的宿主基线（`05daf9b`）不含 host-services broker；改动越大越难在评审窗口复现 | 未选（另见下「A 路线其实是此路不通后的最优」） |
| OctoSense ROM 扩展 | 系统改动 + 构建安装 + 前后对照 | ❌ 与初赛"可运行作品"定位不符（需刷 ROM），周期不匹配 | 未选 |

## 为什么落到 script-app（A 路线）

一条硬事实决定了方向：**官方 Design-Flow 中文 README（9-27 状态页）写明**——
商店 script-app 在 card-host 与各 OctoSense Shell 中调用 `octos.*` / `model` 会返回
`no service answers`（AI 相关宿主服务目前只有 Rinx mini-app host 提供）。

因此：

1. **不能把"AI 自动理解群消息"作为提交物卖点**——那条路在商店形态下运行时不可用；
2. 我们选择**把 AI 降为可选增强**（`octos.turn.start` 仅在宿主提供时出现，
   否则明确降级），核心链路（分诊 / 时间槽 / 冲突 / 状态机 / 回执）全部**确定性本地实现**；
3. 这与"最佳 Agentic 评价任务自动化与可靠性"的评分并不冲突——我们自动化的是
   **可核验的确定性流程**，每一步都有读回断言，而不是"AI 可能会做对"。

## 保留的场外证明（Python guardian）

同一套业务设计在 `app/guardian/` 有 Python 实现，跑通真实 Matrix + 真实 LLM 通道
（G1–G5 六套冒烟 70+ 断言全绿，含真实注入拦截与崩溃补偿）。
它**不进提交包**（Hub 门禁扩展名白名单无 `.py`），但作为**同一设计的另一形态证据**保留，
供评审对照"这套 Case 状态机在真实群里也跑得通"。

## 复现要点

- 提交物门禁：`hub check my-entry/app/qianxian/bundle --allow-unsigned` → `PASSED`
- 门禁 7 问作答：`evidence/qianxian/review-answers.md`
- 场外冒烟：`cd my-entry/app/guardian && python3 smoke_g4b.py`（9/9）、`smoke_g5.py`（9/9）
