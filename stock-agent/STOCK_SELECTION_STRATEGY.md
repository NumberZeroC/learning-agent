# 📈 Stock-Agent 选股方案

**版本：** 1.0  
**更新时间：** 2026-03-27

---

## 🎯 选股理念

**核心思想：** 多因子量化选股 + Agent 智能决策

```
基本面筛选 → 技术面确认 → 资金流验证 → 情绪面加分 → 综合评分 → 择优推荐
```

---

## 📊 选股流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Stock-Agent 选股流程                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  第一步：初筛（基本面）                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • PE 0-30（排除高估值）                               │   │
│  │ • PB 0-5（排除高溢价）                                │   │
│  │ • ROE > 10%（盈利能力）                               │   │
│  │ • 营收增长 > 10%（成长性）                            │   │
│  │ • 非 ST、非问题股                                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  第二步：精选（技术面）                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • MACD 金叉（动量确认）                                │   │
│  │ • 均线多头排列（趋势向上）                            │   │
│  │ • 量比 > 1.5（放量）                                  │   │
│  │ • 突破 20 日/60 日高点                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  第三步：验证（资金流）                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • 主力净流入 > 500 万                                  │   │
│  │ • 机构净买入 > 0                                      │   │
│  │ • 融资净买入 > 0                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  第四步：加分（情绪面）                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • 正面新闻 > 负面新闻                                 │   │
│  │ • 板块热度高                                          │   │
│  │ • 龙虎榜上榜（机构买入）                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  第五步：综合评分                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 综合得分 = 基本面 30% + 技术面 35% + 资金流 25% + 情绪 10%  │   │
│  │ 选取 TOP 10 推荐                                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 选股因子详解

### 1. 基本面因子（30 分）

