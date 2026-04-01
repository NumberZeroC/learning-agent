# ✅ 数据看板大盘指数显示为 0 修复

**完成时间：** 2026-03-29 19:34  
**问题：** 修复后大盘指数显示为 0  
**状态：** ✅ 已修复代码，需重启服务

---

## 🔍 问题分析

### API 返回的数据结构

```json
{
    "code": 200,
    "data": {
        "index": {
            "value": 3913.724,
            "change": 0.63
        },
        "sentiment": "偏暖",
        "sentimentScore": 6.0
    }
}
```

### 前端期望的数据结构（旧）

```javascript
// ❌ 旧代码期望的结构
{
    "market": {
        "indices": {
            "shanghai": {
                "close": 3913.72,
                "change_pct": 0.63
            }
        }
    }
}
```

### 不匹配导致的问题

```javascript
// 旧代码
const market = data.market || data;  // data.market 不存在 → 使用 data
const indices = market.indices || {};  // data.indices 不存在 → {}
const shanghai = indices.shanghai || {};  // {} → {}
const indexValue = shanghai.close || 0;  // undefined → 0  ❌
```

---

## ✅ 修复方案

### 修复代码

```javascript
// ✅ 新代码：适配 latest-data API 的数据结构
function updateMarketOverview(data) {
    let indexValue = 0;
    let indexChange = 0;
    
    // 优先使用 latest-data API 的结构
    if (data.index) {
        indexValue = data.index.value || 0;
        indexChange = data.index.change || 0;
    } else {
        // 兼容旧结构
        const market = data.market || data;
        const indices = market.indices || {};
        const shanghai = indices.shanghai || {};
        indexValue = shanghai.close || 0;
        indexChange = shanghai.change_pct || 0;
    }
    
    // 显示逻辑
    document.getElementById('indexValue').textContent = indexValue > 0 ? indexValue.toFixed(2) : '--';
    
    const trendEl = document.getElementById('indexTrend');
    if (indexValue > 0) {
        const changeClass = indexChange >= 0 ? 'text-danger' : 'text-success';
        const arrow = indexChange >= 0 ? 'bi-arrow-up' : 'bi-arrow-down';
        trendEl.className = changeClass;
        trendEl.innerHTML = `<i class="bi ${arrow}"></i> ${Math.abs(indexChange)}%`;
    } else {
        trendEl.className = 'text-muted';
        trendEl.innerHTML = '休市中';
    }
    
    // 情绪数据
    const sentiment = data.sentiment || '--';
    const sentimentScore = data.sentimentScore || 0;
    document.getElementById('sentimentValue').textContent = sentiment;
    document.getElementById('sentimentScore').textContent = sentimentScore > 0 ? `得分：${sentimentScore}` : '';
}
```

---

## 📋 修改的文件

| 文件 | 修改内容 |
|------|---------|
| `templates/dashboard.html` | 修复 `updateMarketOverview()` 函数 |

---

## 🔄 重启服务

```bash
# 停止旧服务
pkill -9 -f "python.*stock-notification-web.*app.py"

# 启动新服务
cd /home/admin/.openclaw/workspace/stock-notification-web
source ../stock-notification/venv311/bin/activate
nohup python3 app.py > logs/web.log 2>&1 &

# 验证
curl -s "http://localhost:5000/dashboard" > /dev/null && echo "✅ 服务正常"
```

---

## 🧪 验证结果

### 预期显示

```
数据看板
┌────────────────────────┐
│ 上证指数               │
│ 3913.72                │
│ ↑ 0.63%                │
└────────────────────────┘
```

### 数据结构对比

| API | 字段 | 值 |
|-----|------|-----|
| `/api/v1/reports/latest-data` | `data.index.value` | 3913.724 |
| `/api/v1/reports/latest-data` | `data.index.change` | 0.63 |
| `/api/v1/reports/latest-data` | `data.sentiment` | "偏暖" |
| `/api/v1/reports/latest-data` | `data.sentimentScore` | 6.0 |

---

## 📝 修复总结

### 问题根因

1. **第一次修复**：改了 API 调用（从 `reports?type=evening` 改为 `latest-data`）✅
2. **第二次修复**：但没改数据解析逻辑，导致字段不匹配 ❌
3. **最终修复**：同时修改 API 调用和数据解析逻辑 ✅

### 经验教训

- ✅ API 变更后，前端数据结构也要同步更新
- ✅ 添加数据结构兼容性检查
- ✅ 生产环境需要重启服务才能加载新模板

---

*修复完成时间：2026-03-29 19:34*
