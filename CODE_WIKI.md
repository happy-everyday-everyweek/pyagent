# PyAgent 代码维基

## 1. 项目概述

PyAgent是一个企业级Python智能体框架，支持多平台IM集成、多智能体协作、ReAct推理引擎、MCP协议等高级特性。

### 1.1 核心特性

| 类别 | 特性 |
|------|------|
| **架构** | 多智能体架构（交互模块+执行模块）、ReAct推理引擎、热更新 |
| **IM支持** | QQ、钉钉、飞书、企业微信、微信、Kimi |
| **记忆系统** | 四级记忆架构（日常/周度/月度/季度）、项目记忆域 |
| **任务管理** | AI原生Todo系统、人工任务系统、日历管理 |
| **文档处理** | 原生文档编辑器（Word/Excel/PPT）、PDF处理 |
| **多媒体** | 原生视频编辑器、语音交互（ASR/TTS） |
| **自动化** | 浏览器自动化、工作流引擎 |
| **扩展** | MCP协议、ClawHub Skill、知识库系统 |

### 1.2 环境要求

- Python 3.10+
- Node.js 16+ (前端开发)
- 8GB+ 内存

## 2. 项目结构

```
pyagent/
├── src/                    # 源代码
│   ├── interaction/        # 交互模块 - 拟人化聊天、情感系统
│   ├── execution/          # 执行模块 - ReAct引擎、任务执行
│   ├── agents/             # 智能体系统 - Agent基类、注册中心
│   ├── human_tasks/        # 人工任务系统
│   ├── calendar/           # 日历管理
│   ├── email/              # 邮件客户端
│   ├── voice/              # 语音交互（ASR/TTS）
│   ├── browser/            # 浏览器自动化
│   ├── pdf/                # PDF处理
│   ├── storage/            # 分布式存储
│   ├── mobile/             # 移动端支持
│   ├── memory/             # 记忆系统
│   ├── todo/               # Todo系统
│   ├── llm/                # LLM客户端/网关
│   ├── im/                 # IM平台适配器
│   ├── mcp/                # MCP协议支持
│   └── web/                # Web服务
├── frontend/               # 前端代码(Vue.js)
├── config/                 # 配置文件
├── docs/                   # 文档目录
├── tests/                  # 测试套件
├── data/                   # 数据目录
├── skills/                 # 技能目录
└── android/                # Android项目
```

## 3. 系统架构

### 3.1 整体架构

PyAgent采用**模块化、分层架构**设计，将系统划分为多个独立的模块，每个模块负责特定的功能领域。

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                              PyAgent v0.8.0                                   │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                           前端层(Frontend)                           │ │
│ │ Vue.js 3 + TypeScript + Element Plus                                  │ │
│ │ - 聊天界面 | 任务视图 | 配置面板 | 文档编辑视图 | 视频编辑视图 | 域管理     │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│                                   ▼                                        │
│                                   │HTTP / WebSocket                        │
│                                   ▼                                        │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                            API层(API Layer)                          │ │
│ │ FastAPI + WebSocket                                                     │ │
│ │ - Chat API | Task API | Document API | Video API | Calendar API        │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│                                   ▼                                        │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                           核心服务层(Core Services)                      │ │
│ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │
│ │ │交互模块   │ │ │执行模块   │ │ │记忆系统   │ │ │Todo系统   │ │ │LLM客户端  │ │
│ │ │- HeartFlow│ │ │- ReAct引擎│ │ │- 四级架构  │ │ │- 三级任务  │ │ │- 多模型支持│ │
│ │ └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│                                   ▼                                        │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                         基础设施层(Infrastructure)                      │ │
│ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ │
│ │ │工具系统   │ │ │存储系统   │ │ │MCP协议   │ │ │技能系统   │ │ │设备管理   │ │
│ │ └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 模块关系

```
                    ┌────────────────────────┐
                    │  前端 (Vue.js)  │
                    └────────────────┬───────────────┘
                                     │
              ┌─────────────────────┼──────────────────────┐
              │             │             │
              ▼             ▼             ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │Chat API│  │Task API│  │Doc API │
        └────┬────┘  └────┬────┘  └────┬────┘
             │            │            │
             └────────────────────────┼────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │           │           │
              ▼           ▼           ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │交互模块 │ │执行模块 │ │核心服务 │
        │        │ │        │ │        │
        │心流聊天│ │任务管理│ │记忆系统│
        │拟人化   │ │规划智能体│ │Todo系统 │
        │行为规划│ │ReAct引擎│ │自我学习│
        └────┬────┘ └────┬────┘ └────┬────┘
             │           │           │
             └───────────────────────┼────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │          │          │
              ▼          ▼          ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │LLM客户端│ │工具系统 │ │存储系统 │
        └─────────┘ └─────────┘ └─────────┘
```

