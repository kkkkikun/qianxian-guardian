# 牵线 · 聚会筹办守护（qianxian）

> 📄 **一分钟读懂这个作品** → [evidence/one-pager.md](evidence/one-pager.md)
> （做了什么 / 为什么这么设计 / 怎么核验 / 怎么跑 / 已知边界，一页纸）

> **一条群消息，长成一个被照顾到收尾的完整活动。**
> 本作品是**活动生命周期守护**（Case 状态机），不是聊天增强——聊天只是意图的入口和结果的回执通道。

- **决赛迭代（v0.3.0 管家模式）**：**agent 驱动全流程，人只做最终拍板**——
  粘贴群消息点「交给管家」→ agent 分诊/查冲突/出 **PLAN 机器提案** → 提案卡上点「拍板」→
  白名单动作执行 + 回执。**Rinx 真宿主 × MiniMax-M3 真模型端到端实测**：
  create/reschedule/confirm 全链落盘，真模型主动预警「与 #1 撞时段」（[evidence/s4-real-host-20261010.md](evidence/s4-real-host-20261010.md)）
- **v0.4.0 出行保障扩展**：**天气**（管家回合内真调内核 get_forecast 工具，诚实拒绝编造）/
  **日历**（确认即生成标准 ICS 可导入任意日历；官方 device_calendar 通路按平台边界记档）/
  **状态全生命周期**（待拍板→已确认→已完成 + AA 待收尾徽章）/ **主动提醒**（确认即登记
  T-24h，伴生守护进程经 Matrix 真投递）/ **分享到群**（Rinx 宿主真发群消息）
  （[evidence/v040-features-20261011.md](evidence/v040-features-20261011.md)）
- **主场景**：日历（时间收敛、**冲突检测**、待定 vs 已确认）
  → 与官方「日历」场景四步演示的逐条对齐见
  **[evidence/official-scenario-alignment.md](evidence/official-scenario-alignment.md)**
