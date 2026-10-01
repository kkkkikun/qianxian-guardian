# Splash 硬约束手册（v1，2026-10-01）

> 本手册汇总 24 轮双环迭代中**实证**的 Splash（OctoScript script-app）运行时限制。
> 每条都有实测证据。**写新切片前必读；验收时逐条 grep 核对。**
> 来源：黑板 `.octos/OUTER_LOOP_REVIEW.md` 各轮外环复验记录。

## A. 渲染限制（最隐蔽，优先看）

| # | 约束 | 证据 | 绕法 |
|---|---|---|---|
| **A1** | **节点深度上限约 6 层**：超过则**静默丢弃**（不报错、`/snap` 里直接消失） | 展开态详情原在深度 8-9 完全不渲染；提升到深度 6 后状态/活动/地点/回执全部正常（#21/#23）。**[#31 修正]** 深度只是次要因素——超出 ScrollY 盒高的内容（不论深度）都会被不实例化；「深度 6」的可行解其实是「深度与盒高都没超」 | UI 保持在深度 6 以内；与摘要行**同级并列**，不要多包 `View`；**先估盒高再估深度** |
| **A2** | **同一父节点下只渲染第一个同类子节点**：`RoundedView{Label Label}` 只显示第一个 | 冲突卡两个并列 Label 只显示前一个（#17b） | 两行**合并进一个 Label**，或各自一张卡 |
| **A3** | **#31 修正·机制重写**：展开态「尾部丢布局」不是节点数量上限，而是**盒高竞争 + ScrollY 虚拟化**的复合表现：①ScrollY 与 Fit 兄弟节点共享父高，Fit 侧过高（详情面板/说明卡等）会把 ScrollY 挤到 0 → 列表整体消失；②ScrollY 自身内容超过盒高 → 超出盒高的 widget 不实例化（虚拟化机制见 A5），不论节点数量是否真的"过多" | 旧表述「#20 展开态 43 个顶层节点，后加的「改时间/参与人」全丢」实证的是同一机制（盒外不实例化），并非「数量截断」 | ①ScrollY 与 Fit 兄弟节点共享父高要**预算**（Fit 侧总高不要喧宾夺主）②长内容用「底部固定面板」承接（#31 模式）而非塞进 ScrollY 卡内③验收必须**边滚边看**（静态单次 `/snap` 看不到盒外内容） |
| **A4** | `RoundedView`/`View` **必须 `show_bg: true` 才绘背景**，且**必须给 width/height** | 只给 `show_bg` 不布局，整块消失（#17b） | 两者都写 |
| **A5** | **#31 修正·新增**：**`ScrollYView` 是虚拟化列表**——视口外的 widget **不实例化**（不进入渲染树、`/snap` 里看不见）；滚动时才**物化**进树（实测：怎么用卡/AI 按钮滚动后出现于树，rect 可能仍是占位值如 `[0,29,412,863]`）。**驱动/验证方法论**：必须边滚边看（滚动→`/snap`→再滚动），静态单次 `/snap` 看不到盒外内容；坐标点击验证在未物化的 widget 上**会失败**（#32 AI 按钮点击验证即被此机制挡住） | #31 列表被挤零布局；#32「降级按钮坐标点击验证失败」；#28「展开态截断」实为此机制 + 盒高竞争复合 | ①长列表用底部固定面板承接关键交互（#31 模式），不要把按钮藏在 ScrollY 深处②验收时**滚动到目标位置再 `/snap` 验证**③坐标点击方案不可靠——优先按 id 取 widget 后再交互 |

## B. 类型与取值

| # | 约束 | 证据 | 绕法 |
|---|---|---|---|
| **B1** | **颜色字面量（`#x1c1c1e`）与字符串（`"#x1c1c1e"`）是不同类型**；`draw_*.color` 期望 `Vec4f` | 颜色函数返回字符串 → `type mismatch: expected Vec4f, got string`（#13/#17b） | 颜色函数**直接返回字面量**（不加引号）；**不经字符串数组传递**，闭包内直接调函数 |
| **B2** | **字符串不能下标取字符**（`s[i]` → `cannot index 0 on string`） | #15 截断原文时踩到 | 用 `split("")` 切分后循环拼 |
| **B3** | **数组没有 `join`** | 同上 | 循环 `+=` 拼接 |
| **B4** | **nil 参与 `+` 结果为 nil**（注意：仅限**拼接**；直接把数组元素绑给 `text:` 不受此限） | #15 `Label{text: nil}` → `type mismatch … got nil`，整个 `on_render` 中断 | 拼接字段一律 `"" + ` 兜底；`text: arr[i]` 形可直接用（已验证） |
| **B5** | **Label 内 `\n` 不换行** | 冲突卡两行合并不显示 | 用多个 Label 或单行分隔符 |
| **B6** | `TextInput` **只有 `empty_text`**，没有 `value`/`placeholder` | #20 用了 `value:` → `property not defined`，`on_render` 中断 | 读值用 `ui.<id>.text()` |

## C. 作用域与赋值

