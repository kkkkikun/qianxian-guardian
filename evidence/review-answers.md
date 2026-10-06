# hub scan 7 问作答（qianxian 0.1.0，2026-10-06 复赛版刷新）

> review 包：`build/review.json`（`hub scan bundle --packet build/review.json` 产出）。
> 本版 digest `743c1a7f…`（初赛冻结后按晋级反馈持续开发：AI 建议卡 / 回执风格 /
> agent 摘要 / capability 可见性 / 「红线」UI 重构 / 详情视图重构）。
> 真机验证：card-host（App-Hub `46d67e5` 自建链），回归 14/14（`evidence/regression-48-20261006.md`）。

## 1. 名实相符？

是。名 `牵线`、副标题"群里说好的聚会，盯到人人到场、账目清零"。
源码对应：`add_case()`（建守护）→ `confirm_case()`（组织者拍板→Confirmed）→
`reschedule_case()`（改口）→ `cancel_case()`（取消留历史）；`storage` 持久化
`cases.json`（同目录 `pref.json` 偏好、`agent-brief.json` agent 摘要）。
真机 `/snap` 实测：建卡/冲突徽章/详情/回执四行/AI 建议卡/风格切换全部在屏（回归 14/14）。

## 2. 平台与分类？

合适。`platforms: ["linux"]`——仅写在 card-host 实测过的平台；
`category: "productivity"`——聚会组织是生产力事项。不多写未测平台。

## 3. 权限与所见功能匹配？hosts？

匹配，无多余。`grants: capabilities {"octos.turn.start", "storage"}, hosts {}`，
agent `workspace-write`（仅对话，`tools: []`——agent 只能就 `cases.json` 状态问答，
无任何读写工具）。
- `storage`：`fs.write("cases.json")` 守护列表 + `pref.json` 回执风格偏好 +
  `agent-brief.json` 状态摘要，均可在 jail 目录实读。
- `octos.turn.start`：仅"AI 解析"用。先 `host.has("model")`/`host.has("octos.turn.start")`
  探测（capability 行常驻可见），请求失败快速降级本地规则并在屏上如实改写
  "AI：通道实测无响应，本地规则兜底"——**"已注册"与"有活后端"的差距对用户可见**。
- `hosts: {}`：无 `net`，不请求任何外部主机。

## 4. 欺骗性界面？

无。无系统弹窗仿冒、无支付单、无登录表单（`secrets` 项通过）、无品牌仿冒。
模型文本纪律：AI 输出只进文本槽（建议卡汇总/回执），按钮全部静态绑定——
符合官方 AI-SERVICES "Words fill text slots; Actions never" 约束。

## 5. 对助手的指令注入？

无。AI 调用只传用户输入框原文（`model.complete` schema 四字段首选 /
`octos.turn.start` 降级）；本机无服务时请求根本发出后失败即降级，LLM 不碰状态机
（解析结果先渲染"✨ AI 生成"建议卡，用户点「采纳到输入框」才写回，人主动）。

## 6. 辱骂/针对私人？

无。全部文案为中性操作反馈；测试消息为合成（"周六上午去深圳湾骑车"），无真实个人信息。

## 7. agent 文件（agent_files）越界？

未越界。`AGENT.md`（2033 字节，纯文本 UTF-8）自我申明的边界与实现一致：
**只按 `cases.json` 状态对话/问答**（活动/时间/地点/参与人/AA/回执完成度），
不读写 app 之外任何文件（manifest `agent.tools=[]`，hub 对 contained app 不开放
工具调用），不调度别的 app（store app 走 peer），不能自驱（无 needs/triggers），
不代替用户操作（所有变更走 splash UI 由人触发）。它引用的 `agent-brief.json`
是 app 自己写的状态摘要（同一数据 jail 内），无任何外部主机或指令源。
agent 数据全部留在本 app 的存储 jail 内（`<app-data>/qianxian/`）。

## 8. 路由

**pass**。`hub check — PASSED`（digest `743c1a7f…`；发布者签名 key-id `aurora-x`，
`--publisher-key` 验签通过，App-Hub `78dfda5` / contract 1.3.0 门禁含结构化准入：
PNG/SVG 可解码、listing 图标方形、manifest 精确字段——agent 文件经新规则显式声明
`agent.instructions: "AGENT.md"`）。
截图说明（诚实标注）：`bundle/screenshots/` 三张（均 412×892）：`01-main.png` 主界面
（筛选+冲突徽章）、`02-expanded.png` 详情+确认回执四行、`03-conflict.png` 失败/冲突态
（两条同时段，双「! 时间冲突」警示行，对应官方"数据来源与失败状态"要求）。
**不是宿主渲染的像素**——本评审环境 `/g` 抓帧超时（llvmpipe 无 present），图由
`tools/snap-to-png.py` 依据应用运行时真实控件树（`/snap?all=1` 类型/文本/矩形）
重绘：文字、层级、坐标、状态语义色均来自实际运行，不是设计稿。渲染器配色与
「红线」UI tokens 同源（#48）。评审在有图形会话的机器上跑
`tools/octo shot` 可得宿主像素图。
