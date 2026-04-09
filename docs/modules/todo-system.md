# AIåçTodoç³»ç»ææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»æè¿°PyAgent v0.8.0çAIåçTodoç³»ç»çè®¾è®¡åå®ç°ã?
## æ¦è¿°

AIåçTodoç³»ç»æ¯ä¸ä¸ªä¸çº§åç±»çä»»å¡ç®¡çç³»ç»ï¼ä¸ä¸ºAI Agentè®¾è®¡ï¼æ¯æèªå¨æ´æ°ãéªæ¶ææ¡£çæåé¶æ®µåæã?
## æ ¸å¿ç¹æ?
- **ä¸çº§åç±»æ¶æ**: Phase â?Task â?Step
- **èªå¨æ´æ°æºå¶**: æ­¥éª¤å®æåèªå¨æ´æ°ä»»å¡è¿åº?- **éªæ¶ææ¡£ç³»ç»**: æ¯ä¸ªä»»å¡èªå¨åå»ºéªæ¶ææ¡£
- **é¶æ®µåææºå?*: é¶æ®µå®æåè¿è¡?-5è½®åæ?
## æ¶æè®¾è®¡

```
âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?â?                   Todoç³»ç»æ¶æ                              â?âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?â?                                                            â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â? â?                 Phase (é¶æ®µ)                        â?  â?â? â? âââââââââââââââââââââââââââââââââââââââââââââââ?  â?  â?â? â? â?å±æ?                                        â?  â?  â?â? â? â?- id: å¯ä¸æ è¯                               â?  â?  â?â? â? â?- title: æ é¢                                â?  â?  â?â? â? â?- description: æè¿°                          â?  â?  â?â? â? â?- status: ç¶æ?                              â?  â?  â?â? â? â?- priority: ä¼åçº?                          â?  â?  â?â? â? â?- tasks: ä»»å¡åè¡¨                            â?  â?  â?â? â? â?- reflections: åæç»æ?                     â?  â?  â?â? â? â?- min/max_reflections: åæè½®æ°èå?         â?  â?  â?â? â? âââââââââââââââââââââââââââââââââââââââââââââââ?  â?  â?â? â?                                                    â?  â?â? â? æä½:                                              â?  â?â? â? - create_task(): åå»ºä»»å¡                         â?  â?â? â? - get_progress(): è·åè¿åº¦                        â?  â?â? â? - needs_reflection(): æ¯å¦éè¦åæ?               â?  â?â? â?                                                    â?  â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â?                             â?                             â?â?                             â?                             â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â? â?                 Task (ä»»å¡)                         â?  â?â? â? âââââââââââââââââââââââââââââââââââââââââââââââ?  â?  â?â? â? â?å±æ?                                        â?  â?  â?â? â? â?- id: å¯ä¸æ è¯                               â?  â?  â?â? â? â?- phase_id: æå±é¶æ®µID                       â?  â?  â?â? â? â?- title: æ é¢                                â?  â?  â?â? â? â?- description: æè¿°                          â?  â?  â?â? â? â?- steps: æ­¥éª¤åè¡¨                            â?  â?  â?â? â? â?- verification_document: éªæ¶ææ¡£            â?  â?  â?â? â? âââââââââââââââââââââââââââââââââââââââââââââââ?  â?  â?â? â?                                                    â?  â?â? â? æä½:                                              â?  â?â? â? - create_step(): åå»ºæ­¥éª¤                         â?  â?â? â? - get_progress(): è·åè¿åº¦                        â?  â?â? â? - auto_verify(): èªå¨éªæ¶                         â?  â?â? â?                                                    â?  â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â?                             â?                             â?â?                             â?                             â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â? â?                 Step (æ­¥éª¤)                         â?  â?â? â? âââââââââââââââââââââââââââââââââââââââââââââââ?  â?  â?â? â? â?å±æ?                                        â?  â?  â?â? â? â?- id: å¯ä¸æ è¯                               â?  â?  â?â? â? â?- task_id: æå±ä»»å¡ID                        â?  â?  â?â? â? â?- content: åå®¹                              â?  â?  â?â? â? â?- status: ç¶æ?                              â?  â?  â?â? â? â?- dependencies: ä¾èµæ­¥éª¤                     â?  â?  â?â? â? âââââââââââââââââââââââââââââââââââââââââââââââ?  â?  â?â? â?                                                    â?  â?â? â? ç¶æ?                                              â?  â?â? â? - PENDING: å¾å¤ç?                                â?  â?â? â? - IN_PROGRESS: è¿è¡ä¸?                          â?  â?â? â? - COMPLETED: å·²å®æ?                            â?  â?â? â? - BLOCKED: è¢«é»å¡?                              â?  â?â? â? - SKIPPED: å·²è·³è¿?                              â?  â?â? â?                                                    â?  â?â? âââââââââââââââââââââââââââââââââââââââââââââââââââââââ?  â?â?                                                            â?âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ?```

