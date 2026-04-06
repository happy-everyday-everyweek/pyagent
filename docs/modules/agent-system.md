# 智能体系统文档 v0.9.9

本文档详细描述PyAgent v0.9.9智能体系统的设计和实现。

## 概述

智能体系统是PyAgent v0.8.0引入的核心功能，提供统一的Agent管理、注册、执行能力。支持声明式Agent定义、自动任务分配、多Agent协作等高级特性。

v0.9.9 新增编码类垂类智能体，基于 Claw Code 架构移植。

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    智能体系统架构                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌───────────┐ │
│  │   Agent     │────→│   Agent     │────→│   Agent   │ │
│  │   Registry  │     │   Executor  │     │   Base    │ │
│  │             │     │             │     │           │ │
│  │ - 注册      │     │ - 调度      │     │ - 抽象基类 │ │
│  │ - 发现      │     │ - 执行      │     │ - 能力声明 │ │
│  │ - 管理      │     │ - 监控      │     │ - 生命周期 │ │
│  └─────────────┘     └─────────────┘     └───────────┘ │
│         │                   │                          │
│         └───────────────────┼───────────────────┐      │
│                             ▼                   ▼      │
│                    ┌─────────────────┐  ┌───────────┐  │
│                    │   Agent A       │  │  Agent B  │  │
│                    │   (数据分析)     │  │  (搜索)   │  │
│                    └─────────────────┘  └───────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              垂类智能体 (v0.9.9)                  │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐    │   │
│  │  │  Coding   │  │ Financial │  │  Screen   │    │   │
│  │  │  Agent    │  │  Agent    │  │ Operation │    │   │
│  │  │ (编码)    │  │  (金融)   │  │  (屏幕)   │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### Agent基类

**文件**: `src/agents/base.py`

所有Agent必须继承的抽象基类：

```python
from abc import ABC, abstractmethod
from typing import Any

class Agent(ABC):
    """Agent抽象基类"""
    
    def __init__(
        self,
        name: str,
        description: str,
        capabilities: list[str] = None
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.status = AgentStatus.IDLE
    
    @abstractmethod
    async def execute(self, task: dict[str, Any]) -> AgentResult:
        """执行任务"""
        pass
    
    @abstractmethod
    async def can_handle(self, task: dict[str, Any]) -> bool:
        """判断是否能处理任务"""
        pass
```

### Agent注册中心

**文件**: `src/agents/registry.py`

管理所有Agent的注册、发现和执行：

```python
class AgentRegistry:
    """Agent注册中心"""
    
    def __init__(self):
        self._agents: dict[str, Agent] = {}
        self._executor = AgentExecutor()
    
    def register(self, agent: Agent) -> bool:
        """注册Agent"""
        if agent.name in self._agents:
            return False
        self._agents[agent.name] = agent
        return True
    
    def unregister(self, name: str) -> bool:
        """注销Agent"""
        if name not in self._agents:
            return False
        del self._agents[name]
        return True
    
    def get_agent(self, name: str) -> Agent | None:
        """获取Agent"""
        return self._agents.get(name)
    
    def list_agents(self) -> list[AgentInfo]:
        """列出所有Agent"""
        return [
            AgentInfo(
                name=agent.name,
                description=agent.description,
                capabilities=agent.capabilities,
                status=agent.status
            )
            for agent in self._agents.values()
        ]
    
    def find_agents_by_capability(
        self,
        capability: str
    ) -> list[Agent]:
        """根据能力查找Agent"""
        return [
            agent for agent in self._agents.values()
            if capability in agent.capabilities
        ]
    
    async def execute(
        self,
        agent_name: str,
        task: dict[str, Any]
    ) -> AgentResult:
        """执行Agent任务"""
        agent = self.get_agent(agent_name)
        if not agent:
            return AgentResult(
                success=False,
                error=f"Agent '{agent_name}' not found"
            )
        return await self._executor.execute(agent, task)
```

### Agent执行器

**文件**: `src/agents/executor.py`

负责任务调度和执行：

```python
class AgentExecutor:
    """Agent执行器"""
    
    def __init__(self):
        self._running_tasks: dict[str, TaskInfo] = {}
        self._max_concurrent = 10
    
    async def execute(
        self,
        agent: Agent,
        task: dict[str, Any]
    ) -> AgentResult:
        """执行Agent任务"""
        # 检查Agent是否能处理任务
        if not await agent.can_handle(task):
            return AgentResult(
                success=False,
                error="Agent cannot handle this task"
            )
        
        # 执行任务
        task_id = generate_task_id()
        self._running_tasks[task_id] = TaskInfo(
            id=task_id,
            agent_name=agent.name,
            status=TaskStatus.RUNNING
        )
        
        try:
            agent.status = AgentStatus.BUSY
            result = await agent.execute(task)
            self._running_tasks[task_id].status = TaskStatus.COMPLETED
            return result
        except Exception as e:
            self._running_tasks[task_id].status = TaskStatus.FAILED
            return AgentResult(success=False, error=str(e))
        finally:
            agent.status = AgentStatus.IDLE
            del self._running_tasks[task_id]
```

