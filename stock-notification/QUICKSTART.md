# 🚀 Stock-Agent 快速入门

## 1. 环境检查

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 检查 Python 环境
./venv311/bin/python --version

# 检查配置
cat config.yaml | head -20
```

---

## 2. 运行分析

### 晚间分析（盘后总结）

```bash
./venv311/bin/python evening_analysis.py
```

输出：
- `data/reports/evening_summary_YYYY-MM-DD.md`
- `data/reports/evening_summary_YYYY-MM-DD.json`

### 早盘推荐（开盘前）

```bash
./venv311/bin/python morning_recommend.py
```

输出：
- `data/reports/morning_recommend_YYYY-MM-DD.md`
- `data/reports/morning_recommend_YYYY-MM-DD.json`

---

## 3. 查看报告

```bash
# 最新晚间报告
cat data/reports/evening_summary_$(date +%Y-%m-%d).md

# 最新早盘报告
cat data/reports/morning_recommend_$(date +%Y-%m-%d).md
```

---

## 4. 定时任务

### 安装 crontab

```bash
crontab crontab.txt
```

### 任务时间

| 时间 | 任务 |
|------|------|
| 08:00 | 日志清理 |
| 09:30 | 早盘推荐 + 监控 |
| 15:00 | 最后一次监控 |
| 20:00 | 晚间分析 |

### 查看状态

```bash
# 查看 crontab
crontab -l

# 查看日志
tail -20 logs/cron_morning.log
tail -20 logs/cron_evening.log
```

---

## 5. 配置说明

### 修改分析板块

编辑 `config.yaml`：

```yaml
sectors:
  - 半导体
  - 人工智能
  - 新能源
  - 医药生物
  - 消费电子
  - 汽车
```

### 配置 Tushare

```yaml
tushare:
  token: your_token_here
```

获取 Token：https://tushare.pro

---

## 6. 故障排查

### 数据获取失败

```bash
# 检查网络连接
curl -I https://www.akshare.xyz

# 检查 Tushare 积分
./venv311/bin/python -c "import tushare as ts; pro = ts.pro_api('your_token'); print(pro.token())"
```

### 查看缓存

```bash
ls -la data/cache/
rm -rf data/cache/*  # 清理缓存
```

---

## 7. 下一步

- 阅读 [系统说明](docs/ANALYSIS_SYSTEM.md) 了解详细架构
- 阅读 [USAGE.md](USAGE.md) 了解完整功能
- 查看 [config.yaml](config.yaml) 了解所有配置项

---

*有问题？查看 logs/ 目录下的日志文件*
