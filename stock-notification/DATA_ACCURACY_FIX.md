# 📊 数据准确性修复

## 问题诊断

用户反馈：**大盘指数数据不准确**

### 根本原因

1. **AKShare 指数数据缺少涨跌幅字段**
   - `stock_zh_index_daily` 返回的列只有：`['date', 'open', 'high', 'low', 'close', 'volume']`
   - 没有 `change` 和 `change_pct` 字段
   - 原有代码直接使用可能导致数据错误或异常

2. **单一数据源风险**
   - 依赖单一数据源（AKShare 或 Tushare）
   - 数据源故障时没有备份方案
   - 无法验证数据准确性

3. **数据未固定保存**
   - 报告生成后，原始数据未保存
   - 后续查看时数据可能已变化
   - 无法追溯历史数据的准确性

---

## 解决方案

### 1. 新增可靠数据源模块 (`src/reliable_data_source.py`)

**特性：**
- ✅ **多数据源备份**：AKShare → Tushare → 新浪财经 API
- ✅ **数据验证**：范围检查、时间戳检查、合理性验证
- ✅ **数据快照**：报告生成时保存原始数据到 JSON
- ✅ **详细日志**：记录每个数据源的获取情况

**支持的数据类型：**
| 数据类型 | 数据源优先级 | 验证规则 |
|---------|------------|---------|
| 大盘指数 | AKShare → Tushare → Sina | 涨跌幅 -12%~+12% |
| 个股股价 | AKShare → Tushare → Sina | 价格 0.01~10000，涨跌幅 -22%~+22% |
| 资金流 | Tushare → AKShare | 净流入合理性检查 |

**主要指数代码：**
```python
indices = {
    'shanghai': {'code': 'sh000001', 'name': '上证指数'},
    'shenzhen': {'code': 'sz399001', 'name': '深证成指'},
    'chinext': {'code': 'sz399006', 'name': '创业板指'},
    'hs300': {'code': 'sh000300', 'name': '沪深 300'},
    'zheng50': {'code': 'sh000016', 'name': '上证 50'}
}
```

---

### 2. 修改晚间分析 (`evening_analysis.py`)

**变更内容：**

```python
# 新增：可靠数据源初始化
self.reliable_data = ReliableDataSource(
    cache_dir=akshare_config.get('cache_dir'),
    cache_ttl=300,
    tushare_token=tushare_config.get('token')
)

# 修改：大盘数据获取优先使用可靠数据源
if self.reliable_data:
    indices_data = self.reliable_data.get_index_data()
    if indices_data:
        market_data['indices'] = indices_data

# 新增：保存数据快照
self.reliable_data.save_data_snapshot('evening', snapshot_data, str(output_dir))
```

---

### 3. 数据快照文件

**文件格式：**
```
data/reports/evening_data_snapshot_2026-03-22_200015.json
```

**内容结构：**
```json
{
  "report_type": "evening",
  "generated_at": "2026-03-22T20:00:15",
  "trade_date": "2026-03-22",
  "data": {
    "market_indices": {
      "shanghai": {
        "name": "上证指数",
        "close": 3957.05,
        "change_pct": -1.23,
        "open": 4004.57,
        "high": 4022.70,
        "low": 3955.71,
        "volume": 66679838700
      }
    },
    "sector_flows": [...],
    "sector_sentiment": {...}
  },
  "data_sources": {
    "akshare": true,
    "tushare": true,
    "requests": true
  },
  "log": [
    {
      "timestamp": "2026-03-22T20:00:10",
      "type": "index_data",
      "data": {...}
    }
  ]
}
```

---

## 测试验证

### 1. 测试可靠数据源

```bash
cd /home/admin/.openclaw/workspace/stock-agent
./venv311/bin/python src/reliable_data_source.py
```

