# æ§è¡æ¨¡åææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»æè¿°PyAgent v0.8.0æ§è¡æ¨¡åçè®¾è®¡åå®ç°ï¼åæ¬ä»»å¡æ¦å¿µãåç¶æç³»ç»ãè§åæºè½ä½åå¤æºè½ä½åä½æ¨¡å¼ã?
## æ¦è¿°

æ§è¡æ¨¡åæ¯PyAgentçæ ¸å¿ç»ä»¶ï¼è´è´£ä»»å¡çæ§è¡åç®¡çï¼?- **ä»»å¡(Task)**: æå°ä¸ä¸æåä½ï¼åå«æ§è¡æéçææä¿¡æ?- **åç¶æç³»ç»?*: æ´»è·ãæåãå¼å¸¸ãç­å¾ï¼ç²¾ç»æ§å¶ä»»å¡çå½å¨æ
- **è§åæºè½ä½?PlannerAgent)**: è´è´£ä»»å¡åè§£åæºè½ä½åé
- **å¤æºè½ä½åä½æ¨¡å¼**: å¹¶è¡/ä¸²è¡/æ··åæ§è¡
- **æéåæ¢**: èªå¨éè¯åæºè½ä½åæ¢æºå¶

## æ¶æè®¾è®¡

```
âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?â?                    æ§è¡æ¨¡åæ¶æ                                 â?âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?â?                                                                â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â? â?                 è§åæºè½ä½?(PlannerAgent)                â?  â?â? â?                                                        â?  â?â? â? èè´£: è´è´£ä»»å¡åè§£ãæºè½ä½åéãç»æèå?                 â?  â?â? â?                                                        â?  â?â? â? æ ¸å¿åè½:                                               â?  â?â? â? - ä»»å¡åè§£: å°å¤æä»»å¡æåä¸ºå­ä»»å?                       â?  â?â? â? - æºè½ä½åé? ä¸ºæ¯ä¸ªå­ä»»å¡éæ©æåéçæºè½ä½?              â?  â?â? â? - ç»æèå: æ¶éåæ´åå­ä»»å¡æ§è¡ç»æ                      â?  â?â? â? - ä¾èµç®¡ç: ç®¡çå­ä»»å¡ä¹é´çä¾èµå³ç³»                      â?  â?â? â?                                                        â?  â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â?                             â?                                 â?â?                             â?                                 â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â? â?                  å¤æºè½ä½åä½æ¨¡å¼                        â?  â?â? â?                                                        â?  â?â? â? âââââââââââââââ? âââââââââââââââ? âââââââââââââââ?    â?  â?â? â? â? å¹¶è¡æ§è¡    â? â? ä¸²è¡æ§è¡    â? â? æ··åæ§è¡    â?    â?  â?â? â? â? Parallel   â? â? Sequential â? â?  Hybrid    â?    â?  â?â? â? â?            â? â?            â? â?            â?    â?  â?â? â? â?åæ¶æ§è¡    â? â?æåºæ§è¡    â? â?æºè½éæ©    â?    â?  â?â? â? â?æ ä¾èµ?     â? â?æä¾èµ?     â? â?èªå¨å¤æ­    â?    â?  â?â? â? â?æçé«?     â? â?ä¿è¯æ­£ç¡®    â? â?æä¼ç­ç?   â?    â?  â?â? â? âââââââââââââââ? âââââââââââââââ? âââââââââââââââ?    â?  â?â? â?                                                        â?  â?â? â? æéåæ¢æºå¶:                                          â?  â?â? â? - ä»»å¡å¤±è´¥èªå¨éè¯                                      â?  â?â? â? - æºè½ä½å¤±è´¥èªå¨åæ?                                   â?  â?â? â? - è¶æ¶å¤ç                                             â?  â?â? â?                                                        â?  â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â?                             â?                                 â?â?                             â?                                 â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â? â?                   ä»»å¡ (Task)                           â?  â?â? â?                                                        â?  â?â? â? æå°ä¸ä¸æåä½:                                         â?  â?â? â? - prompt: ä»»å¡æç¤ºè¯?                                   â?  â?â? â? - context: æ§è¡ä¸ä¸æ?                                  â?  â?â? â? - dependencies: ä¾èµä»»å¡åè¡¨                            â?  â?â? â? - status: ä»»å¡ç¶æ?                                     â?  â?â? â? - result: æ§è¡ç»æ                                      â?  â?â? â?                                                        â?  â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â?                             â?                                 â?â?                             â?                                 â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â? â?                æ§è¡æºè½ä½?(ExecutorAgent)                â?  â?â? â?                                                        â?  â?â? â? - ReActæ¨çå¼æ                                        â?  â?â? â? - å·¥å·è°ç¨                                             â?  â?â? â? - å­Agentåä½                                          â?  â?â? â?                                                        â?  â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â?                                                                â?âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?```