## 4. 核心模块

### 4.1 交互模块 (Interaction Module)

**位置**: `src/interaction/`

负责处理用户对话和交互，采用心流(HeartFlow)架构。

#### 4.1.1 架构设计

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     交互模块架构                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                   HeartFlow (心流)                    │ │
│ │ 管理连续的Focus Chat循环                              │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                │
│          ┌───────────────┼───────────────┐                                  │
│          │               │               │                                  │
│          ▼               ▼               ▼                                  │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐      │
│ │拟人化Prompt      │ │情感系统        │ │行为规划        │      │
│ │                  │ │                  │ │                  │      │
│ │构建自然        │ │10种情感类型    │ │回复时机        │      │
│ │语言化对话      │ │个性状态切换    │ │主动提问        │      │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘      │
```

#### 4.1.2 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| HeartFlow | `heart_flow/heartf_chatting.py` | 管理连续的对话循环 |
| HumanizedPrompt | `heart_flow/humanized_prompt.py` | 构建拟人化Prompt |
| PersonaSystem | `persona/persona_system.py` | 管理个性和情感 |
| ActionManager | `planner/action_manager.py` | 行为规划和决策 |

#### 4.1.3 数据流

```
用户消息 → HeartFlow → 情感分析 → 个性状态更新 → Prompt构建 → LLM调用 → 回复生成
```

### 4.2 执行模块 (Execution Module)

**位置**: `src/execution/`

负责任务执行和多智能体协作。

#### 4.2.1 架构设计

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     执行模块架构                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                  规划智能体(PlannerAgent)            │ │
│ │ 任务分解、智能体分配、结果融合                        │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                │
│          ┌───────────────┼───────────────┐                                  │
│          │               │               │                                  │
│          ▼               ▼               ▼                                  │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐      │
│ │单智能体        │ │多智能体        │ │ReAct引擎        │      │
│ │                  │ │协作模式        │ │                  │      │
│ │简单任务        │ │复杂任务        │ │Think-Act        │      │
│ │直接执行        │ │并行/串行        │ │-Observe        │      │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘      │
```

#### 4.2.2 协作模式

```python
class CollaborationMode(Enum):
    SINGLE = "single"       # 单智能体执行
    PARALLEL = "parallel"   # 并行执行
    SEQUENTIAL = "sequential"  # 串行执行
    HYBRID = "hybrid"       # 混合执行
```

#### 4.2.3 任务状态机

```
┌───────────┐   创建    ┌───────────┐  开始   ┌───────────┐
│ PENDING   │──────────►│ ACTIVE    │────────►│RUNNING    │
└───────────┘          └───────────┘         └────┬──────┘
     ▲                   ▲                   ▲     │     ▲
     │                   │                   │     │     │
     │ 重新激活          │ 暂停              │ 完成│     │ 恢复
     │                   │                   │     │     │
     │                   └───────────┐        │     │     │
     │                               │        │     │     │
     └───────────────────────────────┼────────┘     │     │
                                     ▼              │     │
                               ┌───────────┐         │     │
                               │ PAUSED   │─────────┘     │
                               └───────────┘               │
                                     ▲                   │
                                     │                   │
                                     └───────────────────┘
                                            COMPLETED
```

### 4.3 四级记忆系统

**位置**: `src/memory/`

