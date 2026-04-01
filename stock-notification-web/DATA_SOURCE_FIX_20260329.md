# 🔧 大盘指数数据源修复报告

**修复时间：** 2026-03-29 14:47  
**问题：** 大盘指数显示不正确  
**状态：** ✅ 已修复

---

## 📊 问题诊断

### 问题现象

用户报告：Web 端大盘指数显示不正确

### 实际数据对比

| 日期 | 上证指数 | 状态 |
|------|---------|------|
| **3 月 27 日（周五）实际收盘** | 3913.72 (+0.63%) | ✅ 正确数据 |
| **Web 端显示（修复前）** | 3889.08 (-1.09%) | ❌ 3 月 26 日旧数据 |
| **Web 端显示（修复后）** | 3913.72 (+0.63%) | ✅ 已修复 |

---

## 🔍 根本原因

### 1. 数据源架构问题

```
stock-notification 数据流:
┌───────────────────┐
│ evening_analysis.py │
└─────────┬─────────┘
          ↓
┌───────────────────┐
│ ReliableDataSource │ ← 多数据源备份
└─────────┬─────────┘
          ↓
    ┌─────┴─────┬──────────┐
    ↓           ↓          ↓
 AKShare    Tushare    新浪财经
 (❌未安装)  (❌未配置)   (✅周末无数据)
```

**问题：**
- stock-notification 的 venv311 环境未安装 AKShare
- Tushare 未配置 token
- 只能依赖新浪财经 API（周末休市无数据）

### 2. 3 月 27 日数据缺失

- 3 月 27 日（周五）晚间报告未生成
- 最新数据停留在 3 月 26 日

### 3. API 文件排序问题

- API 按文件名字母排序查找最新报告
- `evening_summary_2026-03-26.json` 排在 `evening_data_snapshot_2026-03-27_*.json` 前面
- 导致读取到旧数据

---

## 🔧 修复方案

### 修复 1：补生成 3 月 27 日数据

使用 stock-agent 的 venv_ak 环境（已安装 AKShare）生成缺失数据：

```bash
source /home/admin/.openclaw/workspace/stock-agent/venv_ak/bin/activate
python3 generate_missing_data.py
```

**生成文件：**
- `/home/admin/.openclaw/workspace/data/stock-agent/market/20260327.json`
- `/home/admin/.openclaw/workspace/data/stock-agent/reports/evening_data_snapshot_2026-03-27_200000.json`
- `/home/admin/.openclaw/workspace/stock-agent/data/reports/evening_summary_2026-03-27.json`

### 修复 2：修复 API 文件查找逻辑

修改 `/home/admin/.openclaw/workspace/stock-notification-web/api/v1/report_routes.py`：

```python
# 修复前：按字母排序
for filename in sorted(os.listdir(reports_dir), reverse=True):
    if filename.startswith('evening_...'):
        latest_json = filepath
        break

# 修复后：按日期排序
import re
latest_date = None
for filename in os.listdir(reports_dir):
    if filename.startswith('evening_...'):
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if match:
            date_str = match.group(1)
            if latest_date is None or date_str > latest_date:
                latest_date = date_str
                latest_json = filepath
```

---

## ✅ 验证结果

### API 测试

```bash
curl -s "http://localhost:5000/api/v1/reports/latest-data"
```

**返回结果：**
```json
{
    "code": 200,
    "data": {
        "index": {
            "value": 3913.72,
            "change": 0.63
        },
        "report_date": "2026-03-27",
        "sentiment": "偏暖",
        "sentimentScore": 6.0
    }
}
```

### 数据验证

| 指数 | 收盘价 | 涨跌幅 | 状态 |
|------|--------|--------|------|
| **上证指数** | 3913.72 | +0.63% | ✅ |
| **深证成指** | 13760.37 | +1.13% | ✅ |
| **创业板指** | 3295.88 | +0.71% | ✅ |
| **沪深 300** | 4502.57 | +0.56% | ✅ |
| **上证 50** | 2837.31 | +0.45% | ✅ |

---