## æ ¸å¿ç»ä»¶

### 1. ä»»å¡ (Task)

**æä»¶**: `src/execution/task.py`

ä»»å¡æ¯æå°ä¸ä¸æåä½ï¼åå«æ§è¡æéçææä¿¡æ¯ã?
#### ä»»å¡ç»æ

```python
@dataclass
class Task:
    """ä»»å¡ - æ§è¡æ¨¡åçæå°ä¸ä¸æåä½"""
    
    id: str                    # ä»»å¡å¯ä¸ID
    prompt: str                # ä»»å¡æç¤ºè¯?    context: Dict[str, Any]    # æ§è¡ä¸ä¸æ?    dependencies: List[str]    # ä¾èµä»»å¡IDåè¡¨
    status: TaskStatus         # ä»»å¡ç¶æ?    priority: int              # ä¼åçº?    assigned_agent: str        # åéçæºè½ä½
    result: Optional[str]      # æ§è¡ç»æ
    error: Optional[str]       # éè¯¯ä¿¡æ¯
    created_at: float          # åå»ºæ¶é´
    started_at: Optional[float]  # å¼å§æ¶é?    completed_at: Optional[float]  # å®ææ¶é´
    retry_count: int           # éè¯æ¬¡æ°
    max_retries: int           # æå¤§éè¯æ¬¡æ?```

#### ä»»å¡æ§è¡ç¶æ?
```python
class TaskStatus(Enum):
    """ä»»å¡æ§è¡ç¶æ?- è¡¨ç¤ºä»»å¡çæ§è¡çå½å¨æ?""
    PENDING = "pending"           # ç­å¾æ§è¡
    RUNNING = "running"           # æ§è¡ä¸?    COMPLETED = "completed"       # å·²å®æ?    FAILED = "failed"             # å¤±è´¥
    CANCELLED = "cancelled"       # å·²åæ¶?```

#### ä»»å¡è¿è¡ç¶æï¼åç¶æç³»ç»ï¼

```python
class TaskState(Enum):
    """ä»»å¡è¿è¡ç¶æ?- è¡¨ç¤ºä»»å¡çè¿è¡æ§å¶ç¶æ?""
    ACTIVE = "active"             # æ´»è·ï¼é»è®¤ï¼- ä»»å¡æ­£å¸¸è¿è¡
    PAUSED = "paused"             # æå - ä»»å¡æåæ§è¡ï¼å¯æ¢å¤
    ERROR = "error"               # å¼å¸¸ - å¤æ¬¡éè¯åä»æ æ³å®æï¼éäººå·¥ä»å¥
    WAITING = "waiting"           # ç­å¾ - éè¦ç¨æ·ç¡®è®¤æåå©
```

#### ç­å¾ç±»å

```python
class WaitingType(Enum):
    """ç­å¾ç¨æ·æä½ç±»å"""
    CONFIRM = "confirm"           # é¡»æ¨ç¡®è®¤
    ASSIST = "assist"             # é¡»æ¨åå©
```

