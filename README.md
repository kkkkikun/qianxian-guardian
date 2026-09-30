# 牵线 · 聚会筹办守护（qianxian）

> **一条群消息，长成一个被照顾到收尾的完整活动。**
> 本作品是**活动生命周期守护**（Case 状态机），不是聊天增强——聊天只是意图的入口和结果的回执通道。

- **主场景**：日历（时间收敛、**冲突检测**、待定 vs 已确认）
- **提交形态**：OctoSense **script-app**（`app/qianxian/bundle/`，`hub check — PASSED`）
- **比赛**：GOSIM Agentic App 黑客松 2026（队伍 Aurora-X）

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

**四条最高法则**：

1. **不编造**：抽不到的时间/活动/地点一律留空显示「未抽取到」，不猜、不填。
2. **用户始终主动**：分诊不确定时给澄清卡 +「仍然建守护」入口，不替用户做决定。
3. **危险操作留退路**：取消/清空是两段式确认，且 5 秒内可撤销。
4. **矛盾交人裁决**：检测到同时段冲突只提示不自作主张；改一个时段即可自动解冲突。
5. **数据在用户手里**：可导出（屏显 JSON 供复制）、可一键清空、损坏自动备份。

失败不掩盖：无 AI 服务→明确降级继续可用 · 分诊未命中→澄清卡说明原因 ·
损坏数据→备份后重启不丢 · 重复确认→「已确认，未重复」。

## 无 AI 也完整可用

本应用**不依赖任何模型服务**：分诊、时间槽抽取、冲突检测、状态机全部是确定性规则。
AI 只是可选增强——宿主提供 `octos.turn.start` 时才出现「AI 解析（可选）」按钮；
本运行环境无该服务时**明确降级**并继续可用（见 `evidence/ux-specs.md` 4.8 记档的平台限制）。

## 怎么审这个作品（三条路，从零门槛到完整复现）

**① 零门槛：直接读源码**（不需要任何构建）
本应用是纯解释执行的脚本，核心逻辑都在一个文件里：
`app/qianxian/bundle/main.splash`（约 1600 行，Splash/OctoScript 方言；函数名即语义：add_case / confirm_case / cycle_slot / add_person / rebuild_lines …）。
配套阅读：[evidence/demo-script.md](evidence/demo-script.md)（21 步操作）、
[evidence/regression-20261001.md](evidence/regression-20261001.md)（14 项真机验证）。

**② 门禁核验**（需要上游 `hub` 工具）
```sh
git clone https://github.com/OctoSense-org/OctoSense-App-Hub.git
cd OctoSense-App-Hub && cargo build --release -p octosense-app-hub --bin hub
./target/release/hub check <你的-clone>/my-entry/app/qianxian/bundle --allow-unsigned
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
- **门检**：`python3 $OCTO check app/qianxian/bundle` → 目标 `— PASSED`（仅 unsigned warning）。

## 目录

```
app/qianxian/bundle/     THE SUBMISSION：manifest/listing/main.splash/icon/截图
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

## 设计依据

交互与可用性规范（含第一方系统应用逐条对照）见
**[evidence/ux-specs.md](evidence/ux-specs.md)**；完整状态机与防编造校验链见
**[blueprint-gpt.md](blueprint-gpt.md)** v0.7.1。

## 许可证

Apache License 2.0 — 见 [LICENSE](LICENSE)。
