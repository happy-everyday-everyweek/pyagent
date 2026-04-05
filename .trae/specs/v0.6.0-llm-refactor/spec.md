# v0.6.0 LLM Module Refactor Spec

## Why

当前LLM模块采用四层模型架构（STRONG/BALANCED/FAST/TINY），但存在以下问题：
1. 模型分类不够清晰，无法精确匹配不同场景的需求
2. 缺少垂类模型支持，无法处理特殊场景（如屏幕操作、多模态）
3. 没有设备标识系统，无法进行设备级别的追踪和管理
4. 工具调用流程不统一，Skill、MCP、自定义工具各自实现
5. Mate模式功能复杂，与多智能体协作模式概念混淆

## What Changes

### LLM模块重构
- **BREAKING**: 废除四层模型架构（STRONG/BALANCED/FAST/TINY）
- 新增基础模型配置（必填），作为默认模型
- 新增分级模型系统：
  - 强能力模型（strong）：负责规划任务，如GLM-5、GPT-5
  - 高性能模型（performance）：负责日常任务，如qwen3.5-35b-a3b
  - 性价比模型（cost-effective）：负责意图判断、记忆整理、浏览器操作等高Token消耗或简单任务，如qwen3.5-4b/2b
- 新增垂类模型系统：
  - 屏幕操作模型（screen-operation）：默认推荐AutoGLM-Phone-9B
  - 多模态模型（multimodal）：处理图片、视频、音频内容
  - 支持用户自定义垂类模型类型，需提供使用场景描述
- 新增垂类模型路由判断机制：自定义垂类模型由性价比模型判断是否需要调用

### 设备ID系统
- 新增设备唯一标识符生成
- 设备ID格式：当前日期 + 10位随机数 → SHA256哈希值
- 工具列表包含设备ID信息

### 统一工具调用接口
- **BREAKING**: 重构所有工具调用流程
- 统一三阶段调用：激活 → 调用 → 休眠
- 适用于Skill、MCP工具、自定义工具

### Mate模式重构
- **BREAKING**: 移除原有Mate模式所有功能（推理可视化、预推理反思等）
- 新Mate模式：开启后使用多智能体协作模式，关闭则不使用

### Web UI重构
- **BREAKING**: 移除设置页面入口按钮
- 新增斜杠命令入口：输入框输入"/"后显示快捷菜单
- 快捷菜单选项：设置、新话题、Mate模式开关
- 任务进度卡片重构：
  - 移除标题、创建时间显示
  - 进度条改为卡片背景色渐变显示

### ClawHub集成
- 新增ClawHub平台支持

## Impact

- Affected specs: LLM配置系统、工具调用系统、Mate模式、Web UI
- Affected code:
  - `src/llm/` - 完全重构
  - `src/todo/mate_mode.py` - 重构
  - `src/execution/collaboration.py` - 与Mate模式集成
  - `src/mcp/` - 工具调用统一
  - `frontend/src/views/ChatView.vue` - UI重构
  - `config/models.yaml` - 配置格式变更

## ADDED Requirements

### Requirement: LLM分级模型系统

系统应提供三级分级模型配置，根据任务类型自动选择合适的模型。

#### Scenario: 强能力模型处理规划任务
- **WHEN** 用户请求需要复杂规划的任务
- **THEN** 系统使用强能力模型（如GLM-5、GPT-5）进行处理

#### Scenario: 高性能模型处理日常任务
- **WHEN** 用户请求常规对话或工具调用任务
- **THEN** 系统使用高性能模型（如qwen3.5-35b-a3b）进行处理

#### Scenario: 性价比模型处理简单任务
- **WHEN** 系统需要执行意图判断、记忆整理或浏览器操作
- **THEN** 系统使用性价比模型（如qwen3.5-4b）进行处理

### Requirement: 垂类模型支持

系统应支持垂类模型配置和智能路由。

#### Scenario: 屏幕操作任务
- **WHEN** 任务涉及手机屏幕操作
- **THEN** 系统路由到屏幕操作模型（如AutoGLM-Phone-9B）

#### Scenario: 多模态内容处理
- **WHEN** 配置的主模型不支持多模态，但用户发送了图片/视频/音频
- **THEN** 系统使用多模态模型处理内容，并为主模型添加询问工具

#### Scenario: 自定义垂类模型路由
- **WHEN** 用户添加了自定义垂类模型
- **THEN** 系统使用性价比模型判断是否需要调用该垂类模型

### Requirement: 设备ID系统

系统应为每个设备生成唯一标识符。

#### Scenario: 首次使用生成设备ID
- **WHEN** 设备首次使用系统
- **THEN** 系统生成唯一设备ID（日期+10位随机数的SHA256哈希）
- **AND** 设备ID持久化存储

#### Scenario: 工具列表包含设备ID
- **WHEN** 系统返回工具列表
- **THEN** 每个工具信息包含设备ID标识

### Requirement: 统一工具调用接口

所有工具调用应遵循统一的三阶段流程。

#### Scenario: Skill工具调用
- **WHEN** 调用Skill工具
- **THEN** 系统执行：激活工具 → 调用工具 → 使工具进入休眠状态

#### Scenario: MCP工具调用
- **WHEN** 调用MCP工具
- **THEN** 系统执行：激活工具 → 调用工具 → 使工具进入休眠状态

#### Scenario: 自定义工具调用
- **WHEN** 调用自定义工具
- **THEN** 系统执行：激活工具 → 调用工具 → 使工具进入休眠状态

### Requirement: Mate模式重构

Mate模式应简化为多智能体协作模式的开关。

#### Scenario: 开启Mate模式
- **WHEN** 用户开启Mate模式
- **THEN** 系统使用多智能体协作模式执行任务

#### Scenario: 关闭Mate模式
- **WHEN** 用户关闭Mate模式
- **THEN** 系统使用单智能体模式执行任务

### Requirement: Web UI斜杠命令

设置入口应通过输入框斜杠命令访问。

#### Scenario: 输入斜杠显示菜单
- **WHEN** 用户在输入框输入"/"
- **THEN** 显示快捷菜单，包含：设置、新话题、Mate模式开关选项

#### Scenario: 选择菜单项
- **WHEN** 用户点击菜单项
- **THEN** 执行对应操作（打开设置/开启新话题/切换Mate模式）

### Requirement: 任务进度卡片UI

任务进度卡片应采用简洁的背景色渐变显示。

#### Scenario: 显示任务进度
- **WHEN** 聊天中显示任务进度卡片
- **THEN** 卡片不显示标题和创建时间
- **AND** 进度以背景色渐变形式显示

## MODIFIED Requirements

### Requirement: 模型配置格式

原有的四层模型配置格式修改为新的分级+垂类模型格式。

**原格式**:
```yaml
models:
  strong: {...}
  balanced: {...}
  fast: {...}
  tiny: {...}
```

**新格式**:
```yaml
models:
  base: {...}  # 基础模型（必填）
  tiers:
    strong: {...}
    performance: {...}
    cost-effective: {...}
  vertical:
    screen-operation: {...}
    multimodal: {...}
    # 用户自定义垂类模型
```

## REMOVED Requirements

### Requirement: 旧Mate模式功能

**Reason**: 功能复杂且与多智能体协作模式概念重复
**Migration**: 原有的推理可视化、预推理反思功能移除，用户可使用新版Mate模式（多智能体协作）

### Requirement: 设置页面入口按钮

**Reason**: UI简化，改为斜杠命令入口
**Migration**: 用户通过输入框输入"/"访问设置
