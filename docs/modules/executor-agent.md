# 执行模块文档 v0.8.0

本文档详细描述PyAgent v0.8.0执行模块（原Executor Agent）的设计和实现�?
## 概述

Executor Agent是PyAgent系统中负责执行具体任务的模块。它采用ReAct推理引擎，支持复杂的多步骤任务执行和子Agent协作�?
## 核心组件

### 1. ExecutorAgent (执行Agent)

**文件**: `src/executor/executor_agent.py`

**职责**: 负责任务执行的入口，管理同步/异步执行模式�?
#### 执行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| SYNC | 同步执行 | 简单任务、需要立即返�?|
| ASYNC | 异步执行 | 复杂任务、长时间运行 |

#### 主要方法

```python
class ExecutorAgent:
    async def execute_sync(self, task: str, timeout: int = None) -> str:
        """同步执行任务，阻塞直到完成�?""
        pass
    
    async def submit_async_task(self, task: str) -> str:
        """提交异步任务，返回任务ID�?""
        pass
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取异步任务状态�?""
        pass
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消异步任务�?""
        pass
```

#### 代码示例

```python
from src.executor.executor_agent import ExecutorAgent
from src.llm import create_client_from_env
from src.executor.tools.registry import ToolRegistry
from src.executor.tools.shell_tool import ShellTool

# 初始�?llm_client = create_client_from_env()
tool_registry = ToolRegistry()
tool_registry.register(ShellTool())

executor = ExecutorAgent(
    llm_client=llm_client,
    tool_registry=tool_registry
)

# 同步执行
result = await executor.execute_sync("查询当前目录文件")
print(result)

# 异步执行
task_id = await executor.submit_async_task("分析日志文件")
print(f"任务ID: {task_id}")

# 查询状�?status = await executor.get_task_status(task_id)
print(f"状�? {status['status']}")

# 取消任务
await executor.cancel_task(task_id)
```

---

### 2. ReActEngine (ReAct推理引擎)

**文件**: `src/executor/react_engine.py`

**职责**: 实现Think-Act-Observe三阶段显式推理循环�?
#### 推理循环

```
┌─────────────────────────────────────────────────────────────�?�?                   ReAct 推理循环                            �?├─────────────────────────────────────────────────────────────�?�?                                                            �?�? 初始�?                                                    �?�?   �?                                                       �?�?   �?                                                       �?�? ┌─────────────�?                                          �?�? �?  Think     �?◄─────────────────────────────�?          �?�? �?  思�?     �?                              �?          �?�? �? - 分析任务 �?                              �?          �?�? �? - 制定计划 �?                              �?          �?�? �? - 选择工具 �?                              �?          �?�? └──────┬──────�?                              �?          �?�?        �?                                     �?          �?�?        �?                                     �?          �?�? ┌─────────────�?                              �?          �?�? �?   Act      �?                              �?          �?�? �?  行动      �?                              �?          �?�? �? - 调用工具 �?                              �?          �?�? �? - 执行操作 �?                              �?          �?�? └──────┬──────�?                              �?          �?�?        �?                                     �?          �?�?        �?                                     �?          �?�? ┌─────────────�?                              �?          �?�? �? Observe    �?                              �?          �?�? �?  观察      �?                              �?          �?�? �? - 收集结果 �?                              �?          �?�? �? - 分析反馈 �?                              �?          �?�? └──────┬──────�?                              �?          �?�?        �?                                     �?          �?�?        �?是否完成�?                           �?          �?�?        ├───────── �?──────�?返回结果         �?          �?�?        �?�?                                  �?          �?�?        └──────────────────────────────────────�?          �?�?                     (循环直到完成)                          �?�?                                                            �?└─────────────────────────────────────────────────────────────�?```

#### 安全机制

1. **循环检�?*: 检测是否陷入无限循�?2. **工具抖动检�?*: 防止重复调用同一工具
3. **最大迭代限�?*: 默认最�?0次迭�?
#### 配置选项

```python
react_engine = ReActEngine(
    llm_client=llm_client,
    tool_registry=tool_registry,
    config={
        "max_iterations": 10,
        "max_tool_calls_per_step": 3,
        "enable_loop_detection": True,
        "enable_tool_jitter_detection": True
    }
)
```

---

### 3. TaskQueue (任务队列)

**文件**: `src/executor/task_queue.py`

**职责**: 管理异步任务的队列�?
#### 任务状�?
```python
class TaskStatus(Enum):
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 执行�?    COMPLETED = "completed"   # 已完�?    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取�?```

#### 功能特�?
- 任务优先�?- 并发控制
- 超时处理
- 回调通知

---

### 4. 子Agent系统

#### 4.1 BaseSubAgent (子Agent基类)

**文件**: `src/executor/sub_agents/base_sub_agent.py`

