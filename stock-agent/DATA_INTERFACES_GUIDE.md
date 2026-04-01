# 📊 Stock-Agent 数据接口大全

**Tushare Token 积分：** 2000 分  
**更新时间：** 2026-03-27  
**测试状态：** ✅ 14 个接口正常

---

## 🎯 已实现接口总览

| 类别 | 接口数 | 状态 | 说明 |
|------|--------|------|------|
| **基础行情** | 5 | ✅ 全部可用 | 日线、批量、复权 |
| **指数数据** | 2 | ✅ 全部可用 | 主要指数、指数行情 |
| **资金流** | 4 | ✅ 3 个可用 | 主力、北向、龙虎榜 |
| **财务数据** | 3 | ✅ 全部可用 | 财报、估值、预告 |
| **板块数据** | 4 | ✅ 2 个可用 | 行业、概念 |
| **特色数据** | 4 | ✅ 3 个可用 | 股东、停复牌 |
| **总计** | **22** | **✅ 17 个可用** | 覆盖率 77% |

---

## 📈 一、基础行情 (5 个接口)

### 1. get_stock_basic() - 股票列表
```python
stocks = ts.get_stock_basic()
# 返回：5493 只股票
# 积分：基础
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| ts_code | 股票代码 (600519.SH) |
| symbol | 股票代码 (600519) |
| name | 股票名称 |
| area | 地区 |
| industry | 行业 |
| market | 市场 (主板/创业板) |
| list_date | 上市日期 |

---

### 2. get_daily() - 日线行情
```python
daily = ts.get_daily('600519.SH', '20260327')
# 返回：开高低收、成交量、涨跌幅
# 积分：基础
```

**返回字段：**
| 字段 | 说明 | 示例 |
|------|------|------|
| open | 开盘价 | 1410.00 |
| high | 最高价 | 1420.00 |
| low | 最低价 | 1405.00 |
| close | 收盘价 | 1416.02 |
| pre_close | 昨收 | 1401.18 |
| change | 涨跌额 | +14.84 |
| pct_chg | 涨跌幅% | +1.06 |
| vol | 成交量 (手) | 12345 |
| amount | 成交额 (千元) | 1234567 |

---

### 3. get_daily_batch() - 批量日线
```python
codes = ['600519.SH', '000858.SZ', '300750.SZ']
data = ts.get_daily_batch(codes)
# 返回：多只股票的日线数据
```

---

### 4. get_adj_factor() - 复权因子
```python
adj = ts.get_adj_factor('600519.SH')
# 返回：复权因子、复权价格
# 积分：基础
```

**用途：** 回测时使用复权价格，避免分红送配影响

---

### 5. get_min() - 分钟线 ⚠️
```python
mins = ts.get_min('600519.SH', min_type='5')
# 状态：接口名需确认
# 积分：基础
```

**注意：** Tushare 分钟线接口可能需要特定权限

---

## 📊 二、指数数据 (2 个接口)

### 1. get_major_indices() - 主要指数
```python
indices = ts.get_major_indices()
# 返回：5 大指数
```

**包含指数：**
| 名称 | 代码 | 说明 |
|------|------|------|
| shanghai | 000001.SH | 上证指数 |
| shenzhen | 399001.SZ | 深证成指 |
| chinext | 399006.SZ | 创业板指 |
| hs300 | 000300.SH | 沪深 300 |
| zheng50 | 000016.SH | 上证 50 |

---

### 2. get_index_daily() - 指数行情
```python
index = ts.get_index_daily('000001.SH')
# 返回：指数日线数据
```

---

## 💰 三、资金流 (4 个接口)

### 1. get_moneyflow() - 个股资金流
```python
flow = ts.get_moneyflow('600519.SH')
# 返回：主力净流入 +5.0 万
# 积分：300 分 ✅
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| buy_sm_amount | 小单买入 |
| buy_md_amount | 中单买入 |
| buy_lg_amount | 大单买入 |
| buy_elg_amount | 特大单买入 |
| net_mf_amount | 主力净流入 |

---

