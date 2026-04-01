# 📊 Stock-Agent 实时数据获取方案

**更新时间：** 2026-03-27

---

## 🎯 方案对比

| 方案 | 实时性 | 稳定性 | 成本 | 推荐度 |
|------|--------|--------|------|--------|
| Tushare 日线 | ⭐⭐ | ⭐⭐⭐⭐⭐ | 免费/积分 | ⭐⭐⭐⭐ |
| Tushare 实时 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 600 积分 | ⭐⭐⭐⭐ |
| AKShare | ⭐⭐⭐⭐ | ⭐⭐⭐ | 免费 | ⭐⭐⭐⭐ |
| 东方财富 API | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 免费 | ⭐⭐⭐⭐⭐ |
| 新浪财经 API | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 免费 | ⭐⭐⭐⭐ |
| 腾讯财经 API | ⭐⭐⭐⭐ | ⭐⭐⭐ | 免费 | ⭐⭐⭐ |

---

## 📋 方案详解

### 方案 1：Tushare Pro 日线数据（当前使用）

**特点：**
- **更新频率：** 每日收盘后更新（15:30+）
- **数据质量：** ⭐⭐⭐⭐⭐ 高质量
- **稳定性：** ⭐⭐⭐⭐⭐ 非常稳定
- **成本：** 基础接口免费，高级接口需积分

**优点：**
- 数据准确可靠
- 接口稳定
- 有缓存机制
- 适合盘后分析

**缺点：**
- 盘中无实时数据
- 高级接口需要积分

**适用场景：**
- 盘后分析
- 日线级别策略
- 中长期投资

**代码示例：**
```python
from stock_agent import TushareSource

ts = TushareSource(token="your_token")

# 获取日线（收盘后）
daily = ts.get_daily('600519.SH', '20260327')

# 自动回退到昨日数据
prices = monitor.update_prices()
```

---

### 方案 2：Tushare 实时行情

**特点：**
- **更新频率：** 3 秒延迟
- **数据质量：** ⭐⭐⭐⭐⭐
- **稳定性：** ⭐⭐⭐⭐
- **成本：** 600 积分/年

**接口：**
```python
# 实时行情
df = pro.stk_factor(ts_code='600519.SH')

# 分时行情
df = pro.tick(ts_code='600519.SH', trade_date='20260327')
```

**优点：**
- 数据准确
- 延迟低（3 秒）
- 与日线数据同源

**缺点：**
- 需要 600 积分
- 有调用频率限制

**适用场景：**
- 盘中交易
- 短线策略
- 实时监控

---

### 方案 3：AKShare（开源免费）

**特点：**
- **更新频率：** 实时
- **数据质量：** ⭐⭐⭐⭐
- **稳定性：** ⭐⭐⭐
- **成本：** 完全免费

**接口：**
```python
import akshare as ak

# A 股实时行情
df = ak.stock_zh_a_spot_em()

# 个股实时行情
df = ak.stock_zh_a_hist(symbol="600519", period="daily")

# 实时成交
df = ak.stock_zh_a_tick_tx(symbol="600519")
```

**优点：**
- 完全免费
- 数据源丰富
- 开源可定制

**缺点：**
- 网络不稳定时可能失败
- 依赖东方财富等网站
- 无官方支持

**适用场景：**
- 预算有限
- 需要多种数据源
- 可以接受偶尔失败

**安装：**
```bash
pip install akshare
```

---

### 方案 4：东方财富 API（推荐⭐）

**特点：**
- **更新频率：** 实时（3 秒）
- **数据质量：** ⭐⭐⭐⭐⭐
- **稳定性：** ⭐⭐⭐⭐
- **成本：** 免费

**接口：**
```python
import requests

# 实时行情
url = "https://push2.eastmoney.com/api/qt/clist/get"
params = {
    "pn": "1",
    "pz": "500",
    "fs": "m:0+t:6,m:0+t:80,m:1+t:2",  # 沪深 A 股
    "fields": "f12,f13,f14,f43,f44,f45,f46"
}
resp = requests.get(url, params=params)
data = resp.json()

# 解析
for item in data['data']['diff']:
    code = item['f12']      # 代码
    name = item['f14']      # 名称
    price = item['f43']     # 最新价
    change = item['f146']   # 涨跌幅
```

