# 牵线 · 决赛核验地图（评审 10 分钟可复核）

> 每一条给出「命令或链接 → 期望结果」。全部在本仓库与公仓可复核。
> 当前冻结版本：v0.10.1（tag，`63d1466` 之后见 git log）。

## 1. 回归套件（31/31 全绿）

```sh
docker start gosim-pg 2>/dev/null; ./palpo-ctl.sh start   # 可选（仅 Matrix 相关用例需要）
rm -rf /tmp/octosense-card-apps/qianxian
card-host --bundle bundle --allow-unsigned --stamp --remote 8146 &
python3 app/qianxian/tools/qx-verify-v2.py                # 期望：PASS 31/31
bash scripts/qx-gate-check.sh                             # 期望：GATE: ALL PASS
```

覆盖：建守护/冲突/详情/确认/回执/ICS/AA 闭环/收款/导出/清空/搜索/筛选/管家降级/提案拍板/
群智收敛/主动提案/结案报告/沉默留痕 + R-30（无切片写法）/R-31（迟到回调守卫）。

## 2. ops 覆盖矩阵（18 个状态变更函数逐行）

[evidence/ops-coverage.md](ops-coverage.md)：每个函数标注「驱动它的 PLAN op / UI 入口 / 落盘断言」。
复核：对照表逐行点开源码行号即可。

## 3. PLAN 协议三处同源

- 机器可读 op 表：[bundle/AGENT.md](../bundle/AGENT.md)（v4）
- app 内提示词：bundle/main.splash `build_agent_turn`（grep `PLAN{` 定位）
- 内核直连复跑：`python3 tools/qx-kernel-turn.py --kimi "…"`（真模型返回合规 PLAN）
三处 op 全集一致（create/confirm/reschedule/cancel/add_people/set_bill/complete/
draft_dunning/mark_paid/undo/clear/export）。

## 4. 真宿主 e2e（Rinx × 真模型）

[evidence/s4-real-host-20261010.md](s4-real-host-20261010.md)：Rinx 真宿主四轮
（mock create/reschedule + MiniMax-M3 真模型 create/confirm），落盘断言全过；
Kimi 真模型轮次见 WP4 证据。复现命令在文件内逐条给出。

## 5. 发布与门检

```sh
python3 $OCTO check bundle    # 期望：qianxian 0.10.1 — PASSED（仅 unsigned warning）
```
发布流程：`.github/workflows/publish-app.yml`（官方 publish-github，tag 推送即
GitHub 检查+签名+打包）。Release：[v0.10.1](../../releases/tag/v0.10.1)（密封包 +
12 场景视频 + 3 截图）；历史锚点 [v0.1.0](../../releases/tag/v0.1.0)（初赛冻结）。

## 6. 上游贡献清单

[evidence/upstream-contributions.md](upstream-contributions.md)：Rinx #90（mini-app 消息编辑缺口）、
App-Flow PR #190（snap-to-png 工具，评审修复已推送）、plan-pattern 模板等——
每条带 issue/PR 链接与状态（open/merged/closed）。

## 7. 演示材料

用户视角五幕：[evidence/demo-videos/](demo-videos/)（群消息/冲突/AA/管家/收敛）；
端到端功能验证七套：[evidence/scenarios/](scenarios/)；
全部实机帧录制（`tools/qx-scenario.py --scenario <file> --frames … --video …` 可复录）。
