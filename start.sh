#!/bin/bash
# ============================================
# Learning Agent 启动脚本
# ============================================
# 功能：
#   - 检查环境和依赖
#   - 激活虚拟环境
#   - 启动 Web 服务
#   - 支持后台运行
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助
show_help() {
    cat << EOF
🚀 Learning Agent 启动脚本

用法：$0 [选项]

选项:
  -d, --daemon      后台运行（守护进程模式）
  -f, --foreground  前台运行（默认）
  -p, --port PORT   指定端口（默认：5001）
  -h, --host HOST   指定主机（默认：0.0.0.0）
  -c, --check       只检查环境，不启动
  -s, --status      查看运行状态
  -k, --kill        停止运行中的服务
  -r, --restart     重启服务
  --help            显示此帮助信息

示例:
  $0                     # 前台启动
  $0 -d                  # 后台启动
  $0 -p 8080             # 指定端口 8080
  $0 -r                  # 重启服务
  $0 -c                  # 检查环境

EOF
}

# 检查环境
check_environment() {
    log_info "检查运行环境..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    log_success "Python3: $(python3 --version)"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_error "虚拟环境不存在，请先运行：python3 -m venv venv"
        exit 1
    fi
    log_success "虚拟环境：venv/"
    
    # 检查依赖
    source venv/bin/activate
    if ! python3 -c "import flask" 2>/dev/null; then
        log_warning "Flask 未安装，正在安装依赖..."
        pip install -q -r requirements.txt
    fi
    log_success "依赖检查通过"
    
    # 检查 API Key
    if [ -f ".env" ] && grep -q "DASHSCOPE_API_KEY" .env; then
        log_success "API Key: 已配置"
    else
        log_warning "API Key: 未配置（Web 展示模式）"
        log_info "配置方法：export DASHSCOPE_API_KEY=sk-xxx 或编辑 .env 文件"
    fi
    
    # 检查目录结构
    for dir in data logs config web; do
        if [ ! -d "$dir" ]; then
            log_warning "创建目录：$dir"
            mkdir -p "$dir"
        fi
    done
    
    log_success "环境检查完成"
}

# 查看状态
check_status() {
    log_info "检查服务状态..."
    
    PID_FILE="$SCRIPT_DIR/.pid"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            PORT=$(grep -oP 'port \K\d+' "$PID_FILE" 2>/dev/null || echo "5001")
            log_success "服务运行中 (PID: $PID, 端口：$PORT)"
            echo ""
            echo "访问地址:"
            echo "  - 本地：http://localhost:$PORT"
            echo "  - 远程：http://$(hostname -I | awk '{print $1}'):${PORT:-5001}"
            echo ""
            echo "日志文件：logs/web.log"
            echo "停止服务：$0 -k"
            return 0
        else
            log_warning "PID 文件存在但进程已停止，清理中..."
            rm -f "$PID_FILE"
        fi
    fi
    
    # 检查是否有其他进程占用端口
    PORT=${CUSTOM_PORT:-5001}
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        log_warning "端口 $PORT 被占用"
        lsof -Pi :$PORT -sTCP:LISTEN -t
    else
        log_info "服务未运行"
    fi
    
    return 1
}

# 停止服务
stop_service() {
    log_info "停止服务..."
    
    PID_FILE="$SCRIPT_DIR/.pid"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            sleep 2
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null || true
            fi
            log_success "服务已停止 (PID: $PID)"
        else
            log_warning "进程已停止"
        fi
        rm -f "$PID_FILE"
    else
        # 尝试查找并停止
        pkill -f "python3.*web/app.py" 2>/dev/null && log_success "服务已停止" || log_info "未找到运行中的服务"
    fi
}

# 启动服务
start_service() {
    HOST=${CUSTOM_HOST:-"0.0.0.0"}
    PORT=${CUSTOM_PORT:-5001}
    DAEMON=$1
    
    log_info "启动 Learning Agent Web 服务..."
    log_info "主机：$HOST, 端口：$PORT"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    if [ "$DAEMON" = "true" ]; then
        # 后台运行
        PID_FILE="$SCRIPT_DIR/.pid"
        LOG_FILE="$SCRIPT_DIR/logs/web.log"
        
        # 确保日志目录存在
        mkdir -p logs
        
        # 启动后台进程
        nohup python3 web/app.py --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
        PID=$!
        
        # 保存 PID
        echo "$PID" > "$PID_FILE"
        echo "port $PORT" >> "$PID_FILE"
        
        sleep 2
        
        if ps -p $PID > /dev/null 2>&1; then
            log_success "服务已启动 (后台模式)"
            echo ""
            echo "PID: $PID"
            echo "端口：$PORT"
            echo "日志：$LOG_FILE"
            echo ""
            echo "访问地址:"
            echo "  - 本地：http://localhost:$PORT"
            echo "  - 远程：http://$(hostname -I | awk '{print $1}'):${PORT}"
            echo ""
            echo "查看日志：tail -f $LOG_FILE"
            echo "停止服务：$0 -k"
        else
            log_error "服务启动失败，查看日志：$LOG_FILE"
            exit 1
        fi
    else
        # 前台运行
        log_success "服务启动中..."
        echo ""
        log_info "访问地址:"
        echo "  - 本地：http://localhost:$PORT"
        echo "  - 远程：http://$(hostname -I | awk '{print $1}'):${PORT}"
        echo ""
        log_info "按 Ctrl+C 停止服务"
        echo ""
        
        python3 web/app.py --host "$HOST" --port "$PORT"
    fi
}

# 重启服务
restart_service() {
    log_info "重启服务..."
    stop_service
    sleep 2
    start_service "$DAEMON_MODE"
}

# 主函数
main() {
    # 默认值
    DAEMON_MODE="false"
    CUSTOM_HOST=""
    CUSTOM_PORT=""
    ACTION="start"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--daemon)
                DAEMON_MODE="true"
                shift
                ;;
            -f|--foreground)
                DAEMON_MODE="false"
                shift
                ;;
            -p|--port)
                CUSTOM_PORT="$2"
                shift 2
                ;;
            -h|--host)
                CUSTOM_HOST="$2"
                shift 2
                ;;
            -c|--check)
                ACTION="check"
                shift
                ;;
            -s|--status)
                ACTION="status"
                shift
                ;;
            -k|--kill)
                ACTION="stop"
                shift
                ;;
            -r|--restart)
                ACTION="restart"
                shift
                ;;
                --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项：$1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行动作
    case $ACTION in
        check)
            check_environment
            ;;
        status)
            check_status
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        start|*)
            check_environment
            if [ "$ACTION" = "start" ]; then
                start_service "$DAEMON_MODE"
            fi
            ;;
    esac
}

# 运行主函数
main "$@"
