# Learning Agent 项目功能说明文档

**版本：2.0**
**更新日期：2026-04-19**

---

## 项目概述

Learning Agent 是一个 AI Agent 开发面试知识体系生成系统，采用大模型驱动的方式自动生成系统化的学习内容。

**核心特性：**
- 三轮生成策略（结构 → 详情 → 关联）
- 5层知识架构（理论 → 技术 → 能力 → 实践 → 面试）
- 5个子Agent并发执行
- 断点续传支持
- Web界面展示

---

## 一、核心脚本功能

### 1.1 知识生成脚本

| 脚本 | 命令示例 | 功能说明 |
|-----|---------|---------|
| `run_workflow.py` | `python run_workflow.py` | **完整工作流入口**<br>执行全部5层20主题的生成<br>支持断点续传 |
| `regenerate_topic.py` | `python regenerate_topic.py "机器学习"` | **部分生成工具**<br>支持单主题/单层级生成<br>--skip-details / --skip-relation |
| `generate_framework.py` | `python generate_framework.py --view` | **知识框架生成工具**<br>生成/更新 YAML 配置<br>--preview / --force |

### 1.2 regenerate_topic.py 详细用法

```bash
# 查询功能
python regenerate_topic.py --list              # 列出所有20个主题
python regenerate_topic.py --list-layer 1      # 列出第1层主题

# 生成功能
python regenerate_topic.py "机器学习"          # 生成单个主题（完整三轮）
python regenerate_topic.py --layer-only 1      # 生成第1层所有主题

# 跳过选项
python regenerate_topic.py "机器学习" --skip-details    # 只生成结构
python regenerate_topic.py "机器学习" --skip-relation   # 只生成知识点
```

### 1.3 generate_framework.py 详细用法

```bash
python generate_framework.py --view     # 查看现有框架
python generate_framework.py --preview # 预览生成的框架（不保存）
python generate_framework.py --force   # 强制覆盖现有框架
python generate_framework.py           # 框架不存在时自动生成
```

---

## 二、知识架构设计

### 2.1 五层架构

| 层级 | 名称 | Agent | 主题数 | 定位 |
|-----|------|-------|--------|------|
| 第1层 | 基础理论层 | theory_worker | 4 | 理论基石 |
| 第2层 | 技术栈层 | tech_stack_worker | 4 | 实践工具 |
| 第3层 | 核心能力层 | core_skill_worker | 4 | 能力构建 |
| 第4层 | 工程实践层 | engineering_worker | 4 | 项目落地 |
| 第5层 | 面试准备层 | interview_worker | 4 | 求职准备 |

### 2.2 三轮生成策略

| 轮次 | 输入 | 输出内容 | 方法 |
|-----|------|---------|------|
| 第一轮 | topic_name + 层级信息 | subtopics, key_points, prerequisites, learning_sequence | `_build_question()` |
| 第二轮 | key_point | explanation, core_concepts, code_example, interview_frequency | `_build_keypoint_question()` |
| 第三轮 | 全部知识点 | knowledge_graph, practice_project, interview_highlights | `_build_relation_question()` |

### 2.3 输出数据结构

```json
{
  "topic_name": "主题名称",
  "description": "主题描述",
  "prerequisites": [
    {"knowledge": "前置知识", "from_layer": 1, "from_topic": "...", "reason": "..."}
  ],
  "subtopics": [
    {
      "name": "子主题",
      "key_points": ["知识点列表"],
      "detailed_keypoints": [
        {
          "key_point": "知识点",
          "explanation": "详细解释",
          "core_concepts": [...],
          "code_example": "...",
          "interview_frequency": "high"
        }
      ]
    }
  ],
  "knowledge_graph": {
    "dependencies": [{"from": "A", "to": "B", "strength": "strong"}],
    "cross_topic_relations": [...]
  },
  "practice_project": {
    "name": "项目名称",
    "tasks": [...],
    "skills_covered": [...]
  },
  "interview_highlights": {
    "frequently_asked": [...],
    "coding_challenges": [...],
    "system_design": [...]
  }
}
```

---

## 三、Web应用功能

### 3.1 Web应用版本

