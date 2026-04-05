# Tasks

## Phase 1: 项目基础架构

- [x] Task 1.1: 创建项目目录结构
  - [x] SubTask 1.1.1: 创建src/core核心模块目录
  - [x] SubTask 1.1.2: 创建src/chat聊天Agent模块目录（参考MaiBot heart_flow）
  - [x] SubTask 1.1.3: 创建src/executor执行Agent模块目录
  - [x] SubTask 1.1.4: 创建src/mcp MCP协议模块目录
  - [x] SubTask 1.1.5: 创建src/skills技能系统目录
  - [x] SubTask 1.1.6: 创建src/im IM平台适配器目录
  - [x] SubTask 1.1.7: 创建src/llm模型层目录
  - [x] SubTask 1.1.8: 创建src/memory记忆系统目录
  - [x] SubTask 1.1.9: 创建src/security安全策略目录
  - [x] SubTask 1.1.10: 创建src/tools工具系统目录
  - [x] SubTask 1.1.11: 创建src/web Web服务目录
  - [x] SubTask 1.1.12: 创建src/person用户信息系统目录（参考MaiBot person_info）
  - [x] SubTask 1.1.13: 创建src/expression表达学习系统目录（参考MaiBot bw_learner）
  - [x] SubTask 1.1.14: 创建配置文件目录config/
  - [x] SubTask 1.1.15: 创建数据目录data/
  - [x] SubTask 1.1.16: 创建前端目录frontend/

- [x] Task 1.2: 创建项目配置文件
  - [x] SubTask 1.2.1: 创建pyproject.toml项目配置
  - [x] SubTask 1.2.2: 创建requirements.txt依赖清单
  - [x] SubTask 1.2.3: 创建.env.example环境变量模板
  - [x] SubTask 1.2.4: 创建config/models.yaml模型配置
  - [x] SubTask 1.2.5: 创建config/policies.yaml安全策略配置

## Phase 2: LLM模型层

- [x] Task 2.1: 实现多模型配置系统
  - [x] SubTask 2.1.1: 创建src/llm/config.py模型配置加载器
  - [x] SubTask 2.1.2: 创建src/llm/client.py统一LLM客户端
  - [x] SubTask 2.1.3: 创建src/llm/types.py类型定义
  - [x] SubTask 2.1.4: 实现模型自动选择逻辑
  - [x] SubTask 2.1.5: 实现模型故障切换机制

- [x] Task 2.2: 实现LLM适配器
  - [x] SubTask 2.2.1: 创建OpenAI兼容适配器
  - [x] SubTask 2.2.2: 创建Anthropic适配器
  - [x] SubTask 2.2.3: 创建智谱AI适配器
  - [x] SubTask 2.2.4: 创建DeepSeek适配器

## Phase 3: 聊天Agent核心（参考MaiBot HeartFChatting）

- [x] Task 3.1: 实现聊天Agent核心循环
  - [x] SubTask 3.1.1: 创建src/chat/heart_flow/heartf_chatting.py主循环（参考MaiBot）
  - [x] SubTask 3.1.2: 创建src/chat/heart_flow/cycle_detail.py循环信息记录
  - [x] SubTask 3.1.3: 创建src/chat/heart_flow/frequency_control.py频率控制
  - [x] SubTask 3.1.4: 实现消息监控循环_loopbody
  - [x] SubTask 3.1.5: 实现动作执行_execute_action

- [x] Task 3.2: 实现ActionPlanner动作规划器（参考MaiBot）
  - [x] SubTask 3.2.1: 创建src/chat/planner/action_planner.py规划器核心
  - [x] SubTask 3.2.2: 创建src/chat/planner/action_manager.py动作管理器
  - [x] SubTask 3.2.3: 创建src/chat/planner/action_modifier.py动作修改器
  - [x] SubTask 3.2.4: 实现build_planner_prompt提示词构建
  - [x] SubTask 3.2.5: 实现plan动作规划逻辑
  - [x] SubTask 3.2.6: 实现JSON解析_extract_json_from_markdown

- [x] Task 3.3: 实现Replyer回复生成器（参考MaiBot）
  - [x] SubTask 3.3.1: 创建src/chat/replyer/replyer_manager.py回复器管理
  - [x] SubTask 3.3.2: 创建src/chat/replyer/group_generator.py群聊回复器
  - [x] SubTask 3.3.3: 创建src/chat/replyer/private_generator.py私聊回复器
  - [x] SubTask 3.3.4: 实现generate_reply回复生成

- [x] Task 3.4: 实现聊天Agent工具集（模块间通信）
  - [x] SubTask 3.4.1: 创建src/chat/tools/search_tool.py搜索工具
  - [x] SubTask 3.4.2: 创建src/chat/tools/read_tool.py阅读工具
  - [x] SubTask 3.4.3: 创建src/chat/tools/execute_tool.py执行工具（模块间通信调用执行Agent）
  - [x] SubTask 3.4.4: 创建src/chat/tools/memory_tool.py记忆工具

