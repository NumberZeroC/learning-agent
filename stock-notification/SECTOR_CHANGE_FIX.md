# 板块涨幅数据修复说明

## 问题原因

用户反馈板块涨幅数据与东方财富实际数据有出入。

### 根本原因

1. **`_get_sector_with_market_flow` 函数**：
   - 返回的股票数据中 `change_pct` 固定为 `0`
   - 没有从 Tushare 或任何数据源获取真实的涨跌幅数据

2. **`get_market_moneyflow` 函数**：
   - 只调用了 `moneyflow` 接口获取资金流
   - **没有调用 `daily` 接口获取日线行情（包含涨跌幅）**
   - 导致计算的板块平均涨幅始终为 0

## 修复方案

### 1. 修复 `get_market_moneyflow` 函数

在获取资金流的同时，获取日线行情数据：

```python
# 🔥 获取日线行情（包含涨跌幅）
daily = self.tushare_pro.get_daily(ts_code=ts_code, trade_date=trade_date)

# 获取资金流
mf = self.tushare_pro.get_moneyflow(ts_code=ts_code, trade_date=trade_date)

if daily or mf:
    if code not in market_flow:
        market_flow[code] = {'code': code, 'name': ''}
    
    # 🔥 从日线获取涨跌幅和价格
    if daily:
        market_flow[code]['close'] = daily.get('close', 0)
        market_flow[code]['change_pct'] = daily.get('pct_chg', 0)
        market_flow[code]['name'] = daily.get('name', '')
    
    # 从资金流获取主力资金
    if mf:
        market_flow[code]['main_force_in'] = mf.get('net_mf_amount', 0)
```

### 2. 修复 `_get_sector_with_market_flow` 函数

使用真实的涨跌幅数据：

```python
# 🔥 修复：从 market_flow 获取真实的涨跌幅数据
change_pct = flow_data.get('change_pct', 0)
price = flow_data.get('close', 0) or flow_data.get('price', 0)

result.append({
    'code': code,
    'name': flow_data.get('name', ''),
    'price': price,
    'change_pct': change_pct,  # 🔥 使用真实涨跌幅
    ...
})
```

## 验证方法

### 1. 手动测试

```bash
cd /home/admin/.openclaw/workspace/stock-agent
/home/admin/.openclaw/workspace/stock-agent/venv311/bin/python3 evening_analysis.py
```

查看输出：
```
板块涨幅 TOP5:
1. 半导体：+3.25% (净流入 +1200 万)  # 应该有真实涨幅数据
2. 人工智能：+2.87% (净流入 +800 万)
...
```

### 2. 检查报告

查看生成的报告文件：
```bash
cat /home/admin/.openclaw/workspace/data/reports/evening_summary_2026-03-27.md
```

确认板块涨幅表格中有真实数据：
```markdown
## 🏆 板块涨幅 TOP10（推荐）

| 排名 | 板块 | 平均涨幅 | ... |
|------|------|----------|-----|
| 1 | 半导体 | 🔴 +3.2% | ... |
| 2 | 人工智能 | 🔴 +2.8% | ... |
```

## 数据源说明

### Tushare Pro 接口

| 接口 | 积分要求 | 用途 |
|------|----------|------|
| `daily` | 基础 | 日线行情（包含涨跌幅 `pct_chg`） |
| `moneyflow` | 300 | 个股资金流（主力净流入 `net_mf_amount`） |
| `top_list` | 2000 | 龙虎榜数据 |
| `top_inst` | 2000 | 龙虎榜机构交易 |

### 字段映射

- `daily.pct_chg` → `change_pct`（涨跌幅%）
- `daily.close` → `close`（收盘价）
- `moneyflow.net_mf_amount` → `main_force_in`（主力净流入）

## 预期效果

修复后，板块涨幅数据应该与东方财富一致：

1. **板块平均涨幅** = 成分股涨跌幅的算术平均
2. **排序**：按板块平均涨幅从高到低
3. **显示**：同时显示涨幅和资金流数据

## 注意事项

1. **Tushare 积分**：确保有足够的积分（至少 300 分用于 moneyflow）
2. **API 调用频率**：已添加缓存，同一交易日不重复获取
3. **网络稳定性**：添加异常处理，部分股票失败不影响整体

## 相关文件

- `src/capital_flow.py` - 资金流分析模块（已修复）
- `evening_analysis.py` - 晚间分析报告
- `services/capital_fetcher.py` - 资金流服务

---

*修复时间：2026-03-27*  
*修复版本：1.1*
