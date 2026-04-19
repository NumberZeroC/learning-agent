#!/bin/bash
# ============================================
# Learning Agent 工作流启动脚本
# ============================================
# 功能：
#   - 后台运行知识生成工作流
#   - 支持跳过第二轮/第三轮生成
#   - 支持单主题/单层级生成
# ============================================
# 
# 用法：
#   ./start_workflow.sh                    # 全量生成（三轮）
#   ./start_workflow.sh --skip-details     # 只生成结构
#   ./start_workflow.sh --skip-relation    # 跳过知识关联
#   ./start_workflow.sh --topic "机器学习" # 单主题生成
#   ./start_workflow.sh --layer 1          # 单层级生成
#   ./start_workflow.sh --status           # 查看状态
#   ./start_workflow.sh --stop             # 停止工作流
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="$SCRIPT_DIR/logs"
PIDFILE="$SCRIPT_DIR/.workflow.pid"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$LOGDIR"

cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    cat << EOF
🚀 Learning Agent 工作流启动脚本

用法：$0 [选项]

选项:
  --skip-details     跳过第二轮（知识点详情）
  --skip-relation    跳过第三轮（知识关联）
  --topic NAME       生成单个主题（指定主题名称）
  --layer N          生成单个层级（指定层级号）
  --status           查看运行状态
  --stop             停止运行中的工作流
  --help             显示此帮助信息

示例:
  $0                             # 全量生成（20主题，三轮）
  $0 --skip-details              # 只生成结构（快速）
  $0 --skip-relation             # 跳过知识关联
  $0 --topic "机器学习"           # 单主题生成
  $0 --layer 1                   # 第1层生成
  $0 --status                    # 查看状态
  $0 --stop                      # 停止工作流

说明:
  - 全量生成预计 20-40 分钟
  - 单主题/单层级 2-10 分钟
  - 断点续传支持，可随时中断
EOF
}

check_status() {
    echo -e "${BLUE}📊 工作流状态${NC}"
    echo ""
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 工作流运行中${NC}"
            echo "   PID: $PID"
            echo "   日志: $LOGDIR/workflow.log"
            echo ""
            echo "查看实时日志："
            echo "   tail -f $LOGDIR/workflow.log"
            echo ""
            echo "查看进度："
            echo "   ls -lh data/workflow_results/layer_*_workflow.json"
            return 0
        else
            echo -e "${YELLOW}⚠️  PID文件存在但进程已停止${NC}"
            rm -f "$PIDFILE"
        fi
    fi
    
    echo -e "${BLUE}ℹ️  工作流未运行${NC}"
    return 1
}

stop_workflow() {
    echo -e "${BLUE}🛑 停止工作流...${NC}"
    
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null || true
            fi
            rm -f "$PIDFILE"
            echo -e "${GREEN}✅ 工作流已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  进程已停止${NC}"
            rm -f "$PIDFILE"
        fi
    else
        echo -e "${YELLOW}⚠️  未找到PID文件，工作流可能未运行${NC}"
        # 尝试查找并停止
        pkill -f "python.*run_workflow.py" 2>/dev/null && \
            echo -e "${GREEN}✅ 已停止${NC}" || \
            echo -e "${BLUE}ℹ️  无运行中的工作流${NC}"
    fi
}

