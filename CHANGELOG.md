# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

***

## \[0.9.7] - 2026-04-05

### 新增

**知识库系统** (参考 deer-flow LPMM)

- 添加 `src/knowledge/` 知识库模块
- 支持文档索引和倒排索引搜索
- 支持 TF-IDF 和 BM25 相关性计算
- 支持知识库管理和多租户隔离

**工作流引擎** (参考 twenty)

- 添加 `src/workflow/` 工作流引擎模块
- 支持触发器系统（定时、事件、Webhook、条件）
- 支持动作系统（HTTP请求、脚本执行、通知发送）
- 支持工作流版本管理和执行历史

**Ubuntu环境管理**

- 添加 `src/ubuntu/` Ubuntu/WSL环境管理模块
- 支持 Ubuntu/WSL 环境检测和配置
- 支持包管理器操作（apt、snap）
- 支持 Systemd 服务管理

**本地模型支持** (参考 dexter)

- 添加 `src/local_model/` 本地模型后端模块
- 支持 llama.cpp 后端（GGUF格式模型）
- 支持 MNN 后端（移动端优化）
- 支持模型下载和自动配置

**角色卡系统** (参考 character-card)

- 添加 `src/persona/character_card.py` 角色卡模块
- 支持角色卡定义（名称、描述、性格、问候语）
- 支持 PNG 元数据嵌入和 QR 码分享
- 支持角色卡导入导出

**研究任务分解与验证** (参考 open-deep-research)

- 添加 `src/research/` 研究规划器模块
- 支持研究任务自动分解
- 支持子任务验证和结果聚合
- 支持多轮迭代优化

**调试系统**

- 添加 `src/debug/` 调试便签模块
- 支持工具调用跟踪和记录
- 支持调试会话管理和导出
- 支持执行日志分析

**成本追踪系统** (参考 litellm)

- 添加 `src/llm/gateway/cost_tracker.py` 成本追踪模块
- 支持多租户成本统计
- 支持按模型、时间范围统计
- 支持预算限制和告警

**虚拟密钥管理** (参考 litellm)

- 添加 `src/llm/gateway/key_manager.py` 密钥管理模块
- 支持虚拟密钥生成和管理
- 支持速率限制和配额管理
- 支持密钥权限控制

**视图系统**

- 添加 `src/views/` 视图系统模块
- 支持看板视图、表格视图
- 支持过滤器和排序
- 支持视图配置保存

**浏览器DOM智能解析**

- 添加 `src/browser/dom_parser.py` DOM解析模块
- 支持智能元素定位和提取
- 支持可交互元素识别
- 支持LLM友好的DOM文本输出

**浏览器技能系统**

- 添加 `src/browser/skills.py` 技能模块
- 支持可复用的浏览器操作模式
- 支持技能参数化和变量替换
- 支持技能导入导出

**视频编辑器增强**

- 扩展 `src/video/editor.py` 多轨道时间轴
- 支持视频导出配置（分辨率、码率、格式）
- 支持渲染进度回调

**Azure语音提供商**

- 添加 `src/voice/azure_provider.py` Azure语音模块
- 支持Azure Speech Services集成
- 支持流式语音识别和合成
- 支持多语言语音

**PDF表格提取增强**

- 添加 `src/pdf/table_extractor.py` 表格提取模块
- 支持表格结构识别
- 支持OCR表格识别
- 支持表格导出为Excel

**文档转换器**

- 添加 `src/document/converter.py` 文档转换模块
- 支持DOCX/PDF/HTML互转
- 支持Markdown转换
- 支持文档版本管理

**自我进化机制**

- 添加 `src/evolution/` 自我进化模块
- 支持性能监控和分析
- 支持自动优化建议
- 支持学习反馈循环

### 变更

- 更新 `pyproject.toml` 版本号至 0.9.7
- 添加新模块依赖（azure-cognitiveservices-speech、camelot-py、opencv-python）

***

## \[0.9.6] - 2026-04-05

### 新增

**测试系统全面优化**

- 添加 `tests/test_agents.py` 智能体系统测试（30+ 测试用例）
- 添加 `tests/test_human_tasks.py` 人工任务系统测试（40+ 测试用例）
- 添加 `tests/test_email.py` 邮件客户端测试（15+ 测试用例）
- 添加 `tests/test_llm_gateway.py` LLM模型网关测试（20+ 测试用例）
- 添加 `tests/test_tools.py` 统一工具接口测试（35+ 测试用例）
- 添加 `tests/test_mcp.py` MCP协议测试（25+ 测试用例）
- 添加 `tests/test_security.py` 安全策略系统测试（25+ 测试用例）
- 添加 `tests/test_skills.py` 技能系统测试（20+ 测试用例）
- 添加 `tests/test_storage.py` 分布式存储测试（25+ 测试用例）
- 添加 `tests/test_desktop.py` 桌面自动化测试（20+ 测试用例）
- 添加 `tests/test_person.py` 用户信息系统测试（25+ 测试用例）

**代码风格测试规则扩展**

- 添加 A (flake8-builtins) 规则
- 添加 COM (flake8-commas) 规则
- 添加 EM (flake8-errmsg) 规则
- 添加 FA (flake8-future-annotations) 规则
- 添加 SLF (flake8-self) 规则
- 添加 SLOT (flake8-slots) 规则
- 添加 FLY (flynt) 规则
- 添加 PERF (perflint) 规则
- 添加 FURB (refurb) 规则

### 变更

- 更新 `check.ps1` 自动测试工具 v2.0
  - 添加自动检查和安装开发依赖功能
  - 添加并行测试支持 (-Parallel)
  - 添加覆盖率阈值支持 (-FailUnder)
  - 添加复杂度检查
  - 添加更详细的输出和统计信息
- 更新 `pyproject.toml` 版本号至 0.9.6

***

## \[0.9.5] - 2026-04-05

### 新增

**工程化基础设施**

- 添加 GitHub Actions CI/CD 工作流（ci.yml、publish.yml、docker.yml、release.yml、security.yml）
- 添加 GitHub 模板文件（bug\_report.yml、feature\_request.yml、PR 模板）
- 添加 CONTRIBUTING.md 贡献指南
- 添加 SECURITY.md 安全策略
- 添加 `src/py.typed` 类型标记文件
- 添加 `.pre-commit-config.yaml` 代码质量钩子
- 添加 Dockerfile 和 docker-compose.yml 容器化支持

**中间件链系统** (参考 deer-flow)

- 添加 `src/execution/middlewares/` 中间件架构
- 实现 8 个核心中间件：ThreadData、Uploads、Summarization、TodoList、Title、Memory、ViewImage、Clarification
- 支持同步和异步执行

**浏览器录制回放** (参考 browser-use)

- 添加 `src/browser/recorder.py` 录制回放系统
- 支持多种操作类型（导航、点击、输入、滚动等）
- 支持变量替换和播放速度控制

**MCP 网关** (参考 litellm)

- 添加 `src/llm/gateway/mcp_gateway.py` 统一 MCP 服务器管理
- 支持 HTTP、SSE、stdio 传输
- 支持 API Key、OAuth2、Bearer 认证

**LLM 提供商扩展**

- 添加 DeepSeek 适配器 (`src/llm/adapters/deepseek_adapter.py`)
- 添加智谱 AI 适配器 (`src/llm/adapters/zhipu_adapter.py`)
- 添加 Ollama 本地模型适配器 (`src/llm/adapters/ollama_adapter.py`)

### 变更

- 更新 `pyproject.toml` 版本号至 0.9.5
- 扩展可选依赖组（browser、voice、pdf、all）
- 添加项目 classifiers 和 URL 配置

***

## \[0.9.4] - 2026-04-05

### 修复

- 修复地图工具模块导入错误，添加 `GeoPoint` 和 `GeoBounds` 类的导出
- 修复 DOCX 编辑器测试，正确使用解压后的目录路径初始化 `Document` 类
- 修复 `DocxCreator` 缺少 `settings.xml` 文件的问题，添加完整的设置文件生成
- 添加缺失的 `people.xml` 模板文件用于批注功能

***

## \[0.9.3] - 2026-04-05

### 文档更新

根据新的文档规范 `docs/standards.md`，全面检查和确认项目文档符合规范要求。

**README.md** - 符合规范

- 包含项目名称和徽章
- 包含项目简介和功能特性
- 包含快速开始和环境要求
- 包含安装步骤和基本用法
- 包含配置说明和文档链接
- 包含贡献指南和许可证

**CHANGELOG.md** - 符合规范

- 格式基于 Keep a Changelog
- 遵循语义化版本
- 包含版本号和日期
- 包含变更类型和变更描述

**docs/architecture.md** - 符合规范

- 包含概述和系统架构图
- 包含模块说明和数据流图
- 包含状态管理和通信机制
- 包含扩展机制和安全设计
- 包含性能优化和部署架构

**docs/api.md** - 符合规范

- 包含接口描述和请求方法/路径
- 包含请求参数和请求示例
- 包含响应格式和响应示例
- 包含状态码说明和调用示例
- 包含数据模型和错误处理

**docs/configuration.md** - 符合规范

- 包含配置文件列表和环境变量
- 包含配置项说明和默认值
- 包含配置示例和配置验证

**docs/deployment.md** - 符合规范

- 包含环境要求和安装步骤
- 包含配置说明和启动方式
- 包含健康检查和常见问题
- 包含 Docker 和 Systemd 部署模板

**docs/development.md** - 符合规范

- 包含开发环境搭建和代码规范
- 包含模块开发指南和测试说明
- 包含调试技巧和提交规范

**docs/testing.md** - 符合规范

- 包含测试概述和测试结构
- 包含测试文件说明和运行方法
- 包含测试覆盖范围和编写指南

**docs/frontend.md** - 符合规范

- 包含概述和技术栈
- 包含项目结构和核心特性
- 包含开发指南和组件开发
- 包含 API 集成和状态管理

**docs/modules/\*.md** - 模块文档齐全

