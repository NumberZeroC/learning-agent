# 股灵通 - 股票分析 Agent
FROM node:22-bookworm-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖和 Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# 复制应用代码
COPY . .

# 设置执行权限
RUN chmod +x *.py *.sh 2>/dev/null || true

# 默认命令
CMD ["python3", "monitor.py"]
