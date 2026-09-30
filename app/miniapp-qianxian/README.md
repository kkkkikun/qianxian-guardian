# 轨 2 Spike：「牵线」mini-app（Rinx host services）【已归档：被 ../qianxian 取代】

> ⚠️ **A 路线（2026-09-30）**：提交物是 `../qianxian/`（官方 script-app 形态，
> `hub check — PASSED`）。本目录是 G2.5 时期验证 Rinx host-services 可行性的 spike，
> 保留作设计证据，不再更新、不进提交包。
>
> 目的：验证 script-app 提交形态的可行性（blueprint-gpt.md 附录 A 轨 2）。
> 本 bundle 是 G2.5 spike——一个屏幕证明全链路：Matrix 身份 → Octos 会话 → 消息解析(JSON)。

## 文件

- `manifest.json` — 声明所需能力（matrix.profile/read_messages/send_message + octos.* 四能力）
- `main.splash` — 官方 `main.splash` bundle 格式（照 `Rinx/examples/miniapps/matrix-octos-script` 惯用法）

## 运行（Rinx 最新 main，含 PR #28 assistant-executor）

1. 确认 Rinx 已构建：`repos/Rinx/target/release/rinx`（本次 main `a72e4b00`）
2. 启动 Rinx 并登录 Matrix（本地 Palpo `http://127.0.0.1:8128`，账号见 `../../test-accounts.json`）
3. 侧栏选 **Mini apps**（桌面）或 **Discover → Mini apps**（移动）
4. Assistant provider 设置：
   - OctoSense 托管形态：shell 自动提供（ADR 0007），provider 在 OctoSense Settings → AI providers
   - 独立 Rinx：assistant 设置里选 **Use this device**（用可执行文件旁打包的 `octos`）或填 Octos server URL/profile/token
5. 输入本目录完整路径 → **Review bundle** → 核对声明的能力 → **Run**
6. 依次点：读取 Matrix 身份 → 打开 Octos 会话 → 粘贴群消息 → 守护解析

## Spike 通过标准

- [ ] Matrix 身份读取成功（broker + room grant 生效）
- [ ] Octos 会话打开（host-owned kernel 或独立 Rinx 本地 runtime）
- [ ] 真实模型回合返回 JSON（配 provider 后）
- [ ] 拒绝授权时显示明确失败（不伪造结果）

四项全过 → 提交形态可切轨 2（script-app）；任一失败 → 保持轨 1（独立 guardian，官方演示同款），两轨共享同一套业务设计（`guardian/` 目录的 Case/分诊/校验代码原样迁移）。