- 包含 28 个模块文档
- 涵盖所有核心模块和扩展模块

***

## \[0.9.2] - 2026-04-05

### 新增功能

#### 版本号更新规范

扩展 `docs/standards.md` 版本号规范章节，新增详细的版本号更新说明：

**版本号更新时机表格**

- MAJOR: 不兼容的 API 变更（删除公开 API、修改函数签名、更改配置格式、数据库迁移）
- MINOR: 向后兼容的功能新增（新增模块、新增 API 端点、新增配置选项、功能增强）
- PATCH: 向后兼容的问题修复（Bug 修复、性能优化、文档更新、依赖更新）

**MAJOR 版本更新详细说明**

- 必须更新 MAJOR 版本的四种情况
- 每种情况的详细说明
- 更新示例

**MINOR 版本更新详细说明**

- 必须更新 MINOR 版本的三种情况
- 每种情况的详细说明
- 更新示例

**PATCH 版本更新详细说明**

- 必须更新 PATCH 版本的四种情况
- 每种情况的详细说明
- 更新示例

**版本号更新流程**

- 确定版本类型
- 更新版本号（pyproject.toml、__init__.py、package.json）
- 更新 CHANGELOG
- 创建 Git 标签

**预发布版本规范**

- Alpha: 内部测试版本
- Beta: 公开测试版本
- RC: 发布候选版本
- 版本演进示例

**版本兼容性说明**

- CHANGELOG 中必须说明版本兼容性
- 兼容性表格格式

**AGENTS.md 更新**

- 扩展版本号规范概要部分
- 添加版本号更新时机表格
- 添加各版本类型更新条件
- 添加预发布版本说明

***

## \[0.9.1] - 2026-04-05

### 新增功能

#### 文档规范细化

扩展 `docs/standards.md` 文档规范章节，新增详细的文档类型规范：

**README 文档规范**

- 必须包含的内容：项目名称和徽章、项目简介、功能特性、快速开始、环境要求、安装步骤、基本用法、文档链接、许可证
- 提供完整的 README 模板

**CHANGELOG 文档规范**

- 必须包含的内容：版本号和日期、变更类型、变更描述、兼容性说明、升级指南
- 变更类型说明：新增/变更/弃用/移除/修复/安全
- 提供完整的 CHANGELOG 模板

**架构文档规范**

- 必须包含的内容：概述、系统架构图、模块说明、数据流图、技术栈、设计决策
- 提供架构文档模板和架构图示例

**API 文档规范**

- 必须包含的内容：接口描述、请求方法/路径、请求参数、请求示例、响应格式、响应示例、状态码说明、调用示例
- 提供 REST API 文档模板

**模块文档规范**

- 必须包含的内容：模块概述、快速开始、安装说明、API 参考、配置说明、使用示例、注意事项、相关文档
- 提供模块文档模板

**配置文档规范**

- 必须包含的内容：配置文件列表、环境变量、配置项说明、默认值、配置示例
- 提供配置文档模板

**部署文档规范**

- 必须包含的内容：环境要求、安装步骤、配置说明、启动方式、健康检查、常见问题
- 提供 Systemd 和 Docker 部署模板

**故障排查文档规范**

- 必须包含的内容：常见问题、错误代码、排查步骤、日志分析、联系支持
- 提供故障排查文档模板

**AGENTS.md 更新**

- 扩展文档规范概要部分
- 添加文档类型表格
- 添加各类文档必须包含的内容说明

***

## \[0.9.0] - 2026-04-05

### 新增功能

#### 视频编辑器全面优化

继承 Cutia 项目架构优势，实现完整的视频编辑器功能，支持移动端、Web UI 端和桌面端三个平台。

**命令系统** (`src/video/commands/`)

- `Command` 基类: execute/undo/redo 方法
- `CommandManager`: 历史栈管理，支持撤销/重做
- `BatchCommand`: 批量命令组合
- `AddTrackCommand/RemoveTrackCommand`: 轨道命令
- `InsertElementCommand/DeleteElementsCommand`: 元素命令
- `AddTransitionCommand/RemoveTransitionCommand`: 转场命令
- `DetachAudioCommand`: 音频分离命令

**类型定义扩展** (`src/video/types.py`)

- `Transform`: 变换属性（缩放、位置、旋转、翻转）
- `TransitionType`: 12种转场类型枚举
- `TrackTransition`: 轨道转场
- `StickerElement`: 贴纸元素
- 扩展 `TimelineElement`: playbackRate, reversed 属性
- 扩展 `Track`: transitions 属性

**编辑器核心重构** (`src/video/editor_core.py`)

- 集成 `CommandManager` 命令管理器
- 新增 `SelectionManager` 选择管理器
- 新增 `SaveManager` 自动保存管理器

**转场效果系统** (`src/video/transitions/`)

- `Transition` 基类
- `FadeTransition`: 淡入淡出
- `DissolveTransition`: 溶解效果
- `WipeTransition`: 四方向擦除
- `SlideTransition`: 四方向滑动
- `ZoomInTransition/ZoomOutTransition`: 缩放转场
- 转场工具函数: buildTrackTransition, areElementsAdjacent 等

**平台适配层** (`src/video/platform/`)

- `PlatformAdapter` 基类和 `PlatformCapabilities` 能力定义
- `PlatformDetector`: 平台检测器
- `MobileAdapter`: 移动端适配（触摸手势、性能优化、离线存储）
- `WebAdapter`: Web端适配（浏览器能力检测、IndexedDB）
- `DesktopAdapter`: 桌面端适配（FFmpeg、硬件编码）

**渲染系统** (`src/video/renderer/`)

- `BaseRenderer` 基类和 `RenderConfig` 配置
- `CanvasRenderer`: Canvas渲染器（Web/移动端）
- `FFmpegRenderer`: FFmpeg渲染器（桌面端）
- `RenderQueue`: 渲染任务队列

**AI 功能集成** (`src/video/ai/`)

- `SmartEditService`: 智能剪辑（精彩片段识别、场景检测）
- `SubtitleService`: 字幕生成（语音识别、多语言翻译）
- `EffectRecommendationService`: 特效推荐（转场、滤镜、音乐推荐）

**REST API 扩展** (`src/web/routes/video_routes.py`)

- POST `/api/video/{project_id}/undo` - 撤销
- POST `/api/video/{project_id}/redo` - 重做
- POST `/api/video/{project_id}/transition` - 添加转场
- DELETE `/api/video/{project_id}/transition/{id}` - 删除转场
- POST `/api/video/{project_id}/detach-audio` - 音频分离
- POST `/api/video/ai/smart-edit` - 智能剪辑
- POST `/api/video/ai/subtitle` - 字幕生成
- POST `/api/video/ai/effects` - 特效推荐
- POST `/api/video/{project_id}/render` - 开始渲染
- GET `/api/video/render/{job_id}/status` - 渲染状态

### 平台差异

| 功能   | 移动端    | Web端          | 桌面端             |
| ---- | ------ | ------------- | --------------- |
| 渲染引擎 | Canvas | Canvas        | FFmpeg          |
| 硬件加速 | 有限     | WebCodecs     | NVENC/QuickSync |
| 存储   | SQLite | IndexedDB     | 文件系统            |
| 触摸手势 | 支持     | 支持            | 不支持             |
| 离线编辑 | 支持     | ServiceWorker | 原生支持            |

***

## \[0.8.17] - 2026-04-05

### 新增功能

#### 项目规范文档

新增完整的项目规范文档 `docs/standards.md`，包含：

**代码规范**

- Python 代码规范（类型注解、命名规范、导入规范、类定义规范、异步函数规范、异常处理规范、工具类规范）
- TypeScript/Vue 代码规范（命名规范、组件规范、类型规范）
- Kotlin 代码规范（命名规范、类定义规范）

**文档规范**

- Markdown 文档规范（文档结构、标题层级、代码块规范、表格规范、链接规范）
- API 文档规范（REST API 文档格式）
- 模块文档规范（模块文档模板）

**格式规范**

- 文件命名规范（Python 文件、前端文件、配置文件）
- 目录结构规范（源代码目录、文档目录、配置目录）
- 配置文件规范（YAML、JSON、环境变量）

**提交规范**

- Git 提交规范（提交消息格式、类型说明）
- 分支管理规范（分支命名、分支流程）
- 版本号规范（语义化版本）

**测试规范**

- 单元测试规范（测试文件组织、测试命名规范）
- 集成测试规范
- 测试覆盖要求

**安全规范**

- 敏感信息处理（禁止硬编码、日志脱敏、配置文件安全）
- 输入验证规范（Pydantic 验证、SQL 注入防护）
- 权限控制规范

**日志规范**

- 日志级别规范
- 日志格式规范
- 日志存储规范

**注释规范**

- Python 注释规范（模块注释、类注释、方法注释）
- 前端注释规范（组件注释、函数注释）
- 配置注释规范

**AGENTS.md 更新**

- 在 AGENTS.md 中添加了"项目规范"章节
- 引用了详细规范文档

***

## \[0.8.16] - 2026-04-05

### 新增功能

#### 视频编辑器桌面端适配器

**DesktopAdapter** (`src/video/platform/desktop.py`)

- 继承 PlatformAdapter 基类
- 方法: get\_platform\_name() -> "desktop"
- 方法: detect\_capabilities() -> 返回桌面端能力（硬件编码、GPU渲染、最大分辨率等）
- 方法: get\_storage() -> 返回本地文件系统存储
- 方法: get\_renderer\_config() -> 返回桌面端渲染配置
- 方法: get\_hardware\_encoder() -> 返回硬件编码器实例
- 方法: get\_renderer() -> 返回 FFmpeg 渲染器实例

**FileSystemAccess** (`src/video/platform/desktop.py`)

