# 📈 Stock-Agent - 智能量化模拟交易系统

**版本：** 1.0  
**创建时间：** 2026-03-27  
**架构灵感：** LangGraph + CrewAI 多 Agent 协作

---

## 🎯 项目定位

**stock-agent** 是一个基于多 Agent 协作的**模拟量化交易系统**，核心功能：

1. **模拟炒股** - 虚拟资金实盘演练
2. **智能选股** - 多因子量化筛选
3. **自动交易** - 策略驱动买卖
4. **风险控制** - 实时仓位管理
5. **回测分析** - 历史数据验证

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Stock-Agent 系统架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  分析 Agent  │  │  交易 Agent  │  │  风控 Agent  │      │
│  │  Analyst    │  │  Trader      │  │  RiskMgr     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────▼────────┐                        │
│                   │   状态管理器    │                        │
│                   │  State Manager  │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐              │
│         │                  │                  │              │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │  数据层      │  │  策略层      │  │  账户层      │      │
│  │  Data Layer  │  │  Strategy    │  │  Account     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent 角色设计

### 1. 分析 Agent (Analyst)

**职责：** 市场分析、股票筛选、信号生成

```python
class AnalystAgent:
    """分析 Agent - 负责市场研究和选股"""
    
    def __init__(self):
        self.skills = [
            'technical_analysis',  # 技术分析
            'fundamental_analysis',  # 基本面分析
            'sentiment_analysis',  # 情绪分析
            'sector_analysis'  # 板块分析
        ]
    
    def analyze_market(self) -> MarketReport:
        """生成市场分析报告"""
        pass
    
    def screen_stocks(self, criteria) -> List[Stock]:
        """根据条件筛选股票"""
        pass
    
    def generate_signals(self) -> List[Signal]:
        """生成交易信号"""
        pass
```

**工作流程：**
1. 获取市场数据（行情、资金流、新闻）
2. 执行技术分析（MACD、KDJ、RSI、均线）
3. 执行基本面分析（PE、PB、ROE、营收）
4. 生成股票评分和推荐列表

---

### 2. 交易 Agent (Trader)

**职责：** 执行交易、仓位管理、订单优化

```python
class TraderAgent:
    """交易 Agent - 负责执行买卖操作"""
    
    def __init__(self, account):
        self.account = account
        self.strategies = [
            'momentum',  # 动量策略
            'mean_reversion',  # 均值回归
            'breakout',  # 突破策略
            'grid_trading'  # 网格交易
        ]
    
    def execute_trade(self, signal) -> Order:
        """执行交易信号"""
        pass
    
    def optimize_position(self, stock) -> float:
        """优化仓位大小"""
        pass
    
    def manage_orders(self) -> None:
        """管理挂单和止损"""
        pass
```

**工作流程：**
1. 接收分析 Agent 的信号
2. 检查风控限制
3. 计算最优仓位
4. 生成订单（买入/卖出）
5. 执行模拟交易

---

### 3. 风控 Agent (RiskManager)

**职责：** 风险监控、仓位限制、止损管理

```python
class RiskManagerAgent:
    """风控 Agent - 负责风险管控"""
    
    def __init__(self, limits):
        self.limits = {
            'max_position': 0.3,  # 单只股票最大仓位 30%
            'max_sector': 0.5,  # 单板块最大仓位 50%
            'max_drawdown': 0.1,  # 最大回撤 10%
            'stop_loss': 0.08,  # 止损线 8%
            'take_profit': 0.20  # 止盈线 20%
        }
    
    def check_trade(self, order) -> bool:
        """检查交易是否合规"""
        pass
    
    def monitor_portfolio(self) -> RiskReport:
        """监控组合风险"""
        pass
    
    def trigger_stop_loss(self, position) -> bool:
        """触发止损检查"""
        pass
```

**工作流程：**
1. 实时监控持仓风险
2. 检查每笔交易的合规性
3. 触发止损/止盈
4. 生成风险报告

---

## 📊 状态管理 (State Manager)

**核心设计：** 基于 LangGraph 的状态机