## æ ¸å¿ç»ä»¶

### 1. TodoManager

**æä»¶**: `src/todo/todo_manager.py`

**èè´£**: ç®¡çææTodoç¸å³çæä½?
#### ä¸»è¦æ¹æ³

```python
class TodoManager:
    async def create_phase(
        self,
        title: str,
        description: str = "",
        priority: TodoPriority = TodoPriority.MEDIUM,
        min_reflections: int = 2,
        max_reflections: int = 5,
    ) -> TodoPhase:
        """åå»ºé¶æ®µ"""
        pass
    
    async def create_task(
        self,
        phase_id: str,
        title: str,
        description: str = "",
        priority: TodoPriority = TodoPriority.MEDIUM,
        steps: Optional[List[str]] = None,
    ) -> Optional[TodoTask]:
        """åå»ºä»»å¡ï¼èªå¨åå»ºéªæ¶ææ¡£ï¼"""
        pass
    
    async def create_step(
        self,
        task_id: str,
        content: str,
        priority: TodoPriority = TodoPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
    ) -> Optional[TodoStep]:
        """åå»ºæ­¥éª¤"""
        pass
    
    async def complete_step(self, step_id: str) -> bool:
        """å®ææ­¥éª¤ï¼è§¦åèªå¨æ´æ°ï¼"""
        pass
```

#### èªå¨æ´æ°æºå¶

```python
async def complete_step(self, step_id: str) -> bool:
    """å®ææ­¥éª¤å¹¶è§¦åçº§èæ´æ?""
    # 1. æ è®°æ­¥éª¤å®æ
    step.status = TodoStatus.COMPLETED
    step.completed_at = datetime.now().timestamp()
    
    # 2. è·åæå±ä»»å?    task = self._find_task(step.task_id)
    if task:
        # 3. æ£æ¥ä»»å¡æ¯å¦å®æ?        await self._check_task_completion(task)
    
    self._save_data()
    return True

async def _check_task_completion(self, task: TodoTask) -> None:
    """æ£æ¥ä»»å¡å®æç¶æ?""
    # æ£æ¥æææ­¥éª¤æ¯å¦å®æ?    all_completed = all(
        s.status == TodoStatus.COMPLETED for s in task.steps
    )
    
    if all_completed and task.status != TodoStatus.COMPLETED:
        # æ è®°ä»»å¡å®æ
        task.status = TodoStatus.COMPLETED
        task.completed_at = datetime.now().timestamp()
        
        # èªå¨éªæ¶
        await self._verify_task(task)
        
        # æ£æ¥é¶æ®?        phase = self._find_phase_by_task(task.id)
        if phase:
            await self._check_phase_completion(phase)

async def _check_phase_completion(self, phase: TodoPhase) -> None:
    """æ£æ¥é¶æ®µå®æç¶æ?""
    all_completed = all(
        t.status == TodoStatus.COMPLETED for t in phase.tasks
    )
    
    if all_completed and phase.status != TodoStatus.COMPLETED:
        # æ è®°é¶æ®µå®æ
        phase.status = TodoStatus.COMPLETED
        phase.completed_at = datetime.now().timestamp()
        
        # è¿è¡é¶æ®µåæ?        await self._conduct_phase_reflection(phase)
```

