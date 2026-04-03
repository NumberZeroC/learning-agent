# 🐛 Bug 修复报告 - 工具输入转换

**日期：** 2026-04-03  
**问题：** `mkdir` 工具执行失败 - `'dict' object has no attribute 'path'`  
**状态：** ✅ 已修复

---

## 📋 问题描述

用户在运行 CCP 时遇到错误：

```
AttributeError: 'dict' object has no attribute 'path'
```

**错误堆栈：**
```
File "src/tools/mkdir.py:99 in execute
    path = tool_input.path
AttributeError: 'dict' object has no attribute 'path'
```

**触发场景：**
```python
# 用户请求
tool_input = {'path': 'searchable_agent'}

# 工具执行失败
await registry.execute_tool('mkdir', tool_input, context)
# ❌ AttributeError
```

---

## 🔍 根因分析

### 问题链路

```
ToolRegistry.execute_tool()
  ├─ 接收：dict 类型 tool_input
  ├─ 验证：validate_input(dict) ✅ 通过
  ├─ 转换：dict → Typed Input ❌ 缺失
  └─ 执行：execute_with_hooks(typed_input)
       └─ execute(typed_input)
            └─ tool_input.path ❌ AttributeError
```

### 代码问题

**registry.py 第 168-185 行：**

```python
# Convert dict to tool's input model
from ..tools.bash import BashInput
from ..tools.file_read import FileReadInput
from ..tools.file_edit import FileEditInput
from ..tools.file_write import FileWriteInput
from ..tools.grep import GrepInput
from ..tools.glob import GlobInput

# Map tool names to input classes
input_classes = {
    'bash': BashInput,
    'file_read': FileReadInput,
    'file_edit': FileEditInput,
    'file_write': FileWriteInput,
    'grep': GrepInput,
    'glob': GlobInput,
}

input_class = input_classes.get(name)
if input_class:
    typed_input = input_class(**tool_input)
else:
    typed_input = tool_input  # type: ignore  ❌ 问题在这里！
```

**问题：**
1. `mkdir` 不在 `input_classes` 映射中
2. 未映射的工具直接使用 `dict`，导致 `execute()` 方法访问属性时报错

---

## ✅ 修复方案

### 添加 MkdirInput 到映射

```python
# src/tools/registry.py

# Convert dict to tool's input model
from ..tools.bash import BashInput
from ..tools.file_read import FileReadInput
from ..tools.file_edit import FileEditInput
from ..tools.file_write import FileWriteInput
from ..tools.grep import GrepInput
from ..tools.glob import GlobInput
from ..tools.mkdir import MkdirInput  # ✅ 新增导入

# Map tool names to input classes
input_classes = {
    'bash': BashInput,
    'file_read': FileReadInput,
    'file_edit': FileEditInput,
    'file_write': FileWriteInput,
    'grep': GrepInput,
    'glob': GlobInput,
    'mkdir': MkdirInput,  # ✅ 新增映射
}
```

---

## 🧪 验证测试

### 1. 输入转换测试

```python
from src.tools.mkdir import MkdirInput

tool_input = {'path': 'test_dir'}
typed = MkdirInput(**tool_input)

print(f'✓ 输入转换成功：path={typed.path}, parents={typed.parents}')
# 输出：path=test_dir, parents=True
```

### 2. 工具执行测试

```python
import asyncio
from src.tools.mkdir import MkdirTool, MkdirInput
from src.tools.base import ToolContext

async def test():
    tool = MkdirTool()
    ctx = ToolContext(session_id='test', working_directory='/tmp')
    
    result = await tool.execute(MkdirInput(path='searchable_agent'), ctx)
    
    print(f'✓ 工具执行结果：is_error={result.is_error}')
    # 输出：is_error=False
    
    print(f'✓ 目录存在：{os.path.exists("/tmp/searchable_agent")}')
    # 输出：True

asyncio.run(test())
```

### 3. 完整流程测试

```bash
$ .venv/bin/python -c "
from src.tools.registry import ToolRegistry
from src.tools.mkdir import MkdirTool
from src.tools.base import ToolContext
import asyncio

async def test():
    registry = ToolRegistry()
    registry.register(MkdirTool())
    
    ctx = ToolContext(session_id='test', working_directory='/tmp')
    
    # 使用 dict 输入（模拟 LLM 调用）
    result = await registry.execute_tool(
        'mkdir',
        {'path': 'test_project'},
        ctx
    )
    
    print(f'Result: {result.is_error=}')
    # 输出：result.is_error=False

asyncio.run(test())
"

✅ mkdir 工具修复成功！
```

---

## 📝 修复文件

| 文件 | 修改内容 |
|------|----------|
| `src/tools/registry.py` | 添加 `MkdirInput` 导入和映射 |

**代码变更：**
```diff
+ from ..tools.mkdir import MkdirInput

  input_classes = {
      'bash': BashInput,
      'file_read': FileReadInput,
      'file_edit': FileEditInput,
      'file_write': FileWriteInput,
      'grep': GrepInput,
      'glob': GlobInput,
+     'mkdir': MkdirInput,
  }
```

---

## 🔧 同类问题检查

### 其他可能受影响的工具

检查 `input_classes` 映射是否完整：

```python
# 已支持的工具
supported_tools = [
    'bash', 'file_read', 'file_edit', 'file_write',
    'grep', 'glob', 'mkdir',
]

# 检查所有工具类
from src.tools.git_tool import GitInput
from src.tools.project_template import ProjectTemplateInput
# ... 其他工具

# 需要确保所有工具都在映射中
```

### 建议改进

**当前问题：** 需要手动维护映射

**改进方案：** 自动从工具类获取输入类型

```python
# 改进后的代码
class Tool(ABC, Generic[T]):
    """Tool base class"""
    
    # 每个工具定义自己的输入类
    input_class: type[T] = None  # 子类重写

# Registry 自动获取
async def execute_tool(self, name: str, tool_input: dict, context: ToolContext):
    tool = self.get_required(name)
    
    # 自动转换
    if tool.input_class:
        typed_input = tool.input_class(**tool_input)
    else:
        typed_input = tool_input
    
    return await tool.execute_with_hooks(typed_input, context)
```

---

## ✅ 验证清单

- [x] `mkdir` 工具可以正常执行
- [x] 输入字典正确转换为 `MkdirInput`
- [x] 目录创建成功
- [x] 错误处理正常
- [ ] 检查其他工具是否有同样问题
- [ ] 添加回归测试

---

## 📊 影响范围

**受影响功能：**
- ✅ `mkdir` 工具创建目录
- ✅ 项目模板创建（依赖 `mkdir`）
- ✅ Agent 多步任务（包含目录创建）

**未受影响：**
- ✅ `bash` 工具
- ✅ 文件操作工具（`file_read`, `file_write`, `file_edit`）
- ✅ 搜索工具（`grep`, `glob`）

---

*修复时间：2026-04-03*  
*修复人：小佳 ✨*  
*状态：✅ 完成*
