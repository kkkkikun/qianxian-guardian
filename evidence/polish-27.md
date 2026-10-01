# Polish #27 打磨记录（Top-8 范围内微调，2026-10-01）

> 内环 #27。只动 `app/qianxian/bundle/main.splash`（3 行）+ 新建本文件。
> `manifest.json` 的 digest 由 `octo check` 自动重 stamp，未手工改。
> 工作区另有 #30 进场前既有未提交改动（均摊 `bill_total` 等约 90 行），非本轮引入，见 §五。

## 一、改动清单（函数名/组件名 + 行号 + 改前→改后）

| # | 位置 | 改前 | 改后 | 理由（Top-8 映射） |
|---|---|---|---|---|
| 1 | `Badge` 工厂（约 L1371） | `padding: Inset{left:8 right:8 top:3 bottom:3}` | `padding: Inset{left:8 right:8 top:4 bottom:4}` | Top-8 #2 留白节奏：徽章纵向 +1（±4 内），11bold 小字呼吸感；Badge 圆角 7、语义色一律不动 |
| 2 | 搜索框行 `View`（约 L1408，`case_list.on_render` 内） | `flow: Right spacing: 6` | `flow: Right spacing: 8` | Top-8 #2 留白节奏：搜索框与"× 清空"间距 +2（±4 内），32 高筛选条靠间距豁免（v3 #8）的同源处理 |
| 3 | 筛选栏 `View`（约 L1437，`case_list.on_render` 内） | `flow: Right spacing: 6` | `flow: Right spacing: 8` | 同上：四胶囊之间 +2，横向防拥挤；选中态 `accent` 底白字 bold 双差不动 |

未动项（Top-8 其余 7 项经核对已落地，无需再改）：
- #1 信息层级：26/16bold/14/13/11bold + SectionLabel/BodyLine 复用已齐（L1373–1381）。
- #3 卡片分组：`Card` 工厂圆角 14 已统一；展开 section 间细线 `View{height:1 #xefeff4}` 已有（L1653）。
- #4 按钮主次：绿确认 > 橙收敛 > 灰底红字取消已齐；默认取消键无红底（L1736–1748）；全 44 高。
- #5 冲突卡：红底 `#xff3b30` 白字 13bold（L1662–1665）+ 折叠态 `·冲突` 后缀（L201–204）+ TextLine 冲突行（L1720–1722）。
- #6 选中态三编码：`▶` 前缀 + `hi_w` 色条 + 徽章中文并存（L1595–1621）。
- #7 空态双分支：`cases.len()==0` vs `filtered_idxs.len()==0` 文案已区分（L1500–1571）。
- #8 hint 句式：add/confirm/reschedule/cancel/undo/clear/cycle_slot/add_person 全"动词+对象+结果"，失败明示。

语义色核对（改前改后计数一致，一律未动）：
`#x007aff` 2 / `#x34c759` 2 / `#xff3b30` 6 / `#xff9500` 2 / `#x5856d6` 2。

## 二、自检输出（粘贴）

### octo check bundle（必须 PASSED）

```
octo: hub stamp -> babd47ac16401c4239ea1a0ff8270bd417ca54841a764cd6a773299800fd21a4
octo: .../hub check /home/kikun/MyProject/Agentic-octos/my-entry/app/qianxian/bundle --allow-unsigned
qianxian 0.1.0 — PASSED
  [warning] publisher-signature: unsigned: accountability rests on the hub alone
  grants: capabilities {"octos.turn.start", "storage"}, hosts {}, storage 16777216 bytes, agent none
```

命令：`cd my-entry/app/qianxian && python3 ../../../octosense-ws/OctoScript-App-Design-Flow/tools/octo check bundle`

### 静态自检（splash-constraints.md 末尾命令，全 0）

```
0   # B2 字符串下标
0   # B1 颜色返回字符串
0   # B6 TextInput 非法属性
0   # C3 复用循环变量 j（注：`for j in` 全文件 0；回执循环用 `_ri`，外层用 `i`，见 §五第2条）
0   # D1 注释路径逃逸
0   # fs.rename
0   # C7 布尔返回
E1 root dyn if/visible: 0
```

### 8142 真机 /snap 自检（另起端口，未占 8141）

- 空态：`W=52 HINT=已载入 0 个聚会守护`，err-widgets=0（`ty` 维度无 error 类型；唯一的 "error" 误报是 `Splash.ty` 节点 `t` 字段内嵌源码文本含英文 error 字样，非错误控件）。
- 终态（建→展开→确认→取消→撤销后）：`W=64 err-widgets=0`。

### 功能点按记录（单命令内启动+驱动，/click+wait=1，按 snap 几何取中点）