### 2. éªæ¶ææ¡£ç³»ç»

**æä»¶**: `src/todo/todo_manager.py` (VerificationDocumentç¸å³)

#### éªæ¶ææ¡£ç»æ

```python
@dataclass
class VerificationDocument:
    id: str                           # ææ¡£ID
    task_id: str                      # æå±ä»»å¡ID
    title: str                        # æ é¢
    description: str                  # æè¿°
    acceptance_criteria: List[str]    # éªæ¶æ å
    verification_results: List[str]   # éªæ¶ç»æ
    is_verified: bool                 # æ¯å¦å·²éªæ?    verified_at: Optional[float]      # éªæ¶æ¶é´
    verified_by: str                  # éªæ¶äº?```

#### èªå¨çæéªæ¶æ å

```python
def _generate_acceptance_criteria(self, task: TodoTask) -> List[str]:
    """çæéªæ¶æ å"""
    criteria = []
    
    # ä»»å¡åºæ¬ä¿¡æ¯
    criteria.append(f"ä»»å¡æ é¢: {task.title}")
    
    if task.description:
        criteria.append(f"ä»»å¡æè¿°: {task.description}")
    
    # æ­¥éª¤è¦æ±
    if task.steps:
        criteria.append("å®æä»¥ä¸æææ­¥éª?")
        for step in task.steps:
            criteria.append(f"  - {step.content}")
    
    # éç¨æ å
    criteria.append("æææ­¥éª¤ç¶æä¸ºå·²å®æ?)
    criteria.append("æ éçé®é¢æå·²è®°å½åç»­å¤çæ¹æ¡?)
    
    return criteria
```

#### éªæ¶ææ¡£æ ¼å¼

```markdown
# éªæ¶ææ¡£: {ä»»å¡æ é¢}

**ä»»å¡ID**: task_xxx
**åå»ºæ¶é´**: 2024-01-01 12:00:00

## éªæ¶æ å

- ä»»å¡æ é¢: xxx
- ä»»å¡æè¿°: xxx
- å®æä»¥ä¸æææ­¥éª?
  - æ­¥éª¤1
  - æ­¥éª¤2
- æææ­¥éª¤ç¶æä¸ºå·²å®æ?- æ éçé®é¢æå·²è®°å½åç»­å¤çæ¹æ¡?
## éªæ¶ç»æ

- **ç¶æ?*: å·²éªæ?- **éªæ¶æ¶é´**: 2024-01-01 15:00:00

### éªæ¶è¯¦æ

- ææ?5 ä¸ªæ­¥éª¤å·²å®æ
- ä»»å¡è¿åº¦: 100%
- éªæ¶éè¿

## ç­¾å

éªæ¶äº? system
```

### 3. é¶æ®µåææºå?
**æä»¶**: `src/todo/todo_manager.py` (ReflectionResultç¸å³)

#### åææµç¨?
```
é¶æ®µå®æ
    â?    â?ç¡®å®åæè½®æ?(min_reflections ~ max_reflections)
    â?    â?âââââââââââââââââââ?â?ç¬?è½®åæ?       â?â?- æ»ç»å®ææåµ   â?â?- æåå³é®æ´å¯   â?ââââââââââ¬âââââââââ?         â?         â?âââââââââââââââââââ?â?ç¬?è½®åæ?       â?â?- åæé®é¢       â?â?- æåºæ¹è¿å»ºè®®   â?ââââââââââ¬âââââââââ?         â?         â?     [ç»§ç»­...]
         â?         â?ä¿å­åæç»æå°é¶æ®µ
```

