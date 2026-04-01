# 技术指标选股 - 定时任务配置

## 功能说明

自动筛选符合以下技术特征的股票：
- ✅ 日线稳定运行（均线多头排列）
- ✅ 逐渐放量（成交量温和放大）
- ✅ 拉升试盘（小幅上涨 + 量能配合）
- ✅ 即将启动（MACD 金叉 + 突破关键位置）

**输出：** 推荐 10 支股票，通过 QQ 消息推送

---

## 执行时间

- **交易日：** 周一至周五
- **时段：** 9:30-11:30, 13:00-15:00
- **频率：** 每 30 分钟执行一次（00 分、30 分）

---

## 环境说明

本项目使用 Python 3.11 虚拟环境，已预装必要依赖：
- ✅ akshare 1.18.35
- ✅ pandas
- ✅ numpy

**虚拟环境路径：** `/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3`

---

## 配置定时任务

### 方式一：Cron（推荐）

1. 编辑 crontab：
```bash
crontab -e
```

2. 添加以下行（使用虚拟环境 Python）：
```cron
# 技术指标选股 - 交易日每 30 分钟执行
*/30 9-11 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py >> /home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log 2>&1
*/30 13-14 * * 1-5 cd /home/admin/.openclaw/workspace/stock-notification && /home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py >> /home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log 2>&1
```

3. 创建日志目录：
```bash
mkdir -p /home/admin/.openclaw/workspace/stock-notification/logs
```

### 方式二：Systemd Timer

1. 创建服务文件 `/etc/systemd/system/technical-pick.service`：
```ini
[Unit]
Description=Technical Stock Picker
After=network.target

[Service]
Type=oneshot
User=admin
WorkingDirectory=/home/admin/.openclaw/workspace/stock-notification
ExecStart=/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 scheduled_technical_pick.py
StandardOutput=append:/home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log
StandardError=append:/home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log
```

2. 创建定时器文件 `/etc/systemd/system/technical-pick.timer`：
```ini
[Unit]
Description=Run Technical Stock Picker every 30 minutes during trading hours
Requires=technical-pick.service

[Timer]
# 交易日 9:30-11:30, 13:00-15:00 每 30 分钟
OnCalendar=*-*-* 09-11/1:00:00
OnCalendar=*-*-* 13-14/1:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

3. 启用定时器：
```bash
sudo systemctl daemon-reload
sudo systemctl enable technical-pick.timer
sudo systemctl start technical-pick.timer
```

4. 查看状态：
```bash
systemctl list-timers | grep technical-pick
```

---

## 手动执行

```bash
cd /home/admin/.openclaw/workspace/stock-notification
/home/admin/.openclaw/workspace/stock-notification/venv311/bin/python3 technical_analysis.py --limit 10 --min-score 60
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--limit, -l` | 推荐股票数量 | 10 |
| `--min-score, -s` | 最低分数 | 60 |
| `--config, -c` | 配置文件路径 | config.yaml |
| `--qq` | 发送 QQ 消息 | 否 |

---

## 技术指标说明

### 评分体系（满分 100 分）

| 指标 | 权重 | 说明 |
|------|------|------|
| **MACD** | 35 分 | 金叉 20 分 + 零轴上 10 分 + 柱状线放大 5 分 |
| **成交量** | 25 分 | 逐渐放量 15 分 + 量比>1.5 加 10 分 |
| **均线** | 25 分 | 多头排列 15 分 + 价格在均线上方 10 分 |
| **突破** | 20 分 | 突破 20 日高点 10 分 + 突破 60 日高点 10 分 |
| **RSI** | 10 分 | RSI 在 40-70 之间 |
| **涨幅** | 10 分 | 5 日涨幅 0-15%（避免已大幅拉升） |

### 筛选条件

- 价格 > 2 元（避免垃圾股）
- 市值 < 500 亿（避免大盘股）
- 今日涨幅 -3% ~ 7%（避免已涨停或大跌）
- 非 ST 股票

---

## 输出示例

### QQ 消息

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

...

⚠️ 风险提示：技术分析仅供参考，请结合基本面判断，注意设置止损！
```

### 报告文件

- **Markdown:** `/home/admin/.openclaw/workspace/data/stock-notification/technical/technical_pick_YYYY-MM-DD.md`
- **JSON:** `/home/admin/.openclaw/workspace/data/stock-notification/technical/technical_pick_YYYY-MM-DD.json`

---

## 日志查看

```bash
# 查看最新日志
tail -f /home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log

# 查看今日日志
grep $(date +%Y-%m-%d) /home/admin/.openclaw/workspace/stock-notification/logs/technical_pick.log
```

---

## 注意事项

1. **数据源：** 使用 AKShare 免费数据源，无需 API 密钥
2. **性能：** 全市场扫描约需 5-10 分钟（取决于网络）
3. **准确性：** 技术指标仅供参考，请结合基本面判断
4. **风险控制：** 建议设置 5-8% 止损位
5. **周末/节假日：** 自动跳过非交易日

---

## 故障排查

### 问题 1：依赖缺失
```
ModuleNotFoundError: No module named 'akshare'
```
**解决：** `pip install akshare pandas numpy`

### 问题 2：数据获取失败
```
[依赖] ⚠️ 缺少依赖
```
**解决：** 检查网络连接，AKShare 需要访问东方财富网站

### 问题 3：QQ 消息发送失败
```
❌ QQ 消息发送失败
```
**解决：** 检查 OpenClaw QQBot 配置，确保 channel 和 target 正确

### 问题 4：未找到符合条件的股票
```
⚠️ 未找到符合条件的股票
```
**解决：** 降低 `--min-score` 参数（如改为 50），或检查市场整体情况

---

## 优化建议

1. **增加基本面筛选：** 添加 PE、PB、ROE 等指标
2. **板块热点：** 结合板块资金流，优先推荐热点板块个股
3. **龙虎榜：** 整合龙虎榜数据，识别机构买入
4. **回测验证：** 对推荐逻辑进行历史回测
5. **风险控制：** 增加大盘环境判断，弱势市场降低推荐数量

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `technical_analysis.py` | 核心技术分析模块 |
| `scheduled_technical_pick.py` | 定时执行脚本 |
| `CRON_SETUP.md` | 本文档 |

---

*最后更新：2026-03-27*
