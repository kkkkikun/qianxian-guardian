# WP4 · mail.review_send 真实邮件链证据

> 验证级别：**partially-verified**——集成路径 + 否定用例 verified（回归 R-38）；
> 真实发送 **unverified（平台阻断，官方在案）**：物理审批仅 macOS tap/Android 支持，
> Linux/Windows 按设计不可用（architecture.md §5 + public_review.rs:
> "Physical Mail send approval is unavailable on this platform"）。

## 契约核查（2026-10-13 最新上游源码）

- 跨 app 调用：`mail.review_send` 接受非 Mail 应用调用 → `public_review::open`
  （mail/host-service/src/lib.rs:878）——宿主评审面板，物理确认才发。
- agent 只能 `mail.propose_send`；`mail.send` 一律 `approval_required`。
- 参数：`{account, to, subject, body, compose_id?, expected_revision?, folder?, message?}`。
- 平台边界：review 面板仅 macOS/Android；Linux/Windows 不可用（如实降级）。
- 任务书的「mail.review_send」与现行 API 同名在案。

## 实现

- 催收四段式草稿（draft_dunning 拍板组稿，数字代码算、永不公示名单）→ 聊天视图
  「邮件人审发出催收草稿」按钮 → `mail_review_send()`。
- 结案回顾卡：「分享回顾到群」并列新增「邮件回顾（人审）」→ 同文案走邮件通路
  （`fin_report_body()` 组稿抽出，两通路同文）。
- `mail_review_send(subject, body, tag)` 统一助手：`to` 留空不编造地址（收件人由人
  在宿主评审面板填）；无服务/平台不支持 → 真实错误透出 + 文案回输入框可手动发。
- manifest +mail 能力（app-contract manifest.rs:106 在册；hub check PASSED）。

## 验证

- 否定用例（R-38 回归在案）：card-host 无邮件服务 → 点击后 hint 透出「无邮件服务」
  真实文案 + 文案回输入框兜底。
- 真发送：本机 Linux 平台按官方设计不可行（上引）；macOS/Android 宿主待真机。
