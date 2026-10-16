#!/usr/bin/env bash
set -euo pipefail

# 牵线（Qianxian）电脑端无头开发宿主启停工具 (Headless Fast-Loop Daemon)
# 核心原则：零弹窗、零夺焦、纯后台静默运行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PORT=8146

PID_FILE="/tmp/qianxian-card-host.pid"

case "${1:-start}" in
    "start")
        if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "✓ 宿主已在后台运行中 (PID: $(cat "$PID_FILE"), 端口: $PORT)"
            exit 0
        fi

        echo ">>> 以无头模式启动电脑端宿主 (端口: $PORT)..."
        rm -rf /tmp/octosense-card-apps/qianxian
        
        # 查找 card-host
        CARD_HOST=""
        if command -v card-host >/dev/null 2>&1; then
            CARD_HOST="card-host"
        elif [[ -x "$PROJECT_ROOT/../repos/OctoSense-App-Hub/target/release/card-host" ]]; then
            CARD_HOST="$PROJECT_ROOT/../repos/OctoSense-App-Hub/target/release/card-host"
        fi

        if [[ -z "$CARD_HOST" ]]; then
            echo "❌ 未找到 card-host 二进制文件"
            exit 1
        fi

        cd "$PROJECT_ROOT"
        nohup "$CARD_HOST" --bundle bundle --allow-unsigned --stamp --remote "$PORT" >/tmp/qianxian-card-host.log 2>&1 &
        HOST_PID=$!
        echo "$HOST_PID" > "$PID_FILE"
        sleep 1

        if kill -0 "$HOST_PID" 2>/dev/null; then
            echo "✓ [OK] 无头宿主已成功在后台启动 (PID: $HOST_PID，日志: /tmp/qianxian-card-host.log)"
            echo "  测试状态: curl -s http://127.0.0.1:$PORT/status"
        else
            echo "❌ 宿主启动失败，请检查日志: /tmp/qianxian-card-host.log"
            exit 2
        fi
        ;;

    "status")
        if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "✓ 宿主正在后台静默运行 (PID: $(cat "$PID_FILE"))"
            curl -s "http://127.0.0.1:$PORT/status" || true
            echo ""
        else
            echo "● 宿主未运行"
        fi
        ;;

    "stop")
        if [[ -f "$PID_FILE" ]]; then
            PID=$(cat "$PID_FILE")
            echo ">>> 正在停止宿主 (PID: $PID)..."
            curl -s "http://127.0.0.1:$PORT/quit" 2>/dev/null || true
            kill "$PID" 2>/dev/null || true
            rm -f "$PID_FILE"
            echo "✓ 宿主已停止"
        else
            echo "● 没有找到运行中的宿主 PID"
        fi
        ;;

    *)
        echo "用法: $0 [start | stop | status]"
        exit 1
        ;;
esac
