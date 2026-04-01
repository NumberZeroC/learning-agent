# 🚀 Stock-Agent 快速入门

**5 分钟上手模拟量化交易**

---

## 📦 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 创建虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 🏃 2. 运行演示

```bash
# 运行演示程序
python main.py --demo
```

**输出示例：**
```
============================================================
📈 Stock-Agent - 智能量化模拟交易系统
============================================================

📝 创建模拟账户...
✅ 账户创建成功，初始资金：¥1,000,000.00

🔄 模拟交易...
✅ 买入 贵州茅台 (600519) 100 股 @¥1800.00
✅ 买入 五粮液 (000858) 200 股 @¥150.00
✅ 买入 宁德时代 (300750) 150 股 @¥200.00

📊 账户概览
----------------------------------------
初始资金：   ¥1,000,000.00
可用资金：   ¥760,000.00
持仓市值：   ¥245,000.00
总资产：     ¥1,005,000.00
总收益：     ¥5,000.00
收益率：     +0.50%
仓位：       24.4%
持仓数量：   3
```

---

## ⚙️ 3. 配置文件

创建 `config.yaml`：

```yaml
# 账户配置
account:
  initial_capital: 1000000  # 初始资金 100 万
  currency: CNY
  commission_rate: 0.0003  # 佣金万三
  stamp_duty: 0.001  # 印花税千一

# 风控限制
risk_limits:
  max_single_position: 0.30  # 单只股票最大 30%
  max_sector_exposure: 0.50  # 单板块最大 50%
  stop_loss_pct: 0.08  # 8% 止损
  take_profit_pct: 0.20  # 20% 止盈

# 数据源
data:
  primary: akshare  # akshare | tushare
  cache_enabled: true
  cache_ttl: 3600
```

---

## 📝 4. 基础用法

### 创建账户

```python
from stock_agent import Account

# 创建模拟账户
account = Account(initial_capital=1000000)

# 查看账户状态
print(f"总资产：¥{account.total_value:,.2f}")
print(f"收益率：{account.return_rate:.2%}")
```

### 买入股票

```python
# 买入 100 股贵州茅台
order = account.buy('600519', '贵州茅台', 100, 1800.00)

if order:
    print(f"✅ 买入成功：{order.volume}股 @¥{order.price}")
else:
    print("❌ 买入失败")
```

### 卖出股票

```python
# 卖出 50 股贵州茅台
order = account.sell('600519', 50, 1850.00)

if order:
    print(f"✅ 卖出成功：{order.volume}股 @¥{order.price}")
```

### 查看持仓

```python
# 获取所有持仓
positions = account.get_positions()

for pos in positions:
    print(f"{pos.stock_name}: {pos.volume}股 "
          f"成本¥{pos.avg_cost:.2f} 收益{pos.profit_rate:.2%}")
```

### 更新价格

```python
# 更新持仓价格（模拟实时行情）
prices = {
    '600519': 1850.00,
    '000858': 155.00,
}
account.update_prices(prices)

# 查看最新账户状态
print(f"最新总资产：¥{account.total_value:,.2f}")
```

---

## 🤖 5. Agent 架构（开发中）

### 分析 Agent

```python
from stock_agent.agents import AnalystAgent

analyst = AnalystAgent()

# 筛选股票
stocks = analyst.screen_stocks(
    pe_max=30,
    roe_min=10,
    macd_golden_cross=True
)

# 生成信号
signals = analyst.generate_signals()
```

### 交易 Agent

```python
from stock_agent.agents import TraderAgent

trader = TraderAgent(account)

# 执行信号
for signal in signals:
    trader.execute_trade(signal)
```

### 风控 Agent

```python
from stock_agent.agents import RiskManagerAgent

risk_mgr = RiskManagerAgent(account)

# 检查交易
if risk_mgr.check_trade(order):
    print("✅ 交易合规")
else:
    print("❌ 交易违规")
```

---

## 📊 6. 回测（开发中）

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

## 🔧 7. 常用命令

```bash
# 运行演示
python main.py --demo

# 查询持仓
python main.py --query positions

# 查询账户概览
python main.py --query summary

# 使用自定义配置
python main.py --config my_config.yaml
```

---

## 📁 项目结构

```
stock-agent/
├── main.py                    # 主程序入口
├── config.yaml                # 配置文件
├── requirements.txt           # 依赖
├── README.md                  # 项目说明
├── QUICKSTART.md              # 本文件
└── stock_agent/               # 核心模块
    ├── __init__.py
    ├── config.py              # 配置管理
    ├── account.py             # 账户管理
    └── state_manager.py       # 状态管理
```

---

## 🎯 下一步

1. **学习架构** - 阅读 `README.md` 了解系统架构
2. **开发 Agent** - 实现分析、交易、风控 Agent
3. **添加策略** - 实现量化交易策略
4. **运行回测** - 验证策略效果

---

## ❓ 常见问题

### Q: 如何修改初始资金？

A: 在 `config.yaml` 中修改 `account.initial_capital`

### Q: 支持哪些数据源？

A: 目前支持 AKShare（免费），后续支持 Tushare

### Q: 如何添加新策略？

A: 在 `strategies/` 目录创建新策略类，继承 `BaseStrategy`

### Q: 模拟交易和实盘有什么区别？

A: 模拟交易使用虚拟资金，不影响真实账户，用于策略验证

---

*最后更新：2026-03-27*