- 属性: base\_path - 基础路径
- 方法: read\_file(path) -> bytes - 读取文件
- 方法: write\_file(path, data) - 写入文件
- 方法: delete\_file(path) - 删除文件
- 方法: list\_files(directory) -> list - 列出目录文件
- 方法: file\_exists(path) -> bool - 检查文件是否存在
- 方法: get\_file\_info(path) -> dict - 获取文件信息
- 方法: watch\_directory(path, callback) - 监听目录变化

**FFmpegRenderer** (`src/video/platform/desktop.py`)

- 属性: ffmpeg\_path - FFmpeg 路径
- 方法: detect\_ffmpeg() -> bool - 检测 FFmpeg 是否可用
- 方法: get\_ffmpeg\_version() -> str - 获取 FFmpeg 版本
- 方法: render(input\_files, output\_path, config) - 执行渲染
- 方法: get\_render\_progress() -> float - 获取渲染进度
- 方法: cancel\_render() - 取消渲染

**HardwareEncoder** (`src/video/platform/desktop.py`)

- 属性: available\_encoders - 可用编码器列表
- 方法: detect\_encoders() - 检测可用的硬件编码器
- 方法: has\_nvenc() -> bool - 检测 NVIDIA NVENC 支持
- 方法: has\_qsv() -> bool - 检测 Intel Quick Sync 支持
- 方法: has\_videotoolbox() -> bool - 检测 macOS VideoToolbox 支持
- 方法: get\_recommended\_encoder() -> str - 获取推荐编码器
- 方法: get\_encoder\_options(encoder) -> dict - 获取编码器选项

#### 视频编辑器平台适配器基础架构

参考 Cutia 项目，实现视频编辑器的平台适配器基础架构：

**平台适配器基类** (`src/video/platform/base.py`)

- 新增 PlatformCapabilities 数据类
  - 属性: can\_hardware\_encode - 是否支持硬件编码
  - 属性: can\_gpu\_render - 是否支持GPU渲染
  - 属性: max\_preview\_fps - 最大预览帧率
  - 属性: max\_resolution - 最大分辨率
  - 属性: supports\_touch - 是否支持触摸
  - 属性: supports\_offline - 是否支持离线
  - 属性: storage\_type - 存储类型（file/indexeddb/sqlite）
  - 属性: renderer\_type - 渲染器类型（canvas/opengl/ffmpeg）
- 新增 PlatformAdapter 抽象基类
  - 抽象方法: get\_platform\_name() - 返回平台名称
  - 抽象方法: detect\_capabilities() - 检测平台能力
  - 抽象方法: get\_storage() - 返回存储配置
  - 抽象方法: get\_renderer\_config() - 返回渲染器配置

**平台检测器** (`src/video/platform/detector.py`)

- 新增 PlatformDetector 类
  - 静态方法: detect() - 检测平台类型（mobile/web/desktop）
  - 静态方法: is\_mobile() - 判断是否为移动平台
  - 静态方法: is\_web() - 判断是否为Web平台
  - 静态方法: is\_desktop() - 判断是否为桌面平台
  - 静态方法: get\_os() - 获取操作系统类型（windows/macos/linux/android/ios/web）
  - 静态方法: get\_device\_info() - 获取设备详细信息

**工厂函数** (`src/video/platform/__init__.py`)

- 新增 DefaultAdapter - 默认平台适配器实现
  - 根据平台类型自动配置能力参数
  - 桌面平台: 支持硬件编码、GPU渲染、4K分辨率、60fps预览
  - 移动平台: 支持硬件编码、GPU渲染、1080p分辨率、30fps预览
  - Web平台: 支持GPU渲染、1080p分辨率、30fps预览、IndexedDB存储
- 新增 get\_platform\_adapter() - 工厂函数
  - 单例模式管理适配器实例
  - 根据当前环境返回合适的适配器

#### 视频编辑器转场效果渲染系统

参考 Cutia 项目，实现视频编辑器的转场效果渲染系统：

**转场基类** (`src/video/transitions/base.py`)

- 新增 Transition 抽象基类
  - 属性: duration - 转场持续时间
  - 抽象方法: apply(frame1, frame2, progress) - 应用转场效果
  - 抽象方法: get\_type() - 返回转场类型
  - 辅助方法: validate\_frames() - 验证帧数据
  - 辅助方法: clamp\_progress() - 限制进度值范围

**淡入淡出效果** (`src/video/transitions/fade.py`)

- 新增 FadeTransition - 标准淡入淡出转场
  - 公式: frame1 \* (1-progress) + frame2 \* progress
- 新增 DissolveTransition - 溶解效果转场
  - 带噪声颗粒的溶解效果
  - 支持自定义颗粒强度

**擦除效果** (`src/video/transitions/wipe.py`)

- 新增 WipeTransition - 擦除转场
  - 支持四个方向: left, right, up, down
  - 从一个方向逐渐显示 frame2

**滑动效果** (`src/video/transitions/slide.py`)

- 新增 SlideTransition - 滑动转场
  - 支持四个方向: left, right, up, down
  - frame1 滑出，frame2 滑入

**缩放效果** (`src/video/transitions/zoom.py`)

- 新增 ZoomInTransition - 放大转场
  - frame1 放大消失，frame2 正常出现
  - 支持自定义最大缩放比例
- 新增 ZoomOutTransition - 缩小转场
  - frame1 缩小消失，frame2 正常出现
  - 支持自定义最大缩放比例

**工厂函数** (`src/video/transitions/__init__.py`)

- 新增 TRANSITION\_REGISTRY - 转场类型注册表
- 新增 get\_transition(transition\_type, duration) - 工厂函数
  - 支持所有 12 种转场类型

***

## \[0.8.15] - 2026-04-05

### 新增功能

#### 视频编辑器轨道命令

参考 Cutia 项目，实现视频编辑器的轨道命令系统：

**轨道命令** (`src/video/commands/track_commands.py`)

- 新增 AddTrackCommand - 添加轨道到项目
  - 参数: project\_id, track\_type, index=None, name=None
  - 方法: execute() - 添加轨道到项目，支持指定插入位置
  - 方法: undo() - 移除添加的轨道
  - 方法: get\_track\_id() - 返回创建的轨道ID
- 新增 RemoveTrackCommand - 移除轨道
  - 参数: project\_id, track\_id
  - 方法: execute() - 移除轨道，保存轨道数据用于恢复（主轨道不可移除）
  - 方法: undo() - 恢复轨道到原位置
- 新增 ReorderTracksCommand - 重排轨道顺序
  - 参数: project\_id, track\_ids (新的轨道顺序)
  - 方法: execute() - 按新顺序重排轨道
  - 方法: undo() - 恢复原顺序
- 新增 ToggleTrackMuteCommand - 切换轨道静音状态
  - 参数: project\_id, track\_id
  - 方法: execute() - 切换静音状态（仅视频和音频轨道）
  - 方法: undo() - 恢复原状态
- 新增 ToggleTrackVisibilityCommand - 切换轨道可见性
  - 参数: project\_id, track\_id
  - 方法: execute() - 切换可见性（主轨道不可隐藏）
  - 方法: undo() - 恢复原状态

#### 视频编辑器元素命令

参考 Cutia 项目，实现视频编辑器的元素命令系统：

**元素命令** (`src/video/commands/element_commands.py`)

- 新增 InsertElementCommand - 插入元素到轨道
  - 参数: project\_id, element\_data, track\_id, start\_time
  - 方法: execute() - 创建并插入元素到指定轨道
  - 方法: undo() - 移除插入的元素
  - 方法: get\_element\_id() - 返回创建的元素ID
- 新增 DeleteElementsCommand - 删除多个元素
  - 参数: project\_id, elements (list\[{track\_id, element\_id}])
  - 方法: execute() - 删除元素并保存数据用于恢复
  - 方法: undo() - 恢复所有删除的元素
- 新增 MoveElementCommand - 移动元素到新位置
  - 参数: project\_id, source\_track\_id, target\_track\_id, element\_id, new\_start\_time
  - 方法: execute() - 移动元素（支持同轨道和跨轨道）
  - 方法: undo() - 恢复原位置
- 新增 SplitElementsCommand - 在指定时间分割元素
  - 参数: project\_id, elements, split\_time, retain\_side="both"
  - 方法: execute() - 分割元素（支持 left/right/both 三种模式）
  - 方法: undo() - 合并分割的元素
  - 方法: get\_right\_side\_elements() - 返回分割后右侧元素
- 新增 UpdateElementCommand - 更新元素属性
  - 参数: project\_id, track\_id, element\_id, updates
  - 方法: execute() - 更新元素属性
  - 方法: undo() - 恢复原属性
- 新增 DuplicateElementsCommand - 复制元素
  - 参数: project\_id, elements
  - 方法: execute() - 复制元素到同一轨道
  - 方法: undo() - 删除复制的元素
  - 方法: get\_duplicated\_elements() - 返回复制的元素
- 新增 DetachAudioCommand - 从视频元素分离音频
  - 参数: project\_id, elements
  - 方法: execute() - 创建独立音频轨道，静音原视频
  - 方法: undo() - 合并音频回视频

***

## \[0.8.14] - 2026-04-05

### 新增功能

#### 视频编辑器转场命令

参考 Cutia 项目，实现视频编辑器的转场命令系统：

**转场命令** (`src/video/commands/transition_commands.py`)

- 新增 AddTransitionCommand - 在两个相邻元素之间添加转场
  - 参数: project\_id, track\_id, from\_element\_id, to\_element\_id, transition\_type, duration
  - 方法: execute() - 添加转场，验证元素相邻性和媒体类型
  - 方法: undo() - 移除转场或恢复原有转场
  - 方法: get\_transition\_id() - 获取创建的转场ID
- 新增 RemoveTransitionCommand - 移除转场
  - 参数: project\_id, track\_id, transition\_id
  - 方法: execute() - 移除转场并保存数据用于恢复
  - 方法: undo() - 恢复转场
- 新增 UpdateTransitionCommand - 更新转场属性
  - 参数: project\_id, track\_id, transition\_id, updates
  - 方法: execute() - 更新转场属性（类型、持续时间等）
  - 方法: undo() - 恢复原属性

