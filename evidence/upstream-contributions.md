# 上游贡献清单（OctoSense-org / octos-org）

开发「牵线」过程中定位并上报的上游问题与提案（2026-10-11 提交，全部附源码级根因/复现）：

| # | 仓库 | Issue | 类型 | 内容 |
|---|---|---|---|---|
| 1 | OctoSense-App-Hub | [#213](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/213) | 🐛 bug | script app 网络回调在空闲事件循环下不投递（Wayland 后端缺网络完成唤醒；附三风格复现与源码定位） |
| 2 | OctoSense-App-Hub | [#214](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/214) | 🐛 规则不一致 | network.hosts 准入禁止端口、运行时裸 host 却匹配任意端口 |
| 3 | OctoSense | [#489](https://github.com/OctoSense-org/OctoSense/issues/489) | 💡 提案 | 本机日历第三方 script app 只读/受审写通路（os.calendar 服务 app_id 硬编码自答；三档方案） |
| 4 | OctoSense | [#490](https://github.com/OctoSense-org/OctoSense/issues/490) | 💡 API 补全 | makepad 脚本侧 net.HttpRequest 缺 ignore_ssl_cert 字段（平台类型有；附 SSL_CERT_FILE workaround） |
| 5 | octos | [#2768](https://github.com/octos-org/octos/issues/2768) | 📜 RFC | 宿主内嵌内核定时唤醒能力（app/agent 的 T-24h 提醒场景，附可运行参考实现 qx-reminder-bridge.py） |

另有一项（makepad `on_render` 输出行缺失，初赛期间定位 rev `eeb9a33`/验证 `db4691d0`）因 makepad 仓未开放 issue 且复现细节不足以支撑独立报告，记录于 changes.md 2026-09-30 行，暂不硬发。

**为什么这样做**：评分之外，这些是我们真实踩到的平台缝隙——报告它们比绕开它们对生态更有价值。