#### ç¶ææµè½?
```
åå»º â?æ´»è·(ACTIVE) â?æ§è¡ä¸?â?å®æ/å¤±è´¥
         â?      æå(PAUSED) ââ æ´»è·ï¼å¯åååæ¢ï¼?         â?      ç­å¾(WAITING) â?ç¨æ·æä½ â?æ´»è·
         â?      å¼å¸¸(ERROR) â?äººå·¥ä»å¥ â?æ´»è·
```

#### æ¾ç¤ºç¶æ?
ä»»å¡å¨UIä¸­çæ¾ç¤ºæ ¼å¼ï¼?- `æ§è¡ï½è§åä¸­` - ä»»å¡æ­£å¨è§å/åå¤ä¸?- `æ§è¡ï½XX%` - ä»»å¡æ§è¡ä¸­ï¼æ¾ç¤ºè¿åº¦ç¾åæ¯?- `æ§è¡ï½é¡»æ¨ç¡®è®¤` - ä»»å¡éè¦ç¨æ·ç¡®è®?- `æ§è¡ï½é¡»æ¨åå©` - ä»»å¡éè¦ç¨æ·åå?- `æ§è¡ï½å®æ` - ä»»å¡å·²å®æ?- `æ§è¡ï½å¤±è´¥` - ä»»å¡æ§è¡å¤±è´¥
- `æ§è¡ï½å·²æå` - ä»»å¡å·²æå?- `æ§è¡ï½å¼å¸¸` - ä»»å¡å¼å¸¸ï¼éäººå·¥ä»å¥

#### ä»»å¡ä¸ä¸æ?
```python
@dataclass
class TaskContext:
    """ä»»å¡ä¸ä¸æ?""
    
    # è¾å¥æ°æ®
    input_data: Dict[str, Any]
    
    # åå²è®°å½
    history: List[Dict[str, Any]]
    
    # ç¯å¢ä¿¡æ¯
    environment: Dict[str, Any]
    
    # å¯ç¨å·¥å·
    available_tools: List[str]
    
    # è®°å¿å¼ç¨
    memory_refs: List[str]
    
    # åæ°æ?    metadata: Dict[str, Any]
```

### 2. è§åæºè½ä½?(PlannerAgent)

**æä»¶**: `src/execution/planner_agent.py`

è§åæºè½ä½è´è´£ä»»å¡åè§£ãæºè½ä½åéåç»æèåã?
#### æ ¸å¿åè½

```python
class PlannerAgent:
    """è§åæºè½ä½?""
    
    def __init__(
        self,
        llm_client: Any,
        agent_registry: AgentRegistry,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm_client = llm_client
        self.agent_registry = agent_registry
        self.config = config or {}
        self.max_subtasks = config.get("max_subtasks", 10)
        self.enable_collaboration = config.get("enable_collaboration", True)
    
    async def plan(
        self,
        task: Task,
        collaboration_mode: CollaborationMode = CollaborationMode.HYBRID
    ) -> ExecutionPlan:
        """è§åä»»å¡æ§è¡"""
        
        # 1. åæä»»å¡å¤æåº?        complexity = await self._analyze_complexity(task)
        
        # 2. å³å®æ¯å¦åè§£
        if complexity < self.config.get("decomposition_threshold", 0.5):
            # ç®åä»»å¡ï¼ä¸åè§?            return ExecutionPlan(
                tasks=[task],
                mode=CollaborationMode.SEQUENTIAL
            )
        
        # 3. ä»»å¡åè§£
        subtasks = await self._decompose_task(task)
        
        # 4. åéæºè½ä½?        for subtask in subtasks:
            subtask.assigned_agent = await self._assign_agent(subtask)
        
        # 5. åæä¾èµå³ç³»
        dependencies = await self._analyze_dependencies(subtasks)
        
        # 6. ç¡®å®åä½æ¨¡å¼
        mode = await self._determine_collaboration_mode(subtasks, dependencies)
        
        return ExecutionPlan(
            tasks=subtasks,
            dependencies=dependencies,
            mode=mode
        )
```

#### ä»»å¡åè§£