#### åæç»æç»æ?
```python
@dataclass
class ReflectionResult:
    id: str                    # åæID
    phase_id: str              # æå±é¶æ®µID
    round_number: int          # è½®æ¬¡
    content: str               # åæåå®?    insights: List[str]        # æ´å¯
    improvements: List[str]    # æ¹è¿å»ºè®®
    created_at: float          # åå»ºæ¶é´
```

#### èªå¨çæåæåå®?
```python
async def _generate_reflection(
    self,
    phase: TodoPhase,
    llm_client: Optional[Any] = None,
) -> Optional[ReflectionResult]:
    """çæåæåå®?""
    
    # ç»è®¡ä¿¡æ¯
    completed_tasks = sum(1 for t in phase.tasks if t.status == TodoStatus.COMPLETED)
    total_tasks = len(phase.tasks)
    
    # çæåæ?    reflection = ReflectionResult(
        id=self._generate_id("reflect"),
        phase_id=phase.id,
        round_number=phase.reflection_count,
        content=f"é¶æ®µ '{phase.title}' åæ?(ç¬¬{phase.reflection_count}è½?",
        insights=self._extract_insights(phase),
        improvements=self._extract_improvements(phase),
    )
    
    return reflection

def _extract_insights(self, phase: TodoPhase) -> List[str]:
    """æåæ´å¯"""
    insights = []
    
    for task in phase.tasks:
        if task.status == TodoStatus.COMPLETED:
            insights.append(f"ä»»å¡ '{task.title}' æåå®æ")
            
            blocked_steps = [s for s in task.steps if s.status == TodoStatus.BLOCKED]
            if blocked_steps:
                insights.append(f"ä»»å¡ '{task.title}' æ?{len(blocked_steps)} ä¸ªæ­¥éª¤æ¾è¢«é»å¡?)
    
    return insights

def _extract_improvements(self, phase: TodoPhase) -> List[str]:
    """æåæ¹è¿å»ºè®®"""
    improvements = []
    
    # æ£æ¥ä»»å¡å¤§å°?    avg_steps_per_task = sum(len(t.steps) for t in phase.tasks) / max(len(phase.tasks), 1)
    if avg_steps_per_task > 10:
        improvements.append("å»ºè®®å°å¤§ä»»å¡æåä¸ºæ´å°çä»»å¡")
    
    # æ£æ¥é»å¡æå?    blocked_count = sum(
        sum(1 for s in t.steps if s.status == TodoStatus.BLOCKED)
        for t in phase.tasks
    )
    if blocked_count > 0:
        improvements.append(f"å±æ {blocked_count} ä¸ªæ­¥éª¤è¢«é»å¡ï¼å»ºè®®ä¼åä¾èµå³ç³?)
    
    return improvements
```

## ä½¿ç¨ç¤ºä¾

### åå»ºå®æ´çTodoç»æ

```python
from src.todo.todo_manager import TodoManager, TodoPriority

# åå»ºç®¡çå?todo_mgr = TodoManager()

# 1. åå»ºé¶æ®µ
phase = await todo_mgr.create_phase(
    title="å¼åæ°åè½",
    description="å®ç°ç¨æ·è¯·æ±çæ°åè½",
    priority=TodoPriority.HIGH,
    min_reflections=2,
    max_reflections=5
)

# 2. åå»ºä»»å¡ï¼èªå¨åå»ºéªæ¶ææ¡£ï¼
task = await todo_mgr.create_task(
    phase_id=phase.id,
    title="å®ç°æ ¸å¿åè½",
    description="å®ç°åè½çæ ¸å¿é»è¾",
    priority=TodoPriority.HIGH,
    steps=[
        "è®¾è®¡æ°æ®æ¨¡å",
        "å®ç°ä¸å¡é»è¾",
        "ç¼åååæµè¯",
        "éææµè¯"
    ]
)

# 3. å®ææ­¥éª¤ï¼èªå¨è§¦åæ´æ°ï¼
for step in task.steps:
    await todo_mgr.complete_step(step.id)
    # èªå¨æ´æ°ä»»å¡è¿åº¦
    # ä»»å¡å®æåèªå¨éªæ?    # é¶æ®µå®æåèªå¨åæ?```