## 使用示例

### 创建自定义Agent

```python
from src.agents import Agent, AgentResult

class DataAnalysisAgent(Agent):
    """数据分析Agent"""
    
    def __init__(self):
        super().__init__(
            name="data_analyzer",
            description="数据分析Agent，支持数据清洗、统计分析、可视化",
            capabilities=[
                "data_analysis",
                "data_cleaning",
                "statistical_analysis",
                "visualization"
            ]
        )
    
    async def can_handle(self, task: dict) -> bool:
        """判断是否能处理任务"""
        task_type = task.get("type")
        return task_type in ["data_analysis", "visualization"]
    
    async def execute(self, task: dict) -> AgentResult:
        """执行任务"""
        try:
            data = task.get("data")
            analysis_type = task.get("analysis_type")
            
            if analysis_type == "statistical":
                result = await self._statistical_analysis(data)
            elif analysis_type == "visualization":
                result = await self._create_visualization(data)
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown analysis type: {analysis_type}"
                )
            
            return AgentResult(success=True, data=result)
        except Exception as e:
            return AgentResult(success=False, error=str(e))
    
    async def _statistical_analysis(self, data):
        # 统计分析逻辑
        pass
    
    async def _create_visualization(self, data):
        # 可视化逻辑
        pass
```

### 注册和使用Agent

```python
from src.agents import AgentRegistry

# 获取注册中心
registry = AgentRegistry()

# 创建并注册Agent
agent = DataAnalysisAgent()
registry.register(agent)

# 列出所有Agent
agents = registry.list_agents()
for agent_info in agents:
    print(f"{agent_info.name}: {agent_info.description}")

# 执行Agent任务
result = await registry.execute(
    agent_name="data_analyzer",
    task={
        "type": "data_analysis",
        "data": sales_data,
        "analysis_type": "statistical"
    }
)

if result.success:
    print(f"分析结果: {result.data}")
else:
    print(f"执行失败: {result.error}")
```

### 根据能力查找Agent

```python
# 查找具有数据分析能力的Agent
agents = registry.find_agents_by_capability("data_analysis")

# 选择第一个能处理任务的Agent
for agent in agents:
    if await agent.can_handle(task):
        result = await registry.execute(agent.name, task)
        break
```

## API接口

### 列出Agent

```http
GET /api/agents
```

**响应**:
```json
{
  "agents": [
    {
      "name": "data_analyzer",
      "description": "数据分析Agent",
      "capabilities": ["data_analysis", "visualization"],
      "status": "idle"
    }
  ]
}
```

### 执行Agent

```http
POST /api/agents/{agent_name}/execute
Content-Type: application/json

{
  "type": "data_analysis",
  "data": {...},
  "analysis_type": "statistical"
}
```

**响应**:
```json
{
  "success": true,
  "data": {...}
}
```

### 获取Agent详情

```http
GET /api/agents/{agent_name}
```

## 配置

### agents.yaml

```yaml
# config/agents.yaml

agents:
  # 内置Agent
  built_in:
    - name: data_analyzer
      enabled: true
    - name: web_searcher
      enabled: true
  
  # 自定义Agent路径
  custom_paths:
    - "custom_agents/"
  
  # 执行配置
  execution:
    max_concurrent: 10
    timeout: 300
    retry_count: 3
```

## 最佳实践

1. **能力声明**: 准确声明Agent的能力，便于任务匹配
2. **错误处理**: 在execute方法中捕获所有异常
3. **状态管理**: 正确更新Agent状态（IDLE/BUSY）
4. **任务验证**: 在can_handle中充分验证任务可行性
5. **日志记录**: 记录Agent执行日志，便于调试

## 垂类智能体 (v0.9.9)

### 编码智能体 (CodingAgent)

**文件**: `src/agents/coding.py`

基于 Claw Code 架构移植的专业编码助手，提供代码编写、分析、执行和调试能力。

#### 核心组件

**1. SystemPromptBuilder - 系统提示词构建器**

```python
from src.agents.coding import SystemPromptBuilder

builder = SystemPromptBuilder()
builder.with_os("Windows", "11")
builder.with_project_context(context)

system_prompt = builder.render()
```

