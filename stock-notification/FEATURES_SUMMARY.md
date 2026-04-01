# 📊 Stock-Notification 功能总结

**版本：** 1.0  
**更新时间：** 2026-03-27

> 💡 原名：Stock-Notification，现已更名为 Stock-Notification

---

## 🎯 核心功能概览

Stock-Notification 是一个完整的 A 股智能分析系统，包含以下功能模块：

```
┌─────────────────────────────────────────────────────────────┐
│                    Stock-Notification 系统架构                      │
├─────────────────────────────────────────────────────────────┤
│  📈 盘后分析    │  📱 盘前推荐    │  🔍 技术分析    │  📊 Web 服务 │
│  - 晚间总结    │  - 早盘推荐    │  - 选股策略    │  - API 接口  │
│  - 板块分析    │  - 热点板块    │  - 定时推送    │  - 数据展示  │
│  - 资金流      │  - 龙头股      │  - QQ 消息     │  - 报告查询  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 功能清单

### 1. 🌙 晚间综合分析 (`evening_analysis.py`)

**功能：** 每日盘后自动生成综合分析报告

**分析内容：**
| 模块 | 说明 | 数据源 |
|------|------|--------|
| 📊 大盘走势 | 上证、深证、创业板指数表现 | Tushare/AKShare |
| 💰 板块资金流 | 板块主力资金流入/流出 | Tushare moneyflow |
| 📈 板块涨幅 | 板块平均涨幅排序（新） | Tushare daily |
| 📰 新闻情绪 | 板块相关新闻情感分析 | 同花顺/东方财富 |
| 🤖 AI 行业动态 | AI 领域新闻和趋势分析 | 多源聚合 |

**输出：**
- Markdown 报告：`data/reports/evening_summary_YYYY-MM-DD.md`
- JSON 数据：`data/reports/evening_summary_YYYY-MM-DD.json`

**执行时间：** 每个交易日 20:00

---

### 2. 📈 早盘推荐 (`morning_recommend.py`)

**功能：** 基于晚间分析和早间数据，推荐热点板块和龙头股

**推荐逻辑：**
| 指标 | 权重 | 说明 |
|------|------|------|
| 板块涨幅 | 40% | 前一日板块平均涨幅 |
| 资金流 | 40% | 主力净流入 |
| 新闻情绪 | 20% | 正面新闻比例 |

**龙头股筛选：**
| 指标 | 权重 | 说明 |
|------|------|------|
| 资金流 | 60 分 | 主力净流入 + 机构净买 + 融资净买 |
| 涨幅 | 25 分 | 近期涨幅 |
| 竞价 | 15 分 | 早盘竞价表现 |

**输出：**
- 推荐 5 个热点板块
- 每个板块推荐 3 只龙头股
- QQ 消息推送

**执行时间：** 每个交易日 9:00

---

### 3. 🔍 技术指标选股 (`technical_analysis.py`) 【新增】

**功能：** 扫描全市场，寻找即将启动拉升的股票

**筛选条件：**
| 特征 | 权重 | 说明 |
|------|------|------|
| 日线稳定 | 25 分 | 均线多头排列（5>10>20>30>60） |
| 逐渐放量 | 25 分 | 成交量温和放大，量比>1.5 |
| 拉升试盘 | 10 分 | 小幅上涨（5 日 0-15%） |
| 即将启动 | 35 分 | MACD 金叉 + 突破关键位置 |
| RSI 适中 | 5 分 | RSI 在 40-70 之间 |

**定时执行：**
- 交易日 9:30-11:30, 13:00-15:00
- 每 30 分钟执行一次
- 自动推送 QQ 消息

**输出：**
- 推荐 10 支股票
- Markdown 报告 + JSON 数据
- QQ 消息推送

**相关文件：**
- `technical_analysis.py` - 核心技术分析
- `scheduled_technical_pick.py` - 定时执行脚本
- `CRON_SETUP.md` - 定时任务配置

---

### 4. 📊 股票监控 (`monitor.py` + `stock_monitor.py`)

**功能：** 实时监控持仓股票和关注股票

**监控内容：**
- 股价异动（涨跌幅超过阈值）
- 成交量异常放大
- 主力资金大幅流入/流出
- 龙虎榜上榜
- 重要新闻发布

**通知方式：**
- QQ 消息实时推送
- 支持自定义监控列表

---

### 5. 📰 AI 新闻监控 (`ai_news_monitor.py`)

**功能：** 自动抓取和分析 AI 行业新闻

**数据源：**
- 36Kr
- 腾讯新闻
- WallStreetCN
- V2EX
- 微博
- GitHub Trending
- Product Hunt
- Hacker News

**分析内容：**
- 情感分析（正面/中性/负面）
- 热点话题识别
- 风险信号检测
- 对持仓的启示

**输出：**
- 集成到晚间分析报告
- 独立的 AI 新闻 JSON 数据

---

### 6. 🌐 Web 服务 (`stock-agent-web/`)

**功能：** 提供 RESTful API 和数据展示

**API 接口：**
| 接口 | 说明 |
|------|------|
| `GET /api/v1/data/overview` | 首页概览数据 |
| `GET /api/v1/data/market` | 市场数据 |
| `GET /api/v1/data/capital/sectors` | 板块资金流 |
| `GET /api/v1/data/ai-news` | AI 新闻数据 |
| `GET /api/v1/data/aggregated` | 聚合数据 |
| `GET /api/v1/data/latest` | 最新数据 |
| `GET /api/v1/sectors/rank` | 板块排名（按涨幅） |

**前端功能：**
- 大盘走势展示
- 板块资金流排行
- 热点板块推荐
- AI 新闻聚合
- 历史报告查询

**部署：**
- Flask 应用
- 端口：5000
- 日志：`stock-agent-web/logs/`

---

### 7. 📱 QQ 消息推送 (`notify_report.py` + `send_qq_notify.py`)

**功能：** 自动推送分析报告到 QQ

**推送内容：**
| 报告类型 | 推送时间 | 内容 |
|----------|----------|------|
| 🌙 晚间总结 | 20:00 | 大盘表现 + 板块涨幅 TOP5 + 资金流 |
| 📈 早盘推荐 | 9:00 | 热点板块 + 龙头股推荐 |
| 🔍 技术选股 | 每 30 分钟 | 推荐股票 TOP10 |
| ⚠️ 监控预警 | 实时 | 股价异动 + 资金流异常 |

**配置：**
- 目标用户：`qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52`
- 使用 OpenClaw message 工具发送

---

### 8. 📅 定时任务系统

**Cron 配置：**
```bash
# 晚间总结（每个交易日 20:00）
0 20 * * 1-5 evening_analysis.py

