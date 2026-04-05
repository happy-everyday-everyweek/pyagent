# PyAgent - Python智能体框架 v0.8.0

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.8.0-orange.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-28%20passed-brightgreen.svg)](docs/testing.md)

PyAgent是一个功能强大的Python智能体框架，支持多平台即时通讯(IM)集成、多智能体协作、ReAct推理引擎、MCP协议支持、AI原生Todo管理、四级记忆系统、自我学习、**拟人化聊天**、**多智能体协作模式**、**原生文档编辑器**、**原生视频编辑器**、**域系统**、**智能体系统**、**人工任务系统**、**日历管理**、**邮件收发**、**语音交互**、**浏览器自动化**、**PDF处理**、**分布式存储**、**LLM模型网关**、**移动端支持**等高级特性。

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [核心模块详解](#核心模块详解)
- [API文档](#api文档)
- [配置说明](#配置说明)
- [文档索引](#文档索引)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

PyAgent是一个企业级的Python智能体框架，旨在构建能够进行复杂任务处理、多轮对话、工具调用的AI智能体系统。框架采用模块化设计，支持多种LLM模型、多平台IM接入、以及丰富的扩展能力。

### 设计哲学

1. **模块化架构**: 交互模块与执行模块分离，职责清晰，便于扩展和维护
2. **多智能体协作**: 支持单智能体和多智能体协作模式，适应不同复杂度任务
3. **拟人化交互**: 让AI回复更加自然、有情感、懂得在合适的时间说话
4. **企业级特性**: 支持热更新、域系统、设备管理等企业级功能

### 应用场景

- **智能客服**: 基于IM平台的智能客服机器人
- **个人助手**: 日程管理、任务提醒、信息查询
- **内容创作**: AI辅助写作、视频剪辑、文档编辑
- **数据分析**: Excel数据分析、可视化、报告生成
- **多设备协作**: 域系统支持多设备数据同步和协作

---

## 核心特性

### 1. 多智能体架构

PyAgent采用双模块架构设计：

#### 交互模块 (Interaction Module)
负责处理用户对话和交互：
- **心流聊天架构**: 管理连续的Focus Chat循环
- **拟人化Prompt构建**: 构建自然、口语化的对话
- **情感表达系统**: 10种情感类型，让回复更有温度
- **行为规划系统**: 智能判断回复时机，懂得何时说话

#### 执行模块 (Execution Module)
负责任务执行和工具调用：
- **任务概念**: 最小上下文单位，支持任务分解
- **规划智能体**: 自动分解任务、分配智能体、聚合结果
- **多智能体协作**: 支持并行、串行、混合执行模式
- **ReAct推理引擎**: Think-Act-Observe三阶段显式推理

### 2. 多平台IM支持

统一的消息格式和适配器接口，支持：

| 平台 | 协议 | 特性 | 状态 |
|------|------|------|------|
| QQ | OneBot | 群聊、私聊、图片、文件 | 已支持 |
| 钉钉 | Webhook | 群机器人、工作通知 | 已支持 |
| 飞书 | Webhook | 群机器人、富文本消息 | 已支持 |
| 企业微信 | Webhook | 群机器人、应用消息 | 已支持 |
| 微信 | OpenClaw | 二维码登录、多账号、CDN上传 | 已支持 |
| Kimi | API | 长轮询、Webhook、图文消息 | 已支持 |

### 3. AI原生Todo系统

三级分类的任务管理系统：

```
Phase(阶段)
├── Task(任务)
│   ├── Step(步骤)
│   ├── Step(步骤)
│   └── Step(步骤)
├── Task(任务)
└── Task(任务)
```

**核心能力**:
- 自动更新任务列表和进度
- 自动创建验收文档和验收标准
- 阶段完成后2-5轮反思，提取洞察
- 支持任务依赖和优先级管理

### 4. 四级记忆系统

#### 聊天智能体记忆
四级架构，全部召回，不删除：
- **日常记忆**: 当天对话，高频访问
- **周度记忆**: 本周对话，定期整理
- **月度记忆**: 本月对话，月度总结
- **季度记忆**: 本季度对话，长期保留

#### 工作智能体记忆
- **项目记忆域**: 按项目组织记忆，支持项目匹配
- **偏好记忆**: 用户偏好自动加入系统提示词
- **记忆整理**: 自动整理、归纳、衰减和过期清理

### 5. 拟人化聊天智能体

让AI回复更加自然、像真人一样聊天：

#### 情感表达系统
10种情感类型：
- 中性、开心、悲伤、愤怒、惊讶
- 好奇、思考、调皮、关心、害羞

#### 个性状态系统
- 日常(60%)、开心(15%)、思考(15%)、关心(10%)
- 状态随机切换，影响回复风格

#### 行为规划系统
- **回复时机计算**: 基于对话上下文智能判断
- **主动问候机制**: 早安/午安/晚安等主动问候
- **对话结束判断**: 智能识别对话结束信号

### 6. 原生文档编辑器

集成ONLYOFFICE Docs，支持Word/Excel/PPT在线编辑：

#### Word编辑器
- AI辅助写作：改写、扩写、缩写、翻译、校对
- 文档版本管理
- 多格式导出

#### Excel编辑器
- AI数据分析：趋势分析、图表建议、公式推荐
- 数据清洗和异常检测
- 智能图表生成

#### PPT编辑器
- AI智能生成：大纲生成、布局建议、配图推荐
- 动画效果推荐
- 一键生成完整演示文稿

### 7. 原生视频编辑器

参考Cutia架构实现：

#### 时间轴管理
- 多轨道编辑：视频、音频、字幕、特效
- 元素拖拽：自由调整位置和时长
- 精确剪辑：帧级精确剪辑

#### AI智能剪辑
- 精彩片段识别：自动识别高光时刻
- 智能裁剪：自动去除冗余内容
- 字幕生成：语音转录、时间轴对齐、多语言翻译

#### 特效推荐
- 转场效果：淡入淡出、滑动、缩放
- 滤镜调色：预设滤镜、AI调色、LUT支持
- 背景音乐：音乐库、节奏匹配、音量平衡

### 8. 域系统与分布式准备

支持多设备数据同步和协作：

#### 域概念
- 定义设备域，支持多设备协作
- 设备类型：PC/MOBILE/SERVER/EDGE
- 设备能力声明：CPU、内存、存储、GPU

#### 数据同步
- 实时同步模式：每次操作后立即同步
- 定时同步模式：可配置同步间隔
- 类Git分支模型：每台设备相当于一个分支

#### 冲突解决
- 三方合并算法
- 自动检测和处理冲突
- 支持手动解决策略

### 9. 热更新功能

无需重启服务即可更新系统：
- 支持zip压缩包上传
- 自动验证、解压、应用更新
- 版本备份和回滚机制
- 模块热重载

### 10. MCP协议支持

集成Model Context Protocol：
- 支持MCP服务器连接
- 扩展工具能力
- 统一工具调用接口

### 11. 智能体系统 (v0.8.0)

Agent 抽象基类和注册中心：
- **Agent 基类**: 定义 Agent 标准接口，支持能力声明
- **Registry 注册中心**: 管理所有 Agent，支持动态注册
- **Executor 执行器**: 调度 Agent 执行任务，支持优先级

### 12. 人工任务系统 (v0.8.0)

专为人类用户设计的任务管理：
- **四级优先级**: 低/中/高/紧急
- **子任务支持**: 任务拆分管理，进度追踪
- **时间提醒**: 截止日期和提醒功能
- **统计功能**: 完成率、过期任务分析

### 13. 日历管理 (v0.8.0)

完整的日程管理功能：
- **事件管理**: CRUD 操作，支持标题、描述、地点、参与者
- **重复规则**: 日/周/月/年重复
- **提醒功能**: 邮件/推送/短信提醒
- **ICS 支持**: 与主流日历软件兼容

### 14. 邮件客户端 (v0.8.0)

完整的邮件收发功能：
- **SMTP 发送**: SSL/TLS 加密发送
- **IMAP 接收**: 收取、搜索、管理邮件
- **多格式支持**: 纯文本、HTML、混合内容
- **附件处理**: 多附件上传下载

### 15. 语音交互 (v0.8.0)

语音识别和合成：
- **多 ASR 引擎**: Whisper、百度、阿里等
- **多 TTS 引擎**: Edge TTS、百度、阿里等
- **实时处理**: 流式语音识别和合成
- **多语言支持**: 中/英/日/韩等

### 16. 浏览器自动化 (v0.8.0)

基于 Playwright 的浏览器控制：
- **多浏览器支持**: Chromium、Firefox、WebKit
- **页面操作**: 导航、点击、输入、截图
- **JavaScript 执行**: 页面脚本执行
- **会话管理**: Cookie 和 LocalStorage

### 17. PDF 处理 (v0.8.0)

PDF 文档解析和提取：
- **文本提取**: 精确提取文本和位置信息
- **表格识别**: 自动识别表格数据
- **图片提取**: 提取 PDF 中的图片资源
- **元数据读取**: 标题、作者、日期等

### 18. 分布式存储 (v0.8.0)

跨设备文件存储和同步：
- **跨设备同步**: 文件自动同步到域内设备
- **冲突解决**: 智能处理多设备修改冲突
- **增量同步**: 只传输变更部分
- **版本历史**: 支持文件版本回溯

### 19. LLM 模型网关 (v0.8.0)

参考 LiteLLM 的统一接口：
- **多提供商支持**: OpenAI、Anthropic、DeepSeek、智谱等
- **自动路由**: 根据模型名自动选择提供商
- **故障转移**: 主提供商失败自动切换
- **统一计费**: 跨提供商统一计费接口

### 20. 移动端支持 (v0.8.0)

移动设备后端支持：
- **多平台支持**: Android、iOS、HarmonyOS
- **设备检测**: 自动检测移动环境和能力
- **屏幕控制**: 截图、点击、滑动操作
- **通知管理**: 读取和处理系统通知
- **短信收发**: 发送和接收短信

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         PyAgent 架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      前端层                               │   │
│  │  Vue.js 3 + TypeScript + Element Plus                   │   │
│  │  - 聊天界面 | 任务视图 | 配置面板 | 文档编辑器 | 视频编辑器 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      API层                                │   │
│  │  FastAPI + WebSocket                                     │   │
│  │  - REST API | WebSocket | SSE                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  交互模块    │  │  执行模块    │  │        核心服务         │ │
│  │             │  │             │  │                         │ │
│  │ 心流聊天    │  │ 任务管理    │  │ 四级记忆系统            │ │
│  │ 拟人化Prompt│  │ 规划智能体  │  │ AI原生Todo              │ │
│  │ 情感系统    │  │ ReAct引擎   │  │ 自我学习                │ │
│  │ 行为规划    │  │ 多智能体协作│  │ Mate模式                │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              v0.8.0 扩展模块 (新增)                      │   │
│  │  智能体系统 | 人工任务 | 日历 | 邮件 | 语音 | 浏览器      │   │
│  │  PDF处理 | 分布式存储 | LLM网关 | 移动端支持              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      基础设施层                           │   │
│  │  LLM客户端 | IM适配器 | MCP协议 | 文档/视频编辑器 | 域系统  │   │
│  │  智能体系统 | 人工任务 | 日历 | 邮件 | 语音 | 浏览器        │   │
│  │  PDF处理 | 分布式存储 | LLM网关 | 移动端支持               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户消息 → IM适配器 → 交互模块 → LLM客户端 → 执行模块 → 工具调用
                ↓           ↓           ↓
            记忆系统    情感分析    任务分解
```

---

## 快速开始

### 环境要求

- **Python**: 3.10+
- **Node.js**: 16+ (前端开发)
- **操作系统**: Windows/Linux/macOS
- **内存**: 建议8GB+
- **存储**: 建议10GB+可用空间

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd pyagent
```

#### 2. 创建虚拟环境

```bash
# 使用venv
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### 3. 安装依赖

```bash
# 使用pip
pip install -r requirements.txt

# 或使用uv (更快)
uv pip install -r requirements.txt
```

#### 4. 安装前端依赖 (可选)

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 5. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置API密钥
```

### 配置说明

#### 必需配置

编辑 `.env` 文件：

```env
# OpenAI (推荐)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# 或 DeepSeek
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# 或 智谱AI
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_MODEL=glm-4

# 或 Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

#### 可选配置

```env
# Web服务配置
HOST=0.0.0.0
PORT=8000

# 日志级别
LOG_LEVEL=INFO

# 记忆系统配置
MEMORY_MAX_SIZE=10000

# Todo系统配置
TODO_AUTO_VERIFY=true
```

### 运行方式

#### Web模式（默认）

```bash
python -m src.main --mode web --host 0.0.0.0 --port 8000
```

访问：http://localhost:8000

#### IM模式

```bash
python -m src.main --mode im
```

#### 同时运行Web和IM

```bash
python -m src.main --mode both
```

#### 开发模式（热重载）

```bash
python -m src.main --mode web --reload
```

---

## 项目结构

```
pyagent/
├── src/                          # 源代码目录
│   ├── main.py                   # 主入口文件
│   ├── __init__.py
│   ├── interaction/              # 交互模块
│   │   ├── heart_flow/           # 心流聊天核心
│   │   │   ├── heartf_chatting.py
│   │   │   └── humanized_prompt.py
│   │   ├── persona/              # 个性系统
│   │   ├── planner/              # 动作规划器
│   │   ├── replyer/              # 回复生成器
│   │   └── tools/                # 聊天工具
│   ├── execution/                # 执行模块
│   │   ├── task.py               # 任务定义
│   │   ├── planner_agent.py      # 规划智能体
│   │   ├── collaboration.py      # 协作模式
│   │   ├── planner.py            # 任务规划
│   │   ├── sub_agents/           # 子Agent
│   │   └── tools/                # 执行工具
│   ├── agents/                   # 智能体系统 (v0.8.0)
│   │   ├── base.py               # Agent基类
│   │   ├── registry.py           # 注册中心
│   │   └── executor.py           # 执行器
│   ├── human_tasks/              # 人工任务系统 (v0.8.0)
│   │   ├── manager.py            # 任务管理器
│   │   └── task.py               # 任务模型
│   ├── calendar/                 # 日历管理 (v0.8.0)
│   │   ├── manager.py            # 日历管理器
│   │   └── event.py              # 事件模型
│   ├── email/                    # 邮件客户端 (v0.8.0)
│   │   └── client.py             # 邮件客户端
│   ├── voice/                    # 语音交互 (v0.8.0)
│   │   ├── asr.py                # 语音识别
│   │   ├── tts.py                # 语音合成
│   │   └── processor.py          # 语音处理器
│   ├── browser/                  # 浏览器自动化 (v0.8.0)
│   │   └── controller.py         # 浏览器控制器
│   ├── pdf/                      # PDF处理 (v0.8.0)
│   │   └── parser.py             # PDF解析器
│   ├── storage/                  # 分布式存储 (v0.8.0)
│   │   └── distributed.py        # 分布式存储核心
│   ├── mobile/                   # 移动端支持 (v0.8.0)
│   │   └── backend.py            # 移动端后端
│   ├── document/                 # 文档编辑器模块
│   ├── video/                    # 视频编辑器模块
│   ├── device/                   # 设备管理模块
│   │   ├── device_id.py          # 设备ID管理
│   │   ├── domain_manager.py     # 域管理器
│   │   ├── sync_engine.py        # 数据同步引擎
│   │   └── conflict_resolver.py  # 冲突解决器
│   ├── expression/               # 表情学习模块
│   ├── im/                       # IM平台适配器
│   │   ├── wechat/               # 微信适配器
│   │   └── kimi.py               # Kimi适配器
│   ├── llm/                      # LLM客户端
│   │   └── gateway.py            # LLM模型网关 (v0.8.0)
│   ├── memory/                   # 记忆系统
│   ├── mcp/                      # MCP协议支持
│   ├── skills/                   # 技能系统
│   ├── todo/                     # AI原生Todo系统
│   └── web/                      # Web服务
├── frontend/                     # 前端代码(Vue.js)
├── config/                       # 配置文件
├── data/                         # 数据目录
├── skills/                       # 技能目录
├── docs/                         # 文档目录
├── tests/                        # 测试套件
├── requirements.txt              # 依赖列表
├── pyproject.toml               # 项目配置
├── CHANGELOG.md                 # 更新日志
└── README.md                    # 本文件
```

---

## 核心模块详解

### 1. 交互模块 (Interaction Module)

**位置**: `src/interaction/`

负责处理即时通讯场景中的对话，采用心流(HeartFlow)架构。

#### 1.1 拟人化Prompt构建器

**文件**: `src/interaction/heart_flow/humanized_prompt.py`

负责构建自然、口语化的Prompt：

```python
from src.interaction.heart_flow.humanized_prompt import humanized_prompt_builder

# 更新情感状态
humanized_prompt_builder.update_emotion(messages=[
    {"content": "谢谢你帮我解决问题！"}
])

# 获取当前人设文本
persona_text = humanized_prompt_builder.get_persona_text()
```

**核心功能**:
- **情感推断**: 基于消息内容自动推断情感
- **个性状态切换**: 随机切换个性状态
- **Prompt构建**: 构建拟人化系统提示词

#### 1.2 个性系统

**文件**: `src/interaction/persona/persona_system.py`

管理AI的个性和情感：

```python
from src.interaction.persona.persona_system import persona_system, EmotionType

# 设置情感状态
persona_system.set_emotion(EmotionType.HAPPY, intensity=0.8)

# 获取当前情感
emotion = persona_system.get_current_emotion()
```

**核心组件**:
- **PersonaSystem**: 个性系统核心
- **EmotionState**: 情感状态管理
- **ConversationGoal**: 对话目标管理
- **ActionDecision**: 行动决策

#### 1.3 行为规划

**文件**: `src/interaction/planner/action_manager.py`

智能决策何时说话、说什么：

```python
from src.interaction.planner.action_manager import ActionManager

action_manager = ActionManager()

# 判断是否应该回复
should_reply = action_manager.should_reply(
    talk_value=0.6,
    message_count=5
)
```

**核心功能**:
- **回复时机判断**: 基于对话上下文
- **主动问候**: 根据时间主动问候
- **对话结束判断**: 识别对话结束信号

### 2. 执行模块 (Execution Module)

**位置**: `src/execution/`

负责任务执行和多智能体协作。

#### 2.1 任务概念

**文件**: `src/execution/task.py`

Task是执行模块的最小上下文单位：

```python
from src.execution.task import Task, TaskStatus

task = Task(
    id="task_123",
    prompt="分析这份数据",
    context={"data": "..."},
    dependencies=[],
    status=TaskStatus.PENDING,
    priority=1
)
```

**任务属性**:
- **id**: 唯一标识
- **prompt**: 任务提示词
- **context**: 任务上下文
- **dependencies**: 依赖任务ID列表
- **status**: 任务状态
- **priority**: 优先级

#### 2.2 规划智能体

**文件**: `src/execution/planner_agent.py`

负责任务分解和智能体分配：

```python
from src.execution.planner_agent import PlannerAgent

planner = PlannerAgent()

# 规划任务
plan = await planner.plan(task, collaboration_mode=CollaborationMode.HYBRID)
```

**核心功能**:
- **任务分解**: 将复杂任务拆分为子任务
- **智能体分配**: 为每个子任务选择最合适的智能体
- **结果聚合**: 收集和整合子任务执行结果

#### 2.3 多智能体协作

**文件**: `src/execution/collaboration.py`

支持多种协作模式：

```python
from src.execution.collaboration import CollaborationManager, CollaborationMode

manager = CollaborationManager()

# 设置协作模式
manager.set_mode(CollaborationMode.PARALLEL)

# 执行任务
result = await manager.execute(plan)
```

**协作模式**:
- **SINGLE**: 单智能体执行
- **PARALLEL**: 并行执行，提高效率
- **SEQUENTIAL**: 串行执行，保证正确性
- **HYBRID**: 混合执行，自动选择最优方式

### 3. AI原生Todo系统

**位置**: `src/todo/`

三级分类的任务管理系统。

#### 3.1 核心概念

```
Phase(阶段) - 最高层级，包含多个任务
    └── Task(任务) - 中间层级，包含多个步骤
            └── Step(步骤) - 最低层级，具体执行单元
```

#### 3.2 使用示例

```python
from src.todo import TodoManager

todo_manager = TodoManager()

# 创建阶段
phase = await todo_manager.create_phase("开发新功能")

# 创建任务
task = await todo_manager.create_task(
    phase_id=phase.id,
    title="实现用户认证"
)

# 创建步骤
step = await todo_manager.create_step(
    task_id=task.id,
    title="设计数据库表"
)

# 完成步骤
await todo_manager.complete_step(step.id)
```

#### 3.3 自动机制

- **自动更新**: 步骤完成后自动更新任务进度
- **验收文档**: 每个任务自动创建验收文档
- **阶段反思**: 阶段完成后进行2-5轮反思

### 4. 四级记忆系统

**位置**: `src/memory/`

#### 4.1 聊天智能体记忆

四级架构，全部召回，不删除：

```python
from src.memory.chat_memory import ChatMemoryManager

memory_manager = ChatMemoryManager()

# 添加记忆
await memory_manager.add_memory(
    content="用户喜欢Python编程",
    level=MemoryLevel.DAILY
)

# 检索记忆
memories = await memory_manager.retrieve_relevant(
    query="用户的编程偏好",
    top_k=5
)
```

**记忆层级**:
- **DAILY**: 当天对话，高频访问
- **WEEKLY**: 本周对话，定期整理
- **MONTHLY**: 本月对话，月度总结
- **QUARTERLY**: 本季度对话，长期保留

#### 4.2 工作智能体记忆

```python
from src.memory.work_memory import WorkMemoryManager

work_memory = WorkMemoryManager()

# 创建项目记忆域
await work_memory.create_project_domain("项目A")

# 添加项目记忆
await work_memory.add_project_memory(
    project_name="项目A",
    content="技术栈：Python + Vue"
)
```

### 5. LLM客户端

**位置**: `src/llm/`

统一的LLM客户端，支持多模型负载均衡。

#### 5.1 基础使用

```python
from src.llm import LLMClient, Message

client = LLMClient()

messages = [
    Message(role="system", content="你是一个助手"),
    Message(role="user", content="你好")
]

response = await client.generate(messages=messages)
print(response.content)
```

#### 5.2 任务类型映射

```python
from src.llm import TaskType

# 规划任务 - 使用strong模型
response = await client.generate(
    messages=planning_messages,
    task_type=TaskType.PLANNING
)

# 记忆整理 - 使用cost_effective模型
response = await client.generate(
    messages=memory_messages,
    task_type=TaskType.MEMORY
)
```

### 6. 原生文档编辑器

**位置**: `src/document/`

#### 6.1 创建文档

```python
from src.document import DocumentService, DocumentType

doc_service = DocumentService()

# 创建Word文档
doc = await doc_service.create_document(
    doc_type=DocumentType.WORD,
    title="我的文档"
)

print(f"编辑URL: {doc.edit_url}")
```

#### 6.2 AI辅助写作

```python
# 改写段落
suggestions = await doc_service.ai_rewrite(
    document_id="doc_123",
    paragraph_id="p_1",
    style="formal"
)

# 翻译文档
translated = await doc_service.ai_translate(
    document_id="doc_123",
    target_language="en"
)
```

### 7. 原生视频编辑器

**位置**: `src/video/`

#### 7.1 创建项目

```python
from src.video import VideoProject, TrackType

project = VideoProject(
    name="我的Vlog",
    resolution=(1920, 1080),
    fps=30
)

# 添加轨道
video_track = project.add_track(TrackType.VIDEO, "主视频")
```

#### 7.2 AI智能剪辑

```python
from src.video import VideoAIService

ai_service = VideoAIService()

# 分析精彩片段
highlights = await ai_service.analyze_highlights("/path/to/video.mp4")

# 生成字幕
subtitles = await ai_service.generate_subtitles(
    video_path="/path/to/video.mp4",
    language="zh"
)
```

### 8. 域系统

**位置**: `src/device/`

#### 8.1 创建域

```python
from src.device.domain_manager import DomainManager

domain_manager = DomainManager()

# 创建域
domain = await domain_manager.create_domain(name="我的域")
```

#### 8.2 加入域

```python
from src.device import DeviceType, DeviceCapabilities

capabilities = DeviceCapabilities(
    cpu_cores=8,
    memory_gb=16,
    storage_gb=512,
    has_gpu=True
)

device = await domain_manager.join_domain(
    domain_id="domain_123",
    device_type=DeviceType.PC,
    device_name="我的工作电脑",
    capabilities=capabilities
)
```

#### 8.3 数据同步

```python
from src.device.sync_engine import SyncEngine

sync_engine = SyncEngine()

# 同步数据
result = await sync_engine.sync_to_domain(
    device_id="device_123",
    data_type="memory",
    data=memory_data
)
```

---

## API文档

### REST API

启动服务后访问：http://localhost:8000/docs

#### 基础接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/chat` | 发送聊天消息 |
| GET | `/api/config` | 获取配置 |
| PUT | `/api/config` | 更新配置 |

#### 任务接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/tasks` | 列出任务 |
| POST | `/api/tasks` | 创建任务 |
| GET | `/api/tasks/{task_id}` | 获取任务详情 |
| POST | `/api/tasks/{task_id}/cancel` | 取消任务 |
| POST | `/api/tasks/{task_id}/execute` | 执行任务 |

#### Todo接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/todo/phases` | 列出所有阶段 |
| POST | `/api/todo/phases` | 创建阶段 |
| GET | `/api/todo/phases/{id}` | 获取阶段详情 |
| POST | `/api/todo/phases/{id}/tasks` | 创建任务 |
| POST | `/api/todo/tasks/{id}/steps` | 创建步骤 |
| POST | `/api/todo/steps/{id}/complete` | 完成步骤 |
| GET | `/api/todo/statistics` | 获取统计信息 |

#### 文档接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/documents` | 创建文档 |
| GET | `/api/documents/{id}` | 获取文档 |
| POST | `/api/documents/{id}/ai/rewrite` | AI改写 |
| POST | `/api/documents/{id}/export` | 导出文档 |

#### 视频接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/videos/projects` | 创建视频项目 |
| POST | `/api/videos/ai/analyze` | AI分析视频 |
| POST | `/api/videos/subtitles/generate` | 生成字幕 |
| POST | `/api/videos/export` | 导出视频 |

#### 域接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/domains` | 创建域 |
| GET | `/api/domains/{id}` | 获取域信息 |
| POST | `/api/domains/{id}/devices/join` | 设备加入域 |
| POST | `/api/domains/{id}/sync` | 同步数据 |

### WebSocket

连接地址：`ws://localhost:8000/ws`

**消息格式**:
```json
{
  "type": "chat",
  "message": "你好",
  "chat_id": "default"
}
```

**响应格式**:
```json
{
  "type": "response",
  "message": "你好！有什么可以帮助你的吗？",
  "chat_id": "default",
  "timestamp": "2025-03-30T10:00:00"
}
```

---

## 配置说明

### 模型配置 (config/models.yaml)

```yaml
# 基础模型（必填）
base_model:
  provider: openai
  model: gpt-4o
  api_key: ${OPENAI_API_KEY}
  temperature: 0.7

# 分级模型（可选）
tier_models:
  strong:
    provider: zhipu
    model: glm-5
    api_key: ${ZHIPU_API_KEY}
    description: "强能力模型，负责规划任务"
    
  performance:
    provider: openai
    model: qwen3.5-35b
    api_key: ${OPENAI_API_KEY}
    description: "高性能模型，负责日常任务"
    
  cost_effective:
    provider: zhipu
    model: glm-4-flash
    api_key: ${ZHIPU_API_KEY}
    description: "性价比模型，负责简单任务"

# 垂类模型（可选）
vertical_models:
  screen_operation:
    provider: zhipu
    model: autoglm-phone-9b
    api_key: ${ZHIPU_API_KEY}
    description: "屏幕操作模型"
    
  multimodal:
    provider: openai
    model: gpt-4o-vision
    api_key: ${OPENAI_API_KEY}
    description: "多模态模型"
```

### 拟人化配置 (config/persona.yaml)

```yaml
persona:
  bot_name: "小助手"
  base_personality: "是一个友善、乐于助人的AI助手"
  
  # 情感配置
  emotion:
    enabled: true
    auto_detect: true
    intensity_range: [0.0, 1.0]
    types:
      - neutral
      - happy
      - sad
      - angry
      - surprised
      - curious
      - thinking
      - playful
      - caring
      - shy
  
  # 个性状态配置
  states:
    - name: "日常"
      probability: 0.6
      description: "正常状态"
    - name: "开心"
      probability: 0.15
      description: "心情愉快"
    - name: "思考"
      probability: 0.15
      description: "深度思考"
    - name: "关心"
      probability: 0.1
      description: "关心用户"
  
  # 行为规划配置
  behavior:
    greeting_enabled: true
    reply_timing: "adaptive"
    end_conversation_detection: true
    talk_value_threshold: 0.5
```

### MCP配置 (config/mcp.json)

```json
{
  "servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
      "transport": "stdio"
    },
    {
      "name": "sqlite",
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "/path/to/db.sqlite"],
      "transport": "stdio"
    }
  ]
}
```

### Todo配置 (config/todo.yaml)

```yaml
todo:
  # 反思配置
  reflection:
    min_rounds: 2
    max_rounds: 5
    auto_trigger: true
  
  # 验收配置
  verification:
    auto_create: true
    auto_verify: true
    require_approval: false
  
  # 通知配置
  notification:
    on_phase_complete: true
    on_task_complete: true
    on_step_complete: false
```

### 记忆系统配置 (config/memory.yaml)

```yaml
memory:
  # 聊天记忆配置
  chat:
    levels:
      daily:
        max_size: 1000
        retention_days: 1
      weekly:
        max_size: 500
        retention_days: 7
      monthly:
        max_size: 200
        retention_days: 30
      quarterly:
        max_size: 100
        retention_days: 90
  
  # 工作记忆配置
  work:
    project_domains:
      auto_create: true
      max_projects: 50
    preferences:
      auto_extract: true
      max_preferences: 100
```

### 域系统配置 (config/domain.yaml)

```yaml
domain:
  # 当前设备信息
  device:
    name: "我的工作电脑"
    type: "pc"
    capabilities:
      cpu_cores: 8
      memory_gb: 16
      storage_gb: 512
      has_gpu: true
      gpu_model: "RTX 3060"
      network_type: "wifi"
      supported_tasks:
        - "llm_inference"
        - "video_processing"
        - "document_editing"
  
  # 同步配置
  sync:
    default_mode: "realtime"
    realtime:
      enabled: true
      debounce_ms: 500
    scheduled:
      enabled: false
      interval_minutes: 30
  
  # 冲突解决配置
  conflict_resolution:
    default_strategy: "auto"
    auto_rules:
      - data_type: "memory"
        strategy: "newer_wins"
      - data_type: "todo"
        strategy: "merge"
      - data_type: "config"
        strategy: "manual"
```

---

## 文档索引

### 架构文档

- [架构设计](docs/architecture.md) - 系统架构、模块关系、数据流
- [API文档](docs/api.md) - REST API、WebSocket接口详细说明
- [配置文档](docs/configuration.md) - 所有配置选项详解
- [部署文档](docs/deployment.md) - 部署指南、IM平台接入
- [开发文档](docs/development.md) - 开发指南、代码规范
- [测试文档](docs/testing.md) - 测试套件、运行方法
- [前端文档](docs/frontend.md) - 前端UI、暗色模式

### 模块文档

#### v0.7.0 新增
- [文档编辑器](docs/modules/document-editor.md) - 原生文档编辑器（Word/Excel/PPT）
- [视频编辑器](docs/modules/video-editor.md) - 原生视频编辑器
- [域系统](docs/modules/domain-system.md) - 域系统、多设备同步

#### v0.6.0 新增
- [LLM客户端v2](docs/modules/llm-client-v2.md) - 分级模型、垂类模型
- [设备ID系统](docs/modules/device-id.md) - 设备ID管理
- [统一工具接口](docs/modules/unified-tool.md) - 三阶段工具调用
- [ClawHub](docs/modules/clawhub.md) - Skill技能安装协议

#### v0.5.0 新增
- [执行模块](docs/modules/execution-module.md) - 任务四状态系统
- [热更新](docs/modules/hot-reload.md) - 热更新功能

#### v0.4.0 新增
- [微信适配器](docs/modules/wechat-adapter.md) - 微信机器人

#### v0.3.0 新增
- [拟人化系统](docs/modules/persona-system.md) - 拟人化聊天智能体

#### v0.2.0 新增
- [Todo系统](docs/modules/todo-system.md) - AI原生Todo系统
- [记忆系统](docs/modules/memory-system.md) - 四级记忆系统
- [Mate模式](docs/modules/mate-mode.md) - Mate模式

#### 基础模块
- [交互模块](docs/modules/chat-agent.md) - 交互模块、心流架构
- [执行模块](docs/modules/executor-agent.md) - 执行模块、ReAct引擎
- [LLM客户端](docs/modules/llm-client.md) - LLM客户端模块
- [IM适配器](docs/modules/im-adapter.md) - IM适配器模块

---

## 贡献指南

欢迎提交Issue和Pull Request！

### 提交Issue

- 描述问题时请提供复现步骤
- 附上相关日志和错误信息
- 说明环境信息（操作系统、Python版本等）

### 提交PR

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8规范
- 使用类型注解
- 添加必要的注释和文档字符串
- 确保测试通过

---

## 许可证

GNU General Public License v3.0 - 详见 [LICENSE](LICENSE) 文件

---

## 联系方式

- **项目主页**: [GitHub Repository](https://github.com/your-org/pyagent)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/pyagent/issues)
- **文档**: [在线文档](https://pyagent.readthedocs.io)

---

**PyAgent - 让AI更智能，让协作更高效**
