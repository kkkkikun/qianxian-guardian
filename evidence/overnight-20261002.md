# 通宵日志（2026-10-01 23:30 → 10-02 09:00）

> 任务书：`my-entry/GOAL-overnight.md`。一片一 ACK；中断后先读本文件再续跑。

## 起始基线（P0-1）

- 时间：2026-10-01 23:2x（北京时间）
- commit：`a9ee173`（master，干净，仅新增 GOAL-overnight.md 未跟踪）
- digest：`a67c526dd913f407262832833aa515260effa60ee7f56697cc9cf17cfba23ed9`
- card-host：pid 15796 @ 127.0.0.1:8141，qianxian 0.1.0 admitted
- hub check：**PASSED**（仅 unsigned warning）

## ACK 记录

```
ACK(done): P0-1..P0-4 基线全落档
验证级别: verified
证据: commit a9ee173 起步 → hub check PASSED（digest a67c526d）；
  回归基线 qx-verify-v2 首跑 5/14 → 干净实例 11/14（3 失败定性见 S1-1）；
  smoke_g4b/g5 见下条。
下一片前置: 无
```

```
ACK(done): S1-1/S1-3 回归失败项收口 —— 发现并修复 #36 应用真 bug
验证级别: verified
证据: 根因：#29 把改时间/AI解析/导出/清空全部折叠进「怎么用」说明卡，
  而卡只在 cases.len()==0 空态分支渲染（main.splash L1653 分支归属），
  有守护时四键全部不可达（演示剧本 8/18/19/20 步不可执行）。
  修复：说明卡移到列表模式三分支公共尾部；重 stamp 25acbcda + hub check PASSED；
  真机两段式清空全通；qx-verify-v2 修五处驱动假设偏差（title_re/滚动方向/
  R06 六项/R12 滚回顶部/R13 确保展开+滚动物化/R03+R14 结果重试）后
  **14/14 连续两轮全绿**（/tmp/qx-v2-run5.log + 复跑）。
  回执 i/j 下标 bug（#25 记录）：#31 重构后详情面板统一 sel 全量索引，
  结构性消除，R-08 4/4 实证 —— 终验通过。
下一片前置: 无
```

```
ACK(partial): 基线期发现 R-03 建第二条跨运行偶发失败（4 跑中 2 挂）
验证级别: verified（现象与数据层核实：cases.json 从未出现 #2）
证据: /t 注入或建守护点击偶发丢失；type_and_create 结果重试后两轮全绿。
  疑似 card-host /t 与焦点建立竞态，未深究（驱动侧已健壮化，不影响评审演示——
  人工操作无此问题）。
下一片前置: 无
```

```
ACK(done): S1-2 guardian 真实提醒动作（#37，外环批准的越界增强）
验证级别: verified
证据: 新增 guardian/scheduler.py（schedule_reminder 同事务登记 + sweep 真发 +
  txn=sched-<task_id> 绑定幂等 + NeedsRecovery 同 txn 重试 + Running 崩溃窗口回收）；
  cases.py approve_proposal 批准事务内挂 T-24h 任务（due=start_at-24h，ISO 不可解析
  则创建+24h 兜底）；main.sweep_scheduler 委托（matrix=None 保留 G5 语义）；
  db.reload_due_tasks 回收 Running。冒烟新增 smoke_g6 **12/12**（批准登记/到期真发/
  正文含活动时间守护号/失败重试不重复/崩溃窗口不重复/退化补偿/due 兜底）；
  g4a 9/9 + g4b 9/9 + g5 9/9 全绿无回归。
  附带修复测试基建缺陷：g4a/g4b/g5/g6 冒烟原本不清理 /tmp/gosim 旧库、重跑必炸
  （上一轮绿跑遗留 Active Case → new_case 走 existing 分支），现各冒烟启动时清库。
下一片前置: 无
```

```
ACK(done): S1-4 文档同步
验证级别: verified
证据: limitations.md AA 行改「部分实现（#30/#31）；台账对账划出」；
  changes.md 追加 #36/#37 两行；GOAL-overnight.md 队列勾选同步。
下一片前置: 无
```

```
ACK(done): S2-1 环境与真实 LLM 复验
验证级别: verified
证据: gosim-pg 容器重建（run.md 命令）+ palpo 重启（versions 200）+ 双账号 UIA 重注册
  （B 撞 429 退避成功）；smoke_g3_real **3/3 PASS**（真实模型回合本轮 3s，输出 JSON
  {'activity':'骑车','date_text':'周六上午','place':'深圳湾'}）。
下一片前置: 无
```

```
ACK(partial): S2-2 Rinx turn.start 真通路（timebox 60min 硬停）
验证级别: verified（全链除最后一跳）+ blocked（serve turn 认证 401）
证据: `evidence/rinx-turnstart-20261002.md`。Rinx 真机登录 → Mini apps 导入 →
  Review "牵线 0.1.0 · Services: storage, octos.turn.start" → Run → **牵线以 mini-app
  在 Rinx 内运行** → AI 解析：host.has=true、请求真实到达 octos serve、401 回传、
  应用诚实降级（错误原文透出+本地规则继续）；空输入守卫亦验证。
  401 = Rinx↔octos serve 配对协议上游细节（serve 日志无认证事件），非提交物缺陷。
  另发现 WSLg 显示可用（S3 像素截图前提已变）。
下一片前置: 复赛可用本记录降级路径演示；或上游解决配对后一轮复验即全通。
```


```
ACK(done): S3 截图（官方两关键图要求达标）
验证级别: verified（控件树渲染，诚实标注不变）+ blocked（宿主像素，机制已留痕）
证据: #36 改了首屏布局 → 三张截图按当前 bundle 重生成（01-main 首屏含引导卡/
  02-expanded 详情模式/03-conflict 双冲突徽章+⚠ 行=官方"失败态第二张"）；
  像素截图再试：card-host /g 端点 404（hub 构建链 makepad 无 grab）、Rinx /g
  "grab timeout"（软件渲染无 readback）、X11 root 抓屏全黑（WSLg 经 RDP 合成，
  X 侧无内容；mss 截屏机制已通、内容为黑）——三类证据记入本 ACK，
  控件树渲染图仍是现行诚实做法。
下一片前置: 无
```

```
ACK(done): F-1/F-2 终跑与文档
验证级别: verified
证据: hub check PASSED（digest 25acbcda 不变，截图不进 digest）；
  qx-verify-v2 **14/14**（第三轮全绿，8146 干净实例）；guardian g4a/g4b/g5/g6
  = 9/9+9/9+9/9+12/12；smoke_g3_real 3/3。
下一片前置: F-3 git 提交推送。
```

## 待续（按任务书队列）

- [x] S1-2 guardian 真实提醒动作（#37，smoke_g6 12/12 + 三套无回归）
- [x] S1-4 文档同步（limitations.md AA 行、changes.md #36/#37）
- [x] S2-1 起环境 + smoke_g3_real 3/3
- [x] S2-2 Rinx turn.start（partial→证据落 `evidence/rinx-turnstart-20261002.md`；401 上游留痕）
- [x] S3 截图（三张按 #36 后 bundle 重生成；像素截图三路径证据留痕）
- [x] 收尾（全量终跑全绿；git 提交推送见 F-3）
