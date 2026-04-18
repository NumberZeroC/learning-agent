# Learning Agent 问题修复报告

**修复时间：** 2026-04-18  
**问题：** 前端状态不刷新、数据不展示

---

## 🔍 问题分析

### 问题 1：前端状态不会刷新

**原因：** `checkWorkflowStatus()` 只在页面加载时执行一次，没有轮询机制。

**表现：** 
- 工作流在后台运行/完成后，前端状态一直显示"加载学习路线..."
- 需要手动刷新页面才能看到最新状态

### 问题 2：数据没有展示

**原因：** 双层缓存导致数据不更新！

**后端缓存** (`web/routes/workflow_routes.py`)：
```python
_cache = {}
_CACHE_TTL = 14400  # 4 小时缓存

@workflow_bp.route('/layers')
@cached(ttl=_CACHE_TTL)  # ← 缓存 4 小时
def get_all_layers():
```

**前端缓存** (`web/templates/workflow.html`)：
```javascript
const CACHE_TTL = 4 * 60 * 60 * 1000;  // 4 小时缓存
```

**结果：** 即使后台生成了新数据，前后端缓存都会阻止数据更新，最长可达 4 小时！

---

## 🛠️ 修复方案

### 修复 1：添加状态轮询机制

**文件：** `web/templates/workflow.html`

**改动：**
- 添加 `pollWorkflowStatus()` 函数，每 10 秒轮询一次工作流状态
- 工作流运行时启动轮询，完成后停止轮询
- 工作流完成后自动清除前端缓存并重新加载数据
- 添加浏览器通知支持（工作流完成时弹出通知）

```javascript
// 轮询工作流状态（每 10 秒）
let statusPollingInterval = null;

async function pollWorkflowStatus() {
    const response = await fetch('/api/workflow/run/status');
    const result = await response.json();
    
    if (result.success && !result.data.running) {
        // 工作流完成了
        updateWorkflowStatus('idle');
        clearInterval(statusPollingInterval);
        
        // 清除缓存并重新加载数据
        knowledgeTreeCache = null;
        knowledgeTreeCacheTime = 0;
        loadKnowledgeTree();
        
        // 显示完成通知
        if (window.Notification && Notification.permission === 'granted') {
            new Notification('🎉 知识生成完成', {
                body: 'AI Agent 学习路线已生成完毕，点击查看详情',
                icon: '/favicon.ico'
            });
        }
    }
}
```

### 修复 2：添加缓存清除 API

**文件：** `web/routes/workflow_routes.py`

**改动：**
- 添加 `clear_cache()` 函数，支持按模式清除或清除所有缓存
- 添加 `/api/workflow/cache/clear` API（POST），工作流完成后调用
- 添加 `/api/workflow/refresh` API（POST），手动刷新数据

```python
def clear_cache(pattern=None):
    """清除缓存（支持按模式清除）"""
    global _cache
    if pattern:
        keys_to_remove = [k for k in _cache.keys() if pattern in k]
        for k in keys_to_remove:
            del _cache[k]
        return len(keys_to_remove)
    else:
        count = len(_cache)
        _cache = {}
        return count

@workflow_bp.route('/cache/clear', methods=['POST'])
def clear_cache_api():
    """清除数据缓存（工作流完成后调用）"""
    count = clear_cache()
    return jsonify({
        "success": True,
        "message": f"已清除 {count} 条缓存记录"
    })
```

### 修复 3：工作流完成后自动清除缓存

**文件：** `workflow_orchestrator.py`

**改动：**
- 在 `_save_results()` 方法中添加 `_clear_web_cache()` 调用
- 工作流保存结果后，自动调用 Web 服务的清除缓存 API

```python
def _save_results(self, result: WorkflowResult):
    # ... 保存结果 ...
    
    # 清除 Web 前端缓存（通知 Web 服务刷新数据）
    self._clear_web_cache()

def _clear_web_cache(self):
    """清除 Web 前端缓存"""
    try:
        import urllib.request
        import json
        
        web_url = "http://127.0.0.1:5001/api/workflow/cache/clear"
        
        req = urllib.request.Request(
            web_url,
            data=b'',
            method='POST',
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            logger.info(f"🔄 Web 缓存已清除：{result.get('message', '')}")
    except Exception as e:
        logger.warning(f"⚠️ 清除 Web 缓存失败（Web 服务可能未运行）: {e}")
```

### 修复 4：添加手动刷新按钮

**文件：** `web/templates/workflow.html`

**改动：**
- 在侧边栏添加"刷新"按钮
- 添加 `refreshData()` 函数，调用后端刷新 API 并重新加载数据

```html
<!-- 手动刷新按钮 -->
<div style="padding: 10px 20px; border-bottom: 1px solid #e8ecef; background: #fafbfc; display: flex; justify-content: flex-end;">
    <button onclick="refreshData()" style="...">
        <i class="bi bi-arrow-clockwise"></i> 刷新
    </button>
</div>
```

---

## 📋 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `web/templates/workflow.html` | 添加状态轮询、缓存清除、手动刷新按钮、浏览器通知 |
| `web/routes/workflow_routes.py` | 添加 `clear_cache()` 函数、`/cache/clear` 和 `/refresh` API |
| `workflow_orchestrator.py` | 在 `_save_results()` 中添加自动清除缓存调用 |

---

## ✅ 测试步骤

### 测试 1：工作流完成后自动刷新

1. 启动工作流：点击"生成知识"按钮
2. 等待工作流完成（或手动在后台执行 `python workflow_orchestrator.py`）
3. 观察前端：
   - 状态应从"工作流运行中..."变为空闲
   - 数据应自动加载显示
   - 可能收到浏览器通知

### 测试 2：手动刷新

1. 点击侧边栏的"刷新"按钮
2. 观察数据是否重新加载
3. 按钮应显示"刷新中..." → "已刷新"

### 测试 3：状态轮询

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 启动工作流
4. 观察是否每 10 秒发送一次 `/api/workflow/run/status` 请求
5. 工作流完成后，轮询应停止

---

## 🎯 预期效果

修复后：

1. **实时状态更新**：工作流运行/完成状态每 10 秒自动更新
2. **数据自动展示**：工作流完成后，数据自动加载显示（无需刷新页面）
3. **浏览器通知**：工作流完成时弹出通知（需用户授权）
4. **手动刷新**：随时点击"刷新"按钮获取最新数据
5. **缓存自动清理**：工作流完成后自动清除前后端缓存

---

## 📝 注意事项

1. **浏览器通知权限**：首次使用需要用户授权通知权限
2. **Web 服务需运行**：自动清除缓存功能依赖 Web 服务在 5001 端口运行
3. **轮询频率**：默认 10 秒轮询一次，如需调整修改 `setInterval(pollWorkflowStatus, 10000)`
4. **缓存时间**：目前保持 4 小时缓存，如需调整修改 `_CACHE_TTL` 常量

---

## 🔄 后续优化建议

1. **WebSocket 实时推送**：替代轮询，实现真正的实时状态更新
2. **进度条显示**：显示工作流完成百分比（已完成层数/总层数）
3. **日志实时查看**：在工作流运行期间实时显示日志输出
4. **缓存策略优化**：工作流运行期间使用短缓存（5 分钟），空闲时使用长缓存（4 小时）
