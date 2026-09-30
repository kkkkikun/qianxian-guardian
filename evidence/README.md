# evidence/ 索引（给评审：按你想回答的问题查）

> 23 份文件，不必全读。按下面的问题找即可。

## 「这个作品是什么？」

| 文件 | 回答什么 |
|---|---|
| [one-pager.md](one-pager.md) | **先读这份**（一页纸）：做了什么 / 为什么 / 怎么核验 / 怎么跑 / 已知边界 |
| [official-scenario-alignment.md](official-scenario-alignment.md) | 与官方「日历」场景四步演示的逐条对齐 |
| [../README.md](../README.md) | 完整功能说明 + 三条审阅路径 |

## 「它能跑吗？跑得起来吗？」

| 文件 | 回答什么 |
|---|---|
| [../run.md](../run.md) | 三段式复现（已有构建产物 / 自行构建 / 运行），**全部实测** |
| [demo-script.md](demo-script.md) | 21 步操作脚本 + 口播稿（录屏照着走） |
| [demo-preflight.md](demo-preflight.md) | 口播稿里每句话的事实核验结果 |
| [qianxian/review-answers.md](qianxian/review-answers.md) | `hub scan` 7 问逐条作答 |

## 「它真的被验证过吗？」

| 文件 | 回答什么 |
|---|---|
| [regression-20261001.md](regression-20261001.md) | **14 项功能真机回归**（card-host `/snap` + jail 自证） |
| [edge-cases-20261001.md](edge-cases-20261001.md) | 边界：长文本 228 字 / 注入串 / 连建 / 存储增长 / 旧数据兼容 |
| [entry-audit.md](entry-audit.md) | 13 个 UI 入口的完整性审查（无反馈/死路检查） |
| [self-review.md](self-review.md) | **像评委一样挑自己的毛病**（含 3 处已修的真问题） |
| [全量回归-20260927.txt](全量回归-20260927.txt) | 场外 guardian 六套冒烟结果（70+ 断言） |

## 「为什么这么做？取舍是什么？」

| 文件 | 回答什么 |
|---|---|
| [submission-form-decision.md](submission-form-decision.md) | 四条官方形态如何选，为什么是 script-app |
| [acceptance-mapping.md](acceptance-mapping.md) | task.md 12 条验收 → script-app 逐条对应/不适用原因 |
| [contrast-audit.md](contrast-audit.md) | 对比度实测（6 项未达 AA）与**和第一方一致**的取舍理由 |
| [ux-specs-v2.md](ux-specs-v2.md) | HIG / M3 / WCAG 逐条对照 + **4 项不达标的诚实交代** |
| [ux-specs.md](ux-specs.md) | v1 规范对照（含 4.8 平台限制） |
| [splash-constraints.md](splash-constraints.md) | 本 runtime 的 22 条实现约束（写脚本前必读） |
| [../limitations.md](../limitations.md) | 已知限制与后续工作（按 script-app 口径） |

## 「材料本身可靠吗？」

| 文件 | 回答什么 |
|---|---|
| [link-audit.md](link-audit.md) | 全仓链接实测（13 内部 + 外部 URL 全部 200） |
| [countdown.md](countdown.md) | 交付倒计时：已完成什么、还差什么、谁做 |
| [submission-readiness.md](submission-readiness.md) | 官方六项要求逐条核对 + 评审路径实测 |
| [official-issue-drafts.md](official-issue-drafts.md) | 官方 issue #5 留言草稿 |
| [olo-hello.md](olo-hello.md) | 双环协作首次闭环见证 |

## 文件命名说明

- `acceptance.md` / `checks.md`：guardian 口径（场外证明），
  script-app 口径见 `acceptance-mapping.md`。
- `ux-specs.md`（v1）与 `ux-specs-v2.md`（联网复核版）：内容有重叠，
  **v2 更新**，v1 保留作为首版对照。