- **提交形态**：OctoSense **script-app**（仓库根 `bundle/`，v**0.3.0**，`hub check — PASSED`，contract 1.10.0，agent read-only 最小权限 + AGENT.md v3）
- **比赛**：GOSIM Agentic App 黑客松 2026（队伍 Aurora-X）；初赛入围（73/100）
- 🎥 **演示视频**：70 秒（agent 主线）→ [evidence/finals-demo-v3.mp4](evidence/finals-demo-v3.mp4) 或 [Release v0.5.0 资产](https://github.com/kkkkikun/qianxian-guardian/releases/tag/v0.5.0)

## 界面预览

| 主界面（管家 CTA + 筛选） | 详情与确认回执 | 冲突警示（失败态明示） |
|---|---|---|
| ![主界面](bundle/screenshots/01-main.png) | ![详情](bundle/screenshots/02-expanded.png) | ![冲突](bundle/screenshots/03-conflict.png) |

> 来源标注（诚实）：本开发机 WSLg 会话无头（`/g` 抓帧超时），截图与视频帧为
> `tools/snap-to-png.py` / Rinx 帧渲染器按**运行时真实控件树**重绘（文字/层级/坐标/
> 状态色来自实际运行，v0.1.0 同款先例）。**真模型提案卡与拍板后的实况帧**见
> `evidence/shots-v3/s6-realmodel-proposal.png` / `s7-after-approve.png`；评审可用
> `tools/octo shot` 复核。

## 它做什么

群里一句「周六上午去深圳湾骑车，大概两小时？」之后：

```
粘贴群消息 → 规则分诊（时间词 × 聚会/约定语气）→ 守护诞生（待拍板）
  → 抽时间槽（周六-上午）→ 抽活动/地点（骑车/深圳湾，抽不到就留空，绝不编造）
  → 冲突检测：同日同时段已有安排？→ 提示列出双方，让人裁决
  → 参与人：报名的人记在这里（逗号分隔、上限 10 人；抽不到就写「未填写」，不编造）
  → 组织者点「确认这条守护」→ Confirmed，回执草稿四行就位
  → 改时间：5 个常见时段轮换（周六-上午→下午→晚上→周日-上午→下午），**改完自动重算冲突**
  → 改口回 Proposing（回执刷新）· 取消两段式确认 + 5 秒撤销
```

**守护多了也不乱**：顶部有**搜索框**（按活动/地点/原文实时过滤）与**四标签筛选**
（全部 / 待拍板 / 已确认 / 已取消），带「共 N / M 条」计数，两者可叠加。

**四条最高法则**：

1. **不编造**：抽不到的时间/活动/地点一律留空显示「未抽取到」，不猜、不填。
2. **用户始终主动**：分诊不确定时给澄清卡 +「仍然建守护」入口，不替用户做决定。
3. **危险操作留退路**：取消/清空是两段式确认，且 5 秒内可撤销。
4. **矛盾交人裁决**：检测到同时段冲突只提示不自作主张；改一个时段即可自动解冲突。
5. **数据在用户手里**：可导出（屏显 JSON 供复制）、可一键清空、损坏自动备份。

失败不掩盖：无 AI 服务→明确降级继续可用 · 分诊未命中→澄清卡说明原因 ·
损坏数据→备份后重启不丢 · 重复确认→「已确认，未重复」。

## 管家模式（决赛 v0.3.0）：AI 接管全流程，用户只拍板

「交给管家」是主入口（朱砂主按钮）。管家 = 底层 **octos agent**（`octos.turn.start` 真回合，
app 把角色提示词与当前守护快照嵌入 turn 文本——不依赖宿主注入 AGENT.md）：

```
群消息 → 交给管家 → agent 抽字段+查冲突 → 回复尾部输出单行机器提案：
  PLAN{"op":"create","text":"原文","activity":"骑车","slot_day":"周六","slot_part":"上午","place":"深圳湾",...}
→ app 解析进提案卡（槽位词表归一，编造的时间进不了状态机）
→ 人点「拍板执行」→ 白名单动作（建/确认/改期/取消/加人/记账，全部复用既有函数）
→ sys 回执 + 撤销窗口照常；agent 绝不声称已改状态
```

- **ops**：`create / confirm / reschedule / cancel / add_people / set_bill`——app 的全部状态变更操作都可由 agent 提案驱动。
- **合法性前置校验**：create 必须带消息原文（溯源）、目标 id 必须存在、改期/加人必须有值——非法提案拍板即拒并给拒绝文案。
- **双处一致**：`bundle/AGENT.md` v3（官方四段式）与 app 内提示词同文；agent 工具最小权限（read-only + `ask_user_question`）。
- **真宿主真模型实证**：Rinx（Mini apps 宿主）内四轮端到端——mock create/reschedule +
  **MiniMax-M3 真模型 create/confirm**，全部「PLAN 提案→人拍板→cases.json 落盘断言」；
  真模型跨轮读取守护快照做冲突预警。另有内核直连双证（mock + 真模型）→ `tools/qx-kernel-turn.py`。

## 无 AI 也完整可用

本应用**不依赖任何模型服务**：分诊、时间槽抽取、冲突检测、状态机全部是确定性规则。
无 AI 宿主时点「交给管家」**明确降级**（sys 气泡明示原因），本地规则路径（「建守护」）完整可用；
屏上有常驻能力可见性行，如实显示「可用 / 实测无响应 / 本机无服务」。

## 怎么审这个作品（三条路，从零门槛到完整复现）

**① 零门槛：直接读源码**（不需要任何构建）
本应用是纯解释执行的脚本，核心逻辑都在一个文件里：
`bundle/main.splash`（约 2800 行，Splash/OctoScript 方言；函数名即语义：butler_send / plan_parse / butler_approve / confirm_case / set_slot / rebuild_lines …）。
配套阅读：[evidence/v040-features-20261011.md](evidence/v040-features-20261011.md)（v0.4.0 特性验证）、
[app/qianxian/tools/qx-verify-v2.py](app/qianxian/tools/qx-verify-v2.py)（**20 项真机回归**，`QX_PORT=8160 python3 …` 一键跑）、
[evidence/s4-real-host-20261010.md](evidence/s4-real-host-20261010.md)（Rinx 真宿主×真模型端到端证据）。

**② 门禁核验**（需要上游 `hub` 工具；约 5 分钟）
> 注意：`OctoSense-App-Hub` 把 makepad / Octoscript patch 到**兄弟路径**，
> 只 clone 它一个仓**编不出来**（实测报 `failed to read ../makepad/…/Cargo.toml`）。
> 用官方的一键脚本把兄弟仓拉齐：
```sh
git clone https://github.com/OctoSense-org/OctoScript-App-Design-Flow.git
cd OctoScript-App-Design-Flow && python3 tools/setup-native.py   # 拉齐 makepad/octoscript/octoscript-makepad
cd ../OctoSense-App-Hub
cargo build --release -p octosense-app-hub --bin hub
./target/release/hub check <你的-clone>/my-entry/bundle --allow-unsigned
# 期望：qianxian 0.1.0 — PASSED（仅 unsigned warning）
```

**③ 完整复现**（需 card-host 运行时；见 [run.md](run.md)）
```sh
cd my-entry/app/qianxian
export OCTOSENSE_APP_HUB=../../../.build-hub-926/OctoSense-App-Hub   # 或按 run.md B 段自建
python3 ../../../octosense-ws/OctoScript-App-Design-Flow/tools/octo run bundle --port 8141
```

- **怎么用**：见 **[evidence/demo-script.md](evidence/demo-script.md)**（21 步三线：主线 / 冲突检测 / 危险操作与数据控制；每步输入都经真机验证）。
- **复现与版本锁定**：见 **[run.md](run.md)**。
- **门检**：`python3 $OCTO check bundle` → 目标 `— PASSED`（仅 unsigned warning）。

## 目录

```
bundle/     THE SUBMISSION：manifest/listing/main.splash/icon/截图
app/guardian/            场外链路证明（同一套设计在真实 Matrix + 真实 LLM 通道跑通，
                         G1–G5 六套冒烟 70+ 断言全绿）
app/miniapp-qianxian/    旧 Rinx spike（已归档，被 app/qianxian 取代）
evidence/                验收与证据：regression / edge-cases / demo-script /
                         ux-specs（规范对照）/ splash-constraints（运行时约束手册）/
                         submission-readiness（提交就绪度）/ qianxian review 包 + 7 问作答
PRIVACY.md               隐私政策（无网络 + 本机存储 + 用户可导出/清空）
task.md                  任务说明与 12 条验收条件
blueprint-gpt.md         设计蓝图（v0.7.1 冻结，四轮对抗评审）
run.md                   复现步骤 / 版本锁定
GOAL.md changes.md       执行总纲与变更记录
```

## 提交形态与验收

- **为什么选 script-app**（四条官方形态逐一对照）→ [evidence/submission-form-decision.md](evidence/submission-form-decision.md)
- **验收条件逐条映射**（task.md 的 guardian 口径 → script-app 实际）→ [evidence/acceptance-mapping.md](evidence/acceptance-mapping.md)

## 设计依据

交互与可用性规范（含第一方系统应用逐条对照）见
**[evidence/ux-specs.md](evidence/ux-specs.md)**；完整状态机与防编造校验链见
**[blueprint-gpt.md](blueprint-gpt.md)** v0.7.1。

## 许可证

Apache License 2.0 — 见 [LICENSE](LICENSE)。
