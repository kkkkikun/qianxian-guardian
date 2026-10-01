# GOAL-overnight：通宵冲刺任务书（2026-10-01 23:30 → 10-02 09:00）

> **用法**：这是给任何执行 Agent（ZCode / octoscode / octos goal）的自包含提示词。
> 中途停下后，新 agent 直接读本文件即可续跑：任务队列带复选框，完成的打 `[x]`，
> 进行中的写半行状态，**先读 `evidence/overnight-20261002.md`（通宵日志）再动手**。
> 常驻总纲 `GOAL.md` 与冻结蓝图 `blueprint-gpt.md` 继续有效；本文件与其冲突时以总纲为准。

## 角色

你是「牵线」项目的**内环执行工程师**（通宵班）。外环（用户）已批准本任务书并授权
一项越界增强；其余严格冻结。所有结论必须带可复现证据（命令 + 输出 + 文件），
回报格式见文末。**外环不在场：不要等待确认，按预案降级并留痕，继续推进。**

## 使命

按三步走完成初赛冲刺（截止 **2026-10-04 23:59**），一切服务于：一个好用的
Agentic 应用 + 完美达成比赛目标。时间盒（以实际开始时间顺延，比例不变）：

| 段 | 窗口 | 内容 |
|---|---|---|
| P0 | 23:30–00:00 | 基线与准备 |
| S1 | 00:00–02:30 | 软件基础功能 |
| S2 | 03:00–05:00 | octos 联通 + Agentic（02:30–03:00 休息） |
| S3 | 05:15–07:00 | UI（05:00–05:15 休息） |
| 收尾 | 07:00–08:15 | 全量回归 + 文档 + 提交推送 |
| 缓冲 | 08:15–09:00 | 吸收超时；**09:00 硬停**，未完成项如实移交 |

## 优先级原则（GOAL.md 2026-10-01，用户指令：先完成再完美）

1. 完成应用基本功能——真机完整可见可用；功能没通不做纯视觉打磨。
2. octos 系统 agent 联通——`octos.turn.start` 在 Rinx mini-app host 有真实服务；
   card-host 无服务、按既有降级路径诚实兜底。
3. 整体功能完善后再调 UI。

## 硬纪律（违反任何一条 = 本轮工作作废）

1. **蓝图冻结**：不加功能、不换方向；只修真实测试发现的错误、平台兼容、验收失败、
   必要安全/可靠性约束。**唯一例外（用户已批准）**：guardian scheduler 真实提醒动作。
2. **timebox 硬停**：任何单项超时 → 降级/记 blocked 留痕 → 立即继续下一项，不追。
3. **读回断言**：不采信任何「应该成功了」——包括你自己的。一切结论带证据。
4. **main.splash 任何改动** → 必触发：重 stamp manifest digest（blake3）+ `hub check`
   PASSED + qx-verify-v2 相关项重跑。
5. **诚实回报**：ACK(done|partial|blocked) + 验证级别(verified|partially-verified|unverified)
   + 证据路径；没验证的写 unverified。
6. **09:00 硬停**：停下时把任务队列状态写完整（每个未完成项：卡在哪、下一步是什么），
   保证白天班可无缝接手。
7. **push 前检查**：确认无敏感信息（test-accounts/tokens/db 不入库，.gitignore 已覆盖）。

## 环境与命令速查（全部实测过，勿重新搭建）

```sh
# 工作区根
WS=/home/kikun/MyProject/Agentic-octos

# script-app 真机 card-host（A 路线提交物）
cd $WS/my-entry/app/qianxian
export OCTOSENSE_APP_HUB=$WS/.build-hub-926/OctoSense-App-Hub
OCTO=$WS/octosense-ws/OctoScript-App-Design-Flow/tools/octo
python3 $OCTO run bundle --port 8141 --detach --hidden     # 起真机
python3 $OCTO check bundle                                  # 门禁，期望 PASSED
curl -s 127.0.0.1:8141/quit                                 # 收工时关掉
# 截图：python3 $OCTO shot 8141 out.png（llvmpipe 无头抓帧可能超时，见 S3）

# 14 项真机回归（#34 驱动 v2，此前沙箱被阻、待外环真机跑——就是今晚）
python3 $WS/my-entry/app/qianxian/tools/qx-verify-v2.py

# guardian 冒烟（Python 轨；无外部依赖时 g4b/g5 可直接跑）
cd $WS/my-entry/app/guardian && python3 smoke_g4b.py && python3 smoke_g5.py

# 本地 Matrix 环境（S2 用）
$WS/palpo-ctl.sh start && docker start gosim-pg
curl -s http://127.0.0.1:8128/_matrix/client/versions       # 应返回版本列表

# octos serve（LLM：DeepSeek-V4-Flash @ ModelScope，key 走 MODELSCOPE_API_KEY）
cd $WS/my-entry/app/guardian && python3 smoke_g3_real.py    # 真实 LLM 冒烟

# Rinx 宿主（已构建，--remote 接口实测可用）
$WS/run-rinx.sh
```