| 文件 | 功能 | 使用场景 |
|-----|------|---------|
| `web/app.py` | 开发版（全功能） | 开发测试，包含配置管理、聊天、工作流执行 |
| `web/public_app.py` | 公开版（只读） | 生产部署，只展示知识内容，无配置/执行功能 |

### 3.2 API路由

| 路由模块 | 基础路径 | 功能 |
|---------|---------|------|
| `workflow_routes.py` | `/api/workflow` | 知识内容展示API |
| `workflow_run_routes.py` | `/api/workflow/run` | 工作流执行管理API |
| `chat_routes.py` | `/api/chat` | Web聊天问答API |
| `config_routes.py` | `/api/config` | 配置管理API |

### 3.3 workflow_routes.py API列表

| API | 功能 |
|-----|------|
| `GET /api/workflow/layers` | 获取所有已完成的层 |
| `GET /api/workflow/layer/<layer_num>` | 获取单层详情 |
| `GET /api/workflow/topic/<layer_num>/<topic_index>` | 获取主题详情 |
| `GET /api/workflow/status` | 获取工作流状态 |
| `GET /api/workflow/cache/clear` | 清除缓存 |

### 3.4 workflow_run_routes.py API列表

| API | 功能 |
|-----|------|
| `POST /api/workflow/run/start` | 启动工作流 |
| `GET /api/workflow/run/status` | 检查运行状态 |
| `POST /api/workflow/run/stop` | 停止工作流 |
| `GET /api/workflow/run/check-api` | 检查API配置 |

### 3.5 config_routes.py API列表

| API | 功能 |
|-----|------|
| `GET /api/config` | 获取配置信息 |
| `PUT /api/config/api-key` | 更新API Key（加密存储） |
| `DELETE /api/config/api-key` | 删除API Key |
| `POST /api/config/test-api` | 测试API Key |
| `GET /api/config/audit-logs` | 获取审计日志 |

---

## 四、服务层功能

### 4.1 核心服务

| 服务 | 文件 | 功能说明 |
|-----|------|---------|
| **工作流编排器** | `workflow_orchestrator.py` | 核心引擎，三轮生成逻辑，5层并发执行 |
| **LLM客户端** | `services/llm_client.py` | 异步LLM调用，请求缓存，审计日志 |
| **Key Vault** | `services/key_vault.py` | API Key加密存储（Fernet） |
| **LLM审计日志** | `services/llm_audit_log.py` | SQLite + JSON + CSV 三重日志 |
| **问答服务** | `services/ask_service.py` | Web聊天问答服务 |
| **任务服务** | `services/task_service.py` | 工作流任务管理（被chat_routes引用） |

### 4.2 workflow_orchestrator.py 公开方法

| 方法 | 功能 |
|-----|------|
| `initialize()` | 初始化工作流（加载配置、创建Agent、加载进度） |
| `execute_workflow()` | 执行完整工作流（5层并发） |
| `execute_single_topic(topic_name, layer_num, skip_details, skip_relation)` | 执行单个主题 |
| `execute_layer(layer_num, skip_details, skip_relation)` | 执行整个层级 |
| `list_all_topics()` | 列出所有主题 |
| `list_layer_topics(layer_num)` | 列出指定层主题 |

### 4.3 services/llm_client.py 功能

| 功能 | 说明 |
|-----|------|
| 异步调用 | `async_chat()` 支持并发 |
| 请求缓存 | 相同prompt不重复调用 |
| Token统计 | 统计输入/输出token，估算成本 |
| 自动重试 | max_retries=2，失败自动重试 |
| 审计日志 | 每次调用记录到SQLite/JSON/CSV |

### 4.4 services/key_vault.py 功能

| 功能 | 说明 |
|-----|------|
| Fernet加密 | 使用 cryptography 库对称加密 |
| 主密钥管理 | 从环境变量读取主密钥 |
| Key前缀显示 | 前端只显示前缀，不暴露完整Key |
| 审计日志 | 记录所有Key操作（创建/读取/删除） |
| 多Provider支持 | 支持多API Key存储 |

---

## 五、配置文件

### 5.1 核心配置

