# 消息队列与中断机制

本文档描述 OpenAkita 在 Agent 任务执行期间，如何处理新到达的用户消息。

## 概述

OpenAkita 采用 **双队列 + 会话级锁** 的机制来管理并发消息：

- 会话空闲时，消息直接进入主队列立即处理
- 会话忙碌时，消息进入该会话专属的中断队列排队等待
- 停止指令可以立即取消正在执行的任务

## 核心数据结构

### 1. 主消息队列

```python
_message_queue: asyncio.Queue[UnifiedMessage]
```

所有空闲会话的消息都通过这个队列进行处理，消息循环从中取出消息逐条执行。

### 2. 会话级中断队列

```python
_interrupt_queues: dict[str, asyncio.PriorityQueue[InterruptMessage]]
```

每个正在处理的会话拥有独立的优先级队列。`session_key` 格式为 `{channel}:{chat_id}:{user_id}`，确保会话级隔离。

### 3. 会话处理状态

```python
_processing_sessions: dict[str, bool]
```

标记哪些会话正在执行任务，用于判断新消息应该进入主队列还是中断队列。

### 4. 中断锁

```python
_interrupt_lock: asyncio.Lock()
```

保护对 `_processing_sessions` 和 `_interrupt_queues` 的并发访问，防止竞态条件。

## 中断优先级

```python
class InterruptPriority(Enum):
    NORMAL = 0  # 普通消息，排队等待
    HIGH   = 1  # 高优先级，在工具间隙插入
    URGENT = 2  # 紧急，尝试立即中断
```

优先级队列按 `priority` 降序排列，同优先级按到达时间排序。默认入队优先级为 `HIGH`。

## 消息流转流程

### 流程图

```
用户发送消息
      │
      ▼
 IM 适配器接收
 (DingTalk/Telegram/...)
      │
      ▼
 _on_message() 回调
      │
      ▼
 ┌─────────────────────┐
 │ 获取 _interrupt_lock │
 │ 检查会话处理状态      │
 └─────────┬───────────┘
           │
     ┌─────┴─────┐
     │ 会话忙碌？ │
     └─────┬─────┘
       ┌───┴───┐
       │       │
      Yes      No
       │       │
       ▼       ▼
  ┌─────────┐  ┌──────────────┐
  │是停止指令?│  │ 放入主队列    │
  │         │  │ _message_queue│
  └────┬────┘  └──────────────┘
   ┌───┴───┐
   │       │
  Yes      No
   │       │
   ▼       │
 立即取消   │
 当前任务   │
   │       │
   ▼       ▼
 ┌──────────────────┐
 │ 放入中断队列       │
 │ _interrupt_queues │
 │ (排队等待)        │
 └──────────────────┘
```

### 详细步骤

#### 场景 1：会话空闲

1. 消息到达 `_on_message()`
2. 获取 `_interrupt_lock`，检查 `_processing_sessions[session_key]` 为 `False`
3. 消息放入 `_message_queue`
4. 消息循环取出消息，调用 `_handle_message()` 处理
5. 标记 `_processing_sessions[session_key] = True`
6. 完成处理后标记回 `False`

#### 场景 2：会话忙碌 + 普通消息

1. 消息到达 `_on_message()`
2. 获取 `_interrupt_lock`，检查 `_processing_sessions[session_key]` 为 `True`
3. 消息放入 `_interrupt_queues[session_key]`（优先级 `HIGH`）
4. `_on_message()` 立即返回，**不阻塞**
5. 当前任务继续执行
6. 任务完成后，`_process_pending_interrupts()` 依次取出中断队列中的消息处理

#### 场景 3：会话忙碌 + 停止指令

1. 消息到达 `_on_message()`
2. 获取 `_interrupt_lock`，检查会话正在处理中
3. 检测到消息是停止指令（如 "停止"、"stop"、"取消" 等）
4. **立即调用** `agent_handler.cancel_current_task()`，设置取消标志
5. 消息同时放入中断队列（用于任务取消后的确认回复）
6. Agent 在下一个检查点检测到取消标志，退出当前任务循环

## 停止指令列表

以下指令会被识别为停止命令，触发立即取消：

```
停止 | 停 | stop | 停止执行 | 取消
```

## Agent 端的中断检查

### 检查时机

Agent 在工具调用的间隙检查中断队列，**不会在工具执行过程中中断**：

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│ 工具调用 1 │ ──▶ │ 检查中断队列   │ ──▶ │ 工具调用 2 │
└──────────┘     └──────────────┘     └──────────┘
                       │
                  有中断消息？
                   ┌───┴───┐
                  Yes      No
                   │       │
                   ▼       ▼
              插入中断    继续执行
              消息处理    下一个工具
```

### 开关控制

```python
self._interrupt_enabled = True  # 默认开启（会话模式）
```

可以通过 `_interrupt_enabled` 控制是否在工具间隙检查中断。

### 取消机制

```python
def cancel_current_task(self, reason: str) -> None:
    self._task_cancelled = True
    self._cancel_reason = reason
```

设置取消标志后，Agent 在下一个循环迭代中检测到并退出。

## 任务完成后的清理

当前任务完成后（无论成功还是被取消），会执行以下清理流程：

```python
# _handle_message() 中：

# 步骤 10：处理剩余的中断消息
await self._process_pending_interrupts(session_key, session)

# finally 块：标记会话处理完成
async with self._interrupt_lock:
    self._mark_session_processing(session_key, False)
```

`_process_pending_interrupts()` 会循环取出中断队列中的所有消息，逐条处理：

1. 预处理媒体（下载图片、语音转文字等）
2. 将消息添加到会话历史（标记 `is_interrupt=True`）
3. 调用 Agent 生成回复
4. 将回复发送给用户

## 行为总结

| 场景 | 行为 | 延迟 |
|------|------|------|
| 会话空闲 | 立即处理 | 无 |
| 会话忙碌 + 普通消息 | 排队等待 | 等当前任务完成 |
| 会话忙碌 + 停止指令 | 立即取消当前任务 | 等到下一个中断检查点 |
| 工具执行中 | 不中断，工具运行至完成 | 等工具执行完成 |
| 工具调用间隙 | 检查中断队列 | 几乎无 |
| 任务完成后 | 依次处理积压消息 | 逐条顺序处理 |

## 会话隔离

中断机制是**会话级别**的：

- 每个 `{channel}:{chat_id}:{user_id}` 组合拥有独立的中断队列
- 用户 A 的任务不影响用户 B 的消息处理
- 同一用户在不同渠道的会话也是独立的

## 相关代码

| 文件 | 关键内容 |
|------|---------|
| `channels/gateway.py` | 双队列定义、消息路由、中断处理 |
| `core/agent.py` | 中断检查、任务取消、停止指令识别 |
| `channels/adapters/*.py` | 各渠道适配器的消息接收与分发 |
