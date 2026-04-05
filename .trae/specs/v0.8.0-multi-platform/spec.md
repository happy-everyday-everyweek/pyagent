# PyAgent v0.8.0 多端架构与生态增强 Spec

## Why

PyAgent需要从单端应用升级为多端架构，支持桌面端和移动端，同时增强内置应用生态，提供更完整的AI原生工作体验。通过引入分布式存储、日历、邮件、任务管理等核心功能，以及语音交互、键鼠操作等能力，让PyAgent成为真正的AI助手平台。

## What Changes

### 架构变更

* **BREAKING**: 引入多端架构，支持桌面端(PC)和移动端(Mobile)

* **BREAKING**: 设备类型扩展，新增设备能力声明系统

* **BREAKING**: 移动端后端架构调整，内置Linux运行环境

### 新增功能

* 分布式存储系统：跨设备文件同步与访问

* 日历功能：日程安排与管理

* 任务功能：人类任务管理（区别于AI Todo系统）

* 邮件功能：邮件收发与管理

* 斜杠面板优化：三栏布局（最近、应用、配置）

* 电脑端键鼠操作：AI驱动的桌面自动化

* 语音交互：语音输入与文字转语音

* 金融智能体：垂类智能体扩展

* 浏览器自动化：AI驱动的浏览器操作

* PDF解析：面向AI的高性能PDF解析

* 应用打包：EXE和APK封装

### 参考项目迁移

* twenty: 邮件、日历、看板功能

* dexter: 金融智能体

* VibeVoice: 语音交互能力

* deer-flow: 智能体编排优化

* LiteLLM: 模型网关便捷连接

* project-nomad: 地图、离线维基

* browser-use: 浏览器自动化

* Operit: 移动端架构、MNN本地推理

* opendataloader-pdf: PDF解析

## Impact

### 受影响的模块

* `src/device/`: 设备类型和能力声明扩展

* `src/execution/`: 智能体编排优化

* `src/llm/`: 模型网关集成

* `src/tools/`: 新增工具类型

* `src/web/`: 新增API路由

* `frontend/`: UI重构和移动端适配

### 新增模块

* `src/storage/`: 分布式存储模块

* `src/calendar/`: 日历模块

* `src/human_tasks/`: 人类任务模块

* `src/email/`: 邮件模块

* `src/voice/`: 语音交互模块

* `src/desktop/`: 桌面自动化模块

* `src/mobile/`: 移动端模块

* `src/agents/`: 垂类智能体模块

* `src/pdf/`: PDF解析模块

***

## ADDED Requirements

### Requirement: Multi-Device Architecture

系统应支持多端架构，包括桌面端和移动端。

#### Scenario: Device Type Detection

* **WHEN** 应用启动时

* **THEN** 系统自动检测设备类型（PC/MOBILE）

* **AND** 根据设备类型加载对应的功能模块

#### Scenario: Device Capability Declaration

* **WHEN** 设备加入域时

* **THEN** 系统收集设备能力信息

* **AND** 包括CPU核心数、内存、存储、GPU等

* **AND** 包括可用工具列表（浏览器操作/手机屏幕操作等）

#### Scenario: Mobile Backend Architecture

* **WHEN** 移动端应用启动时

* **THEN** 系统初始化内置Linux环境

* **AND** 在Linux环境中运行Python后端

* **AND** 提供本地API服务

***

### Requirement: Distributed Storage System

系统应提供分布式存储功能，支持跨设备文件同步。

#### Scenario: File Upload and Sync

* **WHEN** 用户上传文件到分布式存储

* **THEN** 系统记录文件所在设备和路径

* **AND** 推送文件元数据到域内所有设备

* **AND** 其他设备可查看文件列表

#### Scenario: File Access from Remote Device

* **WHEN** 用户访问非本设备文件时

* **THEN** 系统从文件所在设备拉取文件

* **AND** 缓存到本地

* **AND** 显示文件来源设备信息

#### Scenario: Office File Integration

* **WHEN** 用户使用Office功能打开文件

* **THEN** 系统自动同步文件到分布式存储

* **AND** 推送文件信息到域内设备

***

### Requirement: Calendar System

系统应提供日历功能，支持日程安排。

#### Scenario: Create Calendar Event

* **WHEN** 用户创建日程事件

* **THEN** 系统保存事件信息

* **AND** 支持设置提醒时间

* **AND** 支持跨设备同步

#### Scenario: AI Assisted Scheduling

* **WHEN** 用户请求AI帮助安排日程

* **THEN** AI分析用户日历