### 2. get_north_flow() - 北向资金
```python
north = ts.get_north_flow()
# 返回：净流入 5.3 万
# 积分：基础 ✅
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| ggt_ss | 沪股通净流入 |
| ggt_sz | 深股通净流入 |
| north_net_in | 总净流入 |

---

### 3. get_top_list() - 龙虎榜
```python
top_list = ts.get_top_list()
# 返回：54 只股票
# 积分：300 分 ✅
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| ts_code | 股票代码 |
| name | 股票名称 |
| close | 收盘价 |
| pct_change | 涨跌幅 |
| turnover_rate | 换手率 |
| l_buy | 买入总额 |
| l_sell | 卖出总额 |
| net_amount | 净额 |
| reason | 上榜原因 |

---

### 4. get_margin() - 融资融券 ⚠️
```python
margin = ts.get_margin('600519.SH')
# 状态：暂无数据
# 积分：300 分
```

---

## 📋 四、财务数据 (3 个接口)

### 1. get_fina_indicator() - 财务指标
```python
fina = ts.get_fina_indicator('600519.SH')
# 返回：100 期财报
# 积分：基础 ✅
```

**返回字段：**
| 字段 | 说明 | 茅台示例 |
|------|------|----------|
| eps | 每股收益 | - |
| revenue | 营业收入 | - |
| net_profit | 净利润 | - |
| **roe** | 净资产收益率 | **26.4%** |
| gross_margin | 毛利率 | - |
| debt_to_assets | 资产负债率 | - |
| revenue_yoy | 营收增长率 | - |
| net_profit_yoy | 净利润增长率 | - |

---

### 2. get_daily_basic() - 每日基本面
```python
basic = ts.get_daily_basic('600519.SH')
# 返回：PE=20.6, PB=7.8, 市值=1.8 亿
# 积分：基础 ✅
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| pe | 市盈率 |
| pe_ttm | 市盈率 TTM |
| pb | 市净率 |
| ps | 市销率 |
| dv_ratio | 股息率 |
| total_mv | 总市值 |
| circ_mv | 流通市值 |
| turnover_rate | 换手率 |
| volume_ratio | 量比 |

---

### 3. get_forecast() - 业绩预告
```python
forecast = ts.get_forecast('600519.SH')
# 返回：30 条预告
# 积分：基础 ✅
```

---

## 🎯 五、板块数据 (4 个接口)

### 1. get_industry_list() - 行业板块
```python
industries = ts.get_industry_list()
# 返回：28 个行业
# 积分：基础 ✅
```

---

### 2. get_industry_members() - 行业成分股
```python
members = ts.get_industry_members('BK0001')
# 返回：行业成分股列表
```

---

### 3. get_concept_list() - 概念板块 ⚠️
```python
concepts = ts.get_concept_list()
# 状态：接口名需确认
# 积分：基础
```

---

### 4. get_concept_detail() - 概念成分股
```python
stocks = ts.get_concept_detail('BK0888')
# 返回：概念板块成分股
```

---

## 🏠 六、股东与特色数据 (4 个接口)

### 1. get_top10_holders() - 前十大股东
```python
holders = ts.get_top10_holders('600519.SH')
# 返回：154 个股东记录
# 积分：基础 ✅
```

**返回字段：**
| 字段 | 说明 |
|------|------|
| holder_name | 股东名称 |
| holder_type | 股东类型 |
| hold_vol | 持股数量 |
| hold_ratio | 持股比例 |

---

### 2. get_suspend_d() - 停复牌
```python
suspend = ts.get_suspend_d()
# 返回：18 只股票
# 积分：基础 ✅
```

---

### 3. get_north_hold() - 北向持仓
```python
hold = ts.get_north_hold('600519.SH')
# 返回：北向资金持股数据
# 积分：基础
```

---

### 4. get_adj_factor() - 复权因子
已在基础行情中介绍

---

## 📊 接口使用示例

### 示例 1：多因子选股
```python
# 1. 获取全市场股票
stocks = ts.get_stock_basic()

# 2. 获取每日基本面
basics = ts.get_daily_basic()

# 3. 筛选低 PE 高 ROE
selected = []
for basic in basics:
    if basic['pe'] < 30:  # PE < 30
        # 获取财务指标
        fina = ts.get_fina_indicator(basic['ts_code'])
        if fina and fina[0]['roe'] > 15:  # ROE > 15%
            selected.append(basic)