**预期输出：**
```
============================================================
测试可靠数据源
============================================================
[可靠数据源] ✅ 已初始化
   缓存目录：.../data/cache/reliable
   AKShare: ✅
   Tushare: ✅
   Requests: ✅

1. 获取大盘指数...
📊 获取大盘指数数据 (2026-03-22)...
   ✅ 上证指数：3957.05 (-1.23%) [AKShare]
   ✅ 深证成指：12345.67 (+0.45%) [AKShare]
   ✅ 创业板指：2345.67 (+0.78%) [AKShare]
   ✅ 沪深 300: 3456.78 (-0.89%) [AKShare]
   ✅ 上证 50: 2567.89 (-1.01%) [AKShare]
   ✅ 成功获取 5 个指数数据

2. 获取个股数据 (平安银行)...
   📈 获取 000001 数据...
      ✅ 平安银行：¥12.34 (+1.23%) [AKShare]

3. 获取资金流 (平安银行)...
   💰 获取 000001 资金流...
      ✅ 主力净流入：1234.5 万 [Tushare]

4. 保存数据快照...
📸 数据快照已保存：.../evening_data_snapshot_2026-03-22_200015.json
   ✅ 快照：.../evening_data_snapshot_2026-03-22_200015.json

============================================================
测试完成
============================================================
```

### 2. 运行晚间分析

```bash
./venv311/bin/python evening_analysis.py
```

**检查点：**
- [ ] 大盘指数数据准确（与新浪财经/东方财富对比）
- [ ] 涨跌幅计算正确
- [ ] 数据快照文件生成
- [ ] 日志中包含数据来源信息

### 3. 验证数据快照

```bash
cat data/reports/evening_data_snapshot_2026-03-22_*.json | jq '.data.market_indices'
```

---

## 数据准确性保障

### 1. 多数据源交叉验证

```
数据获取流程：
1. 尝试 AKShare（免费、开源）
   ↓ 失败或数据异常
2. 尝试 Tushare Pro（付费、准确）
   ↓ 失败或数据异常
3. 尝试新浪财经 API（实时、备份）
   ↓ 全部失败
4. 返回空数据并记录日志
```

### 2. 数据验证规则

| 数据类型 | 验证项 | 合理范围 |
|---------|-------|---------|
| 指数收盘价 | 价格 > 0 | 100 ~ 50000 |
| 指数涨跌幅 | 绝对值 | < 12% |
| 个股价格 | 价格 | 0.01 ~ 10000 |
| 个股涨跌幅 | 绝对值 | < 22%（含创业板/科创板） |
| 成交量 | 非负 | >= 0 |
| 资金流 | 合理性 | 与成交额匹配 |

### 3. 数据追溯

每个报告生成时保存：
- ✅ 原始数据快照（JSON）
- ✅ 数据获取日志（包含时间戳、数据源）
- ✅ 数据源状态（AKShare/Tushare/Requests 可用性）

---

## 后续改进

### 短期（已完成）
- [x] 新增可靠数据源模块
- [x] 修改晚间分析使用可靠数据源
- [x] 保存数据快照
- [x] 添加数据验证

### 中期（待办）
- [ ] 修改早盘推荐使用可靠数据源
- [ ] 修改监控报告使用可靠数据源
- [ ] 添加数据质量监控告警
- [ ] 历史数据对比分析

### 长期（规划）
- [ ] 本地数据库持久化（SQLite）
- [ ] 数据源自动切换策略优化
- [ ] 数据异常自动告警
- [ ] 数据准确性统计报表

---

## 文件清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `src/reliable_data_source.py` | 可靠数据源模块 | ✅ 新增 |
| `evening_analysis.py` | 晚间分析（修改） | ✅ 已修改 |
| `DATA_ACCURACY_FIX.md` | 修复文档 | ✅ 新增 |
| `data/reports/*_data_snapshot_*.json` | 数据快照 | ✅ 自动生成 |

---

## 使用说明

### 运行晚间分析（自动使用可靠数据源）

```bash
cd /home/admin/.openclaw/workspace/stock-agent
./venv311/bin/python evening_analysis.py
```

### 查看数据快照

```bash
# 查看最新快照
ls -lt data/reports/*data_snapshot*.json | head -1 | xargs cat | jq

# 查看大盘指数数据
ls -lt data/reports/*data_snapshot*.json | head -1 | xargs cat | jq '.data.market_indices'
```

### 测试数据源

```bash
./venv311/bin/python src/reliable_data_source.py
```

---

*修复日期：2026-03-22*
*版本：v1.0*
