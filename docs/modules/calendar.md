# PyAgent 日历管理系统

**版本**: v0.8.0  
**模块路径**: `src/calendar/`  
**最后更新**: 2025-04-03

---

## 概述

日历管理系统是 PyAgent v0.8.0 引入的全新模块，提供完整的日程管理和事件提醒功能。支持事件的创建、编辑、删除，以及灵活的重复规则和提醒机制，帮助用户高效管理时间和日程。

### 核心特性

- **事件管理**: 完整的 CRUD 操作，支持标题、描述、地点、参与者
- **重复事件**: 支持日/周/月/年重复规则
- **多种提醒方式**: 邮件、推送、短信提醒
- **ICS 格式支持**: 与主流日历软件兼容
- **智能搜索**: 按标题、描述、地点、参与者搜索
- **统计功能**: 事件数量、状态分布等数据分析

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                   Calendar System                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ CalendarManager │    │ ReminderService │                 │
│  │    (日历管理器)  │◄──►│    (提醒服务)    │                 │
│  └────────┬────────┘    └─────────────────┘                 │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Event (事件模型)                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │  │  Reminder│  │Recurrence│  │  Status  │          │    │
│  │  │  (提醒)  │  │  (重复)  │  │  (状态)  │          │    │
│  │  └──────────┘  └──────────┘  └──────────┘          │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              JSON Persistence Layer                  │    │
│  │                 (data/calendar/)                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 日历管理器 (CalendarManager)

日历管理器是日历系统的核心入口，提供完整的事件生命周期管理。

**位置**: `src/calendar/manager.py`

```python
from src.calendar.manager import CalendarManager

# 创建管理器实例
manager = CalendarManager(data_dir="data/calendar")
```

#### 主要方法

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `create_event()` | 创建事件 | `Event` |
| `update_event()` | 更新事件 | `Event \| None` |
| `delete_event()` | 删除事件 | `bool` |
| `get_event()` | 获取单个事件 | `Event \| None` |
| `list_events()` | 列出事件（支持日期范围） | `list[Event]` |
| `search_events()` | 搜索事件 | `list[Event]` |
| `add_reminder()` | 添加提醒 | `Reminder \| None` |
| `remove_reminder()` | 移除提醒 | `bool` |
| `get_statistics()` | 获取统计信息 | `dict` |

#### 使用示例

```python
from datetime import datetime, timedelta
from src.calendar.manager import CalendarManager
from src.calendar.event import EventStatus

manager = CalendarManager()

# 创建事件
event = manager.create_event({
    "title": "PyAgent 周会",
    "description": "讨论 v0.8.0 版本发布计划",
    "start_time": datetime.now() + timedelta(days=1, hours=10),
    "end_time": datetime.now() + timedelta(days=1, hours=11),
    "location": "会议室 A",
    "attendees": ["user1@example.com", "user2@example.com"],
    "reminders": [
        {
            "remind_at": datetime.now() + timedelta(days=1, hours=9, minutes=30),
            "method": "email"
        }
    ]
})

print(f"事件创建成功: {event.event_id}")

# 列出本周事件
week_start = datetime.now()
week_end = week_start + timedelta(days=7)
week_events = manager.list_events(week_start, week_end)

# 搜索会议
meetings = manager.search_events("会议")

# 获取统计信息
stats = manager.get_statistics()
print(f"总事件数: {stats['total_events']}")
```

---

### 2. 事件数据模型 (Event)

**位置**: `src/calendar/event.py`

```python
@dataclass
class Event:
    event_id: str                   # 唯一标识符
    title: str                      # 事件标题
    description: str                # 事件描述
    start_time: datetime            # 开始时间
    end_time: datetime              # 结束时间
    location: str                   # 地点
    attendees: list[str]            # 参与者列表
    reminders: list[Reminder]       # 提醒列表
    recurrence: RecurrenceRule      # 重复规则
    status: EventStatus             # 事件状态
    created_at: datetime            # 创建时间
    updated_at: datetime            # 更新时间
```

#### 事件状态 (EventStatus)

```python
class EventStatus(Enum):
    CONFIRMED = "confirmed"   # 已确认
    TENTATIVE = "tentative"   # 暂定
    CANCELLED = "cancelled"   # 已取消
```

#### 提醒 (Reminder)

```python
@dataclass
class Reminder:
    reminder_id: str        # 提醒ID
    event_id: str           # 关联事件ID
    remind_at: datetime     # 提醒时间
    method: str             # 提醒方式: "email", "push", "sms"
    sent: bool              # 是否已发送
```

#### 重复规则 (RecurrenceRule)

```python
@dataclass
class RecurrenceRule:
    frequency: RecurrenceFrequency  # 频率: DAILY, WEEKLY, MONTHLY, YEARLY
    interval: int                   # 间隔（每N天/周/月/年）
    count: int | None              # 重复次数
    until: datetime | None         # 结束日期
    by_day: list[str]              # 按星期几（如 ["MO", "WE", "FR"]）
    by_month: list[int]            # 按月份
    by_month_day: list[int]        # 按日期
```

