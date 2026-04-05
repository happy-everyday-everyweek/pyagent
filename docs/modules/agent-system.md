# 智能体系统文档 v0.8.0

本文档详细描述PyAgent v0.8.0智能体系统的设计和实现。

## 概述

智能体系统是PyAgent v0.8.0引入的核心功能，提供统一的Agent管理、注册、执行能力。支持声明式Agent定义、自动任务分配、多Agent协作等高级特性。

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
