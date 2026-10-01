# 外环独立复验报告：#28 修复后（2026-10-01 ~03:10–03:18 UTC）

> 验证级别：partially-verified（hub check + 静态 + 源码级 verified；运行时回执验证被第三个 bug 阻塞）。
> 驱动：`app/qianxian/tools/qx-drive-outer.py`（click_title 精确点按 + click_gesture 筛选点按 + type_text /t 键入）。
> 对照组：`evidence/pre28-baseline.md`。

## 一、已验证通过（verified）

1. **hub check PASSED**：`qianxian 0.1.0 — PASSED`（仅 unsigned warning），新 digest
   `c28b021a0f64302e5f9e8baa87616fd82270a9a41b010301731b1483c437f460`。
   命令：`cd my-entry/app/qianxian && octo check bundle`（OCTO_HUB 指向 `.build-hub-926`）。
2. **静态自检全 0**：颜色返回字符串 0、TextInput 非法属性 0、布尔返回 0、fs.rename 0；
   `grep -c case_counts` = 0（死代码已删）；`case_receipt[i]` 零残留（两处已改 `[j]`）。
3. **冲突双条互标 ✅**：`['待拍板·冲突', '⚠ 时间冲突：#1 · 骑车 …', '待拍板·冲突']`，
   双向冲突卡内容完整（含双方 id/活动/时段）。
4. **建/选中/展开/确认/筛选主链 ✅**：hint 逐条有回执（`已建守护 #2…` → `已展开 #2…` →
   `已确认 #2 → Confirmed…` → `筛选：已确认 · 共 1 条 / 总 1 条`），计数正确。
5. **筛选点按精度**：Label 文字无独立命中区，按文字点会误中全屏 Splash（`r=[0,29,412,863]`）；
   改按 GestureView 矩形（idx=2 Confirmed rect `[171,368,70,32]`）后精确命中。
   经验：后续驱动一律按 widget 类型矩形点，不按文本点。

## 二、#28 两处修复确认落盘（源码级 verified）

- L1708–1709：`for _ri in case_receipt[j].len()` + `case_receipt[j][_ri]`（原 `[i]`），
  守卫 `case_receipt[j].len() > 0` 上下文一致；`#17b 外环修` 旧注释已更新。
  全渲染循环 30+ 处扁平下标现**全部为 `[j]`**，无例外。
- L1325 `case_counts = []` 整行删除，全文件零引用。

## 三、阻塞项：第三个 bug（展开态截断，需开 #29）

**现象**：单卡展开（不确认、无回执分支）同样截断在"参与人/未填写"之后；
时间/活动/地点/原文/回执全部不在 snap 树里。total W=65→64，y>600 只有底部按钮行。

**最小复现**（三次独立 jail 一致）：
建 1 条 → 点标题展开 → snap Label 止于 `未填写`（`r=[41,648,...]`），其后无任何展开 section。

**嫌疑定位**（源码级，未动手修）：
- 截断点 = 参与人输入行（L1679 `people_input := TextInput{...}` 声明行之后）。
- 该行是全文件唯一的 `on_render` 闭包循环内**具名 `:=` 绑定**；
  搜索框 TextInput（L1410，无 `:=`，匿名）不触发截断。
  根组件另有三处 `:=`（msg_input/hint/case_list/action_row）均在闭包外，不受影响。
- `ui.people_input` 另有两处跨闭包引用（L578 `set_text("")`、L1680 `ui.people_input.text()`）。
- 声明 `height:44` 但 snap 显示 `r=[38,709,288,30]`（30 高），声明与渲染不一致，
  佐证该节点实例化异常并拖累后续兄弟节点（A2/A3 类截断表现）。

**影响面**：
- 回执验证被阻塞：#28 的 i→j 修复**源码正确但运行时不可见**（回执区在截断带之后）。
- regression 基线 14 项中"展开态详情"项（#12）实际已不通过——基线截图 `02-expanded.png`
  是旧版本渲染，现版本展开态详情不可见。**基线需重标**，截图需重出。
- 用户可见影响：点卡片展开后只能看到状态/参与人，看不到时间/活动/地点/原文/回执——
  展开功能名存实亡。这是当前**最影响"明确好用"的 bug**，建议优先级高于一切打磨。

**建议 #29 修复方向**（仅建议，内环自行验证）：
1. 首选：参与人输入行改匿名 TextInput（去 `:=` 名），读值走 `ui` 树外其他方式
   （如改"添加"按钮 on_click 用固定 id 参数，或把输入行移出循环 card、放到 action 区，
   用 selected_id 驱动——与"添加"按钮已用 `selected_id` 同范式）。
2. 若必须具名：改名避 `people_input` 全局污染并验证 `ui.people_input` 双引用是否有效。
3. 修后验证：单卡展开 snap 必须出现 时间/活动/地点/原文 四 section（未确认时无回执为正常）；
   再跑本报告 §一全链 + 双条筛选错位（i≠j）回执归属 #2。

## 四、复验局限（诚实标注 unverified）

- 改时间点按效果不明（hint 无变化，作用对象待查；cycle_slot 代码零改动，沿用基线 ✅）。
- 搜索 /t 返回 ok 但过滤效果本轮未断言（set_query 代码零改动）。
- 清空按钮折叠态不可达（cases_counts 删除后清空路径未走通；`clear_all_data` 逻辑除该行外零改动）。
- 像素级渲染（沿用既有 screenshots，不重出——等 #29 修截断后再刷）。