## Phase 4: 执行Agent（支持内部多智能体协作）

- [x] Task 4.1: 实现执行Agent核心
  - [x] SubTask 4.1.1: 创建src/executor/executor_agent.py执行Agent核心
  - [x] SubTask 4.1.2: 实现ReAct推理引擎（参考OpenAkita brain.py）
  - [x] SubTask 4.1.3: 实现任务队列管理
  - [x] SubTask 4.1.4: 实现同步/异步执行模式
  - [x] SubTask 4.1.5: 实现任务状态追踪

- [x] Task 4.2: 实现执行Agent工具系统
  - [x] SubTask 4.2.1: 创建src/executor/tools/base.py工具基类
  - [x] SubTask 4.2.2: 创建src/executor/tools/registry.py工具注册中心
  - [x] SubTask 4.2.3: 创建src/executor/tools/catalog.py工具目录
  - [x] SubTask 4.2.4: 实现shell_tool Shell命令工具
  - [x] SubTask 4.2.5: 实现file_tools文件操作工具
  - [x] SubTask 4.2.6: 实现browser_tools浏览器工具
  - [x] SubTask 4.2.7: 实现web_tools网络请求工具

- [x] Task 4.3: 实现执行Agent内部子Agent协作
  - [x] SubTask 4.3.1: 创建src/executor/sub_agents/base_sub_agent.py子Agent基类
  - [x] SubTask 4.3.2: 创建src/executor/sub_agents/search_agent.py搜索子Agent
  - [x] SubTask 4.3.3: 创建src/executor/sub_agents/browser_agent.py浏览器子Agent
  - [x] SubTask 4.3.4: 实现子Agent任务委派机制
  - [x] SubTask 4.3.5: 实现子Agent结果聚合

## Phase 5: 用户信息系统（参考MaiBot Person）

- [x] Task 5.1: 实现用户信息管理
  - [x] SubTask 5.1.1: 创建src/person/person.py用户类（参考MaiBot）
  - [x] SubTask 5.1.2: 创建src/person/person_manager.py用户管理器
  - [x] SubTask 5.1.3: 实现用户注册register_person
  - [x] SubTask 5.1.4: 实现记忆点管理memory_points
  - [x] SubTask 5.1.5: 实现群昵称管理group_nick_name
  - [x] SubTask 5.1.6: 实现用户关系构建build_relationship

## Phase 6: 表达学习系统（参考MaiBot ExpressionLearner）

- [x] Task 6.1: 实现表达学习器
  - [x] SubTask 6.1.1: 创建src/expression/expression_learner.py表达学习器（参考MaiBot）
  - [x] SubTask 6.1.2: 创建src/expression/jargon_miner.py黑话挖掘器
  - [x] SubTask 6.1.3: 实现learn_and_store学习存储
  - [x] SubTask 6.1.4: 实现表达方式过滤_filter_expressions
  - [x] SubTask 6.1.5: 实现黑话处理_process_jargon_entries

## Phase 7: 记忆系统

- [x] Task 7.1: 实现记忆存储
  - [x] SubTask 7.1.1: 创建src/memory/storage.py记忆存储
  - [x] SubTask 7.1.2: 实现短期记忆（会话级别）
  - [x] SubTask 7.1.3: 实现长期记忆（持久化）
  - [x] SubTask 7.1.4: 实现记忆检索（参考MaiBot memory_retrieval）

- [x] Task 7.2: 实现记忆管理
  - [x] SubTask 7.2.1: 创建src/memory/manager.py记忆管理器
  - [x] SubTask 7.2.2: 实现记忆整理（使用快速模型）
  - [x] SubTask 7.2.3: 实现记忆遗忘机制

## Phase 8: 安全策略系统（参考OpenAkita）

- [x] Task 8.1: 实现策略引擎
  - [x] SubTask 8.1.1: 创建src/security/policy.py策略引擎（参考OpenAkita）
  - [x] SubTask 8.1.2: 实现四区路径保护
  - [x] SubTask 8.1.3: 实现命令风险分级
  - [x] SubTask 8.1.4: 实现工具策略控制

- [x] Task 8.2: 实现安全机制
  - [x] SubTask 8.2.1: 实现高危操作确认机制
  - [x] SubTask 8.2.2: 实现工具抖动检测
  - [x] SubTask 8.2.3: 实现死亡开关（只读模式）

## Phase 9: MCP协议支持

- [x] Task 9.1: 实现MCP客户端
  - [x] SubTask 9.1.1: 创建src/mcp/client.py MCP客户端（参考OpenAkita）
  - [x] SubTask 9.1.2: 实现stdio传输协议
  - [x] SubTask 9.1.3: 实现streamable_http传输协议
  - [x] SubTask 9.1.4: 实现sse传输协议
  - [x] SubTask 9.1.5: 实现工具发现与注册

