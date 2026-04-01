# 📈 Stock-Agent 回测系统设计

**版本：** 1.0  
**设计时间：** 2026-03-29  
**状态：** 设计中

---

## 🎯 设计目标

构建一个专业、灵活、可扩展的回测系统，支持：

1. **多策略回测** - 支持不同选股/交易策略
2. **历史数据回测** - 基于真实历史数据
3. **绩效分析** - 全面的性能指标
4. **可视化报告** - 图表 + 文字报告
5. **参数优化** - 策略参数网格搜索

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Stock-Agent 回测系统                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  回测引擎 (Backtester)                │  │
│  │  • 初始化账户                                         │  │
│  │  • 按时间顺序推进                                     │  │
│  │  • 调用策略生成信号                                   │  │
│  │  • 执行交易模拟                                       │  │
│  │  • 记录持仓和交易                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↑                                   │
│         ┌────────────────┼────────────────┐                 │
│         │                │                │                 │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐        │
│  │  策略层     │  │  数据层     │  │  账户层     │        │
│  │  Strategy   │  │  Data       │  │  Account    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         │                │                │                 │
│         │                │                │                 │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐        │
│  │ 动量策略    │  │ Tushare     │  │ 模拟账户    │        │
│  │ 价值策略    │  │ AKShare     │  │ 持仓管理    │        │
│  │ 均值回归    │  │ 历史数据    │  │ 交易记录    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  绩效分析 (Analyzer)                  │  │
│  │  • 收益率指标                                         │  │
│  │  • 风险指标                                           │  │
│  │  • 交易统计                                           │  │
│  │  • 生成报告                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 模块设计

### 1. 回测引擎 (`backtester.py`)

```python
class Backtester:
    """回测引擎"""
    
    def __init__(
        self,
        strategy: BaseStrategy,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000,
        commission_rate: float = 0.0003,
        stamp_duty: float = 0.001,
        data_source: str = 'tushare'
    ):
        """
        初始化回测器
        
        Args:
            strategy: 交易策略
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            initial_capital: 初始资金
            commission_rate: 佣金率
            stamp_duty: 印花税
            data_source: 数据源 (tushare | akshare)
        """
        pass
    
    def run(self) -> BacktestResult:
        """运行回测"""
        pass
    
    def _next_bar(self, date: str):
        """推进到下一个交易日"""
        pass
    
    def _generate_signals(self, date: str) -> List[Signal]:
        """生成交易信号"""
        pass
    
    def _execute_signals(self, signals: List[Signal]):
        """执行交易信号"""
        pass
```

---

### 2. 策略基类 (`strategies/base.py`)

```python
class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, params: Dict = None):
        self.params = params or {}
    
    @abstractmethod
    def generate_signals(
        self,
        date: str,
        data: MarketData,
        account: Account
    ) -> List[Signal]:
        """
        生成交易信号
        
        Args:
            date: 当前日期
            data: 市场数据
            account: 账户状态
            
        Returns:
            交易信号列表
        """
        pass
    
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
```

---

### 3. 交易信号 (`signal.py`)

```python
@dataclass
class Signal:
    """交易信号"""
    
    stock_code: str
    stock_name: str
    action: str  # BUY | SELL
    price: float
    volume: int
    confidence: float  # 置信度 0-1
    reason: str  # 信号原因
    date: str
    
    # 可选参数
    stop_loss: float = None  # 止损价
    take_profit: float = None  # 止盈价
    hold_period: int = 5  # 预期持有天数
```

---

### 4. 市场数据 (`market_data.py`)

```python
@dataclass
class MarketData:
    """市场数据快照"""
    
    date: str
    
    # 股票日线数据
    daily_quotes: Dict[str, DailyQuote]
    
    # 指数数据
    index_quotes: Dict[str, IndexQuote]
    
    # 资金流数据
    moneyflow: Dict[str, MoneyFlow]
    
    # 财务数据
    fundamentals: Dict[str, Fundamental]
    
    def get_quote(self, ts_code: str) -> Optional[DailyQuote]:
        """获取股票行情"""
        pass
    
    def get_history(self, ts_code: str, days: int) -> List[DailyQuote]:
        """获取历史行情"""
        pass
```

```python
@dataclass
class DailyQuote:
    """日线行情"""
    
    ts_code: str
    trade_date: str
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    change: float
    pct_chg: float
    vol: float  # 成交量 (手)
    amount: float  # 成交额 (千元)
```

---

### 5. 绩效分析 (`analyzer.py`)

```python
class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, result: BacktestResult):
        self.result = result
    
    def calculate_metrics(self) -> PerformanceMetrics:
        """计算绩效指标"""
        pass
    
    def generate_report(self, format: str = 'markdown') -> str:
        """生成回测报告"""
        pass
```

