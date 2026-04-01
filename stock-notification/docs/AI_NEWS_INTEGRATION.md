# AI 新闻监控模块 - 集成文档

## 📦 模块位置

```
/home/admin/.openclaw/workspace/stock-agent/
├── src/
│   └── ai_news_monitor.py      # AI 新闻监控模块
├── scripts/
│   └── ai_news_daily.sh        # 定时执行脚本
├── data/
│   └── reports/
│       └── ai_news/            # AI 新闻报告目录
│           ├── ai_news_*.md    # Markdown 报告
│           └── ai_news_*.json  # JSON 数据
└── logs/
    └── ai_news_*.log           # 执行日志
```

---

## 🎯 功能特性

### 1. 多源新闻获取

| 类别 | 新闻源 | 状态 |
|------|--------|------|
| **国际科技** | The Verge AI | ✅ |
| | TechCrunch AI | ✅ |
| | OpenAI News | ⚠️ (403) |
| | Anthropic News | ✅ |
| | Google AI Blog | ⚠️ (SSL) |
| **中文媒体** | 36Kr AI | ⚠️ (404) |
| | 机器之心 | ✅ |
| | 量子位 | ✅ |
| **社区** | Hacker News | ⏸️ |
| | Reddit ML | ⏸️ |
| **学术** | arXiv AI | ⏸️ |

### 2. 个性化建议

基于用户画像生成：
- **机会识别** - 融资/产品/技术趋势
- **风险警示** - 政策/合规/欺诈
- **行动建议** - 高/中/低优先级

### 3. QQ 推送

- **时间：** 每天 20:00
- **目标：** qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52
- **格式：** 简洁易读，包含热点 + 建议 + 金句

---

## 🔧 使用方式

### 手动执行

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 执行一次（推送 QQ）
./venv311/bin/python3 src/ai_news_monitor.py --once

# 执行一次（不推送 QQ）
./venv311/bin/python3 src/ai_news_monitor.py --once --no-qq

# 执行一次（不导出报告）
./venv311/bin/python3 src/ai_news_monitor.py --once --no-export
```

### 定时任务

```bash
# 查看定时任务
crontab -l

# 输出：
0 20 * * * /home/admin/.openclaw/workspace/stock-agent/scripts/ai_news_daily.sh
```

### 查看日志

```bash
# 今日日志
cat logs/ai_news_$(date +%Y-%m-%d).log

# Cron 日志
cat logs/ai_news_cron.log
```

---

## 📊 与 stock-agent 集成

### 1. 数据共享

AI 新闻数据可与以下模块共享：

| 模块 | 集成方式 |
|------|----------|
| **evening_analysis.py** | 添加 AI 新闻板块到晚间总结 |
| **morning_recommend.py** | 根据 AI 新闻调整早盘推荐 |
| **monitor.py** | 监控股票相关的 AI 公司动态 |
| **sentiment_analyzer.py** | AI 新闻情感分析影响股价 |

### 2. 联合分析示例

```python
# 在 evening_analysis.py 中添加
from ai_news_monitor import AINewsMonitor

ai_monitor = AINewsMonitor()
ai_news = ai_monitor.fetch_all_news(limit_sources=5)

# 分析 AI 新闻对持仓股票的影响
for stock in holdings:
    related_news = [n for n in ai_news if stock['name'] in n['title']]
    if related_news:
        print(f"{stock['name']} 相关 AI 新闻：{len(related_news)} 条")
```

### 3. 报告整合

晚间总结报告结构：

```markdown
# 晚间市场总结

## 📊 市场概览
- 上证指数：xxx
- 成交量：xxx

## 🤖 AI 行业动态
- AI 新闻摘要（来自 ai_news_monitor）
- 相关股票影响分析

