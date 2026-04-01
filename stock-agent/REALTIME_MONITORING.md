# 📊 Stock-Agent 实时交易监控

**功能：** 交易时间持续运行，实时监控股票，自动操作，记录日志和收益

---

## 🚀 快速启动

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 启动实时监控（默认 60 秒间隔）
python run_monitor.py

# 自定义监控间隔（30 秒）
python run_monitor.py --interval 30

# 指定配置文件
python run_monitor.py --config my_config.yaml
```

---

## 📋 功能特性

### 1. 交易时间自动运行

- **自动判断交易时间**：周一至周五 9:15-11:30, 13:00-15:00
- **非交易时间休眠**：每小时检查一次
- **周末/节假日暂停**：自动跳过非交易日

### 2. 实时监控股票池

**默认监控股票：**
```yaml
monitor_stocks:
  stocks:
    - code: '600519'
      name: '贵州茅台'
    - code: '000858'
      name: '五粮液'
    - code: '300750'
      name: '宁德时代'
    - code: '002594'
      name: '比亚迪'
    - code: '601318'
      name: '中国平安'
```

**自定义股票池：**
```bash
python run_monitor.py --watchlist my_stocks.yaml
```

### 3. 自动交易操作

**止损机制：**
- 亏损超过 8% 自动止损
- 优先级最高，立即执行

**止盈机制：**
- 盈利超过 20% 自动止盈（卖出一半）
- 锁定利润

**买入信号：**
- 可扩展自定义买入策略
- 支持多因子触发

### 4. 操作日志记录

**日志文件：** `data/logs/trading_YYYY-MM-DD.log`

**日志内容：**
```
[2026-03-27 09:30:00] [INFO] ============================================================
[2026-03-27 09:30:00] [INFO] 开始监控循环
[2026-03-27 09:30:01] [INFO] 更新股票价格...
[2026-03-27 09:30:02] [INFO] 检查交易信号...
[2026-03-27 09:30:03] [INFO] ⚠️ 止损信号：五粮液 -8.5%
[2026-03-27 09:30:04] [INFO] 订单 SELL_000858_0: SELL 五粮液 200 股 @¥150.00
[2026-03-27 09:30:05] [INFO] 成交：SELL 五粮液 200 股 @¥150.00 金额¥30000.00
[2026-03-27 09:30:06] [INFO] 收益统计：总资产¥1,007,428.00 收益¥7,428.00 收益率+0.74%
[2026-03-27 09:30:07] [INFO] ============================================================
```

### 5. 交易记录

**交易记录文件：** `data/logs/trades_YYYY-MM-DD.json`

**记录内容：**
```json
[
  {
    "type": "trade",
    "timestamp": "2026-03-27T09:30:04",
    "stock_code": "000858",
    "stock_name": "五粮液",
    "side": "SELL",
    "volume": 200,
    "price": 150.00,
    "amount": 30000.00,
    "commission": 9.00,
    "stamp_duty": 30.00
  }
]
```

### 6. 实时收益统计

**统计指标：**
- 总资产
- 可用资金
- 持仓市值
- 日内收益
- 总收益
- 收益率
- 最大回撤
- 持仓数量
- 仓位比例

---

## 📊 监控日志示例

```
============================================================
📈 Stock-Agent 实时交易监控
============================================================

✅ 账户创建成功
   初始资金：¥1,000,000.00

✅ Tushare Pro 已连接

📊 监控股票池:
   贵州茅台 (600519)
   五粮液 (000858)
   宁德时代 (300750)
   比亚迪 (002594)
   中国平安 (601318)

🚀 启动实时监控...
   监控间隔：60 秒
   按 Ctrl+C 停止监控

[2026-03-27 09:30:00] [INFO] ============================================================
[2026-03-27 09:30:00] [INFO] 开始监控循环
[2026-03-27 09:30:01] [INFO] 更新股票价格...
[2026-03-27 09:30:02] [INFO] 检查交易信号...
[2026-03-27 09:30:03] [INFO] 无交易信号
[2026-03-27 09:30:04] [INFO] 收益统计：总资产¥1,000,000.00 收益¥0.00 收益率 0.00%
[2026-03-27 09:30:05] [INFO] 持仓数量：0, 仓位：0.0%
[2026-03-27 09:30:06] [INFO] ============================================================
```

---

## ⚙️ 配置参数

### config.yaml

```yaml
# 监控股票池
monitor_stocks:
  stocks:
    - code: '600519'
      name: '贵州茅台'
    - code: '000858'
      name: '五粮液'
  
  # 监控频率（秒）
  check_interval: 300

