# WP3 · 守护灯速览卡（AppCard / glance）证据

> 验证级别：卡源 **verified**（官方 check_card valid=true, level=L0）；发布动作
> **partially-verified**（card-host 无 glance 服务——载荷 Outbox 落盘断言真实，
> 上屏待真宿主/桌面）。

## 契约核查（源码级，2026-10-13 最新上游）

- 现行服务：`glance.publish / withdraw / list`（crates/shell/src/glance.rs）；
  发布者身份由 shell 从调用方取（不可伪造），每 app 6 次/分钟。
- 卡内容契约：`card_id` + `title` + L0 `source` + `data`（或 template+initial）；
  agent 卡**禁止可执行 Splash**（host_tools/script_apps.rs `check_agent_publication`，
  L0 校验由 octoscript_ui_l0 强制执行）。
- `sys.dataset` 是**封闭字段集**（title/subtitle/summary/coverage/status/as_of/metric*/pick*/url*/evidence*）
  ——自定义字段被拒（实测定版）。

## 实现

- app 内「发布到 glance 屏」→ `publish_glance()` 重写为现行契约：
  card_id=guard-light、L0 卡源（牵线守护灯：标题=守护中·共 N 条，指标=待拍板/冲突，
  副题=待收尾，摘要=确定性与「无异常」如实文案），open app://qianxian。
- **数据源与守护灯同一处**（rebuild_lines 的确定性计数，零模型参与）。
- **证据 Outbox**：发布载荷先写 jail `glance-last.json`——无论宿主有无 glance 服务；
  无服务时 hint 明示「未上屏，载荷已存」（不假装）。

## 留证（命令 + 输出）

```sh
# L0 卡源官方校验（repos/OctoScript，pin 内）
cd repos/OctoScript && cargo run --release -p octoscript-ui-l0 --example check_card -- /tmp/guard.card
# 输出：valid = true  level = L0        （2026-10-13 实跑）

# 回归
python3 app/qianxian/tools/qx-verify-v2.py   # R-37 全绿（载荷一致性+契约字段）
```

## 诚实边界

- 上屏渲染未验：card-host 无 glance 服务；桌面/Rinx 真宿主验收待桌面构建
  （本机 rust 1.96 升级已就绪，shell 重建中）。
- `notify: false`：守护灯卡是常驻语义，不弹通知打扰。
