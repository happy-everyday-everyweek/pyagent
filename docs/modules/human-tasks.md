# PyAgent 人工任务管理系统

**版本**: v0.8.0  
**模块路径**: `src/human_tasks/`  
**最后更新**: 2025-04-03

---

## 概述

人工任务管理系统（Human Tasks）是 PyAgent v0.8.0 引入的全新模块，专为人类用户设计的高效任务管理解决方案。与 AI 原生的 Todo 系统不同，人工任务系统更加注重人类的实际工作习惯，提供直观的任务创建、跟踪和完成功能。

### 核心特性

- **四级优先级系统**: 低/中/高/紧急，帮助用户快速识别重要任务
- **子任务支持**: 将大任务拆分为可管理的小步骤
- **时间提醒**: 截止日期和提醒功能，确保不遗漏重要事项
- **分类与标签**: 灵活的任务组织方式
- **智能统计**: 任务完成率、过期任务等数据分析
- **持久化存储**: JSON 格式本地存储，数据安全可靠

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Human Task System                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  TaskManager │    │   HumanTask  │    │   SubTask    │  │
│  │   (管理器)    │◄──►│   (任务模型)  │◄──►│   (子任务)    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                    │          │
│         ▼                   ▼                    ▼          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              JSON Persistence Layer                  │   │
│  │                 (data/human_tasks/)                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 任务管理器 (TaskManager)

任务管理器是人工任务系统的核心入口，提供完整的任务生命周期管理。

**位置**: `src/human_tasks/manager.py`

```python
from src.human_tasks.manager import TaskManager, task_manager

# 使用全局实例
manager = task_manager

# 或创建新实例
manager = TaskManager(data_dir="data/human_tasks")
```

#### 主要方法

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `create_task()` | 创建新任务 | `HumanTask` |
| `update_task()` | 更新任务 | `HumanTask \| None` |
| `delete_task()` | 删除任务 | `bool` |
| `complete_task()` | 完成任务 | `HumanTask \| None` |
| `start_task()` | 开始任务（标记为进行中） | `HumanTask \| None` |
| `cancel_task()` | 取消任务 | `HumanTask \| None` |
| `get_task()` | 获取单个任务 | `HumanTask \| None` |
| `list_tasks()` | 列出任务（支持过滤） | `list[HumanTask]` |
| `search_tasks()` | 搜索任务 | `list[HumanTask]` |
| `get_overdue_tasks()` | 获取过期任务 | `list[HumanTask]` |
| `get_tasks_due_today()` | 获取今天到期的任务 | `list[HumanTask]` |
| `get_statistics()` | 获取统计信息 | `dict` |

#### 使用示例

```python
from datetime import datetime, timedelta
from src.human_tasks.manager import task_manager
from src.human_tasks.task import Priority

# 创建任务
task = task_manager.create_task(
    title="完成项目文档",
    description="编写 PyAgent v0.8.0 的用户手册",
    priority=Priority.HIGH,
    due_date=datetime.now() + timedelta(days=3),
    category="工作",
    tags=["文档", "重要"],
    subtasks=["编写概述", "编写API文档", "编写示例代码"]
)

print(f"任务创建成功: {task.task_id}")

# 列出所有待处理任务
pending_tasks = task_manager.list_tasks(status=TaskStatus.PENDING)

# 获取今天到期的任务
today_tasks = task_manager.get_tasks_due_today()

# 完成任务
task_manager.complete_task(task.task_id)

# 获取统计信息
stats = task_manager.get_statistics()
print(f"完成率: {stats['completion_rate']:.1f}%")
```

---

### 2. 任务数据模型 (HumanTask)

**位置**: `src/human_tasks/task.py`

```python
@dataclass
class HumanTask:
    task_id: str                    # 唯一标识符
    title: str                      # 任务标题
    description: str                # 任务描述
    status: TaskStatus              # 任务状态
    priority: Priority              # 优先级
    due_date: datetime | None       # 截止日期
    reminder: datetime | None       # 提醒时间
    category: str                   # 分类
    tags: list[str]                 # 标签列表
    subtasks: list[SubTask]         # 子任务列表
    attachments: list[str]          # 附件列表
    created_at: datetime            # 创建时间
    updated_at: datetime            # 更新时间
    completed_at: datetime | None   # 完成时间
```

