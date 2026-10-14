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

## 2026-10-14 · 收口轮：五个 issue 全部推进到「代码/结论」终态

黑客松提交后，把「报问题」推进到「修问题」。本轮结果一览：

| Issue | 终态 | 物证 |
|---|---|---|
| App-Hub [#214](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/214)（hosts 禁端口） | ✅ 已修，PR 待审 | [PR #230](https://github.com/OctoSense-org/OctoSense-App-Hub/pull/230)（61 项测试全绿 + 逐字锚点） |
| App-Hub [#213](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/213)（空闲不投递回调） | ✅ 已修，PR 待审 | [makepad PR #125](https://github.com/OctoSense-org/makepad/pull/125) |
| Rinx [#90](https://github.com/hagency-org/Rinx/issues/90)（无 edit_message） | ✅ 已实现，PR 待审 | [Rinx PR #91](https://github.com/hagency-org/Rinx/pull/91)（miniapp-core 31 项 + rinx lib 357 项全绿） |
| OctoSense [#490](https://github.com/OctoSense-org/OctoSense/issues/490)（SSL 字段缺失） | ❌ 撤回——我的误判 | 撤回评论 + 关闭；[makepad PR #124](https://github.com/OctoSense-org/makepad/pull/124) 把验证固化为回归测试 |
| OctoSense [#489](https://github.com/OctoSense-org/OctoSense/issues/489)（日历通路） | ✅ 已被 device_calendar 回答 | 重新定界评论（剩余项：Linux 覆盖/免面板写，留给维护者裁量） |
| octos [#2768](https://github.com/octos-org/octos/issues/2768)（内核定时唤醒 RFC） | 📜 设计勘察补齐 | 实现勘察评论（gateway 装配行号钉死 + serve 侧三个待决设计问题），待 RFC 共识后实施 |

### #213 根因更正（重要，推翻自己）

初报归因于「Wayland 后端缺网络完成唤醒」——**错了**。裸 `start_timeout` 回调在空闲下正常触发（事件循环侧 8ms 泵与 wake pipe 都工作）。真正断点：**Splash isolate 的脚本任务队列从不被排空**——主 VM 每次事件分发后 drain promise/task 队列，isolate 没有自己的节拍，promise 被定时器/网络回调 resolve 后 await 线程在空闲时永远停摆。修复：两条 isolate 入口（`with_isolate_installed`/`with_isolate`）成功退出前跑 `makepad_script_std::pump`。回归测试拆泵即红；真机（Wayland + card-host）双实验零输入验证：定时器 promise 1s 后送达、自签 HTTPS `on_response` 空闲送达 status=200。

### #490 撤回说明

字段在平台类型上带 `live` 属性且脚本构造/贯通/生效全链路可用（钉住的三个 rev 逐一验证 + 端到端自签 HTTPS 对照：带字段 200 / 不带 TLS 拒绝）。当初的 `named_fn_arg` 报错来自 spike 文件里同行的其它构造（原文件未留存，无法逐字还原——记录教训已入 learned）。撤回后把贯通测试固化进 makepad 测试集，避免后来者再踩同样的疑云。

### Rinx #91 实现要点

`matrix.edit_message`（m.replace）：miniapp-core 加变体+parse+cost+测试；宿主 `send::edit()` 先取原事件校验发送者（伪造编辑会被所有客户端静默丢弃，提前诚实报错），沿用 send 通路的 review+audit 门；wire 形态两个单测钉住（与 room_history 渲染语义对齐；不重复 ping 原 mentions）。
