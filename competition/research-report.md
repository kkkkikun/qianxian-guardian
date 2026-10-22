# GOSIM「Agentic App 黑客松 2026」调研报告

> 📦 **存档说明**：本报告是参赛初期（2026-09-25 起）的原始调研存档，从参赛工作区原样保留。
> 文中引用的 `repos/`、`research/` 等相对路径指向当时的参赛工作区（vendored 上游仓库与调研材料），
> 未随本仓库分发，作为档案引用保留原文。赛制、时间线、评审维度、奖项等内容均为当时核实过的事实。

> 调研日期：2026-09-25 ｜ 信息来源：[比赛官网](https://create.gosim.org/agenticapp26/)（SPA 全部文案已提取至 [research/](research/)）、[octosense.org](https://octosense.org/cn)（12 场景指南全文已抓取）、[OctoSense-org](https://github.com/OctoSense-org) / [octos-org](https://github.com/octos-org) / [hagency-org](https://github.com/hagency-org) 共 23 个仓库（已全部下载到 [repos/](repos/) 并做了深度阅读）。
>
> **09-25 晚更新**：整合队友整理的《比赛说明·团队统一理解版》（[research/队友材料-比赛统一理解版.docx](research/队友材料-比赛统一理解版.docx)，提取版 [同目录 .md](research/队友材料-比赛统一理解版-提取.md)）——该文档补全了官网抓取中缺失的 2 道悬赏题（凑齐 13 道），并带来课程口径的「终端智能层」解释、「完成」判定清单、评审维度表与常见误解澄清，已分别并入本报告第二、六、七、八章。
>
> **09-27 更新（9/26 课程/演示整合）**：官方课程与演示仓库 [gosimfoundation/hackathon-agenticapp26](https://github.com/gosimfoundation/hackathon-agenticapp26) 已整体下载到 [repos/hackathon-official/](repos/hackathon-official/)（144KB 讲稿全部通读）。重要增量：① 仓库大改名——**Rinx**（原 robrix2，hagency-org/Rinx）、OctoSense-Desktop、OctoSense-System-Apps（新，AppCard 并入且含第一方系统应用）、OctoScript-App-Design-Flow（原 OctoScript-AppCard）；② 锁定版本表确认；③ 官方演示项目 **octo-weather「行程守护」设计蓝图**——对齐评审标准的参考架构（见 5.5 节）；④ octos 集成现状的真实边界（只有 AppCard 接通）；⑤ 初赛/复赛/决赛的精确交付清单与答辩格式；⑥ 学员练习包的任务模板与交付目录结构。已并入第二、四、五、八、九章。

---

## ⚡ 最重要的几件事（TL;DR）

1. **今天是 9 月 25 日，初赛提交截止 10/4 23:59（北京时间），只剩 9 天。** 报名已于 9/23 23:59 截止（确认你自己已报名；队伍名单在 10/4 初赛提交时锁定）。
2. **本届主开发基线是 Rinx（原 robrix2，hagency-org/Rinx）**，Matrix 聊天客户端作为小程序宿主；OctoSense ROM 只是可选技术进阶方向。页面原文："本届大赛以 OctoSense 为核心，以 robrix2（现 Rinx）小程序宿主为主要开发基线"。
3. **统一命题**："用一句话，生成一个能用的应用" —— 但今年的重点不是生成 UI（这已经谁都能做到），而是 **Agent 化的应用**：应用由 Agent 生成，是 Agent 行动的手，也是它与你沟通的方式。每个场景都要**完成一项真实任务**（读状态 → 提议 → 授权 → 执行 → 核验结果），而不是生成界面或摘要。
4. **铁律 no-facts**：模型/卡片**不得编造事实**（天气、价格、任务状态……）。一切事实必须来自声明式的 `sys.*` 数据能力，注明来源。违规是评审红线。
5. **硬性提交要求**：Apache 2.0 开源 + 可运行原型 + 可复现的宿主版本与启动说明 + 短视频 + 截图 + 已报名成员名单。设计稿/视频不能代替可运行作品。
6. **奖金**：奖池 ¥50,000（一等奖 1 名 ¥20,000、二等奖 2 名 ¥9,000/名、三等奖 3 名 ¥4,000/名，含 MiniMax Token 额度）；另有两个专项奖（最佳 Agentic 奖、最佳技术突破奖）。
7. 初赛评审用 **10/4 冻结版本**，之后可继续迭代同一作品到复赛（10/9 冻结，10/12 线上决赛答辩）。

---

## 一、比赛概览

| 项目 | 内容 |
|---|---|
| 名称 | Agentic App 黑客松 2026（GOSIM Create 系列赛事之一） |
| 主题 | **意图，即应用**（The Intent Is the App）——"意图所至，应用而生" |
| 主办 | GOSIM（全球开源创新峰会，[gosim.org](https://gosim.org)）；技术平台方为 OctoSense-org |
| 赞助 | **MiniMax**（Token 赞助，¥50,000 额度）、**Kimi/月之暗面**（AI 编程权益） |
| 形式 | 线上为主（初赛、复赛、决赛均线上）；总排名前三受邀 10/17 到深圳 GOSIM Shenzhen 2026 现场展示（到场不影响评奖） |
| 参赛资格 | 设计师、产品人、OPC（一人公司）、学生、开发者；可单人可组队；队长和每位队员须分别报名 |
| 同期赛事 | Agentic App 与「智能体工厂」「巡天智能体」并行，相互独立 |

### 完整时间线（北京时间 UTC+8）

| 日期 | 事件 |
|---|---|
| 9/13 09:00 – 9/23 23:59 | 报名与组队（**已截止**） |
| 9/22 | 开营说明 |
| **9/24** | **锁定版本、支持设备与练习数据发布**（比赛指定环境以此为准） |
| 9/25 | 异步自检（今天——应完成环境自检） |
| 9/26（周六）– 9/27（周日） | 机制入门课（必修：第 0 讲 Agent 化的软件；1A Octoscript 速成；1B robrix2+hagency 小程序；2 Rust 能力与组件；3 悬赏题导览。选修：第 2 讲等。有回放） |
| 9/28 – 10/4 | **作品制作周**（10/3 答疑、10/4 提交检查为可选支持） |
| **10/4 23:59** | **初赛提交截止**（场景 + 可运行原型 + 源码说明 + 短视频 + 截图 + 已报名成员名单；评审用当日冻结版本） |
| 10/5 – 10/6 | 初赛评审（独立评阅、运行核验、交叉复核）；**10/6 20:00 公布 50 人晋级名单与反馈** |
| 10/7 | 复赛工作坊（国庆假期内另安排） |
| 10/1–10/8 国庆 | 可选答疑/门诊（按队预约，解决场景接入、自动化验证、技术扩展阻塞） |
| **10/9 23:59** | **复赛提交截止**（作品 10/9 冻结） |
| 10/10 – 10/11 | 复赛材料评审（安装复现、任务验证、评分；10/11 连线检查由赛务组织） |
| **10/12（周一）** | **线上决赛**：13:00–17:00 分组答辩（3 分钟应用演示 + 2 分钟 Agent 自动化与技术贡献说明 + 评委问答），**20:00 公布一、二、三等奖** |
| 10/13 – 10/16 | 前三名确认代表、行程与展示准备（分队预约检查音视频/投屏/备用视频） |
| **10/17（周六）** | 前三名在 **GOSIM Shenzhen 2026 黑客松现场**展示与颁奖（不再评分） |
| 10/18 – 10/31 | 贡献合入窗口（完善 PR/应用/规范，跟进项目采纳；不改变评奖结果） |

### 奖项

| 奖项 | 名额 | 金额（现金 + MiniMax Token 额度） |
|---|---|---|
| 一等奖 | 1 | ¥20,000 / 队 |
| 二等奖 | 2 | ¥9,000 / 队 |
| 三等奖 | 3 | ¥4,000 / 队 |
| 最佳 Agentic 奖 | 名额随评审细则公布 | 应用层作品可直接争取，不要求改 ROM 或认领悬赏 |
| 最佳技术突破奖 | 名额随评审细则公布 | 在应用自动化基础上评价项目反哺与 OctoSense ROM 突破；单纯刷机/累计 PR 不构成突破 |

另：MiniMax 提供价值 ¥50,000 的 Token 额度作为**参赛开发资源**（与奖金分开发放）；Kimi 提供编程权益（代码理解、功能开发、调试测试）。

---

## 二、命题解读：什么是「Agent 化的应用」

页面原文（第 0 讲文案）非常直白：

> "一句话生成一个应用，今天只要模型不太差就能跑通，这不再是比拼的重点。本届命题是畅想 **Agent 化的应用**：应用由 Agent 生成，是 Agent 行动的手，也是它与你沟通、交互的方式。"

评分总纲是三句话：

> "意图到应用的想象力与 **Agent 化程度**、实际**跑通程度**，以及服务作品的**能力与平台突破**。"

"谁的应用最面向 Agent 自动化，谁就更接近最佳。看 Agent 能否**理解状态、完成多步操作、跟进变化，并把可靠结果交给用户**。"

对参赛作品的隐含要求（从各场景指南和 FAQ 归纳）：

1. **任务闭环**：从真实输入到执行与结果核验（读状态 → 提案卡 → 用户授权 → 执行 → 核验 + 状态更新），"而不止生成界面或摘要"。
2. **失败也要演示**：演示必须包含一个**失败/拒绝/过期状态**（如权限被拒、状态过期、任务失败），并展示处理方式。初赛与复赛的验收口径反复强调这一点。
3. **人在回路**：重要操作展示"需要确认的事项"；授权要写清范围（联系人 + 动作），可撤销；单次允许 vs 持续授权要区分。
4. **来源可查**：邮件、消息、天气、任务进度都要注明来源；区分"练习数据（fixture）"与"真实服务接入"。
5. **可靠性证据**：展示状态变化、失败恢复、重复测试；说明哪些步骤仍需人工。

### 「终端智能层」：Agent 站在哪一层（课程口径，队友文档整理）

> "Agent 不只停留在聊天窗口里，也不直接等同于操作系统内核，而是运行在**应用和系统之间**，负责把用户意图连接到终端中的应用与设备能力。"

- 它接收**消息、邮件、时间和系统状态**等事件，调用日历、提醒、消息、地图、设备设置等**已被授权**的能力，再把执行结果反馈给用户。
- **「持续 Agent」不是无限制的后台自由操作**，而是"长期存在、由事件或时间唤醒的执行者"：事件到来 → 读上下文 → 规划任务 → 执行允许的动作 → 回到等待状态。用户确认、权限、结果反馈三件事永远保留。

队友文档的一句话总结（建议作为全队的"统一记忆点"）：

> **一个完整的 Agentic 任务 = 事件入口 + 状态读取 + 意图理解 + 计划和分工 + 用户确认 + 应用或系统动作 + 结果验证 + 失败和拒绝处理。**
>
> 关键不是"让 Agent 说得更像人"，而是"让 Agent 在终端里完成真实任务，并让用户**看得见、控得住、验得到**"。

### 三级深度阶梯（加分维度，不是资格线）

页面有两套表述（旧版 STEP 1/2/3，新版海洋生物命名），实质相同：

| 深度 | 命名 | 定位 | 做什么 | 交付 |
|---|---|---|---|---|
| L0 意图层 | **鹦鹉螺 / NAUTILUS**（应用层 · 设计师与 vibe coder） | 零编译、人人可做 | 用现有能力与组件写 app.md / L0 卡片，组合既有数据源（旅行计划、买菜清单、健身打卡、播客速览……） | spec + lint + 参考卡片 |
| 能力层 | **帝王蟹 / RUSTACEAN**（用 Rust 扩展） | 数据/操作能力 | 为你的场景新增 `sys.*` helper（公交、汇率、日历、空气质量、邮件、消息、设备状态……），完善契约、权限、错误处理、限流 | 新数据能力 + 应用演示 |
| 平台层 | **大章鱼 / GIANT OCTOPUS**（深水区 · 技术选做） | 改语言、改渲染、改内核、改 ROM | 可视化组件、L0 交互态、工具链与协议悬赏题、OctoSense ROM 系统事件/系统桥/跨应用协作 | 平台贡献 + 应用演示（可复现前后对照） |

> 官方反复强调："阶梯是加分维度，不是资格线。把 STEP 1 做到极致，同样可以夺冠"；"鹦鹉螺的极致设计同样可以拿满创意与完成度分。技术深度加分，不设技术资格门槛。"

### 软件工厂专题（robrix2 + hagency）

页面专门开辟了「ROBRIX AGENT2APP / 软件工厂的应用入口」章节：

- **hagency（原 hafleet）**负责 Agent 编排与任务协作；**robrix2** 提供熟悉的聊天与工作空间界面。参赛作品为两者之间的具体工作环节增加**小程序**。
- 四个选题方向：**任务进度、Agent 状态、结果验收、团队协作**（如：聚合任务/依赖/等待原因；区分实时与过期状态；验收执行结果与测试证据；交接提醒）。
- 交付要求：一个明确的软件工厂使用场景 + 能在指定 robrix2 环境运行的小程序 + 一次完整任务演示（读状态、执行操作、核对结果，并展示一个失败或过期状态）。
- 注意："hagency 服务于软件协作选题，其他场景不要求接入软件工厂。"

---

## 三、12 个场景（OctoSense 应用指南）

官方指南：https://octosense.org/cn（应用体验指南；全文已抓取到 [research/octosense官网-12场景指南全文.txt](research/octosense官网-12场景指南全文.txt)）。每个场景页面统一结构：场景体验 → 步骤演示 → 应用内用法 → App Card 桌面卡用法 → 数据如何关联 → 由你授权的部分 → Agent 什么时候工作。**每个场景，都要完成一项任务。** 官方允许"把多个场景连接成一条任务链"（联动多场景统一参评），但场景本身不是最终作品——最终仍要通过一个可运行 mini-app 展示 Agent 如何完成任务。

| 场景 | 示例任务（官方指南） |
|---|---|
| 邮件 Mail | 学校来信改接孩子时间 → Agent 从邮件提取变化 → 生成日历变更 + 确认回复卡片 → 单次确认或持久授权（限定发件人 + 动作） |
| 即时消息 Messaging（robrix2） | 群里约周五 19:00 聚餐 → 时间地点组成事件卡（显示日历冲突）→ 确认回复与日程 → 授权只针对该对话 |
| 日历 Calendar | 会议改期与私人预约冲突 → 列出冲突原因 → 提议替代时段 → "提出建议还不等于会议已改期"，等待组织者回应 |
| 天气 Weather | 周六野餐遇午后有雨 → 关联日历活动地点的预报 → 提议提前到 10:00 → 确认后日历与天气卡一致更新 |
| 新闻 News | 每日 06:00 五分钟科技简报 → 摘要与原始报道并列、可追溯 → 阅读或收听由用户决定 |
| 音乐 Music | 下雨的晚上 + 一小时空闲 → 按偏好准备歌单 → "卡片等待一次明确的播放操作" → 评分反馈改善下次 |
| 视频 Video | 20 分钟想搞懂一个保存的主题 → 解释每条视频为何入选 → 打开原始来源 → 把引用带进笔记 |
| 财经 Markets | 关注公司发财报 → 区分**事实与解释**（原始披露 vs 评论）→ 研究简报与交易决定是两个独立步骤 |
| 导航 Navigation | 10:00 赴约 + 交通变化 → 计算提前出发 → 确认后导航，途中仍显示应到时间 |
| 购物与物流 Shopping | 订单确认邮件 → 物流追踪卡持续更新同一张卡 → 送达后提示保存收据/退货说明 → 提交退货前审阅 |
| 写作与创作 Creation | 选中一段文字 → 原文与改写对照 → 逐段确认应用 → 保留撤销路径；发布是另一个独立操作 |
| 系统与设备 System | 存储不足 → 清理提案明确范围（临时文件，不含个人文档）→ 授权本次 → 检查结果 |

另有 4 个可交互体验（示例数据）：[安心新家（空调）](https://octosense.org/cn/experience/aircon/)、[学校与家人](https://octosense.org/cn/experience/school/)、[年度体检](https://octosense.org/cn/experience/health/)、[同学聚会](https://octosense.org/cn/experience/reunion/)。

---

## 四、技术栈全景（8+1 个项目）

课程围绕"八个项目"展开：**OctoSense、Makepad、octoscode、Octoscript、octos、OctoLoop、robrix2、hagency**（OctoLoop 是方法论，随 octoscode 落地；另有可选的 OctoSense-ROM）。"课程讲机制与 Agent 协作，不要求每个作品同时接入八个项目。"

```
┌────────────────────────── OctoSense（Agent Shell / 桌面与 launcher）──────────────────────────┐
│  应用触点：mail / calendar / weather / … + AppCard 小程序                                      │
│  渲染：Octoscript(L0 卡) → OctoScript-Makepad(kit/主题) → Makepad(原生 UI, Rust/WASM/Android)  │
└──────────────────────────────────────┬───────────────────────────────────────────────────┘
                                       │ OS UI Protocol (OUP, JSON-RPC over stdio/WS)
┌──────────────────────────────────────┴───────────────────────────────────────────────────┐
│  octos（Agent harness 内核：会话/记忆/工具/沙箱/审批/多agent/16+ LLM provider）             │
│  ↑ octoscode（终端 coding agent，OctoLoop 双环：内环执行 + 外环审查）                       │
│  ↑ hagency（软件工厂控制平面：任务图/消息总线/人工确认）→ robrix2（聊天宿主 + 小程序）        │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

### 仓库更名与锁定版本（9/26 官方课程确认，重要！）

比赛期间仓库经历了大改名（旧地址自动跳转，但**资料和交流要用新名字**）：

| 旧名（本报告 9/25 版） | 现名 | 说明 |
|---|---|---|
| OctoSense-org/robrix2 | **hagency-org/Rinx** | 本届主要小程序宿主。从 robrix2 的 `wechat-ui` 分支独立延续（起点 `16913e0c`），现含 WeChat 风格 UI、Moments、文章编辑器（图片/封面/主题/发布撤回）、makepad-html+Blitz 原生 HTML 预览。比赛核查基线 commit 仍是 `05daf9b`；**9/24 课堂环境包另锁实际使用的提交** |
| OctoSense-org/OctoSense | **OctoSense-Desktop** | 桌面宿主 |
| OctoSense-org/OctoScript-AppCard | **OctoSense-org/OctoScript-App-Design-Flow** | 设计方法 + 图片转卡 lab/ 流水线 + octo CLI + 可运行模板（859MB 大仓库） |
| —（AppCard 运行时 9/25 拆出） | **OctoSense-org/OctoSense-System-Apps** | AppCard 助手现居 `apps/appcard`；同仓还有第一方系统应用 **News / Photos / Maps / Camera / Mail / ai-providers** |

**版本锁定表**（官方课程文档原文，"按锁定版本组合使用，不混用最新 main"）：

| 组件 | 锁定提交 |
|---|---|
| makepad | `1d3d383` |
| Octoscript | `68f6a9d` |
| Octoscript-Makepad | `c4c9682` |
| Rinx（比赛核查基线） | `05daf9b` |
| AppCard（宿主使用） | `9e8e4898` |

### 各仓库角色与本仓库中的位置（`repos/` 目录）

| 仓库 | 角色 | 关键事实 |
|---|---|---|
| `repos/hackathon-official/` | **★ 官方比赛课程/演示仓库**（gosimfoundation/hackathon-agenticapp26） | 赛程执行方案、12 场景选题表、初复赛交付清单、答辩格式、9/26–27 全部讲稿与练习包（`docs/`）、octo-weather 设计蓝图。mdbook：`mdbook serve` 即可本地浏览 |
| `repos/Rinx/` | **★ 本届主要小程序宿主**（9/26 HEAD，188MB） | WeChat 风格 Matrix 客户端。构建 `cargo run --locked --features agent_chat`（钉 Rust 1.98.0，可执行文件 `rinx`）。`crates/article-core/resources/app.card` = 内置文章编辑器的 L0 卡（新路径）；`lab/` 含 article-editor、**article-editor-v2**、article-html-integration 等 7 个实验区；小程序授权模型见 `docs/adr/0002`。注意：Rinx 与 octos **没有**协议级集成（官方文档原话 "Octos AppService and BotFather remain separate integrations"） |
| `repos/robrix2-compete-05daf9b/` | Rinx 的 9/21 核查基线快照 | 与官方 rinx-miniapps.md 引用的 commit 完全一致；`lab/article-editor/README.md` 是当时官方指定的范例说明。**结构与 Rinx main 已不同**（旧：`src/article_app/`；新：`crates/article-core/`），读机制用新仓，对提交基线用本仓 |
| `repos/robrix2-old-snapshot/` | robrix2 main 分支旧快照（09-11） | 保留 robrix2 本体文档：`SPLASH.md`（80KB Splash 语法手册）、`book/`、`roadmap/agentchat-demo/`、`specs/` |
| `repos/OctoSense-Desktop/` | 桌面宿主（9/26 HEAD） | 新增 `native-apps.lock.json`；AppCard 模块现在从 OctoSense-System-Apps 引入。`python3 tools/setup-native.py && cargo run`。**桌面默认构建不含 AppCard**，要 `--features app-appcard`；启动器只列 `config/apps.json` 里的应用，AppCard 需用带 AppCard 行的临时目录 `--apps` 启动 |
| `repos/OctoSense-System-Apps/` | **第一方系统应用**（新仓库，9/26） | `apps/`：**appcard、mail、maps、news、photos、camera、ai-providers**——做场景应用时的官方参照实现 |
| `repos/OctoSense-Desktop-old-snapshot/` | 桌面宿主 9/25 快照（原名 OctoSense） | 探索报告结论仍适用（macOS 验证最充分；BACKLOG 列了移动端缺口） |
| `repos/OctoScript/` | Octoscript 语言（9/26 刷新） | L0 规范 `docs/ui-profile-l0.md`；能力封闭清单 `crates/octoscript-ui-l0/src/lib.rs`。**L0 卡进不了 VM、没有副作用通道；Splash 卡会进 VM**（见 5.5 安全对比） |
| `repos/OctoScript-App-Design-Flow-old-snapshot/` | 原 OctoScript-AppCard（9/25 快照，上游已更名） | `a2app-l0/`（写卡框架 + 11 个示例 app）、`lab/image-to-appcard-flow/`（图片→卡流水线）、`apps/`（aircon/calendar/health/mail 示例）。上游更名后新增 octo CLI 与可运行模板，需要时再拉新 |
| `repos/OctoScript-Makepad/` | 主题组件库 + 渲染管线 | L0 theme kit；`runtime.json` 锁 makepad `1d3d383` + Octoscript `68f6a9d` |
| `repos/makepad/` | Rust GPU UI 框架（fork） | **`apps/weather` 是一个完整原生天气 app**（Open-Meteo 数据、失败状态、AI 总线工具）——官方演示即以它为起点做独立应用。所有 Makepad 应用支持 `--remote`/`MAKEPAD_REMOTE=true`（截图、控件查询、点击、按键、中文输入，见 `docs/agents/app-remote.md`）——外环/评审可远程驱动界面亲眼验证 |
| `repos/octos/` | Agent harness 内核 | `octos serve` 提供会话/模型/工具/goal/peer。MiniMax/GLM/Kimi 全部一等 provider |
| `repos/octoscode/` | 终端 coding agent + OctoLoop | 课程用它当全部内环；OctoLoop skill 定义在 `.claude/skills/octoloop/SKILL.md` |
| `repos/octos-book/` | 《构建 AI Agent OS》21 章 | Ch19–21 对应 octoscode/OctoLoop/herdr |
| `repos/hagency/`、`repos/herdr/` | 软件工厂 / agent 终端运行时 | herdr 的 octoscode 窗格识别在 `feat/octoscode-agent` 分支；课程用 `herdr agent prompt/read` 驱动内环 |
| `repos/OctoSense-ROM/`、`repos/OctoSense-App-Hub/`、其余 | 同 9/25 版说明 | Hub 提交**本届不必须**（"现阶段各轮评审以公开源码仓库和可运行作品为准，无需等待 Hub 上架"），可参考其规范做本地预检 |

---

## 五、核心开发路径（按优先级）

### 路径 A（官方主推）：robrix2 小程序宿主

比赛 FAQ 原文："小程序从哪里开始？→ 从 OctoSense-org/robrix2 小程序宿主开始。在'发现'或聊天'+'中打开文章编辑器，体验授权、草稿、原生预览、分享应用与确认发送。网页小程序也可通过 URL 卡片分享；软件工厂选题可扩展 hagency 协作。"

**已有范例**：原生文章编辑器（`robrix2-compete-05daf9b/lab/article-editor/`）——Octoscript L0 定义输入与状态 → Makepad 原生渲染；robrix2 宿主管账号、授权、发送。已验证的流程：打开应用 → 自己的账号授权 → 编辑 Markdown 存本地草稿 → 原生预览 → 选择聊天确认发送；接收者独立授权、草稿隔离。

**复现命令**（README 原文，需先跑通 Palpo 测试 fixture）：

```sh
cargo test --locked --features agent_chat --lib
cargo build --locked --features agent_chat --bin robrix
python3 tools/wechat-ux/check_i18n.py
python3 lab/article-editor/verify_native.py
python3 tools/wechat-ux/live/native_article_app.py   # 双账号 Palpo fixture 端到端
```

**做自己的原生小程序的关键约束**（FAQ 明说，务必注意）：
- "当前原生示例只接受内置文章编辑器；**新增原生小程序需扩展并构建宿主**，不能直接导入任意应用包。" → 即要改 robrix2 源码（仿 `src/article_app/` 三件套 + `resources/mini_apps/<app>/app.card`），提交时给出"宿主分支与提交版本"。
- 网页卡片路线（分享 HTTP(S) URL，`src/mini_app.rs` 自定义 msgtype）门槛低，但"页面不会因此获得聊天记录或账号权限"，Agent 化程度有限。
- "分享只是入口……参赛作品还要展示 Agent 如何读取获授权的状态、完成操作并核验结果。"

**授权模型**（`docs/adr/0002-octoscript-mini-app-authority.md`）：授权绑定 `账号 + 登录代 + app_id + 版本/内容摘要 + instance`，1 小时过期，登出/关窗/换会话即撤销；"receipt or installation is not consent"。

### 路径 B：AppCard L0 卡片（零编译，设计师友好）

写卡三步：
1. **学语法**：`OctoScript-AppCard/a2app-l0/framework/l0.md`（L0 语法）+ `framework.md`（写卡铁律）。卡片五种声明：

```
# ledger weather@1.0.0
# level: L0
source place  sys.geocode(name: state.city)          # 数据来自能力，绝不写死数值
state  units  { shape: enum[c, f], initial: .c }
event  toggle_units { units: cycle(.c, .f) }          # 点按只改声明状态，4 种变换
copy   title  { class: vocabulary, en: "Weather", zh: "天气" }
view   root   Surface { when now.$state == .pending { TextBody(text: copy.loading) } ... }
```

2. **四条铁律**：① Never write a fact（写 "72°" 的卡是在撒谎）；② Say what a thing IS（用语义角色 TextHero/TextBody/TempBar，不写颜色字号）；③ A tap changes declared state, and nothing else；④ Loading is a state, not a number（用 `when now.$state == .pending` 分支）。
3. **校验**：`cargo run -p octoscript-ui-l0 --example check_card -- <card>` + `--example lint_check`（主题可移植性）+ 负向快速检查 `OctoScript-AppCard/docs/tools/l0-lint.sh`。

可用 `sys.*` 能力封闭清单（32 个，`OctoScript/crates/octoscript-ui-l0/src/lib.rs`）：geocode、wiki、weather、daylight、airquality、moonphase、photo、locale、convert、gps、search、route、step、places、news、news_digest、dataset、quakes、movers、quote、series、watchlist、indicator、video、prefs、reading、topics、link、symbol_search、cities 等。**要新数据 = 能力层（Rust）或组队。**

### 路径 C：Rust 能力与内核（帝王蟹/大章鱼）

- 为场景新增 `sys.*` 数据能力：契约、权限、错误处理、限流、版本；"软件协作可接入 hagency"。
- 用 octos 做自己的 Agent 外壳：消费 OUP（WebSocket `/api/ui-protocol/ws` 或 stdio），能力发现走 `config/capabilities/list`。
- 用 OctoLoop 双环组织开发本身：`npm i -g @octos-org/octoscode` → `bash scripts/olp-init.sh` → 内环 GLM/Kimi 执行，外环强模型审查（这既是课程内容也是高效的开发方式）。

### 路径 D：OctoSense 桌面/ROM（大章鱼）

- 桌面：`python3 tools/setup-native.py && cargo run`（macOS 验证最充分；`--module appcard` 跑卡）。
- ROM：系统事件、权限、系统桥、跨应用协作方向；"ROM 突破：……单纯刷机或累计 PR 数量不直接构成突破"，需要"可复现的前后对照"。

### 5.5 官方参考架构：octo-weather「行程守护」设计蓝图（9/26 演示，强烈建议精读）

官方在开课日现场用 OctoLoop 双环做了一个参赛应用 `octo-weather`（天气场景），其设计蓝图（[repos/hackathon-official/docs/demo/2026-09-26/octo-weather-guardian.md](repos/hackathon-official/docs/demo/2026-09-26/octo-weather-guardian.md)）就是一份**对齐评审标准的模板**——任何场景都可以套用这个骨架：

**核心分工原则："模型写理解和方案，不写事实"**

| 环节 | 谁负责 |
|---|---|
| 解析自然语言计划 | octos agent |
| 地点坐标、预报数据 | **确定性代码**（真实服务取数） |
| 风险判定 | **确定性规则引擎**（不是让模型判断） |
| 方案与解释 | octos agent，**只能引用 app 提供的事实**（有防编造校验） |
| 执行 | app 内**白名单动作执行器**，用户确认后才执行 |
| 核验 | **确定性代码**：读回结果、重取数据复核 |

**蓝图自带评审对照**：任务完成（解析→方案→确认→执行→确定性核验）、可靠运行（显式状态机 + 9 类失败状态各有界面与恢复路径 + agent 不可用时降级为规则建议）、人机协作（每个数字标注来源与数据时间、不确认不执行、解析和方案都能手动修改）。

**工程要点**（全部来自官方踩坑）：
- 显式状态机（mermaid 画出全部状态与出口），竞态防护：每次 agent 请求带单调递增 `request_id`，迟到旧回复直接丢弃；点确认后按钮立即禁用。
- 防编造校验：先归一化（中文数字互转、"9 点"=09:00），豁免清单 + ±1 容差；数据类数值必须与事实比对；不合规回发同一会话修一次，仍不合规走规则兜底。
- 白名单动作全部幂等，执行前写审计日志；重复确认显示"已执行，未重复"。
- 开发切片化（G1 依赖/数据模型/状态机 → G2 取数/规则/兜底/防编造 → G3 接 agent → G4 界面 → G5 失败状态/跟进/重复测试），每片由外环在隔离 worktree 复验 + 亲眼看截图后才放行。
- 设计蓝图先过**异厂牌对抗评审**再开工（抓出防编造误伤、状态机缺出口、排期零缓冲等问题）。
- **三条最贵的教训**：① 截图自己看，不能只信 agent 的回报（ACK 描述比截图好 ×3）；② mock 测试全绿 ≠ 真实可用（G3 真实冒烟因事件格式 v2 失败，关键链路必须真实冒烟）；③ 诚实的"部分验证"比虚高的"已验证"有用。

**octos 集成现状的真实边界**（避免走弯路）：
- 生态里**只有 OctoSense-AppCard 接通了 octos**（四步零代码路径：构建 octos → `octos serve` + 令牌 → 写 `~/.config/octos-app/server.json` → `cargo run --features app-appcard -- --module appcard`；演示输入"深圳天气"生成实时数据卡）。
- **Rinx 与 octos 没有协议级集成**；Rinx 原生小程序是"宿主审定型 L0"（人写卡、编译进宿主），不是模型现场生成型。
- 生成流水线（一句话→卡）只存在于 AppCard：路由大脑 → 应用 agent（octos 会话）→ 三层校验（L0 checker / lint.json / 安全门，L0 最多修 3 次）→ 渲染。
- 值得做的集成缺口（≈悬赏方向）：让 Rinx 接上 octos（对应悬赏第 10 题）、octos agent 调用 OctoSense AI 总线上的应用工具、补齐 Rinx 的 `ServiceExecutor`（`Rinx/src/module.rs` 目前一律返回不可用）。

---

## 六、悬赏题目（13 道，已凑齐 ✚）

> 官方口径："悬赏是大章鱼层的选题，也可以是赛中的小贡献。以下为**蓝图中的建议题目**，难度、分值与认领入口将在赛前公布。" 普通应用**不强制**认领悬赏；贡献需说明对实际任务的改善，不按 PR 数量加分。
>
> 以下清单 = 官网 SPA 提取的 11 道 + 队友文档补齐的 2 道（第 1、2 道对应官网「扩展选题：robrix2 + hagency」小节），共 13 道，与页面宣称数量一致。

| # | 题目 | 说明 |
|---|---|---|
| 1 | **hagency 软件工厂小程序** | 为 hagency 做任务进度、Agent 状态、结果验收或交接 mini-app（在 robrix2 中运行） |
| 2 | **小程序能力与契约测试** | 为工厂小程序补充受限数据能力、状态回放或权限测试，并接回实际参赛应用 |
| 3 | **L0 Web Playground（头号悬赏/优先方向）** | 输入脚本实时预览卡片；若赛前已有 MVP 则转为体验增强 |
| 4 | **check-ui CLI 与 LSP 接入** | 把 L0 校验带进命令行与编辑器 |
| 5 | **错误码与修复建议** | 提供错误代码和可执行修复建议，帮助模型理解失败并自修复 |
| 6 | **结构化 lint 引擎** | 从子串匹配走向 OR、禁止与计数规则 |
| 7 | **跨仓库 schema 契约测试** | Octoscript 与 OctoSense 接口一致性自动检查 |
| 8 | **L0 解析器 fuzz** | 测试解析器边界，提高面对复杂输入时的稳定性 |
| 9 | **L1 规范撰写** | 把语言行为写成清晰规范（技术写作者可认领） |
| 10 | **UI Protocol 最小客户端** | 用 TypeScript/Python 把 Octos 接到手机之外的界面 |
| 11 | **协议 schema / typegen / conformance** | 完善 schema 导出、类型生成或协议一致性测试 |
| 12 | **new-skill 脚手架** | 简化 manifest 与注册流程，让新能力更容易起步 |
| 13 | **「生产回路 Agent」演示** | 读取自身运行指标、发现卡片失败、自动修复并重新发布 |

> 工具链类题目（4–9、11）与 `OctoScript`/`OctoScript-AppCard` 仓库直接对应，边用边贡献即可上手；题目 1–2 对应 hagency 选题（见第二章软件工厂专题）。

---

## 七、评分与评审

**评审维度表**（队友文档整理，与官网口径一致）：

| 评审维度 | 评审关注点 |
|---|---|
| 任务完成和可靠性 | Agent 是否真的完成了目标、能否重复运行、能否处理失败和恢复 |
| 用户控制 | 来源、授权、确认、修改、拒绝、执行反馈是否清晰 |
| 状态变化 | 执行前后是否有**可观察、可验证**的应用或设备状态变化 |
| 可复现性 | 其他人能否按启动说明运行、测试和复核 |
| 技术价值 | 平台/能力/协议/系统层改进是否被**自己的应用**使用，能否用前后对比证明效果 |

官方评审流程要点：

- **初赛海选**：独立评阅 + 运行核验 + 交叉复核 → 50 人晋级；用 10/4 冻结版本。
- **复赛**：材料评审（安装复现、任务验证）+ 10/12 线上分组答辩（3 分钟应用演示 + 2 分钟 Agent 自动化与可选技术贡献说明 + 问答）；统一复核评奖。
- **评分构成**（FAQ）：创意（意图到应用的想象力）+ 完成度（实际跑通）+ 技术深度（加分项，无资格门槛）+ **项目反哺**（可合并 PR、入库应用与能力、合格缺口 issue、采纳规范——"客观清单及分值赛前公示"）+ **可接续性**（"让下一个人接得住的 README/spec"；混合组队、跨队使用能力双方加分）。
- **最佳 Agentic 奖**：看意图覆盖、信息设计、美感、no-facts 遵守、spec 泛化（"让不同问法都能得到正确的卡片"）；应用层作品可直接争取。
- **最佳技术突破奖**：数据能力契约质量；组件/工具链/协议作品的深度与可合并性；ROM 突破（系统事件、权限、系统桥、跨应用协作）。要求"效果证据：版本、补丁、复现步骤与前后对照，同一成果不重复计分"。
- **技术进阶的前提**："先完成可运行、可验证的 Agentic 应用，再看项目反哺与 ROM 突破。"

---

## 八、提交清单（自查用，9/26 官方执行方案精确口径）

**初赛（10/4 23:59 前）**——官方原文："提交简短需求、可运行最小原型及启动说明、固定版本源码或包、2–3 分钟演示、**两张关键截图**、数据来源与限制、已报名成员名单。至少展示一次操作及可核对的结果，以及**一个失败或空状态**。静态概念稿本身不满足原型要求。"

- [ ] 简短需求说明（用官方练习包的一页任务模板：用户与场景/一句话意图/输入/数据来源/Agent 负责/用户负责/一个必要操作/操作后可观察结果/等待时显示/失败时显示/本次不包含的功能/完成证据）
- [ ] 可运行最小原型 + 启动说明（真机优先、桌面兜底；用赛前公布支持的设备与环境）
- [ ] 固定版本源码：**Apache 2.0 公开仓库**（各轮评审均以仓库为准）
- [ ] 宿主版本 + 提交号（Rinx 基线 = 宿主分支 + commit）
- [ ] 2–3 分钟演示视频 + 两张关键截图（一张正常操作结果、一张失败/空状态）
- [ ] 数据来源与限制（区分真实服务 / 明确标注的练习数据）
- [ ] 已报名成员名单（10/4 锁定；两个截止之间只整理已报名成员，不新增未报名者）
- 初赛评审方式：两名评委分别评价**需求与任务价值、核心流程可用性、数据来源与失败状态、复现与材料**，较大分歧第三人复核；**初赛不将 Rust 或 ROM 开发设为门槛**

**复赛（10/9 23:59 前，晋级的 50 人）**：完整应用、安装步骤、冻结版本、能力说明、正常与失败场景验证、**队外用户试用记录**、完整演示及已知限制。"区分参考卡、练习数据与真实在线结果，说明事件或意图输入、Agent 理解与计划、授权、执行、结果核验和后续状态处理；**只生成界面或摘要不足以证明完成任务**。" 技术突破参评另交 PR/补丁/接口/测试等贡献证据及前后对照（不要求评审前已合并）。

**10/12 线上决赛**：12:00 前交最终幻灯片、演示顺序、同版本备用视频（不得包装冻结版本中不存在的功能）。每项目 8 分钟 = **3 分钟应用演示 + 2 分钟 Agent 自动化与自选技术贡献 + 2 分钟问答 + 1 分钟切换**；两个并行组各最多 25 项，每组至少 3 名评委；17:30 向队伍提供评分明细、18:30 前收齐纠错说明、19:30 锁分、20:00 公布。网络故障时用同版本备用视频 + 实时问答。

**注意**：晋级"按人数统计，不是 50 支队伍"；奖项以团队为单位。App Hub 上架**不必须**（评审以公开仓库 + 可运行作品为准）。

**红线**：
- ❌ 只有创意/设计稿/视频 → 不合格（"创意必须通过可运行的开源代码实现"）
- ❌ 编造事实（no-facts 铁律；"不得编造状态、操作成功或执行结果"）
- ❌ 不注明数据来源、不区分练习数据与真实接入
- ❌ 平台/ROM 扩展不落到自己作品的实际改善上

### 「完成」的判定标准（队友文档整理，逐条自查）

> 一个合格的作品应该能让评审**从头到尾复现一项任务**，并看到 Agent 的输入、判断、授权、执行和结果。

- [ ] 有明确的用户、触发条件和目标
- [ ] 能说明 Agent 读取了哪些数据，以及数据来源是什么
- [ ] 能展示 Agent 提出的计划或动作
- [ ] 涉及重要操作时，用户可以确认、修改或拒绝
- [ ] 确认后**真的调用了**应用或系统能力
- [ ] 能够展示执行前后的状态变化
- [ ] 执行失败、被拒绝或确认过期时，**不伪造成功**，并给出可理解的反馈
- [ ] 有启动说明、测试数据、截图或日志，让其他人可以复现

官方给的完整任务示例（"邮件 → 日历"）：不能只停留在邮件内容摘要。完整链路 = 读取邮件 → 识别时间地点 → 提出创建事件的计划 → 等待确认 → 创建日历事件 → **读取日历验证事件已经存在** → 并处理缺少时间或用户拒绝的情况。

### 常见误解澄清（队友文档整理）

| 常见说法 | 准确理解 |
|---|---|
| "做一个聊天机器人就可以" | 不够。聊天只是入口，还要展示 Agent 对应用/系统能力的**实际调用和结果验证** |
| "Agent 可以直接控制手机的一切" | 不准确。Agent 只能调用已暴露、已授权、符合协议的能力，重要动作保留用户确认 |
| "只做底层组件就能参加技术突破" | 不够。技术改进必须服务于**自己的可运行 Agentic app**，并有前后效果对比 |
| "必须买 OnePlus 6 或刷 ROM" | 不需要。ROM 是可选的系统层深化路线，普通作品从 robrix2 和桌面环境开始 |
| "悬赏题目就是必须完成的任务" | 不一定。官网列为建议方向，普通应用不必须认领 |
| "视频可以替代程序" | 不可以。视频只辅助说明，不能替代可运行 Demo、源代码和启动说明 |

---

## 九、对本项目（你）的冲击计划建议（9/27 更新）

今天 9/27（周日），机制课最后一天，距初赛截止 7 天。倒排：

| 时间 | 建议 |
|---|---|
| 9/27（今天） | 上午课 octos × OctoLoop（10:00–12:00）、下午 Rinx × hagency（14:00–15:30）照常上；**16:00–17:00 可选工作坊"把课程变成自己的参赛计划"务必参加**——产出就是一页参赛计划（场景目标、Agent 分工、可用项目、完成标准）。晚上开队会定题，用官方练习包模板写出任务说明 |
| 9/28（周一） | 环境日：以课堂包锁定版本为准搭好 Rinx 构建与测试账号；写蓝图（套用 5.5 节 octo-weather 骨架）+ 找另一家模型做对抗评审；搭好 OctoLoop 双环与交付目录骨架 |
| 9/29–10/1 | 切片开发 G1–G3：数据模型与状态机 → 取数与规则引擎/防编造 → 接 agent 真实冒烟。**每片外环复验 + 亲眼看截图** |
| 10/2–10/3 | 切片 G4–G5：界面接入 + 失败状态/跟进/重复测试；10/3 参加官方答疑门诊抛出阻塞；让**队外用户**完整用一次并记录 |
| 10/4 上午 | 10:00–11:00 官方提交检查门诊；按初赛清单逐项核对；**23:59 前提交**（宁糙勿晚） |
| 10/5–10/9 | 按 10/6 反馈迭代同一作品（不换题）；补队外试用记录与测试证据；做技术贡献的整理 PR/补丁 + 前后对照；10/9 冻结 |
| 10/10–10/12 | 10/11 连线检查；排练 8 分钟答辩（3 演示 + 2 贡献 + 2 问答）；备同版本备用视频；10/12 决赛 |

**官方给的一条龙工作流**（课程文档原文，建议直接照做）：
1. 选定一个真实任务（12 场景之一，写清用户问题、输入来源、完成标准）；
2. 把目标交给 Agent（octoscode 中说明目标/可用项目/参考画面/可操作范围/完成标准，让 Agent 先复述任务和计划）；
3. 做出第一版并**亲自使用**（实际操作一次，记录状态、授权、执行反馈和结果）；
4. 让执行与审查分别发生（OctoLoop 双环：内环执行修正，外环观察独立检查；不把 Agent 的"完成"声明当作完成证据）；
5. 按场景组织协作（即时消息沿用 Rinx 界面；软件工厂题用 hagency）；
6. 比较改进前后的效果（队外用户试用，记录不能完成或需人工接管的地方）；
7. 整理并交付（可运行版本、源码、来源与限制、截图、演示和验证记录；Agent 帮整理材料，人核对真实性）。

**交付目录骨架**（官方练习包建议，直接用作参赛仓库结构）：

```text
my-entry/
  task.md             # 任务与完成条件（一页说明）
  app/                # 卡片或应用源码
  changes.md          # Agent 修改了什么，人检查了什么
  run.md              # 版本、启动方式、数据依赖、复现步骤
  evidence/
    normal.png        # 实际正常操作后的结果
    failure.png       # 失败或无数据时的实际界面
    checks.md         # 日期、环境、动作、结果、未执行项
  limitations.md      # 已知限制与后续工作
```

官方练习包还给了三个可直接抄的模板（[repos/hackathon-official/docs/courses/2026-09-26/workbook.md](repos/hackathon-official/docs/courses/2026-09-26/workbook.md)）：给 octoscode 的首轮指令模板（先复述理解→完成一个改动→核验实际结果→交付摘要与未执行项）、退回 Agent 的反馈模板（复现步骤/预期/实际/证据/允许修改范围/修复后必须重测原失败步骤）、一页验收记录表（6 项检查 × 通过/未通过/未测，"不要把可能通过写成通过"）。

**选题策略提示**（基于调研的判断，供参考）：
- 初赛 7 天且用冻结版本评审"可运行性"——**跑通的任务闭环 > 功能数量**。失败状态、权限拒绝、过期状态是评分口径里反复出现的验收点，实现时预留。
- 官方演示选了天气场景并做到了"行程守护"这个深度——说明**天气场景上限不低**（关键在于守护式任务闭环，不是信息卡）。邮件→日历链仍是官方钦定的"完整任务"标准示例。天气 + 出行计划（octo-weather 同方向）的取数是公开服务（Open-Meteo），不依赖未发布的能力，**复现性最好**；做消息/邮件题则要自建 Palpo 测试数据源。
- 技术形态：Rinx 网页卡片路线门槛最低（可运行页面 + URL 卡片交付）；Rinx 原生扩展需要改宿主源码（工程量大但"Agentic 含金量"足）；独立 Makepad 应用（octo-weather 路线）介于两者之间且官方已验证可行。混合策略：核心交互用 L0 卡/独立应用 + 事件入口与结果回写走宿主。
- 悬赏题里"check-ui CLI/LSP、错误码自修复、生产回路 Agent"与开发工作流天然协同，边用边贡献。

**已知风险**：
- 本机（WSL2）GitHub 直连 git clone 超时（本次调研改用 codeload tarball 解决）；正式开发需要 git 历史（尤其 Rinx 宿主分支提交），建议配代理或镜像后 `git clone` 一遍。
- 平台成熟度：Rinx 的原生验证记录在 macOS（arm64 隐藏窗口 + Palpo 隔离账号、未加密私聊）；加密会话、iOS、移动端执行是"需单独验证"项。**Rinx 钉 Rust 1.98.0**（rust-toolchain.toml 会自动拉取）。Linux/WSLg 桌面理论上可用，第一天就验证。
- 版本锁定：一切以 9/24 发布的课堂环境包为准；官方明确"不混用各项目的最新 main"、"不能以 git pull 完成作为二进制升级证据"。AppCard 期望 octos 0.x/1.x，连 2.0 服务端会有版本告警但会话正常。

---

## 九点五、环境就绪状态（9/27 12:50）

| 组件 | 状态 |
|---|---|
| Rinx 编译 + 冒烟 | ✅ WSL2/Wayland 首次验证通过（官方仅 macOS 记录） |
| 本地 Palpo + PG17 | ✅ http://127.0.0.1:8128 运行中；测试账号 ×2 已验证登录 |
| OctoScript check_card | ✅ 已编译，写卡校验闭环可用 |
| my-entry/ 交付骨架 | ✅ task.md / blueprint.md / changes.md / run.md / evidence/ / limitations.md |

详见 [本地测试环境.md](本地测试环境.md)。

## 十、本目录结构

```
Agentic-octos/
├── 比赛调研报告.md          ← 本文档
├── repos/                   ← 仓库快照（tarball 解压，无 .git；git 直连超时所致）
│   ├── hackathon-official/        ★ 官方比赛课程/演示仓库（赛程/讲稿/练习/蓝图）
│   ├── Rinx/                      ★ 本届主要小程序宿主（9/26 HEAD，WeChat 风格 + Moments）
│   ├── robrix2-compete-05daf9b/   Rinx 的 9/21 比赛核查基线快照
│   ├── robrix2-old-snapshot/      robrix2 main 旧快照（SPLASH.md 等本体文档）
│   ├── OctoSense-Desktop/         桌面宿主（9/26 HEAD）
│   ├── OctoSense-Desktop-old-snapshot/  9/25 快照（原名 OctoSense）
│   ├── OctoSense-System-Apps/     ★ 第一方系统应用（appcard/mail/maps/news/photos/camera）
│   ├── OctoScript/                Octoscript 语言 + L0 规范 + 能力清单（9/26 刷新）
│   ├── OctoScript-App-Design-Flow-old-snapshot/  原 OctoScript-AppCard（a2app-l0 写卡框架等）
│   ├── OctoScript-Makepad/        主题 kit + 渲染管线
│   ├── OctoSense-App-Hub/         应用上架（本届不必须，参考其规范做预检）
│   ├── octos/ octoscode/ octos-book/   Agent 内核 / 终端 agent + OctoLoop / 21 章书
│   ├── hagency/ herdr/            软件工厂 / agent 终端运行时
│   ├── makepad/                   Rust GPU UI 框架（apps/weather 完整天气 app、--remote 接口）
│   ├── OctoSense-ROM/             OnePlus 6 ROM（可选进阶）
│   └── …（其余见第四章表格）
└── research/                ← 调研原始材料
    ├── 比赛页面全部文案-i18n提取.txt   （492 条中英对照，含 FAQ/课程/评分全部原文）
    ├── octosense官网-12场景指南全文.txt（12 场景 + 4 交互体验页全文）
    ├── OctoSense-org组织理念README.md
    ├── 队友材料-比赛统一理解版.docx / -提取.md
    └── （旧文件名 robrix2 相关目录已按更名对照表重命名）
```

> 注：repos/ 内均为 tarball 快照（保留内容、无 git 历史）。正式开发前建议自行 `git clone`（本机 GitHub 直连超时，可走代理/镜像），并把 `robrix2` 切到比赛发布包指定的锁定版本（9/24 发布，课程群内获取）。
