# 贡献指南

感谢你考虑为 Learning Agent 做出贡献！

## 🚀 快速开始

### 1. Fork 项目

在 GitHub 上点击 Fork 按钮创建你自己的副本。

### 2. 克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/learning-agent.git
cd learning-agent
```

### 3. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 4. 配置环境

```bash
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

### 5. 运行测试

```bash
./run_tests.sh
```

## 📝 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具/配置更新

### 示例

```
feat(workflow): 添加断点续传功能

- 实现工作流进度自动保存
- 支持从中断点恢复执行
- 添加进度状态检查接口

Closes #123
```

## 🔧 开发流程

### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 开发并测试

确保你的代码：
- 通过现有测试
- 添加了必要的单元测试
- 更新了相关文档

### 3. 提交代码

```bash
git add .
git commit -m "feat: your commit message"
```

### 4. 推送并创建 PR

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## 📋 PR 要求

- [ ] 代码通过所有测试
- [ ] 添加了必要的单元测试
- [ ] 更新了相关文档
- [ ] Commit message 符合规范
- [ ] 无敏感信息泄露（API Key、密码等）

## 🐛 报告 Bug

请在 GitHub Issues 中创建 Bug 报告，包含：

1. 问题描述
2. 复现步骤
3. 预期行为
4. 实际行为
5. 环境信息（Python 版本、操作系统等）
6. 日志输出（如有）

## 💡 功能建议

欢迎在 GitHub Issues 中提出新功能建议，请说明：

1. 功能描述
2. 使用场景
3. 预期效果

## 📧 联系方式

如有问题，请通过 GitHub Issues 联系。

---

再次感谢你的贡献！🎉
