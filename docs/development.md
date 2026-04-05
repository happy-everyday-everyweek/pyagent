# PyAgent 开发文�?v0.8.0

本文档为开发者提供PyAgent v0.8.0的开发指南�?
## 目录

- [开发环境搭建](#开发环境搭�?
- [代码规范](#代码规范)
- [模块开发指南](#模块开发指�?
- [测试](#测试)
- [调试技巧](#调试技�?
- [版本信息](#版本信息)

## 开发环境搭�?
### 1. 克隆项目

```bash
git clone <repository-url>
cd pyagent
```

### 2. 创建开发环�?
```bash
python -m venv venv-dev
source venv-dev/bin/activate  # Linux/Mac
# �?venv-dev\Scripts\activate  # Windows
```

### 3. 安装开发依�?
```bash
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 4. 安装预提交钩�?
```bash
pre-commit install
```

### 5. 配置IDE

#### VSCode 配置

创建 `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv-dev/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## 代码规范

### 1. Python代码规范

项目使用Ruff进行代码格式化和检查：

```bash
# 格式化代�?ruff format .

# 检查代�?ruff check .

# 自动修复
ruff check . --fix
```

### 2. 类型注解

所有函数必须添加类型注解：

```python
from typing import Optional, Dict, Any

def process_message(
    message: str,
    user_id: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """处理消息�?    
    Args:
        message: 消息内容
        user_id: 用户ID
        context: 上下文信�?        
    Returns:
        处理结果
    """
    pass
```

### 3. 文档字符�?
使用Google风格的文档字符串�?
```python
def complex_function(param1: int, param2: str) -> bool:
    """函数简短描述�?    
    详细描述函数的功能、使用场景和注意事项�?    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说�?        
    Raises:
        ValueError: 当参数无效时
        RuntimeError: 当运行时错误�?        
    Example:
        >>> complex_function(1, "test")
        True
    """
    pass
```

### 4. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划�?| `chat_agent.py` |
| �?| 大驼�?| `ChatAgent` |
| 函数 | 小写+下划�?| `send_message()` |
| 常量 | 大写+下划�?| `MAX_RETRY_COUNT` |
| 私有 | 前缀下划�?| `_internal_func()` |

---

## 模块开发指�?
### 1. 创建自定义工�?
工具必须继承 `UnifiedTool`�?
```python
# src/executor/tools/my_tool.py
from typing import Any, Dict
from .base import BaseTool

class MyTool(BaseTool):
    """我的自定义工具�?    
    详细描述工具的功能和使用场景�?    """
    
    name = "my_tool"
    description = "工具简短描�?
    parameters = {
        "param1": "参数1说明",
        "param2": "参数2说明（可选）"
    }
    
    async def execute(self, param1: str, param2: int = 0) -> str:
        """执行工具�?        
        Args:
            param1: 参数1
            param2: 参数2，默认为0
            
        Returns:
            执行结果字符�?            
        Raises:
            ValueError: 参数验证失败
            RuntimeError: 执行失败
        """
        # 参数验证
        if not param1:
            raise ValueError("param1不能为空")
        
        # 执行逻辑
        result = self._do_something(param1, param2)
        
        return f"处理结果: {result}"
    
    def _do_something(self, p1: str, p2: int) -> Any:
        """内部辅助方法�?""
        pass
```

注册工具�?
```python
# src/executor/tools/__init__.py
from .my_tool import MyTool

__all__ = ["MyTool", ...]
```

### 2. 创建IM适配�?
适配器必须继�?`BaseIMAdapter`�?
```python
# src/im/my_platform.py
from typing import Any, Dict, Optional
from .base import BaseIMAdapter, IMMessage, IMReply, IMUser, MessageType, ChatType

class MyPlatformAdapter(BaseIMAdapter):
    """我的平台适配器�?""
    
    platform = "my_platform"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self._client = None
    
    async def connect(self) -> bool:
        """连接到平台�?""
        try:
            self._client = MyPlatformClient(
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            await self._client.connect()
            self._connected = True
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    async def disconnect(self) -> None:
        """断开连接�?""
        if self._client:
            await self._client.disconnect()
        self._connected = False
    
    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        """发送消息�?""
        try:
            await self._client.send_text(
                chat_id=chat_id,
                content=reply.content
            )
            return True
        except Exception as e:
            self.logger.error(f"发送失�? {e}")
            return False
    
    async def get_user_info(self, user_id: str) -> Optional[IMUser]:
        """获取用户信息�?""
        try:
            user_data = await self._client.get_user(user_id)
            return IMUser(
                user_id=user_id,
                name=user_data.get("name", ""),
                nickname=user_data.get("nickname", "")
            )
        except Exception:
            return None
    
    async def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """获取聊天信息�?""
        # 实现获取聊天信息逻辑
        pass
    
    async def _handle_incoming_message(self, raw_message: Dict[str, Any]) -> None:
        """处理收到的消息�?""
        message = IMMessage(
            message_id=raw_message["id"],
            platform=self.platform,
            chat_id=raw_message["chat_id"],
            chat_type=ChatType.GROUP if raw_message["is_group"] else ChatType.PRIVATE,
            sender=IMUser(
                user_id=raw_message["sender_id"],
                name=raw_message["sender_name"]
            ),
            content=raw_message["content"],
            message_type=MessageType.TEXT,
            timestamp=raw_message["timestamp"]
        )
        
        await self._dispatch_message(message)
```

### 3. 创建子Agent

子Agent必须继承 `BaseSubAgent`�?
```python
# src/executor/sub_agents/my_agent.py
from typing import Any, Dict
from .base_sub_agent import BaseSubAgent

class MySubAgent(BaseSubAgent):
    """我的子Agent�?    
    专门处理某类特定任务�?    """
    
    name = "my_sub_agent"
    description = "子Agent描述"
    capabilities = ["task_type_1", "task_type_2"]
    
    def __init__(self, llm_client: Any = None, config: Dict[str, Any] = None):
        super().__init__(llm_client, config)
        self.max_iterations = config.get("max_iterations", 5)
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行任务�?        
        Args:
            task: 任务描述
            context: 上下文信�?            
        Returns:
            执行结果
        """
        # 1. 分析任务
        analysis = await self._analyze_task(task)
        
        # 2. 制定计划
        plan = await self._create_plan(analysis)
        
        # 3. 执行计划
        result = await self._execute_plan(plan, context)
        
        return result
    
    async def _analyze_task(self, task: str) -> Dict[str, Any]:
        """分析任务�?""
        # 实现任务分析逻辑
        pass
    
    async def _create_plan(self, analysis: Dict[str, Any]) -> list:
        """创建执行计划�?""
        # 实现计划创建逻辑
        pass
    
    async def _execute_plan(self, plan: list, context: Dict[str, Any]) -> str:
        """执行计划�?""
        # 实现计划执行逻辑
        pass
```

### 4. 创建技�?
技能目录结构：

```
skills/my_skill/
├── SKILL.md          # 技能定�?├── scripts/          # 脚本目录
�?  ├── setup.py      # 安装脚本
�?  ├── run.py        # 运行脚本
�?  └── utils.py      # 工具模块
└── resources/        # 资源文件
    └── template.txt
```

SKILL.md 示例�?
```markdown
# My Skill

## Metadata
- Name: my_skill
- Version: 1.0.0
- Author: Your Name
- SupportedOS: [win32, linux, darwin]

## Description
这是一个示例技能，演示如何创建自定义技能�?
## Requirements
- Python 3.10+
- requests

## Usage
```python
from skills import skill_loader

result = skill_loader.run_script("my_skill", "run.py", ["arg1", "arg2"])
```

## Scripts
- setup: scripts/setup.py
- run: scripts/run.py
- test: scripts/test.py

## API

### run.py
参数:
- input: 输入文件路径
- output: 输出文件路径
- format: 输出格式 (json, csv)

返回�?
- 成功: {"status": "success", "data": ...}
- 失败: {"status": "error", "message": ...}
```

---

## 测试

### 1. 运行测试

```bash
# 运行所有测�?pytest

# 运行特定测试
pytest tests/test_llm_client.py

# 运行带覆盖率
pytest --cov=src --cov-report=html

# 运行特定标记的测�?pytest -m "not slow"
```

### 2. 编写测试

```python
# tests/test_my_module.py
import pytest
from src.my_module import MyClass

class TestMyClass:
    """MyClass测试类�?""
    
    @pytest.fixture
    def instance(self):
        """创建测试实例�?""
        return MyClass(config={"test": True})
    
    def test_initialization(self, instance):
        """测试初始化�?""
        assert instance.config["test"] is True
    
    def test_process(self, instance):
        """测试处理方法�?""
        result = instance.process("input")
        assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_method(self, instance):
        """测试异步方法�?""
        result = await instance.async_process("input")
        assert result is not None
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_multiple_cases(self, instance, input, expected):
        """测试多个案例�?""
        result = instance.process(input)
        assert result == expected
```

### 3. Mock使用

```python
from unittest.mock import Mock, patch, AsyncMock

# Mock函数
with patch("src.module.external_api") as mock_api:
    mock_api.return_value = {"status": "ok"}
    result = my_function()
    assert result == "ok"

# Mock异步函数
with patch("src.module.async_function") as mock_async:
    mock_async.return_value = AsyncMock(return_value="result")
    result = await my_async_function()
    assert result == "result"

# Mock对象
mock_client = Mock()
mock_client.send_message.return_value = True
mock_client.get_user_info.return_value = {"name": "Test"}
```

---

## 调试技�?
### 1. 日志调试

```python
import logging

logger = logging.getLogger(__name__)

# 不同级别的日�?logger.debug("调试信息: %s", variable)
logger.info("普通信�?)
logger.warning("警告信息")
logger.error("错误信息")
logger.exception("异常信息")  # 自动包含堆栈
```

### 2. 断点调试

使用pdb�?
```python
import pdb; pdb.set_trace()

# 常用命令
# n - 下一�?# s - 进入函数
# c - 继续执行
# p variable - 打印变量
# l - 显示代码
# q - 退�?```

使用ipdb（推荐）�?
```python
import ipdb; ipdb.set_trace()
```

### 3. 异步调试

```python
import asyncio

async def debug_async():
    # 在异步函数中设置断点
    await some_async_operation()
    import ipdb; ipdb.set_trace()
    await another_operation()

# 运行
asyncio.run(debug_async())
```

### 4. 性能分析

```python
import cProfile
import pstats

# 分析代码
profiler = cProfile.Profile()
profiler.enable()

# 要分析的代码
my_function()

profiler.disable()

# 输出结果
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # 显示�?0�?```

### 5. 内存分析

```python
from memory_profiler import profile

@profile
def my_function():
    # 函数代码
    large_list = [i for i in range(1000000)]
    return large_list

# 运行
my_function()
```

---

## 提交规范

### Commit Message格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型�?- **feat**: 新功�?- **fix**: 修复
- **docs**: 文档
- **style**: 格式
- **refactor**: 重构
- **test**: 测试
- **chore**: 构建/工具

示例�?
```
feat(chat): 添加消息撤回功能

- 实现消息撤回API
- 添加撤回权限检�?- 更新文档

Closes #123
```

### 分支管理

- **main**: 主分支，稳定版本
- **develop**: 开发分�?- **feature/***: 功能分支
- **bugfix/***: 修复分支
- **release/***: 发布分支

---

## 版本信息

### 当前版本: v0.8.0

**发布日期**: 2026-04-01

**主要变更**:
- 重构域管理API路由，消除重复实�?- 实现数据持久化，服务重启后数据不再丢�?- 统一数据模型，提升代码质�?- 通过 ruff �?mypy 代码检�?
**兼容�?*:
- 完全兼容 v0.7.x 的配置文�?- API接口保持向后兼容
- 数据格式自动迁移

### 版本历史

| 版本 | 发布日期 | 主要特�?|
|------|----------|----------|
| v0.8.0 | 2026-04-01 | 重构域管理API路由、实现数据持久化 |
| v0.7.1 | 2026-03-30 | 修复LLM模块问题、完善Anthropic适配�?|
| v0.7.0 | 2026-03-30 | 原生文档编辑器、原生视频编辑器、域系统 |
| v0.6.0 | 2025-03-29 | LLM分级模型架构、设备ID系统 |

---

## 相关文档

- [架构文档](architecture.md) - 系统架构设计
- [API文档](api.md) - API接口文档
- [配置说明](configuration.md) - 配置文件说明
- [部署文档](deployment.md) - 部署指南
- [域系统文档](modules/domain-system.md) - 域系统详细说�?