```python
class State(TypedDict):
    """系统状态定义"""
    
    # 账户状态
    cash: float  # 可用现金
    positions: Dict[str, Position]  # 持仓
    portfolio_value: float  # 组合总市值
    
    # 市场状态
    market_data: Dict[str, Any]  # 市场数据
    signals: List[Signal]  # 交易信号
    
    # 交易历史
    orders: List[Order]  # 订单记录
    trades: List[Trade]  # 成交记录
    
    # 性能指标
    daily_return: float  # 日收益
    total_return: float  # 总收益
    max_drawdown: float  # 最大回撤
    sharpe_ratio: float  # 夏普比率
    
    # 系统状态
    current_step: str  # 当前步骤
    messages: List[str]  # Agent 消息
```

**状态流转：**

```
初始化 → 数据获取 → 分析 → 信号生成 → 风控检查 → 交易执行 → 更新状态 → 循环
```

---

## 📁 项目结构

```
stock-agent/
├── 📄 核心模块
│   ├── main.py                    # 主程序入口
│   ├── state_manager.py           # 状态管理
│   ├── account.py                 # 账户管理
│   └── config.py                  # 配置管理
│
├── 🤖 Agent 模块 (agents/)
│   ├── __init__.py
│   ├── base_agent.py              # Agent 基类
│   ├── analyst_agent.py           # 分析 Agent
│   ├── trader_agent.py            # 交易 Agent
│   └── risk_manager_agent.py      # 风控 Agent
│
├── 📊 数据模块 (data/)
│   ├── __init__.py
│   ├── data_fetcher.py            # 数据获取
│   ├── data_processor.py          # 数据处理
│   └── cache_manager.py           # 缓存管理
│
├── 📈 策略模块 (strategies/)
│   ├── __init__.py
│   ├── base_strategy.py           # 策略基类
│   ├── momentum.py                # 动量策略
│   ├── mean_reversion.py          # 均值回归
│   ├── breakout.py                # 突破策略
│   └── stock_screener.py          # 选股器
│
├── 💰 交易模块 (trading/)
│   ├── __init__.py
│   ├── order_manager.py           # 订单管理
│   ├── position_manager.py        # 仓位管理
│   ├── execution_engine.py        # 执行引擎
│   └── simulator.py               # 模拟交易引擎
│
├── ⚠️ 风控模块 (risk/)
│   ├── __init__.py
│   ├── risk_limits.py             # 风控限制
│   ├── position_limits.py         # 仓位限制
│   └── stop_loss.py               # 止损管理
│
├── 📉 分析模块 (analysis/)
│   ├── __init__.py
│   ├── technical.py               # 技术分析
│   ├── fundamental.py             # 基本面分析
│   └── performance.py             # 性能分析
│
├── 📝 工具模块 (utils/)
│   ├── __init__.py
│   ├── logger.py                  # 日志
│   ├── helpers.py                 # 辅助函数
│   └── indicators.py              # 技术指标
│
├── 📂 数据目录 (data/)
│   ├── cache/                     # 缓存数据
│   ├── historical/                # 历史数据
│   └── reports/                   # 报告输出
│
├── 📖 文档
│   ├── README.md
│   ├── ARCHITECTURE.md            # 架构说明
│   ├── STRATEGIES.md              # 策略说明
│   └── API.md                     # API 文档
│
└── ⚙️ 配置
    ├── config.yaml                # 主配置
    ├── strategies.yaml            # 策略配置
    └── risk_limits.yaml           # 风控配置
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/stock-agent
pip install -r requirements.txt
```

### 2. 配置账户

```yaml
# config.yaml
account:
  initial_capital: 1000000  # 初始资金 100 万
  currency: CNY
  commission_rate: 0.0003  # 佣金万三
  stamp_duty: 0.001  # 印花税千一

data_source:
  primary: tushare
  backup: akshare
```

### 3. 运行模拟交易

```bash
# 启动主程序
python main.py --mode simulate

# 回测模式
python main.py --mode backtest --start 2025-01-01 --end 2026-03-27

# 实时模拟
python main.py --mode live --paper
```

