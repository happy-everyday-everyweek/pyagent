# Python Agent 智能体系统 Spec

## Why
构建一个模块化、可扩展的Python Agent智能体框架，实现执行与交互分离的设计理念，支持多模型配置、MCP协议、Skills系统和多IM平台集成。

## What Changes
- 创建核心Agent框架，实现聊天Agent与执行Agent的模块间通信架构
- 集成MCP (Model Context Protocol) 协议支持
- 实现Skills技能系统加载与管理
- 支持微信、飞书、企微、钉钉、QQ、OneBot六大IM平台
- 构建多模型配置系统（较强/均衡/快速/微小）
- 实现拟人化聊天系统（参考MaiBot HeartFChatting架构）
- 实现ReAct推理引擎与安全策略（参考OpenAkita）
- 构建Web UI管理界面

## Impact
- Affected specs: 新建完整Agent系统
- Affected code: 全新项目结构

## ADDED Requirements

### Requirement: 核心架构设计 - 模块间通信
系统应采用分层模块化架构，聊天Agent与执行Agent之间是模块间通信关系，而非多智能体转交关系。

#### Scenario: 聊天Agent与执行Agent模块间通信
- **WHEN** 用户发送消息到任意IM平台
- **THEN** 聊天Agent接收消息，通过ActionPlanner规划动作
- **AND** 聊天Agent通过模块间通信调用执行Agent的工具
- **AND** 执行Agent返回执行结果给聊天Agent
- **AND** 聊天Agent生成拟人化回复

#### Scenario: 执行Agent内部多智能体协作
- **WHEN** 执行Agent需要执行复杂任务
- **THEN** 执行Agent可以将任务委派给专业子Agent
- **AND** 子Agent之间是多智能体转交关系
- **AND** 子Agent完成后将结果返回给执行Agent

### Requirement: 聊天Agent核心循环（参考MaiBot HeartFChatting）
聊天Agent应实现持续的消息监控和动作规划循环。

#### Scenario: 消息监控循环
- **WHEN** 聊天Agent启动
- **THEN** 进入HeartFChatting风格的主循环
- **AND** 持续监控新消息到达
- **AND** 根据频率控制决定是否响应

#### Scenario: ActionPlanner动作规划
- **WHEN** 聊天Agent决定响应消息
- **THEN** 调用ActionPlanner规划动作
- **AND** 构建包含聊天上下文的提示词
- **AND** LLM返回动作选择（reply/no_reply/其他动作）
- **AND** 执行选定的动作

#### Scenario: 动作执行与记录
- **WHEN** ActionPlanner返回动作列表
- **THEN** 并行执行所有动作
- **AND** 记录CycleDetail循环信息
- **AND** 更新last_active_time

### Requirement: 多模型配置系统
系统应支持四层模型配置，按任务复杂度自动选择合适模型。

#### Scenario: 模型自动选择
- **WHEN** 系统需要调用LLM
- **THEN** 根据任务类型自动选择对应模型
- **AND** 规划任务使用较强模型（GLM-5/GPT-5）
- **AND** 常规任务使用均衡模型（DeepSeek-chat）
- **AND** 记忆整理使用快速模型（qwen3.5-35b）
- **AND** 意图判断使用微小模型（qwen3.5-4b）

### Requirement: 聊天Agent工具集
聊天Agent应具备四个核心工具，通过模块间通信调用。

#### Scenario: 搜索工具调用
- **WHEN** 用户提问需要搜索信息
- **THEN** 聊天Agent通过模块间通信调用搜索模块
- **AND** 搜索模块执行搜索并返回结果
- **AND** 聊天Agent基于结果生成回复

#### Scenario: 阅读工具调用
- **WHEN** 需要阅读文件或网页内容
- **THEN** 聊天Agent通过模块间通信调用阅读模块
- **AND** 阅读模块返回内容摘要

#### Scenario: 执行工具调用
- **WHEN** 需要执行具体操作任务
- **THEN** 聊天Agent通过模块间通信调用执行Agent
- **AND** 执行Agent支持同步和异步两种模式
- **AND** 同步模式直接返回结果
- **AND** 异步模式返回任务编号

#### Scenario: 记忆工具调用
- **WHEN** 需要存储或检索记忆
- **THEN** 聊天Agent通过模块间通信调用记忆模块
- **AND** 记忆模块支持短期记忆和长期记忆

### Requirement: 拟人化聊天系统（参考MaiBot）
系统应具备拟人化的聊天能力。

#### Scenario: 自然语言风格
- **WHEN** 聊天Agent生成回复
- **THEN** 使用自然语言风格构建Prompt
- **AND** 回复贴近人类习惯
- **AND** 学习用户的表达方式和黑话（ExpressionLearner）

