# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 5 层知识架构工作流（基础理论 → 技术栈 → 核心能力 → 工程实践 → 面试准备）
- Web 聊天问答界面，支持多个专家角色
- 断点续传功能，防止工作流中断丢失
- 实时进度保存
- 对话历史记录功能

### Changed
- 优化 LLM 客户端，支持 DashScope/Qwen 等兼容 OpenAI API 格式的模型
- 改进 Web 界面交互体验

### Fixed
- 修复流式输出问题
- 修复数据准确性问题
- 修复板块变化排序问题

## [0.1.0] - 2026-03-30

### Added
- 初始版本发布
- 多 Agent 协作知识生成系统
- Flask Web 服务
- 基础测试框架
