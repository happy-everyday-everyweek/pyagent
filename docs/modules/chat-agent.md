# 交互模块文档 v0.8.0

本文档详细描述PyAgent v0.8.0交互模块（原Chat Agent）的设计和实现�?
## 概述

Chat Agent是PyAgent系统中负责处理即时通讯场景的核心模块。它采用心流(HeartFlow)架构，实现连续的消息监控和智能回复�?
## 核心组件

### 1. HeartFChatting (心流聊天)

**文件**: `src/chat/heart_flow/heartf_chatting.py`

**职责**: 管理一个连续的Focus Chat循环，负责消息监控、触发判断和回复生成�?
#### 主要属�?
| 属�?| 类型 | 说明 |
|------|------|------|
| stream_id | str | 聊天流唯一标识 |
| running | bool | 循环运行状�?|
| history_loop | List[CycleDetail] | 循环历史记录 |
| consecutive_no_reply_count | int | 连续未回复计�?|
| talk_value | float | 发言意愿�?0-1) |
| planner_smooth | float | 规划器平滑时�?|

#### 工作流程

```
┌─────────────────────────────────────────────────────────────�?�?                   HeartFChatting 工作流程                   �?├─────────────────────────────────────────────────────────────�?�?                                                            �?�? ┌─────────────�?                                          �?�? �?  启动      �?                                          �?�? �? start()    �?                                          �?�? └──────┬──────�?                                          �?�?        �?                                                  �?�?        �?                                                  �?�? ┌─────────────�?    �?     ┌─────────────�?              �?�? �? 检查消�?  │────────────▶│  等待       �?              �?�? �? _loopbody()�?            �? sleep(0.2) �?              �?�? └──────┬──────�?            └─────────────�?              �?�?        �?�?                                               �?�?        �?                                                  �?�? ┌─────────────�?                                          �?�? �? 检查@提及  �?                                          �?�? �? 频率控制   �?                                          �?�? └──────┬──────�?                                          �?�?        �?                                                  �?�?        �?                                                  �?�? ┌─────────────�?                                          �?�? �? 观察规划   �?                                          �?�? �? _observe() �?                                          �?�? └──────┬──────�?                                          �?�?        �?                                                  �?�?        �?                                                  �?�? ┌─────────────�?                                          �?�? �? 执行动作   �?                                          �?�? �? _execute_  �?                                          �?�? �? action()   �?                                          �?�? └──────┬──────�?                                          �?�?        �?                                                  �?�?        �?                                                  �?�? ┌─────────────�?                                          �?�? �? 记录循环   �?                                          �?�? �? end_cycle()�?                                          �?�? └──────┬──────�?                                          �?�?        �?                                                  �?�?        └───────────────────────────────────────────────�?  �?�?                                                        �?  �?�?        ◄───────────────────────────────────────────────�?  �?�?                     (循环直到停止)                          �?�?                                                            �?└─────────────────────────────────────────────────────────────�?```

#### 触发条件

1. **消息数量**: 达到阈值（默认1条）
2. **@提及**: 用户@机器�?3. **频率控制**: talk_value决定的发言意愿

#### 代码示例

```python
from src.interaction.heart_flow.heartf_chatting import HeartFChatting, MessageInfo

# 创建实例
chat = HeartFChatting(
    chat_id="group_123",
    config={
        "talk_value": 0.5,
        "planner_smooth": 0.5,
        "max_context_size": 50
    }
)

# 启动
await chat.start()

# 推送消�?message = MessageInfo(
    message_id="msg_001",
    chat_id="group_123",
    user_id="user_001",
    platform="qq",
    content="你好",
    is_mentioned=True
)
await chat.push_message(message)

# 停止
await chat.stop()
```

---

### 2. ActionPlanner (动作规划�?

**文件**: `src/interaction/planner/action_planner.py`

**职责**: 使用LLM规划回复动作�?
#### 支持的动�?
| 动作 | 说明 | 参数 |
|------|------|------|
| reply | 回复消息 | target_message_id |
| no_reply | 保持沉默 | �?|

#### 规划流程

1. **构建提示�?*: 整合聊天内容、历史记录、可选动�?2. **调用LLM**: 获取规划结果
3. **解析JSON**: 提取动作列表
4. **强制回复检�?*: 确保@提及时必回复

