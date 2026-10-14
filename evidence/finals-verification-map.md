# 牵线 · 决赛核验地图（评审 10 分钟可复核）

> 每一条给出「命令或链接 → 期望结果」。全部在本仓库与公仓可复核。
> 当前版本：v0.10.1（tag，官方 publish-github 工作流签名发布）。

## 0. 总入口

- 仓库：https://github.com/kkkkikun/qianxian-guardian （bundle/ 在仓库根，一仓一应用）
- 签名 Release：[v0.10.1](https://github.com/kkkkikun/qianxian-guardian/releases/tag/v0.10.1)
  （密封包 `app.bundle.pack.json` + manifest + receipt；演示视频与截图在资产区）
- 演示视频（103 秒，配音+字幕，实机帧）：[B 站](https://www.bilibili.com/video/BV1djp66AEfA/) ·
  [仓库内同一文件](finals-demo-v0.10.1.mp4)
- 实机实拍（官方桌面 shell 内运行）：[host-desktop-20261014.png](host-desktop-20261014.png)
- 提交 issue（App Hub）：[#98](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/98)

## 1. 端到端回归（40/40 全绿）

```sh
rm -rf /tmp/octosense-card-apps/qianxian
card-host --bundle bundle --allow-unsigned --stamp --remote 8146 &
python3 app/qianxian/tools/qx-verify-v2.py    # 期望：PASS 40/40
bash scripts/qx-gate-check.sh                 # 期望：GATE: ALL PASS
```

覆盖：建守护/冲突/详情/确认/回执/ICS/AA 闭环/收款/导出/清空/搜索/筛选/管家降级/提案拍板/
群智收敛/主动提案/结案报告/沉默留痕 + WP0 防回退（R-30 切片/R-31 迟到回调守卫）+
WP1 成员端（R-32 横幅+Outbox / R-33 自治策略自测 / R-34 归票幂等自测）+
WP2 可操性（R-35/36 内核 op 链）+ WP3 速览卡（R-37 载荷一致性）+ WP4 邮件（R-38 降级否定）+
WP5 主动回合（R-39 催拍板 / R-40 催收+留痕对照）。

## 2. ops 与可操性

- [evidence/ops-coverage.md](ops-coverage.md)：18 个状态变更函数逐行（驱动 op / UI 入口 / 落盘断言）。
- [evidence/operability-matrix.md](operability-matrix.md)：12 PLAN op × 五入口逐格证据；
  结论：12/12 op 全部 agent 可表达 + 全部 UI 可达，平台限制如实标注。

## 3. PLAN 协议三处同源

bundle/AGENT.md（v4 op 表）· bundle/main.splash `build_agent_turn` · `tools/qx-kernel-turn.py`。
复核：`python3 tools/qx-dialog-chain.py` → 期望 `DIALOG-CHAIN ALL PASS`（真内核×剧本 mock）。

## 4. 真宿主与群体协调实证

- Rinx 真宿主四轮（含 MiniMax-M3 真模型）：[s4-real-host-20261010.md](s4-real-host-20261010.md)。
- **双实例牵线**（agent×agent，palpo 真房全链 16 断言）：
  `python3 tools/qx-wp1-e2e.py` → 期望 `WP1-E2E ALL PASS`；
  证据 + 诚实边界：[finals-wp1-agent2agent-20261013.md](finals-wp1-agent2agent-20261013.md)。
- 主动守护：[v100-wp4-proactive-20261012.md](v100-wp4-proactive-20261012.md) +
  [WP5 扩展](finals-wp5-proactive-expansion-20261013.md)（催拍板/梯度催收/留痕对照）。
- 群智收敛降级路径：[v100-wp3-converge-20261012.md](v100-wp3-converge-20261012.md)。
- 结案报告卡：[v100-wp5-finreport-20261012.md](v100-wp5-finreport-20261012.md)。
- 守护灯速览卡（L0 校验 valid=true）：[finals-wp3-glance-card-20261013.md](finals-wp3-glance-card-20261013.md)。
- 邮件人审通路（平台边界在案）：[finals-wp4-mail-20261013.md](finals-wp4-mail-20261013.md)。

## 5. 发布与门检

```sh
python3 $OCTO check bundle    # 期望：qianxian 0.10.1 — PASSED（仅 unsigned warning）
```

发布流：`.github/workflows/publish-app.yml`（tag 推送 → GitHub 检查+签名+打包）。

## 6. 上游贡献

[evidence/upstream-contributions.md](upstream-contributions.md) 全清单。当前在途：
[PR #230](https://github.com/OctoSense-org/OctoSense-App-Hub/pull/230)（network.hosts 准入/运行时
端口对齐，修 #214，待审）· [PR #190](https://github.com/OctoSense-org/OctoSense-App-Flow/pull/190)
（snap-to-png，评审修复已推送待复审）· Rinx #90 · OctoSense #489/#490 · octos #2768。

## 7. 演示材料

- 决赛 103 秒讲解视频（七章，配音+字幕，制作器可复跑 `tools/qx-finals-video.py`）。
- 用户视角五幕 [demo-videos/](demo-videos/) + 端到端七套 [scenarios/](scenarios/)
  （实机录制+断言全过，`tools/qx-scenario.py --scenario <文件> --frames … --video …` 复录）。
- 界面截图三张：[bundle/screenshots/](../bundle/screenshots/)（宿主真实渲染帧）。