#### 任务状态 (TaskStatus)

```python
class TaskStatus(Enum):
    PENDING = "pending"         # 待处理
    IN_PROGRESS = "in_progress" # 进行中
    COMPLETED = "completed"     # 已完成
    CANCELLED = "cancelled"     # 已取消
```

#### 优先级 (Priority)

```python
class Priority(Enum):
    LOW = "low"         # 低优先级
    MEDIUM = "medium"   # 中优先级（默认）
    HIGH = "high"       # 高优先级
    URGENT = "urgent"   # 紧急
```

#### 子任务 (SubTask)

```python
@dataclass
class SubTask:
    id: str             # 子任务ID
    title: str          # 标题
    completed: bool     # 是否完成
    created_at: datetime
    completed_at: datetime | None
```

#### 任务方法

```python
# 状态检查
task.is_overdue()       # 是否过期
task.is_due_today()     # 是否今天到期
task.is_completed()     # 是否已完成
task.is_in_progress()   # 是否进行中

# 进度计算
task.get_progress()     # 返回 0.0 - 100.0

# 子任务操作
task.add_subtask("子任务标题")
task.complete_subtask(subtask_id)
task.remove_subtask(subtask_id)

# 状态变更
task.mark_completed()
task.mark_in_progress()
task.mark_cancelled()

# 更新任务
task.update(title="新标题", priority=Priority.HIGH)

# 序列化
task.to_dict()          # 转为字典
HumanTask.from_dict(data)  # 从字典创建
```

---

## 使用场景

### 场景1: 个人日常任务管理

```python
from datetime import datetime, timedelta
from src.human_tasks.manager import task_manager
from src.human_tasks.task import Priority

# 创建购物清单
shopping_task = task_manager.create_task(
    title="周末购物",
    description="购买本周所需的生活用品",
    category="生活",
    due_date=datetime.now() + timedelta(days=2),
    subtasks=[
        "购买牛奶和鸡蛋",
        "购买新鲜蔬菜和水果",
        "购买日用品",
        "取快递"
    ]
)

# 创建学习任务
study_task = task_manager.create_task(
    title="学习 Python 异步编程",
    description="深入学习 asyncio 和并发编程",
    priority=Priority.HIGH,
    category="学习",
    tags=["Python", "编程", "进阶"],
    due_date=datetime.now() + timedelta(days=7)
)
```

### 场景2: 工作项目管理

```python
# 创建项目任务
project_task = task_manager.create_task(
    title="PyAgent v0.8.0 文档更新",
    description="全面更新所有模块文档",
    priority=Priority.URGENT,
    category="工作",
    tags=["PyAgent", "文档", "v0.8.0"],
    due_date=datetime.now() + timedelta(days=1),
    subtasks=[
        "更新 README.md",
        "更新 AGENTS.md",
        "更新 CHANGELOG.md",
        "创建新模块文档"
    ]
)

# 开始任务
task_manager.start_task(project_task.task_id)

# 完成子任务
for subtask in project_task.subtasks[:2]:
    task_manager.complete_subtask(project_task.task_id, subtask.id)

# 检查进度
progress = project_task.get_progress()
print(f"当前进度: {progress}%")
```

### 场景3: 任务统计与回顾

```python
# 获取所有统计信息
stats = task_manager.get_statistics()

print(f"""
任务统计报告
============
总任务数: {stats['total_tasks']}
完成率: {stats['completion_rate']:.1f}%

状态分布:
  - 待处理: {stats['status_distribution']['pending']}
  - 进行中: {stats['status_distribution']['in_progress']}
  - 已完成: {stats['status_distribution']['completed']}
  - 已取消: {stats['status_distribution']['cancelled']}

优先级分布:
  - 紧急: {stats['priority_distribution']['urgent']}
  - 高: {stats['priority_distribution']['high']}
  - 中: {stats['priority_distribution']['medium']}
  - 低: {stats['priority_distribution']['low']}

需要关注:
  - 过期任务: {stats['overdue_tasks']}
  - 今天到期: {stats['due_today_tasks']}
""")

# 获取过期任务并处理
overdue = task_manager.get_overdue_tasks()
for task in overdue:
    print(f"过期任务: {task.title} (截止: {task.due_date})")
```

