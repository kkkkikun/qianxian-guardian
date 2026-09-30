# 演示脚本事实核验（2026-10-01）

> 录屏前必查：口播稿里的**每个数字与措辞**都必须与运行中的应用一致，
> 否则录出来的话与画面不符，评审一眼看穿。本表为逐条实测结果。

## 按钮文案（`demo-script.md` 引用 → 代码实际）

| 脚本写法 | 代码实际 | 一致 |
|---|---|---|
| 用示例试试 / 建守护 / 确认这条守护 / 重新收敛 / 取消守护 | 同名 `ButtonFlat{text: …}` | ✅ |
| 改时间（5 槽） | `改时间（5 槽）` | ✅ |
| 撤销取消 | `撤销取消` | ✅ |
| 导出数据 / 清空全部 / AI 解析 / 添加 | 同名 | ✅ |

（对照方式：`grep -c 'ButtonFlat{text: "<名>"' app/qianxian/bundle/main.splash`）

## 口播中的数字与措辞

| 口播说法 | 实测 | 一致 |
|---|---|---|
| 「在 **5 个**常见时段间轮换，改完**自动重算冲突**」 | 连点 5 次改时间后回到起点「周六-上午」= 闭环；冲突随重算变化 | ✅ |
| 「逗号分隔、**上限 10 人**」 | `add_person()` 内 `total + added.len() > 10` 拦截并提示 | ✅ |
| 「抽不到就写「未抽取到」，不编造名字」 | `place_disp == ""` → 显示「地点未抽取到」/「未填写」 | ✅ |
| 澄清卡「有时间，但这看起来不像聚会安排」 | 实际文案：`有时间，但这看起来不像聚会安排——要牵线跟这条吗？再点一次「建守护」即可（仍是您主动）` | ✅ |
| 「再点一次…（**5 秒**）」 | 确认态按钮文案含「5s」，`start_timeout(5.0, …)` 过期 | ✅ |
| 「只恢复刚取消的那一条」（#25 修复后） | 取消 #1、#2 → 撤销 → 仅 #2 恢复，#1 仍 Cancelled | ✅ |

## 截图来源（录屏时如需宿主原始像素）

本环境无图形会话，`/g` 抓帧超时。`bundle/screenshots/` 三张是**按真实控件树渲染**的
（`tools/snap-to-png.py`），来源已在 `evidence/qianxian/review-answers.md` 标注。
在有显示器的机器上可用宿主原始像素覆盖：

```sh
python3 $OCTO shot <port> bundle/screenshots/01-main.png
```

## 复现方式

```sh
cd my-entry/app/qianxian
export OCTOSENSE_APP_HUB=../../../.build-hub-926/OctoSense-App-Hub
python3 ../../../octosense-ws/OctoScript-App-Design-Flow/tools/octo run bundle --port 8141
```
