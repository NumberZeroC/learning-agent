# 持仓监控页面股价为 0 问题修复报告

**日期：** 2026-03-24  
**问题发现时间：** 19:40  
**修复完成时间：** 19:45  

---

## 🔍 问题描述

持仓监控页面显示的所有股票价格均为 0：

```json
{
  "stocks": [
    {"code": "002181", "name": "粤传媒", "price": 0, "change_pct": 0},
    {"code": "300058", "name": "蓝色光标", "price": 0, "change_pct": 0},
    ...
  ]
}
```

---

## 📊 问题诊断

### 根本原因

`monitor.py` 依赖 `StockMonitor` 类获取股票数据，而 `StockMonitor` 使用 **AKShare** 作为主要数据源。

**问题链路：**
1. `monitor.py` → `StockMonitor.generate_trading_signal()` → AKShare
2. AKShare 连接失败：`Connection aborted. Remote end closed connection without response`
3. 数据获取降级，返回默认值 `{'current_price': 0, 'change_percent': 0}`

### 日志证据

```
[002181] AKShare 失败：('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
[002181] 获取 K 线数据失败：('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
⚠️ 数据暂不可用
```

### 备用数据源正常

虽然 `monitor.py` 中有使用 Tushare 的 `_get_stock_data()` 方法，但由于以下原因未被充分利用：
- `StockMonitor` 优先使用 AKShare
- AKShare 失败后没有回退到 Tushare 获取股价

**Tushare 测试（正常）：**
```python
粤传媒 (002181): ¥11.13 (+6.00%) ✅
蓝色光标 (300058): ¥13.92 (+2.20%) ✅
天龙集团 (300063): ¥11.23 (+4.66%) ✅
```

---

## ✅ 修复方案

### 修改文件

`/home/admin/.openclaw/workspace/stock-agent/monitor.py`

### 修改内容

1. **优化 `_get_stock_data()` 错误处理**
   - 添加异常日志输出，便于排查问题
   - 确保 Tushare 调用失败时有明确的错误信息

2. **改进 `_get_signal()` 错误处理**
   - 添加异常捕获和日志输出
   - 防止 StockMonitor 异常影响整体流程

### 修复后效果

```
📈 粤传媒 (002181)... ¥11.13 (+6.00%) ✅
📈 蓝色光标 (300058)... ¥13.92 (+2.20%) ✅
📈 天龙集团 (300063)... ¥11.23 (+4.66%) ✅
📈 中文在线 (300364)... ¥25.12 (+3.59%) ✅
📈 天下秀 (600556)... ¥5.94 (+4.21%) ✅
📈 塞力斯 (600038)... ¥33.05 (+2.39%) ✅
📈 南京商旅 (600250)... ¥11.76 (+5.47%) ✅
```

---

## 📋 验证结果

### JSON 数据（已修复）

```json
{
  "date": "2026-03-24",
  "update_time": "2026-03-24T19:45:19.079494",
  "stocks": [
    {"code": "002181", "name": "粤传媒", "price": 11.13, "change_pct": 6.0},
    {"code": "300058", "name": "蓝色光标", "price": 13.92, "change_pct": 2.2026},
    {"code": "300063", "name": "天龙集团", "price": 11.23, "change_pct": 4.6598},
    {"code": "300364", "name": "中文在线", "price": 25.12, "change_pct": 3.5876},
    {"code": "600556", "name": "天下秀", "price": 5.94, "change_pct": 4.2105},
    {"code": "600038", "name": "塞力斯", "price": 33.05, "change_pct": 2.3854},
    {"code": "600250", "name": "南京商旅", "price": 11.76, "change_pct": 5.4709}
  ]
}
```

---

## 🔧 后续优化建议

### 1. 数据源优先级调整

建议修改 `StockMonitor` 的数据源优先级：
- **优先使用 Tushare**（稳定，有官方 API）
- AKShare 作为备用（免费但稳定性较差）

### 2. 增加数据源健康检查

在 `StockWatcher.__init__()` 中添加数据源连通性测试：
```python
def _check_data_source_health(self):
    """检查数据源健康状态"""
    # 测试 Tushare
    try:
        self.tushare_pro.query('daily', ts_code='002181.SZ', 
                               start_date='20260324', end_date='20260324')
        print("[Tushare] ✅ 健康")
    except Exception as e:
        print(f"[Tushare] ❌ 异常：{e}")
```

### 3. 添加股价数据验证

在 `_get_stock_data()` 中添加数据有效性检查：
```python
if price <= 0 or np.isnan(price):
    print(f"[数据验证] {code} 股价异常：{price}")
    return {'current_price': 0, 'change_percent': 0}
```

### 4. 监控告警

当连续多次获取数据失败时，发送告警通知。

---

## 📝 经验总结

1. **数据源冗余很重要**：单一数据源故障会导致整个系统失效
2. **降级策略要完善**：AKShare 失败后应自动切换到 Tushare
3. **日志输出要清晰**：便于快速定位问题
4. **定期健康检查**：在系统启动时验证数据源可用性

---

**修复状态：** ✅ 已完成  
**验证状态：** ✅ 已验证  
**文档更新：** ✅ 已完成
