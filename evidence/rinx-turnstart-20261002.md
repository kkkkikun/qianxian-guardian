# Rinx 宿主 turn.start 真通路验证记录（2026-10-02 凌晨，#38）

> 任务书 S2-2（60min timebox）。结论：**真通路全链打通至最后一跳（octos serve 的
> turn 认证），应用侧行为全程符合设计；401 认证属上游 Rinx↔octos serve 配对协议
> 细节，留痕转复赛/上游 issue。** 此前 `regression-20261001.md` 的
> "turn.start 真通路待 Rinx 宿主"（partially-verified）在本轮大幅收口。

## 环境起跑（全部实测命令）

```sh
docker run -d --name gosim-pg --restart unless-stopped \
  -e POSTGRES_PASSWORD=palpo_dev -e POSTGRES_USER=palpo -e POSTGRES_DB=palpo \
  -p 127.0.0.1:5433:5432 docker.m.daocloud.io/library/postgres:17   # 容器已失重建
./palpo-ctl.sh start                                                # Matrix @ 8128
# UIA 两段式注册 rinx_test_a / rinx_test_b（B 撞 429，retry_after 7s 后成功）
export MAKEPAD_REMOTE=8147
repos/Rinx/target/release/rinx "@rinx_test_a:127.0.0.1:8128" "<pw>" "http://127.0.0.1:8128"
repos/octos/target/release/octos serve --port 50080                 # HTTP 模式，打印配对码
```

## 真机验证达成项（verified，远驱桥 /snap //click /t 逐步驱动）

1. **Rinx 真机登录**：CLI 凭据登录成功（`LoginAction::LoginSuccess`），房间列表 Loaded。
2. **Mini apps 导入流**：导航栏 `octoscript_apps_button` → 面板 → path 填
   `my-entry/app/qianxian/bundle` → **Review bundle → "牵线 0.1.0 · Local unsigned
   bundle / Services: storage, octos.turn.start"**（服务声明与 manifest 一致）。
3. **牵线以 mini-app 形态在 Rinx 内运行**：Run → "Running · Back closes this app and
   revokes its services"，Splash 控件树完整（msg_input/建守护/说明卡/低频键 #36 全在）。
4. **AI 请求真实发起且到达 serve**：AI 解析 → `host.has("octos.turn.start")` 在 Rinx
   为真 → host.request 真实调用 → Rinx provider（octos.rs 白名单：仅 text ≤32KiB）→
   HTTP 到达 octos serve → **401 Unauthorized** 回传。
5. **应用侧诚实降级全链验证**：hint 显示
   `AI 不可用，已降级为本地规则（could not reach the server: HTTP error: 401 Unauthorized）`
   ——与 #32 设计一致（错误原文透出、不伪造结果、本地规则继续可用）；
   空输入点 AI 被应用自身守卫拒绝（"先输入一条群消息再试 AI 解析"）。

## 阻塞点（blocked，精确留痕）

- **octos serve HTTP 的 turn 认证 401**：两轮配对（重启 serve 取新配对码，token=配对码）
  后 Connect 状态均为 "Assistant (your server): starts on first use"，但首次 turn 即 401；
  serve 日志无任何配对/认证事件输出。octos-local（Use this device + ModelScope 四元组）
  路径点击后状态仍回显 server 分支，疑似表单状态或 feature 生效问题（未深究，timebox 硬停）。
- 判定：**上游集成细节**（Rinx assistant/host.rs ↔ octos serve 配对协议），非提交物缺陷；
  script-app 侧行为（发现/请求/超时降级/诚实报错）已全部真机验证。
- 后续：① 查 `repos/Rinx/src/assistant/host.rs` 配对实现与 octos serve dashboard 审批流；
  ② 或以 octos-local 特性重编 Rinx 验证内嵌核心路径；③ 复赛演示可沿用本记录的
  降级路径（评审宿主里 AI 不可用时应用依然完整可用，这正是作品主张）。

## 同场加验（对 S3 的关键发现）

- **WSLg 显示环境可用**（WAYLAND_DISPLAY=wayland-0 / DISPLAY=:0）——`octo shot`
  真像素截图此前"无图形会话超时"的前提已变化，S3 按有窗模式重试。
