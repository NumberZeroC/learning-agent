# Stock-Agent 配置说明

## 🔑 重要配置

### Tushare Token
- **Token**: `0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2`
- **积分**: 600 分 (VIP)
- **状态**: ✅ 已连接
- **可用接口**: 日线行情、指数行情、财务数据等基础接口
- **限制**: 资金流接口 (moneyflow) 需要更高权限

### 资金流数据源状态

| 数据源 | 状态 | 说明 |
|--------|------|------|
| Tushare Pro | ⚠️ 部分可用 | 600 积分，资金流接口无权限 |
| AKShare | ❌ 失败 | 连接被远程断开 |
| 东方财富 | ❌ 失败 | 连接被远程断开 |
| 腾讯财经 | ⚠️ 有限 | 只提供行情，无资金流 |
| 本地列表 | ✅ 回退 | 无实时数据 |

### 当前解决方案

由于所有资金流 API 都不可用，系统目前**回退到本地成分股列表**，导致资金流数据为 0。

**建议方案：**

1. **升级 Tushare 积分** (推荐)
   - 资金流接口需要 1000+ 积分
   - 可通过签到、贡献、充值获得
   - 官网：https://tushare.pro

2. **修复网络连接**
   - 检查服务器到东方财富/AKShare 的网络
   - 可能是防火墙或 IP 限流

3. **使用替代数据源**
   - 考虑其他免费 API（如同花顺、百度财经）

## 📁 配置文件

- `config.yaml` - 主配置文件
- `scheduled_*.sh` - 定时任务脚本（已设置 TUSHARE_TOKEN 环境变量）

## 🔧 环境变量

```bash
export TUSHARE_TOKEN="0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2"
```

## 📊 测试命令

```bash
# 测试 Tushare 连接
cd /home/admin/.openclaw/workspace/stock-agent
export TUSHARE_TOKEN="0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2"
./venv311/bin/python -c "
import sys
sys.path.insert(0, 'src')
from tushare_pro_source import TushareProSource
pro = TushareProSource()
print(f'积分：{pro.token_info[\"total_points\"]}')
"
```

---
*最后更新：2026-03-23 21:57*
