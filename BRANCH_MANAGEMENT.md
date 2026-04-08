# 分支管理与版本管理规范

> 📅 创建时间：2026-04-08  
> 📋 目的：规范 Git 分支管理，确保版本可控、发布有序

---

## 🌿 分支策略

采用 **Git Flow** 简化版，适合个人/小团队项目：

```
main (受保护，稳定版本)
  │
  ├── develop (开发分支，日常开发)
  │     │
  │     ├── feature/* (功能分支)
  │     ├── bugfix/* (修复分支)
  │     └── hotfix/* (紧急修复)
  │
  └── backup/* (备份分支，重要节点快照)
```

---

## 📋 分支说明

| 分支类型 | 命名规范 | 说明 | 保留策略 |
|---------|---------|------|---------|
| **main** | `main` | 生产环境，稳定版本 | 永久保留 |
| **develop** | `develop` | 开发主线，集成新功能 | 永久保留 |
| **功能分支** | `feature/功能名` | 开发新功能 | 合并后删除 |
| **修复分支** | `bugfix/问题描述` | 修复非紧急 bug | 合并后删除 |
| **紧急修复** | `hotfix/问题描述` | 生产环境紧急修复 | 合并后删除 |
| **备份分支** | `backup-YYYY-MM-DD` | 重要节点快照 | 按需保留 |

---

## 🏷️ 版本标签 (Tags)

采用 **Semantic Versioning** (语义化版本)：`v主版本。次版本。修订号`

### 版本规范

| 版本类型 | 格式 | 说明 | 示例 |
|---------|------|------|------|
| **主版本** | `vX.0.0` | 不兼容的 API 变更 | `v2.0.0` |
| **次版本** | `v1.X.0` | 向后兼容的功能新增 | `v1.2.0` |
| **修订号** | `v1.0.X` | 向后兼容的问题修复 | `v1.0.3` |
| **预发布** | `v1.0.0-beta.1` | 测试版本 | `v1.0.0-rc.1` |

### 打标签流程

```bash
# 1. 确认在 main 分支
git checkout main

# 2. 更新 CHANGELOG.md
# 编辑 CHANGELOG.md，记录本次版本变更

# 3. 提交变更
git add CHANGELOG.md
git commit -m "📦 准备发布 v1.0.0"

# 4. 打标签
git tag -a v1.0.0 -m "🎉 v1.0.0 - 首次稳定发布"

# 5. 推送标签
git push origin v1.0.0
```

---

## 🔄 标准工作流程

### 开发新功能

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git checkout -b feature/web-chat-improvement

# 2. 开发功能（多次提交）
git add .
git commit -m "✨ 添加：聊天导出功能"

# 3. 推送到远程
git push origin feature/web-chat-improvement

# 4. 创建 Pull Request (GitHub)
# 等待代码审查通过后合并到 develop

# 5. 删除功能分支
git branch -d feature/web-chat-improvement
git push origin --delete feature/web-chat-improvement
```

### 发布新版本

```bash
# 1. 从 develop 创建 release 分支
git checkout develop
git checkout -b release/v1.1.0

# 2. 最终测试和文档更新
# 更新 README.md, CHANGELOG.md

# 3. 合并到 main
git checkout main
git merge release/v1.1.0
git tag -a v1.1.0 -m "🎉 v1.1.0 - 新增聊天导出功能"

# 4. 合并回 develop
git checkout develop
git merge release/v1.1.0

# 5. 删除 release 分支
git branch -d release/v1.1.0

# 6. 推送所有变更
git push origin main develop --tags
```

### 紧急修复 (Hotfix)

```bash
# 1. 从 main 创建 hotfix 分支
git checkout main
git checkout -b hotfix/api-key-leak

# 2. 修复问题
git add .
git commit -m "🐛 修复：API Key 泄露问题"

# 3. 合并到 main 并打标签
git checkout main
git merge hotfix/api-key-leak
git tag -a v1.0.1 -m "🔒 v1.0.1 - 安全修复"