### 4. 查看结果

```bash
# 查看持仓
python main.py query positions

# 查看收益
python main.py query performance

# 生成报告
python main.py report daily
```

---

## 📊 核心功能

### 1. 模拟账户

```python
from stock_agent import Account

# 创建模拟账户
account = Account(initial_capital=1000000)

# 查看账户状态
print(f"可用资金：{account.cash}")
print(f"持仓市值：{account.market_value}")
print(f"总资产：{account.total_value}")
print(f"收益率：{account.return_rate:.2%}")
```

### 2. 股票筛选

```python
from stock_agent.agents import AnalystAgent

analyst = AnalystAgent()

# 多因子选股
stocks = analyst.screen_stocks(
    factors={
        'pe_ratio': (0, 30),  # PE 0-30
        'pb_ratio': (0, 5),   # PB 0-5
        'roe': (10, 100),     # ROE > 10%
        'revenue_growth': (10, 100),  # 营收增长>10%
        'macd_golden_cross': True,  # MACD 金叉
        'volume_ratio': (1.5, 10)  # 量比 1.5-10
    },
    limit=20
)
```

### 3. 自动交易

```python
from stock_agent import StockAgent

# 创建交易员
agent = StockAgent(
    initial_capital=1000000,
    strategy='momentum',  # 动量策略
    risk_limits={'max_position': 0.3}
)

# 运行一天
agent.run_daily('2026-03-27')

# 查看交易记录
trades = agent.get_trades()
for trade in trades:
    print(f"{trade.stock}: {trade.side} {trade.volume}@{trade.price}")
```

### 4. 回测

```python
from stock_agent import Backtester

# 创建回测器
backtester = Backtester(
    strategy='momentum',
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
```

---

## 📈 策略示例

### 动量策略

```python
class MomentumStrategy(BaseStrategy):
    """动量策略 - 追涨杀跌"""
    
    def __init__(self):
        self.lookback_period = 20  # 20 日动量
        self.holding_period = 5    # 持有 5 天
    
    def generate_signals(self, data) -> List[Signal]:
        signals = []
        
        for stock in data.stocks:
            # 计算 20 日涨幅
            momentum = stock.calculate_momentum(20)
            
            # 成交量确认
            volume_ratio = stock.volume / stock.avg_volume(20)
            
            # 买入信号：涨幅前 10% + 放量
            if momentum > 0.15 and volume_ratio > 1.5:
                signals.append(Signal(
                    stock=stock.code,
                    action='BUY',
                    strength=0.8,
                    reason=f'20 日动量 {momentum:.1%}, 量比 {volume_ratio:.1f}'
                ))
        
        return signals
```

### 均值回归策略

```python
class MeanReversionStrategy(BaseStrategy):
    """均值回归 - 低买高卖"""
    
    def __init__(self):
        self.lookback_period = 60  # 60 日均线
        self.threshold = 0.1       # 偏离 10% 触发
    
    def generate_signals(self, data) -> List[Signal]:
        signals = []
        
        for stock in data.stocks:
            # 计算偏离度
            deviation = (stock.price - stock.ma60) / stock.ma60
            
            # 买入信号：低于均线 10%
            if deviation < -self.threshold:
                signals.append(Signal(
                    stock=stock.code,
                    action='BUY',
                    strength=abs(deviation),
                    reason=f'低于 60 日均线 {abs(deviation):.1%}'
                ))
            
            # 卖出信号：高于均线 10%
            elif deviation > self.threshold:
                signals.append(Signal(
                    stock=stock.code,
                    action='SELL',
                    strength=deviation,
                    reason=f'高于 60 日均线 {deviation:.1%}'
                ))
        
        return signals
```

---

## ⚠️ 风控规则

