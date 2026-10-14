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

**证据补充（2026-10-11 二次提交）**：每个 issue 均已追加「补充证据」评论——完整复现物料（最小脚本/逐字日志/时间线表/双向实测），要点：
- #213：三风格实验时间线表（P/RST/GW）+ 服务端 REQ/UPSTREAM 200 日志原文 + 排除项（nudge 定时器无效、on_error 也不投递）
- #214：准入拒绝与运行时放行的**逐字输出**对照 + splash_policy.rs 门代码原文引用
- #489：三路线平台矩阵（含拒绝原文出处行号）+ ICS 替代方案作为需求佐证
- #490：最小复现脚本（整个 app 一个调用）+ 原始 `[E]` 日志行 + SSL_CERT_FILE workaround 验证记录
- #2768：参考实现全文 + 「用户触发的 agent 回合完全正常（tool_calls=1 get_forecast）」的内核日志对照——缺的只是到点自动发起


## 2026-10-12 · Rinx #90：mini-app 无 matrix.edit_message（m.replace）服务

- **链接**：https://github.com/hagency-org/Rinx/issues/90
- **类型**：能力缺口 issue（群体协作最小缺口；证据充分的源码核实）。
- **内容**：miniapp-core 的 `MatrixServiceCall` 无 `EditMessage`；`m.replace` 只在
  Rinx 自身聊天编辑（room_history.rs:196/831/867）与文章应用（article_app/backend.rs:232/348）
  内部；palpo「acknowledge m.replace without populating /relations」语义在案。
  建议暴露 `matrix.edit_message`（event_id+新 body，与 room_history 编辑渲染同语义）。
- **降级参考实现随 issue 附上**（协议不变仅承载降级：qx-converge 归票+伴生进程+app 三按钮）。
- **触发动机**：WP3 群智收敛的活卡片路径被源码核实否决（约束 4），按规划降级分支交付后，
  把缺口作为贡献补报——评审「对 OctoSense 的贡献」轴的硬物证。

- **2026-10-12 追评**：提 issue 前已拉取上游最新代码复核——Rinx 主仓自 10-11 无新提交、
  App-Hub 拉取 87 提交后仍无 edit_message 服务面（comment 6123285301）。证据钉在 issue 里。

## 2026-10-14 · 从报问题到提 PR：App-Hub #214 已修，PR #230 待审

- **PR**：https://github.com/OctoSense-org/OctoSense-App-Hub/pull/230（fix/host-port-entries → main）
- **内容**：准入层 `check_host`（app-contract/src/policy.rs）接受 `host:port` 条目——端口须纯数字且 1..=65535；空端口/非数字/超界/无主机名/多冒号/带路径/通配符逐一拒绝。裸 host 语义不变。PUBLISHING 双语档「Network hosts」节同步为「可显式带一个端口；裸 host 匹配任意端口、带端口只匹配该端口」。
- **验证**：新增 `network_hosts_may_name_one_explicit_port`（接受 1 + 拒绝 8 例）；`cargo test -p octosense-app-contract` 全绿（61 项）。
- **定位依据**：运行时门 `url_allowed`（splash_policy.rs）本就支持 host:port——准入与运行时对齐，而非收紧运行时（对存量零破坏，最小授权可用）。
