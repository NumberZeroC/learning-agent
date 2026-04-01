# 📊 Stock-Agent 数据源配置 - Tushare Pro

**参考项目：** stock-notification  
**数据源：** Tushare Pro（主）+ AKShare（备用）

---

## 🎯 配置说明

### 1. 获取 Tushare Token

1. 访问 https://tushare.pro
2. 注册账号
3. 进入个人中心 → 接口 Token
4. 复制 Token（如：`0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2`）

### 2. 配置 Token

**方式一：配置文件**

编辑 `config.yaml`：
```yaml
tushare:
  enabled: true
  token: "your_token_here"  # 替换为你的 Token
  priority: 1
```

**方式二：环境变量**

```bash
export TUSHARE_TOKEN=your_token_here
```

---

## 📁 数据源模块

### TushareSource 类

```python
from stock_agent import TushareSource

# 初始化
ts = TushareSource(token="your_token")

# 获取股票列表
stocks = ts.get_stock_basic()

# 获取日线行情
daily = ts.get_daily('600519.SH', '20260327')

# 获取资金流
moneyflow = ts.get_moneyflow('600519.SH', '20260327')

# 获取主要指数
indices = ts.get_major_indices()

# 获取龙虎榜
top_list = ts.get_top_list('20260327')
```

---

## 🔌 支持的数据接口

### 基础数据

| 方法 | 说明 | 积分要求 |
|------|------|----------|
| `get_stock_basic()` | 股票列表 | 基础 |
| `get_daily()` | 日线行情 | 基础 |
| `get_daily_batch()` | 批量日线 | 基础 |

### 资金流

| 方法 | 说明 | 积分要求 |
|------|------|----------|
| `get_moneyflow()` | 个股资金流 | 300 |
| `get_margin()` | 融资融券 | 300 |

### 指数数据

| 方法 | 说明 | 积分要求 |
|------|------|----------|
| `get_index_daily()` | 指数行情 | 基础 |
| `get_major_indices()` | 主要指数 | 基础 |

### 特色数据

| 方法 | 说明 | 积分要求 |
|------|------|----------|
| `get_top_list()` | 龙虎榜 | 300 |
| `get_concept_list()` | 概念板块 | 基础 |
| `get_concept_detail()` | 板块成分股 | 基础 |

---

## 💾 缓存机制

### 自动缓存

所有数据自动缓存到 `data/cache/tushare/` 目录

```python
# 缓存配置
ts = TushareSource(
    token="your_token",
    cache_dir="./data/cache",
    cache_ttl=600  # 10 分钟缓存
)

# 查看缓存统计
stats = ts.get_cache_stats()
print(f"命中率：{stats['hit_rate']}")

# 清理缓存
ts.clear_cache()
```

---

## 📊 使用示例

### 示例 1：获取股票行情

```python
from stock_agent import TushareSource

ts = TushareSource(token="your_token")

# 获取贵州茅台日线
daily = ts.get_daily('600519.SH', '20260327')

if daily:
    print(f"贵州茅台")
    print(f"开盘：{daily['open']}")
    print(f"收盘：{daily['close']}")
    print(f"涨跌幅：{daily['pct_chg']:.2f}%")
    print(f"成交量：{daily['vol']}手")
    print(f"成交额：{daily['amount']}千元")
```

### 示例 2：获取板块成分股

```python
# 获取概念板块列表
concepts = ts.get_concept_list()

# 获取半导体板块成分股
for concept in concepts:
    if '半导体' in concept['name']:
        stocks = ts.get_concept_detail(concept['code'])
        print(f"半导体板块成分股：{len(stocks)}只")
        for stock in stocks[:10]:
            print(f"  {stock['name']} ({stock['ts_code']})")
        break
```

### 示例 3：获取龙虎榜

```python
# 获取今日龙虎榜
top_list = ts.get_top_list()

print("今日龙虎榜:")
for stock in top_list[:10]:
    print(f"  {stock['name']}: {stock['net_amount']/10000:.1f}万")
```

### 示例 4：批量获取行情

```python
# 监控股票池
stocks = ['600519.SH', '000858.SZ', '300750.SZ']

# 批量获取日线
data = ts.get_daily_batch(stocks, '20260327')

for code, daily in data.items():
    print(f"{code}: {daily['close']:.2f} ({daily['pct_chg']:+.2f}%)")
```

---

## 🔧 与 stock-notification 对比

| 项目 | stock-notification | stock-agent |
|------|-------------------|-------------|
| 数据源 | Tushare + AKShare | Tushare + AKShare |
| 主数据源 | Tushare（资金流） | Tushare（全数据） |
| 缓存 | 支持 | 支持 |
|  Token 配置 | config.yaml | config.yaml + 环境变量 |
| 数据接口 | 部分 | 完整 |

---

## ⚠️ 注意事项

1. **Token 安全**
   - 不要将 Token 提交到 Git
   - 使用环境变量存储敏感信息

2. **积分限制**
   - 基础接口：免费
   - 资金流/龙虎榜：300 积分
   - 确保积分充足

3. **调用频率**
   - 默认限速：每分钟 500 次
   - 使用缓存减少调用

4. **数据质量**
   - Tushare 数据质量高
   - AKShare 作为备用
   - 故障自动切换

---

## 📝 配置文件完整示例

```yaml
# ============================================
# Stock-Agent 配置文件
# ============================================

# 账户配置
account:
  initial_capital: 1000000
  commission_rate: 0.0003
  stamp_duty: 0.001

# Tushare Pro 配置
tushare:
  enabled: true
  token: "0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2"
  priority: 1
  cache:
    enabled: true
    ttl_seconds: 600

# AKShare 配置（备用）
akshare:
  enabled: true
  priority: 2
  cache_ttl: 300
  max_retries: 3

# 风控配置
risk_limits:
  max_single_position: 0.30
  stop_loss_pct: 0.08
  take_profit_pct: 0.20
```

---

## 🚀 快速测试

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 安装依赖
pip install tushare

# 设置 Token
export TUSHARE_TOKEN=your_token_here

# 运行测试
python -c "
from stock_agent import TushareSource
ts = TushareSource()
indices = ts.get_major_indices()
for name, data in indices.items():
    print(f'{name}: {data[\"close\"]:.2f} ({data[\"pct_chg\"]:+.2f}%)')
"
```

---

*参考：stock-notification/src/tushare_pro_source.py*  
*更新时间：2026-03-27*