```python
@dataclass
class PerformanceMetrics:
    """绩效指标"""
    
    # 收益指标
    total_return: float  # 总收益率
    annual_return: float  # 年化收益率
    excess_return: float  # 超额收益 (相对基准)
    
    # 风险指标
    max_drawdown: float  # 最大回撤
    volatility: float  # 年化波动率
    var_95: float  # 95% VaR
    
    # 风险调整收益
    sharpe_ratio: float  # 夏普比率
    sortino_ratio: float  # 索提诺比率
    calmar_ratio: float  # 卡玛比率
    
    # 交易统计
    total_trades: int  # 总交易次数
    win_rate: float  # 胜率
    profit_loss_ratio: float  # 盈亏比
    avg_win: float  # 平均盈利
    avg_loss: float  # 平均亏损
    avg_hold_period: float  # 平均持有天数
    
    # 其他
    benchmark_return: float  # 基准收益
    alpha: float  # Alpha
    beta: float  # Beta
    information_ratio: float  # 信息比率
```

---

## 📊 回测流程

```
┌─────────────────────────────────────────────────────────────┐
│                      回测执行流程                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 初始化                                                   │
│     ┌──────────────────────────────────────────────────┐    │
│     │ • 创建模拟账户                                    │    │
│     │ • 加载历史数据                                    │    │
│     │ • 初始化策略                                      │    │
│     └──────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  2. 按交易日推进                                             │
│     ┌──────────────────────────────────────────────────┐    │
│     │ for date in trading_dates:                       │    │
│     │     │                                            │    │
│     │     │ # 获取当日数据                             │    │
│     │     │ data = get_market_data(date)               │    │
│     │     │                                            │    │
│     │     │ # 更新持仓价格                             │    │
│     │     │ account.update_prices(data)                │    │
│     │     │                                            │    │
│     │     │ # 检查止损止盈                             │    │
│     │     │ signals = check_stop_loss(account, data)   │    │
│     │     │                                            │    │
│     │     │ # 生成新信号                               │    │
│     │     │ new_signals = strategy.generate_signals()  │    │
│     │     │                                            │    │
│     │     │ # 执行交易                                 │    │
│     │     │ execute_trades(signals, account)           │    │
│     │     │                                            │    │
│     │     │ # 记录快照                                 │    │
│     │     │ record_snapshot(date, account)             │    │
│     └──────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  3. 绩效分析                                                 │
│     ┌──────────────────────────────────────────────────┐    │
│     │ • 计算收益率曲线                                  │    │
│     │ • 计算风险指标                                    │    │
│     │ • 生成交易统计                                    │    │
│     │ • 对比基准指数                                    │    │
│     └──────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  4. 生成报告                                                 │
│     ┌──────────────────────────────────────────────────┐    │
│     │ • Markdown 报告                                   │    │
│     │ • JSON 结果                                       │    │
│     │ • 图表可视化                                      │    │
│     └──────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 绩效指标详解

### 收益指标

| 指标 | 公式 | 说明 |
|------|------|------|
| **总收益率** | (期末总值 - 期初总值) / 期初总值 | 整体收益 |
| **年化收益率** | (1 + 总收益率)^(252/交易日数) - 1 | 年化标准 |
| **超额收益** | 策略收益 - 基准收益 | 相对表现 |

### 风险指标

| 指标 | 公式 | 说明 |
|------|------|------|
| **最大回撤** | max(历史最高值 - 当前值) / 历史最高值 | 最大亏损幅度 |
| **年化波动率** | std(日收益率) × √252 | 收益波动程度 |
| **VaR(95%)** | 日收益率的 5% 分位数 | 95% 置信度最大日亏损 |

### 风险调整收益

| 指标 | 公式 | 说明 |
|------|------|------|
| **夏普比率** | (年化收益 - 无风险利率) / 年化波动率 | 单位风险的超额收益 |
| **索提诺比率** | (年化收益 - 无风险利率) / 下行波动率 | 只考虑下行风险 |
| **卡玛比率** | 年化收益 / 最大回撤 | 收益回撤比 |

### 交易统计

| 指标 | 公式 | 说明 |
|------|------|------|
| **胜率** | 盈利交易次数 / 总交易次数 | 交易成功概率 |
| **盈亏比** | 平均盈利 / 平均亏损 | 盈利亏损比 |
| **期望值** | 胜率×平均盈利 - (1-胜率)×平均亏损 | 单次交易期望收益 |

---

## 📁 文件结构

```
stock-agent/
├── backtest/
│   ├── __init__.py
│   ├── backtester.py          # 回测引擎
│   ├── analyzer.py            # 绩效分析
│   ├── signal.py              # 交易信号
│   ├── market_data.py         # 市场数据
│   └── result.py              # 回测结果
│
├── strategies/
│   ├── __init__.py
│   ├── base.py                # 策略基类
│   ├── momentum.py            # 动量策略
│   ├── value.py               # 价值策略
│   ├── mean_reversion.py      # 均值回归
│   └── breakout.py            # 突破策略
│
├── reports/
│   └── backtest_*.md          # 回测报告
│
├── run_backtest.py            # 回测入口脚本
└── BACKTEST_DESIGN.md         # 本文件
```

---

## 🚀 使用示例

### 基础回测

```python
from backtest import Backtester
from strategies.momentum import MomentumStrategy

