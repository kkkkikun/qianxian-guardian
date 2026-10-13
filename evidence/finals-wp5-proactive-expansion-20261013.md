# WP5 · 主动回合扩场景证据

> 验证级别：**verified**（守护进程 jail 级驱动，两条新主动回合各真跑留证 +
> 沉默留痕对照；回归 R-39/R-40 全绿）。模型零参与（纯模板组稿，数字代码算）。

## 新增两类主动回合（qx-proactive-butler.py 同循环、同幂等标记纪律）

1. **临期催拍板**（WP5-B）：T-24h 仍 Proposing → 写 pending_plan.json
   （trigger=proactive_nudge，PLAN{"op":"confirm","id":N}）——从「被问才说」升级为「到点主动说」。
2. **梯度催收主动化**（WP5-A）：活动日后 T+1/T+3/T+7 + 有账未清（Confirmed/Completed）→
   写 pending_plan.json（trigger=proactive_dunning，tier 标记，PLAN{"op":"draft_dunning","id":N}，
   差额 ¥ 由 payments.json 代码算出）；拍板后走 WP4 的 matrix/mail 通路发出。
3. **沉默纪律**：不在窗口 → suppressed.json 记「为什么不醒」（dunning_not_due，
   每条 case+天一次，幂等不刷屏）——可回看可审计。

## 留证（本轮真跑输出）

```
[proactive] #1 临期催拍板提案已写     → pending_plan.json PLAN confirm
[proactive] #1 催收提案（T+1）已写    → pending_plan.json PLAN draft_dunning，差额 ¥200.00（300-100 代码算）
suppressed.json: dunning_not_due 在案（活动当天未到期对照）
```

## 边界

- 提案卡单槽契约：有未消费提案时守护进程不覆盖（下轮再写）——app 拍板/放弃即消费清除。
- target_date 优先于 slot_day 推导（绝对日期地基在案）；只有相对词的未来守护不参与催收窗。
- 天气主动回合（WP4 既有）不受影响：Confirmed+T-24h 专属，互斥不串。