| # | 约束 | 证据 | 绕法 |
|---|---|---|---|
| **C1** | **`on_render` 闭包内读 `cases[i][…]` 全部为空** | #5–#8 反复踩；扁平化前列表全空 | 闭包只读**扁平字符串/整数数组**；逻辑放 `rebuild_lines`（函数上下文可读对象字段） |
| **C2** | **函数返回的数组取不到元素**（`f()[0]`） | #20 `cycle_slot_current` 返回数组后 `next[0]` 为空 | 拆成多个返回**字符串**的函数 |
| **C3** | **不要复用循环变量名**：外层 `let j = …` 被内层 `for j` 覆盖 | #17b 回执行循环复用 `j` → 后续 `case_lines[j]` 全部 `InvalidArgs` | 内层用 `_k`/`_ri`/`ci` 等独立名 |
| **C4** | **对象字段动态赋值不可靠**：`cases[i]["x"] = v` 写不进去 | #20 改时间槽时 `slot_day` 赋值无效 | **重建整个数组**（逐个 push 新对象）再 `cases = new_cases` 整体替换 |
| **C5** | **新增字段必须在 `cases.push` 的对象字面量里预置**（key 带引号） | 动态加字段不可靠（#4 实证） | push 时写全字段，初值给 `""` |
| **C6** | **按钮 `on_click` 闭包不要捕获循环变量 `j`** | #20 按钮点了没反应 | 用全局 `selected_id`：`on_click: \|\| f("" + selected_id)` |
| **C7** | **函数返回布尔不可靠**：跨函数 `return true` 在调用点 `== false` 比较会误判 | #13 写入成功却报「保存失败」 | 用**字符串标记**（`save_result = "ok"/"fail"`） |
| **C8** | 对象字面量 key **必须带引号**（`{"id": 1}` 而非 `{id: 1}`），否则与 `["id"]` 不是同一命名空间 | #5 字面量 key 读取全空 | 全部带引号 |
| **C9** | **for 循环内两层嵌套 `if` 中的条件赋值会让目标 let 变量变空串**；方法链临时值（`("" + x).trim().to_chars()`）上取数组可得全零字节 | 外环#30探针（2026-10-01，`evidence/probe30-float-paradigm.md` W2 实测输出 `ok=`） | 不在循环内嵌套 if 里赋值：正向条件收拢/赋值抬出循环/单层 if-else；方法调用逐个 let 绑定，不链式 |

## D. 门检（`hub check`）

| # | 约束 | 证据 | 绕法 |
|---|---|---|---|
| **D1** | **注释里也不能出现 `../`、`http://`、`file://`** —— assets 规则扫全文含注释 | #17b 注释里 `.../周日` 含 `../` → **整个包被拒** | 注释避免这些前缀；用 `…` 代替 `...` |
| **D2** | 文件扩展名白名单、≤8MB、无 symlink、`id` 不以 `os.` 开头 | 标准规则 | 提交前跑 `octo check` |

## E. 根组件与状态

| # | 约束 | 证据 | 绕法 |
|---|---|---|---|
| **E1** | **根组件的属性（`visible:` / `if`）只在首次求值定型**，之后不随状态重算 | #8 取消按钮确认态变体永不出现；#11 撤销条回退 | 随状态变化的 UI **必须放进某个 `on_render` 闭包内** |
| **E2** | `on_change: \|text\|` 给出新文本；读值用 `ui.<id>.text()` | 搜索框实现 | 别指望闭包捕获的变量 |

## F. 环境限制（非缺陷，无法绕开）

- **无读屏语义槽位**（`accessibility_*` 不存在）→ 用 `▶`/`▾` 字符 + 状态文字补偿
- **无暗色模式槽位**（`is_dark` 不存在）→ 第一方系统应用同样固定浅色
- **无动态字体槽位** → 用 11/12/13/14/15/16/26/32 层级
- **无时钟/日期 API** → 时间槽只判「同一天同一时段」，不做精确时刻比较（如实说明）
- **无头环境抓帧超时**（`/g` → `grab timeout`）→ 真截图须在有显示器的机器产出

---

## 使用方式

1. **写任务书时**：把相关条目抄进条目（内环看不到本手册）。
2. **验收时**：按 A→F 顺序逐条 grep 核对，**先查 A1/A2/A3/A5（渲染/虚拟化/盒高竞争）再看功能**——A5 的「边滚边看」方法论是 #31/#32 后所有 ScrollY 内交互验证的前置。
3. **踩到新坑**：追加到本表并注明证据轮次。

## 自检命令（可直接复制）

```sh
S=app/qianxian/bundle/main.splash
echo "A/B/C/D/E 自检："
grep -cE '_full_text\[[a-z_]\]|\w+\[[a-z_]+\]\.push' $S        # B2 字符串下标（应0）
grep -c 'return "#x' $S                                              # B1 颜色返回字符串（应0）
grep -c 'value:\|placeholder:' $S                                   # B6 TextInput 非法属性（应0）
grep -c 'for j in' $S                                                # C3 复用循环变量 j（应0）
grep -cE '^\s*//.*(\.\./|http://|file://)' $S                      # D1 注释路径逃逸（应0）
grep -c 'fs.rename' $S                                               # fs 无 rename（应0）
grep -c 'return true\|return false' $S                               # C7 布尔返回不可靠（应0）
# E1 根组件层无动态 if/visible（需脚本，见下）
python3 - <<'EOF'
import re
src=open("app/qianxian/bundle/main.splash").read().split("\n")
inside=False; depth=0; root=0
for l in src:
    if "on_render: ||" in l: inside=True; depth=l.count("{")-l.count("}"); continue
    if inside:
        depth += l.count("{")-l.count("}")
        if depth<=0: inside=False
        continue
    if re.match(r"^    \w+ :?=", l) or re.match(r"^    (ButtonFlat|View|SolidView|ScrollYView|Label|TextInput)", l):
        if re.search(r"\b(if .*\{|visible:)", l) and not l.strip().startswith("//"): root+=1
print("E1 根组件动态if/visible:", root, "(应0)")
EOF
# A1 节点深度：展开态 UI 应 ≤6
```