```python
async def _decompose_task(self, task: Task) -> List[Task]:
    """å°ä»»å¡åè§£ä¸ºå­ä»»å?""
    
    prompt = f"""
    è¯·å°ä»¥ä¸ä»»å¡åè§£ä¸ºå¤ä¸ªå­ä»»å¡ï¼?    
    ä»»å¡: {task.prompt}
    
    è¦æ±ï¼?    1. æ¯ä¸ªå­ä»»å¡åºè¯¥æ¯ç¬ç«å¯æ§è¡ç
    2. å­ä»»å¡ä¹é´å°½éåå°ä¾èµ?    3. æå¤åè§£ä¸º {self.max_subtasks} ä¸ªå­ä»»å¡
    
    è¯·æä»¥ä¸æ ¼å¼è¾åºï¼?    1. [å­ä»»å?æè¿°]
    2. [å­ä»»å?æè¿°]
    ...
    """
    
    response = await self.llm_client.generate(prompt)
    
    # è§£æå­ä»»å?    subtasks = self._parse_subtasks(response, task)
    
    return subtasks
```

#### æºè½ä½åé?
```python
async def _assign_agent(self, task: Task) -> str:
    """ä¸ºä»»å¡åéæåéçæºè½ä½?""
    
    # è·åææå¯ç¨æºè½ä½
    available_agents = self.agent_registry.list_agents()
    
    # è¯ä¼°æ¯ä¸ªæºè½ä½çééåº?    scores = []
    for agent in available_agents:
        score = await self._evaluate_agent_fit(agent, task)
        scores.append((agent, score))
    
    # éæ©å¾åæé«çæºè½ä½?    scores.sort(key=lambda x: x[1], reverse=True)
    
    return scores[0][0].id if scores else "default"
```

#### ä¾èµåæ

```python
async def _analyze_dependencies(
    self,
    subtasks: List[Task]
) -> Dict[str, List[str]]:
    """åæå­ä»»å¡ä¹é´çä¾èµå³ç³»"""
    
    dependencies = {}
    
    for i, task in enumerate(subtasks):
        task_deps = []
        
        # æ£æ¥æ¯å¦ä¾èµåé¢çä»»å¡
        for j in range(i):
            if await self._check_dependency(subtasks[j], task):
                task_deps.append(subtasks[j].id)
        
        dependencies[task.id] = task_deps
    
    return dependencies
```

### 3. å¤æºè½ä½åä½æ¨¡å¼

**æä»¶**: `src/execution/collaboration.py`

#### åä½æ¨¡å¼ç±»å

```python
class CollaborationMode(Enum):
    """åä½æ¨¡å¼"""
    SINGLE = "single"           # åæºè½ä½æ¨¡å¼
    PARALLEL = "parallel"       # å¹¶è¡æ§è¡
    SEQUENTIAL = "sequential"   # ä¸²è¡æ§è¡
    HYBRID = "hybrid"           # æ··åæ§è¡
```

