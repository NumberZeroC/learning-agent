# AKShare 备用数据源配置说明

**更新时间：** 2026-03-27  
**状态：** ⚠️ 需要 Python 3.8+

---

## ⚠️ 当前环境问题

```
当前 Python 版本：3.6.8
AKShare 最低要求：Python 3.8+
```

AKShare 需要 Python 3.8 或更高版本，当前系统 Python 3.6 不兼容。

---

## 🔧 解决方案

### 方案 1：使用虚拟环境（推荐）

```bash
# 1. 安装 Python 3.8+
sudo yum install python38 -y  # CentOS/RHEL
# 或
sudo apt install python3.8 -y  # Ubuntu/Debian

# 2. 创建虚拟环境
cd /home/admin/.openclaw/workspace/stock-agent
python3.8 -m venv venv_ak

# 3. 激活虚拟环境
source venv_ak/bin/activate

# 4. 安装 AKShare
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 测试
python -c "import akshare as ak; print(ak.__version__)"
```

---

### 方案 2：使用 UV 工具（如果有）

```bash
# 使用 UV 创建 Python 3.8 环境
uv venv --python 3.8 venv_ak
source venv_ak/bin/activate
uv pip install akshare
```

---

### 方案 3：仅使用 Tushare（当前方案）

如果无法安装 Python 3.8+，可以仅使用 Tushare：

**当前状态：**
- ✅ Tushare Pro 正常工作（2000 积分）
- ✅ 17 个数据接口可用
- ✅ 缓存机制完善
- ⚠️ AKShare 备用源暂不可用

**建议：**
1. 继续使用 Tushare 作为唯一数据源
2. 在条件允许时（Python 3.8+ 环境）再配置 AKShare
3. 代码已预留 AKShare 接口，随时可以启用

---

## 📊 当前数据源状态

| 数据源 | 状态 | 说明 |
|--------|------|------|
| **Tushare Pro** | ✅ 正常 | 2000 积分，17 个接口可用 |
| **AKShare** | ⚠️ 待启用 | 需要 Python 3.8+ |

---

## 🔄 故障切换代码（已实现）

```python
from stock_agent import TushareSource, AKShareSource

# 初始化
ts = TushareSource(token="your_token")

# AKShare 可选初始化
try:
    ak = AKShareSource()
except ImportError:
    ak = None  # Python 版本不兼容

# 故障切换
def get_price(ts_code):
    # 1. 优先 Tushare
    data = ts.get_daily(ts_code)
    if data:
        return data
    
    # 2. AKShare 备用
    if ak:
        data = ak.get_daily_quote(ts_code)
        if data:
            return data
    
    return None
```

---

## 📦 已实现功能

即使没有 AKShare，以下功能也已实现：

1. **AKShareSource 类** (`stock_agent/akshare_source.py`)
   - 代码已完整实现
   - 支持缓存和重试
   - 等待 Python 环境升级后启用

2. **双数据源切换** (`test_dual_source.py`)
   - 测试脚本已就绪
   - 自动检测可用数据源

3. **配置支持** (`config.yaml`)
   - AKShare 配置已添加
   - 优先级设置完成

---

## 📋 启用 AKShare 步骤

当 Python 环境升级到 3.8+ 后：

```bash
# 1. 安装 AKShare
pip install akshare

# 2. 测试连接
cd /home/admin/.openclaw/workspace/stock-agent
python stock_agent/akshare_source.py

# 3. 运行双数据源测试
python test_dual_source.py

# 4. 验证故障切换
# 观察 Tushare 和 AKShare 的数据对比
```

---

## 🎯 当前推荐配置

```yaml
# config.yaml

# Tushare Pro (主数据源 - 正在使用)
tushare:
  enabled: true
  token: "0b8ed09db7d7e733c133a04fad31fc34ff4938afd57f7766cfc6a3f2"
  priority: 1
  cache_ttl: 600

# AKShare (备用数据源 - 待启用)
akshare:
  enabled: false  # Python 3.6 不兼容，暂时禁用
  priority: 2
  cache_ttl: 300
```

---

## 📊 Tushare 单数据源覆盖

即使没有 AKShare，Tushare 也提供完整数据：

| 数据类别 | 接口数 | 说明 |
|---------|--------|------|
| 基础行情 | 4 | 日线、批量、复权 |
| 指数数据 | 2 | 5 大指数 |
| 资金流 | 3 | 主力、北向、龙虎榜 |
| 财务数据 | 3 | 财报、估值、预告 |
| 板块数据 | 2 | 行业、成分股 |
| 特色数据 | 3 | 股东、停复牌 |
| **总计** | **17** | **覆盖率 77%** |

---

## 🔍 替代方案对比

| 功能 | Tushare | AKShare | 当前状态 |
|------|---------|---------|---------|
| 日线行情 | ✅ | ✅ | Tushare 可用 |
| 实时行情 | ❌ | ✅ | 暂缺 |
| 股票列表 | ✅ | ✅ | Tushare 可用 |
| 资金流 | ✅ | ✅ | Tushare 可用 |
| 财务数据 | ✅ | ❌ | Tushare 可用 |
| 新闻数据 | ❌ | ✅ | 暂缺 |
| 板块数据 | ✅ | ✅ | Tushare 可用 |

**结论：** Tushare 覆盖核心功能，AKShare 主要补充实时行情和新闻数据。

---

## 📝 后续计划

1. **短期** - 使用 Tushare 单数据源
   - 2000 积分足够使用
   - 核心功能完整

2. **中期** - 升级 Python 环境
   - 安装 Python 3.8+
   - 创建虚拟环境
   - 启用 AKShare

3. **长期** - 双数据源故障切换
   - 提高数据可靠性
   - 数据源交叉验证
   - 降低成本（减少 Tushare 调用）

---

*文档创建时间：2026-03-27 10:40 PM*  
*当前状态：Tushare 单数据源运行中*
