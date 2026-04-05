# 架构重构 Spec

## Why
当前架构中"聊天智能体"和"执行智能体"的命名不够清晰，需要重构为更准确的模块化架构。同时需要引入"任务"概念作为执行模块的最小上下文单位，支持多智能体协作模式。此外，需要集成OpenClaw微信插件以支持微信通道。

## What Changes
- **BREAKING**: 重命名"聊天智能体"为"交互模块"
- **BREAKING**: 重命名"执行智能体"为"执行模块"
- 新增"任务"概念：执行模块的最小上下文单位
- 新增"规划智能体"：负责创建和管理执行智能体
- 新增多智能体协作模式开关
- 新增OpenClaw微信插件集成
- 优化Web UI体验

## Impact
- Affected specs: 交互模块、执行模块、IM适配器
- Affected code: 
  - `src/chat/` → `src/interaction/`
  - `src/executor/` → 重构为执行模块（包含任务定义）
  - 新增 `src/im/openclaw/` OpenClaw适配器
  - `frontend/` UI优化

## ADDED Requirements

### Requirement: 任务定义
系统 SHALL 将"任务"定义为执行模块的最小上下文单位。任务是一段提示词，执行模块需按照提示词完成相应工作。

#### Scenario: 创建任务
- **WHEN** 用户或系统创建一个任务
- **THEN** 系统生成唯一的任务ID，并初始化任务上下文

#### Scenario: 任务执行
- **WHEN** 执行模块接收任务
- **THEN** 按照任务提示词执行，并返回执行结果

### Requirement: 规划智能体
系统 SHALL 提供规划智能体，负责创建若干个提示词不同的执行智能体执行任务。

#### Scenario: 多智能体协作
- **WHEN** 多智能体协作模式开启
- **THEN** 规划智能体分析任务，创建多个执行智能体并行或串行执行子任务

#### Scenario: 单智能体模式
- **WHEN** 多智能体协作模式关闭
- **THEN** 单个执行智能体直接执行任务

### Requirement: 多智能体协作模式开关
系统 SHALL 提供多智能体协作模式的开关配置。

#### Scenario: 开启协作模式
- **WHEN** 用户开启多智能体协作模式
- **THEN** 规划智能体介入，分解任务并分配给多个执行智能体

#### Scenario: 关闭协作模式
- **WHEN** 用户关闭多智能体协作模式
- **THEN** 任务直接由单个执行智能体处理

### Requirement: 模块重命名
系统 SHALL 将原有模块重命名为更准确的名称。

#### Scenario: 聊天智能体重命名
- **WHEN** 系统启动
- **THEN** "聊天智能体"模块重命名为"交互模块"

#### Scenario: 执行智能体重命名
- **WHEN** 系统启动
- **THEN** "执行智能体"模块重命名为"执行模块"

### Requirement: OpenClaw微信插件集成
系统 SHALL 集成OpenClaw微信插件，支持微信通道的消息收发。

#### Scenario: 微信登录
- **WHEN** 用户执行微信登录命令
- **THEN** 系统显示二维码，用户扫码授权后保存登录凭证

#### Scenario: 多账号支持
- **WHEN** 用户添加多个微信账号
- **THEN** 系统支持多账号同时在线，并支持上下文隔离

#### Scenario: 消息接收
- **WHEN** 微信收到新消息
- **THEN** 系统通过长轮询获取消息并转发给交互模块处理

#### Scenario: 消息发送
- **WHEN** 交互模块需要发送消息
- **THEN** 系统通过OpenClaw API发送文本、图片、视频或文件消息

#### Scenario: 输入状态
- **WHEN** 系统正在生成回复
- **THEN** 可以发送输入状态指示给微信用户

### Requirement: Web UI优化
系统 SHALL 优化Web UI的用户体验。

#### Scenario: 界面布局优化
- **WHEN** 用户访问Web界面
- **THEN** 显示优化后的交互界面，包含任务管理、协作模式开关等功能

## MODIFIED Requirements