#### åä½ç®¡çå?
```python
class CollaborationManager:
    """åä½ç®¡çå?""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enable_collaboration = config.get("enable_collaboration", True)
        self.default_mode = config.get("default_mode", CollaborationMode.HYBRID)
        self.fault_tolerance = config.get("fault_tolerance", True)
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        executor: ExecutorAgent
    ) -> ExecutionResult:
        """æ§è¡è®¡å"""
        
        if plan.mode == CollaborationMode.SINGLE:
            return await self._execute_single(plan, executor)
        elif plan.mode == CollaborationMode.PARALLEL:
            return await self._execute_parallel(plan, executor)
        elif plan.mode == CollaborationMode.SEQUENTIAL:
            return await self._execute_sequential(plan, executor)
        elif plan.mode == CollaborationMode.HYBRID:
            return await self._execute_hybrid(plan, executor)
    
    async def _execute_parallel(
        self,
        plan: ExecutionPlan,
        executor: ExecutorAgent
    ) -> ExecutionResult:
        """å¹¶è¡æ§è¡"""
        
        # æ£æ¥ä¾èµ?        ready_tasks = [
            task for task in plan.tasks
            if not plan.dependencies.get(task.id)
        ]
        
        # å¹¶è¡æ§è¡ææå°±ç»ªä»»å?        results = await asyncio.gather(*[
            self._execute_task_with_retry(task, executor)
            for task in ready_tasks
        ])
        
        # èåç»æ
        return self._aggregate_results(results)
    
    async def _execute_sequential(
        self,
        plan: ExecutionPlan,
        executor: ExecutorAgent
    ) -> ExecutionResult:
        """ä¸²è¡æ§è¡"""
        
        results = []
        
        for task in plan.tasks:
            # ç­å¾ä¾èµå®æ
            await self._wait_for_dependencies(task, plan.dependencies)
            
            # æ§è¡ä»»å¡
            result = await self._execute_task_with_retry(task, executor)
            results.append(result)
            
            # å¦æä»»å¡å¤±è´¥ä¸ä¸åè®¸ç»§ç»­ï¼åæ­¢æ§è¡?            if not result.success and not self.config.get("continue_on_error"):
                break
        
        return self._aggregate_results(results)
    
    async def _execute_hybrid(
        self,
        plan: ExecutionPlan,
        executor: ExecutorAgent
    ) -> ExecutionResult:
        """æ··åæ§è¡ - æºè½éæ©æ§è¡æ¹å¼"""
        
        # åæä»»å¡ä¾èµå?        dependency_graph = self._build_dependency_graph(plan)
        
        # è¯å«å¯ä»¥å¹¶è¡æ§è¡çç»
        parallel_groups = self._identify_parallel_groups(dependency_graph)
        
        # æç»æ§è¡
        results = []
        for group in parallel_groups:
            if len(group) == 1:
                # åä¸ªä»»å¡ï¼ä¸²è¡æ§è¡?                result = await self._execute_task_with_retry(group[0], executor)
                results.append(result)
            else:
                # å¤ä¸ªä»»å¡ï¼å¹¶è¡æ§è¡?                group_results = await asyncio.gather(*[
                    self._execute_task_with_retry(task, executor)
                    for task in group
                ])
                results.extend(group_results)
        
        return self._aggregate_results(results)
```

#### æéåæ¢

```python
async def _execute_task_with_retry(
    self,
    task: Task,
    executor: ExecutorAgent
) -> TaskResult:
    """æ§è¡ä»»å¡ï¼æ¯æéè¯?""
    
    for attempt in range(task.max_retries + 1):
        try:
            # æ§è¡ä»»å¡
            result = await executor.execute(task)
            
            return TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                attempts=attempt + 1
            )
            
        except Exception as e:
            task.retry_count += 1
            
            if task.retry_count > task.max_retries:
                # éè¯æ¬¡æ°ç¨å°½ï¼å°è¯åæ¢æºè½ä½
                if self.fault_tolerance:
                    new_agent = await self._switch_agent(task)
                    if new_agent:
                        task.assigned_agent = new_agent
                        task.retry_count = 0
                        continue
                
                return TaskResult(
                    task_id=task.id,
                    success=False,
                    error=str(e),
                    attempts=attempt + 1
                )
            
            # ç­å¾åéè¯?            await asyncio.sleep(self.config.get("retry_delay", 1.0) * (2 ** attempt))
    
    return TaskResult(
        task_id=task.id,
        success=False,
        error="Max retries exceeded",
        attempts=task.retry_count
    )
```

### 4. ä»»å¡è§åå?
**æä»¶**: `src/execution/planner.py`