**转场验证逻辑**

- 验证元素必须是视频或图片类型
- 验证元素必须相邻（时间间隔小于 0.05 秒）
- 支持覆盖已存在的转场

**支持的转场类型** (TransitionType)

- fade, dissolve - 淡入淡出类
- wipe-left, wipe-right, wipe-up, wipe-down - 擦除类
- slide-left, slide-right, slide-up, slide-down - 滑动类
- zoom-in, zoom-out - 缩放类

***

## \[0.8.13] - 2026-04-05

### 新增功能

#### 视频编辑器管理器系统

参考 Cutia 项目，重构视频编辑器核心，集成命令系统：

**选择管理器 (SelectionManager)** (`src/video/managers/selection.py`)

- 新增 selected\_elements - 选中的元素ID集合
- 新增 selected\_tracks - 选中的轨道ID集合
- 新增 select\_element(element\_id, add=False) - 选择元素
- 新增 deselect\_element(element\_id) - 取消选择元素
- 新增 select\_track(track\_id, add=False) - 选择轨道
- 新增 deselect\_track(track\_id) - 取消选择轨道
- 新增 clear\_selection() - 清空所有选择
- 新增 get\_selected\_elements(project) - 获取选中的元素对象
- 新增 get\_selected\_tracks(project) - 获取选中的轨道对象
- 新增 subscribe(listener) - 订阅选择变化事件

**保存管理器 (SaveManager)** (`src/video/managers/save.py`)

- 新增 auto\_save\_enabled - 自动保存开关
- 新增 auto\_save\_interval - 自动保存间隔（秒）
- 新增 last\_save\_time - 上次保存时间
- 新增 start() - 启动自动保存
- 新增 stop() - 停止自动保存
- 新增 pause() / resume() - 暂停/恢复保存
- 新增 save(project) - 保存项目
- 新增 mark\_dirty() - 标记需要保存
- 新增 get\_status() - 获取保存状态

**编辑器核心重构 (EditorCore)**

- 新增 command 属性 - CommandManager 实例
- 新增 selection 属性 - SelectionManager 实例
- 新增 save 属性 - SaveManager 实例
- 新增 execute\_command(command) - 执行命令并标记脏状态
- 新增 undo() / redo() - 快捷撤销/重做方法
- 新增 can\_undo() / can\_redo() - 检查撤销/重做可用性
- 新增 start\_auto\_save() / stop\_auto\_save() - 自动保存控制
- TimelineManager 现在使用 SelectionManager 管理选择状态

***

## \[0.8.12] - 2026-04-05

### 新增功能

#### 文档编辑器集成

参考 openakita 项目，集成完整的文档处理功能：

**OOXML 工具模块** (`src/document/ooxml/`)

- 新增 `pack.py` - 打包工具，将解压后的目录打包为 Office 文档
- 新增 `unpack.py` - 解包工具，将 Office 文档解压为 XML 文件
- 新增 `validate.py` - 验证工具，验证文档的 XML 模式合规性
- 支持 DOCX、PPTX、XLSX 文档的底层操作

**DOCX 处理模块** (`src/document/docx/`)

- 新增 `editor.py` - 文档编辑器，基于 XML 的底层编辑
- 新增 `creator.py` - 文档创建器，从模板创建新文档
- 新增 `comment.py` - 批注管理器，添加/回复/删除批注
- 新增 `revision.py` - 修订跟踪器，跟踪文档修改历史
- 新增 `converter.py` - 格式转换器，DOCX 转 PDF/HTML/图片
- 新增 `utilities.py` - XML 编辑器，安全的 XML 解析

**PPTX 处理模块** (`src/document/pptx/`)

- 新增 `creator.py` - 演示文稿创建器，支持幻灯片布局和主题
- 新增 `editor.py` - 演示文稿编辑器，修改文本和形状
- 新增 `slide.py` - 幻灯片管理器，添加/删除/重排幻灯片
- 新增 `thumbnail.py` - 缩略图生成器，生成幻灯片预览图

**XLSX 处理模块** (`src/document/xlsx/`)

- 新增 `creator.py` - 工作簿创建器，支持从模板创建或空白创建
- 新增 `editor.py` - 工作簿编辑器，读取和修改单元格数据
- 新增 `sheet.py` - 工作表管理器，添加/删除/重命名/移动/复制工作表
- 新增 `chart.py` - 图表管理器，支持柱状图、折线图、饼图、散点图等

**PDF 处理模块** (`src/document/pdf/`)

- 新增 `extractor.py` - 文本和表格提取器
- 新增 `merger.py` - PDF 合并和拆分器
- 新增 `form.py` - PDF 表单填写器
- 新增 `ocr.py` - OCR 处理器，支持扫描 PDF 文字识别

**文档管理器增强** (`src/document/manager.py`)

- 新增 `convert_document()` - 文档格式转换
- 新增 `get_document_comments()` - 获取文档批注
- 新增 `add_document_comment()` - 添加文档批注
- 新增 `get_document_revisions()` - 获取文档修订
- 新增 `accept_revision()` / `reject_revision()` - 接受/拒绝修订
- 新增 `create_version_snapshot()` - 创建版本快照
- 新增 `list_versions()` - 列出所有版本
- 新增 `restore_version()` - 恢复到指定版本

### 依赖更新

新增以下 Python 包依赖：

- `pypdf>=4.0.0` - PDF 处理
- `reportlab>=4.0.0` - PDF 生成
- `defusedxml>=0.7.0` - 安全的 XML 解析
- `python-docx>=1.1.0` - Word 文档处理
- `python-pptx>=0.6.23` - PowerPoint 处理
- `pytesseract>=0.3.10` - OCR 支持
- `pdf2image>=1.16.0` - PDF 转图片
- `Pillow>=10.0.0` - 图像处理

***

## \[0.8.11] - 2026-04-05

### 新增功能

#### 视频编辑器命令系统

新增视频编辑器命令系统基础架构，支持撤销/重做操作：

**命令基类 (Command)**

- 新增 execute() 抽象方法 - 执行命令
- 新增 undo() 方法 - 撤销命令（默认抛出未实现异常）
- 新增 redo() 方法 - 重做命令（默认调用 execute）
- 新增 description 属性 - 命令描述（可选）

**命令管理器 (CommandManager)**

- 新增 undo\_stack - 撤销栈
- 新增 redo\_stack - 重做栈
- 新增 execute(command) - 执行命令并压入撤销栈
- 新增 undo() - 撤销最近命令
- 新增 redo() - 重做最近撤销的命令
- 新增 can\_undo() - 是否可撤销
- 新增 can\_redo() - 是否可重做
- 新增 clear() - 清空历史
- 新增 max\_history - 最大历史记录限制（默认100）

**批量命令 (BatchCommand)**

- 新增 commands 列表 - 命令列表
- 新增 execute() - 依次执行所有命令
- 新增 undo() - 逆序撤销所有命令
- 新增 add\_command() - 添加命令到批量操作

#### 本地百科工具

参考 Project N.O.M.A.D. 项目，新增本地百科知识检索功能：

**百科知识工具 (knowledge\_search)**

- 新增 ZIM 文件解析器 - 支持 Wikipedia 离线包格式
- 新增知识搜索功能 - 从本地知识库搜索内容
- 新增文章获取功能 - 获取指定文章的完整内容
- 新增百科库管理功能 - 列出可用的百科库
- 新增 Wikipedia 选项配置 - 支持多种 Wikipedia 版本选择
- 新增 Kiwix 分类支持 - 支持医学、教育、DIY等分类

**数据文件**

- 复制 Project N.O.M.A.D. 的收藏数据：
  - `data/knowledge/wikipedia.json` - Wikipedia 下载选项
  - `data/knowledge/kiwix-categories.json` - Kiwix 分类数据
  - `data/knowledge/maps.json` - 地图收藏数据

#### 离线地图工具

新增离线地图查询功能：

**离线地图工具 (offline\_map)**

- 新增 POI 搜索功能 - 搜索兴趣点
- 新增附近搜索功能 - 搜索指定半径内的 POI
- 新增逆地理编码功能 - 坐标转地址
- 新增距离计算功能 - 计算两点间距离和方位角
- 新增区域列表功能 - 列出可用的地图区域
- 新增收藏集功能 - 列出地图收藏集

**地理计算工具 (GeoUtils)**

- Haversine 距离计算
- 方位角计算
- 边界框计算
- 坐标格式化（小数/度分秒）
- 坐标解析

**内置示例数据**

- 内置 8 个中国主要城市 POI 数据
- 支持天安门、故宫、外滩、东方明珠等景点

### 配置更新

- 新增 `config/knowledge.yaml` - 百科工具配置
- 新增 `config/map.yaml` - 地图工具配置

### 工具系统更新

- 在 `ToolCategory` 枚举中新增 `KNOWLEDGE` 和 `MAP` 类别
- 更新工具注册中心，自动注册新工具
- 更新工具目录生成，支持新类别展示

### 测试

- 新增 `tests/test_knowledge_tool.py` - 百科工具测试
- 新增 `tests/test_map_tool.py` - 地图工具测试

#### 视频编辑器类型扩展

扩展视频编辑器类型定义，参考 Cutia 项目实现：

**新增类型**

- 新增 `Transform` dataclass - 变换属性（scale、position、rotate、flip\_x、flip\_y）
- 新增 `TransitionType` 枚举 - 转场类型（fade、dissolve、wipe、slide、zoom 等 12 种）
- 新增 `TrackTransition` dataclass - 轨道转场（id、type、duration、from\_element\_id、to\_element\_id）
- 新增 `StickerElement` dataclass - 贴纸元素（icon\_name、transform、opacity、color、hidden）

**扩展现有类型**

- `TimelineElement` 新增属性：
  - `transform: Transform` - 变换属性
  - `playback_rate: float` - 播放速率（默认 1.0）
  - `reversed: bool` - 是否倒放（默认 False）