### Requirement: 执行模块架构
执行模块 SHALL 支持两种模式：
1. 单智能体模式：直接执行任务
2. 多智能体协作模式：由规划智能体协调多个执行智能体

### Requirement: 交互模块
交互模块 SHALL 专注于用户交互，包括：
- 接收用户输入（来自Web UI或IM平台）
- 理解用户意图
- 创建任务并提交给执行模块
- 返回执行结果给用户

### Requirement: IM适配器扩展
IM适配器 SHALL 支持OpenClaw微信通道：
- 支持二维码登录
- 支持多账号管理
- 支持消息收发（文本、图片、视频、文件）
- 支持输入状态指示
- 支持CDN媒体上传

## REMOVED Requirements
无移除的需求。

## 架构设计

```
新架构:

用户
  ↓
交互模块 (Interaction Module)
  ├── 意图理解
  ├── 任务创建
  └── 结果返回
  ↓
任务 (Task)
  ├── 任务ID
  ├── 提示词
  └── 上下文
  ↓
执行模块 (Execution Module)
  ├── 多智能体协作模式 (开启)
  │   ├── 规划智能体 (Planner Agent)
  │   │   ├── 任务分解
  │   │   └── 智能体分配
  │   └── 执行智能体组 (Executor Agents)
  │       ├── 执行智能体1
  │       ├── 执行智能体2
  │       └── ...
  │
  └── 单智能体模式 (关闭)
      └── 执行智能体 (Executor Agent)

IM平台适配器:
  ├── OpenClaw微信 (新增)
  │   ├── 二维码登录
  │   ├── 多账号管理
  │   ├── 消息收发
  │   └── CDN媒体上传
  ├── 飞书
  ├── 企微
  ├── 钉钉
  └── OneBot
```

## 目录结构变更

```
src/
├── interaction/          # 交互模块 (原 chat/)
│   ├── intent/           # 意图理解
│   ├── persona/          # 个性系统
│   └── reply/            # 回复生成
├── execution/            # 执行模块 (重构)
│   ├── task.py           # 任务定义
│   ├── task_context.py   # 任务上下文
│   ├── executor.py       # 执行智能体
│   ├── planner.py        # 规划智能体
│   ├── collaboration.py  # 协作模式管理
│   └── react_engine.py   # ReAct引擎
├── im/                   # IM平台适配器
│   ├── openclaw/         # OpenClaw微信 (新增)
│   │   ├── adapter.py    # 适配器实现
│   │   ├── api.py        # API客户端
│   │   └── types.py      # 类型定义
│   ├── feishu/           # 飞书
│   ├── wecom/            # 企微
│   ├── dingtalk/         # 钉钉
│   └── onebot/           # OneBot
├── memory/               # 记忆系统 (保留)
├── todo/                 # Todo系统 (保留)
└── web/                  # Web服务 (优化)
```

## OpenClaw API集成

### 核心接口

| 接口 | 路径 | 说明 |
|------|------|------|
| getUpdates | getupdates | 长轮询获取新消息 |
| sendMessage | sendmessage | 发送消息（文本/图片/视频/文件） |
| getUploadUrl | getuploadurl | 获取CDN上传预签名URL |
| getConfig | getconfig | 获取账号配置（输入状态票据等） |
| sendTyping | sendtyping | 发送/取消输入状态指示 |

### 消息类型

| 类型 | 值 | 说明 |
|------|-----|------|
| TEXT | 1 | 文本消息 |
| IMAGE | 2 | 图片消息 |
| VOICE | 3 | 语音消息（SILK编码） |
| FILE | 4 | 文件消息 |
| VIDEO | 5 | 视频消息 |

### CDN媒体处理

所有媒体类型通过CDN传输，使用AES-128-ECB加密：
1. 计算文件明文大小、MD5和加密后密文大小
2. 调用getUploadUrl获取上传参数
3. 使用AES-128-ECB加密文件内容
4. PUT上传到CDN URL
5. 构造CDNMedia引用并发送