```yaml
# risk_limits.yaml
risk_management:
  # 仓位限制
  position_limits:
    max_single_position: 0.30    # 单只股票最大 30%
    max_sector_exposure: 0.50   # 单板块最大 50%
    min_cash_ratio: 0.10        # 最低现金 10%
  
  # 止损止盈
  stop_loss:
    enabled: true
    percentage: 0.08            # 8% 止损
    trailing: true              # 移动止损
    trailing_pct: 0.05          # 回撤 5% 止盈
  
  # 交易限制
  trading_limits:
    max_daily_trades: 10        # 每日最多 10 笔
    max_turnover_rate: 0.20     # 日换手率<20%
    min_holding_period: 1       # 最少持有 1 天
  
  # 风险指标
  risk_metrics:
    max_drawdown: 0.15          # 最大回撤 15%
    var_95: 0.05                # 95% VaR < 5%
    max_beta: 1.5               # 最大 Beta 1.5
```

---

## 📊 性能指标

| 指标 | 说明 | 计算公式 |
|------|------|----------|
| **总收益** | 累计收益率 | (期末值 - 期初值) / 期初值 |
| **年化收益** | 年化收益率 | (1+ 总收益)^(252/天数) - 1 |
| **最大回撤** | 最大亏损幅度 | max(历史最高 - 当前值) / 历史最高 |
| **夏普比率** | 风险调整后收益 | (年化收益 - 无风险利率) / 年化波动 |
| **胜率** | 盈利交易比例 | 盈利次数 / 总交易次数 |
| **盈亏比** | 平均盈利/平均亏损 | 平均盈利金额 / 平均亏损金额 |
| **换手率** | 交易频繁程度 | 交易金额 / 平均持仓 |

---

## 🔧 配置文件

### config.yaml

```yaml
# 账户配置
account:
  initial_capital: 1000000  # 初始资金
  currency: CNY
  commission_rate: 0.0003
  stamp_duty: 0.001

# 数据源配置 - Tushare Pro 为主
tushare:
  enabled: true
  token: "your_token_here"  # 替换为你的 Tushare Token
  priority: 1
  cache_ttl: 600

# AKShare（备用）
akshare:
  enabled: true
  priority: 2
  cache_ttl: 300

# Agent 配置
agents:
  analyst:
    enabled: true
    technical_weight: 0.4
    fundamental_weight: 0.4
    sentiment_weight: 0.2
  
  trader:
    enabled: true
    strategy: momentum
    max_positions: 10
  
  risk_manager:
    enabled: true
    strict_mode: true

# 运行模式
mode:
  type: simulate  # simulate | backtest | live
  trading_hours:
    morning: "09:30-11:30"
    afternoon: "13:00-15:00"
```

---

## 📝 日志示例

```
[2026-03-27 09:30:00] INFO  Stock-Agent 启动
[2026-03-27 09:30:01] INFO  分析 Agent: 获取市场数据...
[2026-03-27 09:30:05] INFO  分析 Agent: 筛选出 15 只候选股票
[2026-03-27 09:30:06] INFO  风控 Agent: 检查交易限制...
[2026-03-27 09:30:07] INFO  交易 Agent: 执行买入 600519 贵州茅台 100 股 @1800.00
[2026-03-27 09:30:08] INFO  账户更新：持仓 1 只，可用资金 820000.00
[2026-03-27 15:00:00] INFO  日终处理：今日收益 +1.2%，总资产 1012000.00
```

---

## 🎯 下一步开发

1. **Phase 1** - 核心框架
   - [x] 项目结构设计
   - [ ] 状态管理器实现
   - [ ] Agent 基类实现
   - [ ] 模拟账户实现

2. **Phase 2** - 数据与策略
   - [ ] 数据获取模块
   - [ ] 技术指标计算
   - [ ] 基础策略实现
   - [ ] 选股器实现

3. **Phase 3** - 交易与风控
   - [ ] 订单管理
   - [ ] 仓位管理
   - [ ] 风控规则
   - [ ] 止损止盈

4. **Phase 4** - 回测与分析
   - [ ] 回测引擎
   - [ ] 性能分析
   - [ ] 报告生成
   - [ ] 可视化

---

*创建时间：2026-03-27*  
*架构参考：LangGraph + CrewAI*
