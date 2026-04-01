# 📈 Stock-Agent 回测系统使用指南

**版本：** 1.0  
**创建时间：** 2026-03-29

---

## 🎯 功能概述

回测系统支持：

- ✅ 多策略回测（动量、价值、均值回归等）
- ✅ 历史数据回测（Tushare/AKShare）
- ✅ 完整绩效分析（收益、风险、夏普比率等）
- ✅ Markdown/JSON 报告生成
- ✅ 参数优化（网格搜索）

---

## 📦 文件结构

```
stock-agent/
├── backtest/
│   ├── __init__.py          # 模块导出
│   ├── backtester.py        # 回测引擎 ⭐
│   ├── analyzer.py          # 绩效分析
│   ├── signal.py            # 交易信号
│   ├── market_data.py       # 市场数据
│   └── result.py            # 回测结果
│
├── strategies/
│   ├── __init__.py
│   ├── base.py              # 策略基类
│   ├── momentum.py          # 动量策略
│   └── value.py             # 价值策略
│
├── run_backtest.py          # 回测入口脚本
├── BACKTEST_GUIDE.md        # 本文件
└── reports/
    └── backtest_*.md        # 回测报告
```

---

## 🚀 快速开始

### 1. 基础回测

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 激活虚拟环境
source venv_ak/bin/activate

# 运行动量策略回测
python run_backtest.py --strategy momentum \
    --start 2025-01-01 \
    --end 2026-03-29 \
    --capital 1000000
```

### 2. 自定义参数

```bash
# 动量策略 - 调整参数
python run_backtest.py --strategy momentum \
    --start 2025-01-01 \
    --end 2026-03-29 \
    --top-n 20 \
    --lookback 30 \
    --holding-period 10

# 价值策略
python run_backtest.py --strategy value \
    --start 2025-01-01 \
    --end 2026-03-29 \
    --top-n 15 \
    --holding-period 30
```

### 3. 配置文件

创建 `backtest_config.yaml`:

```yaml
strategy: momentum
start_date: '2025-01-01'
end_date: '2026-03-29'
initial_capital: 1000000

strategy_params:
  lookback_period: 20
  holding_period: 5
  top_n: 10
  ma_period: 20
  rsi_upper: 80
  rsi_lower: 50
```

运行：

```bash
python run_backtest.py --config backtest_config.yaml
```

---

## 📊 回测报告

回测完成后会生成两个文件：

### Markdown 报告 (`reports/backtest_*.md`)

包含：

- 绩效概览（收益率、回撤、夏普比率等）
- 风险调整收益
- 交易统计
- 基准对比
- 交易明细

### JSON 结果 (`reports/backtest_*.json`)

包含完整数据：

- 每日快照
- 所有交易记录
- 绩效指标
- 最终持仓

---

## 📈 绩效指标说明

### 收益指标

| 指标 | 说明 | 优秀标准 |
|------|------|---------|
| **总收益率** | 回测期间总收益 | >20% |
| **年化收益率** | 年化标准收益 | >15% |
| **超额收益** | 相对基准的超额收益 | >5% |

### 风险指标

| 指标 | 说明 | 优秀标准 |
|------|------|---------|
| **最大回撤** | 最大亏损幅度 | <15% |
| **年化波动率** | 收益波动程度 | <25% |
| **95% VaR** | 95% 置信度最大日亏损 | <3% |

### 风险调整收益

| 指标 | 说明 | 优秀标准 |
|------|------|---------|
| **夏普比率** | 单位风险的超额收益 | >1.0 |
| **索提诺比率** | 下行风险调整收益 | >1.5 |
| **卡玛比率** | 收益/最大回撤 | >2.0 |

### 交易统计

| 指标 | 说明 | 优秀标准 |
|------|------|---------|
| **胜率** | 盈利交易占比 | >50% |
| **盈亏比** | 平均盈利/平均亏损 | >1.5 |
| **平均持有天数** | 平均持仓时间 | 策略相关 |

---

## 🔧 自定义策略

### 1. 创建策略类

在 `strategies/` 目录创建新策略：

```python
# strategies/my_strategy.py
from typing import List, Dict, Any
from backtest.signal import Signal, SignalType
from strategies.base import BaseStrategy


