# 外环真机复验报告：#30 AA收账（2026-10-01，外环接手首轮）

> 验证对象：commit `bd28be4`（内环 #30 UI三件）+ `4c3e3a1`（外环 #30b 三目修复）。
> 复验环境：直驱 card-host（headless，llvmpipe 软渲染），fresh jail /tmp/qx-outer30，
> 端口 8145；探针 app 另跑 8146。驱动：/snap /click /t /m?k=scroll 远程桥。

## 一、已验证通过（verified）

1. **hub check PASSED**：`qianxian 0.1.0 — PASSED`（仅 unsigned warning），
   修复后 digest `218342aa927ea12c848e35f7d5705fa66555e84efad7183f28930c211c52028f`。
2. **静态硬约束自检全 0**：B2 字符串下标 / B1 颜色字符串 / B6 TextInput 非法属性 /
   C3 循环变量复用 / D1 注释路径逃逸 / fs.rename / C7 布尔返回 / case_counts 残留
   （8 项 grep，见 `evidence/splash-constraints.md` 自检命令）。
3. **AA 数字范式探针（7 例真机全过，`evidence/probe30-float-paradigm.md`）**：
   `to_f64` 语义、浮点除、`to_chars` 字节码、NaN 正向守卫、参考实现
   300/3→`约 ¥100.00/人`、100/3→`约 ¥33.33/人`、空/0/"3x0"→`未记账`、300.5/3→`约 ¥100.16/人`。
4. **三目运算符 bug 修复复验**：`bd28be4` 曾在 rebuild_lines 用 `?:`（splash 不支持，
   真机每次 rebuild 报 `[E] unknown named arg` → 卡片列表完全不渲染）；
   `4c3e3a1` 改单层 if 归一化后：`[E]` 清零、建卡/标题行/计数恢复正常。
5. **主链冒烟（真机，修复后 build）**：
   - 用示例试试 → 输入框填入示例（不自动建卡，符合文案）→ 建守护 → `#1 · 骑车` ✅
   - 分诊：无关键词文本建卡不编造活动/时段（卡片标题正常落行）✅
   - ScrollYView 滚动本身工作（卡片可见数随 /m?k=scroll 变化）✅

## 二、阻断发现：展开态详情尾部零布局（#28 起既有，本轮深挖）

**现象**：展开单卡后，详情区只渲染 `状态`、`参与人(+输入行)` 两个 section；
`AA总额 / 均摊 / 时间 / 活动 / 地点 / 原文 / 回执` 全部不可见。

**测量（`/snap` vs `/snap?all`）**：
- 默认 snap：Card 高度止于参与人输入行（h≈333），其后是一个 2px 空壳 View（y=737）。
- `?all`：**所有缺失 section 都在 widget 树里，但 rect 全为 `[0,0,0,0]`**——
  即节点存在、布局（layout walk）未覆盖。
- 折叠态 W=65 / 展开态 W=65 / 多种修复变体 W=65（默认过滤后可见数恰均 65）。

**已逐一排除的假设（全部真机实验）**：
| # | 假设 | 实验 | 结果 |
|---|---|---|---|
| 1 | on_render 闭包内具名 `:=` 绑定（outer-verify-28 的怀疑） | bill_input、people_input 先后匿名化 | 截断点不变，**排除** |
| 2 | on_render 内第 2 个 TextInput | 先后把 people/AA 的 TextInput 换成纯占位 View（卡内仅剩 search 一个 TextInput） | 截断点不变，**排除** |
| 3 | Card 顶层子节点过多（A3 字面理解） | 8 个 section View 合并进单个 `View{flow: Down}` 容器 | 截断点不变，**排除** |
| 4 | ScrollY 视口裁剪（未滚动） | `/m?k=scroll` 实测滚动有效（多卡场景可见数随滚动变化）；展开卡内滚动无效 | 滚动本身正常，但解释不了零布局 |
| 5 | 三目/新语法残留 | 修复后 `[E]` 全 0；`grep '?'` = 0 | 已修复，与本截断无关 |

**结论**：布局 walk 在 Card 内累计到参与人输入行（y≈737，ScrollY 视口下沿附近）即停，
后续兄弟节点零布局。**高度疑似 makepad 运行时问题**（ScrollYView > GestureView > Card{height:Fit}
的内容超出视口剩余高度时的 walk 截断），非 app 逻辑可绕——本轮已尝试手册全部在案绕法无效。
按设计流 AGENTS.md「需要改 runtime 仓库时，说明并停止」，此发现需：
1. 向 makepad 仓提 issue/最小复现（或由内环换一种不依赖超视口 Card Fit 的 UI 形态，
   例如：展开详情改为底部固定面板（静态区，handler 用 selected_id 驱动，如 hint/动作键模式）；
2. **影响面**：14 项回归中依赖展开态详情的项（#6 回执可见、#12 详情、#30 均摊行真机验收）
   全部被阻；折叠态主链不受影响。

## 三、未验证（被阻断或超时会话）

- #30 AA 收账端到端真机（输入行在展开态不可见——被二阻断；数学部分已由探针实证）。
- 重出 3 张 listing 截图：headless `/g` 抓帧挂起（手册既有限制），
  需带显示器的窗口实例（上个会话 03:18 的截图来自其桌面会话）。
- 14 项回归全绿：折叠态可测项本轮已过 4 项（14a/14b 主链、9 搜索、3 冲突徽章、
  2 分诊、确认/取消链路待重跑——本轮脚本中断于选择器笔误，非 app 问题）。

## 四、本轮回填与提交

- `5ffbcdc`：探针证据 + 手册 C9（循环内嵌套 if 条件赋值变量变空串——新坑实锤）。
- `4c3e3a1`：#30b 三目修复（外环修，单文件，真机复验通过）。
- 派单通道：`octos chat --provider minimax-cn --model MiniMax-M3 --json -m …`（探活 ✅）。
  本轮派单 4 次：2 次被 octos 内核熔断（shell-spiral / doom-loop——
  **建议内环任务书继续压缩单轮 scope**）、1 次 provider 初始化失败、1 次成功（bd28be4）。

## 五、建议下一轮派单（外环备忘）

1. **截断块**（最高优先）：内环试「展开详情底部固定面板」形态；或外环出最小复现提 makepad。
2. **截图**：在有显示器的窗口实例重出 3 张 listing 截图（`octo shot`）。
3. 回归全绿重跑（折叠态项先行，展开态项等 1 落地）。
4. 清 pending：`evidence/ux-specs.md` §4.8 的 18 行未提交 diff（内环 ^mbehelx 遗留）。
