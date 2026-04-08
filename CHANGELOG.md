# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

***

## [1.0.0] - 2026-04-07

### 新增

**后端API完善**

- 修复 `src/web/routes/verification_routes.py` 导入错误
- 修复 `src/web/routes/slash_commands.py` 路由配置
- 添加斜杠命令API端点（/api/slash/parse, /api/slash/execute, /api/slash/commands）
- 完善FastAPI应用路由配置

**前端应用测试**

- 测试Vue前端应用正常加载
- 验证前端页面内容正确

**自动化测试**

- 创建 `test_pyagent.py` 自动化测试脚本
- 测试API健康检查
- 测试任务管理API
- 测试协作模式API
- 测试前端页面加载
- 尝试测试浏览器自动化功能

### 变更

- 更新测试脚本配置，适配正确的前端端口
- 优化测试脚本错误处理

***

## [0.9.9] - 2026-04-06

### 新增

**编码类垂类智能体（移植自 Claw Code）**

- 添加 `src/agents/coding.py` 编码智能体
- 添加 `SystemPromptBuilder` 系统提示词构建器
- 添加 `ProjectContext` 项目上下文发现
- 支持多语言代码执行（Python、JavaScript、Shell）
- 支持代码静态分析（语法检查、复杂度分析）
- 支持代码审查（安全漏洞检测）
- 支持 Git 操作（状态查询、提交、分支管理）
- 支持 CLAW.md 指令文件发现和加载

**手机端优化（移植自 OpenKiwi）**

- 添加 `src/mobile/verification_code.py` 验证码提取器
  - 支持多种验证码格式识别
  - 支持有效期提取
  - 支持来源识别
- 添加 `src/mobile/notification_classifier.py` 通知分类器
  - 支持通知重要性评估
  - 支持子类别检测
  - 支持关键词和实体提取
- 添加 `src/mobile/auto_reply.py` 自动回复管理器
  - 支持白名单管理
  - 支持速率限制（8次/小时）
  - 支持回复模板
- 添加 `src/mobile/code_sandbox.py` 代码执行沙箱
  - 支持危险命令检测
  - 支持超时控制
  - 支持输出截断
- 添加 `src/mobile/gesture_executor.py` 手势执行器
  - 支持低延迟手势执行（50-300ms）
  - 支持节点缓存（TTL 500ms）
  - 支持多种手势（点击、滑动、长按、缩放等）

### 变更

- 更新 `src/agents/__init__.py` 导出 CodingAgent
- 简化 `README.md` 文档（从1377行精简到182行）
- 简化 `AGENTS.md` 文档（从1333行精简到238行）
- 优化文档结构，移除冗余内容，通过链接指向详细文档
- 更新 `src/mobile/__init__.py` 导出新模块
- 更新 `AGENTS.md` 添加"发布前检查流程"章节
  - 添加多端兼容性检查流程
  - 添加自动测试运行规范
  - 添加代码提交到develop分支的规范
  - 添加构建测试流程
  - 添加完整发布流程
  - 添加快速检查脚本示例

***

## [0.9.8] - 2026-04-05

### 新增

**统一后端架构**

- 添加 `src/core/` 统一后端核心模块
- 添加 `src/core/platform/` 平台适配层
- 支持 Web 端和移动端共用同一后端代码
- 支持平台检测和能力识别

**平台适配系统**

- 添加 `PlatformDetector` 平台检测器
- 添加 `PlatformAdapter` 平台适配器
- 支持 Web、Android、iOS、Desktop 四种平台
- 支持工具类别过滤（根据平台能力）

**Android 原生应用重构**

- 添加 `ProotManager.kt` proot 环境管理
- 添加 `PythonRuntime.kt` Python 运行时管理
- 添加 `WebViewManager.kt` WebView 管理
- 添加 `BackendService.kt` 后台服务
- 添加 `BootReceiver.kt` 开机启动接收器
- 添加原生 UI 界面（初始化、聊天、任务、设置）
- 支持 WebView 加载 Web UI（多端统一）
- 支持封装完整 Linux 环境和 Python 运行时

**构建系统增强**

- 更新 `build.ps1` 支持 `-BundlePython` 参数
- 添加 `download-linux.ps1` Linux 环境下载脚本
- 支持打包 Alpine Linux rootfs 到 APK
- 支持多架构构建（arm64-v8a, armeabi-v7a, x86_64）

### 变更

- 重构 `src/web/app.py` 使用统一核心
- 重构 `src/mobile/backend.py` 使用统一核心
- 更新 `android/app/build.gradle.kts` 添加新依赖
- 更新 `AndroidManifest.xml` 添加必要权限

### 移除

- 移除 Web 后端中的重复代码
- 移除移动端后端中的独立实现
