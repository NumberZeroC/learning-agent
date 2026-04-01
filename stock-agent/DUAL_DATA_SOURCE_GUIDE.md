# 📊 Stock-Agent 双数据源配置指南

**Tushare Pro (主) + AKShare (备用)**  
**更新时间：** 2026-03-27

---

## 🎯 数据源架构

```
┌─────────────────────────────────────────────────────────────┐
│                    双数据源架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │   Tushare Pro   │         │    AKShare      │           │
│  │   (主数据源)    │         │   (备用数据源)  │           │
│  │   2000 积分      │         │   免费开源      │           │
│  └────────┬────────┘         └────────┬────────┘           │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
│                       │                                     │
│              ┌────────▼────────┐                           │
│              │  故障切换层     │                           │
│              │  Failover Layer │                           │
│              └────────┬────────┘                           │
│                       │                                     │
│              ┌────────▼────────┐                           │
│              │   统一接口     │                           │
│              │  get_price()   │                           │
│              └─────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 数据源对比

| 特性 | Tushare Pro | AKShare |
|------|-------------|---------|
| **类型** | 专业财经数据 API | 开源财经数据接口 |
| **费用** | 积分制 (2000 分) | 完全免费 |
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **数据质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **覆盖范围** | A 股/港股/美股/期货 | A 股为主 |
| **实时性** | 15 分钟延迟 | 实时 |
| **需要 Token** | ✅ | ❌ |
| **缓存支持** | ✅ | ✅ |
| **重试机制** | ✅ | ✅ |

---

## 🔧 配置说明

### config.yaml

```yaml
# ============================================
# 数据源配置
# ============================================

# Tushare Pro (主数据源)
tushare:
  enabled: true
  token: "your_token_here"  # 替换为你的 Token
  priority: 1  # 第一优先级
  cache:
    enabled: true
    ttl_seconds: 600  # 10 分钟缓存

# AKShare (备用数据源)
akshare:
  enabled: true
  priority: 2  # 第二优先级（Tushare 故障时切换）
  cache_dir: "./data/cache/akshare"
  cache_ttl: 300  # 5 分钟缓存
  max_retries: 3  # 失败重试次数
```

---

## 💻 代码使用

### 1. 基础用法

```python
from stock_agent import TushareSource, AKShareSource

# 初始化数据源
ts = TushareSource(token="your_token", cache_ttl=600)
ak = AKShareSource(cache_ttl=300, max_retries=3)

# 获取日线行情
ts_data = ts.get_daily('600519.SH')
ak_data = ak.get_daily_quote('600519.SH')
```

---

### 2. 故障切换模式

```python
def get_price_with_failover(ts_code: str):
    """
    带故障切换的价格获取
    优先级：Tushare > AKShare
    """
    # 1. 优先使用 Tushare
    if ts:
        try:
            data = ts.get_daily(ts_code)
            if data:
                return data
        except Exception as e:
            print(f"Tushare 失败：{e}")
    
    # 2. Tushare 失败，切换 AKShare
    if ak:
        try:
            data = ak.get_daily_quote(ts_code)
            if data:
                return data
        except Exception as e:
            print(f"AKShare 失败：{e}")
    
    # 3. 都失败
    return None

# 使用
price_data = get_price_with_failover('600519.SH')
if price_data:
    print(f"价格：{price_data['close']}元")
else:
    print("无法获取价格数据")
```

---

### 3. 批量获取（带故障切换）

```python
def get_batch_prices(ts_codes: list):
    """批量获取价格，自动故障切换"""
    results = {}
    
    for ts_code in ts_codes:
        # 先尝试 Tushare
        data = ts.get_daily(ts_code) if ts else None
        
        # Tushare 失败则用 AKShare
        if not data and ak:
            data = ak.get_daily_quote(ts_code)
        
        if data:
            results[ts_code] = data
    
    return results

# 使用
codes = ['600519.SH', '000858.SZ', '300750.SZ']
prices = get_batch_prices(codes)