- [x] Task 9.2: 实现MCP服务器管理
  - [x] SubTask 9.2.1: 创建src/mcp/manager.py服务器管理器
  - [x] SubTask 9.2.2: 实现服务器配置加载
  - [x] SubTask 9.2.3: 实现连接状态监控

## Phase 10: Skills技能系统

- [x] Task 10.1: 实现Skills加载器
  - [x] SubTask 10.1.1: 创建src/skills/loader.py技能加载器（参考OpenAkita）
  - [x] SubTask 10.1.2: 创建src/skills/parser.py SKILL.md解析器
  - [x] SubTask 10.1.3: 创建src/skills/registry.py技能注册中心

- [x] Task 10.2: 实现Skills执行
  - [x] SubTask 10.2.1: 创建src/skills/executor.py技能执行器
  - [x] SubTask 10.2.2: 实现脚本执行环境
  - [x] SubTask 10.2.3: 实现技能工具生成

## Phase 11: IM平台适配器

- [x] Task 11.1: 实现IM适配器框架
  - [x] SubTask 11.1.1: 创建src/im/base.py IM适配器基类
  - [x] SubTask 11.1.2: 定义统一消息格式
  - [x] SubTask 11.1.3: 实现消息路由

- [x] Task 11.2: 实现微信/QQ适配器（OneBot协议）
  - [x] SubTask 11.2.1: 创建src/im/onebot.py OneBot适配器
  - [x] SubTask 11.2.2: 实现WebSocket连接
  - [x] SubTask 11.2.3: 实现消息收发

- [x] Task 11.3: 实现钉钉适配器
  - [x] SubTask 11.3.1: 创建src/im/dingtalk.py钉钉适配器
  - [x] SubTask 11.3.2: 实现钉钉机器人Webhook
  - [x] SubTask 11.3.3: 实现消息收发

- [x] Task 11.4: 实现飞书适配器
  - [x] SubTask 11.4.1: 创建src/im/feishu.py飞书适配器
  - [x] SubTask 11.4.2: 实现飞书开放平台API对接
  - [x] SubTask 11.4.3: 实现消息收发

- [x] Task 11.5: 实现企业微信适配器
  - [x] SubTask 11.5.1: 创建src/im/wecom.py企业微信适配器
  - [x] SubTask 11.5.2: 实现企业微信API对接
  - [x] SubTask 11.5.3: 实现消息收发

## Phase 12: Web服务

- [x] Task 12.1: 实现后端API
  - [x] SubTask 12.1.1: 创建src/web/app.py FastAPI应用
  - [x] SubTask 12.1.2: 创建src/web/routes/chat.py聊天API
  - [x] SubTask 12.1.3: 创建src/web/routes/tasks.py任务API
  - [x] SubTask 12.1.4: 创建src/web/routes/config.py配置API
  - [x] SubTask 12.1.5: 创建src/web/routes/mcp.py MCP管理API
  - [x] SubTask 12.1.6: 实现WebSocket实时通信

- [x] Task 12.2: 实现前端界面
  - [x] SubTask 12.2.1: 创建Vue/Vite项目结构
  - [x] SubTask 12.2.2: 实现聊天对话组件
  - [x] SubTask 12.2.3: 实现任务监控组件
  - [x] SubTask 12.2.4: 实现配置管理组件
  - [x] SubTask 12.2.5: 实现系统状态仪表盘

## Phase 13: 集成与测试

- [x] Task 13.1: 系统集成
  - [x] SubTask 13.1.1: 创建src/main.py主入口
  - [x] SubTask 13.1.2: 实现服务启动脚本
  - [x] SubTask 13.1.3: 实现Docker部署配置

- [ ] Task 13.2: 测试与文档
  - [ ] SubTask 13.2.1: 编写单元测试
  - [ ] SubTask 13.2.2: 编写集成测试
  - [ ] SubTask 13.2.3: 创建使用文档

# Task Dependencies

- Task 2.1 depends on Task 1.2
- Task 3.1 depends on Task 2.1
- Task 3.2 depends on Task 3.1
- Task 3.3 depends on Task 3.1
- Task 3.4 depends on Task 3.1
- Task 4.1 depends on Task 2.1
- Task 4.2 depends on Task 4.1
- Task 4.3 depends on Task 4.1
- Task 5.1 depends on Task 2.1
- Task 6.1 depends on Task 2.1
- Task 7.1 depends on Task 2.1
- Task 8.1 depends on Task 4.2
- Task 9.1 depends on Task 2.1
- Task 10.1 depends on Task 4.2
- Task 11.1 depends on Task 3.1
- Task 12.1 depends on Task 3.1, Task 4.1
- Task 12.2 depends on Task 12.1
- Task 13.1 depends on Task 12.1, Task 12.2
