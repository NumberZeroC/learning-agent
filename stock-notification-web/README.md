# Stock-Agent Web

Stock-Agent 股票分析平台的 Web 展示界面

## 📁 项目结构

```
stock-agent-web/
├── app.py                    # Flask 应用入口
├── config.py                 # 配置文件
├── requirements.txt          # Python 依赖
├── start.sh                  # 启动脚本
├── api/
│   └── v1/
│       ├── stocks.py        # 选股 API
│       ├── monitor.py       # 监控 API
│       └── config_routes.py # 配置 API
├── services/
│   ├── stock_service.py     # 选股服务
│   ├── monitor_service.py   # 监控服务
│   └── config_service.py    # 配置服务
├── templates/               # HTML 模板
└── static/                  # 静态文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/stock-agent-web

# 使用现有虚拟环境（stock-agent 的 venv311）
# 或创建新的
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
# 方式一：使用启动脚本
./start.sh

# 方式二：直接运行
python3 app.py
```

### 3. 访问

- **首页:** http://localhost:5000
- **API:** http://localhost:5000/api/v1

## 📡 API 接口

### 选股功能

| 接口 | 说明 |
|------|------|
| `GET /api/v1/stocks/recommend` | 获取选股推荐 |
| `GET /api/v1/stocks/sentiment` | 获取市场情绪 |
| `GET /api/v1/stocks/sectors/rank` | 获取板块排名 |
| `GET /api/v1/stocks/{code}/detail` | 获取个股详情 |

### 监控功能

| 接口 | 说明 |
|------|------|
| `GET /api/v1/monitor/stocks` | 获取持仓监控列表 |
| `GET /api/v1/monitor/stocks/{code}` | 获取个股监控详情 |
| `GET /api/v1/monitor/report` | 获取监控报告 |
| `GET /api/v1/monitor/history` | 获取历史监控记录 |

### 配置功能

| 接口 | 说明 |
|------|------|
| `GET /api/v1/config` | 获取配置 |
| `PUT /api/v1/config` | 更新配置 |
| `POST /api/v1/config/monitor-stocks` | 添加监控股票 |
| `DELETE /api/v1/config/monitor-stocks/{code}` | 删除监控股票 |
| `GET /api/v1/config/schedule/status` | 获取定时任务状态 |

## 📝 API 使用示例

### 获取选股推荐

```bash
curl http://localhost:5000/api/v1/stocks/recommend
```

### 获取持仓监控

```bash
curl http://localhost:5000/api/v1/monitor/stocks
```

### 添加监控股票

```bash
curl -X POST http://localhost:5000/api/v1/config/monitor-stocks \
  -H "Content-Type: application/json" \
  -d '{"code": "600519", "name": "贵州茅台"}'
```

## 🔧 配置

编辑 `stock-agent/config.yaml` 配置：

- 监控股票列表
- 推荐板块
- 信号阈值
- 定时任务时间

## 📊 数据来源

Web 应用从以下目录读取数据：

```
stock-agent/data/reports/
├── evening_analysis_*.md    # 晚间分析
├── evening_analysis_*.json  # 晚间分析数据
├── recommendation_*.md      # 推荐报告
├── recommendation_*.json    # 推荐数据
├── monitor_*.md            # 监控报告
└── analysis_*.json         # 分析数据
```

## 🛠️ 开发

### 运行模式

```bash
# 开发模式（自动重载）
FLASK_ENV=development python3 app.py

# 生产模式
FLASK_ENV=production gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 日志

```bash
# 查看日志
tail -f stock-agent/logs/web.log
```

## 📋 待办事项

- [ ] 完善前端页面
- [ ] 添加用户认证
- [ ] 添加实时推送（WebSocket）
- [ ] 添加数据持久化（SQLite）
- [ ] 添加更多图表

## 📄 许可证

MIT License
