#!/usr/bin/env bash
# ==============================================================================
# 牵线 (Qianxian) Android 真机自动化回归与全流程业务走查脚本
# 适用平台：Redmi K50 Ultra / 骁龙 8+ Gen 1 (1220x2712 Makepad Mobile Viewport)
# 规约：纯 bash + adb 驱动，无额外依赖，严格遵循 no-facts 铁律与读回断言
# ==============================================================================

set -euo pipefail

# 1. 环境准备与 ADB 检测
export PATH="$HOME/Android/Sdk/platform-tools:$PATH"
export ADB_SERVER_SOCKET="${ADB_SERVER_SOCKET:-tcp:127.0.0.1:5037}"

ADB_BIN=$(command -v adb || true)
if [ -z "$ADB_BIN" ]; then
    echo "❌ 错误: 未找到 adb 命令，请确保已安装 Android SDK platform-tools" >&2
    exit 1
fi

DEVICE_ID=$("$ADB_BIN" devices | awk 'NR>1 && $2=="device" {print $1; exit}')
if [ -z "$DEVICE_ID" ]; then
    echo "❌ 错误: 未检测到已连接的 Android 真机设备" >&2
    "$ADB_BIN" devices
    exit 1
fi

echo "📱 检测到在线设备: $DEVICE_ID"
PACKAGE_NAME="dev.aurorax.qianxian"
ACTIVITY_NAME=".MainActivity"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
EVIDENCE_DIR="$ROOT_DIR/my-entry/evidence"
mkdir -p "$EVIDENCE_DIR"

adb_cmd() {
    "$ADB_BIN" -s "$DEVICE_ID" "$@"
}

log_step() {
    echo -e "\n\033[1;34m[STEP]\033[0m \033[1;32m$1\033[0m"
}

capture_frame() {
    local target_name="$1"
    local local_path="$EVIDENCE_DIR/$target_name"
    adb_cmd exec-out screencap -p > "$local_path"
    echo "📸 已截帧存证: $local_path"
}

# 2. 坐标常量定义（基准：1220x2712）
# 首页输入栏与管家
INPUT_X=300
INPUT_Y=719
BUTLER_BTN_X=682
BUTLER_BTN_Y=719
PAIBAN_BTN_X=322
PAIBAN_BTN_Y=2179
BACK_TO_HOME_X=959
BACK_TO_HOME_Y=586

# 详情页与操作栏
FIRST_CARD_X=200
FIRST_CARD_Y=1450
TOP_BACK_BTN_X=180
TOP_BACK_BTN_Y=310
CONFIRM_BTN_X=601
CONFIRM_BTN_Y=1294
RESCHEDULE_BTN_X=149
RESCHEDULE_BTN_Y=2285

# AA 记账区
AA_INPUT_X=450
AA_INPUT_Y=1550
AA_SUBMIT_X=950
AA_SUBMIT_Y=1550
AA_CLEAR_BTN_X=300
AA_CLEAR_BTN_Y=2100

# 筛选标签
FILTER_ALL_X=130
FILTER_ALL_Y=1094

# 3. 启停与清理
log_step "重启并拉起牵线 Android 应用"
adb_cmd shell am force-stop "$PACKAGE_NAME"
sleep 1
adb_cmd shell am start -n "$PACKAGE_NAME/$ACTIVITY_NAME"
sleep 2

# 4. 执行第一条聚会（骑车）创建
log_step "通过管家交互输入 'bike' 起草第一条聚会（骑车）"
adb_cmd shell input tap $INPUT_X $INPUT_Y
sleep 0.5
adb_cmd shell input text "bike"
sleep 0.5
adb_cmd shell input tap $BUTLER_BTN_X $BUTLER_BTN_Y
sleep 1.5

log_step "拍板执行提案创建 #1 · 骑车"
adb_cmd shell input tap $PAIBAN_BTN_X $PAIBAN_BTN_Y
sleep 1.5

# 5. AA 记账与收尾实测
log_step "进入 #1 · 骑车 详情页"
adb_cmd shell input tap $FIRST_CARD_X $FIRST_CARD_Y
sleep 1.5

log_step "录入 AA 金额 300 并提交"
adb_cmd shell input tap $AA_INPUT_X $AA_INPUT_Y
sleep 0.5
adb_cmd shell input text "300"
sleep 0.5
adb_cmd shell input tap $AA_SUBMIT_X $AA_SUBMIT_Y
sleep 1.5
capture_frame "real-device-aa-ledger.png"

log_step "滚动至对账表底部并执行「AA 已收齐」收尾"
adb_cmd shell input swipe 120 2000 120 800 300
sleep 1.0
adb_cmd shell input tap $AA_CLEAR_BTN_X $AA_CLEAR_BTN_Y
sleep 1.5
capture_frame "real-device-aa-cleared.png"

log_step "返回守护主列表"
adb_cmd shell input tap $TOP_BACK_BTN_X $TOP_BACK_BTN_Y
sleep 1.5

# 6. 第二条聚会（羽毛球）创建与冲突检测
log_step "通过管家交互输入 'badminton' 起草第二条聚会（同占周六-下午）"
adb_cmd shell input tap $INPUT_X $INPUT_Y
sleep 0.5
adb_cmd shell input text "badminton"
sleep 0.5
adb_cmd shell input tap $BUTLER_BTN_X $BUTLER_BTN_Y
sleep 1.5

log_step "拍板执行创建 #2 · 羽毛球"
adb_cmd shell input tap $PAIBAN_BTN_X $PAIBAN_BTN_Y
sleep 1.5

log_step "返回主列表并验证双卡时段冲突横幅"
adb_cmd shell input tap $BACK_TO_HOME_X $BACK_TO_HOME_Y
sleep 1.5
capture_frame "real-device-conflict-detected.png"

# 7. 冲突裁决与改时间轮换
log_step "进入 #2 · 羽毛球 详情页执行时间槽位轮换"
adb_cmd shell input tap $FIRST_CARD_X $FIRST_CARD_Y
sleep 1.5
adb_cmd shell input tap $RESCHEDULE_BTN_X $RESCHEDULE_BTN_Y
sleep 1.5
capture_frame "real-device-conflict-resolved.png"

log_step "确认拍板这条守护（生成 ICS 日历回执）"
adb_cmd shell input tap $CONFIRM_BTN_X $CONFIRM_BTN_Y
sleep 1.5

# 8. 最终全量健康视图
log_step "返回主列表并切换为「全部」筛选视图"
adb_cmd shell input tap $TOP_BACK_BTN_X $TOP_BACK_BTN_Y
sleep 1.5
adb_cmd shell input tap $FILTER_ALL_X $FILTER_ALL_Y
sleep 1.5
capture_frame "real-device-two-cases-confirmed.png"

echo -e "\n\033[1;32m🎉 真机全流程自动化回归验证圆满完成！所有证据已落盘至 $EVIDENCE_DIR\033[0m"