### è·åç»è®¡ä¿¡æ¯

```python
# è·åç»è®¡
stats = todo_mgr.get_statistics()
print(f"""
æ»é¶æ®µæ°: {stats['total_phases']}
æ»ä»»å¡æ°: {stats['total_tasks']}
æ»æ­¥éª¤æ°: {stats['total_steps']}

å·²å®æ?
- é¶æ®µ: {stats['completed_phases']}
- ä»»å¡: {stats['completed_tasks']}
- æ­¥éª¤: {stats['completed_steps']}

è¿åº¦:
- é¶æ®µ: {stats['progress']['phases']:.1%}
- ä»»å¡: {stats['progress']['tasks']:.1%}
- æ­¥éª¤: {stats['progress']['steps']:.1%}
""")
```

### æ ¼å¼åæ¾ç¤?
```python
# è·åæ ¼å¼åçTodoåè¡¨
todo_list = todo_mgr.format_todo_list()
print(todo_list)

# è¾åºç¤ºä¾:
# # Todo List
#
# ## [>] å¼åæ°åè½ (50%)
#    å®ç°ç¨æ·è¯·æ±çæ°åè½
#
# ### [x] å®ç°æ ¸å¿åè½ (100%)
# - [x] è®¾è®¡æ°æ®æ¨¡å
# - [x] å®ç°ä¸å¡é»è¾
# - [x] ç¼åååæµè¯
# - [x] éææµè¯
#
# ### [ ] ææ¡£ç¼å (0%)
# - [ ] ç¼åAPIææ¡£
# - [ ] ç¼åä½¿ç¨è¯´æ
```

## APIæ¥å£

### REST API

| æ¹æ³ | è·¯å¾ | æè¿° |
|------|------|------|
| GET | `/api/todo/phases` | ååºææé¶æ®?|
| POST | `/api/todo/phases` | åå»ºé¶æ®µ |
| GET | `/api/todo/phases/{id}` | è·åé¶æ®µè¯¦æ |
| POST | `/api/todo/phases/{id}/tasks` | åå»ºä»»å¡ |
| POST | `/api/todo/tasks/{id}/steps` | åå»ºæ­¥éª¤ |
| POST | `/api/todo/steps/{id}/complete` | å®ææ­¥éª¤ |
| GET | `/api/todo/statistics` | è·åç»è®¡ä¿¡æ¯ |

### è¯·æ±/ååºç¤ºä¾

#### åå»ºé¶æ®µ

```http
POST /api/todo/phases
Content-Type: application/json

{
  "title": "å¼åæ°åè½",
  "description": "å®ç°ç¨æ·è¯·æ±çæ°åè½",
  "priority": "high",
  "min_reflections": 2,
  "max_reflections": 5
}
```

```json
{
  "id": "phase_abc123",
  "title": "å¼åæ°åè½",
  "description": "å®ç°ç¨æ·è¯·æ±çæ°åè½",
  "status": "pending",
  "priority": "high",
  "tasks": [],
  "created_at": 1704067200
}
```

#### å®ææ­¥éª¤

```http
POST /api/todo/steps/step_abc123/complete
```

```json
{
  "success": true,
  "step_id": "step_abc123",
  "task_progress": 75.0,
  "task_completed": false
}
```

## éç½®

### éç½®æä»¶

```yaml
# config/todo.yaml
todo:
  # åæéç½?  reflection:
    min_rounds: 2        # æå°åæè½®æ?    max_rounds: 5        # æå¤åæè½®æ?    auto_generate: true  # èªå¨çæåæåå®?  
  # éªæ¶éç½®
  verification:
    auto_create: true    # èªå¨åå»ºéªæ¶ææ¡£
    auto_verify: true    # ä»»å¡å®æåèªå¨éªæ?    format: "markdown"   # éªæ¶ææ¡£æ ¼å¼
  
  # å­å¨éç½®
  storage:
    data_dir: "data/todo"
    verification_dir: "data/todo/verifications"
    auto_save: true
    save_interval: 300   # èªå¨ä¿å­é´é(ç§?
```