for code, data in prices.items():
    print(f"{code}: {data['close']:.2f}元 ({data['pct_chg']:+.2f}%)")
```

---

## 📊 数据源接口对比

### 基础行情

| 功能 | Tushare 方法 | AKShare 方法 |
|------|-------------|-------------|
| 股票列表 | `get_stock_basic()` | `get_stock_list()` |
| 日线行情 | `get_daily()` | `get_daily_quote()` |
| 批量日线 | `get_daily_batch()` | 循环调用 |
| 实时行情 | ❌ | `get_realtime_quote()` |
| 复权因子 | `get_adj_factor()` | ❌ |

### 资金流

| 功能 | Tushare 方法 | AKShare 方法 |
|------|-------------|-------------|
| 个股资金流 | `get_moneyflow()` | `get_moneyflow()` |
| 北向资金 | `get_north_flow()` | ❌ |
| 龙虎榜 | `get_top_list()` | ❌ |
| 融资融券 | `get_margin()` | ❌ |

### 板块数据

| 功能 | Tushare 方法 | AKShare 方法 |
|------|-------------|-------------|
| 概念板块 | `get_concept_list()` | `get_sector_concepts()` |
| 板块成分 | `get_concept_detail()` | `get_sector_stocks()` |
| 行业板块 | `get_industry_list()` | ❌ |

### 财务数据

| 功能 | Tushare 方法 | AKShare 方法 |
|------|-------------|-------------|
| 财务指标 | `get_fina_indicator()` | ❌ |
| 估值指标 | `get_daily_basic()` | ❌ |
| 业绩预告 | `get_forecast()` | ❌ |

### 新闻数据

| 功能 | Tushare 方法 | AKShare 方法 |
|------|-------------|-------------|
| 财经新闻 | ❌ | `get_news()` |

---

## 🔄 故障切换策略

### 策略 1：优先级切换

```python
DATA_SOURCE_PRIORITY = ['tushare', 'akshare']

def get_data_with_priority(ts_code: str, func_name: str):
    """按优先级获取数据"""
    for source_name in DATA_SOURCE_PRIORITY:
        if source_name == 'tushare' and ts:
            try:
                func = getattr(ts, func_name)
                data = func(ts_code)
                if data:
                    print(f"使用 Tushare 获取 {ts_code}")
                    return data
            except:
                pass
        
        elif source_name == 'akshare' and ak:
            try:
                func = getattr(ak, func_name)
                data = func(ts_code)
                if data:
                    print(f"使用 AKShare 获取 {ts_code}")
                    return data
            except:
                pass
    
    return None
```

---

### 策略 2：数据校验

```python
def get_and_validate(ts_code: str):
    """获取并校验双数据源数据"""
    ts_data = ts.get_daily(ts_code) if ts else None
    ak_data = ak.get_daily_quote(ts_code) if ak else None
    
    if ts_data and ak_data:
        # 双数据源都成功，校验一致性
        price_diff = abs(ts_data['close'] - ak_data['close'])
        if price_diff < 0.1:
            print(f"✅ 数据一致：{ts_data['close']:.2f}元")
            return ts_data  # 优先使用 Tushare
        else:
            print(f"⚠️ 数据差异：{price_diff:.2f}元")
            print(f"   Tushare: {ts_data['close']:.2f}")
            print(f"   AKShare: {ak_data['close']:.2f}")
            return ts_data
    
    elif ts_data:
        print(f"仅 Tushare 成功")
        return ts_data
    
    elif ak_data:
        print(f"仅 AKShare 成功")
        return ak_data
    
    else:
        print(f"❌ 双数据源都失败")
        return None
```

---

### 策略 3：缓存优先

```python
def get_with_cache_priority(ts_code: str):
    """缓存优先，数据源次之"""
    # 1. 先检查 Tushare 缓存
    ts_cached = ts._get_cached('get_daily', ts_code=ts_code, 
                                trade_date=datetime.now().strftime('%Y%m%d'))
    if ts_cached:
        print(f"Tushare 缓存命中")
        return ts_cached
    
    # 2. 检查 AKShare 缓存
    ak_cached = ak.cache.get('get_daily_quote', ts_code=ts_code,
                              trade_date=datetime.now().strftime('%Y%m%d'))
    if ak_cached:
        print(f"AKShare 缓存命中")
        return ak_cached
    
    # 3. 缓存未命中，获取新数据
    return get_price_with_failover(ts_code)
