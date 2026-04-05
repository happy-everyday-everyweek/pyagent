# Tasks

## 阶段一：模块重命名和基础架构

- [x] Task 1: 重命名聊天智能体为交互模块
  - [x] SubTask 1.1: 创建 `src/interaction/` 目录结构
  - [x] SubTask 1.2: 迁移 `src/chat/heart_flow/` 到 `src/interaction/heart_flow/`
  - [x] SubTask 1.3: 迁移 `src/chat/persona/` 到 `src/interaction/persona/`
  - [x] SubTask 1.4: 迁移 `src/chat/planner/` 到 `src/interaction/planner/`
  - [x] SubTask 1.5: 迁移 `src/chat/replyer/` 到 `src/interaction/reply/`
  - [x] SubTask 1.6: 更新所有导入路径

- [x] Task 2: 重命名执行智能体为执行模块
  - [x] SubTask 2.1: 创建 `src/execution/` 目录结构
  - [x] SubTask 2.2: 迁移 `src/executor/` 内容到 `src/execution/`
  - [x] SubTask 2.3: 创建 `src/execution/task.py` 任务定义
  - [x] SubTask 2.4: 创建 `src/execution/task_context.py` 任务上下文
  - [x] SubTask 2.5: 更新所有导入路径

## 阶段二：规划智能体和协作模式

- [x] Task 3: 实现规划智能体
  - [x] SubTask 3.1: 创建 `src/execution/planner.py` 规划智能体类
  - [x] SubTask 3.2: 实现任务分解逻辑
  - [x] SubTask 3.3: 实现智能体分配逻辑
  - [x] SubTask 3.4: 实现执行结果聚合

- [x] Task 4: 实现多智能体协作模式
  - [x] SubTask 4.1: 创建 `src/execution/collaboration.py` 协作管理器
  - [x] SubTask 4.2: 实现协作模式开关配置
  - [x] SubTask 4.3: 实现并行执行逻辑
  - [x] SubTask 4.4: 实现串行执行逻辑
  - [x] SubTask 4.5: 实现故障切换机制

- [x] Task 5: 重构执行智能体
  - [x] SubTask 5.1: 重构 `src/execution/executor.py` 支持任务执行
  - [x] SubTask 5.2: 添加任务上下文管理
  - [x] SubTask 5.3: 添加执行结果返回机制

## 阶段三：交互模块优化

- [x] Task 6: 优化交互模块
  - [x] SubTask 6.1: 创建 `src/interaction/intent/` 意图理解模块
  - [x] SubTask 6.2: 实现意图识别逻辑
  - [x] SubTask 6.3: 实现任务创建逻辑
  - [x] SubTask 6.4: 实现结果返回逻辑

## 阶段四：OpenClaw微信插件集成

- [x] Task 7: 创建微信适配器基础结构
  - [x] SubTask 7.1: 创建 `src/im/wechat/` 目录
  - [x] SubTask 7.2: 创建 `src/im/wechat/types.py` 类型定义
  - [x] SubTask 7.3: 创建 `src/im/wechat/api.py` API客户端
  - [x] SubTask 7.4: 创建 `src/im/wechat/adapter.py` 适配器实现

- [x] Task 8: 实现微信核心功能
  - [x] SubTask 8.1: 实现二维码登录功能
  - [x] SubTask 8.2: 实现多账号管理
  - [x] SubTask 8.3: 实现长轮询消息接收
  - [x] SubTask 8.4: 实现消息发送（文本/图片/视频/文件）
  - [x] SubTask 8.5: 实现CDN媒体上传
  - [x] SubTask 8.6: 实现输入状态指示

- [x] Task 9: 集成微信到IM路由
  - [x] SubTask 9.1: 更新 `src/im/router.py` 支持微信通道
  - [x] SubTask 9.2: 添加微信配置到 `config/wechat.yaml`
  - [x] SubTask 9.3: 实现上下文隔离配置

## 阶段五：Web UI优化

- [x] Task 10: 优化Web UI
  - [x] SubTask 10.1: 更新 `frontend/src/App.vue` 添加协作模式开关
  - [x] SubTask 10.2: 更新 `frontend/src/views/ChatView.vue` 优化交互体验
  - [x] SubTask 10.3: 创建 `frontend/src/views/TasksView.vue` 任务管理界面
  - [x] SubTask 10.4: 更新 `frontend/src/views/ConfigView.vue` 添加协作模式配置

- [x] Task 11: 更新API路由
  - [x] SubTask 11.1: 创建 `src/web/routes/task_routes.py` 任务API
  - [x] SubTask 11.2: 创建 `src/web/routes/execution_routes.py` 执行模块API
  - [x] SubTask 11.3: 更新 `src/web/app.py` 集成新路由

## 阶段六：测试和文档

- [x] Task 12: 更新测试
  - [x] SubTask 12.1: 创建 `tests/test_execution.py` 执行模块测试
  - [x] SubTask 12.2: 创建 `tests/test_planner.py` 规划智能体测试
  - [x] SubTask 12.3: 创建 `tests/test_wechat.py` 微信适配器测试
  - [x] SubTask 12.4: 更新 `tests/test_humanized.py` 导入路径

- [x] Task 13: 更新文档和版本
  - [x] SubTask 13.1: 更新 `CHANGELOG.md` 添加v0.4.0记录
  - [x] SubTask 13.2: 更新 `pyproject.toml` 版本号为0.4.0
  - [x] SubTask 13.3: 更新 `AGENTS.md` 架构说明
  - [x] SubTask 13.4: 创建记忆文档记录重构过程

# Task Dependencies

- [Task 2] depends on [Task 1] (先完成模块重命名)
- [Task 3] depends on [Task 2] (规划智能体依赖执行模块)
- [Task 4] depends on [Task 3] (协作模式依赖规划智能体)
- [Task 5] depends on [Task 2] (执行智能体重构依赖执行模块)
- [Task 6] depends on [Task 2] (交互模块优化依赖执行模块)
- [Task 7] depends on [Task 1] (OpenClaw适配器依赖交互模块重命名)
- [Task 8] depends on [Task 7] (OpenClaw核心功能依赖基础结构)
- [Task 9] depends on [Task 8] (IM路由集成依赖OpenClaw功能)
- [Task 10] depends on [Task 4, Task 5, Task 6] (Web UI依赖后端完成)
- [Task 11] depends on [Task 4, Task 5] (API路由依赖后端完成)
- [Task 12] depends on [Task 1-11] (测试依赖所有功能完成)
- [Task 13] depends on [Task 12] (文档更新依赖测试通过)

# Parallelizable Work

以下任务可以并行执行：
- Task 1 和 Task 2 (模块重命名可并行)
- Task 3 和 Task 5 (规划智能体和执行智能体重构可并行)
- Task 7、Task 8、Task 9 (OpenClaw集成可串行但与Task 3-6并行)
- Task 10 和 Task 11 (前端和API路由可并行)
- Task 12 的各子任务 (测试可并行编写)