# 创建策略
strategy = MomentumStrategy(
    lookback_period=20,
    holding_period=5,
    top_n=10
)

# 创建回测器
backtester = Backtester(
    strategy=strategy,
    start_date='2025-01-01',
    end_date='2026-03-29',
    initial_capital=1000000,
    commission_rate=0.0003
)

# 运行回测
result = backtester.run()

# 查看结果
print(f"总收益率：{result.metrics.total_return:.2%}")
print(f"年化收益：{result.metrics.annual_return:.2%}")
print(f"最大回撤：{result.metrics.max_drawdown:.2%}")
print(f"夏普比率：{result.metrics.sharpe_ratio:.2f}")
print(f"胜率：{result.metrics.win_rate:.2%}")
```

### 参数优化

```python
from backtest import Backtester, ParameterOptimizer
from strategies.momentum import MomentumStrategy

# 定义参数网格
param_grid = {
    'lookback_period': [10, 20, 30, 60],
    'holding_period': [3, 5, 10, 20],
    'top_n': [5, 10, 20, 30]
}

# 参数优化
optimizer = ParameterOptimizer(
    strategy_class=MomentumStrategy,
    param_grid=param_grid,
    start_date='2025-01-01',
    end_date='2026-03-29'
)

# 运行优化
best_params, best_result = optimizer.optimize(metric='sharpe_ratio')

print(f"最优参数：{best_params}")
print(f"最优夏普比率：{best_result.metrics.sharpe_ratio:.2f}")
```

### 多策略对比

```python
from backtest import Backtester, StrategyComparator
from strategies import MomentumStrategy, ValueStrategy, MeanReversionStrategy

# 定义策略
strategies = [
    MomentumStrategy(lookback_period=20),
    ValueStrategy(pe_max=30, roe_min=10),
    MeanReversionStrategy(lookback_period=60, threshold=0.1)
]

# 对比回测
comparator = StrategyComparator(
    strategies=strategies,
    start_date='2025-01-01',
    end_date='2026-03-29',
    initial_capital=1000000
)

# 运行对比
results = comparator.run_all()

# 生成对比报告
report = comparator.generate_comparison_report(results)
print(report)
```

---

## 📊 回测报告示例

```markdown
# 📈 回测报告 - 动量策略

**策略名称：** MomentumStrategy  
**回测区间：** 2025-01-01 ~ 2026-03-29  
**初始资金：** ¥1,000,000

---

## 📊 绩效概览

| 指标 | 数值 | 说明 |
|------|------|------|
| **总收益率** | +32.5% | |
| **年化收益率** | +28.7% | |
| **最大回撤** | -12.3% | |
| **夏普比率** | 1.85 | |
| **胜率** | 58.3% | |
| **盈亏比** | 2.1 | |

---

## 📈 收益曲线

[图表：策略收益 vs 基准指数]

---

## 📋 交易统计

- 总交易次数：156
- 盈利交易：91
- 亏损交易：65
- 平均持有天数：8.5 天
- 平均盈利：+5.2%
- 平均亏损：-2.8%

---

## 🏆 持仓贡献 TOP10

| 股票 | 贡献收益 | 交易次数 |
|------|---------|---------|
| 贵州茅台 | +8.5% | 3 |
| 宁德时代 | +6.2% | 5 |
| ... | ... | ... |

---

## ⚠️ 风险提示

- 历史业绩不代表未来表现
- 回测未考虑滑点和冲击成本
- 策略可能存在过拟合风险
```

---

## 🔧 实现优先级

### Phase 1 - 核心功能 (本周)

- [ ] `backtester.py` - 回测引擎核心
- [ ] `signal.py` - 交易信号
- [ ] `market_data.py` - 历史数据加载
- [ ] `analyzer.py` - 绩效分析
- [ ] `strategies/base.py` - 策略基类
- [ ] `strategies/momentum.py` - 动量策略

### Phase 2 - 策略扩展 (下周)

- [ ] `strategies/value.py` - 价值策略
- [ ] `strategies/mean_reversion.py` - 均值回归
- [ ] `strategies/breakout.py` - 突破策略
- [ ] 参数优化器

### Phase 3 - 报告可视化 (下下周)

- [ ] Markdown 报告生成
- [ ] JSON 结果导出
- [ ] 图表可视化 (可选：matplotlib/plotly)
- [ ] 多策略对比

---

## ⚠️ 注意事项

1. **前视偏差** - 确保只使用当日及之前的数据
2. **幸存者偏差** - 使用当时的股票列表，包含已退市股票
3. **交易成本** - 考虑佣金、印花税、滑点
4. **停牌处理** - 停牌股票无法交易
5. **涨跌停限制** - 涨停无法买入，跌停无法卖出
6. **最小交易单位** - A 股最小 100 股 (1 手)

---

*设计完成，等待实现*
