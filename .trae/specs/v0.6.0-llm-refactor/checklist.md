# Checklist

## LLM模块核心重构

- [x] 新的ModelTier枚举包含BASE/STRONG/PERFORMANCE/COST_EFFECTIVE
- [x] VerticalType枚举包含SCREEN_OPERATION/MULTIMODAL/CUSTOM
- [x] ModelConfig支持分级模型和垂类模型配置
- [x] VerticalModelConfig包含使用场景描述字段
- [x] 设备ID生成器正确实现日期+随机数→SHA256哈希
- [x] 设备ID持久化存储正常工作
- [x] config/models.yaml使用新格式
- [x] 分级模型自动选择逻辑正确
- [x] 垂类模型路由判断逻辑正确
- [x] 多模态模型回退机制正常工作
- [x] 不支持多模态的模型添加了询问工具

## 统一工具调用接口

- [x] ToolLifecycle枚举包含ACTIVATE/EXECUTE/DORMANT
- [x] UnifiedTool基类定义完整
- [x] Skill工具继承UnifiedTool并实现三阶段调用
- [x] MCP工具继承UnifiedTool并实现三阶段调用
- [x] 工具注册中心正常工作
- [x] 工具列表包含设备ID信息
- [x] 工具状态管理（激活/休眠）正常

## Mate模式重构

- [x] 移除了原有的推理可视化功能
- [x] 移除了预推理反思功能
- [x] Mate模式简化为多智能体协作模式开关
- [x] 与CollaborationManager正确集成
- [x] Mate模式API已简化

## Web UI重构

- [x] 输入框支持斜杠命令检测
- [x] 快捷菜单组件正常显示（设置、新话题、Mate模式）
- [x] 设置页面入口按钮已移除
- [x] 任务进度卡片不显示标题和创建时间
- [x] 进度以背景色渐变形式显示
- [x] 设置页面模型配置界面已优化
- [x] 垂类模型配置入口可用

## ClawHub集成

- [x] ClawHub安装器创建完成
- [x] URL解析和服务器信息获取正常工作
- [x] MCP服务器安装和卸载功能正常

## 文档更新

- [x] CHANGELOG.md已更新v0.6.0版本信息
- [x] AGENTS.md版本信息已更新为v0.6.0
- [x] docs/modules/llm-client.md已更新

## 测试验证

- [x] LLM分级模型选择测试通过
- [x] 垂类模型路由测试通过
- [x] 设备ID生成测试通过
- [x] 统一工具调用测试通过
- [x] 端到端任务执行测试通过
- [x] Web UI交互测试通过
- [x] Mate模式切换测试通过