- `Track` 新增属性：
  - `transitions: list[TrackTransition]` - 轨道转场列表
  - `is_main: bool` - 是否主轨道（默认 False）
- `MediaType` 枚举新增 `STICKER` 类型
- `TrackType` 枚举新增 `STICKER` 类型

***

## \[0.8.10] - 2025-04-04

### 新增功能

#### 手机操作工具增强

参考 Operit 项目，优化移动端模块，新增以下核心功能：

**手机操作工具**

- 新增 `phone_operation` 工具 - 统一的自然语言驱动 UI 自动化工具
- 支持自然语言操作意图（如"打开微信发送消息给张三"）
- 支持虚拟屏幕模式（不影响主屏幕）
- 支持最大步骤数限制

**AutoGLM 子代理优化**

- 新增循环执行模式：截图 -> 分析 -> 规划 -> 执行 -> 验证
- 新增屏幕内容理解（使用多模态模型分析截图）
- 新增操作结果验证功能
- 新增失败恢复机制
- 新增操作历史记录

**配置更新**

- 新增 `phone_operation` 配置节
- 新增 `subagent` 配置节
- 支持虚拟屏幕、操作验证、失败恢复等参数配置

### 改进

- 优化子代理执行流程，支持真正的循环执行
- 集成 screen-operation 垂类模型
- 添加 31 个测试用例（全部通过）

***

## \[0.8.9] - 2026-04-04

### 新增功能

#### 浏览器自动化模块全面优化

参考 browser-use 项目，对浏览器自动化模块进行全面优化，新增以下核心功能：

**AI 驱动的浏览器代理系统**

- 新增 `src/browser/agent.py` - BrowserAgent 类，支持自然语言任务执行
- 新增 MessageManager 消息管理器，管理对话历史
- 新增 AgentState/AgentStatus 代理状态管理
- 新增 AgentHistory 代理历史记录

**任务规划系统**

- 新增 `src/browser/planner.py` - TaskPlanner 任务规划器
- 支持 LLM 自动生成执行计划
- 支持计划执行跟踪和动态调整
- 支持重新规划功能

**循环检测系统**

- 新增 `src/browser/loop_detector.py` - LoopDetector 循环检测器
- 支持动作循环检测（相同动作重复执行）
- 支持页面停滞检测（页面内容未变化）
- 支持 URL 循环检测（URL 往返循环）
- 支持状态相似性检测
- 自动生成智能提示建议

**智能元素定位器**

- 新增 `src/browser/locator.py` - ElementLocator 智能元素定位器
- 支持基于索引的元素定位
- 支持基于文本的元素定位（精确/模糊匹配）
- 支持坐标点击模式
- 支持 LLM 友好的元素列表输出

**动作注册中心**

- 新增 `src/browser/registry.py` - Registry 动作注册中心
- 支持装饰器方式注册动作
- 支持参数模型验证（Pydantic）
- 支持动作依赖注入
- 支持超时和重试机制
- 新增 ActionResult 标准化输出

**视觉处理器**

- 新增 `src/browser/vision.py` - VisionProcessor 视觉处理器
- 支持多种截图模式（全页面/元素/区域）
- 支持多模态 LLM 截图分析
- 支持通过视觉分析定位元素坐标
- 支持截图压缩和调整

**结构化输出处理器**

- 新增 `src/browser/structured_output.py` - StructuredOutputProcessor
- 支持 JSON Schema 验证
- 支持分页数据增量提取
- 支持数据去重机制
- 支持 LLM 辅助数据提取

**敏感数据处理器**

- 新增 `src/browser/sensitive.py` - SensitiveDataHandler
- 支持敏感数据占位符替换
- 支持日志脱敏
- 支持安全存储集成
- 支持 SensitiveLogFilter 日志过滤器

***

## \[0.8.8] - 2026-04-04

### 优化改进

#### MobileSubAgent 子代理执行流程优化

- 重构 `src/mobile/advanced_control/subagent.py`，实现真正的循环执行流程
- **循环执行流程**: 截图 -> 分析 -> 规划 -> 执行 -> 验证
- 新增 `_capture_screen` 方法: 使用 ScreenTools 截取屏幕
- 新增 `_analyze_screen` 方法: 使用多模态模型分析截图，提取可操作元素
- 新增 `_plan_next_action` 方法: 根据意图和屏幕内容规划下一步操作
- 新增 `_execute_action` 方法: 执行具体操作（tap, swipe, input\_text, press\_key, launch, long\_press）
- 新增 `_is_task_complete` 方法: 判断任务是否完成
- 新增 `_verify_result` 方法: 验证操作结果
- 新增 `_init_screen_tools` 方法: 初始化屏幕工具
- 新增 `_wait_for_response` 方法: 等待界面响应（默认 500ms）
- 增强 `ActionStep` 数据类: 添加截图前后、分析结果、验证状态字段
- 新增 `ScreenAnalysis` 数据类: 屏幕分析结果模型
- 新增 `PlannedAction` 数据类: 规划操作模型
- 使用 `TaskType.SCREEN_OPERATION` 调用 screen-operation 垂类模型
- 支持操作历史记录功能，记录每步操作的详细信息
- 支持任务完成检测和最大步骤限制
- 支持设备ID参数传递

***

## \[0.8.7] - 2026-04-04

### 新增功能

#### 移动端工具注册 - phone\_operation

- 在 `src/mobile/tool_registry.py` 中新增 `phone_operation` 工具注册
- 工具描述：手机操作工具，通过自然语言控制手机执行各种操作
- 支持参数：
  - `intent` (string, required): 自然语言操作意图
  - `target_app` (string, optional): 目标应用包名
  - `max_steps` (integer, optional): 最大执行步骤数，默认20
  - `use_virtual_display` (boolean, optional): 是否使用虚拟屏幕执行，默认false
- 返回结果包含：success, message, steps\_taken, final\_state
- 集成 `MobileControlManager` 实现自然语言手机控制

***

## \[0.8.6] - 2026-04-04

### 新增功能

#### 浏览器状态管理系统

- 新增 `src/browser/state.py`，实现完整的浏览器状态管理系统
- **PageLoadState 枚举**: 页面加载状态（loading/dom\_content\_loaded/load/network\_idle/error）
- **DOMElement 类**: DOM元素状态模型
  - 包含 element\_id, tag\_name, text, attributes, bounding\_box 等属性
  - `to_llm_text()`: 生成 LLM 友好的文本表示
- **TabState 类**: 标签页状态模型
  - 包含 tab\_id, url, title, is\_active, load\_state 等属性
  - 支持 `to_dict()` 和 `from_dict()` 序列化方法
- **DOMState 类**: DOM状态模型
  - 包含元素列表、选择器映射、可交互元素计数
  - `get_element_by_id()`: 通过ID获取元素
  - `get_clickable_elements()`: 获取所有可点击元素
  - `get_input_elements()`: 获取所有输入元素
  - `to_llm_text()`: 生成 LLM 友好的 DOM 文本表示
- **BrowserState 类**: 浏览器完整状态模型
  - 包含 URL、标题、标签页列表、DOM状态、截图、滚动位置、视口大小
  - `get_active_tab()`: 获取当前活动标签页
  - `get_tab_by_id()`: 通过ID获取标签页
  - `to_llm_text()`: 生成 LLM 友好的状态文本
- **StateDiff 类**: 状态差异检测模型
  - 检测 URL 变化、标题变化、标签页变化、DOM变化
  - 计算 DOM 相似度
  - `to_summary()`: 生成差异摘要
- **BrowserStateHistory 类**: 状态历史记录管理
  - `add_state()`: 添加状态到历史记录
  - `go_back()`/`go_forward()`: 状态回退/前进
  - `get_state_at()`: 获取指定索引的状态
  - 支持历史记录导出和导入
- **StateManager 类**: 状态管理器
  - `capture_state()`: 捕获当前浏览器状态
  - `restore_state()`: 恢复浏览器状态
  - `compare_states()`: 比较两个状态的差异
  - `find_state_by_url()`/`find_state_by_title()`: 查找历史状态
  - `get_url_history()`: 获取 URL 历史记录
- 更新 `src/browser/__init__.py`，导出所有状态管理相关类

***

## \[0.8.5] - 2026-04-04

### 新增功能

#### 浏览器事件总线系统

- 新增 `src/browser/event_bus.py`，实现完整的事件总线系统
- **EventBus 类**: 事件总线核心，提供事件分发和管理功能
  - `dispatch(event)`: 分发事件到所有注册的处理器
  - `on(event_type, handler, priority)`: 注册事件监听器
  - `off(event_type, handler)`: 移除事件监听器
  - `subscribe()`: 装饰器方式订阅事件
  - `add_middleware()`: 添加事件中间件
  - `get_history()`: 获取事件历史记录
- **EventHandler 协议**: 定义事件处理器接口，支持同步和异步处理
- **EventResult 类**: 存储事件处理结果，支持异常捕获和传播
- **BaseEvent 基类**: 事件基类，提供事件ID、时间戳、父事件追踪
  - `event_result()`: 异步等待事件处理完成
  - `get_results()`: 获取所有处理结果
- **EventPriority 枚举**: 定义处理器优先级（LOWEST/LOW/NORMAL/HIGH/HIGHEST/MONITOR）
- **EventState 枚举**: 定义事件状态（PENDING/PROCESSING/COMPLETED/FAILED）
- **浏览器事件类型**: BrowserStartEvent, BrowserStopEvent, NavigateEvent, PageLoadedEvent, ScreenshotEvent, ScriptExecutedEvent, TabCreatedEvent, TabClosedEvent, TabSwitchedEvent, FileDownloadedEvent, ErrorEvent
- 支持多个监听器订阅同一事件类型
- 支持事件处理链（中间件模式）
- 支持事件优先级排序
- 支持通配符订阅（`*`）
- 支持异步事件等待
- 支持全局事件总线实例（`get_event_bus()`/`set_event_bus()`）
- 更新 `src/browser/__init__.py`，导出所有事件总线相关类