#### Scenario: 行为规划
- **WHEN** 聊天Agent决定是否回复
- **THEN** 懂得在合适的时间说话
- **AND** 支持主动问候
- **AND** 支持no_reply动作保持沉默
- **AND** 支持频率控制（frequency_control）

#### Scenario: 表达学习（ExpressionLearner）
- **WHEN** 聊天Agent处理消息
- **THEN** 从用户消息中学习语言风格
- **AND** 提取黑话/俚语/网络缩写
- **AND** 存储到数据库供后续使用

#### Scenario: 用户信息系统（Person）
- **WHEN** 聊天Agent需要了解用户
- **THEN** 从Person系统获取用户信息
- **AND** 包含用户昵称、记忆点、群昵称等
- **AND** 构建用户关系信息用于回复

### Requirement: ReAct推理引擎（参考OpenAkita）
执行Agent应实现显式三阶段推理循环。

#### Scenario: ReAct推理循环
- **WHEN** 执行Agent需要做出决策
- **THEN** 执行Think-Act-Observe三阶段循环
- **AND** 支持循环检测避免无限循环
- **AND** 失败时自动切换策略

#### Scenario: 工具抖动检测
- **WHEN** 检测到工具调用异常频繁
- **THEN** 触发抖动检测机制
- **AND** 自动降级或停止调用

### Requirement: 安全治理系统（参考OpenAkita）
系统应实现六层安全防护体系。

#### Scenario: 策略管理
- **WHEN** 执行敏感操作
- **THEN** 根据POLICIES.yaml策略判断
- **AND** 高危操作需要用户确认
- **AND** 数据本地存储

#### Scenario: 四区路径保护
- **WHEN** 执行文件操作
- **THEN** 判断路径所属区域（workspace/controlled/protected/forbidden）
- **AND** 根据区域策略决定是否允许操作

### Requirement: MCP协议支持
系统应支持MCP (Model Context Protocol) 协议。

#### Scenario: MCP服务器连接
- **WHEN** 系统启动或配置更新
- **THEN** 自动连接配置的MCP服务器
- **AND** 发现并注册MCP工具
- **AND** 支持stdio/streamable_http/sse三种传输协议

#### Scenario: MCP工具调用
- **WHEN** Agent调用MCP工具
- **THEN** 通过MCP协议与服务器通信
- **AND** 支持工具调用、资源读取、提示词获取

### Requirement: Skills技能系统
系统应支持Skills技能加载与管理。

#### Scenario: 技能发现与加载
- **WHEN** 系统启动
- **THEN** 自动扫描skills目录
- **AND** 解析SKILL.md文件
- **AND** 注册技能工具

#### Scenario: 技能执行
- **WHEN** Agent调用技能
- **THEN** 执行技能脚本或指令
- **AND** 返回执行结果

### Requirement: IM平台集成
系统应支持微信、飞书、企微、钉钉、QQ、OneBot六大IM平台。

#### Scenario: 微信消息接收
- **WHEN** 微信用户发送消息
- **THEN** 通过OneBot协议接收消息
- **AND** 转换为统一消息格式
- **AND** 传递给聊天Agent处理

#### Scenario: QQ消息接收
- **WHEN** QQ用户发送消息
- **THEN** 通过OneBot协议接收消息
- **AND** 转换为统一消息格式
- **AND** 传递给聊天Agent处理

#### Scenario: 钉钉消息接收
- **WHEN** 钉钉用户发送消息
- **THEN** 通过钉钉机器人Webhook接收
- **AND** 转换为统一消息格式
- **AND** 传递给聊天Agent处理

#### Scenario: 飞书消息接收
- **WHEN** 飞书用户发送消息
- **THEN** 通过飞书开放平台API接收
- **AND** 转换为统一消息格式
- **AND** 传递给聊天Agent处理

#### Scenario: 企业微信消息接收
- **WHEN** 企业微信用户发送消息
- **THEN** 通过企业微信API接收
- **AND** 转换为统一消息格式
- **AND** 传递给聊天Agent处理

### Requirement: Web UI管理界面
系统应提供前后端分离的Web管理界面。

#### Scenario: 聊天界面
- **WHEN** 用户访问Web界面
- **THEN** 显示聊天对话界面
- **AND** 支持发送消息和查看回复
- **AND** 显示任务执行状态

#### Scenario: 系统配置
- **WHEN** 管理员访问配置页面
- **THEN** 可以配置模型参数
- **AND** 可以管理MCP服务器
- **AND** 可以管理Skills技能

#### Scenario: 任务监控
- **WHEN** 查看任务列表
- **THEN** 显示所有异步任务状态
- **AND** 支持取消正在执行的任务
- **AND** 显示任务执行日志