#### 4.3.1 架构设计

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     记忆系统架构                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                  记忆管理中心                           │ │
│ │ 统一接口，自动路由到合适的记忆存储                      │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                │
│          ┌────────────────┼─────────────────┐                               │
│          │                                │                               │
│          ▼                                ▼                               │
│ ┌────────────────────────────────┐ ┌────────────────────────────────┐    │
│ │  聊天智能体记忆              │ │  工作智能体记忆              │    │
│ │                  │ │                  │    │
│ │四级架构              │ │项目记忆域           │    │
│ ├── 日常            │ │                  │    │
│ ├── 周度            │ │偏好记忆            │    │
│ ├── 月度            │ │                  │    │
│ └── 季度            │ │                  │    │
│ └────────────────────────────────┘ └────────────────────────────────┘    │
```

#### 4.3.2 记忆层级

| 层级 | 保存时间 | 访问频率 | 用途 |
|------|----------|----------|------|
| 日常 | 1天 | 高 | 当天对话 |
| 周度 | 7天 | 中 | 本周对话 |
| 月度 | 30天 | 低 | 本月对话 |
| 季度 | 90天 | 很低 | 本季度对话 |

### 4.4 AI原生Todo系统

**位置**: `src/todo/`

#### 4.4.1 架构设计

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     Todo系统架构                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                  Todo管理中心                           │ │
│ │ 统一接口，自动管理三级结构                              │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                │
│          ┌───────────────┼───────────────┐                                  │
│          │               │               │                                  │
│          ▼               ▼               ▼                                  │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐      │
│ │  Phase     │ │   Task     │ │   Step     │      │
│ │  (阶段)     │ │  (任务)    │ │  (步骤)    │      │
│ │                  │ │                  │ │                  │      │
│ │包含多个        │ ├───────►│ 包含多个        │ ├───────►│ 最小执行    │      │
│ │任务        │ │ 步骤        │ │ 单元        │      │
│ │                  │ │                  │ │                  │      │
│ │                  │ │                  │ │                  │      │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘      │
```

#### 4.4.2 自动机制

```
步骤完成 → 任务进度更新 → 阶段进度更新 → 阶段完成 → 反思触发
```

### 4.5 LLM客户端

**位置**: `src/llm/`

#### 4.5.1 架构设计

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     LLM客户端架构                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                  LLMClient                            │ │
│ │ 统一接口，自动选择模型                                │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                │
│          ┌───────────────┼───────────────┐                                  │
│          │               │               │                                  │
│          ▼               ▼               ▼                                  │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐      │
│ │ 基础模型        │ │ 分级模型        │ │ 垂直模型        │      │
│ │                  │ │                  │ │                  │      │
│ │默认模型        │ │strong      │ │屏幕操作        │      │
│ │                  │ │performance │ │多模态        │      │
│ │                  │ │cost_effective│ │自定义        │      │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘      │
```

#### 4.5.2 任务类型映射

| 任务类型 | 映射模型 | 说明 |
|----------|----------|------|
| PLANNING | strong | 规划任务 |
| GENERAL | performance | 日常任务 |
| TOOL_USE | performance | 工具调用 |
| MEMORY | cost_effective | 记忆整理 |
| SCREEN_OPERATION | screen_operation | 屏幕操作 |
| MULTIMODAL | multimodal | 多模态处理 |

### 4.6 域系统

**位置**: `src/device/`

#### 4.6.1 架构设计

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                     域系统架构                              │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────────────────────────────────────────────────┐ │
│ │                  DomainManager                        │ │
│ │ 域管理器，管理域和设备                                │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                           │                                                │
│          ┌───────────────┼───────────────┐                                  │
│          │               │               │                                  │
│          ▼               ▼               ▼                                  │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐      │
│ │ 域管理        │ │ 设备管理        │ │ 同步引擎        │      │
│ │                  │ │                  │ │                  │      │
│ │创建/删除        │ │加入/离开        │ │实时/定时        │      │
│ │配置管理        │ │能力声明        │ │冲突解决        │      │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘      │
```

#### 4.6.2 数据同步模型

```
设备A (本地分支)          域(中央仓库)           设备B (本地分支)
     │                        │                       │
     │修改数据                 │                       │
     └────────────────────────┼───────────────────────┘
                              │
                              │广播变更                │
     │                        │                       │
     │                        └───────────────────────┼───────
     │                        │                       │接收变更
     │                        │                       │解决冲突
     │接收变更                 │确认同步                │
     └────────────────────────┼───────────────────────┘
                              │
```

## 5. 数据流程

### 5.1 聊天消息处理流程

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│ 用户    │──────►│ IM适配器  │──────►│ 交互模块 │──────►│ LLM客户端│──────►│  回复    │
└───────────┘    └───────────┘    └────┬──────┘    └───────────┘    └───────────┘
                                     │
                                     ▼
                              ┌───────────────────┐
                              │ 记忆系统    │
                              │ - 搜索记忆 │
                              │ - 存储记忆  │
                              └───────────────────┘
