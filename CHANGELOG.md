# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-08

### 🎉 首次稳定发布

### Added
- ✨ **5 层知识架构工作流** - 基础理论 → 技术栈 → 核心能力 → 工程实践 → 面试准备
- ✨ **Web 聊天问答系统** - 支持多个专家角色（理论/技术/工程/面试）
- ✨ **API Key 安全存储** - 加密存储 + 审计日志 (key_vault.py)
- ✨ **事件总线集成** - 统一日志 + 配置验证 + 实时通知
- ✨ **Docker/systemd 部署** - 支持容器化和系统服务长期运行
- ✨ **断点续传功能** - 防止工作流中断丢失
- ✨ **对话历史记录** - SQLite 存储，支持历史查询
- ✨ **单元测试** - 覆盖核心服务 (test_key_vault.py, test_integration.py 等)
- ✨ **工具脚本** - scripts/migrate_keys.py 等迁移工具

### Changed
- ♻️ **重构 LLM 客户端** - 支持 DashScope/Qwen/DeepSeek/GLM 等多种大模型
- ♻️ **迁移 pydantic 到 V2 语法** - 适配最新版本
- ♻️ **统一日志管理** - 标准化日志格式和输出
- ♻️ **优化配置验证** - config_validator.py 完整校验
- 🎨 **改进 Web 界面** - 配置页面重构，交互体验优化

### Fixed
- 🐛 修复流式输出问题
- 🐛 修复数据准确性问题
- 🐛 修复 API Key 验证失败时未记录日志的问题

### Security
- 🔒 **加密存储 API Key** - 使用 Fernet 加密
- 🔒 **LLM 调用审计日志** - 记录所有 API 调用
- 🔒 **敏感数据隔离** - secrets.db 独立存储
- 🔒 **配置验证器** - 启动前校验所有配置

### Removed
- 🗑️ 删除过时的设计文档和测试报告，保持仓库整洁

---

## [0.1.0] - 2026-03-30

### Added
- 初始版本发布
- 多 Agent 协作知识生成系统
- Flask Web 服务
- 基础测试框架