| 文件 | 功能 | 内容 |
|-----|------|------|
| `config/agent_config.yaml` | Agent配置 | 5个子Agent定义、LLM参数、工具列表 |
| `config/knowledge_framework.yaml` | 知识架构 | 5层架构、主题列表、优先级 |

### 5.2 agent_config.yaml 结构

```yaml
agents:
  theory_worker:
    layer: 1
    role: AI 理论基础专家
    model: qwen3.5-plus
    system_prompt: ...
    llm_config:
      max_tokens: 4000
      temperature: 0.7
  # ... 其他4个Agent

providers:
  dashscope:
    base_url: https://coding.dashscope.aliyuncs.com/v1
    models:
      qwen3.5-plus:
        max_tokens: 4000

performance:
  cache:
    ttl: 14400  # 4小时缓存
```

### 5.3 knowledge_framework.yaml 结构

```yaml
name: Agent 开发面试知识体系
version: "1.0"

layers:
  - layer: 1
    name: 基础理论层
    agent: theory_worker
    topics:
      - name: 机器学习
        priority: high
      # ... 其他主题
```

---

## 六、数据存储

### 6.1 数据目录

| 目录 | 内容 |
|-----|------|
| `data/workflow_results/` | 工作流生成结果JSON |
| `data/llm_audit_logs/` | LLM调用审计日志 |
| `data/chat_history/` | Web聊天历史 |
| `data/secrets.db` | API Key加密存储（SQLite） |
| `data/learning_agent.db` | LLM审计日志数据库 |

### 6.2 工作流结果文件命名

| 文件 | 内容 |
|-----|------|
| `layer_X_workflow.json` | 第X层合并结果 |
| `workflow_TIMESTAMP.json` | 完整工作流结果 |
| `workflow_summary.json` | 汇总文件 |

---

## 七、工具类

### 7.1 utils目录

| 文件 | 功能 | 使用情况 |
|-----|------|---------|
| `event_bus.py` | 事件总线，发布/订阅模式 | ✅ 被 workflow_orchestrator、llm_client 使用 |
| `logger.py` | 日志工具 | ❌ 未使用（各模块有自己的logger） |
| `logging_config.py` | 日志配置 | ❌ 未使用 |

---

## 八、测试

### 8.1 测试文件

| 文件 | 功能 |
|-----|------|
| `tests/test_workflow_orchestrator.py` | WorkflowOrchestrator 单元测试 |
| `tests/test_key_vault.py` | Key Vault 测试 |
| `tests/test_llm_client.py` | LLM Client 测试 |
| `tests/test_config_routes.py` | 配置路由测试 |
| `tests/test_web_routes.py` | Web路由测试 |
| `tests/test_ask_service.py` | 问答服务测试 |
| `tests/test_integration.py` | 集成测试 |

---

## 九、废弃文件（待删除）

| 文件 | 原因 |
|-----|------|
| `test_llm.py` | 简单测试脚本，硬编码API Key |
| `llm_test.py` | 重复测试脚本，硬编码API Key |
| `test_api_key_flow.py` | 一次性验证脚本 |
| `utils/logging_config.py` | 未被引用 |
| `utils/logger.py` | 未被引用（可合并到event_bus） |
| `config/config_validator.py` | 未被引用 |
| `models/database.py` | 未被引用 |
| `scripts/migrate_keys.py` | 一次性迁移脚本 |

---

## 十、命令速查表

### 10.1 知识生成

```bash
# 完整生成（5层20主题）
python run_workflow.py

# 查看主题列表
python regenerate_topic.py --list
python regenerate_topic.py --list-layer 1

# 单主题生成
python regenerate_topic.py "机器学习"
python regenerate_topic.py "机器学习" --layer 1
python regenerate_topic.py "机器学习" --skip-details --skip-relation

# 单层级生成
python regenerate_topic.py --layer-only 1
python regenerate_topic.py --layer-only 1 --skip-details

# 知识框架管理
python generate_framework.py --view
python generate_framework.py --preview
python generate_framework.py --force
```

### 10.2 Web应用

```bash
# 开发版（全功能）
python web/app.py

# 公开版（只读展示）
python web/public_app.py
```

### 10.3 API Key管理