* **AND** 智能推荐时间安排

* **AND** 自动创建事件

***

### Requirement: Human Task Management

系统应提供人类任务管理功能（区别于AI Todo系统）。

#### Scenario: Create Human Task

* **WHEN** 用户创建待办事项

* **THEN** 系统保存任务信息

* **AND** 支持设置截止日期和优先级

* **AND** 支持任务分类和标签

#### Scenario: Task Reminder

* **WHEN** 任务到达提醒时间

* **THEN** 系统发送通知

* **AND** 支持多端同步提醒

***

### Requirement: Email System

系统应提供邮件功能。

#### Scenario: Send Email

* **WHEN** 用户发送邮件

* **THEN** 系统通过配置的邮件服务器发送

* **AND** 支持附件

* **AND** 记录邮件历史

#### Scenario: Receive Email

* **WHEN** 系统检测到新邮件

* **THEN** 解析邮件内容

* **AND** 通知用户

* **AND** AI可辅助处理邮件

***

### Requirement: Slash Panel Optimization

斜杠面板应优化为三栏布局。

#### Scenario: Panel Display

* **WHEN** 用户输入"/"触发斜杠面板

* **THEN** 显示三栏布局

* **AND** 最近栏：彩色图标横排展示Word/PPT/Excel

* **AND** 最近栏下方：最近打开的三个文件

* **AND** 应用栏：其他应用，黑白图标，三列布局

* **AND** 配置栏：设置、Mate模式、新话题等

#### Scenario: Recent Files Sync

* **WHEN** 用户在任一设备打开文件

* **THEN** 文件信息同步到域内所有设备

* **AND** 显示在最近文件列表中

***

### Requirement: Desktop Mouse and Keyboard Automation

电脑端应支持AI驱动的键鼠操作功能。

#### Scenario: Screen Analysis

* **WHEN** AI需要操作桌面应用

* **THEN** 系统截取屏幕

* **AND** AI分析屏幕内容

* **AND** 决定操作步骤

#### Scenario: Mouse and Keyboard Simulation

* **WHEN** AI决定执行操作

* **THEN** 系统模拟鼠标移动和点击

* **AND** 模拟键盘输入

* **AND** 支持滚动等操作

#### Scenario: Operation Verification

* **WHEN** 操作执行后

* **THEN** 系统再次截图验证

* **AND** AI判断操作是否成功

* **AND** 必要时进行修正

***

### Requirement: Voice Interaction

系统应支持语音交互能力。

#### Scenario: Voice Input

* **WHEN** 用户说话时

* **THEN** 系统实时转录语音为文字

* **AND** 支持多语言识别

* **AND** 支持热词定制

#### Scenario: Text to Speech

* **WHEN** AI需要语音回复

* **THEN** 系统将文字转换为语音

* **AND** 支持多种音色选择

* **AND** 支持语速调节

#### Scenario: Video Narration

* **WHEN** 用户在视频编辑器中生成旁白

* **THEN** 系统使用TTS生成音频

* **AND** 自动对齐时间轴

***

### Requirement: Financial Agent

系统应提供金融垂类智能体。

#### Scenario: Financial Analysis

* **WHEN** 用户请求金融分析

* **THEN** 金融智能体分析数据

* **AND** 提供投资建议

* **AND** 展示相关图表

#### Scenario: Market Monitoring

* **WHEN** 用户设置市场监控

* **THEN** 智能体持续监控市场动态

* **AND** 异常情况及时通知

***

### Requirement: Browser Automation

系统应支持AI驱动的浏览器自动化。

#### Scenario: Web Task Execution

* **WHEN** 用户请求执行网页任务

* **THEN** AI控制浏览器访问目标网站

* **AND** 自动填写表单

* **AND** 提取所需信息

#### Scenario: Multi-Tab Management

* **WHEN** 任务需要多个网页

* **THEN** AI管理多个标签页

* **AND** 协调跨页面操作

***

### Requirement: PDF Parsing

系统应提供面向AI的高性能PDF解析。

#### Scenario: PDF Content Extraction

* **WHEN** 用户上传PDF文件

* **THEN** 系统解析PDF内容

* **AND** 提取文本、表格、图片

* **AND** 保留文档结构

#### Scenario: AI Ready Output

* **WHEN** PDF解析完成

* **THEN** 输出AI友好的格式

* **AND** 支持Markdown输出

* **AND** 支持结构化数据提取

***

### Requirement: Application Packaging

系统应提供EXE和APK封装。

#### Scenario: Windows EXE Build