**2. ProjectContext - 项目上下文发现**

自动发现项目上下文信息：
- CLAW.md 指令文件
- Git 状态和差异
- 工作目录

```python
from src.agents.coding import ProjectContext

context = ProjectContext.discover_with_git(
    cwd="/path/to/project",
    current_date="2026-04-06"
)

print(context.git_status)
print(context.instruction_files)
```

**3. CodingAgent - 编码智能体**

```python
from src.agents.coding import CodingAgent, coding_agent

# 使用全局实例
result = await coding_agent.handle("read_file", {"path": "main.py"})

# 或创建新实例
agent = CodingAgent()
agent.set_working_directory("/path/to/project")
```

#### 支持的操作

| 操作 | 描述 | 参数 |
|------|------|------|
| `read_file` | 读取文件 | `path` |
| `write_file` | 写入文件 | `path`, `content` |
| `edit_file` | 编辑文件 | `path`, `old_str`, `new_str` |
| `execute_command` | 执行命令 | `command`, `timeout` |
| `git_status` | Git 状态 | - |
| `git_commit` | Git 提交 | `message` |
| `git_branch` | Git 分支 | `action`, `name` |
| `search_code` | 搜索代码 | `pattern`, `path` |
| `analyze_code` | 分析代码 | `code`, `language` |
| `run_tests` | 运行测试 | `path`, `framework` |

#### CLAW.md 指令文件

在项目根目录创建 `CLAW.md` 文件，编码智能体会自动加载：

```markdown
# Project Instructions

## Code Style
- Use 4 spaces for indentation
- Maximum line length: 100 characters

## Testing
- Run tests before committing
- Minimum coverage: 80%

## Git
- Use conventional commits
- Branch naming: feature/, hotfix/, release/
```

### 金融智能体 (FinancialAgent)

**文件**: `src/agents/financial.py`

专业的金融分析智能体，支持股票分析、财务报表分析、风险评估等。

详见 [金融智能体文档](./financial-agent.md)。

## 手机端增强模块 (v0.9.9)

### 验证码提取器

**文件**: `src/mobile/verification_code.py`

从通知中自动提取验证码：

```python
from src.mobile.verification_code import verification_code_extractor

result = verification_code_extractor.extract(
    text="您的验证码是 123456，5分钟内有效",
    package_name="com.android.mms"
)

print(result.code)  # "123456"
print(result.expires_in)  # 300 (秒)
```

### 通知分类器

**文件**: `src/mobile/notification_classifier.py`

智能分类通知并评估重要性：

```python
from src.mobile.notification_classifier import notification_classifier
from src.mobile.notification import Notification

notification = Notification(...)
classified = notification_classifier.classify(notification)

print(classified.importance)  # CRITICAL, HIGH, NORMAL, LOW, SPAM
print(classified.keywords)
print(classified.entities)
```

### 自动回复管理器

**文件**: `src/mobile/auto_reply.py`

管理通知的自动回复：

```python
from src.mobile.auto_reply import auto_reply_manager

# 启用自动回复
auto_reply_manager.enable()

# 添加白名单
auto_reply_manager.whitelist.add("com.tencent.mm")

# 添加回复模板
from src.mobile.auto_reply import ReplyTemplate
template = ReplyTemplate(
    name="busy",
    template="我现在有点忙，稍后回复你。",
    keywords=["在吗", "忙吗"]
)
auto_reply_manager.add_template(template)

# 回复通知
record = await auto_reply_manager.reply(notification)
```

### 代码执行沙箱

**文件**: `src/mobile/code_sandbox.py`

安全的代码执行环境：

```python
from src.mobile.code_sandbox import code_sandbox

# 执行 Shell 命令
result = await code_sandbox.execute_shell("ls -la")
print(result.stdout)

# 执行 Python 代码
result = await code_sandbox.execute_python("print('Hello, World!')")

# 危险命令检测
allowed, reason = code_sandbox.check_command("rm -rf /")
print(allowed)  # False
```

### 手势执行器

**文件**: `src/mobile/gesture_executor.py`

低延迟的屏幕手势操作：

```python
from src.mobile.gesture_executor import gesture_executor

# 初始化
await gesture_executor.initialize()

# 执行手势
result = await gesture_executor.tap(500, 800)
result = await gesture_executor.swipe(100, 500, 400, 500)
result = await gesture_executor.scroll_down(1080, 1920)

# 截图
screenshot = await gesture_executor.capture_screen()
```

**特性**:
- 手势执行延迟：50-300ms
- 节点缓存 TTL：500ms
- 支持多种手势：点击、双击、长按、滑动、缩放、滚动
- 整合 `ScreenTools` 提供统一接口