# 早盘推荐（每个交易日 9:00）
0 9 * * 1-5 morning_recommend.py

# 技术选股（交易日每 30 分钟）
*/30 9-11 * * 1-5 scheduled_technical_pick.py
*/30 13-14 * * 1-5 scheduled_technical_pick.py

# 通知检查（每 30-60 分钟）
*/30 * * * 1-5 check_notifications.py
```

---

## 📁 目录结构

```
stock-notification/
├── 📄 核心脚本
│   ├── evening_analysis.py      # 晚间综合分析
│   ├── morning_recommend.py     # 早盘推荐
│   ├── technical_analysis.py    # 技术指标选股（新）
│   ├── scheduled_technical_pick.py  # 定时执行（新）
│   ├── monitor.py               # 股票监控
│   ├── notify_report.py         # 报告推送
│   └── send_qq_notify.py        # QQ 消息发送
│
├── 📦 数据源模块 (src/)
│   ├── tushare_pro_source.py    # Tushare Pro（主数据源）
│   ├── akshare_source.py        # AKShare（备用）
│   ├── capital_flow.py          # 资金流分析（已修复）
│   ├── news_monitor.py          # 新闻监控
│   ├── ai_news_monitor.py       # AI 新闻监控
│   └── ...
│
├── 🛠️ 服务模块 (services/)
│   ├── capital_fetcher.py       # 资金流服务
│   ├── market_fetcher.py        # 行情服务
│   ├── ai_news_fetcher.py       # AI 新闻服务
│   └── data_aggregator.py       # 数据聚合
│
├── 📊 Web 服务 (stock-agent-web/)
│   ├── app.py                   # Flask 应用
│   ├── api/v1/                  # API 路由
│   ├── services/                # 数据服务
│   └── logs/                    # 日志目录
│
├── 📂 数据目录 (data/)
│   ├── reports/                 # 分析报告
│   ├── capital/                 # 资金流数据
│   ├── market/                  # 市场数据
│   ├── ai_news/                 # AI 新闻数据
│   └── technical/               # 技术分析数据（新）
│
└── 📖 文档
    ├── README.md
    ├── CRON_SETUP.md            # 定时任务配置（新）
    ├── TECHNICAL_ANALYSIS_README.md  # 技术分析说明（新）
    ├── SECTOR_CHANGE_FIX.md     # 板块涨幅修复（新）
    └── RECOMMENDATION_UPDATE.md # 推荐逻辑优化（新）
```

---

## 📊 数据流程图

```
交易日 15:00 收盘
       ↓
┌─────────────────┐
│ 获取收盘数据    │
│ - 日线行情      │
│ - 资金流        │
│ - 龙虎榜        │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 晚间分析        │ ←─── 📰 新闻监控
│ - 大盘走势      │      - 板块新闻
│ - 板块涨幅      │      - 情感分析
│ - 资金流        │
│ - AI 新闻       │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 生成报告        │
│ - Markdown      │
│ - JSON          │
└────────┬────────┘
         ↓
