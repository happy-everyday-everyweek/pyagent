# Coding Agent 编码类垂类智能体 + 手机端优化 Spec

## Why
1. 构建一个专业的编码类垂类智能体，参考 Claw Code (OpenClaw) 的设计理念，为 PyAgent 提供强大的代码编写、分析、执行和调试能力。
2. 优化手机端模块，参考 OpenKiwi 的低延迟屏幕操作、通知跟踪、自动回复等功能。

## What Changes
### 编码类垂类智能体（参考 Claw Code/OpenClaw）
- 创建 CodingAgent 垂类智能体，继承 BaseVerticalAgent
- 实现多语言代码执行引擎（Python、JavaScript、Shell、PowerShell）
- 实现代码静态分析能力（语法检查、复杂度分析、代码风格）
- 实现代码审查能力（安全漏洞检测、最佳实践建议）
- 实现 Git 操作能力（状态查询、提交、分支管理）
- 实现依赖管理能力（pip、npm、cargo 等）
- 实现测试执行能力（pytest、unittest、jest 等）

### 手机端优化（参考 OpenKiwi）
- 实现低延迟屏幕操作（AccessibilityService + GestureDescription）
- 实现通知跟踪和智能分类（NotificationListenerService）
- 实现验证码自动提取和剪贴板复制
- 实现自动回复功能（RemoteInput）
- 实现代码执行沙箱（参考 CodeSandbox）

## Impact
- Affected specs: 新增编码类垂类智能体模块 + 手机端优化
- Affected code:
  - `src/agents/coding.py`（新增）
  - `src/mobile/`（优化）
- 参考:
  - 编码智能体: `claw-code-main/src/tools.py`, `claw-code-main/src/query_engine.py`
  - 手机端: `OpenKiwi-master/app/src/main/java/com/orizon/openkiwi/core/`

## ADDED Requirements

### Requirement: 多语言代码执行（参考 Claw Code）
智能体应支持多种编程语言的代码执行。

#### Scenario: Python 代码执行
- **WHEN** 用户请求执行 Python 代码
- **THEN** 系统创建临时文件执行代码
- **AND** 捕获 stdout、stderr 和返回码
- **AND** 支持超时控制（默认 30 秒，最大 120 秒）
- **AND** 支持输出截断（最大 100KB）

#### Scenario: JavaScript/Node.js 代码执行
- **WHEN** 用户请求执行 JavaScript 代码
- **THEN** 系统使用 Node.js 执行代码
- **AND** 捕获执行结果和错误信息
- **AND** 处理 Node.js 未安装的情况

#### Scenario: Shell/PowerShell 命令执行
- **WHEN** 用户请求执行 Shell 命令
- **THEN** 根据操作系统选择合适的 Shell
- **AND** Windows 使用 PowerShell 或 cmd
- **AND** Linux/macOS 使用 bash 或 sh
- **AND** 支持命令超时和输出捕获

### Requirement: 代码静态分析
智能体应提供代码静态分析能力。

#### Scenario: Python 代码语法检查
- **WHEN** 用户请求检查 Python 代码
- **THEN** 使用 ast 模块进行语法分析
- **AND** 返回语法错误和警告
- **AND** 提供错误位置信息（行号、列号）

#### Scenario: 代码复杂度分析
- **WHEN** 用户请求分析代码复杂度
- **THEN** 计算圈复杂度（Cyclomatic Complexity）
- **AND** 识别高复杂度函数
- **AND** 提供重构建议

### Requirement: 代码审查
智能体应提供代码审查能力。

#### Scenario: 安全漏洞检测
- **WHEN** 用户请求审查代码安全性
- **THEN** 检测常见安全漏洞模式
- **AND** 识别 SQL 注入、XSS、命令注入等风险
- **AND** 检测敏感信息泄露（API Key、密码等）

### Requirement: Git 操作
智能体应支持 Git 版本控制操作。

#### Scenario: Git 状态查询
- **WHEN** 用户请求查询 Git 状态
- **THEN** 返回当前分支、暂存区状态
- **AND** 返回未跟踪文件列表
- **AND** 返回修改文件列表

### Requirement: 低延迟屏幕操作（移植 OpenKiwi）
手机端应支持低延迟的屏幕操作。

#### Scenario: 手势执行
- **WHEN** Agent 需要执行屏幕操作
- **THEN** 使用 AccessibilityService 的 GestureDescription API
- **AND** 支持点击、滑动、长按、双击、缩放等手势
- **AND** 支持异步执行和结果回调
- **AND** 执行延迟控制在 50-300ms

#### Scenario: 截图捕获
- **WHEN** Agent 需要获取屏幕内容
- **THEN** 使用 AccessibilityService 的 takeScreenshot API
- **AND** 支持 HardwareBuffer 到 Bitmap 转换
- **AND** 支持缩放和质量调整

#### Scenario: 节点缓存
- **WHEN** Agent 需要访问界面节点
- **THEN** 使用带 TTL 的节点缓存（500ms）
- **AND** 避免重复遍历节点树
- **AND** 支持缓存失效

### Requirement: 通知跟踪和智能分类（移植 OpenKiwi）
手机端应支持通知的智能处理。

#### Scenario: 通知监听
- **WHEN** 系统收到新通知
- **THEN** 通过 NotificationListenerService 捕获
- **AND** 提取标题、内容、包名等信息
- **AND** 缓存最近 200 条通知

#### Scenario: 验证码提取
- **WHEN** 通知包含验证码
- **THEN** 使用正则表达式提取验证码
- **AND** 自动复制到剪贴板
- **AND** 通过 StateFlow 通知订阅者

#### Scenario: 通知分类
- **WHEN** 收到新通知
- **THEN** 自动分类（验证码、快递、日程、金融、来电、一般）
- **AND** 使用 LLM 分析重要性
- **AND** 自动提取日程信息

### Requirement: 自动回复（移植 OpenKiwi）
手机端应支持通知的自动回复。

#### Scenario: 内联回复
- **WHEN** 收到支持 RemoteInput 的通知
- **THEN** 检查是否在允许列表中
- **AND** 使用 Notification.Action 发送回复
- **AND** 支持速率限制（每小时最多 8 次）

#### Scenario: 白名单管理
- **WHEN** 配置自动回复
- **THEN** 支持配置允许的应用包名
- **AND** 默认支持微信、QQ、Telegram 等
- **AND** 支持自定义回复模板

### Requirement: 代码执行沙箱（移植 OpenKiwi）
手机端应支持安全的代码执行。

#### Scenario: Shell 执行
- **WHEN** 执行 Shell 命令
- **THEN** 在沙箱目录中执行
- **AND** 检测危险命令（rm -rf / 等）
- **AND** 支持超时控制

#### Scenario: Python 执行
- **WHEN** 执行 Python 代码
- **THEN** 使用本地 Python 执行
- **AND** 支持输出截断

### Requirement: 沙箱安全
智能体应确保代码执行的安全性。

#### Scenario: 资源限制
- **WHEN** 执行用户代码
- **THEN** 限制执行时间
- **AND** 限制内存使用
- **AND** 限制输出大小

#### Scenario: 危险操作检测
- **WHEN** 检测到危险操作
- **THEN** 识别文件系统危险操作
- **AND** 识别网络危险操作
- **AND** 要求用户确认或拒绝执行