# 风控配置
risk_limits:
  stop_loss_pct: 0.08   # 8% 止损
  take_profit_pct: 0.20 # 20% 止盈
  trailing_stop: true   # 移动止损

# 输出配置
output:
  log_dir: "./data/logs"
  save_history: true
```

---

## 📈 收益统计

### 查看今日交易

```bash
cat data/logs/trades_$(date +%Y-%m-%d).json
```

### 查看操作日志

```bash
tail -f data/logs/trading_$(date +%Y-%m-%d).log
```

### 收益报告

```python
from stock_agent import TradingLogger

logger = TradingLogger()
summary = logger.get_summary()

print(f"今日交易：{summary['total_trades']}笔")
print(f"买入：{summary['buy_count']}, 卖出：{summary['sell_count']}")
```

---

## 🔧 高级用法

### 1. 后台运行

```bash
# 使用 nohup
nohup python run_monitor.py > monitor.log 2>&1 &

# 使用 screen
screen -S stock-monitor
python run_monitor.py
# Ctrl+A, D 退出

# 使用 tmux
tmux new -s stock-monitor
python run_monitor.py
# Ctrl+B, D 退出
```

### 2. 查看进程

```bash
ps aux | grep run_monitor
```

### 3. 停止监控

```bash
# 找到进程 ID
ps aux | grep run_monitor

# 停止
kill <PID>

# 或发送 SIGTERM
kill -15 <PID>
```

### 4. 定时启动

```bash
# crontab -e
# 每个交易日 9:00 启动
0 9 * * 1-5 cd /home/admin/.openclaw/workspace/stock-agent && python run_monitor.py >> logs/monitor.log 2>&1
```

---

## 📊 日志分析

### 日志文件结构

```
data/logs/
├── trading_2026-03-27.log    # 操作日志
├── trades_2026-03-27.json    # 交易记录
├── trading_2026-03-26.log
└── trades_2026-03-26.json
```

### 日志分析脚本

```python
import json
from pathlib import Path
from datetime import datetime

# 加载今日交易记录
today = datetime.now().strftime('%Y-%m-%d')
trade_file = Path(f'data/logs/trades_{today}.json')

if trade_file.exists():
    with open(trade_file, 'r') as f:
        trades = json.load(f)
    
    # 统计
    buy_count = sum(1 for t in trades if t.get('side') == 'BUY')
    sell_count = sum(1 for t in trades if t.get('side') == 'SELL')
    total_amount = sum(t.get('amount', 0) for t in trades)
    
    print(f"今日交易统计:")
    print(f"  买入：{buy_count}笔")
    print(f"  卖出：{sell_count}笔")
    print(f"  总成交额：¥{total_amount:,.2f}")
```

---

## ⚠️ 注意事项

1. **Tushare Token**
   - 确保配置了有效的 Tushare Token
   - 检查积分是否足够

2. **网络稳定**
   - 确保网络连接稳定
   - 断网会自动重试

3. **风险控制**
   - 设置合理的止损止盈
   - 不要过度交易

4. **日志管理**
   - 定期清理旧日志
   - 日志文件可能较大

5. **系统资源**
   - 监控程序占用资源较少
   - 可在后台长期运行

---

## 🎯 下一步优化

1. **更智能的买入策略**
   - 多因子选股
   - 技术指标确认
   - 资金流验证

2. **仓位管理**
   - 动态调整仓位
   - 分批建仓/平仓

3. **风险控制**
   - 最大回撤限制
   - 单日交易次数限制
   - 板块集中度限制

4. **性能优化**
   - 异步数据获取
   - 批量处理
   - 缓存优化

---

## 📝 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--interval, -i` | 监控间隔（秒） | 60 |
| `--config, -c` | 配置文件路径 | config.yaml |
| `--watchlist, -w` | 监控股票列表 | 配置文件 |
| `--initial-capital` | 初始资金 | 配置文件 |

---

*实时交易监控 - Stock-Agent v1.0*  
*最后更新：2026-03-27*
