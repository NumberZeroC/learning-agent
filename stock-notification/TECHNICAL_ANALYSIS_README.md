# 📊 技术指标选股功能 - 使用说明

## 功能概述

自动筛选符合以下技术特征的股票，寻找**即将启动拉升**的标的：

| 特征 | 说明 | 权重 |
|------|------|------|
| 📈 **日线稳定** | 均线多头排列（5>10>20>30>60） | 25 分 |
| 💰 **逐渐放量** | 成交量温和放大，量比>1.5 | 25 分 |
|  **拉升试盘** | 小幅上涨（5 日 0-15%）+ 量能配合 | 10 分 |
| ⚡ **即将启动** | MACD 金叉 + 突破关键位置 | 35 分 |
| 📊 **RSI 适中** | RSI 在 40-70 之间（非超买超卖） | 5 分 |

**输出：** 推荐 10 支股票，通过 QQ 消息推送

---

## 快速开始

### 1. 手动执行一次

```bash
/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 /home/admin/.openclaw/workspace/stock-notification/technical_analysis.py --limit 10
```

### 2. 设置定时任务（开盘时间每 30 分钟）

```bash
crontab -e
```

添加以下行：

```cron
# 技术指标选股 - 交易日每 30 分钟执行
*/30 9-11 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py >> /home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log 2>&1
*/30 13-14 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py >> /home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log 2>&1
```

### 3. 查看日志

```bash
tail -f /home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log
```

---

## QQ 消息示例

```
📊 技术选股推送 (03-27 09:30)

🔍 筛选条件：日线稳定 + 逐渐放量 + MACD 金叉 + 突破形态

🏆 推荐 TOP10

1. **中芯国际** (688981)
   价格：¥52.30 (+2.5%) | 得分：85 分
   信号：MACD 金叉、逐渐放量

2. **北方华创** (002371)
   价格：¥285.60 (+1.8%) | 得分：82 分
   信号：均线多头、突破 20 日高点

3. **韦尔股份** (603501)
   价格：¥98.50 (+1.2%) | 得分：78 分
   信号：成交量放大、稳步上涨

...（共 10 只）

⚠️ 风险提示：技术分析仅供参考，请结合基本面判断，注意设置止损！
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `technical_analysis.py` | 核心技术分析模块 |
| `scheduled_technical_pick.py` | 定时执行脚本（含交易时间判断） |
| `CRON_SETUP.md` | 详细配置文档 |
| `test_technical.sh` | 测试脚本 |
| `TECHNICAL_ANALYSIS_README.md` | 本文档 |

---

## 报告输出

### Markdown 报告
`/home/admin/.openclaw/workspace/data/stock-notification/technical/technical_pick_YYYY-MM-DD.md`

### JSON 数据
`/home/admin/.openclaw/workspace/data/stock-notification/technical/technical_pick_YYYY-MM-DD.json`

---

## 执行时间

- **交易日：** 周一至周五（自动跳过周末和节假日）
- **时段：** 
  - 上午：9:30-11:30
  - 下午：13:00-15:00
- **频率：** 每 30 分钟（00 分、30 分）

---

## 筛选条件

### 基础过滤
- ✅ 价格 > 2 元（避免垃圾股）
- ✅ 市值 < 500 亿（避免大盘股）
- ✅ 今日涨幅 -3% ~ 7%（避免已涨停或大跌）
- ✅ 非 ST 股票

### 技术指标
- ✅ MACD 金叉或零轴上方
- ✅ 成交量逐渐放大
- ✅ 均线多头排列
- ✅ 突破 20 日/60 日高点
- ✅ RSI 在 40-70 之间
- ✅ 5 日涨幅 0-15%（避免已大幅拉升）

---

## 注意事项

1. **数据源：** 使用 AKShare 免费数据（东方财富）
2. **性能：** 全市场扫描约需 5-10 分钟
3. **准确性：** 技术指标仅供参考，请结合基本面判断
4. **风险控制：** 建议设置 5-8% 止损位
5. **QQ 推送：** 需要配置 OpenClaw QQBot

---

## 故障排查

### 问题 1：依赖缺失
```
ModuleNotFoundError: No module named 'akshare'
```
**解决：** 使用虚拟环境 Python：`venv311/bin/python3`

### 问题 2：数据获取失败
```
[依赖] ⚠️ 缺少依赖
```
**解决：** 检查网络连接，AKShare 需要访问东方财富网站

### 问题 3：未找到符合条件的股票
```
⚠️ 未找到符合条件的股票
```
**解决：** 
- 降低 `--min-score` 参数（如改为 50）
- 检查市场整体情况（弱势市场可能确实没有符合条件的）

---

## 测试运行

```bash
# 运行测试脚本
/home/admin/.openclaw/workspace/stock-notification/test_technical.sh

# 或手动测试单只股票
/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 -c "
from technical_analysis import TechnicalAnalyzer
analyzer = TechnicalAnalyzer()
result = analyzer.analyze_stock('000001', '平安银行')
print(f'得分：{result[\"score\"]}')
print(f'信号：{result[\"signals\"]}')
"
```

---

*创建时间：2026-03-27*  
*版本：1.0*