## 已定决策（外环 10-01 深夜拍板，不要重新讨论）

- MiniMax/Kimi 供应商切换**今晚不做**，维持 DeepSeek-V4-Flash 实测。
- guardian 真实提醒动作**批准做**（越界增强，timebox 75min，见 S1-2）。
- script-app 的 T-24h 占位文本**保持不动**（宿主无定时 API，limitation 声明继续有效）。

## 任务队列（按序执行，完成一片回报一片；中断后从第一个未完成项续跑）

### P0 基线与准备
- [x] P0-1 建通宵日志 `evidence/overnight-20261002.md`，写入起始基线（时间/commit/digest）。
- [x] P0-2 起真机 card-host + `hub check` → PASSED。
- [x] P0-3 跑 `qx-verify-v2.py` 14 项 → 失败项清单写进日志（= S1 工作清单）。
- [x] P0-4 guardian 冒烟 smoke_g4b + smoke_g5 → 全绿基线。
- **门禁**：基线快照落档，无基线不施工。

### S1 软件基础功能（门禁：qx-verify-v2 全绿 + hub check PASSED + 冒烟全绿）
- [x] S1-1 逐项修回归失败项（≤90min）：根因 → 最小修复 → 重跑该项 → ACK。
- [x] S1-2 **guardian 真实提醒动作**（75min timebox）：scheduler sweep 到期任务 →
  真发 Matrix 房间消息（复用 `matrix.py` txn_id 幂等 + outbox 对账机制）；
  冒烟扩展：真实发出 + 重放不重复 + 失败走 UNKNOWN 对账。
  卡住 → 保留占位、记 blocked，**不拖累后续**。
- [x] S1-3 回执渲染终验：回归覆盖「筛选子集下的回执显示」（#31 重构后已统一 `sel`
  索引，预期已修复；若仍有错位 → 修复）。
- [x] S1-4 文档同步：`limitations.md` 滞后项（AA 收账已实现）+ `changes.md` 台账。
- S1 已知遗留线索（供排查，不承诺全修）：scheduler 补偿只做标记；
  冲突检测粒度 = 同 slot_day+slot_part（runtime 无时钟 API，非缺陷）。

### S2 octos 联通 + Agentic（门禁：G3 真实冒烟绿；turn.start verified 或 blocked 留痕）
- [x] S2-1 起 palpo + gosim-pg + 复跑 `smoke_g3_real.py` → OUP 通道仍绿。
- [x] S2-2 **主目标：Rinx `--remote` 驱动 turn.start 真通路收口**（60min timebox）：
  `host.has("octos.turn.start")` 为真 → 真实 AI 解析回合 → 结果经本地校验落状态机；
  再断 octos serve 验证 8 秒超时兜底。证据落 `evidence/`，
  把 `regression-20261001.md` 的 partially-verified 升级或留痕。
- [x] S2-3 受阻预案：Rinx 路径超时 → 精确记录阻塞点（对评审有价值），
  转做 card-host 降级路径证据补强（AI 按钮 → 无服务 → 诚实降级提示可见性）。

### S3 UI（门禁：截图与 UI 现状一致 + hub check PASSED）
- [x] S3-1 像素截图重试（45min timebox）：检查 DISPLAY/WSLg → `octo shot 8141` 覆盖
  `bundle/screenshots/{01-main,02-expanded,03-conflict}.png`；仍超时 → 保留控件树渲染图
  （诚实标注为现行做法，不虚报）。
- [x] S3-2 失败态截图确认：官方硬性要求第二张为失败/空状态（03-conflict 现为冲突失败态）；
  S1/S2 若改过 UI → 重生成受影响截图。
- [ ] S3-3 纯视觉打磨（仅当功能全绿且有裕）：对照 `evidence/contrast-audit.md` 选 2–3 处
  关键文本对比度 quick win；每处改动重跑受影响回归步。

### 收尾（07:00–08:15）
- [x] F-1 全量回归终跑：qx-verify-v2 14 项 + guardian 冒烟全绿。
- [x] F-2 文档同步：通宵日志、`regression-v2-20261001.md`（#34 blocked→resolved）、
  `countdown.md`、`submission-readiness.md`、`changes.md`。
- [x] F-3 git 提交 + 推送公仓（push 前敏感信息检查）。
- [x] F-4 按 ACK 格式写通宵汇总进日志；留给人白天的清单：
  演示视频（`evidence/demo-script.md` 21 步就绪）、官方 issue #5 留言、
  名单锁定（10-4）、队外复现。

## 回报格式（写进通宵日志，一片一 ACK）

```
ACK(done|partial|blocked): <任务号> <一句话>
验证级别: verified|partially-verified|unverified
证据: <命令/输出/截图/DB 查询结果路径>
下一片前置: <缺什么>
```