| 因子 | 权重 | 评分标准 | 说明 |
|------|------|----------|------|
| **PE 市盈率** | 8 分 | 0-15 倍：8 分<br>15-30 倍：5 分<br>>30 倍：0 分 | 排除高估值 |
| **PB 市净率** | 5 分 | 0-3 倍：5 分<br>3-5 倍：3 分<br>>5 倍：0 分 | 排除高溢价 |
| **ROE 净资产收益率** | 8 分 | >20%：8 分<br>10-20%：5 分<br><10%：0 分 | 盈利能力 |
| **营收增长率** | 5 分 | >30%：5 分<br>10-30%：3 分<br><10%：0 分 | 成长性 |
| **非 ST/非问题** | 4 分 | 正常：4 分<br>ST/*ST：0 分 | 风险排除 |

**数据来源：** Tushare `stock_basic` + 财务数据

---

### 2. 技术面因子（35 分）

| 因子 | 权重 | 评分标准 | 说明 |
|------|------|----------|------|
| **MACD** | 12 分 | 金叉：12 分<br>延续：6 分<br>死叉：0 分 | 动量确认 |
| **均线排列** | 10 分 | 多头：10 分<br>震荡：5 分<br>空头：0 分 | 趋势判断 |
| **量比** | 8 分 | >2.0：8 分<br>1.5-2.0：5 分<br><1.5：0 分 | 成交量确认 |
| **突破形态** | 5 分 | 突破 60 日：5 分<br>突破 20 日：3 分<br>无突破：0 分 | 关键位置 |

**数据来源：** Tushare `daily` 计算技术指标

---

### 3. 资金流因子（25 分）

| 因子 | 权重 | 评分标准 | 说明 |
|------|------|----------|------|
| **主力净流入** | 12 分 | >1000 万：12 分<br>500-1000 万：8 分<br>0-500 万：3 分<br><0：0 分 | 主力动向 |
| **机构净买入** | 8 分 | >500 万：8 分<br>0-500 万：4 分<br><0：0 分 | 机构态度 |
| **融资净买入** | 5 分 | >0：5 分<br><0：0 分 | 杠杆资金 |

**数据来源：** Tushare `moneyflow` + `margin`

---

### 4. 情绪面因子（10 分）

| 因子 | 权重 | 评分标准 | 说明 |
|------|------|----------|------|
| **新闻情绪** | 5 分 | 正面>负面：5 分<br>中性：3 分<br>负面>正面：0 分 | 舆论导向 |
| **板块热度** | 3 分 | 热门板块：3 分<br>一般：1 分<br>冷门：0 分 | 板块效应 |
| **龙虎榜** | 2 分 | 机构买入：2 分<br>无上榜：0 分 | 资金认可 |

**数据来源：** 新闻监控 + 板块分析 + `top_list`

---

## 🧮 综合评分计算

```python
def calculate_score(stock_data):
    """计算综合得分"""
    
    # 基本面得分（30 分）
    fundamental_score = (
        pe_score(stock_data['pe']) * 0.27 +      # 8 分
        pb_score(stock_data['pb']) * 0.20 +      # 5 分
        roe_score(stock_data['roe']) * 0.27 +    # 8 分
        growth_score(stock_data['revenue_growth']) * 0.17 +  # 5 分
        (0 if 'ST' in stock_data['name'] else 4)  # 4 分
    )
    
    # 技术面得分（35 分）
    technical_score = (
        macd_score(stock_data['macd']) * 0.34 +    # 12 分
        ma_score(stock_data['ma_pattern']) * 0.29 +  # 10 分
        volume_ratio_score(stock_data['volume_ratio']) * 0.23 +  # 8 分
        breakout_score(stock_data['breakout']) * 0.14  # 5 分
    )
    
    # 资金流得分（25 分）
    capital_score = (
        main_force_score(stock_data['main_force_net']) * 0.48 +  # 12 分
        inst_score(stock_data['inst_net']) * 0.32 +  # 8 分
        financing_score(stock_data['financing_net']) * 0.20  # 5 分
    )
    
    # 情绪面得分（10 分）
    sentiment_score = (
        news_score(stock_data['news_sentiment']) * 0.50 +  # 5 分
        sector_score(stock_data['sector_hot']) * 0.30 +  # 3 分
        top_list_score(stock_data['top_list']) * 0.20  # 2 分
    )
    
    # 综合得分
    total_score = (
        fundamental_score * 0.30 +
        technical_score * 0.35 +
        capital_score * 0.25 +
        sentiment_score * 0.10
    )
    
    return total_score
```

---

## 📊 选股策略

### 策略 1：价值成长策略

**适合：** 中长线投资

**选股条件：**
- PE < 25
- ROE > 15%
- 营收增长 > 20%
- 技术面 MACD 金叉
- 资金流主力净流入

**权重调整：**
- 基本面：40%
- 技术面：30%
- 资金流：20%
- 情绪面：10%

---

### 策略 2：动量突破策略

**适合：** 短线交易

**选股条件：**
- 20 日涨幅 > 10%
- 突破 60 日新高
- 量比 > 2.0
- MACD 金叉
- 主力净流入 > 1000 万

**权重调整：**
- 基本面：20%
- 技术面：45%
- 资金流：25%
- 情绪面：10%

---

### 策略 3：资金流驱动策略

**适合：** 跟随主力

**选股条件：**
- 主力净流入 > 2000 万
- 机构净买入 > 1000 万
- 融资净买入 > 0
- 股价上涨 2-5%
- 非高位股

**权重调整：**
- 基本面：25%
- 技术面：25%
- 资金流：40%
- 情绪面：10%

---

### 策略 4：板块轮动策略

**适合：** 热点追踪

**选股条件：**
- 板块涨幅前 5
- 板块资金净流入前 3
- 个股为板块龙头
- 技术面多头排列
- 有新闻催化

**权重调整：**
- 基本面：25%
- 技术面：30%
- 资金流：25%
- 情绪面：20%

---

## 🤖 Agent 选股流程

### 分析 Agent (Analyst)

```python
class AnalystAgent:
    """分析 Agent - 负责选股"""
    
    def screen_stocks(self, strategy='balanced') -> List[Stock]:
        """执行选股流程"""
        
        # 第一步：获取股票池
        stock_pool = self.get_stock_pool()  # 全 A 股
        
        # 第二步：基本面初筛
        filtered = self.fundamental_filter(stock_pool)
        print(f"基本面筛选后：{len(filtered)}只")
        
        # 第三步：技术面精选
        filtered = self.technical_filter(filtered)
        print(f"技术面筛选后：{len(filtered)}只")
        
        # 第四步：资金流验证
        filtered = self.capital_filter(filtered)
        print(f"资金流验证后：{len(filtered)}只")
        
        # 第五步：综合评分
        scored = self.calculate_scores(filtered, strategy)
        
        # 第六步：排序推荐
        recommendations = sorted(scored, key=lambda x: x['score'], reverse=True)[:10]
        
        return recommendations
```

### 交易 Agent (Trader)

```python
class TraderAgent:
    """交易 Agent - 负责执行"""
    
    def execute_recommendations(self, recommendations):
        """执行推荐"""
        
        for stock in recommendations:
            # 检查风控
            if not self.risk_check(stock):
                continue
            
            # 计算仓位
            position = self.calculate_position(stock)
            
            # 执行买入
            self.buy(stock['code'], position)
```

### 风控 Agent (RiskManager)

```python
class RiskManagerAgent:
    """风控 Agent - 负责审核"""
    
    def risk_check(self, stock) -> bool:
        """风控检查"""
        
        # 检查单只股票仓位
        if self.get_position_ratio(stock['code']) > 0.30:
            return False
        
        # 检查板块集中度
        if self.get_sector_ratio(stock['sector']) > 0.50:
            return False
        
        # 检查止损
        if self.check_stop_loss(stock['code']):
            return False
        
        return True
```

---

## 📝 选股报告示例

```
========================================
📈 Stock-Agent 选股报告
日期：2026-03-27
策略：平衡策略
========================================

推荐股票 TOP10：

1. 贵州茅台 (600519) - 综合得分：92.5
   基本面：28/30  |  技术面：32/35  |  资金流：23/25  |  情绪：9/10
   PE: 28  |  ROE: 28%  |  MACD: 金叉  |  主力净流入：+1500 万
   推荐理由：白酒龙头，业绩稳定，技术面突破

2. 宁德时代 (300750) - 综合得分：89.3
   基本面：26/30  |  技术面：33/35  |  资金流：22/25  |  情绪：8/10
   PE: 25  |  ROE: 22%  |  MACD: 金叉  |  主力净流入：+2000 万
   推荐理由：新能源龙头，高成长，资金追捧

3. 五粮液 (000858) - 综合得分：87.1
   ...

========================================
```

---

## 🔧 配置选股参数

### config.yaml

```yaml
# 选股配置
stock_selection:
  # 默认策略
  default_strategy: 'balanced'  # balanced | value | momentum | capital | sector
  
  # 选股范围
  stock_pool:
    exclude_st: true          # 排除 ST
    exclude_kcb: false        # 排除科创板
    min_market_cap: 50e8      # 最小市值 50 亿
    max_market_cap: 500e8     # 最大市值 500 亿
  
  # 基本面阈值
  fundamental:
    pe_max: 30
    pb_max: 5
    roe_min: 10
    revenue_growth_min: 10
  
  # 技术面阈值
  technical:
    macd_golden_cross: true
    ma_bull_pattern: true
    volume_ratio_min: 1.5
    breakout_days: 20
  
  # 资金流阈值
  capital:
    main_force_net_min: 5000000  # 500 万
    inst_net_min: 0
    financing_net_min: 0
  
  # 推荐数量
  recommendations:
    max_count: 10
    min_score: 60  # 最低 60 分
```

---

## 📊 选股绩效评估

### 评估指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| **胜率** | 盈利交易比例 | > 55% |
| **盈亏比** | 平均盈利/平均亏损 | > 1.5 |
| **年化收益** | 年化收益率 | > 20% |
| **最大回撤** | 最大亏损幅度 | < 15% |
| **夏普比率** | 风险调整后收益 | > 1.0 |
| **信息比率** | 超额收益/跟踪误差 | > 0.5 |

### 回测验证

```python
from stock_agent import Backtester

# 创建回测器
backtester = Backtester(
    strategy='balanced',
    start_date='2025-01-01',
    end_date='2026-03-27',
    initial_capital=1000000
)

# 运行回测
results = backtester.run()

# 查看结果
print(f"总收益：{results.total_return:.2%}")
print(f"年化收益：{results.annual_return:.2%}")
print(f"最大回撤：{results.max_drawdown:.2%}")
print(f"夏普比率：{results.sharpe_ratio:.2f}")
print(f"胜率：{results.win_rate:.2%}")
```

---

## ⚠️ 风险提示

1. **历史不代表未来** - 回测成绩不代表未来表现
2. **市场风险** - 系统性风险无法避免
3. **流动性风险** - 小盘股可能流动性不足
4. **数据延迟** - 实时数据可能有延迟
5. **模型风险** - 量化模型可能失效

---

## 📚 总结

**选股方案核心：**

1. **多因子选股** - 基本面 + 技术面 + 资金流 + 情绪面
2. **Agent 决策** - 分析 + 交易 + 风控三方协作
3. **动态调整** - 根据市场调整权重
4. **风险控制** - 严格的风控机制
5. **持续优化** - 回测验证 + 参数调优

**选股目标：** 在控制风险的前提下，获取稳定超额收益

---

*选股方案版本：1.0*  
*最后更新：2026-03-27*