```

### 5.2 任务执行流程

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│ 任务    │──────►│ 规划智能体│──────►│ 协作管理器│──────►│ 执行智能体│
│ 创建    │    │ 分解    │    │ 调度    │    │ 执行    │
└───────────┘    └───────────┘    └────┬──────┘    └────┬──────┘
                                      │                 │
                                      ▼                 ▼
                              ┌───────────────────┐ ┌───────────────────┐
                              │ 工具调用    │ │ 结果融合    │
                              └───────────────────┘ └───────────────────┘
```

### 5.3 Todo状态更新流程

```
┌─────────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│步骤完成    │──────►│ 任务更新 │──────►│ 阶段更新 │──────►│ 反思触发│
└─────────────┘    └───────────┘    └───────────┘    └───────────┘
     │                  │                  │
     ▼                  ▼                  ▼
┌───────────┐    ┌───────────┐    ┌───────────┐
│进度计算    │    │进度计算    │    │阶段完成    │
└───────────┘    └───────────┘    └───────────┘
```

## 6. 核心类与函数

### 6.1 主入口

**文件**: `src/main.py`

| 函数 | 说明 | 参数 | 返回值 |
|------|------|------|------|
| `init_data_directories()` | 初始化数据目录 | 无 | None |
| `init_services()` | 初始化服务 | 无 | None |
| `run_im_mode()` | 运行IM模式 | 无 | None |
| `run_web_mode()` | 运行Web模式 | host: str, port: int | None |
| `main()` | 主函数 | 无 | None |

### 6.2 交互模块

**文件**: `src/interaction/heart_flow/heartf_chatting.py`

| 类/函数 | 说明 | 参数 | 返回值 |
|---------|------|------|------|
| `ChatStream` | 聊天流 | stream_id: str, platform: str, group_info: Any, user_info: Any, context: Any | - |
| `MessageInfo` | 消息信息 | message_id: str, chat_id: str, user_id: str, platform: str, content: str, timestamp: float, is_mentioned: bool, is_at: bool | - |
| `HeartFChatting` | 管理连续的Focus Chat循环 | chat_id: str, config: Any | - |
| `HeartFChatting.start()` | 启动主循环 | 无 | None |
| `HeartFChatting.stop()` | 停止主循环 | 无 | None |
| `HeartFChatting._main_chat_loop()` | 主循环 | 无 | None |
| `HeartFChatting._observe()` | 观察并规划动作 | recent_messages: list[MessageInfo], force_reply_message: MessageInfo | bool |
| `HeartFChatting._plan_actions()` | 规划动作 | messages: list[MessageInfo], force_reply_message: MessageInfo | list[dict[str, Any]] |
| `HeartFChatting._execute_action()` | 执行动作 | action: dict[str, Any], thinking_id: str, timers: dict[str, float] | dict[str, Any] |

### 6.3 执行模块

**文件**: `src/execution/react_engine.py`

| 类/函数 | 说明 | 参数 | 返回值 |
|---------|------|------|------|
| `ReasoningStep` | 推理步骤枚举 | - | - |
| `ThoughtStep` | 思考步骤 | step_type: ReasoningStep, content: str, tool_name: str, tool_args: dict[str, Any], observation: str, timestamp: float | - |
| `ReActResult` | ReAct推理结果 | success: bool, result: str, steps: list[ThoughtStep], final_thought: str, iterations: int, duration: float | - |
| `ReActEngine` | ReAct推理引擎 | llm_client: Any, tool_registry: Any, security_policy: Any, config: dict[str, Any] | - |
| `ReActEngine.run()` | 运行ReAct推理循环 | task: str, context: dict[str, Any] | dict[str, Any] |
| `ReActEngine._think()` | 思考阶段 | task: str, previous_observation: str, history: list[dict[str, str]] | ThoughtStep |
| `ReActEngine._act()` | 行动阶段 | think_step: ThoughtStep | ThoughtStep |
| `ReActEngine._observe()` | 观察阶段 | act_step: ThoughtStep | ThoughtStep |

### 6.4 记忆系统

**文件**: `src/memory/unified_store.py`