**优点：**
- 完全免费
- 实时数据（3 秒延迟）
- 数据准确
- 覆盖全市场

**缺点：**
- 非官方 API
- 需要自己解析

**适用场景：**
- 实时交易
- 全市场监控
- 预算有限

---

### 方案 5：新浪财经 API

**特点：**
- **更新频率：** 实时
- **数据质量：** ⭐⭐⭐⭐
- **稳定性：** ⭐⭐⭐⭐
- **成本：** 免费

**接口：**
```python
import requests

# 获取实时行情
url = "https://hq.sinajs.cn/list=sh600519"
resp = requests.get(url)
# 返回：var hq_str_sh600519="贵州茅台，1800.00,1800.00,..."

# 解析
data = resp.text.split('"')[1].split(',')
name = data[0]
open_price = float(data[1])
close = float(data[3])
current = float(data[8])  # 当前价
```

**批量获取：**
```python
# 一次获取多只股票
codes = ["sh600519", "sz000858", "sz300750"]
url = f"https://hq.sinajs.cn/list={','.join(codes)}"
```

**优点：**
- 完全免费
- 实时数据
- 接口简单
- 支持批量

**缺点：**
- 数据格式不标准
- 需要自己解析

**适用场景：**
- 实时行情展示
- 简单监控
- 少量股票

---

### 方案 6：腾讯财经 API

**特点：**
- **更新频率：** 实时
- **数据质量：** ⭐⭐⭐⭐
- **稳定性：** ⭐⭐⭐
- **成本：** 免费

**接口：**
```python
import requests

url = "http://qt.gtimg.cn/q=sh600519,sz000858"
resp = requests.get(url)
# 返回：v_sh600519="51~贵州茅台~600519~1800.00~..."
```

**优点：**
- 免费
- 实时
- 支持多只股票

**缺点：**
- 数据格式复杂
- 稳定性一般

---

## 🔧 实现方案

### 方案 A：多数据源故障转移（推荐）

```python
class DataFetcher:
    """多数据源智能获取"""
    
    def __init__(self):
        self.sources = [
            'eastmoney',  # 东方财富（优先）
            'sina',       # 新浪
            'tushare',    # Tushare（备用）
            'akshare',    # AKShare（最后）
        ]
    
    def get_price(self, code):
        """获取实时价格"""
        for source in self.sources:
            try:
                price = self._fetch_from_source(source, code)
                if price:
                    return price
            except Exception as e:
                print(f"{source} 失败：{e}")
                continue
        
        return None  # 所有数据源都失败
```

**优点：**
- 高可用性
- 自动故障转移
- 数据准确性高

---

### 方案 B：定时轮询 + 缓存

```python
import time
from datetime import datetime

class PriceCache:
    """价格缓存管理器"""
    
    def __init__(self, update_interval=60):
        self.cache = {}
        self.update_interval = update_interval  # 60 秒更新
        self.last_update = {}
    
    def get_price(self, code):
        """获取价格（带缓存）"""
        now = time.time()
        
        # 检查缓存是否过期
        if code in self.cache:
            if now - self.last_update.get(code, 0) < self.update_interval:
                return self.cache[code]
        
        # 更新价格
        price = fetch_realtime_price(code)
        self.cache[code] = price
        self.last_update[code] = now
        
        return price
```

**优点：**
- 减少 API 调用
- 提高响应速度
- 降低失败率

---

### 方案 C：WebSocket 实时推送（高级）

```python
import websocket
import json

class RealtimeWebSocket:
    """WebSocket 实时推送"""
    
    def __init__(self, callback):
        self.callback = callback
        self.ws = None
    
    def connect(self):
        # 连接东方财富 WebSocket
        self.ws = websocket.WebSocketApp(
            "wss://push2.eastmoney.com/",
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever()
    
    def on_message(self, ws, message):
        data = json.loads(message)
        self.callback(data)
    
    def subscribe(self, codes):
        # 订阅股票
        sub_msg = {
            "cmd": "subscribe",
            "codes": codes
        }
        self.ws.send(json.dumps(sub_msg))
```

