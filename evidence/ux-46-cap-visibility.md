# #46 A切片：AI capability 可见性提示

**日期**: 2026-10-06
**commit**: 203cf1d `qianxian UX #46：AI capability 可见性提示（A切片 探测+可见小字标签）`
**改动文件**: `app/qianxian/bundle/main.splash`（单文件，+24 行）
**verification level**: unverified（沙箱内无 splash runtime，照 ^maytqxx 标准）

## 改法落地

### 1. `probe_ai_cap()` fn（main.splash:1485 附近）

```
fn probe_ai_cap(){
    if host.has("model") {
        return "AI 服务：model.complete（结构化解析可用）"
    }
    if host.has("octos.turn.start") {
        return "AI 服务：对话通道可用（首次使用需在宿主点允许）"
    }
    return "AI：本机无 AI 服务，本地规则解析兜底"
}
```

顺序与 ai_parse() 双通道优先级一致：model.complete → turn.start → 本地规则。

### 2. 根组件插入 ai_cap_label（main.splash:1943，输入行与 hint 之间）

```
ai_cap_label := Label{width: Fill text: "AI 服务：探测中…"
    draw_text.color: secondary draw_text.text_style.font_size: 12}
```

- 位置：输入行 `View{...}` 之后、`hint := Label{...}` 之前
- 样式：次级色（secondary）、font_size 12、width Fill
- 静态 placeholder "AI 服务：探测中…"，根组件首次求值定型；load() 末尾命令式同步

### 3. load() 末尾同步（main.splash:548，照 #44 ui.style_btn.set_text 范式）

```
ui.style_btn.set_text("风格：" + style_label_for(receipt_style))
// #46 A切片：根组件 ai_cap_label 首次定型为静态 placeholder，
//   load() 末尾用 probe_ai_cap() 命令式同步真实 host 探测文案（照 #44 范式）。
ui.ai_cap_label.set_text(probe_ai_cap())
rebuild_lines()
```

### 4. ai_parse() 双通道皆无服务分支（main.splash:1583，防御性幂等）

```
// 双通道皆无服务
ai_pending = "no"
ui.hint.set_text("本设备无 AI 服务（no service answers \"model/octos\"），本地规则继续可用")
// #46 A切片：防御性幂等——load() 已设过 ai_cap_label，此处保持一致。
ui.ai_cap_label.set_text(probe_ai_cap())
```

## 自测结果

**blocked**：沙箱内无 card-host（`command -v card-host` 失败，`/usr/local/bin/card-host` 与 `/usr/bin/card-host` 不存在，`/tmp/qx-inner46` 不存在）。无法起 card-host 看实拍文案。

按 ^maytqxx：splash 改动标准验收为 `unverified`，由外环在生产环境跑真实验证。本回合不做自测冒进（不起 spl 试图跑 splash）。

## 纪律检查

- [x] 单文件 commit：仅 `app/qianxian/bundle/main.splash`（+24 行）
- [x] 未 push（本地 master 已 ahead）
- [x] commit message 形如 `qianxian UX #N：<brief>`：#46
- [x] 未新增 capability 声明、未动 manifest、未改 ai_parse 通道逻辑
- [x] 单次 shell 输出 ≤30 行（grep 全 ≤20 行内）
- [x] 禁全量 git diff/show/log -p（仅 -U0 + 定点 grep）
- [x] git identity 已为 `octos-inner <octos-inner@local>`（仓内既有设置）

## diff 摘要（-U0）

```
@@ fn load() {:
+    ui.ai_cap_label.set_text(probe_ai_cap())

@@ fn ai_parse() 上方:
+ fn probe_ai_cap(){ ... } (12 行：注释 4 + 函数体 9)

@@ ai_parse 双通道皆无服务分支:
+    ui.ai_cap_label.set_text(probe_ai_cap())

@@ 根组件输入行与 hint 之间:
+ ai_cap_label := Label{width: Fill text: "AI 服务：探测中…" ... } (5 行)
```

合计 4 处插入，共 +24 行，零修改（纯增量），零删除。