```python
class TaskPlanner:
    """ä»»å¡è§åå?""
    
    def __init__(self, llm_client: Any):
        self.llm_client = llm_client
    
    async def create_plan(
        self,
        objective: str,
        constraints: Optional[List[str]] = None
    ) -> TaskPlan:
        """åå»ºä»»å¡è®¡å"""
        
        prompt = f"""
        ç®æ : {objective}
        
        çº¦æ: {constraints or []}
        
        è¯·åå»ºä¸ä¸ªè¯¦ç»çä»»å¡æ§è¡è®¡åï¼åæ¬ï¼
        1. ä»»å¡åè§£
        2. æ§è¡é¡ºåº
        3. ä¾èµå³ç³»
        4. é¢æç»æ
        """
        
        response = await self.llm_client.generate(prompt)
        
        return self._parse_plan(response)
    
    def optimize_plan(self, plan: TaskPlan) -> TaskPlan:
        """ä¼åä»»å¡è®¡å"""
        
        # åå¹¶å¯ä»¥å¹¶è¡æ§è¡çä»»å?        # åå°ä¸å¿è¦çä¾èµ
        # è°æ´æ§è¡é¡ºåº
        
        return optimized_plan
```

## ä½¿ç¨ç¤ºä¾

### åºç¡ä½¿ç¨

```python
from src.execution.task import Task, TaskContext
from src.execution.planner_agent import PlannerAgent
from src.execution.collaboration import CollaborationManager, CollaborationMode

# åå»ºä»»å¡
task = Task(
    id="task_001",
    prompt="åæç¨æ·åé¦æ°æ®å¹¶çææ¥å?,
    context=TaskContext(
        input_data={"feedback_file": "data/feedback.csv"},
        history=[],
        environment={"workspace": "/tmp/analysis"},
        available_tools=["file_reader", "data_analyzer", "report_generator"]
    ),
    priority=1
)

# åå»ºè§åæºè½ä½?planner = PlannerAgent(
    llm_client=llm_client,
    agent_registry=agent_registry
)

# è§åä»»å¡
plan = await planner.plan(task, collaboration_mode=CollaborationMode.HYBRID)

# åå»ºåä½ç®¡çå?collaboration_mgr = CollaborationManager(
    config={
        "enable_collaboration": True,
        "default_mode": CollaborationMode.HYBRID,
        "fault_tolerance": True
    }
)

# æ§è¡è®¡å
result = await collaboration_mgr.execute_plan(plan, executor)
```

### å¤æºè½ä½åä½

```python
# å¯ç¨å¤æºè½ä½åä½æ¨¡å¼
collaboration_mgr = CollaborationManager(
    config={
        "enable_collaboration": True,
        "default_mode": CollaborationMode.PARALLEL,
        "fault_tolerance": True,
        "max_retries": 3,
        "retry_delay": 1.0
    }
)

# åå»ºå¤æä»»å¡
complex_task = Task(
    id="complex_task",
    prompt="å¼åä¸ä¸ªæ°åè½ï¼åæ¬è®¾è®¡ãç¼ç ãæµè¯ãææ¡?,
    context=TaskContext(...)
)

# è§åå¹¶æ§è¡?plan = await planner.plan(complex_task)
result = await collaboration_mgr.execute_plan(plan, executor)

# æ¥çæ§è¡è¯¦æ
for task_result in result.task_results:
    print(f"ä»»å¡ {task_result.task_id}: {'æå' if task_result.success else 'å¤±è´¥'}")
```

### æéåæ¢

```python
# éç½®æéåæ¢
collaboration_mgr = CollaborationManager(
    config={
        "fault_tolerance": True,
        "max_retries": 3,
        "retry_delay": 1.0,
        "agent_switch_on_failure": True
    }
)

# æ§è¡ä»»å¡
result = await collaboration_mgr.execute_task_with_retry(task, executor)

if result.success:
    print(f"ä»»å¡æåï¼å°è¯äº {result.attempts} æ¬?)
else:
    print(f"ä»»å¡å¤±è´¥ï¼å°è¯äº {result.attempts} æ¬¡ï¼éè¯¯: {result.error}")
```

## éç½®

### éç½®æä»¶

```yaml
# config/execution.yaml
execution:
  # è§åæºè½ä½éç½?  planner:
    max_subtasks: 10
    decomposition_threshold: 0.5
    enable_collaboration: true
  
  # åä½æ¨¡å¼éç½®
  collaboration:
    default_mode: "hybrid"  # single/parallel/sequential/hybrid
    enable_collaboration: true
    fault_tolerance: true
    max_retries: 3
    retry_delay: 1.0
    continue_on_error: false
    agent_switch_on_failure: true
  
  # ä»»å¡éç½®
  task:
    default_priority: 1
    default_max_retries: 3
    timeout: 300
```