start_workflow() {
    SKIP_DETAILS=$1
    SKIP_RELATION=$2
    TOPIC_NAME=$3
    LAYER_NUM=$4
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🚀 Learning Agent 工作流启动${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        exit 1
    fi
    
    # 检查配置文件
    if [ ! -f "config/agent_config.yaml" ]; then
        echo -e "${RED}❌ 配置文件不存在：config/agent_config.yaml${NC}"
        exit 1
    fi
    
    # 检查知识框架
    if [ ! -f "config/knowledge_framework.yaml" ]; then
        echo -e "${YELLOW}⚠️  知识框架不存在，将自动生成${NC}"
    fi
    
    LOGFILE="$LOGDIR/workflow_$TIMESTAMP.log"
    
    echo -e "${BLUE}📋 任务信息${NC}"
    echo "   工作目录：$SCRIPT_DIR"
    echo "   日志文件：$LOGFILE"
    echo "   启动时间：$(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 构建命令
    CMD="python3 run_workflow.py"
    
    if [ -n "$TOPIC_NAME" ]; then
        # 🔒 安全验证：检查主题名称是否有效
        echo -e "${BLUE}🔍 验证主题名称...${NC}"
        VALID_TOPICS=$(python3 regenerate_topic.py --list 2>&1 | grep "^\s*\[" | awk -F'- ' '{print $NF}' | sed 's/^ *//')
        
        if ! echo "$VALID_TOPICS" | grep -qx "$TOPIC_NAME"; then
            echo -e "${RED}❌ 错误：无效的主题名称 '$TOPIC_NAME'${NC}"
            echo ""
            echo -e "${BLUE}✅ 有效的主题列表：${NC}"
            python3 regenerate_topic.py --list 2>&1 | grep -v "^2026-"
            echo ""
            echo -e "${YELLOW}💡 提示：使用 --list 查看所有主题${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ 主题名称验证通过${NC}"
        echo ""
        
        CMD="python3 regenerate_topic.py \"$TOPIC_NAME\""
        if [ "$SKIP_DETAILS" = "true" ]; then
            CMD="$CMD --skip-details"
        fi
        if [ "$SKIP_RELATION" = "true" ]; then
            CMD="$CMD --skip-relation"
        fi
        echo -e "${BLUE}📝 生成模式：单主题${NC}"
        echo "   主题：$TOPIC_NAME"
    elif [ -n "$LAYER_NUM" ]; then
        CMD="python3 regenerate_topic.py --layer-only $LAYER_NUM"
        if [ "$SKIP_DETAILS" = "true" ]; then
            CMD="$CMD --skip-details"
        fi
        if [ "$SKIP_RELATION" = "true" ]; then
            CMD="$CMD --skip-relation"
        fi
        echo -e "${BLUE}📝 生成模式：单层级${NC}"
        echo "   层级：第$LAYER_NUM层"
    else
        echo -e "${BLUE}📝 生成模式：全量${NC}"
        echo "   层数：5层，20主题"
        echo "   轮次：三轮（结构→详情→关联）"
        if [ "$SKIP_DETAILS" = "true" ]; then
            CMD="$CMD --skip-details"
            echo "   ⚠️  已跳过第二轮"
        fi
        if [ "$SKIP_RELATION" = "true" ]; then
            CMD="$CMD --skip-relation"
            echo "   ⚠️  已跳过第三轮"
        fi
    fi
    
    echo ""
    echo -e "${BLUE}⏱️  预计耗时${NC}"
    if [ -n "$TOPIC_NAME" ]; then
        echo "   单主题：2-5 分钟"
    elif [ -n "$LAYER_NUM" ]; then
        echo "   单层级：5-15 分钟"
    else
        if [ "$SKIP_DETAILS" = "true" ] && [ "$SKIP_RELATION" = "true" ]; then
            echo "   只生成结构：5-10 分钟"
        elif [ "$SKIP_DETAILS" = "true" ] || [ "$SKIP_RELATION" = "true" ]; then
            echo "   两轮生成：10-20 分钟"
        else
            echo "   完整三轮：20-40 分钟"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}🚀 启动工作流...${NC}"
    
    # 后台启动
    nohup bash -c "$CMD" > "$LOGFILE" 2>&1 &
    PID=$!
    
    # 保存PID
    echo $PID > "$PIDFILE"
    
    sleep 2
    
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 工作流已启动${NC}"
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${BLUE}📊 信息${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo "   PID:        $PID"
        echo "   日志：      $LOGFILE"
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${BLUE}📋 常用命令${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo "   查看日志：     tail -f $LOGFILE"
        echo "   查看进度：     ls -lh data/workflow_results/"
        echo "   查看状态：     $0 --status"
        echo "   停止工作流：   $0 --stop"
        echo ""
    else
        echo -e "${RED}❌ 工作流启动失败，查看日志：${NC}"
        echo "   $LOGFILE"
        tail -20 "$LOGFILE"
        exit 1
    fi
}

# 主函数
main() {
    SKIP_DETAILS="false"
    SKIP_RELATION="false"
    TOPIC_NAME=""
    LAYER_NUM=""
    ACTION="start"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-details)
                SKIP_DETAILS="true"
                shift
                ;;
            --skip-relation)
                SKIP_RELATION="true"
                shift
                ;;
            --topic)
                TOPIC_NAME="$2"
                shift 2
                ;;
            --layer)
                LAYER_NUM="$2"
                shift 2
                ;;
            --status)
                ACTION="status"
                shift
                ;;
            --stop)
                ACTION="stop"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 未知选项：$1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
    
    case $ACTION in
        status)
            check_status
            ;;
        stop)
            stop_workflow
            ;;
        start)
            start_workflow "$SKIP_DETAILS" "$SKIP_RELATION" "$TOPIC_NAME" "$LAYER_NUM"
            ;;
    esac
}

main "$@"