***

## \[0.8.4] - 2026-04-04

### 新增功能

#### 浏览器自动化事件系统

- 新增 `src/browser/events.py`，定义浏览器自动化所需的所有事件类型
- **BrowserEvent**: 基础事件类，包含 event\_id, event\_type, timestamp, target\_id 等基础字段
- **EventType**: 事件类型枚举，定义 18 种事件类型
- **EventStatus**: 事件状态枚举（pending/running/completed/failed/cancelled）
- **导航类事件**: NavigateToUrlEvent, GoBackEvent, GoForwardEvent, RefreshEvent
- **交互类事件**: ClickElementEvent, ClickCoordinateEvent, TypeTextEvent, ScrollEvent, SendKeysEvent
- **标签页事件**: SwitchTabEvent, CloseTabEvent, NewTabEvent
- **表单事件**: SelectDropdownOptionEvent, GetDropdownOptionsEvent, UploadFileEvent
- **其他事件**: ScreenshotEvent, ExecuteScriptEvent, ExtractContentEvent
- **create\_event()**: 事件工厂函数，根据事件类型创建事件实例
- 使用 Pydantic BaseModel 作为基类，确保所有事件可序列化
- 更新 `src/browser/__init__.py`，导出所有事件类

***

## \[0.8.3] - 2026-04-04

### 新增功能

#### PDF处理模块

- 新增 `src/document/pdf/` 模块，提供完整的PDF处理功能
- **extractor.py**: PDF文本和表格提取器
  - 使用 pdfplumber 实现文本提取功能
  - 支持按页提取文本内容
  - 支持提取文本块及其坐标信息
  - 支持表格提取并转换为 pandas DataFrame
  - 支持将表格导出为 Excel 文件
  - 支持提取PDF元数据
- **merger.py**: PDF合并和拆分器
  - 使用 pypdf 实现PDF合并功能
  - 支持合并多个PDF文件并添加元数据
  - 支持添加水印
  - 支持旋转页面
  - 支持按页拆分PDF
  - 支持按页码范围拆分
  - 支持提取指定页面
- **form.py**: PDF表单填写器
  - 使用 pypdf 实现表单字段提取
  - 支持文本字段、复选框、单选按钮、下拉选择
  - 支持表单字段验证
  - 支持填写表单并保存
  - 支持导出字段信息为JSON
  - 支持从JSON文件读取并填写表单
- **ocr.py**: PDF OCR处理器
  - 使用 pytesseract 和 pdf2image 实现OCR功能
  - 支持多语言OCR识别（中文、英文等）
  - 支持将PDF转换为图片
  - 支持图片OCR识别
  - 支持返回文本坐标信息
  - 支持判断PDF是否为扫描件
- 更新 `src/document/__init__.py`，导出PDF处理模块

***

## \[0.8.2] - 2026-04-04

### 问题修复

#### 项目配置修复

- **pyproject.toml**: 修复包路径配置 `packages = ["src/pyagent"]` -> `packages = ["src"]`
- **pyproject.toml**: 修复入口点配置 `pyagent.main:main` -> `src.main:main`
- **pyproject.toml**: 同步依赖配置，添加 PyPDF2 和 pdfplumber

#### 模块初始化完善

