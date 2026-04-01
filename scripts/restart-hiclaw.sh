#!/bin/bash
# HiClaw 一键重启脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "========================================"
echo "🦞 HiClaw 重启服务"
echo "========================================"
echo ""

bash "${SCRIPT_DIR}/stop-hiclaw.sh"
sleep 5
bash "${SCRIPT_DIR}/start-hiclaw.sh"

echo ""
echo "========================================"
