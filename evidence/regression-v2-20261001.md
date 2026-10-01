# 回归验证记录 v2（2026-10-01，#34：适配列表/详情新路径）

> 外环派单 #34：#31 改了交互路径（点卡=进详情模式、返回列表、AA/参与人输入在详情内），
> 旧驱动 `app/qianxian/tools/qx-drive-outer.py` 与 `evidence/regression-20261001.md` 基线（14项）
> 按旧路径写。本轮按新路径重做驱动 + 全量回归自测尝试。

## 一、驱动 v2（`app/qianxian/tools/qx-verify-v2.py`）

- 新增驱动覆盖 14 项回归映射到新路径（点卡进详情→8项信息→AA 300/3=约¥100.00/人→
  确认→回执四行→返回列表；折叠态项照旧）。
- 遵循 A5 方法论（#33）：通过 /snap 找 Label/Button 文字定位，不依赖固定坐标；
  虚拟化列表下坐标点击不可靠（rect 可能是占位值），用文字 + 类型双键定位。
- 内置模式判据：`is_detail_mode`（含「返回列表」按钮）/ `is_list_mode`（含「建守护」且无「返回列表」），
  驱动按模式分支选择下一步动作。
- 收尾包含 14 项 PASS/FAIL 汇总输出，便于脚本化采集。

## 二、自测尝试：headless 直驱 card-host

按 #34 step 2 启动命令：

```
MAKEPAD_REMOTE=8146 card-host --bundle app/qianxian/bundle \
  --app-data /tmp/qx-outer34 --allow-unsigned --stamp &
sleep 24 && curl 127.0.0.1:8146/snap
```

### 实测尝试结果：blocked（沙箱阻止）

| 检查项 | 结果 |
|---|---|
| `command -v card-host` | NOT FOUND（exit 1，无输出） |
| `command -v makepad` | NOT FOUND |
| `find / -maxdepth 6 -name "card-host"` | 0 命中 |
| `ls /opt` | NOT A DIRECTORY（无 /opt） |
| `ls /usr/local/bin/` 内 card-host / makepad | 0 命中 |

**阻塞原因**：本沙箱（`AppUi session workspace root: /home/kikun/MyProject/Agentic-octos/my-entry`）
未安装 card-host / makepad 二进制，且无 `/opt`。/snap 端点无法联通 → 无法执行 14 项端到端验证。

**沙箱限制**：
1. 内环不安装运行时（card-host 是外环/真机复验工具，^maytqxx 已记录"内环 sandbox 不安装 splash 运行时"）。
2. 网络受限，无外网下载通道。
3. 真机复验能力归外环（参见 #31 真机 8/8、#32 真机降级验证）。

### 仍交付的产物

- 驱动脚本 `app/qianxian/tools/qx-verify-v2.py`：272 行，按新路径完整覆盖 14 项，
  - 模式判据（list/detail 互斥）
  - 文字定位（避免虚拟化下坐标点击不可靠）
  - 边滚边看（调用 /scroll?dy=200 → /snap）
  - 收尾 PASS/FAIL 汇总
- 本证据文件：含驱动说明、自测尝试结果、阻塞原因、待办（外环真机复验路径）。

## 三、外环真机复验建议（blocked 时移交脚本的接续路径）

按 #34 step 2「沙箱阻止→ACK(blocked)交外环执行，脚本照交」：

1. 外环真机（带显示器窗口）执行：
   ```
   card-host --bundle app/qianxian/bundle \
     --app-data /tmp/qx-outer34 --allow-unsigned --stamp --port 8146 &
   sleep 24
   python3 app/qianxian/tools/qx-verify-v2.py 2>&1 | tee /tmp/qx-v2.log
   curl 127.0.0.1:8146/quit
   ```
2. 把 PASS/FAIL 汇总回填本文件「四、外环真机复验结果」一节（待填）。
3. 若有 FAIL 项：按 #33 边滚边看方法论重试（rect 占位值时滚动→snap→再点击），
   仍 FAIL 则上报黑板追加 #35+。

## 四、外环真机复验结果（待外环填）

> 占位：14 项 PASS/FAIL 由外环真机复验后回填。

| R-# | 项 | 结果 | 证据 |
|---|---|---|---|
| R-01 | 示例填充可见 | _ | _ |
| R-02 | 建守护 #1 可见 | _ | _ |
| R-03 | 建守护 #2 可见 | _ | _ |
| R-04 | 冲突标签可见 | _ | _ |
| R-05 | 进入详情模式（返回列表按钮可见） | _ | _ |
| R-06 | 详情 8 项信息可见 | _ | _ |
| R-07 | 详情内确认生效 | _ | _ |
| R-08 | 回执行可见 | _ | _ |
| R-09 | 返回列表生效 | _ | _ |
| R-10 | 折叠态可见 | _ | _ |
| R-11 | 滚动后物化稳定 | _ | _ |
| R-12 | 搜索生效 | _ | _ |
| R-13 | 清空全部两段式生效 | _ | _ |
| R-14 | 第 3 条（不同 slot）建卡可见 | _ | _ |

## 五、与旧基线的差异（新路径专属修订）

| 项 | 旧基线（regression-20261001.md） | v2（新路径） |
|---|---|---|
| 点卡行为 | 展开折叠（原地 8 项可见） | 进详情模式（detail 视图） |
| 返回路径 | 点同一卡片（▶↔▾） | 详情内点「返回列表」 |
| AA/参与人 输入位置 | 折叠态展开区域 | 详情面板内 |
| 驱动方法 | 按标题前缀点开 + 折叠行内查回执 | 模式判据（list/detail）+ 文字定位 |

**验证级别：unverified**（内环 sandbox 无 card-host，驱动本身只完成静态自检：
脚本语法 OK、模块导入 OK、URL/模式判据与新交互路径设计一致；端到端真机验证归外环执行）。
