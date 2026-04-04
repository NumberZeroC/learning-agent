# Learning Agent 测试文档

## 📋 测试概览

本项目使用 **pytest** 作为测试框架，所有测试使用 **Mock** 替代真实的大模型 API 调用。

### 测试文件结构

```
tests/
├── conftest.py                      # Pytest 配置和全局 fixture
├── test_workflow_orchestrator.py    # 工作流编排器测试
├── test_ask_service.py              # 问答服务测试
├── test_web_routes.py               # Web API 路由测试
└── README.md                        # 测试文档
```

---

## 🚀 快速开始

### 1. 安装测试依赖

```bash
pip3 install pytest pytest-mock pytest-cov
```

### 2. 运行所有测试

```bash
# 方式 1：使用测试脚本
./run_tests.sh

# 方式 2：直接使用 pytest
pytest tests/ -v
```

### 3. 运行带覆盖率的测试

```bash
./run_tests.sh --coverage
# 或
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

### 4. 运行单个测试文件

```bash
# 测试工作流编排器
pytest tests/test_workflow_orchestrator.py -v

# 测试问答服务
pytest tests/test_ask_service.py -v

# 测试 Web 路由
pytest tests/test_web_routes.py -v
```

### 5. 运行特定测试用例

```bash
# 运行特定测试类
pytest tests/test_workflow_orchestrator.py::TestSubAgent -v

# 运行特定测试方法
pytest tests/test_workflow_orchestrator.py::TestSubAgent::test_ask_success -v
```

---

## 📊 测试覆盖范围

### 1. 工作流编排器测试 (`test_workflow_orchestrator.py`)

| 测试类 | 测试用例 | 说明 |
|--------|---------|------|
| **TestSubAgent** | `test_sub_agent_init` | 测试 SubAgent 初始化 |
| | `test_ask_success` | 测试成功调用 API |
| | `test_ask_api_error` | 测试 API 错误处理 |
| | `test_ask_retry_mechanism` | 测试重试机制 |
| **TestWorkflowOrchestrator** | `test_orchestrator_init` | 测试编排器初始化 |
| | `test_create_tasks` | 测试任务创建 |
| | `test_build_question` | 测试问题构建 |
| | `test_parse_knowledge_valid_json` | 测试解析有效 JSON |
| | `test_parse_knowledge_invalid_json` | 测试解析无效 JSON（容错） |
| | `test_execute_task_success` | 测试任务执行成功 |
| | `test_save_task_result` | 测试保存任务结果 |
| | `test_merge_layer_results` | 测试层结果合并 |
| **TestWorkflowResult** | `test_workflow_result_creation` | 测试工作流结果创建 |
| **TestIntegration** | `test_full_workflow_mock` | 完整工作流集成测试 |

### 2. 问答服务测试 (`test_ask_service.py`)

| 测试类 | 测试用例 | 说明 |
|--------|---------|------|
| **TestAskServiceInit** | `test_init_with_config` | 测试有配置文件时的初始化 |
| | `test_init_without_config` | 测试无配置文件时的初始化 |
| **TestAskServiceChat** | `test_chat_success` | 测试成功聊天 |
| | `test_chat_api_error` | 测试 API 错误 |
| | `test_chat_empty_message` | 测试空消息 |
| **TestAskServiceHistory** | `test_get_history` | 测试获取对话历史 |
| | `test_chat_saves_history` | 测试聊天保存历史 |
| | `test_clear_history` | 测试清空历史 |
| | `test_history_limit` | 测试历史长度限制 |
| **TestAskServiceLLMCall** | `test_call_llm_request_format` | 测试 LLM 请求格式 |
| | `test_call_llm_timeout` | 测试超时设置 |
| | `test_call_llm_empty_response` | 测试空响应处理 |
| **TestAskServiceAgents** | `test_get_available_agents` | 测试获取可用 Agent |
| **TestSingleton** | `test_get_ask_service_singleton` | 测试单例模式 |

### 3. Web API 路由测试 (`test_web_routes.py`)

| 测试类 | 测试用例 | 说明 |
|--------|---------|------|
| **TestChatRoutes** | `test_send_message_success` | 测试发送消息成功 |
| | `test_send_message_empty_message` | 测试空消息 |
| | `test_send_message_missing_message` | 测试缺少消息字段 |
| | `test_send_message_empty_json` | 测试空 JSON |
| | `test_get_history` | 测试获取对话历史 |
| **TestWorkflowRoutes** | `test_get_all_layers` | 测试获取所有层 |
| | `test_get_layer_success` | 测试获取单层成功 |
| | `test_get_layer_not_found` | 测试获取不存在的层 |
| | `test_get_topic_success` | 测试获取主题成功 |
| | `test_get_topic_index_out_of_range` | 测试主题索引超出范围 |
| | `test_get_workflow_status` | 测试获取工作流状态 |
| | `test_get_workflow_summary` | 测试获取工作流汇总 |
| **TestAppRoutes** | `test_health_check` | 测试健康检查接口 |
| | `test_api_summary_success` | 测试获取汇总成功 |
| | `test_api_summary_not_found` | 测试汇总文件不存在 |
| **TestPageRoutes** | `test_index_page` | 测试首页 |
| | `test_chat_page` | 测试聊天页面 |
| | `test_layer_page` | 测试层级页面 |
| | `test_topic_page` | 测试主题页面 |

---

## 🔧 Mock 使用示例

### Mock 大模型 API 调用

```python
from unittest.mock import patch, MagicMock
import json

