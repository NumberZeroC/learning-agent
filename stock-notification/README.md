# 📈 Stock-Agent 智能股票分析系统

自动化股票分析系统，提供晚间市场总结和早盘推荐报告。

---

## 🚀 快速开始

### 查看最新报告

```bash
# 晚间总结报告
cat data/reports/evening_summary_$(date +%Y-%m-%d).md

# 早盘推荐报告
cat data/reports/morning_recommend_$(date +%Y-%m-%d).md
```

### 手动运行

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 运行晚间分析
./venv311/bin/python evening_analysis.py

# 运行早盘推荐
./venv311/bin/python morning_recommend.py
```

---

## 📋 功能说明

| 模块 | 时间 | 说明 |
|------|------|------|
| 🌙 晚间分析 | 20:00 | 大盘走势、新闻情绪、资金流分析 |
| 📈 早盘推荐 | 9:30 | 5 个热点板块 + 各 3 只龙头股 |
| 🎯 交易监控 | 30 分钟/次 | 交易时间每 30 分钟监控持仓 |
| 🧹 日志清理 | 08:00 | 自动清理旧报告和日志 |

---

## 📁 项目结构

```
stock-agent/
├── evening_analysis.py      # 晚间分析脚本
├── morning_recommend.py     # 早盘推荐脚本
├── scheduled_*.sh           # 定时任务脚本
├── cleanup_logs.sh          # 日志清理脚本
├── crontab.txt              # Crontab 配置
├── config.yaml              # 配置文件
├── src/                     # 核心模块
├── data/
│   ├── reports/             # 报告输出
│   ├── archives/            # 归档压缩包
│   └── cache/               # 数据缓存
└── logs/                    # 日志目录
```

---

## 📖 文档

- [系统说明](docs/ANALYSIS_SYSTEM.md) - 详细的系统架构和使用说明
- [QUICKSTART.md](QUICKSTART.md) - 快速入门指南
- [USAGE.md](USAGE.md) - 使用手册

---

## ⚙️ 配置

编辑 `config.yaml` 配置：

```yaml
# 分析板块
sectors:
  - 半导体
  - 人工智能
  - 新能源
  - 医药生物

# Tushare Token
tushare:
  token: your_token_here
```

---

## 📊 报告保留策略

| 类型 | 保留 | 处理 |
|------|------|------|
| 晚间/早盘报告 | 14 天 | 超期打包压缩 |
| 监控报告 | 1 天 | 超期打包压缩 |
| 压缩包 | 10 个 | 超数删除最旧 |

---

## 🔧 维护

### 查看定时任务

```bash
crontab -l
```

### 更新定时任务

```bash
crontab crontab.txt
```

### 查看日志

```bash
tail -f logs/cron_evening.log
tail -f logs/cron_morning.log
```

---

## ⚠️ 免责声明

本系统仅供学习和研究使用，不构成投资建议。股市有风险，投资需谨慎。

---

*最后更新：2026-03-18*
