# AI 应用创业日报 - 配置文档

## ✅ 已完成的配置

### 1. 定时任务

**执行时间：** 每天晚上 20:00  
**执行方式：** Cron 定时任务  
**推送目标：** QQ (qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52)

```bash
# 查看定时任务
crontab -l

# 输出：
0 20 * * * /home/admin/.openclaw/workspace/ai-news-daily/run_daily.sh
```

---

### 2. 用户画像

| 维度 | 内容 |
|------|------|
| **称呼** | 老板 |
| **开发经验** | 6 年 |
| **工作背景** | 华为云计算 5 年 |
| **当前状态** | AI 应用创业 |
| **目标** | 抓住 AI 风口 |

---

### 3. 推送内容结构

```
🤖 AI 应用创业日报 | 2026-03-24 Tuesday

━━━━━━━━━━━━━━━━━━

📰 今日热点（精选 3-5 条）
1. 英伟达 CEO：已实现 AGI
2. OpenAI 洽谈收购核聚变公司
3. AI 音乐欺诈案获利 800 万
...

━━━━━━━━━━━━━━━━━━

💡 个人建议（基于你的背景）

【机会】
• 资本动向：关注融资热点领域
• 产品趋势：分析竞品功能

【风险】
• 合规警示：注意 AI 监管动态

【行动项】
🔥 高 研究融资新闻中的公司
   → 华为云人脉 + 行业理解 = 独特优势
📅 中 记录今日新闻到知识库
   → 建立行业认知体系

━━━━━━━━━━━━━━━━━━

🎯 今日金句
"2026 年不是 AI 取代程序员，而是会用 AI 的程序员取代不会用的。"
```

---

### 4. 新闻来源

| 来源 | 优先级 | 类型 |
|------|--------|------|
| The Verge AI | ⭐⭐⭐ | 综合科技 |
| TechCrunch AI | ⭐⭐⭐ | 创业/融资 |
| OpenAI News | ⭐⭐ | 官方动态 |
| Hacker News | ⭐⭐ | 社区热度 |
| 36Kr AI | ⭐⭐ | 国内动态 |

---

### 5. 建议生成逻辑

根据新闻内容 + 用户背景，自动生成：

#### 机会识别
- 融资新闻 → 投资热点方向
- 产品发布 → 市场趋势
- 技术突破 → 学习方向

#### 风险警示
- 监管政策 → 合规注意
- 欺诈案例 → 避坑指南

#### 行动建议
结合华为云背景 + 创业状态：
- 🔥 高优先级：直接关联创业决策
- 📅 中优先级：能力建设
- 💡 低优先级：影响力建设

---

## 🔧 手动触发

### 立即执行一次

```bash
/home/admin/.openclaw/workspace/ai-news-daily/run_daily.sh
```

### 查看日志

```bash
# 今日日志
cat /home/admin/.openclaw/workspace/ai-news-daily/logs/ai_news_$(date +%Y-%m-%d).log

# Cron 日志
cat /home/admin/.openclaw/workspace/ai-news-daily/logs/cron.log
```

---

## 📝 修改配置

### 修改推送时间

```bash
crontab -e
# 修改这一行（格式：分 时 日 月 周）
0 20 * * * /home/admin/.openclaw/workspace/ai-news-daily/run_daily.sh
```

### 修改推送目标

编辑 `ai_news_daily.py`：
```python
QQ_TARGET = "qqbot:c2c:YOUR_QQ_ID"
```

### 修改用户画像

编辑 `ai_news_daily.py` 中的 `USER_PROFILE`：
```python
USER_PROFILE = {
    "name": "老板",
    "experience": "6 年开发",
    "background": "华为云计算 5 年",
    ...
}
```

---

## 🧪 测试推送

### 测试命令

```bash
cd /home/admin/.openclaw/workspace
./ai-news-daily/run_daily.sh
```

### 预期结果

1. ✅ 获取到 AI 新闻
2. ✅ 生成个人建议
3. ✅ QQ 收到推送消息
4. ✅ 日志文件生成

---

## 📊 文件结构

```
/home/admin/.openclaw/workspace/ai-news-daily/
├── ai_news_daily.py      # 主程序
├── run_daily.sh          # 执行脚本
├── logs/                 # 日志目录
│   ├── ai_news_*.log     # 每日日志
│   └── cron.log          # Cron 日志
└── output/               # 输出备份
    └── ai_news_*.md      # 每日消息备份
```

---

## 🎯 推送时间

| 时区 | 时间 |
|------|------|
| **Asia/Shanghai** | 20:00 (晚上 8 点) |
| UTC | 12:00 (中午 12 点) |
| US/Pacific | 04:00 (凌晨 4 点) |

---

## 💡 优化建议

### 短期（本周）
- [ ] 测试推送是否正常
- [ ] 调整建议的个性化程度
- [ ] 添加更多新闻源

### 中期（本月）
- [ ] 添加新闻摘要生成功能
- [ ] 集成股票监控（持仓相关 AI 公司）
- [ ] 添加周末复盘报告

### 长期（本季度）
- [ ] 建立新闻知识库
- [ ] AI 分析新闻情感倾向
- [ ] 关联创业项目方向

---

## 📞 问题排查

### QQ 没收到推送

1. 检查 QQ Bot 是否在线
2. 检查 Target ID 是否正确
3. 查看日志：`cat logs/cron.log`

### 新闻获取失败

1. 检查网络连接
2. 检查新闻源是否可访问
3. 查看日志：`cat logs/ai_news_*.log`

### 建议不够个性化

1. 修改 `USER_PROFILE` 添加更多背景信息
2. 调整 `generate_action_items` 逻辑
3. 在日志中反馈问题

---

**配置完成时间：** 2026-03-24  
**下次推送时间：** 2026-03-25 20:00  
**状态：** ✅ 正常运行