class MyStrategy(BaseStrategy):
    """我的自定义策略"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'top_n': 10,
            'holding_period': 5,
        }
        
        if params:
            default_params.update(params)
        
        super().__init__(default_params)
        self.name_str = "我的策略"
    
    def generate_signals(
        self,
        date: str,
        data: Dict,
        account: Any,
        market_data: Any = None
    ) -> List[Signal]:
        """生成交易信号"""
        signals = []
        
        # 实现你的策略逻辑
        # ...
        
        return signals
```

### 2. 注册策略

编辑 `strategies/__init__.py`:

```python
from .my_strategy import MyStrategy

__all__ = [
    'BaseStrategy',
    'MomentumStrategy',
    'ValueStrategy',
    'MyStrategy',  # 添加新策略
]
```

### 3. 运行回测

```bash
python run_backtest.py --strategy my_strategy
```

---

## 🧪 参数优化

### 网格搜索

```python
from backtest import Backtester
from strategies import MomentumStrategy
from itertools import product

# 定义参数网格
param_grid = {
    'lookback_period': [10, 20, 30],
    'holding_period': [3, 5, 10],
    'top_n': [5, 10, 20],
}

# 遍历所有组合
best_sharpe = 0
best_params = None
best_result = None

for params in product(*param_grid.values()):
    param_dict = dict(zip(param_grid.keys(), params))
    
    strategy = MomentumStrategy(param_dict)
    backtester = Backtester(
        strategy=strategy,
        start_date='2025-01-01',
        end_date='2026-03-29',
        data_source=data_source
    )
    
    backtester.prepare_data()
    result = backtester.run()
    
    if result.metrics.sharpe_ratio > best_sharpe:
        best_sharpe = result.metrics.sharpe_ratio
        best_params = param_dict
        best_result = result

print(f"最优参数：{best_params}")
print(f"最优夏普比率：{best_sharpe:.2f}")
```

---

## ⚠️ 注意事项

### 1. 数据质量

- 确保数据源稳定可靠
- 注意停牌、退市股票处理
- 考虑复权因素（当前未实现）

### 2. 前视偏差

- 确保只使用当日及之前的数据
- 财务数据注意发布日期
- 避免使用未来函数

### 3. 交易成本

- 佣金：0.03% (万三)
- 印花税：0.1% (卖出时)
- 滑点：未考虑（实际交易会有）

### 4. 涨跌停限制

- 涨停无法买入
- 跌停无法卖出
- 当前简化处理，未完全模拟

### 5. 最小交易单位

- A 股最小 100 股 (1 手)
- 系统已自动处理

---

## 📝 示例输出

```
======================================================================
📈 Stock-Agent 回测系统
======================================================================
策略：动量策略 (N=20)
区间：2025-01-01 ~ 2026-03-29
资金：¥1,000,000
======================================================================

✅ 策略：动量策略 (N=20)
   参数：{'lookback_period': 20, 'holding_period': 5, 'top_n': 10, ...}

📊 准备历史数据...
✅ 加载 500 只股票，50000 条数据

交易天数：290
============================================================
开始回测：动量策略 (N=20)
区间：2025-01-01 ~ 2026-03-29
初始资金：¥1,000,000
============================================================

进度：0.0% (1/290)
  BUY 贵州茅台 100 股 @¥1800.00
  BUY 宁德时代 100 股 @¥200.00
...

回测完成！期末总值：¥1,325,000
计算绩效指标...

======================================================================
回测结果摘要
======================================================================
总收益率：  +32.50%
年化收益：  +28.70%
最大回撤：  -12.30%
夏普比率：  1.85
胜率：      58.3%
交易次数：  156
======================================================================

📝 生成报告...
✅ 报告已保存：reports/backtest_momentum_20260329_142530.md
✅ 结果已保存：reports/backtest_momentum_20260329_142530.json

======================================================================
📊 回测摘要
======================================================================
【动量策略 (N=20)】回测结果
区间：2025-01-01 ~ 2026-03-29 (290 天)
初始资金：¥1,000,000 → 期末总值：¥1,325,000
总收益率：+32.50%
总收益率：32.50% | 年化收益：28.70% | 最大回撤：12.30% | 夏普比率：1.85 | 胜率：58.3%
======================================================================
```

---

## 🔮 后续优化

### Phase 1 - 已完成 ✅

- [x] 回测引擎核心
- [x] 绩效分析
- [x] 动量/价值策略
- [x] 报告生成

### Phase 2 - 进行中 🚧

- [ ] 更多策略（均值回归、突破）
- [ ] 参数优化器
- [ ] 多策略对比

### Phase 3 - 计划中 📋

- [ ] 图表可视化 (matplotlib/plotly)
- [ ] 实时回测进度显示
- [ ] 分布式回测加速
- [ ] 因子分析工具

---

## 📞 快速命令

```bash
# 基础回测
python run_backtest.py --strategy momentum

# 自定义参数
python run_backtest.py --strategy momentum --top-n 20 --lookback 30

# 价值策略
python run_backtest.py --strategy value --holding-period 30

# 使用配置文件
python run_backtest.py --config backtest_config.yaml

# 查看报告
ls -lh reports/
cat reports/backtest_momentum_*.md
```

---

*回测系统已就绪！开始你的量化之旅吧！* 🚀