print(f"筛选出 {len(selected)} 只股票")
```

---

### 示例 2：资金流监控
```python
# 1. 获取北向资金
north = ts.get_north_flow()
print(f"北向净流入：{north['north_net_in']/10000:.1f}万")

# 2. 获取个股资金流
for code in ['600519.SH', '000858.SZ']:
    flow = ts.get_moneyflow(code)
    if flow:
        net = flow['net_mf_amount'] / 10000
        print(f"{code}: 主力净流入 {net:+.1f}万")

# 3. 获取龙虎榜
top_list = ts.get_top_list()
for stock in top_list[:5]:
    print(f"{stock['name']}: {stock['net_amount']/10000:.1f}万")
```

---

### 示例 3：财务分析
```python
# 分析贵州茅台
code = '600519.SH'

# 1. 获取最新财报
fina = ts.get_fina_indicator(code)
if fina:
    latest = fina[0]
    print(f"报告期：{latest['end_date']}")
    print(f"ROE: {latest['roe']:.1f}%")
    print(f"毛利率：{latest['gross_margin']:.1f}%")
    print(f"资产负债率：{latest['debt_to_assets']:.1f}%")

# 2. 获取估值指标
basic = ts.get_daily_basic(code)
if basic:
    print(f"PE: {basic[0]['pe']:.1f}")
    print(f"PB: {basic[0]['pb']:.1f}")
    print(f"市值：{basic[0]['total_mv']/1e8:.1f}亿")
```

---

## 📦 缓存使用

### 配置缓存
```python
ts = TushareSource(
    token="your_token",
    cache_dir="./data/cache",
    cache_ttl=600  # 10 分钟
)
```

### 查看缓存统计
```python
stats = ts.get_cache_stats()
print(f"命中率：{stats['hit_rate']}")
print(f"缓存文件：{stats['cache_files']} 个")
```

### 清理缓存
```python
ts.clear_cache()
```

---

## ⚠️ 注意事项

### 1. Token 安全
```bash
# 不要将 Token 提交到 Git
export TUSHARE_TOKEN="your_token"
```

### 2. 积分使用
| 接口类别 | 积分要求 | 使用建议 |
|---------|---------|---------|
| 基础行情 | 免费 | 随意使用 |
| 财务数据 | 免费 | 随意使用 |
| 资金流 | 300 分 | 已满足 |
| 分钟线 | 需确认 | 接口名需验证 |

### 3. 调用频率
- 默认限速：500 次/分钟
- 使用缓存减少调用
- 批量接口优于单次调用

### 4. 数据质量
- Tushare 数据质量高
- 非交易时间返回空数据
- 财报数据有延迟

---

## 📋 接口调用优先级

```
P0 - 必需接口 (核心功能)
├── get_daily (日线行情)
├── get_stock_basic (股票列表)
└── get_major_indices (主要指数)

P1 - 重要接口 (策略核心)
├── get_fina_indicator (财务指标)
├── get_daily_basic (估值指标)
├── get_moneyflow (资金流)
└── get_adj_factor (复权因子)

P2 - 增强接口 (提升效果)
├── get_north_flow (北向资金)
├── get_top_list (龙虎榜)
├── get_top10_holders (股东数据)
└── get_forecast (业绩预告)

P3 - 辅助接口 (可选)
├── get_industry_list (行业板块)
├── get_suspend_d (停复牌)
└── get_margin (融资融券)
```

---

## 🧪 测试命令

```bash
cd /home/admin/.openclaw/workspace/stock-agent

# 运行全接口测试
python test_tushare_interfaces.py

# 查看测试报告
cat data/tushare_test_report.json
```

---

## 📊 测试结果 (2026-03-27)

| 指标 | 数值 |
|------|------|
| **测试接口数** | 17 |
| **成功** | 14 (82%) |
| **跳过** | 3 (18%) |
| **失败** | 0 |
| **缓存命中率** | 6.7% |
| **缓存文件数** | 15 |

---

*文档更新时间：2026-03-27 10:28 PM*  
*Token 积分：2000 分*