```bash
# 通过Key Vault保存（加密）
python -c "from services.key_vault import get_key_vault; get_key_vault().save_key('dashscope', 'sk-xxx')"

# 查看Key前缀
python -c "from services.key_vault import get_key_vault; print(get_key_vault().get_key_prefix('dashscope'))"
```

---

## 十一、架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Learning Agent 系统架构                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐     ┌──────────────────┐                      │
│  │   命令行工具      │     │    Web应用        │                      │
│  │ run_workflow.py  │     │  web/app.py      │                      │
│  │ regenerate_topic │     │  web/public_app  │                      │
│  │ generate_framework│     │                  │                      │
│  └────────┬─────────┘     └────────┬─────────┘                      │
│           │                        │                                 │
│           ▼                        ▼                                 │
│  ┌──────────────────────────────────────────────────┐               │
│  │          workflow_orchestrator.py (核心引擎)      │               │
│  │  ┌─────────────────────────────────────────────┐│               │
│  │  │ 三轮生成: _build_question → _build_kp → _rel ││               │
│  │  │ 5层并发: asyncio.gather(layer1...layer5)    ││               │
│  │  │ 断点续传: _load_partial_progress            ││               │
│  │  └─────────────────────────────────────────────┘│               │
│  └────────┬────────────────────┬───────────────────┘               │
│           │                    │                                    │
│           ▼                    ▼                                    │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │ 5个AsyncAgent│     │   LLM Client │     │   Key Vault  │        │
│  │ theory_worker│     │ async_chat() │     │ Fernet加密   │        │
│  │ tech_worker  │     │ 缓存/审计    │     │ audit log    │        │
│  │ core_worker  │     └──────────────┘     └──────────────┘        │
│  │ eng_worker   │                                                  │
│  │ interview    │                                                  │
│  └──────────────┘                                                  │
│                                                                      │
│  ┌──────────────────────────────────────────────────┐               │
│  │                    配置文件                        │               │
│  │ config/agent_config.yaml (Agent配置)             │               │
│  │ config/knowledge_framework.yaml (知识架构)       │               │
│  └──────────────────────────────────────────────────┘               │
│                                                                      │
│  ┌──────────────────────────────────────────────────┐               │
│  │                    数据存储                        │               │
│  │ data/workflow_results/ (生成结果JSON)            │               │
│  │ data/llm_audit_logs/ (审计日志)                  │               │
│  │ data/secrets.db (API Key加密存储)                │               │
│  └──────────────────────────────────────────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 十二、版本历史

| 版本 | 日期 | 更新内容 |
|-----|------|---------|
| 1.0 | 2026-04-18 | 初始版本，两轮生成策略 |
| 2.0 | 2026-04-19 | 三轮生成策略，知识关联生成，重构代码消除重复 |

---

---

## 十四、Shell脚本功能说明

> **优化说明：** 已删除重复脚本，从17个减少到8个（优化日期：2026-04-19）

### 14.1 脚本列表（最终版）

| 脚本 | 行数 | 功能说明 |
|-----|------|---------|
| **启动相关** | | |
| `start.sh` | 363 | **统一Web启动脚本（合并版）**<br>- 开发版：默认模式，全功能<br>- 公开版：--public参数，只读展示<br>- 支持前台/后台/状态/重启/停止/指定端口 |
| `start_workflow.sh` | 258 | **工作流启动脚本（优化版）**<br>支持参数：--skip-details/--skip-relation/--topic/--layer/--status/--stop |
| `start_watchdog.sh` | 143 | **守护进程脚本（修复版）**<br>自动监控/重启Web服务，修复硬编码路径 |
| **部署相关** | | |
| `deploy.sh` | 105 | systemd服务部署（开发环境） |
| `deploy_public.sh` | 327 | **公开版部署脚本（合并版）**<br>支持--mode systemd/docker，统一部署方式 |
| **同步相关** | | |
| `sync_web_data.sh` | 121 | Web数据同步到部署目录（保留layer文件，删除冗余） |
| **其他** | | |
| `install_aliases.sh` | 80 | 安装快捷命令别名 |
| `test_hot_reload.sh` | 56 | 测试API Key热更新功能 |

---

### 14.2 已删除的脚本