# 4. 合并到 develop
git checkout develop
git merge hotfix/api-key-leak

# 5. 删除 hotfix 分支
git branch -d hotfix/api-key-leak

# 6. 推送
git push origin main develop --tags
```

---

## 📝 提交信息规范

采用 **Conventional Commits** 格式：

```
<类型>(<范围>): <描述>

[可选的正文]

[可选的脚注]
```

### 类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `✨ feat` | 新功能 | `✨ feat(web): 添加配置页面` |
| `🐛 fix` | Bug 修复 | `🐛 fix(api): 修复 Key 验证逻辑` |
| `📝 docs` | 文档更新 | `📝 docs: 更新 README` |
| `🎨 style` | 代码格式 | `🎨 style: 格式化代码` |
| `♻️ refactor` | 重构 | `♻️ refactor: 优化数据库连接` |
| `⚡ perf` | 性能优化 | `⚡ perf: 缓存优化` |
| `✅ test` | 测试 | `✅ test: 添加单元测试` |
| `🔧 chore` | 构建/工具 | `🔧 chore: 更新依赖` |
| `🚀 deploy` | 部署 | `🚀 deploy: 添加 systemd 配置` |
| `📦 release` | 发布 | `📦 release: 准备 v1.0.0` |

### 提交示例

```bash
# ✅ 好的提交
git commit -m "✨ feat(web): 添加聊天历史记录导出功能"
git commit -m "🐛 fix(api): 修复 API Key 验证失败时未记录日志的问题"
git commit -m "📝 docs: 更新部署文档，添加 systemd 配置说明"

# ❌ 不好的提交
git commit -m "fix bug"
git commit -m "update"
git commit -m "修改了一些东西"
```

---

## 🛡️ 当前项目状态 (2026-04-08)

### 分支情况
```
main                    ✅ 当前分支，领先远程 1 个提交
backup-2026-04-05      ✅ 备份分支
develop                ❌ 未创建（需要创建）
```

### 待处理变更
```
修改的文件：20+
删除的文件：10+ (旧文档)
新增的文件：10+ (新文档和服务)
未跟踪文件：scripts/, tests/, services/key_vault.py
```

### 建议操作

#### 1. 创建 develop 分支
```bash
cd /home/admin/.openclaw/workspace/learning-agent
git checkout -b develop
git push -u origin develop
```

#### 2. 整理当前变更
```bash
# 审查变更
git status
git diff

# 添加重要变更
git add API_KEY_SECURITY_README.md
git add services/key_vault.py
git add scripts/
git add tests/
git add docs/API_KEY_*.md

# 提交
git commit -m "🔒 feat(security): API Key 安全存储重构

- 新增 key_vault.py 安全存储模块
- 新增审计日志功能
- 更新文档和测试
- 删除旧版本文档"

# 推送到 develop
git push origin develop
```

#### 3. 创建新版本标签
```bash
# 合并到 main
git checkout main
git merge develop
git tag -a v1.0.0 -m "🎉 v1.0.0 - 初始稳定版本

核心功能:
- 5 层知识架构生成
- Web 聊天问答
- API Key 安全存储
- 事件总线集成
- Docker/systemd 部署"

git push origin main --tags
```

---

## 📊 版本发布检查清单

发布前确认：

- [ ] 所有测试通过 (`make test`)
- [ ] 代码格式化 (`make format`)
- [ ] 文档已更新 (`README.md`, `CHANGELOG.md`)
- [ ] `.env.example` 包含所有新环境变量
- [ ] `requirements.txt` 已更新
- [ ] 版本号已更新 (如有)
- [ ] 在测试环境验证过
- [ ] 备份数据库 (如适用)

---

## 🔗 相关资源

- [Git Flow 工作流](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)

---

## 📜 维护记录

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-04-08 | 创建规范 | 初始版本，定义分支和版本管理策略 |