---

## 数据存储

### 存储结构

```
data/human_tasks/
└── tasks.json          # 所有任务数据
```

### 数据格式

```json
{
  "tasks": [
    {
      "task_id": "task_abc123",
      "title": "示例任务",
      "description": "任务描述",
      "status": "pending",
      "priority": "high",
      "due_date": "2025-04-10T18:00:00",
      "reminder": null,
      "category": "工作",
      "tags": ["重要", "紧急"],
      "subtasks": [
        {
          "id": "sub_xxx",
          "title": "子任务1",
          "completed": false,
          "created_at": "2025-04-03T10:00:00",
          "completed_at": null
        }
      ],
      "attachments": [],
      "created_at": "2025-04-03T10:00:00",
      "updated_at": "2025-04-03T10:00:00",
      "completed_at": null
    }
  ],
  "updated_at": "2025-04-03T12:00:00"
}
```

---

## API 接口

### REST API

#### 创建任务
```http
POST /api/human-tasks/tasks
Content-Type: application/json

{
  "title": "任务标题",
  "description": "任务描述",
  "priority": "high",
  "due_date": "2025-04-10T18:00:00",
  "category": "工作",
  "tags": ["标签1", "标签2"]
}
```

#### 获取任务列表
```http
GET /api/human-tasks/tasks?status=pending&category=工作
```

#### 更新任务
```http
PUT /api/human-tasks/tasks/{task_id}
Content-Type: application/json

{
  "title": "新标题",
  "priority": "urgent"
}
```

#### 完成任务
```http
POST /api/human-tasks/tasks/{task_id}/complete
```

#### 删除任务
```http
DELETE /api/human-tasks/tasks/{task_id}
```

#### 获取统计信息
```http
GET /api/human-tasks/statistics
```

---

## 配置选项

### 配置示例

```python
# config/human_tasks.yaml
human_tasks:
  data_dir: "data/human_tasks"
  default_priority: "medium"
  enable_reminders: true
  reminder_check_interval: 60  # 秒
```

---

## 最佳实践

### 1. 任务命名规范

- 使用动词开头，如"完成..."、"编写..."、"审查..."
- 标题简洁明了，不超过50个字符
- 详细描述放在 description 中

### 2. 优先级使用建议

- **URGENT**: 立即处理，阻塞其他工作
- **HIGH**: 今天或明天必须完成
- **MEDIUM**: 本周内完成（默认）
- **LOW**: 有空时处理

### 3. 分类和标签策略

```python
# 推荐分类
categories = ["工作", "学习", "生活", "健康", "财务"]

# 标签用于跨分类标记
tags = ["重要", "紧急", "长期", "重复", "等待中"]
```

### 4. 子任务拆分原则

- 每个子任务应在 2 小时内完成
- 子任务数量建议 3-7 个
- 按执行顺序排列

---

## 故障排除

### 常见问题

**Q: 任务数据丢失怎么办？**  
A: 检查 `data/human_tasks/tasks.json` 文件是否存在。系统会自动备份，可以尝试恢复备份文件。

**Q: 如何批量导入任务？**  
A: 直接编辑 JSON 文件，然后重启服务即可。

**Q: 任务提醒不工作？**  
A: 确保设置了 `reminder` 字段，且系统时间正确。

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持任务 CRUD 操作
- 支持子任务管理
- 支持优先级和分类
- 支持时间提醒
- 支持统计功能

---

## 相关文档

- [Todo 系统](./todo-system.md) - AI 原生任务管理
- [记忆系统](./memory-system.md) - 长期记忆存储
- [API 文档](../api.md) - 完整 API 参考