@patch('workflow_orchestrator.urllib.request.urlopen')
def test_ask_success(self, mock_urlopen):
    # Mock API 响应
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "choices": [
            {
                "message": {
                    "content": "这是测试回答"
                }
            }
        ]
    }).encode('utf-8')
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    # 测试代码
    agent = SubAgent(...)
    result = agent.ask("测试问题")
    
    # 验证结果
    assert result["success"] is True
    assert result["content"] == "这是测试回答"
```

### Mock 环境变量

```python
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock 环境变量"""
    monkeypatch.setenv('DASHSCOPE_API_KEY', 'sk-test-mock-key')
    monkeypatch.setenv('LEARNING_AGENT_TOKEN', 'test-token')
```

### Mock 服务依赖

```python
@patch('web.routes.chat_routes.get_ask_service')
def test_send_message_success(self, mock_get_service):
    # Mock AskService
    mock_service = Mock()
    mock_service.chat.return_value = {
        "success": True,
        "reply": "这是测试回答",
        "agent": "test_agent",
        "timestamp": "2026-03-31T12:00:00"
    }
    mock_get_service.return_value = mock_service
    
    # 测试代码
    response = client.post('/api/chat/send', json={...})
    
    # 验证结果
    assert response.status_code == 200
```

---

## 📈 测试覆盖率

### 查看覆盖率报告

```bash
# 运行带覆盖率的测试
pytest tests/ --cov=. --cov-report=html

# 在浏览器中打开报告
open htmlcov/index.html
# 或
xdg-open htmlcov/index.html  # Linux
```

### 覆盖率目标

- **行覆盖率**: > 80%
- **分支覆盖率**: > 70%
- **关键模块**: 100%（workflow_orchestrator.py, ask_service.py）

---

## 🎯 测试最佳实践

### 1. 测试命名规范

```python
def test_<功能>_<场景>_<预期结果>():
    # 例如：
    def test_ask_success():  # 成功场景
    def test_ask_api_error():  # 错误场景
    def test_ask_retry_mechanism():  # 特定功能
```

### 2. 使用 Fixture 复用代码

```python
@pytest.fixture
def sample_workflow_result():
    """示例工作流结果"""
    return {
        "workflow_id": "test_20260331_120000",
        "total_tasks": 17,
        "success_count": 17
    }

def test_workflow_result(sample_workflow_result):
    # 直接使用 fixture
    assert sample_workflow_result["total_tasks"] == 17
```

### 3. 测试边界条件

```python
# 测试空值
def test_empty_message():
    ...

# 测试极大值
def test_large_input():
    ...

# 测试异常
def test_api_error():
    ...
```

### 4. 保持测试独立

```python
# ❌ 错误：测试之间有依赖
def test_1():
    global data
    data = prepare_data()

def test_2():
    # 依赖 test_1 的 data
    process_data(data)

# ✅ 正确：每个测试独立
def test_1():
    data = prepare_data()
    ...

def test_2():
    data = prepare_data()  # 独立准备数据
    ...
```

---

## 🐛 常见问题

### Q: 测试失败 "ModuleNotFoundError"

**解决：** 确保在项目根目录运行测试

```bash
cd /home/admin/.openclaw/workspace/learning-agent
pytest tests/
```

### Q: Mock 不生效

**解决：** 检查 Mock 路径是否正确

```python
# ❌ 错误：Mock 原始模块
@patch('urllib.request.urlopen')

# ✅ 正确：Mock 被导入的模块
@patch('workflow_orchestrator.urllib.request.urlopen')
```

### Q: 测试运行缓慢

**解决：** 使用标记跳过慢测试

```bash
# 跳过慢测试
pytest tests/ -v -m "not slow"
```

---

## 📝 添加新测试

### 1. 创建测试文件

```python
# tests/test_new_feature.py

import pytest
from pathlib import Path
import sys

# 添加项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from module_to_test import new_feature

class TestNewFeature:
    def test_feature_success(self):
        # 测试成功场景
        pass
    
    def test_feature_error(self):
        # 测试错误场景
        pass
```

### 2. 运行新测试

```bash
pytest tests/test_new_feature.py -v
```

---

## 🎉 总结

- ✅ **所有测试使用 Mock**，不依赖真实 API
- ✅ **覆盖核心功能**：工作流、问答、Web API
- ✅ **持续集成友好**：可配置到 CI/CD 流程
- ✅ **覆盖率可视化**：HTML 报告

**运行所有测试：**
```bash
./run_tests.sh
```