```
f0 base W=52 HINT=已载入 0 个聚会守护
f1 1.fill-example W=51 HINT=已填示例到输入框（不自动建守护），点「建守护」继续
f2 2.add-case W=56 HINT=已建守护 #1（分诊命中：time），已选中，点卡片可展开详情
f3 3.expand W=65 HINT=已展开 #1（再点一次可折叠）
f4 4.confirm W=64 HINT=已确认 #1 → Confirmed（组织者拍板，读回一致）（作用于最新一条，因未选中）
f5 5.filter-confirmed W=65 HINT=筛选：已确认 · 共 1 条 / 总 1 条
f6 6.filter-proposing W=47 HINT=筛选：待拍板 · 共 0 条 / 总 0 条
f7 7.filter-all W=65 HINT=筛选：全部 · 共 1 条 / 总 1 条
f8 8.cancel-1st W=61 HINT=再点一次「确认取消」才会真取消 #1；5 秒内点别的按钮或选别的卡可放弃（作用于最新一条，因未选中）
f9 9.cancel-2nd W=63 HINT=已取消 #1（5 秒内可点「撤销取消」）（作用于最新一条，因未选中）
f10 10.undo W=64 HINT=已撤销取消 #1 → 恢复到 Confirmed（仅本次，其他已取消条目维持）
```

- 建守护 → 选中（新建自动选中）→ 展开（▾ 前缀+详情 section）→ 确认（Confirmed+回执）→ 取消（两段式）→ 撤销（仅本次恢复）：全部逐条有 hint 回执。
- 改时间：本轮未点按——"改时间（5 槽）"按钮折叠在「怎么用？」说明卡低频区内，本轮驱动的快照里该卡处于折叠态，按 `snap` 几何找不到该按钮（`改时间Btn: False`，但"低频操作"标签存在，按钮只是未渲染而非缺失）。回归基线 `regression-20261001.md` #4 对改时间已有 ✅（周六-上午→周六-下午，冲突重算解除），本轮未破坏其代码路径（cycle_slot 函数零改动）。诚实标注见 §三。
- 搜索：未逐字键入验证；`set_query` 代码零改动，筛选叠加逻辑未动。

## 三、未能验证项（诚实标注 unverified）

1. 改时间按钮本次点按 unverified（折叠态不可达；代码零改动，沿用回归基线 ✅）。
2. 搜索键入 unverified（代码零改动）。
3. 像素级渲染效果 unverified（无头环境，只能以 /snap 树 + 既有 screenshots 目视结论为准；本轮未改 screenshots/）。
4. 冲突双条互标本轮 unverified（单条驱动未触发冲突分支；冲突检测代码零改动，沿用回归基线 ✅）。

## 四、约束遵守声明

- A1 深度≤6：只改 `spacing/padding` 数值，未增减任何节点，深度不变。
- A2 同父不同类并置：未增减节点。
- B1 颜色字面量：语义色计数改前改后一致，未动。
- B5 不用 `\n` 布局：未动文案换行。
- C1 闭包只读扁平数组：未动逻辑。
- C4 整数组替换：未动逻辑。
- D1 注释禁 `../|http://|file://`：静态自检 0。
- E1 状态 UI 进 `on_render`：两处 spacing 改动本就在 `on_render` 闭包内；Badge 工厂为静态定义，与 E1 无关。
- 未加功能/按钮/字段/capability，未改状态机/分诊/冲突算法，未碰 `.secrets/`、screenshots/，未手工改 digest。

## 五、附带发现（非本轮引入，不改，只记录）

1. 工作区 `main.splash` 另有约 90 行未提交 diff（#30 均摊 `bill_total`/`slot_init_asked` 等，`git -C my-entry diff HEAD --stat` 显示 `95 ++---`，其中本轮仅 3 行 spacing/padding），`changes.md` 亦有 1 行未提交。外环合并时请注意归属。
2. 回执循环 `for _ri in case_receipt[i].len()` 用 `i`（外层 `filtered_idxs` 下标）而注释写"原用 j"——`i` 恰为本层循环变量，`case_receipt[i]` 与守卫 `case_receipt[j]` 下标语义不一致（`i` 是筛选序，`j` 是 case 序）。本轮按"不改逻辑"纪律未动；建议外环用"筛选非 all + 展开回执"复验一条确认。
3. `clear_all_data` 内 `case_counts = []` 引用了未声明变量（`grep case_counts` 全文件仅此 1 处），触发清空第二次点按即可能报错。本轮未动（动即改逻辑）；建议外环另起任务修。
4. 后台 card-host 进程在两次 bash 调用之间会被回收——真机驱动必须"启动+点按"放在同一个 bash 命令内，否则跨命令必 Connection refused。本轮最终驱动已按此方式跑通。