#### 提示词结�?
```
当前时间�?024-01-01 12:00:00
你的名字是Assistant

**聊天内容**
[m1] 用户A: 你好
[m2] 用户B: 大家�?
**可选的action**
reply
动作描述：回复消�?{"action":"reply", "target_message_id":"消息id(m+数字)"}

no_reply
动作描述：保持沉�?{"action":"no_reply"}

**你之前的action执行和思考记�?*
�?
请选择**可选的**且符合使用条件的action...
```

---

### 3. ActionManager (动作管理�?

**文件**: `src/interaction/planner/action_manager.py`

**职责**: 管理可用动作，支持动态注册和注销�?
#### 动作定义

```python
@dataclass
class ActionInfo:
    name: str                    # 动作名称
    description: str             # 动作描述
    parameters: Dict[str, str]   # 参数说明
    requirements: List[str]      # 使用条件
    parallel_action: bool        # 是否可并�?```

---

### 4. ReplyerManager (回复管理�?

**文件**: `src/chat/replyer/replyer_manager.py`

**职责**: 管理回复生成器，根据聊天类型选择生成策略�?
#### 回复生成�?
| 生成�?| 用�?| 特点 |
|--------|------|------|
| GroupGenerator | 群聊回复 | 考虑群氛围、@关系 |
| PrivateGenerator | 私聊回复 | 个性化、深入对�?|

---

## 频率控制

### FrequencyControlManager

**文件**: `src/interaction/heart_flow/frequency_control.py`

**职责**: 控制聊天频率，避免过于频繁的发言�?
#### 控制策略

```python
class FrequencyControl:
    def should_reply(self, talk_value: float) -> bool:
        """根据talk_value决定是否回复�?        
        talk_value越高，回复概率越大�?        同时考虑�?        - 距离上次回复的时�?        - 今日发言次数
        - 聊天活跃�?        """
        pass
```

---

## 聊天工具

### 1. MemoryTool (记忆工具)

**文件**: `src/chat/tools/memory_tool.py`

**功能**: 检索和存储对话相关的记忆�?
### 2. ExecuteTool (执行工具)

**文件**: `src/chat/tools/execute_tool.py`

**功能**: 调用ExecutorAgent执行复杂任务�?
### 3. SearchTool (搜索工具)

**文件**: `src/chat/tools/search_tool.py`

**功能**: 搜索网络信息�?
### 4. ReadTool (阅读工具)

**文件**: `src/chat/tools/read_tool.py`

**功能**: 阅读文件或网页内容�?
---

## 配置选项

```yaml
# config/chat.yaml
chat:
  heart_flow:
    planner_smooth: 0.5        # 规划器平滑时�?�?
    talk_value: 0.5            # 发言意愿�?    max_context_size: 50       # 最大上下文大小
    
  action_planner:
    max_plan_history: 20       # 最大规划历史记录数
    
  frequency_control:
    enabled: true
    min_interval: 10           # 最小发言间隔(�?
    max_daily_messages: 1000   # 每日最大消息数
    
  replyer:
    group:
      max_length: 500          # 群聊最大回复长�?      emoji_probability: 0.3   # 使用表情概率
    private:
      max_length: 1000         # 私聊最大回复长�?```

---

## 扩展开�?
### 创建自定义动�?
```python
from src.interaction.planner.action_manager import ActionManager, ActionInfo

# 定义动作
action_info = ActionInfo(
    name="custom_action",
    description="自定义动�?,
    parameters={
        "param1": "参数1说明"
    },
    requirements=["条件1", "条件2"],
    parallel_action=True
)

# 注册动作
action_manager = ActionManager()
action_manager.register_action(action_info)

# 实现处理�?async def handle_custom_action(action_data: dict) -> str:
    param1 = action_data.get("param1")
    # 处理逻辑
    return "处理结果"

# 注册处理�?chat.register_action_handler("custom_action", handle_custom_action)
```

---

## 性能优化

### 1. 消息队列优化

- 使用`asyncio.Queue`实现异步消息处理
- 设置队列大小限制，防止内存溢�?
### 2. LLM调用优化

- 缓存规划结果
- 批量处理消息
- 使用流式响应

### 3. 上下文管�?
- 定期清理过期上下�?- 压缩历史消息
- 智能选择相关上下�?
