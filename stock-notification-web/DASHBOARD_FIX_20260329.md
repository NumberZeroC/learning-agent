# ✅ 数据看板大盘指数修复

**完成时间：** 2026-03-29 19:28  
**问题：** 数据看板大盘指数与主页不一致  
**状态：** ✅ 已修复

---

## 📊 问题描述

### 现象

- **主页（/）**：显示上证指数 3913.72 (+0.63%) ✅
- **数据看板（/dashboard）**：显示上证指数 3813.28 (-3.63%) ❌

### 原因分析

| 页面 | 数据源 | API | 问题 |
|------|--------|-----|------|
| **主页** | `/api/v1/reports/latest-data` | 最新报告数据 | ✅ 正确 |
| **数据看板** | `/api/v1/reports?type=evening` | 晚间报告列表 | ❌ 读取旧报告 |

**数据看板问题代码：**
```javascript
// dashboard.html 第 148 行
const response = await fetch('/api/v1/reports?type=evening&t=' + Date.now());
const result = await response.json();

if (result.code === 200 && result.data.length > 0) {
    const latestReport = result.data[0];
    
    // 🔴 问题：读取报告列表的第一个，可能是旧报告
    const jsonFilename = latestReport.filename.replace('.md', '.json');
    const jsonResponse = await fetch(`/data/reports/${jsonFilename}?t=${Date.now()}`);
}
```

---

## ✅ 修复方案

### 修复代码

```javascript
// 🔥 修复：使用与主页一致的 latest-data API
async function loadMarketOverview() {
    try {
        // ✅ 使用 latest-data API（与主页一致）
        const response = await fetch('/api/v1/reports/latest-data?t=' + Date.now());
        const result = await response.json();
        
        if (result.code === 200 && result.data) {
            const jsonData = result.data;
            updateMarketOverview(jsonData);
        } else {
            // fallback：默认数据
            updateMarketOverview({
                index: { value: 0, change: 0 },
                sentiment: '--',
                sentimentScore: 0
            });
        }
    } catch (error) {
        console.error('加载市场概览失败:', error);
    }
}
```

---

## 📋 修改的文件

| 文件 | 修改内容 |
|------|---------|
| `templates/dashboard.html` | 修改 `loadMarketOverview()` 函数，使用 `latest-data` API |

---

## 🧪 验证结果

### API 数据对比

```bash
# 主页使用的 API
$ curl -s "http://localhost:5000/api/v1/reports/latest-data" | python3 -m json.tool

{
    "code": 200,
    "data": {
        "index": {
            "value": 3913.72,
            "change": 0.63
        },
        "report_date": "2026-03-27"
    }
}
```

### 修复前后对比

| 页面 | 修复前 | 修复后 |
|------|--------|--------|
| **主页** | 3913.72 (+0.63%) ✅ | 3913.72 (+0.63%) ✅ |
| **数据看板** | 3813.28 (-3.63%) ❌ | 3913.72 (+0.63%) ✅ |

---

## 📊 数据流对比

### 修复前

```
数据看板
  ↓
/api/v1/reports?type=evening
  ↓
报告列表 [report1, report2, ...]
  ↓
取第一个报告 report1
  ↓
/data/reports/report1.json
  ↓
可能是旧数据 ❌
```

### 修复后

```
数据看板
  ↓
/api/v1/reports/latest-data  ← 与主页一致 ✅
  ↓
最新报告数据
  ↓
包含指数、板块、龙虎榜
  ↓
数据一致 ✅
```

---

## 🔄 其他页面检查

### 检查所有使用大盘指数的页面

```bash
# 查找所有引用上证指数的文件
grep -rn "上证指数\|indexValue" /home/admin/.openclaw/workspace/stock-notification-web/templates/
```

**结果：**
| 文件 | 数据源 | 状态 |
|------|--------|------|
| `index.html` | `/api/v1/reports/latest-data` | ✅ |
| `dashboard.html` | `/api/v1/reports/latest-data` | ✅ 已修复 |
| `monitor.html` | `/api/v1/monitor/stocks` | ✅ |
| `reports.html` | 无指数显示 | - |

---

## ✅ 总结

### 问题根因

- 数据看板使用了错误的 API（`/api/v1/reports?type=evening`）
- 该 API 返回报告列表，需要额外读取 JSON 文件
- 可能读取到旧报告

### 修复方案

- 统一使用 `/api/v1/reports/latest-data` API
- 与主页保持数据源一致
- 简化代码逻辑

### 验证结果

- ✅ 主页和数据看板指数一致
- ✅ 数据来自最新报告（2026-03-27）
- ✅ 上证指数：3913.72 (+0.63%)

---

*修复完成时间：2026-03-29 19:28*