## 📈 持仓分析
...
```

---

## 🔍 新闻源优化

### 当前问题

| 新闻源 | 问题 | 解决方案 |
|--------|------|----------|
| OpenAI News | 403 Forbidden | 使用 RSS 或 API |
| Google AI Blog | SSL 错误 | 跳过 SSL 验证 |
| 36Kr AI | 404 Not Found | 更新 URL |

### 建议添加的新闻源

```python
# 添加到 news_sources 列表
{
    "name": "InfoQ AI",
    "url": "https://www.infoq.cn/ai/",
    "type": "news",
    "language": "zh",
    "priority": 2
},
{
    "name": "Reddit r/artificial",
    "url": "https://www.reddit.com/r/artificial/",
    "type": "community",
    "language": "en",
    "priority": 2
},
{
    "name": "Product Hunt AI",
    "url": "https://www.producthunt.com/topics/artificial-intelligence",
    "type": "product",
    "language": "en",
    "priority": 2
}
```

---

## 📝 配置选项

### 用户画像配置

编辑 `src/ai_news_monitor.py` 中的 `user_profile`：

```python
self.user_profile = {
    "name": "老板",
    "experience": "6 年开发",
    "background": "华为云计算 5 年",
    "current": "AI 应用创业",
    "goal": "抓住 AI 风口"
}
```

### 推送目标配置

```python
# 在 _send_to_qq 方法中修改
qq_target = "qqbot:c2c:YOUR_QQ_ID"
```

### 缓存配置

```python
# 初始化时设置
monitor = AINewsMonitor(
    cache_dir="./data/cache/ai_news",
    cache_ttl=600  # 10 分钟缓存
)
```

---

## 🧪 测试命令

```bash
# 测试新闻获取
cd /home/admin/.openclaw/workspace/stock-agent
./venv311/bin/python3 -c "
from src.ai_news_monitor import AINewsMonitor
monitor = AINewsMonitor()
news = monitor.fetch_all_news(limit_sources=3)
print(f'获取到 {len(news)} 条新闻')
for n in news[:5]:
    print(f'- {n[\"title\"][:50]}')
"

# 测试建议生成
./venv311/bin/python3 -c "
from src.ai_news_monitor import AINewsMonitor
monitor = AINewsMonitor()
news = [{'title': 'OpenAI 发布新模型', 'source': 'Test'}]
advice = monitor.generate_personal_advice(news)
print(advice)
"
```

---

## 📈 效果评估

### 成功指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 新闻源可用率 | >80% | ~60% |
| 每日新闻数量 | >20 条 | 21 条 ✅ |
| 推送准时率 | 100% | 待观察 |
| 建议相关性 | 高 | 待优化 |

### 优化方向

1. **短期（本周）**
   - [ ] 修复 403/404 新闻源
   - [ ] 改进 HTML 解析逻辑
   - [ ] 添加更多中文源

2. **中期（本月）**
   - [ ] 与持仓股票关联分析
   - [ ] 添加新闻情感评分
   - [ ] 生成周度/月度报告

3. **长期（本季度）**
   - [ ] AI 自动摘要生成
   - [ ] 个性化推荐优化
   - [ ] 建立新闻知识库

---

## 📞 故障排查

### 常见问题

**Q: 新闻获取失败**
```bash
# 检查网络连接
curl -I https://www.anthropic.com/news

# 检查 BeautifulSoup 安装
./venv311/bin/pip install beautifulsoup4

# 手动测试
./venv311/bin/python3 src/ai_news_monitor.py --once --no-qq
```

**Q: QQ 推送失败**
```bash
# 检查 openclaw CLI
openclaw --version

# 检查 QQ Bot 配置
cat ~/.openclaw/openclaw.json | grep qqbot
```

**Q: 解析结果为空**
- 检查网站结构是否变化
- 更新解析逻辑
- 使用备用新闻源

---

## 📚 相关文档

- [stock-agent README](../README.md)
- [晚间分析模块](./evening_analysis.py)
- [早盘推荐模块](./morning_recommend.py)
- [持仓监控模块](./monitor.py)

---

**集成完成时间：** 2026-03-24  
**下次推送时间：** 2026-03-25 20:00  
**状态：** ✅ 正常运行