| 类/函数 | 说明 | 参数 | 返回值 |
|---------|------|------|------|
| `UnifiedMemoryStore` | 统一记忆存储 | chat_data_dir: str, work_data_dir: str | - |
| `UnifiedMemoryStore.store_chat_memory()` | 存储聊天记忆 | content: str, level: MemoryLevel, source: str, importance: float, metadata: dict[str, Any] | ChatMemoryEntry |
| `UnifiedMemoryStore.search_chat_memories()` | 搜索聊天记忆 | query: str, levels: list[MemoryLevel], limit: int | list[ChatMemoryEntry] |
| `UnifiedMemoryStore.consolidate_chat_memories()` | 整合聊天记忆 | llm_client: Any | dict[str, MemoryConsolidationResult] |
| `UnifiedMemoryStore.create_project_domain()` | 创建项目域 | name: str, description: str, project_path: str, keywords: list[str] | ProjectMemoryDomain |
| `UnifiedMemoryStore.add_project_memory()` | 添加项目记忆 | domain_id: str, content: str, memory_type: str, priority: MemoryPriority, importance: float, metadata: dict[str, Any] | ProjectMemoryEntry |
| `UnifiedMemoryStore.add_preference()` | 添加偏好 | content: str, category: str, priority: MemoryPriority, importance: float, metadata: dict[str, Any] | PreferenceMemory |
| `UnifiedMemoryStore.build_system_prompt_context()` | 构建系统提示上下文 | project_context: str, project_path: str, include_chat_memories: bool, include_preferences: bool, include_project_memories: bool | str |

## 7. 配置文件

| 配置 | 路径 | 说明 |
|------|------|------|
| 环境变量 | `.env` | API密钥、基础配置 |
| 模型配置 | `config/models.yaml` | LLM模型配置 |
| MCP配置 | `config/mcp.json` | MCP服务器配置 |
| 记忆系统 | `config/memory.yaml` | 记忆系统配置 |
| 拟人化 | `config/persona.yaml` | 拟人化配置 |
| 浏览器 | `config/browser.yaml` | 浏览器自动化配置 |
| 日历 | `config/calendar.yaml` | 日历管理配置 |
| 邮件 | `config/email.yaml` | 邮件客户端配置 |
| Todo | `config/todo.yaml` | Todo系统配置 |
| 语音 | `config/voice.yaml` | 语音交互配置 |

## 8. 项目运行方式

### 8.1 安装

```bash
# 克隆项目
git clone <repository-url>
cd pyagent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API密钥
```

### 8.2 运行

```bash
# Web模式
python -m src.main --mode web --host 0.0.0.0 --port 8000

# IM模式
python -m src.main --mode im

# 同时运行Web和IM
python -m src.main --mode both
```

访问 http://localhost:8000 查看Web界面。

### 8.3 自动化脚本

项目提供了一键自动化脚本，简化开发和构建流程：

#### 代码检查

```powershell
# 一键运行所有检查（测试 + 代码风格 + 类型检查 + 安全检查）
.heck.ps1

# 可选参数
.heck.ps1 -SkipTests      # 跳过测试
.heck.ps1 -Fix            # 自动修复代码风格问题
.heck.ps1 -Coverage       # 生成覆盖率报告
```

#### 构建

```powershell
# 一键构建（wheel + EXE + APK）
.uild.ps1

# 可选参数
.uild.ps1 -SkipExe        # 跳过EXE构建
.uild.ps1 -SkipApk        # 跳过APK构建
.uild.ps1 -NoClean        # 增量构建
```

## 9. 测试

