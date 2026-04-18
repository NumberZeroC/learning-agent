#!/bin/bash
# ============================================
# Learning Agent 公开版部署脚本
# ============================================
# 功能：
#   - 支持 systemd 和 Docker 两种部署方式
#   - 公开模式（隐藏配置/聊天/工作流执行）
# ============================================
# 
# 用法：
#   ./deploy_public.sh --mode systemd    # systemd部署（推荐生产）
#   ./deploy_public.sh --mode docker      # Docker部署
#   ./deploy_public.sh --help             # 显示帮助
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="/opt/learning-agent"
SERVICE_NAME="learning-agent-public"
PORT=32015

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    cat << EOF
🚀 Learning Agent 公开版部署脚本

用法：$0 --mode [systemd|docker]

选项:
  --mode systemd     systemd服务部署（推荐生产环境）
  --mode docker      Docker容器部署
  --port PORT        自定义端口（默认32015）
  --help             显示帮助

示例:
  $0 --mode systemd           # systemd部署
  $0 --mode docker            # Docker部署
  $0 --mode systemd --port 80 # 指定端口

说明:
  - 公开模式：只展示知识内容
  - 已禁用：聊天、配置、工作流执行
  - 部署目录：/opt/learning-agent
EOF
}

deploy_systemd() {
    PORT=$1
    
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}🚀 systemd 服务部署${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${BLUE}📋 部署信息:${NC}"
    echo "   部署目录：$DEPLOY_DIR"
    echo "   服务端口：$PORT"
    echo "   运行方式：systemd 服务"
    echo ""
    
    # 1. 创建部署目录
    echo -e "${BLUE}📁 步骤 1/6: 创建部署目录...${NC}"
    sudo mkdir -p $DEPLOY_DIR
    sudo chown $(whoami):$(whoami) $DEPLOY_DIR
    echo "   ✅ 完成"
    echo ""
    
    # 2. 复制源码
    echo -e "${BLUE}📦 步骤 2/6: 复制源码...${NC}"
    for dir in web config docs services utils; do
        if [ -d "$SCRIPT_DIR/$dir" ]; then
            cp -r "$SCRIPT_DIR/$dir" $DEPLOY_DIR/
        fi
    done
    cp $SCRIPT_DIR/*.py $DEPLOY_DIR/ 2>/dev/null || true
    cp $SCRIPT_DIR/requirements.txt $DEPLOY_DIR/
    echo "   ✅ 完成"
    echo ""
    
    # 3. 复制知识数据
    echo -e "${BLUE}💾 步骤 3/6: 复制知识数据...${NC}"
    mkdir -p $DEPLOY_DIR/data/{workflow_results,llm_audit_logs,logs}
    cp -r $SCRIPT_DIR/data/workflow_results/* $DEPLOY_DIR/data/workflow_results/ 2>/dev/null || true
    cp -r $SCRIPT_DIR/data/llm_audit_logs/* $DEPLOY_DIR/data/llm_audit_logs/ 2>/dev/null || true
    echo "   ✅ 完成"
    echo ""
    
    # 4. 配置环境变量
    echo -e "${BLUE}🔐 步骤 4/6: 配置环境变量...${NC}"
    cat > $DEPLOY_DIR/.env << EOF
# Learning Agent 公开知识展示网站
# 部署时间：$(date -Iseconds)

# 公开模式配置（强制）
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true

# 时区
TZ=Asia/Shanghai

# API Key（请手动配置）
DASHSCOPE_API_KEY=
EOF
    echo "   ✅ .env 已创建"
    echo ""
    
    # 5. 创建虚拟环境
    echo -e "${BLUE}🐍 步骤 5/6: 创建虚拟环境...${NC}"
    cd $DEPLOY_DIR
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip -q
    ./venv/bin/pip install -r requirements.txt -q
    echo "   ✅ 完成"
    echo ""
    
    # 6. 创建 systemd 服务
    echo -e "${BLUE}⚙️  步骤 6/6: 创建 systemd 服务...${NC}"
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Learning Agent Public Knowledge Website
After=network.target

[Service]
Type=simple
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$DEPLOY_DIR
Environment="PATH=$DEPLOY_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$DEPLOY_DIR/venv/bin/python web/public_app.py --host 0.0.0.0 --port $PORT
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# 资源限制
LimitNOFILE=65535
Nice=10
IOSchedulingClass=idle

# 安全加固
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    
    # 启用并启动服务
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    
    sleep 3
    echo "   ✅ 完成"
    echo ""
    
    # 健康检查
    echo -e "${BLUE}🔍 健康检查...${NC}"
    sleep 2
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ 服务运行正常${NC}"
    else
        echo -e "${YELLOW}   ⚠️  服务启动中，请稍后检查${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}✅ systemd 部署完成！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${BLUE}📊 服务信息:${NC}"
    echo "   访问地址：http://localhost:$PORT/"
    echo "   服务名称：$SERVICE_NAME"
    echo ""
    echo -e "${BLUE}📋 管理命令:${NC}"
    echo "   查看状态：sudo systemctl status $SERVICE_NAME"
    echo "   查看日志：sudo journalctl -u $SERVICE_NAME -f"
    echo "   重启服务：sudo systemctl restart $SERVICE_NAME"
    echo "   停止服务：sudo systemctl stop $SERVICE_NAME"
    echo ""
}

deploy_docker() {
    PORT=$1
    
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}🐳 Docker 部署${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${BLUE}📋 部署信息:${NC}"
    echo "   部署目录：$DEPLOY_DIR"
    echo "   容器端口：$PORT"
    echo "   运行方式：Docker 容器"
    echo ""
    
    # 1. 停止旧服务
    echo -e "${BLUE}🛑 步骤 1/7: 停止旧服务...${NC}"
    sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
    docker stop $SERVICE_NAME 2>/dev/null || true
    docker rm $SERVICE_NAME 2>/dev/null || true
    echo "   ✅ 完成"
    echo ""
    
    # 2. 创建部署目录
    echo -e "${BLUE}📁 步骤 2/7: 创建部署目录...${NC}"
    sudo mkdir -p $DEPLOY_DIR
    sudo chown $(whoami):$(whoami) $DEPLOY_DIR
    echo "   ✅ 完成"
    echo ""
    
    # 3. 复制源码
    echo -e "${BLUE}📦 步骤 3/7: 复制源码...${NC}"
    for dir in web config docs services utils; do
        if [ -d "$SCRIPT_DIR/$dir" ]; then
            cp -r "$SCRIPT_DIR/$dir" $DEPLOY_DIR/
        fi
    done
    cp $SCRIPT_DIR/*.py $DEPLOY_DIR/ 2>/dev/null || true
    cp $SCRIPT_DIR/requirements.txt $DEPLOY_DIR/
    
    # 复制Dockerfile
    if [ -f "$SCRIPT_DIR/Dockerfile.public" ]; then
        cp $SCRIPT_DIR/Dockerfile.public $DEPLOY_DIR/
    fi
    echo "   ✅ 完成"
    echo ""
    
    # 4. 复制知识数据
    echo -e "${BLUE}💾 步骤 4/7: 复制知识数据...${NC}"
    mkdir -p $DEPLOY_DIR/data/{workflow_results,llm_audit_logs,logs}
    cp -r $SCRIPT_DIR/data/workflow_results/* $DEPLOY_DIR/data/workflow_results/ 2>/dev/null || true
    cp -r $SCRIPT_DIR/data/llm_audit_logs/* $DEPLOY_DIR/data/llm_audit_logs/ 2>/dev/null || true
    echo "   ✅ 完成"
    echo ""
    
    # 5. 配置环境变量
    echo -e "${BLUE}🔐 步骤 5/7: 配置环境变量...${NC}"
    cat > $DEPLOY_DIR/.env << EOF
# Learning Agent 公开知识展示网站 - Docker 部署
# 部署时间：$(date -Iseconds)

# 公开模式配置（强制）
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true

# 时区
TZ=Asia/Shanghai

# API Key（从原配置复制）
DASHSCOPE_API_KEY=$(grep DASHSCOPE_API_KEY $SCRIPT_DIR/.env 2>/dev/null | cut -d'=' -f2 || echo "")
EOF
    echo "   ✅ .env 已配置"
    echo ""
    
    # 6. 构建 Docker 镜像
    echo -e "${BLUE}🐳 步骤 6/7: 构建 Docker 镜像...${NC}"
    cd $DEPLOY_DIR
    
    if [ -f "Dockerfile.public" ]; then
        docker build -f Dockerfile.public -t learning-agent:public-release .
    else
        echo -e "${YELLOW}   ⚠️  Dockerfile.public 不存在，跳过构建${NC}"
    fi
    echo "   ✅ 完成"
    echo ""
    
    # 7. 启动容器
    echo -e "${BLUE}🚀 步骤 7/7: 启动容器...${NC}"
    docker run -d \
        --name $SERVICE_NAME \
        --port $PORT:5001 \
        --restart always \
        -v $DEPLOY_DIR/data:/app/data \
        -v $DEPLOY_DIR/config:/app/config \
        --env-file $DEPLOY_DIR/.env \
        learning-agent:public-release 2>/dev/null || \
    docker run -d \
        --name $SERVICE_NAME \
        -p $PORT:5001 \
        --restart always \
        -v $DEPLOY_DIR/data:/app/data \
        -v $DEPLOY_DIR:/app \
        -w /app \
        --env PUBLIC_MODE=true \
        python:3.11-slim \
        bash -c "pip install -r requirements.txt && python web/public_app.py --host 0.0.0.0 --port 5001"
    
    echo "   ✅ 完成"
    echo ""
    
    # 等待服务启动
    echo -e "${BLUE}⏳ 等待服务启动...${NC}"
    sleep 5
    
    # 健康检查
    echo -e "${BLUE}🔍 健康检查...${NC}"
    for i in {1..10}; do
        if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
            echo -e "${GREEN}   ✅ 服务健康检查通过${NC}"
            break
        fi
        if [ $i -eq 10 ]; then
            echo -e "${YELLOW}   ⚠️  服务启动中，请稍后检查${NC}"
        else
            echo "   等待中... ($i/10)"
            sleep 2
        fi
    done
    
    echo ""
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}✅ Docker 部署完成！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${BLUE}📊 服务信息:${NC}"
    echo "   访问地址：http://localhost:$PORT/"
    echo "   容器名称：$SERVICE_NAME"
    echo ""
    echo -e "${BLUE}📋 管理命令:${NC}"
    echo "   查看状态：docker ps | grep $SERVICE_NAME"
    echo "   查看日志：docker logs -f $SERVICE_NAME"
    echo "   重启服务：docker restart $SERVICE_NAME"
    echo "   停止服务：docker stop $SERVICE_NAME"
    echo ""
}

# 主函数
main() {
    MODE=""
    PORT=32015
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --port)
                PORT="$2"
                shift 2
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
    
    if [ -z "$MODE" ]; then
        echo -e "${RED}❌ 请指定部署模式：--mode systemd 或 --mode docker${NC}"
        show_help
        exit 1
    fi
    
    case $MODE in
        systemd)
            deploy_systemd $PORT
            ;;
        docker)
            deploy_docker $PORT
            ;;
        *)
            echo -e "${RED}❌ 不支持的部署模式：$MODE${NC}"
            echo "   支持：systemd, docker"
            exit 1
            ;;
    esac
}

main "$@"