## 📡 数据源说明

### 当前数据源

**主要数据源：** AKShare（通过 stock-agent 环境）
- 版本：1.18.48
- 环境：`/home/admin/.openclaw/workspace/stock-agent/venv_ak`
- 数据质量：✅ 准确可靠

**备用数据源：**
- Tushare Pro（需配置 token）
- 新浪财经 API（实时但周末无数据）

### 数据更新流程

1. **晚间分析报告** - 每个交易日 20:00 后运行
   ```bash
   cd /home/admin/.openclaw/workspace/stock-notification
   python evening_analysis.py
   ```

2. **数据生成** - 使用 ReliableDataSource
   - 优先 AKShare
   - 失败则尝试 Tushare
   - 最后使用新浪财经

3. **数据存储**
   - 市场数据：`/home/admin/.openclaw/workspace/data/stock-agent/market/YYYYMMDD.json`
   - 报告快照：`/home/admin/.openclaw/workspace/data/stock-agent/reports/evening_data_snapshot_*.json`

4. **Web 端读取** - 自动查找最新日期数据

---

## 📁 修复文件清单

### 修改的文件

1. `/home/admin/.openclaw/workspace/stock-notification-web/api/v1/report_routes.py`
   - 修复报告目录路径
   - 支持两种文件名格式
   - 按日期排序查找最新文件
   - 兼容两种数据结构

2. `/home/admin/.openclaw/workspace/stock-notification/generate_missing_data.py`（新增）
   - 补生成缺失的市场数据

### 生成的数据文件

1. `/home/admin/.openclaw/workspace/data/stock-agent/market/20260327.json`
2. `/home/admin/.openclaw/workspace/data/stock-agent/reports/evening_data_snapshot_2026-03-27_200000.json`
3. `/home/admin/.openclaw/workspace/stock-agent/data/reports/evening_summary_2026-03-27.json`

---

## 🔄 后续优化建议

### 短期（本周）

1. **安装 AKShare 到 stock-notification 环境**
   ```bash
   cd /home/admin/.openclaw/workspace/stock-notification
   source venv311/bin/activate
   pip install akshare
   ```

2. **配置 Tushare Token**
   - 在 config.yaml 中添加 token
   - 作为备用数据源

3. **添加数据更新监控**
   - 监控每日数据生成
   - 失败时发送告警

### 中期（本月）

1. **统一数据源配置**
   - stock-notification 和 stock-notification-web 使用同一数据源
   - 减少数据不一致

2. **添加数据验证**
   - 检查数据完整性
   - 验证数据合理性

3. **自动化数据补全**
   - 检测缺失数据自动补生成
   - 使用 stock-agent 环境作为备份

### 长期（下季度）

1. **数据源健康检查**
   - 定期检查各数据源可用性
   - 自动切换最优数据源

2. **历史数据归档**
   - 定期归档历史数据
   - 优化查询性能

3. **实时数据接口**
   - 交易时段提供实时指数
   - 减少数据延迟

---

## 📞 快速命令

```bash
# 查看最新数据
ls -lt /home/admin/.openclaw/workspace/data/stock-agent/reports/ | head -5

# 测试 API
curl -s "http://localhost:5000/api/v1/reports/latest-data" | python3 -m json.tool

# 重启 Web 服务
pkill -f "python.*app.py"
cd /home/admin/.openclaw/workspace/stock-notification-web
source ../stock-notification/venv311/bin/activate
nohup python3 app.py > logs/web.log 2>&1 &

# 查看日志
tail -f logs/web.log

# 手动生成数据（使用 stock-agent 环境）
source /home/admin/.openclaw/workspace/stock-agent/venv_ak/bin/activate
python3 /home/admin/.openclaw/workspace/stock-notification/generate_missing_data.py
```

---

## ✅ 修复完成

**修复状态：** 已完成  
**验证状态：** 通过  
**数据日期：** 2026-03-27（周五）  
**上证指数：** 3913.72 (+0.63%) ✅

---

*修复完成时间：2026-03-29 14:47*