```bash
# 运行所有测试
pytest

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

测试文件命名：`test_*.py`，测试类命名：`Test*`，测试函数命名：`test_*`

## 10. 构建与发布

### 10.1 构建输出位置

| 构建类型 | 输出路径 |
|----------|----------|
| Wheel包 | `dist/pyagent-*.whl` |
| EXE | `dist/exe/PyAgent/PyAgent.exe` |
| APK | `android/app/build/outputs/apk/` |

### 10.2 发布流程

1. 运行一键检查：`.heck.ps1`
2. 运行一键构建：`.uild.ps1`
3. 更新 CHANGELOG.md
4. 创建发布分支：`git checkout -b release/vX.X.X develop`
5. 合并到main：`git checkout main && git merge release/vX.X.X && git tag -a vX.X.X -m "Release vX.X.X" && git push origin main --tags`
6. 合并回develop：`git checkout develop && git merge release/vX.X.X && git push origin develop`
7. 删除发布分支：`git branch -d release/vX.X.X`

## 11. 版本号规范

格式：`MAJOR.MINOR.PATCH`

| 版本号 | 更新时机 |
|--------|----------|
| MAJOR | 不兼容的API变更 |
| MINOR | 向后兼容的功能新增 |
| PATCH | 向后兼容的问题修复 |

## 12. 开发规范

### 12.1 代码规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划线 | `chat_agent.py` |
| 类 | 大驼峰 | `ChatAgent` |
| 函数 | 小写+下划线 | `send_message()` |
| 常量 | 大写+下划线 | `MAX_RETRY_COUNT` |

- 使用 Ruff 进行代码格式化和检查
- 所有公开函数必须添加类型注解
- 使用 Google 风格的文档字符串

### 12.2 Git 分支

| 分支类型 | 命名规则 | 说明 |
|----------|----------|------|
| main | `main` | 生产分支 |
| develop | `develop` | 开发分支 |
| feature | `feature/<name>` | 功能分支 |
| hotfix | `hotfix/<name>` | 热修复分支 |
| release | `release/<version>` | 发布分支 |

### 12.3 提交规范

采用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

类型: feat/fix/docs/style/refactor/test/chore/perf
范围: agents/memory/todo/llm/im/mcp/web/api/config
```

示例：
- `feat(agents): add agent registry system`
- `fix(memory): resolve memory leak in chat history`
- `docs(api): update API documentation`

## 13. 扩展机制

### 13.1 技能系统 (Skills)

```
skills/
├── skill_name/
│   ├── SKILL.md          # 技能描述
│   ├── __init__.py       # 技能入口
│   ├── tools.py          # 工具实现
│   └── config.yaml       # 技能配置
```

### 13.2 MCP协议

```json
{
  "servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
      "transport": "stdio"
    }
  ]
}
```

### 13.3 自定义工具

```python
from src.tools.unified_tool import UnifiedTool, ToolState

class MyTool(UnifiedTool):
    def __init__(self):
        super().__init__("my_tool")
    
    async def activate(self):
        # 初始化资源
        pass
    
    async def execute(self, **kwargs):
        # 执行业务逻辑
        pass
    
    async def dormant(self):
        # 释放资源
        pass
```

## 14. 文档索引

### 14.1 入门

| 文档 | 说明 |
|------|------|
| [README.md](file:///workspace/README.md) | 项目总览 |
| [CHANGELOG.md](file:///workspace/CHANGELOG.md) | 版本更新记录 |
| [AGENTS.md](file:///workspace/AGENTS.md) | 开发者指南 |

### 14.2 架构与开发

| 文档 | 说明 |
|------|------|
| [docs/architecture.md](file:///workspace/docs/architecture.md) | 系统架构 |
| [docs/api.md](file:///workspace/docs/api.md) | API文档 |
| [docs/configuration.md](file:///workspace/docs/configuration.md) | 配置说明 |
| [docs/deployment.md](file:///workspace/docs/deployment.md) | 部署指南 |
| [docs/development.md](file:///workspace/docs/development.md) | 开发指南 |
| [docs/testing.md](file:///workspace/docs/testing.md) | 测试文档 |

### 14.3 模块文档

详细模块文档位于 `docs/modules/` 目录，包括：
- [Todo系统](file:///workspace/docs/modules/todo-system.md)
- [记忆系统](file:///workspace/docs/modules/memory-system.md)
- [拟人化系统](file:///workspace/docs/modules/persona-system.md)
- [智能体系统](file:///workspace/docs/modules/agent-system.md)
- [LLM客户端](file:///workspace/docs/modules/llm-client-v2.md)
- [浏览器自动化](file:///workspace/docs/modules/browser-automation.md)
- [文档编辑器](file:///workspace/docs/modules/document-editor.md)
- [视频编辑器](file:///workspace/docs/modules/video-editor.md)
- [更多模块...](file:///workspace/docs/modules/)

## 15. 许可证

GNU General Public License v3.0 - 详见 [LICENSE](file:///workspace/LICENSE) 文件

---

**PyAgent - 让AI更智能，让协作更高效**