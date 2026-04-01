# 公共数据目录文档

**位置：** `/home/admin/.openclaw/workspace/data/`

**创建日期：** 2026-03-24

---

## 📁 目录结构

```
data/
├── stock-agent/          # Stock-Agent 数据
│   ├── market/          # 市场数据
│   │   └── YYYYMMDD.json
│   ├── capital/         # 资金流数据
│   │   └── YYYYMMDD.json
│   ├── ai_news/         # AI 新闻数据
│   │   └── YYYYMMDD.json
│   ├── aggregated/      # 聚合数据
│   │   └── YYYYMMDD.json
│   ├── cache/           # 缓存数据
│   ├── archives/        # 归档数据
│   ├── notifications/   # 通知数据
│   └── reports/         # 报告文件
│       ├── evening_summary_*.json
│       ├── morning_recommend_*.json
│       └── stock_monitor_*.json
│
├── other-project/       # 其他项目数据（未来扩展）
│   └── ...
│
└── shared/              # 共享数据（未来扩展）
    └── ...
```

---

## 🎯 设计目标

### 1. 数据共享

多个项目可以共享同一份数据：

```
stock-agent  →  data/stock-agent/
stock-agent-web  →  data/stock-agent/
future-project →  data/future-project/
```

### 2. 解耦

项目代码和数据分离：

```
stock-agent/      # 代码目录
└── services/     # 服务代码

data/stock-agent/ # 数据目录
└── market/       # 市场数据
```

### 3. 扩展性

新项目名称空间预留：

```
data/
├── stock-agent/      # 现有项目
├── ai-trader/        # 未来项目
├── portfolio-mgr/    # 未来项目
└── shared/           # 共享数据
```

---

## 📊 数据格式

### 市场数据 (stock-agent/market/YYYYMMDD.json)

```json
{
  "trade_date": "20260324",
  "fetched_at": "2026-03-24T22:00:00",
  "indices": {
    "shanghai": {"name": "上证指数", "close": 3881.28, "change_pct": 1.78}
  },
  "top_list": [...],
  "top_inst": [...]
}
```

### 资金流数据 (stock-agent/capital/YYYYMMDD.json)

```json
{
  "trade_date": "20260324",
  "fetched_at": "2026-03-24T22:00:00",
  "sector_flows": [...],
  "market_flow": [...]
}
```

### AI 新闻数据 (stock-agent/ai_news/YYYYMMDD.json)

```json
{
  "trade_date": "20260324",
  "fetched_at": "2026-03-24T22:00:00",
  "news": [...],
  "sentiment": {...}
}
```

### 聚合数据 (stock-agent/aggregated/YYYYMMDD.json)

```json
{
  "trade_date": "20260324",
  "aggregated_at": "2026-03-24T22:00:00",
  "market": {...},
  "capital": {...},
  "ai_news": {...}
}
```

---

## 🔧 配置方式

### Stock-Agent 配置

```python
# services/market_fetcher.py
self.data_dir = Path(__file__).parent.parent.parent.parent / 'data' / 'stock-agent' / 'market'
```

### Stock-Agent-Web 配置

```python
# config.py
WORKSPACE_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(WORKSPACE_DIR, 'data', 'stock-agent')
```

---

## 📝 使用示例

### 示例 1：读取市场数据

```python
from pathlib import Path

data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent/market')
data_file = data_dir / '20260324.json'

with open(data_file, 'r') as f:
    market_data = json.load(f)
```

### 示例 2：写入资金流数据

```python
from pathlib import Path
import json

data_dir = Path('/home/admin/.openclaw/workspace/data/stock-agent/capital')
data_dir.mkdir(parents=True, exist_ok=True)

data_file = data_dir / '20260324.json'

with open(data_file, 'w') as f:
    json.dump(capital_data, f, ensure_ascii=False, indent=2)
```

### 示例 3：跨项目共享数据

```python
# 项目 A：写入数据
data_dir = Path('/home/admin/.openclaw/workspace/data/shared/market')
save_market_data(data_dir / 'latest.json', data)

# 项目 B：读取数据
data_dir = Path('/home/admin/.openclaw/workspace/data/shared/market')
data = load_market_data(data_dir / 'latest.json')
```

---

## 🗂️ 数据生命周期

### 热数据（最近 7 天）

- 位置：`data/stock-agent/*/`
- 访问频率：高
- 清理策略：保留

### 温数据（7-30 天）

- 位置：`data/stock-agent/*/`
- 访问频率：中
- 清理策略：可选压缩

### 冷数据（30 天以上）

- 位置：`data/stock-agent/archives/`
- 访问频率：低
- 清理策略：归档或清理

---

## 🔒 权限管理

### 文件权限

```bash
# 设置目录权限
chmod 755 /home/admin/.openclaw/workspace/data/
chmod 755 /home/admin/.openclaw/workspace/data/stock-agent/

# 设置文件权限
chmod 644 /home/admin/.openclaw/workspace/data/stock-agent/market/*.json
```

### 访问控制

- 同一 workspace 下的项目可以自由访问
- 跨 workspace 访问需要权限配置
- 敏感数据（如 API token）不存储在公共数据目录

---

## 📈 未来扩展

### 新增项目

```bash
# 1. 创建项目数据目录
mkdir -p /home/admin/.openclaw/workspace/data/new-project

# 2. 配置项目使用公共数据目录
# 在项目中设置 data_dir 路径

# 3. 更新本文档
```

### 共享数据区

```bash
# 创建共享数据目录
mkdir -p /home/admin/.openclaw/workspace/data/shared

# 存放多个项目共享的数据
# 如：市场数据、新闻数据、配置数据等
```

---

## 📞 故障排查

### 问题 1：找不到数据目录

```bash
# 检查目录是否存在
ls -la /home/admin/.openclaw/workspace/data/

# 检查软链接
ls -la /home/admin/.openclaw/workspace/stock-agent/data
```

### 问题 2：权限错误

```bash
# 检查权限
ls -la /home/admin/.openclaw/workspace/data/stock-agent/

# 修复权限
chmod -R 755 /home/admin/.openclaw/workspace/data/stock-agent/
```

### 问题 3：数据不一致

```bash
# 检查数据文件时间戳
stat /home/admin/.openclaw/workspace/data/stock-agent/market/20260324.json

# 对比多个副本
diff /path/to/copy1.json /path/to/copy2.json
```

---

**文档版本：** 1.0  
**最后更新：** 2026-03-24  
**维护者：** Stock-Agent Team
