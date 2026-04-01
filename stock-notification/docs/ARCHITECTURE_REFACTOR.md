# Stock-Agent 解耦架构文档

## 🏗️ 架构重构

**重构日期：** 2026-03-24  
**目标：** 数据获取与报告生成解耦

---

## 📐 新架构设计

### 三层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      数据获取层 (Fetchers)                       │
│  services/market_fetcher.py    │  市场数据（指数、龙虎榜）       │
│  services/capital_fetcher.py   │  资金流数据（板块、个股）       │
│  services/ai_news_fetcher.py   │  AI 新闻数据（情感分析）         │
│  services/data_aggregator.py   │  数据聚合服务                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据存储层 (Data Store)                     │
│  data/market/YYYYMMDD.json     │  市场数据                      │
│  data/capital/YYYYMMDD.json    │  资金流数据                    │
│  data/ai_news/YYYYMMDD.json    │  AI 新闻数据                   │
│  data/aggregated/YYYYMMDD.json │  聚合数据                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      报告生成层 (Reporters)                      │
│  reporters/evening_reporter.py │  晚间总结报告                   │
│  reporters/morning_reporter.py │  早盘推荐报告（待实现）         │
│  reporters/monitor_reporter.py │  持仓监控报告（待实现）         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 设计原则

### 1. 职责分离

- **数据获取层** - 只负责获取和存储数据，不生成报告
- **报告生成层** - 只负责读取数据和生成报告，不获取数据

### 2. 数据持久化

- 所有数据都存储到文件系统
- 支持历史数据回溯
- 多个报告可以共享同一份数据

### 3. 容错性

- 数据获取失败不影响报告生成（可使用旧数据）
- 报告生成失败不影响数据获取
- 每个模块独立运行

### 4. 可扩展性

- 新增数据源只需添加新的 Fetcher
- 新增报告类型只需添加新的 Reporter
- 不影响现有模块

---

## 📁 目录结构

```
stock-agent/
├── services/                    # 数据获取服务
│   ├── market_fetcher.py       # 市场数据获取
│   ├── capital_fetcher.py      # 资金流数据获取
│   ├── ai_news_fetcher.py      # AI 新闻数据获取
│   └── data_aggregator.py      # 数据聚合服务
│
├── reporters/                   # 报告生成服务
│   ├── evening_reporter.py     # 晚间报告生成
│   ├── morning_reporter.py     # 早盘报告生成（待实现）
│   └── monitor_reporter.py     # 监控报告生成（待实现）
│
├── data/                        # 数据存储
│   ├── market/                 # 市场数据
│   ├── capital/                # 资金流数据
│   ├── ai_news/                # AI 新闻数据
│   └── aggregated/             # 聚合数据
│
├── scripts/                     # 脚本
│   ├── fetch_data.sh           # 数据获取脚本
│   └── generate_report.sh      # 报告生成脚本
│
└── logs/                        # 日志
    ├── data_fetch_*.log        # 数据获取日志
    └── report_gen_*.log        # 报告生成日志
```

---

## 🔧 使用方法

### 方式 1：分步执行

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 1. 获取数据
./scripts/fetch_data.sh 20260324

# 2. 生成报告
./scripts/generate_report.sh 20260324
```

### 方式 2：直接调用服务

```bash
# 获取市场数据
./venv311/bin/python3 services/market_fetcher.py --date 20260324

# 获取资金流数据
./venv311/bin/python3 services/capital_fetcher.py --date 20260324

# 获取 AI 新闻数据
./venv311/bin/python3 services/ai_news_fetcher.py --date 20260324

# 生成晚间报告
./venv311/bin/python3 reporters/evening_reporter.py --date 20260324
```

### 方式 3：使用数据聚合器

```bash
# 一次性获取所有数据
./venv311/bin/python3 services/data_aggregator.py --date 20260324

# 生成报告（从聚合数据读取）
./venv311/bin/python3 reporters/evening_reporter.py --date 20260324
```

---

## 📊 数据格式

### 市场数据 (data/market/YYYYMMDD.json)

```json
{
  "trade_date": "20260324",
  "fetched_at": "2026-03-24T22:00:00",
  "indices": {
    "shanghai": {"name": "上证指数", "close": 3881.28, "change_pct": 1.78},
    "shenzhen": {"name": "深证成指", "close": 13536.56, "change_pct": 1.43}
  },
  "top_list": [...],
  "top_inst": [...]
}
```

### 资金流数据 (data/capital/YYYYMMDD.json)

```json
{
  "trade_date": "20260324",
  "fetched_at": "2026-03-24T22:00:00",
  "sector_flows": [
    {"sector": "银行", "net_flow": 176294, "inst_net": 0, ...}
  ],
  "market_flow": [...]
}
```

### AI 新闻数据 (data/ai_news/YYYYMMDD.json)

```json
{
  "trade_date": "20260324",
  "fetched_at": "2026-03-24T22:00:00",
  "news": [...],
  "sentiment": {
    "overall_score": 51.2,
    "overall_level": "neutral",
    "hot_topics": ["Claude (6)", "Anthropic (3)"]
  }
}
```

### 聚合数据 (data/aggregated/YYYYMMDD.json)

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

## ⏰ 定时任务配置

### 更新 crontab

```bash
crontab -e
```

### 数据获取任务

```bash
# 每个交易日 16:00 获取盘后数据（周一到周五）
0 16 * * 1-5 /home/admin/.openclaw/workspace/stock-agent/scripts/fetch_data.sh

# 每天早上 08:00 获取隔夜数据（周一到周五）
0 8 * * 1-5 /home/admin/.openclaw/workspace/stock-agent/scripts/fetch_data.sh
```

### 报告生成任务

```bash
# 每天晚上 20:25 生成晚间报告（周一到周五）
# 在 AI 新闻推送 (20:00) 之后，晚间总结 (20:30) 之前
25 20 * * 1-5 /home/admin/.openclaw/workspace/stock-agent/scripts/generate_report.sh
```

---

## 🔄 迁移计划

### 阶段 1：并行运行（当前）

- 新架构和旧架构同时运行
- 验证数据准确性
- 测试稳定性

### 阶段 2：切换（2026-03-25）

- 更新定时任务使用新脚本
- 旧代码保留作为备份

### 阶段 3：优化（2026-03-26 及以后）

- 实现 morning_reporter.py
- 实现 monitor_reporter.py
- 添加更多数据源

---

## ✅ 优势对比

| 维度 | 旧架构 | 新架构 |
|------|--------|--------|
| **耦合度** | 高（数据 + 报告混合） | 低（完全解耦） |
| **容错性** | 低（一处失败全失败） | 高（模块独立） |
| **可维护性** | 中 | 高 |
| **可扩展性** | 低 | 高 |
| **数据回溯** | 困难 | 简单 |
| **报告共享数据** | 不支持 | 支持 |

---

## 📞 故障排查

### 数据获取失败

```bash
# 检查日志
cat logs/data_fetch_*.log

# 手动测试
./venv311/bin/python3 services/data_aggregator.py --date 20260324
```

### 报告生成失败

```bash
# 检查日志
cat logs/report_gen_*.log

# 检查数据是否存在
ls -la data/aggregated/

# 手动测试
./venv311/bin/python3 reporters/evening_reporter.py --date 20260324
```

---

**文档版本：** 1.0  
**最后更新：** 2026-03-24  
**维护者：** Stock-Agent Team
