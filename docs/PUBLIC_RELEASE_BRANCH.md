# 🌐 public-release 分支 - 对外公开知识展示

**分支定位：** 对外公开发布的生产分支  
**创建日期：** 2026-04-18  
**基础：** main 分支完整 Web 功能  
**模式：** 只读展示（隐藏后台管理）

---

## 🎯 功能定位

### ✅ 保留功能（对外展示）

- ✅ **知识架构展示** - 5 层知识体系可视化
- ✅ **知识点详情** - 完整的学习内容
- ✅ **Web 聊天问答** - AI 知识问答助手
- ✅ **层级导航** - 侧边栏层级切换
- ✅ **搜索功能** - 知识点搜索

### ❌ 隐藏功能（仅内部使用）

- ❌ **工作流执行按钮** - 隐藏"生成知识"按钮
- ❌ **配置管理页面** - `/config` 返回 403
- ❌ **API Key 配置** - 不暴露配置界面
- ❌ **后台管理** - 隐藏管理功能

---

## 🔧 配置方式

### 环境变量控制

```bash
# .env 文件
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true
```

### 启动脚本

```bash
# 公开模式启动
./web/start_public_release.sh --port 32015
```

---

## 📁 代码变更

### 1. web/app.py

```python
# 公开模式配置
PUBLIC_MODE = os.getenv('PUBLIC_MODE', 'false').lower() == 'true'
HIDE_CONFIG_PAGE = os.getenv('HIDE_CONFIG_PAGE', 'false').lower() == 'true'

# 隐藏配置页面
if not HIDE_CONFIG_PAGE:
    app.register_blueprint(config_bp)
else:
    @app.route("/config")
    def config_disabled():
        return jsonify({"error": "此功能在公开模式下已禁用"}), 403

# 传递 public_mode 到模板
@app.route("/")
def index():
    return render_template("workflow.html", public_mode=PUBLIC_MODE)
```

### 2. web/templates/workflow.html

```html
<!-- 隐藏工作流执行按钮 -->
{% if not public_mode %}
<div class="workflow-control">
    <button class="btn-run" onclick="showRunConfirm()" id="runWorkflowBtn">
        <i class="bi bi-play-fill"></i> 生成知识
    </button>
</div>
{% endif %}

<!-- 隐藏配置管理菜单 -->
{% if not public_mode %}
<a class="nav-link" href="/config"><i class="bi bi-gear"></i> 配置管理</a>
{% endif %}
```

---

## 🚀 部署步骤

### 1. 切换到 public-release 分支

```bash
git checkout public-release
git merge main  # 同步最新代码
```

### 2. 配置环境变量

```bash
cat >> .env << EOF

# 公开模式配置
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true
EOF
```

### 3. 启动服务

```bash
# 使用公开模式启动
./web/start_public_release.sh --port 32015
```

### 4. 配置 Nginx（可选增强）

```nginx
# 在 nginx/conf.d/learning-agent.conf 中添加

# 隐藏配置页面
location /config {
    return 403;
}

# 隐藏工作流执行 API
location ~ ^/api/workflow/(execute|start|stop) {
    return 403;
}
```

---

## 🧪 测试清单

### 功能测试

- [ ] 主页正常显示知识架构
- [ ] 层级导航正常工作
- [ ] 知识点详情正常显示
- [ ] 聊天功能正常
- [ ] 搜索功能正常

### 安全测试

- [ ] `/config` 返回 403
- [ ] 工作流执行按钮隐藏
- [ ] 工作流执行 API 返回 403
- [ ] API Key 不暴露
- [ ] 配置页面无法访问

---

## 📊 功能对比

| 功能 | main 分支 | public-release |
|------|---------|----------------|
| **知识展示** | ✅ | ✅ |
| **聊天问答** | ✅ | ✅ |
| **层级导航** | ✅ | ✅ |
| **搜索** | ✅ | ✅ |
| **工作流执行** | ✅ | ❌ 隐藏 |
| **配置管理** | ✅ | ❌ 隐藏 |
| **API Key 配置** | ✅ | ❌ 隐藏 |
| **后台管理** | ✅ | ❌ 隐藏 |

---

## 🔄 与 main 分支同步

```bash
# 定期同步知识内容和 bug 修复
git checkout public-release
git merge main

# 解决冲突时保留 public_mode 相关配置
# 推送更新
git push origin public-release
```

**注意：** 合并时保留 `PUBLIC_MODE` 相关配置和模板条件判断。

---

## ⚠️ 注意事项

### 1. 不要删除功能代码

- 只是隐藏，不是删除
- 保持与 main 分支的代码同步
- 方便后续功能更新

### 2. 使用环境变量控制

- 便于切换模式
- 便于不同环境配置
- 便于测试

### 3. Nginx 作为最后防线

- 即使后端配置错误，Nginx 也能拦截
- 双重保护更安全

---

## 📝 快速部署脚本

```bash
#!/bin/bash
# deploy_public_release.sh

echo "🚀 部署 public-release 分支..."

# 1. 切换分支
git checkout public-release
git pull origin public-release

# 2. 安装依赖
source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量
cat >> .env << EOF

# 公开模式配置
PUBLIC_MODE=true
HIDE_WORKFLOW_EXECUTION=true
HIDE_CONFIG_PAGE=true
EOF

# 4. 重启服务
./web/stop_web.sh 2>/dev/null
./web/start_public_release.sh --port 32015

# 5. 重载 Nginx
docker exec nginx-proxy nginx -s reload

echo "✅ 部署完成"
echo "🌐 访问地址：http://agentlearn.net/"
```

---

## 📞 总结

**public-release 分支特点：**

| 特性 | 说明 |
|------|------|
| **定位** | 对外公开发布 |
| **基础** | main 分支完整功能 |
| **模式** | 只读展示 |
| **隐藏** | 工作流执行、配置管理 |
| **保留** | 知识展示、聊天问答 |
| **安全** | 后端 + Nginx 双重保护 |

**适用场景：**

- ✅ 对外知识分享网站
- ✅ 生产环境部署
- ✅ 演示和展示
- ❌ 内部开发测试（使用 main 分支）

---

**文档版本：** 2.0  
**最后更新：** 2026-04-18  
**状态：** ✅ 重新设计完成