```

---

## 📦 缓存管理

### Tushare 缓存

```python
# 查看缓存统计
stats = ts.get_cache_stats()
print(f"命中率：{stats['hit_rate']}")
print(f"缓存文件：{stats['cache_files']} 个")

# 清理缓存
ts.clear_cache()
```

### AKShare 缓存

```python
# 查看缓存统计
stats = ak.get_cache_stats()
print(f"命中率：{stats['hit_rate']}")
print(f"缓存文件：{stats['cache_files']} 个")

# 清理缓存
ak.clear_cache()
```

---

## 🧪 测试命令

### 测试 Tushare

```bash
cd /home/admin/.openclaw/workspace/stock-agent
python test_tushare_interfaces.py
```

### 测试 AKShare

```bash
python stock_agent/akshare_source.py
```

### 测试双数据源

```bash
python test_dual_source.py
```

---

## ⚠️ 注意事项

### 1. Token 安全

```bash
# 不要将 Token 提交到 Git
echo "TUSHARE_TOKEN=your_token" >> .env
export TUSHARE_TOKEN
```

### 2. AKShare 安装

```bash
# Python 3.8+
pip install akshare

# 如果安装失败，尝试
pip install akshare -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 依赖冲突

AKShare 依赖较多，可能与现有包冲突：

```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install akshare
```

### 4. 数据延迟

| 数据源 | 延迟 |
|--------|------|
| Tushare | 15 分钟 |
| AKShare | 实时（盘中）|

---

## 📋 推荐配置

### 生产环境

```yaml
tushare:
  enabled: true
  token: "your_token"
  priority: 1
  cache_ttl: 600  # 10 分钟

akshare:
  enabled: true
  priority: 2
  cache_ttl: 300  # 5 分钟
  max_retries: 3
```

### 开发环境

```yaml
tushare:
  enabled: false  # 开发时禁用，节省积分

akshare:
  enabled: true
  priority: 1
  cache_ttl: 60  # 1 分钟，快速迭代
```

---

## 🎯 最佳实践

### 1. 数据源选择

```
盘中交易时间 (9:30-15:00):
├── 实时行情 → AKShare (实时)
├── 历史数据 → Tushare (质量高)
└── 财务数据 → Tushare (完整)

盘后分析:
├── 日线数据 → Tushare (主)
├── 资金流 → Tushare (300 分可用)
└── 新闻数据 → AKShare (免费)
```

### 2. 缓存策略

```python
# 高频数据（短线）
cache_ttl = 60  # 1 分钟

# 日线数据（中线）
cache_ttl = 300  # 5 分钟

# 财务数据（长线）
cache_ttl = 3600  # 1 小时
```

### 3. 重试策略

```python
# 网络请求
max_retries = 3
base_delay = 1.0  # 秒
exponential = True  # 指数退避
```

---

## 📊 测试结果 (2026-03-27)

| 测试项 | Tushare | AKShare |
|--------|---------|---------|
| **股票列表** | ✅ 5493 只 | ✅ 待测试 |
| **日线行情** | ✅ 100% | ✅ 待测试 |
| **实时行情** | ❌ | ✅ 待测试 |
| **资金流** | ✅ +5.0 万 | ✅ 待测试 |
| **北向资金** | ✅ +5.3 万 | ❌ |
| **龙虎榜** | ✅ 54 只 | ❌ |
| **财务数据** | ✅ ROE 26.4% | ❌ |
| **概念板块** | ⚠️ 接口需确认 | ✅ 待测试 |
| **新闻数据** | ❌ | ✅ 待测试 |

---

*文档更新时间：2026-03-27 10:35 PM*  
*双数据源配置完成*