┌─────────────────┐
│ QQ 推送          │
│ - 晚间总结      │
└────────┬────────┘
         ↓
    交易日 20:00

       ↓

交易日 9:00
       ↓
┌─────────────────┐
│ 早盘推荐        │
│ - 读取晚间报告  │
│ - 获取早间新闻  │
│ - 选择热点板块  │
│ - 筛选龙头股    │
└────────┬────────┘
         ↓
┌─────────────────┐
│ QQ 推送          │
│ - 热点板块      │
│ - 龙头股推荐    │
└─────────────────┘

       ↓

交易日 9:30-15:00
       ↓
┌─────────────────┐
│ 技术选股        │
│ - 每 30 分钟扫描  │
│ - MACD 金叉      │
│ - 均线多头      │
│ - 成交量放大    │
│ - 突破形态      │
└────────┬────────┘
         ↓
┌─────────────────┐
│ QQ 推送          │
│ - 推荐 TOP10    │
└─────────────────┘
```

---

## 🔧 配置文件

### 环境变量
```bash
# Tushare Token（必需）
TUSHARE_TOKEN=your_token_here

# 数据目录
STOCK_AGENT_DATA_DIR=/home/admin/.openclaw/workspace/data/stock-agent

# QQ 推送目标
QQ_TARGET=qqbot:c2c:6BD7A1BCF3F92369D0580647287C0D52
```

### config.yaml
```yaml
# 板块列表
sectors:
  - 半导体
  - 人工智能
  - 新能源
  - 医药生物
  - ...

# 数据源配置
tushare:
  token: ${TUSHARE_TOKEN}
  
akshare:
  cache_dir: ./data/cache
  cache_ttl: 300
  max_retries: 3

# 新闻关键词
news_keywords:
  半导体：['芯片', '集成电路', '半导体']
  人工智能：['AI', '大模型', 'GPT']
  ...
```

---

## 📈 输出示例

### 晚间总结报告
```markdown
# 🌙 晚间市场总结报告

## 📊 大盘走势
| 指数 | 收盘价 | 涨跌幅 |
|------|--------|--------|
| 上证指数 | 3050.25 | +1.25% |
| 深证成指 | 9850.60 | +1.80% |

## 🏆 板块涨幅 TOP10
| 排名 | 板块 | 平均涨幅 | 主力流入 | 净流入 |
|------|------|----------|----------|--------|
| 1 | 半导体 | 🔴 +3.2% | 1500 万 | +1200 万 |
| 2 | 人工智能 | 🔴 +2.8% | 1000 万 | +800 万 |
```

### 早盘推荐
```
📈 早盘推荐报告

🔥 今日热点板块

1. 半导体 (得分：85.5)
   - 中芯国际 (688981) - 主力净流入 +1200 万
   - 北方华创 (002371) - 主力净流入 +750 万
   - 韦尔股份 (603501) - 主力净流入 +600 万

2. 人工智能 (得分：78.3)
   ...
```

### 技术选股推送
```
📊 技术选股推送 (03-27 09:30)

🏆 推荐 TOP10

1. **中芯国际** (688981)
   价格：¥52.30 (+2.5%) | 得分：85 分
   信号：MACD 金叉、逐渐放量

2. **北方华创** (002371)
   价格：¥285.60 (+1.8%) | 得分：82 分
   信号：均线多头、突破 20 日高点

...

⚠️ 风险提示：技术分析仅供参考
```

---

## 🚀 快速开始

### 1. 安装依赖
```bash
cd /home/admin/.openclaw/workspace/stock-agent
source venv311/bin/activate
pip install akshare pandas numpy pyyaml
```

### 2. 配置 Tushare Token
```bash
export TUSHARE_TOKEN=your_token_here
```

### 3. 手动执行
```bash
# 晚间分析
python3 evening_analysis.py

# 早盘推荐
python3 morning_recommend.py

# 技术选股
python3 technical_analysis.py --limit 10
```

### 4. 设置定时任务
```bash
crontab -e
# 添加 CRON_SETUP.md 中的配置
```

---

## 📝 更新日志

### 2026-03-27
- ✅ 新增技术指标选股功能
- ✅ 新增定时执行脚本（每 30 分钟）
- ✅ 修复板块涨幅数据问题（change_pct 字段）
- ✅ 优化推荐逻辑（按涨幅排序）
- ✅ 增强龙头股筛选（资金流权重 60%）

### 之前版本
- ✅ 晚间综合分析报告
- ✅ 早盘推荐系统
- ✅ AI 新闻监控
- ✅ Web API 服务
- ✅ QQ 消息推送

---

*Stock-Notification - 您的智能股票分析助手*