- **src/**__init__.py: 添加模块初始化代码，导出核心类和函数
- **src/web/routes/**__init__.py: 补充缺失的路由导出（calendar\_router, verification\_router 等）

#### 配置文件补充

- 新增 `config/mcp.json`: MCP服务器配置模板
- 新增 `config/memory.yaml`: 记忆系统配置
- 新增 `config/todo.yaml`: Todo系统配置
- 新增 `config/llm_gateway.yaml`: LLM网关配置

### 改进

- 统一版本号到 v0.8.2
- 完善项目打包配置

***

## \[0.8.1] - 2026-04-04

### 新增功能

#### 意图分析系统

- 新增意图分析层，在消息发送前进行意图识别
- 支持多种意图类型：CHAT、OPEN\_FILE、OPEN\_APP、CREATE\_EVENT、CREATE\_TODO、MODIFY\_SETTINGS
- 实现基于规则的快速匹配和基于 LLM 的深度分析
- 新增意图路由器，智能路由到对应模块

#### IM 通道验证机制

- 新增用户验证机制，仅接收经过验证的私聊消息
- 实现6位随机验证码生成和校验
- 验证状态持久化存储，用户只需验证一次
- 支持管理员撤销用户验证状态
- 验证码10分钟过期机制

#### 斜杠命令增强

- 新增应用打开命令：/calendar、/tasks、/email、/notes、/browser、/files
- 新增文档打开命令：/word、/ppt、/excel
- 新增日程创建命令：/event
- 新增待办创建命令：/todo
- 新增快捷操作命令：/open、/launch
- 前端斜杠面板增加快捷操作区域

#### 拟人系统优化（参考 MaiBot）

- 实现个性状态随机切换（state\_probability 概率控制）
- 实现对话目标分析（GoalAnalyzer，最多3个目标）
- 实现用户记忆管理（Person 类，memory\_points 格式）
- 扩展情感类型和对话风格
- 优化主动行为和上下文理解

#### 设置页面重构

- 设置分类展示：通用、AI Agent、应用、分布式、实验室功能
- 区分同步设置和本地设置
- 同步设置自动同步到域内设备
- 本地设置仅本机生效
- 添加同步状态指示器和"仅本机"标识

#### 分布式架构优化

- 实现智能同步模式选择（实时/增量/手动/离线）
- 网络状态检测和自动切换
- 智能冲突解决（合并算法、最后修改优先）
- 设备能力感知和任务分配
- 离线操作缓存和自动同步恢复

#### 手机操作功能优化（参考 Operit 项目）

- 实现 AutoGLM 子代理模式
- 使用 screen-operation 垂类模型执行自然语言操作
- 支持虚拟屏幕执行（不影响主屏幕）
- 支持并行子代理执行
- 支持会话复用机制

### 新增配置文件

- `config/intent.yaml`: 意图分析配置
- `config/im_verification.yaml`: IM 验证配置
- `config/persona.yaml`: 拟人系统配置

### 新增模块

- `src/interaction/intent/router.py`: 意图路由器
- `src/im/verification/`: IM 通道验证模块
- `src/im/intent_middleware.py`: 意图分析中间件
- `src/interaction/persona/goal_analyzer.py`: 对话目标分析器
- `src/interaction/persona/person.py`: 用户记忆管理
- `src/storage/smart_sync.py`: 智能同步管理器
- `src/mobile/advanced_control/`: 高级手机控制模块
- `src/web/routes/slash_commands.py`: 斜杠命令处理器
- `src/web/routes/settings_routes.py`: 设置管理 API
- `src/web/routes/verification_routes.py`: 验证管理 API

### 版本兼容性

- 向后兼容 v0.8.0
- 自动迁移 v0.8.0 配置到新格式
- 所有 v0.8.0 数据可直接使用

***

## \[0.8.0] - 2026-04-03

### 问题修复

#### 空壳模块修复

- **src/person/**__init__.py: 添加了Person、MemoryPoint、PersonManager的正确导出
- **src/core/**__init__.py: 添加了CoreContext核心上下文类
- **src/chat/**__init__.py: 添加了ChatMessage、ChatSession聊天相关类

#### ASR语音识别模块完善

- 实现了基于Whisper的真实语音识别功能（支持faster-whisper和openai-whisper）
- 添加了FFmpeg音频格式转换和预处理功能
- 支持10+种音频格式（mp3, wav, m4a, mp4, aac, ogg, opus, flac, wma, webm, m4b）
- 添加了多引擎自动检测和降级机制
- 添加了完整的错误处理和日志记录

#### PDF解析器完善

- 添加了基于pdfplumber的备用解析方案
- 添加了基于PyPDF2的备用解析方案
- 修复了基础解析返回空文档的问题（page\_count=00 -> 实际页数）
- 完善了元数据读取功能

#### 金融智能体完善

- 集成了yfinance真实金融数据API
- 添加了缓存机制避免频繁API调用
- 添加了RateLimiter限流机制
- 添加了错误处理和优雅降级

#### 前端修复

- 同步前端版本号从v0.3.2到v0.8.0
- 实现了VideoEditor的splitClip函数

### 智能体系统

- **Agent 抽象基类**: 定义 Agent 标准接口
  - `execute()` 方法：执行任务
  - `can_handle()` 方法：判断是否可处理任务
  - 能力声明：声明可处理的任务类型
- **Registry 注册中心**: 管理所有 Agent
  - 动态注册和注销 Agent
  - 按能力查找 Agent
  - Agent 状态管理
- **Executor 执行器**: 调度 Agent 执行任务
  - 支持优先级调度
  - 支持并发执行
  - 支持任务取消

### 人工任务系统

专为人类用户设计的任务管理系统：

- **四级优先级**: 低/中/高/紧急
- **子任务支持**: 任务拆分管理，进度追踪
- **时间提醒**: 截止日期和提醒功能
- **分类与标签**: 灵活的任务组织方式
- **智能统计**: 任务完成率、过期任务分析
- **持久化存储**: JSON 格式本地存储

### 日历管理

完整的日程管理功能：

- **事件管理**: CRUD 操作，支持标题、描述、地点、参与者
- **重复规则**: 日/周/月/年重复
- **多种提醒**: 邮件、推送、短信提醒
- **ICS 格式**: 与主流日历软件兼容
- **智能搜索**: 按标题、描述、地点、参与者搜索

### 邮件客户端

完整的 SMTP/IMAP 邮件收发功能：

- **SMTP 发送**: SSL/TLS 加密发送邮件
- **IMAP 接收**: 收取、搜索、管理邮件
- **多格式支持**: 纯文本、HTML、混合内容
- **附件处理**: 支持多附件上传下载
- **邮件解析**: 自动解析邮件头、正文、附件

### 语音交互

语音识别（ASR）和语音合成（TTS）功能：

- **多 ASR 引擎**: Whisper、百度、阿里等
- **多 TTS 引擎**: Edge TTS、百度、阿里等
- **实时处理**: 支持流式语音识别和合成
- **多语言支持**: 中文、英文、日文、韩文等
- **语音活动检测**: 自动检测语音开始和结束
- **热词优化**: 支持自定义热词提升识别准确率

### 浏览器自动化

基于 Playwright 的浏览器控制能力：

- **多浏览器支持**: Chromium、Firefox、WebKit
- **页面操作**: 导航、刷新、前进、后退
- **元素交互**: 点击、输入、等待、截图
- **JavaScript 执行**: 在页面上下文中执行脚本
- **数据提取**: 页面内容、Cookie、LocalStorage
- **会话管理**: Cookie 持久化、多页面管理

### PDF 处理

完整的 PDF 文档解析、提取和转换功能：

- **文本提取**: 精确提取 PDF 文本内容和位置信息
- **表格识别**: 自动识别和提取 PDF 中的表格数据
- **图片提取**: 提取 PDF 中的图片资源
- **元数据读取**: 读取标题、作者、创建日期等元数据
- **大纲解析**: 提取 PDF 书签和目录结构

### 分布式存储

跨设备的文件存储和同步功能：

- **跨设备同步**: 文件自动同步到域内所有设备
- **元数据管理**: 完整的文件元数据和位置追踪
- **冲突解决**: 智能处理多设备同时修改的冲突
- **增量同步**: 只传输变更部分，节省带宽
- **本地缓存**: 智能缓存策略，加速文件访问
- **版本历史**: 支持文件版本回溯

### LLM 模型网关

参考 LiteLLM 设计，提供统一的接口访问多个 LLM 提供商：

- **多提供商支持**: OpenAI、Anthropic、DeepSeek、智谱、Moonshot、百度、阿里等
- **统一接口**: 一致的 API 调用方式
- **自动路由**: 根据模型名称自动选择提供商
- **故障转移**: 主提供商失败时自动切换
- **流式响应**: 支持流式输出
- **嵌入向量**: 支持文本嵌入

### 移动端支持

在 Android、iOS、HarmonyOS 等移动设备上运行 PyAgent：

- **多平台支持**: Android、iOS、HarmonyOS
- **设备检测**: 自动检测移动设备环境和能力
- **屏幕控制**: 截图、点击、滑动等操作
- **通知管理**: 读取和处理系统通知
- **短信收发**: 发送和接收短信
- **Linux 环境**: 支持 Linux 部署模式

### 新增模块

- `src/agents/`: 智能体系统
  - `base.py`: Agent 抽象基类
  - `registry.py`: 注册中心
  - `executor.py`: 执行器
- `src/human_tasks/`: 人工任务系统
  - `manager.py`: 任务管理器
  - `task.py`: 任务模型
- `src/calendar/`: 日历管理
  - `manager.py`: 日历管理器
  - `event.py`: 事件模型
- `src/email/`: 邮件客户端
  - `client.py`: 邮件客户端
- `src/voice/`: 语音交互
  - `asr.py`: 语音识别
  - `tts.py`: 语音合成
  - `processor.py`: 语音处理器
- `src/browser/`: 浏览器自动化
  - `controller.py`: 浏览器控制器
- `src/pdf/`: PDF 处理
  - `parser.py`: PDF 解析器
- `src/storage/`: 分布式存储
  - `distributed.py`: 分布式存储核心
- `src/mobile/`: 移动端支持
  - `backend.py`: 移动端后端
- `src/llm/gateway.py`: LLM 模型网关

### 新增文档

- `docs/modules/agent-system.md`: 智能体系统文档
- `docs/modules/human-tasks.md`: 人工任务系统文档
- `docs/modules/calendar.md`: 日历管理文档
- `docs/modules/email-client.md`: 邮件客户端文档
- `docs/modules/voice-interaction.md`: 语音交互文档
- `docs/modules/browser-automation.md`: 浏览器自动化文档
- `docs/modules/pdf-processing.md`: PDF 处理文档
- `docs/modules/distributed-storage.md`: 分布式存储文档
- `docs/modules/llm-gateway.md`: LLM 模型网关文档
- `docs/modules/mobile-support.md`: 移动端支持文档

### 配置文件更新

- 新增 `config/human_tasks.yaml`: 人工任务系统配置
- 新增 `config/calendar.yaml`: 日历管理配置
- 新增 `config/email.yaml`: 邮件客户端配置
- 新增 `config/voice.yaml`: 语音交互配置
- 新增 `config/browser.yaml`: 浏览器自动化配置
- 新增 `config/pdf.yaml`: PDF 处理配置
- 新增 `config/storage.yaml`: 分布式存储配置
- 新增 `config/llm_gateway.yaml`: LLM 模型网关配置
- 新增 `config/mobile.yaml`: 移动端支持配置

***

## \[0.7.2] - 2026-04-01

### 重构

- **域管理API路由重构**: 消除重复实现，统一数据管理
  - 删除内存存储实现 (`_domain_store`, `_device_store`, `_current_domain`)
  - 使用 `DomainManager` 单例替代重复逻辑
  - 实现数据持久化，服务重启后数据不再丢失
  - 统一数据模型 (`DomainInfo`, `DeviceRecord`)
  - 重构 7 个 API 端点 (`create`, `join`, `devices`, `sync`, `status`, `list`, `leave`)
  - 通过 ruff 和 mypy 代码检查

### 改进

- 提升代码质量，消除约 60 行重复代码
- 域和设备数据自动持久化到 `data/domain/` 目录
- 降低维护成本，域管理逻辑集中在 `DomainManager`

***

## \[0.7.1] - 2026-03-30

### 修复

- 修复 `llm/client.py` 缺少 `create_client_from_env` 函数的问题
- 修复 `llm/adapters/anthropic_adapter.py` 文件缺失的问题
- 修复 `llm/__init__.py` 导入问题，正确导入 `LLMRequest` 和 `LLMResponse`
- 修复 `web/app.py` 错误的导入路径（`src.executor` -> `src.execution`）
- 修复 `web/app.py` 重复导入和初始化 `hot_reload_router` 的问题

### 改进

- 完善 `AnthropicAdapter` 实现，支持完整的 Claude API 功能
- 优化模块导入结构，减少循环依赖风险

***

## \[0.7.0] - 2026-03-30

### 原生文档编辑器

- 集成ONLYOFFICE Docs，支持Word/Excel/PPT在线编辑
- AI辅助写作：改写、扩写、缩写、翻译、校对
- Excel数据分析：趋势分析、图表建议、公式推荐
- PPT智能生成：大纲生成、布局建议、配图推荐
- 文档版本管理和导出功能

### 原生视频编辑器

- 参考Cutia架构实现视频编辑核心
- 时间轴管理：多轨道、元素拖拽、精确剪辑
- AI智能剪辑：自动识别精彩片段
- 字幕自动生成：语音转录、时间轴字幕、多语言翻译
- 特效推荐：转场、滤镜、背景音乐推荐
- 多格式导出：支持多种分辨率和格式

### 域系统与分布式准备

- **域概念**: 定义设备域，支持多设备协作
- **设备类型**: PC/MOBILE/SERVER/EDGE四种类型
- **设备能力声明**: CPU核心、内存、存储、GPU等
- **数据同步引擎**:
  - 实时同步模式：每次操作后立即同步
  - 定时同步模式：可配置同步间隔
  - 类Git分支模型：每台设备相当于一个分支
- **冲突解决**: 三方合并算法，自动检测和处理冲突
- **设备记录**: 所有连接过域的设备都会留下记录

### 斜杠菜单优化

- 顶部显示三个彩色文档图标
- PPT图标（橙色）、Word图标（蓝色）、Excel图标（绿色）
- 点击图标快速创建对应文档并跳转编辑器

### Kimi IM通道

- 新增Kimi智能助手作为IM接入通道
- 支持bot-token认证
- 支持长轮询和Webhook两种消息接收模式
- 支持文本和图片消息

### 新增模块

- `src/document/`: 文档编辑器模块
- `src/video/`: 视频编辑器模块
- `src/device/domain_manager.py`: 域管理器
- `src/device/sync_engine.py`: 数据同步引擎
- `src/device/conflict_resolver.py`: 冲突解决器
- `src/im/kimi.py`: Kimi适配器
- `src/web/routes/document_routes.py`: 文档API
- `src/web/routes/video_routes.py`: 视频API
- `src/web/routes/domain_routes.py`: 域API

### 新增前端页面

- `DocumentEditor.vue`: 文档编辑器页面
- `VideoEditor.vue`: 视频编辑器页面

### 配置文件更新

- 新增 `config/domain.yaml`: 域系统配置
- 新增 `config/kimi.yaml`: Kimi通道配置

***

## \[0.6.0] - 2025-03-29

### LLM模块重构

#### 新模型架构

- **BREAKING**: 废除四层模型架构（STRONG/BALANCED/FAST/TINY）
- 新增**基础模型**配置（必填），作为默认模型
- 新增**分级模型**系统：
  - 强能力模型（strong）：负责规划任务，如GLM-5、GPT-5
  - 高性能模型（performance）：负责日常任务，如Qwen3.5-35B
  - 性价比模型（cost-effective）：负责意图判断、记忆整理、浏览器操作等
- 新增**垂类模型**系统：
  - 屏幕操作模型（screen-operation）：默认推荐AutoGLM-Phone-9B
  - 多模态模型（multimodal）：处理图片、视频、音频内容
  - 支持用户自定义垂类模型类型

#### 任务类型映射

- PLANNING → 强能力模型
- GENERAL/TOOL\_USE/REPLY → 高性能模型
- MEMORY/INTENT/BROWSER → 性价比模型
- SCREEN\_OPERATION → 屏幕操作垂类模型
- MULTIMODAL → 多模态垂类模型

#### 多模态回退机制

- 自动检测消息中的多模态内容
- 当模型不支持多模态时，自动使用垂类多模态模型处理

### 设备ID系统

- 新增设备唯一标识符生成
- 设备ID格式：当前日期 + 10位随机数 → SHA256哈希值前16位
- 设备ID持久化存储到 `data/device/device_id.json`
- 工具列表包含设备ID信息

### 统一工具调用接口

- **BREAKING**: 重构所有工具调用流程
- 统一三阶段调用：**激活 → 调用 → 休眠**
- 适用于Skill、MCP工具、自定义工具
- 新增 `UnifiedTool` 抽象基类
- 新增 `ToolRegistry` 工具注册中心

### Mate模式重构

- **BREAKING**: 移除原有Mate模式所有功能（推理可视化、预推理反思等）
- 新Mate模式：开启后使用多智能体协作模式，关闭则不使用
- 简化API接口

### Web UI重构

- **BREAKING**: 移除设置页面入口按钮
- 新增**斜杠命令**入口：输入框输入"/"后显示快捷菜单
- 快捷菜单选项：设置、新话题、Mate模式开关
- 任务进度卡片重构：
  - 移除标题、创建时间显示
  - 进度条改为卡片背景色渐变显示

### ClawHub集成

- 新增ClawHub Skill安装协议支持
- 支持URL格式：
  - `clawhub://skill-name`
  - `https://clawhub.io/skills/skill-name`
- 快速安装Skill技能到本地
- 自动创建SKILL.md文件和目录结构

### 配置文件更新

- 更新 `config/models.yaml` 配置格式
- 新增 `src/device/` 设备ID模块
- 新增 `src/tools/` 统一工具模块
- 新增 `src/skills/clawhub.py` ClawHub安装器

***

## \[0.5.0] - 2025-03-29

### 任务状态系统增强

#### 四状态系统

- **活跃(ACTIVE)**: 任务正常执行（默认状态）
- **暂停(PAUSED)**: 任务暂停执行，可恢复
- **异常(ERROR)**: AI多次尝试后仍无法完成，需人工介入
- **等待(WAITING)**: 任务需要用户确认或协助

#### 状态流转

- 创建 → 活跃 → 执行中 → 完成/失败
- 活跃 ↔ 暂停（可双向切换）
- 执行中 → 等待 → 活跃（需用户操作）
- 执行中 → 异常 → 活跃（需人工介入）

### UI优化

#### 任务卡片显示

- 执行｜规划中
- 执行｜XX%（进度百分比）
- 执行｜须您确认
- 执行｜须您协助
- 执行｜完成
- 执行｜失败

#### 交互改进

- 添加状态筛选功能
- 添加进度排序功能
- 优化卡片布局和动画

### 热更新功能

#### 后端支持

- 新增 `/api/hot-reload` 热更新API
- 支持zip压缩包上传
- 自动验证、解压、应用更新
- 版本备份和回滚机制

#### 特性

- 无需重启服务
- 无缝更新体验
- 更新失败自动回滚

***

## \[0.4.0] - 2025-03-28

### 架构重构

#### 模块重命名

- **BREAKING**: "聊天智能体"重命名为"交互模块" (`src/interaction/`)
- **BREAKING**: "执行智能体"重命名为"执行模块" (`src/execution/`)

#### 新增功能

- **任务概念**: 执行模块的最小上下文单位，包含提示词和上下文
- **规划智能体**: 负责创建和管理多个执行智能体
- **多智能体协作模式**: 支持并行/串行/混合执行，可一键切换
- **微信通道**: 集成OpenClaw微信插件，支持二维码登录、多账号、消息收发、CDN上传

#### Web UI优化

- 协作模式开关
- 任务管理界面
- 交互体验优化

#### API更新

- 新增 `/api/tasks` 任务API
- 新增 `/api/execution` 执行模块API

***

## \[0.3.2] - 2025-03-27

### 新增

- **暗色模式支持**
  - 深色/亮色模式切换
  - 主题色跟随系统设置变化
  - CSS变量系统实现主题样式
  - 平滑过渡动画
- **优化UI组件**
  - 聊天视图： 重新设计，更加现代美观
  - 任务视图: 优化布局和样式
  - 配置视图: 添加暗色模式切换
  - 改进响应式设计
- **改进样式**
  - 使用CSS变量实现主题色
  - 使用SVG图标替代文字图标
  - 添加空状态提示
  - 添加打字动画效果
  - 添加消息淡入淡出动画
  - 优化输入区域布局
- **技术细节**
  - 更新 `App.vue`: 主应用组件
  - 更新 `ChatView.vue`: 聊天视图
  - 更新 `TasksView.vue`: 任务视图
  - 更新 `ConfigView.vue`: 配置视图
  - 更新 `package.json`: 匽"version": "0.3.2"\`

***

## \[0.3.1] - 2025-03-27

### 修复

- 修复 `heart_flow/__init__.py` 导入错误
- 修复测试文件导入路径问题
- 修复代码风格问题

### 改进

- 优化代码结构，修复10个代码风格问题
- 添加完整的测试套件（28个测试用例全部通过）
- 改进模块导出结构

### 测试

- 新增 `tests/conftest.py`: 测试配置
- 新增 `tests/test_memory.py`: 记忆系统测试
- 新增 `tests/test_todo.py`: Todo系统测试
- 新增 `tests/test_humanized.py`: 拟人化系统测试

***

## \[0.3.0] - 2025-03-27

### 新增

- **拟人化聊天智能体**
  - 10种情感类型（中性、开心、悲伤、愤怒、惊讶、好奇、思考、调皮、关心、害羞）
  - 个性状态系统（日常、开心、思考、关心）
  - 行为规划系统（回复时机判断、主动问候、对话结束判断）
  - 拟人化Prompt构建器
- **情感表达系统**
  - 基于消息内容自动推断情感
  - 情感强度控制（0.0-1.0）
  - 情感影响回复风格
- **行为规划系统**
  - 智能判断回复时机
  - 根据时间主动问候（早安/午安/晚安）
  - 识别对话结束信号

### 技术实现

- 新增 `src/interaction/persona/`: 个性系统
- 新增 `src/interaction/planner/action_manager.py`: 行为规划器
- 新增 `src/interaction/heart_flow/humanized_prompt.py`: 拟人化Prompt构建器
- 新增 `config/persona.yaml`: 拟人化配置

***

## \[0.2.0] - 2025-03-27

### 新增

- **AI原生Todo系统**
  - 三级分类架构（Phase → Task → Step）
  - 自动更新任务进度
  - 自动创建验收文档
  - 阶段完成后2-5轮反思
- **四级记忆系统**
  - 聊天智能体记忆（日常/周度/月度/季度）
  - 工作智能体记忆（项目记忆域、偏好记忆）
  - 自动整理和衰减机制
- **Mate模式**
  - 推理可视化
  - 预推理反思
  - 多轮反思机制

### 技术实现

- 新增 `src/todo/`: Todo系统
- 新增 `src/memory/`: 记忆系统
- 新增 `config/todo.yaml`: Todo配置
- 新增 `config/memory.yaml`: 记忆配置
- 新增 `config/mate.yaml`: Mate模式配置

***

## \[0.1.0] - 2025-03-27

### 新增

- **记忆系统优化**
  - 改进记忆存储结构
  - 优化记忆检索算法
- **自我学习系统**
  - 表达学习
  - 黑话学习

### 技术实现

- 新增 `src/expression/`: 自我学习模块
- 新增 `config/self_learning.yaml`: 自我学习配置

***

## \[0.0.1] - 2025-03-20

### 新增

- **项目初始化**
  - 基础项目结构
  - 核心模块框架
  - 基础IM适配器

### 技术实现

- 创建 `src/`: 源代码目录
- 创建 `config/`: 配置文件目录
- 创建 `docs/`: 文档目录
- 创建基础模块：im, llm, web

***

## 版本兼容性说明

### 向后兼容

| 版本     | 兼容性                    |
| ------ | ---------------------- |
| v0.8.0 | **不兼容** v0.7.x（新增大量模块） |
| v0.7.2 | 完全兼容 v0.7.x            |
| v0.7.1 | 完全兼容 v0.7.0            |
| v0.7.0 | **不兼容** v0.6.x（新增模块）   |
| v0.6.0 | **不兼容** v0.5.x（模型配置变更） |
| v0.5.0 | 兼容 v0.4.x              |
| v0.4.0 | **不兼容** v0.3.x（模块重命名）  |
| v0.3.x | 兼容 v0.2.x              |

### 升级指南

#### 从 v0.7.x 升级到 v0.8.0+

1. 备份数据目录
2. 更新代码到 v0.8.0
3. 根据需要添加新模块配置：
   - `config/human_tasks.yaml` - 人工任务系统
   - `config/calendar.yaml` - 日历管理
   - `config/email.yaml` - 邮件客户端
   - `config/voice.yaml` - 语音交互
   - `config/browser.yaml` - 浏览器自动化
   - `config/pdf.yaml` - PDF 处理
   - `config/storage.yaml` - 分布式存储
   - `config/llm_gateway.yaml` - LLM 模型网关
   - `config/mobile.yaml` - 移动端支持
4. 重启服务

#### 从 v0.6.x 升级到 v0.7.0+

1. 备份数据目录
2. 更新代码到 v0.7.0
3. 添加域系统配置 `config/domain.yaml`
4. 重启服务

#### 从 v0.5.x 升级到 v0.6.0+

1. 备份 `config/models.yaml`
2. 更新代码到 v0.6.0
3. 按照新格式更新 `config/models.yaml`
4. 重启服务

#### 从 v0.3.x 升级到 v0.4.0+

1. 备份数据
2. 更新代码到 v0.4.0
3. 更新导入路径（`chat_agent` → `interaction`, `executor_agent` → `execution`）
4. 重启服务

***

## 贡献者

感谢所有为PyAgent做出贡献的开发者！

***

**PyAgent - 让AI更智能，让协作更高效**
