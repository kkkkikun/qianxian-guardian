# 外环实证探针：Splash 数字解析/显示范式（#30 AA收账前置，2026-10-01）

> 背景内环 ACK(blocked)（黑板#30）：重写均摊算法时缺「字符→整数」标准范式，拒绝盲编。
> 本探针由外环在真机 card-host 上实证（一次性探针 app，端口 8146，llvmpipe 软渲染），
> 结论全部来自 `/snap` 实测 Label 输出，非静态推断。

## 一、实证结论（真机 /snap 实测）

| # | 表达式 | 实测 | 结论 |
|---|---|---|---|
| 1 | `"300".to_f64()` | `300` | **to_f64 存在**（源码 string.rs:108，`s.parse().unwrap_or(NAN)`） |
| 2 | `"abc".to_f64()` | `NaN` | 非法输入 → NaN（拼接后显示 "NaN"） |
| 3 | `"300.5".to_f64()` | `300.5` | 支持小数 |
| 4 | `" 42 ".to_f64()` | `NaN` | **空格不宽容**（如需 trim 注意坑 C9，见下） |
| 5 | `"" + (30000.0 / 3.0)` | `10000` | **除法是浮点除**（opcodes_ops.rs handle_div `fa / fb`）；整值浮点 Display 无 `.0` |
| 6 | `"" + (10000.0 / 3.0)` | `3333.3333333333335` | 非整值 → 全精度 Display |
| 7 | `"ab7".to_chars()` | `[97, 98, 55]` | **to_chars 返回字节码数字数组**（非字符串！）；数字字符 = 字节-48，`.` = 46 |
| 8 | `cs[i] - 48` 后拼接 | `"307"` | 字节→数字→字符串通路可用 |
| 9 | `"a,b,c".split(",").len()` | `3` | split+数组len 可用 |
| 10 | NaN 参与比较 | `NaN > 0` 为 false | **正向条件守卫天然过滤 NaN/0/负数**（无需显式 NaN 检测） |

## 二、新发现的运行时坑（已实测复现）

**坑 C9（for 循环内两层嵌套 if 中的条件赋值 → 目标 let 变量变空串）**：

```
let ok = "yes"
for i in cs.len() {
    if cs[i] != 46 {
        if cs[i] < 48 { ok = "no" }   // 两层嵌套 if 内赋值
        if cs[i] > 57 { ok = "no" }
    }
}
return "ok=" + ok        // 实测输出 "ok="（变量被清空！）
```

- 同逻辑改为 `let b = cs[i]` 后比较（赋值未执行）→ 正常；单层 if（或 if/else）内赋值 → 正常
  （`cut2` 的 `if/else` 形态与 `hit = hit + 1` 单层形态均实测正常）。
- 规避：**不要在循环内两层嵌套 if 里做条件赋值**——用正向条件收拢（见参考实现）、
  把赋值抬出循环、或用单层 if/else。
- 另：`("" + x).trim().to_chars()` 这类**方法链临时值**上再取数组曾得到全零字节
  （v2 探针 T 组全灭）；先 let 绑定再逐个调用则正常。与 C2 同族：别依赖链式临时值。

## 三、参考实现（真机全 7 例通过，可直接采用或改造）

验收对照：300/3 → `约 ¥100.00/人`（#30 验收①）；100/3 → `约 ¥33.33/人`（验收②）；
200/3 → `约 ¥66.66/人`（截断不四舍五入，符合"不做四舍五入到分"）；
""/0/"3x0" → `未记账`（NaN 与 0 走正向守卫假分支）；300.5/3 → `约 ¥100.16/人`。

```
fn cut2(x){
    let s = "" + x
    let cs = s.to_chars()
    let n = cs.len()
    let dot = -1
    for i in n {
        if cs[i] == 46 { dot = i }
    }
    let take = n
    if dot >= 0 {
        take = dot + 3
        if take > n { take = n }
    }
    let out = ""
    for i in take {
        if cs[i] == 46 { out = out + "." } else { out = out + ("" + (cs[i] - 48)) }
    }
    if dot < 0 { out = out + ".00" }
    if dot >= 0 {
        if (n - dot) == 2 { out = out + "0" }
    }
    return out
}
fn bill_display(total_str, n_f){
    let bt = "" + total_str
    let total_f = bt.to_f64()
    let out = "未记账"
    if total_f > 0 {
        if n_f > 0 {
            out = "约 ¥" + cut2(total_f / n_f) + "/人"
        }
    }
    return out
}
```

设计要点：无循环内嵌套赋值（避 C9）、无中途 return（v6 W2/W3 实证早退+标志位组合脆）、
NaN/0/负数由 `total_f > 0` 正向守卫统一兜底为「未记账」（诚实不编造）。

## 四、复现方法（外环）

```bash
# octo run --detach 在 llvmpipe 软渲染+高负载下可能等不到 first frame 而静默失败
# （日志止于 pool 0 jobs，无错误行）。可靠启动法：直接驱动 card-host：
export OCTO_CARD_HOST=.build-hub-926/OctoSense-App-Hub/target/release/card-host
MAKEPAD_REMOTE=8146 $OCTO_CARD_HOST --bundle /tmp/qx-probe --app-data /tmp/qx-probe-state \
  --allow-unsigned --stamp > /tmp/qx-probe.log 2>&1 &
sleep 20   # llvmpipe 首帧较慢
curl -s --noproxy '*' http://127.0.0.1:8146/snap    # 读 widget 树
curl -s --noproxy '*' http://127.0.0.1:8146/quit
```

探针源码已随本轮外环工作留存于 `/tmp/qx-probe/`（一次性环境，不入库；
本文件记录了全部实测输入输出，可据此重建）。

## 五、局限

- 未测超大金额/inf 边界（`to_f64("1e999")` → inf → inf>0 为 true → cut2("inf") 会出垃圾；
  如担心可在 bill_display 加金额上限分支，内环自行取舍）。
- 探针未走 hub gate（无 capability 的 /tmp bundle）；参考实现并入 main.splash 后
  以 hub check + 外环真机回归为准。
