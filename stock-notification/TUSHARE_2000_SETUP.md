# Tushare 2000 积分配置说明

## ✅ 配置完成

**Token**: `0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2`  
**积分**: 2000 分 (VIP)  
**状态**: ✅ 已连接并启用

---

## 🎯 已启用的资金流接口

### 1. 个股资金流 (`moneyflow`)
- **积分**: 2000 分
- **更新**: 交易日 19:00
- **字段**:
  - `buy_sm_amount` - 小单买入
  - `buy_md_amount` - 中单买入
  - `buy_lg_amount` - 大单买入
  - `buy_elg_amount` - 特大单买入
  - `sell_*` - 对应卖出
  - `net_mf_amount` - 主力净流入

### 2. 龙虎榜每日明细 (`top_list`)
- **积分**: 2000 分
- **更新**: 交易日 20:00
- **字段**:
  - `close` - 收盘价
  - `pct_chg` - 涨跌幅
  - `amount` - 成交额
  - `net` - 净流入
  - `buy/sell` - 买入/卖出总额
  - `reason` - 上榜原因

### 3. 龙虎榜机构交易 (`top_inst`)
- **积分**: 2000 分
- **更新**: 交易日 20:00
- **字段**:
  - `buy_sm` - 机构买入
  - `sell_sm` - 机构卖出
  - `net_sm` - 机构净买卖

### 4. 融资融券汇总 (`margin`)
- **积分**: 2000 分
- **更新**: 交易日 09:00
- **字段**:
  - `buy_amount` - 融资买入额
  - `repay_amount` - 融资偿还额
  - `margin_bal` - 融资余额
  - `net_financing` - 融资净买入

### 5. 融资融券明细 (`margin_detail`)
- **积分**: 2000 分
- **更新**: 交易日 09:00
- **字段**: 同汇总，按个股明细

### 6. 股东增减持 (`stk_holdertrade`)
- **积分**: 2000 分
- **更新**: 交易日 19:00
- **字段**:
  - `holder_name` - 股东名称
  - `change_vol` - 变动数量
  - `change_ratio` - 变动比例
  - `hold_ratio` - 持股比例

---

## 📊 数据获取策略

### 全市场资金流（一次调用）
```python
market_flow = analyzer.get_market_moneyflow(trade_date='20260323')
```
- 获取龙虎榜 63 只股票
- 获取机构席位 690 只股票
- 获取融资融券数据
- 合并去重后约 56 只股票

### 板块资金流（按板块聚合）
```python
stocks = analyzer._get_sector_with_market_flow('半导体', market_flow)
```
- 使用本地板块成分股映射
- 关联全市场资金流数据
- 计算板块总体净流入

### 晚间分析增强
```python
sector_flows = analyzer.analyze_sector_capital_flow()
```
- 包含龙虎榜净流入
- 包含机构净买入
- 包含融资净买入
- 包含上榜股票列表

---

## 📁 修改的文件

### 1. `src/tushare_pro_source.py`
新增接口方法：
- `get_top_list()` - 龙虎榜
- `get_top_inst()` - 机构交易
- `get_margin()` - 融资融券汇总
- `get_margin_detail()` - 融资融券明细
- `get_stk_holdertrade()` - 股东增减持
- `get_moneyflow_cnt()` - 板块资金流

### 2. `src/capital_flow.py`
新增功能：
- `get_market_moneyflow()` - 全市场资金流（缓存）
- `_get_sector_with_market_flow()` - 板块资金流筛选
- 优先使用 Tushare 2000 积分接口

### 3. `evening_analysis.py`
增强功能：
- `analyze_sector_capital_flow()` - 使用全市场资金流
- JSON 导出包含机构/融资数据
- 新增 `market_summary` 统计

### 4. `scheduled_*.sh`
环境变量：
```bash
export TUSHARE_TOKEN="0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2"
```

---

## 🧪 测试命令

```bash
cd /home/admin/.openclaw/workspace/stock-agent
export TUSHARE_TOKEN="0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2"

# 测试全市场资金流
./venv311/bin/python -c "
import sys; sys.path.insert(0, 'src')
from capital_flow import CapitalFlowAnalyzer
a = CapitalFlowAnalyzer()
mf = a.get_market_moneyflow()
print(f'获取到 {len(mf)} 只股票')
"

# 测试晚间分析
./venv311/bin/python evening_analysis.py
```

---

## 📈 数据展示

### Web 端展示（dashboard.html）
- 板块资金流 TOP10（含机构/融资）
- 龙虎榜股票列表
- 机构交易活跃股票
- 融资净买入 TOP10

### QQ 推送
```
📈 晚间市场总结 - 2026-03-23

资金流 TOP3:
1. 半导体：+5000 万 (机构 +2000 万)
2. 人工智能：+3000 万
3. 新能源：+1500 万

龙虎榜：
- 深华发 A：+500 万 (振幅 15%)
- 韶能股份：+300 万 (换手 20%)
```

---

## ⚠️ 注意事项

1. **数据更新时间**
   - 资金流：19:00
   - 龙虎榜：20:00
   - 融资融券：09:00
   - 晚间分析：20:00（确保数据已更新）

2. **缓存策略**
   - 全市场资金流：按交易日缓存
   - 同一交易日不重复获取
   - 缓存目录：`data/cache/tushare_pro`

3. **API 限流**
   - 2000 积分：每分钟 100 次
   - 已实现缓存减少调用
   - 失败自动回退到其他数据源

---

*最后更新：2026-03-23 22:15*