### ç¯å¢åé

```env
# æ§è¡æ¨¡åéç½®
EXECUTION_ENABLE_COLLABORATION=true
EXECUTION_DEFAULT_MODE=hybrid
EXECUTION_FAULT_TOLERANCE=true
EXECUTION_MAX_RETRIES=3
```

## APIæ¥å£

### åå»ºä»»å¡è®¡å

```http
POST /api/execution/plan
Content-Type: application/json

{
  "objective": "åæç¨æ·åé¦æ°æ®",
  "constraints": ["ä½¿ç¨Python", "çæPDFæ¥å"],
  "collaboration_mode": "hybrid"
}
```

### æ§è¡ä»»å¡

```http
POST /api/execution/execute
Content-Type: application/json

{
  "task_id": "task_001",
  "enable_collaboration": true,
  "mode": "parallel"
}
```

### è·åä»»å¡ç¶æ?
```http
GET /api/execution/tasks/{task_id}/status
```

### åæ¢åä½æ¨¡å¼

```http
POST /api/execution/collaboration/mode
Content-Type: application/json

{
  "mode": "hybrid",
  "enable": true
}
```

## æä½³å®è·?
### 1. åçéæ©åä½æ¨¡å¼

```python
# ç®åä»»å?- åæºè½ä½
if task_complexity < 0.3:
    mode = CollaborationMode.SINGLE

# ç¬ç«å­ä»»å?- å¹¶è¡
elif all_independent(subtasks):
    mode = CollaborationMode.PARALLEL

# æä¾èµå³ç³?- ä¸²è¡
elif has_dependencies(subtasks):
    mode = CollaborationMode.SEQUENTIAL

# å¤æä»»å¡ - æ··å
else:
    mode = CollaborationMode.HYBRID
```

### 2. éç½®æéåæ¢

```python
# å¯ç¨æéåæ¢
collaboration_mgr = CollaborationManager(
    config={
        "fault_tolerance": True,
        "max_retries": 3,
        "agent_switch_on_failure": True
    }
)
```

### 3. ä»»å¡ç²åº¦æ§å¶

```python
# é¿åä»»å¡è¿å¤§æè¿å°?# åéçä»»å¡åºè¯¥ï¼?# - è½å¨5-10åéåå®æ?# - ææç¡®çè¾å¥åè¾å?# - ç¸å¯¹ç¬ç«
```

### 4. çæ§æ§è¡ç¶æ?
```python
# å®ææ£æ¥ä»»å¡ç¶æ?for task in plan.tasks:
    status = await collaboration_mgr.get_task_status(task.id)
    if status == TaskStatus.FAILED:
        logger.warning(f"ä»»å¡ {task.id} å¤±è´¥")
```

## æéæé¤

### 1. ä»»å¡åè§£å¤±è´¥

**åå **: ä»»å¡æè¿°ä¸æ¸æ?
**è§£å³**: æä¾æ´è¯¦ç»çä»»å¡æè¿°åçº¦ææ¡ä»?
### 2. æºè½ä½åéä¸å½?
**åå **: æºè½ä½è½åä¸è¶?
**è§£å³**: æ©å±æºè½ä½æ³¨åè¡¨ï¼æ·»å æ´å¤ä¸ä¸æºè½ä½

### 3. åä½æ¨¡å¼éæ©ä¸å½

**åå **: ä¾èµå³ç³»åæéè¯¯

**è§£å³**: æå¨æå®åä½æ¨¡å¼ï¼æä¼åä¾èµåæç®æ³

### 4. ä»»å¡è¶æ¶

**åå **: ä»»å¡è¿å¤§ææ§è¡æ¶é´è¿é?
**è§£å³**: å°å¤§ä»»å¡æåä¸ºæ´å°çå­ä»»å?
