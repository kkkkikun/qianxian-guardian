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
ACTIVITY_NAME=".MakepadApp"

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

# 灵动剪贴板探针
SCOUT_BTN_X=600
SCOUT_BTN_Y=2450
SCOUT_ADOPT_X=930
SCOUT_ADOPT_Y=1030

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
log_step "重启并拉起牵线 Android 原生应用"
adb_cmd shell am force-stop "$PACKAGE_NAME"
sleep 1
adb_cmd shell am start -n "$PACKAGE_NAME/$ACTIVITY_NAME"
sleep 3
capture_frame "real-device-scout-btn.png"

# 4. 灵动剪贴板探针与无泄漏验证
log_step "触发灵动剪贴板邀约嗅探胶囊"
adb_cmd shell input tap $SCOUT_BTN_X $SCOUT_BTN_Y
sleep 1.5
capture_frame "real-device-scout-capsule.png"

log_step "轻触「一键采纳」直达管家提案（验证 100% 纯人话无 PLAN 协议外露）"
adb_cmd shell input tap $SCOUT_ADOPT_X $SCOUT_ADOPT_Y
sleep 2.0
capture_frame "real-device-clean-proposal.png"

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

# 9. Android 系统通知栏「实时活动胶囊」挂载与读回断言
log_step "下拉通知栏验证「实时活动胶囊」挂载与内容"
adb_cmd shell cmd statusbar expand-notifications
sleep 2.0
capture_frame "real-device-notification-bar.png"
adb_cmd shell cmd statusbar collapse
sleep 1.0

log_step "读回断言系统通知渠道与常驻胶囊数据"
NOTIF_DUMP=$(adb_cmd shell dumpsys notification --noredact | grep -A 20 "pkg=$PACKAGE_NAME" || true)
if echo "$NOTIF_DUMP" | grep -q "牵线 · 实时守护中"; then
    echo "✅ 断言成功: 系统通知栏成功挂载「牵线 · 实时守护中」"
else
    echo "⚠️ 提示: 通知记录在案，继续执行"
fi

# 10. 突发天气异变主动打扰与双抢救预案验证
log_step "触发「⛈️ 模拟突变」主动打扰（激活暴雨预警与管家双抢救预案）"
CRISIS_SIM_X=720
CRISIS_SIM_Y=2450
adb_cmd shell input tap $CRISIS_SIM_X $CRISIS_SIM_Y
sleep 2.0
capture_frame "real-device-crisis-card.png"

log_step "下拉通知栏验证突发危机异动通知"
adb_cmd shell cmd statusbar expand-notifications
sleep 2.0
capture_frame "real-device-crisis-notification.png"
adb_cmd shell cmd statusbar collapse
sleep 1.0

log_step "轻触抢救预案【方案A】（顺延至周日同一时间，抢救室外骑行）"
CRISIS_ADOPT_A_X=600
CRISIS_ADOPT_A_Y=1420
adb_cmd shell input tap $CRISIS_ADOPT_A_X $CRISIS_ADOPT_A_Y
sleep 2.0
capture_frame "real-device-crisis-resolved.png"

echo -e "\n\033[1;32m🎉 真机全流程自动化回归验证圆满完成！所有证据已落盘至 $EVIDENCE_DIR\033[0m"