| 脚本 | 删除原因 |
|-----|---------|
| `run_workflow_background.sh` | 功能与`start_workflow.sh`重复 |
| `sync_to_deploy.sh` | 功能与`sync_web_data.sh`重复 |
| `deploy_public_release.sh` | 合并到`deploy_public.sh` |
| `deploy_public_simple.sh` | 合并到`deploy_public.sh` |
| `deploy_docker.sh` | 合并到`deploy_public.sh` |
| `web/start_web.sh` | 功能被`start.sh`覆盖 |
| `web/start_public_web.sh` | 合并到`start.sh --public` |
| `web/start_public_release.sh` | 合并到`start.sh --public` |
| `web/stop_web.sh` | 功能被`start.sh -k`覆盖 |

---

### 14.3 start.sh 统一启动脚本

**开发版启动（默认）：**
```bash
./start.sh                    # 前台启动（端口5001）
./start.sh -d                  # 后台启动
./start.sh -p 8080             # 自定义端口
./start.sh -s                  # 查看状态
./start.sh -k                  # 停止服务
./start.sh -r                  # 重启服务
```

**公开版启动（新增）：**
```bash
./start.sh --public            # 公开版启动（端口80）
./start.sh --public -d         # 公开版后台启动
./start.sh --public -p 32015   # 公开版自定义端口
```

**功能对比：**

| 功能 | 开发版 | 公开版 |
|-----|--------|--------|
| 知识架构展示 | ✅ | ✅ |
| 知识点详情 | ✅ | ✅ |
| Web聊天问答 | ✅ | ❌ |
| 配置管理 | ✅ | ❌ |
| 工作流执行 | ✅ | ❌ |
| 默认端口 | 5001 | 80 |

---

### 14.4 Shell脚本命令速查表

```bash
# ===== Web服务管理 =====
./start.sh                           # 前台启动（开发版）
./start.sh -d                        # 后台启动（开发版）
./start.sh --public                  # 公开版启动（端口80）
./start.sh --public -d -p 32015      # 公开版后台启动（端口32015）
./start.sh -s                        # 查看状态
./start.sh -k                        # 停止服务
./start.sh -r                        # 重启服务

# ===== 工作流管理 =====
./start_workflow.sh                  # 全量生成（三轮）
./start_workflow.sh --skip-details   # 只生成结构
./start_workflow.sh --skip-relation  # 跳过知识关联
./start_workflow.sh --topic "机器学习" # 单主题
./start_workflow.sh --layer 1        # 第1层
./start_workflow.sh --status         # 查看状态
./start_workflow.sh --stop           # 停止工作流

# ===== 守护进程 =====
./start_watchdog.sh                  # 启动守护进程
./start_watchdog.sh --status         # 查看状态
./start_watchdog.sh --stop           # 停止守护进程

# ===== 部署 =====
./deploy.sh                          # systemd部署（开发）
./deploy_public.sh --mode systemd    # systemd部署（公开）
./deploy_public.sh --mode docker     # Docker部署（公开）

# ===== 数据同步 =====
./sync_web_data.sh                   # 同步知识数据

# ===== 快捷命令 =====
./install_aliases.sh                 # 安装快捷命令
la                                   # 进入项目目录
la-sync                              # 同步数据
la-status                            # 查看容器状态
```

---

### 14.5 优化成果

| 项目 | 优化前 | 优化后 | 变化 |
|-----|--------|--------|------|
| **脚本数量** | 17个 | 8个 | ⬇️ 减少53% |
| **总代码行数** | ~1266行 | 1619行 | ⬆️ 增强35% |
| **功能覆盖** | 分散 | 集中 | ✅ 统一入口 |

---

## 十五、后续优化方向

| 方向 | 说明 |
|-----|------|
| 知识图谱可视化 | 前端展示知识点依赖关系图 |
| 实践项目执行 | 支持实际运行项目代码 |
| 面试模拟 | 根据知识点生成模拟面试题 |
| 学习路径推荐 | 根据用户情况推荐学习顺序 |
| 多语言支持 | 支持英文等其他语言内容生成 |

---

**文档维护：**
- 本文档随项目更新同步维护
- 如有功能变更，请及时更新对应章节