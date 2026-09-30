# hub scan 7 问作答（qianxian 0.1.0，2026-09-30）

> review 包：`build/review.json`（`hub scan bundle --packet build/review.json` 产出）。
> 真机验证：card-host（App-Hub `46d67e5` + makepad `db4691d0` + OSM `3d3ef80` 自建），
> `/snap` 实测 11 个文本控件。

## 1. 名实相符？

是。名 `牵线`、副标题“群里说好的聚会，盯到人人到场”、描述“把群里一句聚会意向认领为守护（Case），
组织时间收敛……只有组织者能确认……无 AI 也完整可用”。
源码对应：`main.splash` `add_case()`（建守护）→ `confirm_case()`（组织者拍板→Confirmed）
→ `reschedule_case()`（改口回 Proposing）→ `cancel_case()`（取消留历史）；
`storage` 持久化 `cases.json`；`triage()` 未命中显示澄清卡。`/snap` 实测：
标题/输入框/建守护/“已建守护 #1（分诊命中：time）”/`#1 · 骑车 · Proposing` 全在。

## 2. 平台与分类？

合适。`platforms: ["linux"]`——仅写在 card-host 实测过的平台；
`category: "productivity"`——聚会组织是生产力事项。不多写未测平台。

## 3. 权限与所见功能匹配？hosts？

匹配，无多余。`grants: capabilities {"octos.turn.start", "storage"}, hosts {}`。
- `storage`：`fs.write("cases.json")` 存守护列表，界面“已载入 N 个聚会守护”即其呈现。
- `octos.turn.start`：仅“AI 解析（可选）”按钮用；`main.splash` `ai_parse()` 先查
  `host.capabilities()`，card-host 下走“本设备无 AI 服务……本地规则继续可用”降级分支。
  商店权限行会如实显示该项，用户知情。
- `hosts: {}`：无 `net`，不请求任何外部主机。屏幕上无任何项用不到已授权限。

## 4. 欺骗性界面？

无。无系统弹窗仿冒、无支付单、无登录表单（`is_password` 等秘密字段零出现，
`hub check` `secrets` 项通过）、无品牌仿冒。三个操作按钮文案即其效果
（同意/改口/取消），取消/改口均有 hint 回执。

## 5. 对助手的指令注入？

无。`main.splash` 无 SYSTEM/role 提示词残留；AI 调用只传用户在输入框里 typed 的原文
（`octos.turn.start {text: "从这条聚会消息提取活动/时间/地点，只回 JSON：" + text}`），
且该调用在 card-host 下根本不发出（降级分支）。群消息只做事实输入，
`triage()` 用本地正则，不改变任何规则。

## 6. 辱骂/针对私人？

无。全部文案为中性操作反馈（“已确认/已取消/澄清卡”）；测试消息为合成
（“周六上午去深圳湾骑车”），无真实个人信息。

## 7. 路由

**pass**（待换真截图后）。publisher 三字段已换真值（Aurora-X /
kkkkikun@foxmail.com / 公仓 PRIVACY.md 链接），`hub check — PASSED` 无占位提示
（digest `fdcae9bb`，privacy 链接分支修正后重检）。截图说明（诚实标注）：`bundle/screenshots/01-main.png`（412×892）**不是宿主渲染的像素**——
本评审环境无图形会话，card-host 的 `/g` 抓帧超时（llvmpipe 无 present）。
该图由 `app/qianxian/tools/snap-to-png.py` 依据**应用运行时的真实控件树**
（card-host `/snap?all=1` 的类型/文本/矩形）重绘而成：
文字内容、层级顺序、坐标、状态语义色均来自实际运行，不是设计稿。
若评审在有图形会话的机器上运行 `tools/octo shot <port> bundle/screenshots/01-main.png`，
会得到宿主渲染的原始像素图。
（`/g` 在 llvmpipe 无头后端抓帧超时，`snap` 树 11 控件验证通过）。
真图替换后重 `stamp`+`check` 即可提交；功能与权限侧无问题。