```python
class RecurrenceFrequency(Enum):
    DAILY = "daily"       # 每天
    WEEKLY = "weekly"     # 每周
    MONTHLY = "monthly"   # 每月
    YEARLY = "yearly"     # 每年
```

#### 事件方法

```python
# 序列化
event.to_dict()          # 转为字典
Event.from_dict(data)    # 从字典创建

# 生成ID
Event.generate_id()      # 生成唯一事件ID

# 更新时间戳
event.update_timestamp() # 更新 updated_at
```

---

## 使用场景

### 场景1: 创建一次性会议

```python
from datetime import datetime, timedelta
from src.calendar.manager import CalendarManager

manager = CalendarManager()

# 创建团队会议
event = manager.create_event({
    "title": "产品评审会议",
    "description": "评审 Q2 产品路线图",
    "start_time": datetime(2025, 4, 10, 14, 0),
    "end_time": datetime(2025, 4, 10, 15, 30),
    "location": "线上会议室: https://meet.example.com/abc",
    "attendees": [
        "pm@example.com",
        "dev@example.com",
        "design@example.com"
    ],
    "reminders": [
        {
            "remind_at": datetime(2025, 4, 10, 13, 45),
            "method": "email"
        },
        {
            "remind_at": datetime(2025, 4, 10, 13, 55),
            "method": "push"
        }
    ]
})

print(f"会议已创建: {event.title}")
print(f"时间: {event.start_time} - {event.end_time}")
```

### 场景2: 创建重复事件

```python
from src.calendar.event import RecurrenceRule, RecurrenceFrequency

# 创建每周团队例会
event = manager.create_event({
    "title": "每周站会",
    "description": "团队同步进度",
    "start_time": datetime(2025, 4, 7, 9, 30),
    "end_time": datetime(2025, 4, 7, 9, 45),
    "location": "会议室 B",
    "recurrence": RecurrenceRule(
        frequency=RecurrenceFrequency.WEEKLY,
        interval=1,
        by_day=["MO", "WE", "FR"]  # 周一、周三、周五
    ),
    "reminders": [
        {
            "remind_at": datetime(2025, 4, 7, 9, 25),
            "method": "push"
        }
    ]
})

# 创建每月报告提醒
event = manager.create_event({
    "title": "月度报告截止",
    "description": "提交本月工作报告",
    "start_time": datetime(2025, 4, 30, 17, 0),
    "end_time": datetime(2025, 4, 30, 17, 0),
    "recurrence": RecurrenceRule(
        frequency=RecurrenceFrequency.MONTHLY,
        interval=1,
        by_month_day=[30]  # 每月30日
    ),
    "reminders": [
        {
            "remind_at": datetime(2025, 4, 30, 9, 0),
            "method": "email"
        }
    ]
})
```

### 场景3: 日程查询与统计

```python
from datetime import datetime, timedelta

# 获取今天的事件
today = datetime.now().replace(hour=0, minute=0, second=0)
tomorrow = today + timedelta(days=1)
today_events = manager.list_events(today, tomorrow)

print(f"今天有 {len(today_events)} 个事件:")
for event in today_events:
    print(f"  - {event.title} ({event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')})")

# 获取本周事件
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=7)
week_events = manager.list_events(week_start, week_end)

# 搜索包含"会议"的事件
meetings = manager.search_events("会议")

# 获取统计信息
stats = manager.get_statistics()
print(f"""
日历统计
========
总事件数: {stats['total_events']}
已确认: {stats['confirmed']}
暂定: {stats['tentative']}
已取消: {stats['cancelled']}
即将开始: {stats['upcoming']}
已结束: {stats['past']}
""")
```

### 场景4: 管理提醒

```python
from datetime import datetime, timedelta

# 为现有事件添加提醒
event_id = "event_abc123"
reminder = manager.add_reminder(event_id, {
    "remind_at": datetime.now() + timedelta(hours=1),
    "method": "sms"
})

if reminder:
    print(f"提醒已添加: {reminder.reminder_id}")

# 移除提醒
success = manager.remove_reminder(event_id, reminder.reminder_id)
```

---

## 数据存储

### 存储结构

```
data/calendar/
└── events.json          # 所有事件数据
```

### 数据格式