### ç¯å¢åé

```env
# Todoéç½®
TODO_DATA_DIR=data/todo
TODO_AUTO_SAVE=true
TODO_REFLECTION_MIN_ROUNDS=2
TODO_REFLECTION_MAX_ROUNDS=5
```

## æ°æ®å­å¨

### å­å¨ç»æ

```
data/todo/
âââ todos.json              # Todoæ°æ®
âââ verifications/          # éªæ¶ææ¡£
    âââ verify_xxx.md
    âââ verify_yyy.md
```

### æ°æ®æ ¼å¼

```json
{
  "phases": [
    {
      "id": "phase_xxx",
      "title": "é¶æ®µæ é¢",
      "status": "completed",
      "tasks": [
        {
          "id": "task_xxx",
          "title": "ä»»å¡æ é¢",
          "status": "completed",
          "steps": [...],
          "verification_document": {...}
        }
      ],
      "reflections": [...]
    }
  ],
  "updated_at": "2024-01-01T12:00:00"
}
```

## æ©å±å¼å?
### èªå®ä¹åæçæå¨

```python
class CustomReflectionGenerator:
    async def generate(
        self,
        phase: TodoPhase,
        round_number: int,
        llm_client: Any
    ) -> ReflectionResult:
        """èªå®ä¹åæçæé»è¾"""
        
        # æå»ºæç¤ºè¯?        prompt = self._build_prompt(phase, round_number)
        
        # è°ç¨LLM
        response = await llm_client.generate(prompt)
        
        # è§£æç»æ
        return self._parse_response(response, round_number)
```

### èªå®ä¹éªæ¶æ åçæå¨

```python
class CustomAcceptanceCriteriaGenerator:
    def generate(self, task: TodoTask) -> List[str]:
        """èªå®ä¹éªæ¶æ åçæé»è¾"""
        criteria = []
        
        # æ ¹æ®ä»»å¡ç±»åçæä¸åçéªæ¶æ å?        if task.title.startswith("å¼å?):
            criteria.extend([
                "ä»£ç éè¿ååæµè¯",
                "ä»£ç éè¿Code Review",
                "ææ¡£å·²æ´æ?
            ])
        
        return criteria
```

## æä½³å®è·?
### 1. åçååé¶æ®µåä»»å?
- é¶æ®µåºè¯¥æ¯ç¸å¯¹ç¬ç«çå¤§çå·¥ä½åå
- ä»»å¡åºè¯¥æ¯å¯ä»¥å¨è¾ç­æ¶é´åå®æç
- æ­¥éª¤åºè¯¥æ¯å·ä½çãå¯æ§è¡çæä½?
### 2. è®¾ç½®åççåæè½®æ?
- ç®åé¶æ®µï¼2è½®åæ?- å¤æé¶æ®µï¼?-5è½®åæ?- æ ¹æ®é¶æ®µéè¦æ§è°æ?
### 3. å©ç¨ä¾èµå³ç³»

```python
# åå»ºæä¾èµå³ç³»çæ­¥éª¤
step1 = await todo_mgr.create_step(
    task_id=task.id,
    content="è®¾è®¡æ°æ®æ¨¡å"
)

step2 = await todo_mgr.create_step(
    task_id=task.id,
    content="å®ç°ä¸å¡é»è¾",
    dependencies=[step1.id]  # ä¾èµstep1
)
```

### 4. å®ææ£æ¥ç»è®¡ä¿¡æ?
```python
# å®æè·åç»è®¡ä¿¡æ¯
stats = todo_mgr.get_statistics()

# æ£æ¥è¿åº?if stats['progress']['phases'] < 0.5:
    logger.warning("æ´ä½è¿åº¦ä½äº50%")
```