```python
class BaseSubAgent(ABC):
    """子Agent基类�?""
    
    name: str = ""
    description: str = ""
    capabilities: List[str] = []
    
    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行任务�?""
        pass
```

#### 4.2 BrowserAgent (浏览器Agent)

**文件**: `src/execution/sub_agents/browser_agent.py`

**功能**: 浏览器自动化操作

- 网页浏览
- 元素点击
- 表单填写
- 内容提取

```python
browser_agent = BrowserAgent(llm_client=llm_client)

# 浏览网页
result = await browser_agent.execute(
    "访问 https://example.com 并提取标�?
)
```

#### 4.3 SearchAgent (搜索Agent)

**文件**: `src/executor/sub_agents/search_agent.py`

**功能**: 网络搜索和信息汇�?
- 多引擎搜�?- 结果去重
- 信息摘要

```python
search_agent = SearchAgent(llm_client=llm_client)

# 搜索信息
result = await search_agent.execute(
    "搜索Python最新版本信�?
)
```

---

## 工具系统

### 1. BaseTool (工具基类)

**文件**: `src/executor/tools/base.py`

```python
class BaseTool(ABC):
    """工具基类�?""
    
    name: str = ""
    description: str = ""
    parameters: Dict[str, str] = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行工具�?""
        pass
```

### 2. 内置工具

| 工具 | 文件 | 功能 |
|------|------|------|
| ShellTool | shell_tool.py | 执行shell命令 |
| FileReadTool | file_tools.py | 读取文件 |
| FileWriteTool | file_tools.py | 写入文件 |
| FileListTool | file_tools.py | 列出目录 |
| WebRequestTool | web_tools.py | HTTP请求 |
| WebFetchTool | web_tools.py | 获取网页内容 |

### 3. 工具注册�?
**文件**: `src/executor/tools/registry.py`

```python
from src.executor.tools.registry import ToolRegistry

# 创建注册�?registry = ToolRegistry()

# 注册工具
registry.register(ShellTool())
registry.register(FileReadTool())

# 获取工具
tool = registry.get_tool("shell")

# 列出所有工�?tools = registry.list_tools()
```

---

## 配置选项

```yaml
# config/executor.yaml
executor:
  react_engine:
    max_iterations: 10         # 最大迭代次�?    max_tool_calls_per_step: 3 # 每步最大工具调用数
    enable_loop_detection: true
    enable_tool_jitter_detection: true
    
  task_queue:
    max_concurrent_tasks: 5    # 最大并发任务数
    default_timeout: 300       # 默认超时时间(�?
    
  sub_agents:
    browser:
      headless: true           # 无头模式
      timeout: 30              # 页面加载超时
    search:
      engines: ["google", "bing"]
      max_results: 10
```

---

## 扩展开�?
### 创建自定义工�?
```python
from src.executor.tools.base import BaseTool

class DatabaseTool(BaseTool):
    """数据库查询工具�?""
    
    name = "database"
    description = "执行SQL查询"
    parameters = {
        "query": "SQL查询语句",
        "database": "数据库名�?
    }
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        self._connection = None
    
    async def execute(self, query: str, database: str = "default") -> str:
        """执行SQL查询�?""
        # 连接数据�?        if not self._connection:
            self._connection = await self._connect()
        
        # 执行查询
        try:
            result = await self._connection.execute(query)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return f"查询失败: {str(e)}"
    
    async def _connect(self):
        # 实现连接逻辑
        pass
```

### 创建自定义子Agent

```python
from src.execution.sub_agents.base_sub_agent import BaseSubAgent

class DataAnalysisAgent(BaseSubAgent):
    """数据分析子Agent�?""
    
    name = "data_analysis"
    description = "专门进行数据分析"
    capabilities = ["data_cleaning", "statistical_analysis", "visualization"]
    
    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """执行数据分析任务�?""
        # 1. 理解分析需�?        requirements = await self._parse_requirements(task)
        
        # 2. 获取数据
        data = await self._load_data(requirements["data_source"])
        
        # 3. 数据清洗
        cleaned_data = await self._clean_data(data)
        
        # 4. 执行分析
        results = await self._analyze(cleaned_data, requirements["analysis_type"])
        
        # 5. 生成报告
        report = await self._generate_report(results)
        
        return report
```

---

## 性能优化

### 1. 并发控制

```python
# 限制并发任务�?executor = ExecutorAgent(
    config={
        "max_concurrent_tasks": 5
    }
)
```

### 2. 超时控制

```python
# 设置任务超时
result = await executor.execute_sync(
    task="复杂任务",
    timeout=60  # 60秒超�?)
```

### 3. 工具缓存

```python
# 缓存工具结果
class CachedTool(BaseTool):
    def __init__(self):
        self._cache = {}
    
    async def execute(self, **kwargs) -> str:
        cache_key = json.dumps(kwargs, sort_keys=True)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await self._do_execute(**kwargs)
        self._cache[cache_key] = result
        
        return result
```
