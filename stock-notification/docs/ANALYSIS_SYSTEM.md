# 📊 Stock-Agent 分析系统说明

## 系统概述

本系统包含两个核心分析模块：

1. **晚间市场分析** - 每日盘后总结
2. **早盘推荐报告** - 次日开盘前推荐

---

## 🌙 晚间市场分析

### 功能

- **大盘走势分析**：上证指数、深证成指、创业板指等五大指数
- **全天新闻收集**：从同花顺、金融界、证券时报等媒体抓取新闻
- **板块资金流分析**：分析各板块主力资金流入/流出情况
- **新闻情绪分析**：评估各板块新闻面情绪
- **重点关注板块**：综合资金流和情绪选出热点板块
- **明日策略建议**：仓位建议和操作策略

### 输出文件

| 文件 | 说明 |
|------|------|
| `data/reports/evening_summary_YYYY-MM-DD.md` | Markdown 格式报告 |
| `data/reports/evening_summary_YYYY-MM-DD.json` | JSON 格式数据（供早盘使用） |

### 执行时间

**每个交易日 20:00** 自动执行

```bash
0 20 * * 1-5 /home/admin/.openclaw/workspace/stock-agent/scheduled_evening.sh
```

### 手动执行

```bash
cd /home/admin/.openclaw/workspace/stock-agent
./venv311/bin/python evening_analysis.py
```

---

## 📈 早盘推荐报告

### 功能

- **加载晚间报告**：读取前一天的晚间分析数据
- **早间新闻获取**：收集隔夜消息和早盘新闻
- **竞价数据分析**：获取集合竞价数据（交易时间）
- **热点板块推荐**：最多推荐 5 个热点板块
- **龙头股票推荐**：每个热点板块推荐 3 只龙头股

### 推荐逻辑

1. **热点板块选择**：
   - 晚间资金流向（权重 40%）
   - 新闻情绪得分（权重 30%）
   - 早间新闻热度（权重 30%）

2. **龙头股选择**：
   - 资金流得分（权重 50%）
   - 涨幅得分（权重 30%）
   - 竞价表现（权重 20%）

### 输出文件

| 文件 | 说明 |
|------|------|
| `data/reports/morning_recommend_YYYY-MM-DD.md` | Markdown 格式报告 |
| `data/reports/morning_recommend_YYYY-MM-DD.json` | JSON 格式数据 |

### 执行时间

**每个交易日 9:30** 自动执行

```bash
30 9 * * 1-5 /home/admin/.openclaw/workspace/stock-agent/scheduled_morning.sh
```

### 手动执行

```bash
cd /home/admin/.openclaw/workspace/stock-agent
./venv311/bin/python morning_recommend.py
```

---

## 📋 报告格式示例

### 晚间报告结构

```markdown
# 🌙 晚间市场总结报告

## 📊 大盘走势
- 主要指数表现表格
- 市场总结

## 📰 新闻概览
- 新闻来源、总数、覆盖板块

## 🏆 板块资金流 TOP10
- 主力流入/流出/净流入

## 📈 新闻情绪分析
- 各板块情绪得分

## 🎯 重点关注板块
- 综合推荐的热点板块

## 💡 明日策略建议
- 市场判断、仓位建议、操作策略
```

### 早盘报告结构

```markdown
# 📈 早盘推荐报告

## 📋 隔夜回顾
- 晚间总结要点
- 早间新闻摘要

## 🔥 今日热点板块推荐
- 最多 5 个热点板块
- 每个板块 3 只龙头股

## 💡 今日操作策略
- 重点关注、仓位建议、风险提示

## 📊 竞价观察
- 涨停/跌停竞价数据
```

---

## 🔧 配置说明

### 配置文件

`config.yaml` 中可配置：

```yaml
# 分析的板块列表
sectors:
  - 半导体
  - 人工智能
  - 新能源
  - 医药生物
  - ...

# 新闻关键词
news_keywords:
  positive:
    - 利好
    - 突破
    - 增长
  negative:
    - 利空
    - 下跌
    - 风险
```

### 数据源

| 数据 | 来源 |
|------|------|
| 大盘指数 | Tushare Pro / AKShare |
| 板块资金流 | AKShare / 本地缓存 |
| 财经新闻 | 同花顺、金融界、证券时报等 |
| 实时行情 | AKShare / Tushare Pro |

---

## 📁 文件结构

```
stock-agent/
├── evening_analysis.py      # 晚间分析脚本
├── morning_recommend.py     # 早盘推荐脚本
├── scheduled_evening.sh     # 晚间定时任务
├── scheduled_morning.sh     # 早盘定时任务
├── cleanup_logs.sh          # 日志清理脚本
├── data/
│   ├── reports/             # 报告输出目录
│   │   ├── evening_summary_*.md
│   │   ├── evening_summary_*.json
│   │   ├── morning_recommend_*.md
│   │   ├── morning_recommend_*.json
│   │   └── monitor/         # 监控报告
│   └── archives/            # 归档压缩包
└── logs/                    # 日志目录
```

---

## ⚠️ 注意事项

1. **非交易时间**：资金流数据可能为 0，主要依赖新闻情绪分析
2. **数据源稳定性**：AKShare 可能不稳定，已配置故障转移机制
3. **Tushare 积分**：需要 600 积分以上才能获取完整数据
4. **竞价数据**：仅在 9:15-9:30 可获取真实竞价数据

---

## 📊 报告保留策略

| 报告类型 | 保留策略 |
|----------|----------|
| 晚间总结 | 保留 14 天，之前打包压缩 |
| 早盘推荐 | 保留 14 天，之前打包压缩 |
| 监控报告 | 保留 1 天，之前打包压缩 |
| 压缩包 | 最多保留 10 个 |

由 `cleanup_logs.sh` 每天 8:00 自动执行清理。

---

*文档更新时间：2026-03-18*
