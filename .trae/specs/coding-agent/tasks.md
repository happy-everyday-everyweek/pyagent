# Tasks

## Phase 1: 编码类垂类智能体核心（参考 Claw Code）

- [ ] Task 1.1: 创建 CodingAgent 基础结构
  - [ ] SubTask 1.1.1: 创建 src/agents/coding.py 文件
  - [ ] SubTask 1.1.2: 定义 CodingAgent 类继承 BaseVerticalAgent
  - [ ] SubTask 1.1.3: 定义核心能力列表（AgentCapability）
  - [ ] SubTask 1.1.4: 实现 _setup_handlers 方法

- [ ] Task 1.2: 实现代码执行引擎
  - [ ] SubTask 1.2.1: 创建 CodeResult 数据类
  - [ ] SubTask 1.2.2: 实现 execute_code 统一入口
  - [ ] SubTask 1.2.3: 实现 _run_python Python 执行器
  - [ ] SubTask 1.2.4: 实现 _run_javascript Node.js 执行器
  - [ ] SubTask 1.2.5: 实现 _run_shell Shell 执行器
  - [ ] SubTask 1.2.6: 实现 _execute_process 进程执行核心
  - [ ] SubTask 1.2.7: 实现超时控制和输出截断

- [ ] Task 1.3: 实现代码静态分析
  - [ ] SubTask 1.3.1: 实现 Python 语法检查（ast 模块）
  - [ ] SubTask 1.3.2: 实现错误位置定位
  - [ ] SubTask 1.3.3: 实现圈复杂度计算
  - [ ] SubTask 1.3.4: 集成 ruff 进行风格检查

- [ ] Task 1.4: 实现代码审查
  - [ ] SubTask 1.4.1: 定义安全漏洞模式
  - [ ] SubTask 1.4.2: 实现 SQL 注入检测
  - [ ] SubTask 1.4.3: 实现命令注入检测
  - [ ] SubTask 1.4.4: 实现敏感信息泄露检测

- [ ] Task 1.5: 实现 Git 操作
  - [ ] SubTask 1.5.1: 实现 git_status 处理器
  - [ ] SubTask 1.5.2: 实现 git_commit 处理器
  - [ ] SubTask 1.5.3: 实现 git_branch 处理器

## Phase 2: 手机端优化（移植 OpenKiwi）

- [ ] Task 2.1: 优化屏幕操作模块
  - [ ] SubTask 2.1.1: 创建 src/mobile/accessibility/ 目录
  - [ ] SubTask 2.1.2: 实现 GestureExecutor 手势执行器
  - [ ] SubTask 2.1.3: 实现 ScreenCapture 截图捕获
  - [ ] SubTask 2.1.4: 实现 NodeCache 节点缓存（TTL 500ms）
  - [ ] SubTask 2.1.5: 实现 GestureResult 回调机制

- [ ] Task 2.2: 实现通知处理模块
  - [ ] SubTask 2.2.1: 创建 src/mobile/notification/ 目录
  - [ ] SubTask 2.2.2: 实现 NotificationListener 通知监听
  - [ ] SubTask 2.2.3: 实现 VerificationCodeExtractor 验证码提取
  - [ ] SubTask 2.2.4: 实现 NotificationClassifier 通知分类
  - [ ] SubTask 2.2.5: 实现 NotificationCache 通知缓存（200 条）

- [ ] Task 2.3: 实现自动回复模块
  - [ ] SubTask 2.3.1: 创建 src/mobile/reply/ 目录
  - [ ] SubTask 2.3.2: 实现 AutoReplyManager 自动回复管理
  - [ ] SubTask 2.3.3: 实现 ReplyWhitelist 白名单管理
  - [ ] SubTask 2.3.4: 实现 RateLimiter 速率限制（8次/小时）

- [ ] Task 2.4: 实现代码执行沙箱
  - [ ] SubTask 2.4.1: 创建 src/mobile/sandbox/ 目录
  - [ ] SubTask 2.4.2: 实现 CodeSandbox 代码沙箱
  - [ ] SubTask 2.4.3: 实现 DangerCommandDetector 危险命令检测
  - [ ] SubTask 2.4.4: 实现 SandboxConfig 沙箱配置

## Phase 3: 注册与集成

- [ ] Task 3.1: 注册编码智能体
  - [ ] SubTask 3.1.1: 在 src/agents/__init__.py 导出
  - [ ] SubTask 3.1.2: 在 src/agents/registry.py 注册
  - [ ] SubTask 3.1.3: 创建全局实例

- [ ] Task 3.2: 更新手机端模块
  - [ ] SubTask 3.2.1: 更新 src/mobile/__init__.py
  - [ ] SubTask 3.2.2: 更新 src/mobile/backend.py 集成新模块
  - [ ] SubTask 3.2.3: 更新配置文件

- [ ] Task 3.3: 编写测试
  - [ ] SubTask 3.3.1: 编写代码执行测试
  - [ ] SubTask 3.3.2: 编写静态分析测试
  - [ ] SubTask 3.3.3: 编写手机端模块测试
  - [ ] SubTask 3.3.4: 编写集成测试

# Task Dependencies

- Task 1.2 depends on Task 1.1
- Task 1.3 depends on Task 1.1
- Task 1.4 depends on Task 1.1
- Task 1.5 depends on Task 1.1
- Task 2.2 depends on Task 2.1
- Task 2.3 depends on Task 2.2
- Task 2.4 depends on Task 2.1
- Task 3.1 depends on Task 1.1, Task 1.2, Task 1.3, Task 1.4, Task 1.5
- Task 3.2 depends on Task 2.1, Task 2.2, Task 2.3, Task 2.4
- Task 3.3 depends on Task 3.1, Task 3.2
