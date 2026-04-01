# AI 新闻情感分析 - 集成文档

## 🎉 集成完成

**时间：** 2026-03-24  
**状态：** ✅ 已上线

---

## 📦 集成内容

### 1. AI 新闻监控模块

**文件：** `stock-agent/src/ai_news_monitor.py`

**新增功能：**
- ✅ `analyze_news_sentiment()` - 情感分析方法
- ✅ `_extract_hot_topics()` - 热点话题提取
- ✅ 情感关键词库（正面/负面）
- ✅ 风险信号检测

### 2. 晚间总结报告集成

**文件：** `stock-agent/evening_analysis.py`

**修改内容：**
- ✅ 导入 AI 新闻监控模块
- ✅ 初始化 `ai_news_monitor`
- ✅ 新增 `get_ai_news_and_sentiment()` 方法
- ✅ 更新 `generate_summary_report()` 添加 AI 板块
- ✅ 更新 `run_analysis()` 调用 AI 新闻获取

---

## 📊 情感分析功能

### 分析方法

```python
# 情感关键词
positive_keywords = [
    "突破", "发布", "上线", "成功", "增长", "创新", "领先",
    "fund", "invest", "launch", "release", "breakthrough"
]

negative_keywords = [
    "风险", "欺诈", "监管", "处罚", "下跌", "失败", "裁员",
    "risk", "fraud", "regulation", "penalty", "layoff"
]

# 情感得分计算
overall_score = 50 + (positive - negative) / total * 25
# 得分范围：0-100
# >60: positive (🟢)
# 40-60: neutral (🟡)
# <40: negative (🔴)
```

### 输出格式

```json
{
  "overall_score": 51.2,
  "overall_level": "neutral",
  "overall_emoji": "🟡",
  "positive_ratio": 4.8,
  "negative_ratio": 0.0,
  "total_news": 21,
  "hot_topics": ["Claude (6)", "Anthropic (3)", "模型 (3)"],
  "risk_signals": [],
  "categories": {
    "product": {"score": 55, "level": "neutral"},
    "tech": {"score": 60, "level": "positive"}
  }
}
```

---

## 📄 晚间报告 AI 板块

### 报告结构

```markdown
## 🤖 AI 行业动态

### 情感分析
| 指标 | 数值 |
|------|------|
| 整体情感 | 🟡 neutral |
| 情感得分 | 51.2/100 |
| 新闻总数 | 21 条 |
| 正面比例 | 4.8% |
| 负面比例 | 0.0% |

### 热点话题
- 🔥 Claude (6)
- 🔥 Anthropic (3)
- 🔥 模型 (3)

### 风险信号
- ✅ 无明显风险信号

### AI 新闻精选
1. **标题...** (来源)
2. **标题...** (来源)

### 💡 对持仓的启示
1. **技术趋势**: 关注 AI 新技术对产品的影响
2. **资本动向**: 融资热点可能是下一个风口
3. **风险提示**: 注意监管政策变化
4. **创业机会**: 结合华为云背景，寻找差异化机会
```

---

## 🧪 测试结果

### 2026-03-24 测试

```
🤖 获取 AI 行业新闻...
[The Verge AI] 📡 获取新闻中...
[TechCrunch AI] 📡 获取新闻中...
[Anthropic News] ✅ 获取 10 条
[机器之心] ✅ 获取 5 条
[量子位] ✅ 获取 6 条
   ✅ 获取 21 条 AI 新闻
   📊 情感得分：51.2 (🟡 neutral)

📝 生成晚间总结报告...
   报告已保存：data/reports/evening_summary_2026-03-24.md
🤖 AI 新闻：21 条，情感得分：51.2
```

### 情感分析详情

| 指标 | 数值 | 说明 |
|------|------|------|
| 整体得分 | 51.2/100 | 中性偏正 |
| 正面新闻 | 4.8% | 较少 |
| 负面新闻 | 0.0% | 无 |
| 热点话题 | Claude, Anthropic | 产品发布相关 |
| 风险信号 | 无 | 安全 |

---

## 🔧 使用方法

### 手动执行

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 运行晚间分析（包含 AI 新闻）
./venv311/bin/python3 evening_analysis.py

# 仅获取 AI 新闻
./venv311/bin/python3 -c "
from src.ai_news_monitor import AINewsMonitor
monitor = AINewsMonitor()
news = monitor.fetch_all_news(limit_sources=5)
sentiment = monitor.analyze_news_sentiment(news)
print(f'情感得分：{sentiment[\"overall_score\"]}')
"
```

### 定时任务

```bash
# 查看定时任务
crontab -l

# 输出：
0 20 * * * /home/admin/.openclaw/workspace/stock-agent/scripts/ai_news_daily.sh
```

---

## 📁 文件位置

```
stock-agent/
├── src/
│   ├── ai_news_monitor.py          # AI 新闻监控（含情感分析）
│   └── ...
├── evening_analysis.py              # 晚间总结（已集成 AI 新闻）
├── scripts/
│   └── ai_news_daily.sh            # 定时脚本
├── data/reports/
│   ├── evening_summary_*.md        # 晚间报告（含 AI 板块）
│   └── ai_news/
│       ├── ai_news_*.md            # AI 新闻报告
│       └── ai_news_*.json          # AI 新闻数据
└── docs/
    └── AI_NEWS_INTEGRATION.md      # 集成文档
```

---

## ⚠️ 已知问题

### 1. 新闻解析问题

**现象：** 部分新闻源显示导航文本（如"Skip to main content"）

**原因：** HTML 解析逻辑需要优化

**解决方案：**
```python
# 改进解析逻辑，过滤导航文本
if any(kw in title for kw in ["Skip to", "Copyright", "All rights"]):
    continue  # 跳过无效标题
```

### 2. 新闻源访问问题

| 新闻源 | 问题 | 状态 |
|--------|------|------|
| OpenAI News | 403 Forbidden | ⚠️ 需修复 |
| Google AI Blog | SSL 错误 | ⚠️ 需修复 |
| 36Kr AI | 404 Not Found | ⚠️ 需修复 |

**临时方案：** 使用可用新闻源（Anthropic、机器之心、量子位）

---

## 🚀 优化计划

### 短期（本周）
- [ ] 修复新闻解析逻辑
- [ ] 更新失效新闻源 URL
- [ ] 添加 RSS 源支持

### 中期（本月）
- [ ] 与持仓股票关联分析
- [ ] 添加情感趋势图
- [ ] 生成周度/月度报告

### 长期（本季度）
- [ ] AI 自动摘要生成
- [ ] 个性化推荐优化
- [ ] 建立新闻知识库

---

## 📞 故障排查

### AI 新闻未显示在报告中

```bash
# 检查模块加载
cd stock-agent
./venv311/bin/python3 -c "from ai_news_monitor import AINewsMonitor; print('OK')"

# 检查晚间分析日志
cat logs/evening_*.log | grep "AI 新闻"
```

### 情感得分异常

```python
# 手动测试情感分析
from src.ai_news_monitor import AINewsMonitor
monitor = AINewsMonitor()
news = [{'title': 'OpenAI 发布新模型', 'source': 'Test'}]
sentiment = monitor.analyze_news_sentiment(news)
print(sentiment)
```

---

## 📚 相关文档

- [AI 新闻监控集成](./AI_NEWS_INTEGRATION.md)
- [晚间分析报告](../data/reports/evening_summary_*.md)
- [stock-agent README](../README.md)

---

**集成完成时间：** 2026-03-24 22:18  
**首次运行：** ✅ 成功  
**下次更新：** 2026-03-25 盘后