```json
{
  "event_uuid_1": {
    "event_id": "event_uuid_1",
    "title": "团队会议",
    "description": "讨论项目进度",
    "start_time": "2025-04-10T14:00:00",
    "end_time": "2025-04-10T15:00:00",
    "location": "会议室 A",
    "attendees": ["user1@example.com"],
    "reminders": [
      {
        "reminder_id": "rem_uuid_1",
        "event_id": "event_uuid_1",
        "remind_at": "2025-04-10T13:30:00",
        "method": "email",
        "sent": false
      }
    ],
    "recurrence": {
      "frequency": "weekly",
      "interval": 1,
      "count": null,
      "until": null,
      "by_day": ["MO"],
      "by_month": [],
      "by_month_day": []
    },
    "status": "confirmed",
    "created_at": "2025-04-03T10:00:00",
    "updated_at": "2025-04-03T10:00:00"
  }
}
```

---

## API 接口

### REST API

#### 创建事件
```http
POST /api/calendar/events
Content-Type: application/json

{
  "title": "会议标题",
  "description": "会议描述",
  "start_time": "2025-04-10T14:00:00",
  "end_time": "2025-04-10T15:00:00",
  "location": "会议室 A",
  "attendees": ["user@example.com"],
  "reminders": [
    {
      "remind_at": "2025-04-10T13:30:00",
      "method": "email"
    }
  ]
}
```

#### 获取事件列表
```http
GET /api/calendar/events?start=2025-04-01T00:00:00&end=2025-04-30T23:59:59
```

#### 更新事件
```http
PUT /api/calendar/events/{event_id}
Content-Type: application/json

{
  "title": "新标题",
  "location": "新地点"
}
```

#### 删除事件
```http
DELETE /api/calendar/events/{event_id}
```

#### 添加提醒
```http
POST /api/calendar/events/{event_id}/reminders
Content-Type: application/json

{
  "remind_at": "2025-04-10T13:30:00",
  "method": "push"
}
```

#### 获取统计信息
```http
GET /api/calendar/statistics
```

---

## ICS 格式导出

### 导出事件为 ICS 格式

```python
from src.calendar.ics_exporter import ICSExporter

exporter = ICSExporter()

# 导出单个事件
ics_content = exporter.export_event(event)

# 导出所有事件
ics_content = exporter.export_all(manager.list_events())

# 保存到文件
with open("calendar.ics", "w", encoding="utf-8") as f:
    f.write(ics_content)
```

### 导入 ICS 文件

```python
from src.calendar.ics_importer import ICSImporter

importer = ICSImporter()
events = importer.import_file("calendar.ics")

for event_data in events:
    manager.create_event(event_data)
```

---

## 配置选项

### 配置示例

```python
# config/calendar.yaml
calendar:
  data_dir: "data/calendar"
  default_reminder_minutes: 15
  enable_email_reminders: true
  enable_push_reminders: true
  enable_sms_reminders: false
  reminder_check_interval: 60  # 秒
```

---

## 最佳实践

### 1. 事件命名规范

- 标题简洁明了，包含事件类型
- 描述详细说明目的和议程
- 地点使用完整地址或会议链接

### 2. 提醒设置建议

```python
# 重要会议：提前15分钟邮件 + 5分钟推送
reminders = [
    {"remind_at": start_time - timedelta(minutes=15), "method": "email"},
    {"remind_at": start_time - timedelta(minutes=5), "method": "push"}
]

# 日常提醒：提前5分钟推送
reminders = [
    {"remind_at": start_time - timedelta(minutes=5), "method": "push"}
]

# 截止日期：提前1天邮件 + 当天早上推送
reminders = [
    {"remind_at": start_time - timedelta(days=1), "method": "email"},
    {"remind_at": start_time.replace(hour=9), "method": "push"}
]
```

### 3. 重复事件使用场景

```python
# 每日：习惯追踪、每日站会
RecurrenceRule(frequency=RecurrenceFrequency.DAILY)

# 每周：团队例会、周报
RecurrenceRule(
    frequency=RecurrenceFrequency.WEEKLY,
    by_day=["MO", "WE", "FR"]
)

# 每月：月度报告、账单提醒
RecurrenceRule(
    frequency=RecurrenceFrequency.MONTHLY,
    by_month_day=[1, 15]
)

# 每年：生日、纪念日
RecurrenceRule(
    frequency=RecurrenceFrequency.YEARLY,
    by_month=[4],
    by_month_day=[3]
)
```

---

## 故障排除

### 常见问题

**Q: 事件时间显示不正确？**  
A: 确保使用 ISO 8601 格式的时间字符串，并注意时区设置。

**Q: 提醒没有触发？**  
A: 检查 `reminder_check_interval` 配置，确保提醒服务正在运行。

**Q: 如何批量导入事件？**  
A: 使用 ICS 导入功能，或编写脚本直接操作 JSON 文件。

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持事件 CRUD 操作
- 支持重复规则
- 支持多种提醒方式
- 支持 ICS 格式导入导出
- 支持统计功能

---

## 相关文档

- [人工任务系统](./human-tasks.md) - 任务管理
- [邮件客户端](./email-client.md) - 邮件提醒
- [API 文档](../api.md) - 完整 API 参考
