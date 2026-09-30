# Agent 修改了什么，人检查了什么

| 日期 | 任务 | Agent 做了什么 | 人检查了什么 | 结论 | 证据 |
|---|---|---|---|---|---|
| 2026-09-27 | G1–G5 全切片（Zcode） | guardian Python 链：schema/幂等/分诊/OUP 真链路/状态机/Outbox/注入拦截/崩溃补偿；6 套冒烟；run.md；本地提交 `703afb1`（历史脱敏重写后；原 `91120c5`） | 全量回归 6 套冒烟自称全绿（G1 7/7+G2 19/19+分发10/10+G4a 9/9+G4b 9/9+G5 9/9）；acceptance 9/12 通过 | P0-A/B 通过并有自动化证据；P0-C 待推送/GUI/队外复现 | `evidence/全量回归-20260927.txt`、`evidence/acceptance.md` |
| 2026-09-28 | 上游核查（31 仓 git 化） | repos/ 29 快照原地转 git（baseline+fetch）；Rinx #28 确认含 broker；App-Hub/Design-Flow/OctoScript 精读 | `robrix2-compete` baseline 与 `05daf9b` 逐字节一致；官方赛制仓 9-27 后零变动 | 快照变 git，漂移可查；A 路线（script-app 主提交）确定 | `repos/README.md` 转换记录 |
| 2026-09-30 | qianxian script-app（A 路线） | `octo new` 起包；`main.splash` 改写（规则分诊→提案→确认/改口/取消→storage，AI 可选降级）；定位上游 `on_render` 行缺失根因（makepad `eeb9a33`，`/snap` 漏建，已用 `db4691d0` 构建链验证列表 11 控件）；`hub check PASSED`；`hub scan` 7 问作答 | 待人：publisher 真值、真截图换占位图重 stamp、GUI 六步、公开推送 | 部分完成（门过，缺真图/真值） | `app/qianxian/bundle/`、`app/qianxian/build/review.json`+`review-answers.md` |