**优点：**
- 真正的实时推送
- 延迟最低（毫秒级）
- 资源消耗少

**缺点：**
- 实现复杂
- 需要维护连接

---

## 📊 推荐配置

### 配置 1：基础版（免费）

```yaml
data_source:
  primary: eastmoney  # 东方财富
  backup: sina        # 新浪
  fallback: tushare   # Tushare（日线）
  
  update_interval: 60  # 60 秒更新
  cache_enabled: true
  cache_ttl: 60
```

**特点：**
- 完全免费
- 实时数据
- 自动故障转移

---

### 配置 2：专业版（Tushare 600 积分）

```yaml
data_source:
  primary: tushare_realtime  # Tushare 实时
  backup: eastmoney          # 东方财富
  fallback: tushare_daily    # Tushare 日线
  
  update_interval: 10  # 10 秒更新
  cache_enabled: true
  cache_ttl: 10
```

**特点：**
- 数据质量高
- 延迟低（3 秒）
- 稳定可靠

---

### 配置 3：机构版（多数据源）

```yaml
data_source:
  primary: 
    - tushare_realtime
    - eastmoney
  backup:
    - sina
    - wind  # 万得（付费）
  
  update_interval: 5  # 5 秒更新
  cache_enabled: true
  cache_ttl: 5
  
  # WebSocket 推送
  websocket:
    enabled: true
    url: "wss://push2.eastmoney.com/"
```

**特点：**
- 多数据源验证
- 超低延迟
- 最高可靠性

---

## 🧪 测试代码

```python
def test_data_sources():
    """测试各数据源"""
    from datetime import datetime
    
    codes = ['600519', '000858', '300750']
    
    print("="*60)
    print("数据源测试")
    print("="*60)
    
    # 1. Tushare 日线
    print("\n1. Tushare 日线:")
    ts = TushareSource(token="your_token")
    for code in codes:
        ts_code = f"{code}.SH" if code.startswith('6') else f"{code}.SZ"
        daily = ts.get_daily(ts_code)
        if daily:
            print(f"  {code}: ¥{daily['close']:.2f} ({daily['pct_chg']:+.2f}%)")
    
    # 2. 新浪财经
    print("\n2. 新浪财经:")
    import requests
    code_list = ",".join([f"sh{c}" if c.startswith('6') else f"sz{c}" for c in codes])
    resp = requests.get(f"https://hq.sinajs.cn/list={code_list}")
    for line in resp.text.split('\n'):
        if line:
            data = line.split('"')[1].split(',')
            print(f"  {data[0]}: ¥{data[8]} ({data[32]}%)")
    
    # 3. 东方财富
    print("\n3. 东方财富:")
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {"pn": "1", "pz": "500", "fs": "m:0+t:6,m:0+t:80,m:1+t:2"}
    resp = requests.get(url, params=params)
    data = resp.json()
    for item in data['data']['diff']:
        if item['f12'] in codes:
            print(f"  {item['f14']}: ¥{item['f43']} ({item['f146']}%)")
    
    print("\n" + "="*60)

# 运行测试
test_data_sources()
```

---

## ⚠️ 注意事项

1. **API 限流**
   - 控制请求频率
   - 使用缓存
   - 避免被封 IP

2. **数据准确性**
   - 多数据源验证
   - 异常值过滤
   - 定期校准

3. **网络稳定性**
   - 添加重试机制
   - 超时设置
   - 故障转移

4. **合规性**
   - 遵守 API 使用条款
   - 不要用于非法用途
   - 注意数据版权

---

## 📝 总结

| 需求 | 推荐方案 |
|------|----------|
| **盘后分析** | Tushare 日线 |
| **实时监控** | 东方财富 API |
| **高可靠性** | Tushare 实时 + 多数据源 |
| **预算有限** | 东方财富 + 新浪 |
| **超低延迟** | WebSocket 推送 |

---

*最后更新：2026-03-27*