* **WHEN** 执行打包命令

* **THEN** 系统生成Windows可执行文件

* **AND** 包含所有依赖

* **AND** 支持一键安装

#### Scenario: Android APK Build

* **WHEN** 执行打包命令

* **THEN** 系统生成Android安装包

* **AND** 包含Linux后端环境

* **AND** 支持直接安装运行

***

## MODIFIED Requirements

### Requirement: Device System Enhancement

原有设备系统需要扩展以支持多端架构。

**新增内容**:

* 设备类型枚举扩展：PC、MOBILE、SERVER、EDGE

* 设备能力声明：包括可用工具集

* 移动端特殊能力：屏幕操作、通知读取、短信收发

### Requirement: Execution Module Enhancement

执行模块需要优化智能体编排架构。

**新增内容**:

* 参考deer-flow优化中间件架构

* 支持更灵活的子智能体编排

* 增强错误处理和重试机制

### Requirement: LLM Module Enhancement

LLM模块需要支持更多模型提供商。

**新增内容**:

* 参考LiteLLM简化模型连接

* 支持更多模型提供商

* 统一API接口

***

## REMOVED Requirements

无移除的功能。

***

## Technical Architecture

### Directory Structure Changes

```
src/
├── storage/              # 分布式存储
│   ├── distributed.py    # 分布式存储核心
│   ├── file_tracker.py   # 文件追踪
│   └── sync_protocol.py  # 同步协议
├── calendar/             # 日历模块
│   ├── manager.py        # 日历管理
│   ├── event.py          # 事件模型
│   └── reminder.py       # 提醒服务
├── human_tasks/          # 人类任务
│   ├── manager.py        # 任务管理
│   ├── task.py           # 任务模型
│   └── notification.py   # 通知服务
├── email/                # 邮件模块
│   ├── client.py         # 邮件客户端
│   ├── parser.py         # 邮件解析
│   └── templates.py      # 邮件模板
├── voice/                # 语音交互
│   ├── asr.py            # 语音识别
│   ├── tts.py            # 语音合成
│   └── processor.py      # 语音处理
├── desktop/              # 桌面自动化
│   ├── screen.py         # 屏幕捕获
│   ├── mouse.py          # 鼠标控制
│   ├── keyboard.py       # 键盘控制
│   └── automation.py     # 自动化核心
├── mobile/               # 移动端模块
│   ├── linux_env.py      # Linux环境
│   ├── screen_tools.py   # 屏幕操作工具
│   ├── notification.py   # 通知读取
│   └── sms.py            # 短信工具
├── agents/               # 垂类智能体
│   ├── base.py           # 基类
│   ├── financial.py      # 金融智能体
│   └── registry.py       # 注册中心
├── pdf/                  # PDF解析
│   ├── parser.py         # 解析器
│   ├── extractor.py      # 内容提取
│   └── converter.py      # 格式转换
└── packaging/            # 打包配置
    ├── windows.py        # Windows打包
    └── android.py        # Android打包
```

### Frontend Structure Changes

```
frontend/
├── src/
│   ├── views/
│   │   ├── CalendarView.vue    # 日历视图
│   │   ├── TasksView.vue       # 人类任务视图
│   │   ├── EmailView.vue       # 邮件视图
│   │   └── SettingsView.vue    # 设置视图
│   ├── components/
│   │   ├── slash_panel/        # 斜杠面板
│   │   │   ├── RecentSection.vue
│   │   │   ├── AppsSection.vue
│   │   │   └── ConfigSection.vue
│   │   └── voice/              # 语音组件
│   └── mobile/                 # 移动端适配
│       ├── App.vue
│       └── views/
```

### Configuration Files

```
config/
├── storage.yaml      # 分布式存储配置
├── calendar.yaml     # 日历配置
├── email.yaml        # 邮件配置
├── voice.yaml        # 语音配置
├── desktop.yaml      # 桌面自动化配置
└── mobile.yaml       # 移动端配置
```

***

## Migration Strategy

### Phase 1: Core Infrastructure

1. 多端架构基础设施
2. 设备能力声明系统
3. 分布式存储核心

### Phase 2: Feature Migration

1. 从twenty迁移日历、邮件功能
2. 从VibeVoice迁移语音功能
3. 从browser-use迁移浏览器自动化
4. 从Operit迁移移动端架构

### Phase 3: Enhancement

1. 斜杠面板优化
2. 智能体编排优化
3. 金融智能体

### Phase 4: Packaging

1. EXE打包
2. APK打包
3. 测试和发布

