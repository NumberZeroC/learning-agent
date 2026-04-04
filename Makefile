# Learning Agent Makefile

.PHONY: help install test run clean lint format

# 默认目标
help:
	@echo "Learning Agent - 可用命令:"
	@echo ""
	@echo "  make install    - 安装依赖"
	@echo "  make test       - 运行测试"
	@echo "  make run        - 启动工作流"
	@echo "  make web        - 启动 Web 服务"
	@echo "  make clean      - 清理缓存和临时文件"
	@echo "  make lint       - 代码检查"
	@echo "  make format     - 代码格式化"
	@echo ""

# 安装依赖
install:
	@echo "📦 安装依赖..."
	pip3 install -r requirements.txt
	@echo "✅ 安装完成"

# 运行测试
test:
	@echo "🧪 运行测试..."
	python3 -m pytest tests/ -v --tb=short
	@echo "✅ 测试完成"

# 启动工作流
run:
	@echo "🚀 启动工作流..."
	./start_workflow.sh

# 启动 Web 服务
web:
	@echo "🌐 启动 Web 服务..."
	cd web && ./start_web.sh

# 清理缓存和临时文件
clean:
	@echo "🧹 清理中..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	rm -rf logs/*.log 2>/dev/null || true
	@echo "✅ 清理完成"

# 代码检查（如已安装 flake8）
lint:
	@echo "🔍 代码检查..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 . --exclude=venv,env,.venv,build,dist; \
	else \
		echo "⚠️  flake8 未安装，跳过检查"; \
		echo "   安装：pip3 install flake8"; \
	fi

# 代码格式化（如已安装 black）
format:
	@echo "🎨 代码格式化..."
	@if command -v black >/dev/null 2>&1; then \
		black . --exclude=venv/|env/|.venv/|build/|dist/; \
	else \
		echo "⚠️  black 未安装，跳过格式化"; \
		echo "   安装：pip3 install black"; \
	fi
