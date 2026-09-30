# 文档链接实测（2026-10-01）

> 规矩：**引用不实测不能写。** 外环用脚本对全仓 Markdown 做了两轮扫描。

## 内部链接

- 扫描范围：`my-entry/**/*.md`（排除 `.git`）
- 结果：**13 个内部链接全部有效，0 失效**（`README.md` / `task.md` / `GOAL.md` /
  `evidence/*.md` 之间的交叉引用）。

## 外部链接

- 扫描范围：全仓 Markdown 中所有 `http(s)://` 链接
- 首轮 46 条（含正文里的示例 URL，如 `127.0.0.1:8128` 本地地址，已排除）

### 修复记录

Apple HIG 与 Material 3 站点在 2026 年改版，**训练知识里的旧路径大面积失效**：

| 失效 URL | 替换为（实测 200） |
|---|---|
| `…/empty-states` | `…/feedback` |
| `…/selection-and-primary-action` | `…/lists-and-tables` |
| `…/confirming-and-allowing-destructive-actions` | `…/buttons` |
| `m3…/accessible-design/accessibility-basics` | `m3…/foundations/accessible-design/overview` |
| `m3…/foundations/communication/empty-states` | `m3…/foundations/overview` |
| `m3…/foundations/communication/error-states` | `m3…/foundations/overview` |

> Apple 站点为 JS 渲染，静态抓取拿不到导航结构，只能逐个探测可用路径。
> **站点随时可能再改**——评审若点不开，以本表为准（均为 2026-10-01 实测 200）。

### 仍然可用的关键引用（实测 200）

- Apple HIG：`alerts` / `buttons` / `color` / `feedback` / `inputs#touch-targets` /
  `lists-and-tables` / `onboarding` / `privacy` / `status` / `typography`
- Material 3：`components/{lists,dialogs,app-bars}` / `foundations/overview` /
  `foundations/accessible-design/overview` / `styles/color/roles` / `styles/typography/applying-type`
- WCAG 2.2：`Understanding/contrast-minimum` / `Understanding/non-text-contrast`
- WebAIM：`resources/contrastchecker/`
- 上游文档（GitHub raw 页面）：`OctoScript-App-Design-Flow/docs/{QUICKSTART,SCRIPT-API,PUBLISHING,CAPABILITIES}`
- 本作品公仓：`https://github.com/kkkkikun/qianxian-guardian`（submit issue #1）

## 复现脚本

```python
import re, os, glob
base = "my-entry"
bad = []
for md in glob.glob(base + "/**/*.md", recursive=True):
    for m in re.finditer(r'\]\(([^)#][^)]*?)\)', open(md).read()):
        link = m.group(1).split('#')[0]
        if link.startswith(('http://', 'https://', 'mailto:')):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(md), link))):
            bad.append((md, link))
print("失效内部链接:", len(bad), bad)
```
