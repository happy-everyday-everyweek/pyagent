# Tasks

## Phase 1: LLM模块核心重构

- [x] Task 1: 重构LLM类型定义系统
  - [x] SubTask 1.1: 创建新的模型层级枚举（ModelTier: BASE/STRONG/PERFORMANCE/COST_EFFECTIVE）
  - [x] SubTask 1.2: 创建垂类模型类型枚举（VerticalType: SCREEN_OPERATION/MULTIMODAL/CUSTOM）
  - [x] SubTask 1.3: 定义新的ModelConfig数据结构，支持分级模型和垂类模型
  - [x] SubTask 1.4: 定义VerticalModelConfig数据结构，包含使用场景描述字段

- [x] Task 2: 实现设备ID系统
  - [x] SubTask 2.1: 创建DeviceID生成器，实现日期+随机数→SHA256哈希
  - [x] SubTask 2.2: 实现设备ID持久化存储
  - [x] SubTask 2.3: 创建设备ID管理器单例

- [x] Task 3: 重构模型配置加载器
  - [x] SubTask 3.1: 更新config/models.yaml配置格式
  - [x] SubTask 3.2: 实现新配置格式的解析逻辑
  - [x] SubTask 3.3: 实现分级模型自动选择逻辑
  - [x] SubTask 3.4: 实现垂类模型路由判断逻辑

- [x] Task 4: 重构LLM客户端
  - [x] SubTask 4.1: 实现基于任务类型的模型选择器
  - [x] SubTask 4.2: 实现垂类模型调用接口
  - [x] SubTask 4.3: 实现多模态模型回退机制
  - [x] SubTask 4.4: 为不支持多模态的模型添加询问工具

## Phase 2: 统一工具调用接口

- [x] Task 5: 设计统一工具调用接口
  - [x] SubTask 5.1: 定义ToolLifecycle枚举（ACTIVATE/EXECUTE/DORMANT）
  - [x] SubTask 5.2: 创建UnifiedTool基类
  - [x] SubTask 5.3: 定义工具调用上下文（包含设备ID）

- [x] Task 6: 重构Skill工具系统
  - [x] SubTask 6.1: 使Skill继承UnifiedTool基类
  - [x] SubTask 6.2: 实现三阶段调用流程

- [x] Task 7: 重构MCP工具系统
  - [x] SubTask 7.1: 使MCP工具继承UnifiedTool基类
  - [x] SubTask 7.2: 实现三阶段调用流程

- [x] Task 8: 创建工具注册中心
  - [x] SubTask 8.1: 实现统一工具注册中心
  - [x] SubTask 8.2: 工具列表包含设备ID信息
  - [x] SubTask 8.3: 实现工具状态管理（激活/休眠）

## Phase 3: Mate模式重构

- [x] Task 9: 重构Mate模式管理器
  - [x] SubTask 9.1: 移除原有的推理可视化和预推理反思功能
  - [x] SubTask 9.2: 简化为多智能体协作模式开关
  - [x] SubTask 9.3: 与CollaborationManager集成

- [x] Task 10: 更新Mate模式API
  - [x] SubTask 10.1: 简化Mate模式状态接口
  - [x] SubTask 10.2: 移除不再需要的API端点

## Phase 4: Web UI重构

- [x] Task 11: 重构ChatView输入区域
  - [x] SubTask 11.1: 实现斜杠命令检测
  - [x] SubTask 11.2: 创建快捷菜单组件（设置、新话题、Mate模式）
  - [x] SubTask 11.3: 移除设置页面入口按钮

- [x] Task 12: 重构任务进度卡片
  - [x] SubTask 12.1: 移除标题和创建时间显示
  - [x] SubTask 12.2: 实现进度背景色渐变效果
  - [x] SubTask 12.3: 优化卡片布局

- [x] Task 13: 简化设置页面
  - [x] SubTask 13.1: 优化模型配置界面
  - [x] SubTask 13.2: 添加垂类模型配置入口

## Phase 5: ClawHub集成与文档更新

- [x] Task 14: ClawHub MCP安装协议集成
  - [x] SubTask 14.1: 创建ClawHub安装器
  - [x] SubTask 14.2: 实现URL解析和服务器信息获取
  - [x] SubTask 14.3: 实现MCP服务器安装和卸载

- [x] Task 15: 更新文档
  - [x] SubTask 15.1: 更新CHANGELOG.md
  - [x] SubTask 15.2: 更新AGENTS.md版本信息
  - [x] SubTask 15.3: 更新docs/modules/llm-client.md

## Phase 6: 测试与验证

- [x] Task 16: 编写单元测试
  - [x] SubTask 16.1: LLM分级模型选择测试
  - [x] SubTask 16.2: 垂类模型路由测试
  - [x] SubTask 16.3: 设备ID生成测试
  - [x] SubTask 16.4: 统一工具调用测试

- [x] Task 17: 集成测试
  - [x] SubTask 17.1: 端到端任务执行测试
  - [x] SubTask 17.2: Web UI交互测试
  - [x] SubTask 17.3: Mate模式切换测试

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 1
- Task 4 depends on Task 3
- Task 5 can run in parallel with Task 1-4
- Task 6 depends on Task 5
- Task 7 depends on Task 5
- Task 8 depends on Task 5, Task 6, Task 7
- Task 9 can run in parallel with Task 1-8
- Task 10 depends on Task 9
- Task 11 can run in parallel with backend tasks
- Task 12 can run in parallel with backend tasks
- Task 13 depends on Task 11
- Task 14 can run in parallel with other tasks
- Task 15 depends on all previous tasks
- Task 16 depends on Task 1-8
- Task 17 depends on all previous tasks
