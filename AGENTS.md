# PyAgent 项目介绍 v0.9.7

## 项目概述

PyAgent 是一个功能强大的 Python 智能体框架，支持多平台即时通讯(IM)集成、多智能体协作、ReAct推理引擎、MCP协议支持、AI原生Todo管理、四级记忆系统、自我学习、拟人化聊天、多智能体协作模式、原生文档编辑器、原生视频编辑器、域系统、智能体系统、人工介入任务、日历管理、邮件收发、语音交互、浏览器自动化、PDF处理、分布式存储、知识库系统、工作流引擎、本地模型支持等高级特性。

**当前版本**: v0.9.7

**核心特性**:
- 多智能体架构（交互模块 + 执行模块）
- 多平台IM支持（QQ、钉钉、飞书、企业微信、微信、Kimi）
- ReAct推理引擎
- MCP协议支持
- AI原生Todo系统
- 四级记忆系统
- 自我学习系统
- 拟人化聊天智能体
- 多智能体协作模式（并行/串行/混合）
- 规划智能体
- 任务四状态系统（活跃/暂停/异常/等待）
- 热更新功能（无需重启服务）
- LLM分级模型架构（基础模型+分级模型+垂类模型）
- 统一工具调用接口（激活→调用→休眠）
- ClawHub Skill安装协议支持
- **原生文档编辑器**（Word/Excel/PPT）
- **原生视频编辑器**（AI智能剪辑）
- **域系统**（多设备数据同步）
- **智能体系统**（Agent管理、注册、执行）
- **人工介入任务**（Human-in-the-loop任务管理）
- **日历管理**（事件创建、查询、提醒）
- **邮件收发**（SMTP/IMAP邮件客户端）
- **语音交互**（ASR语音识别、TTS语音合成）
- **浏览器自动化**（Playwright浏览器控制）
- **PDF处理**（PDF解析、转换、提取）
- **分布式存储**（跨设备文件同步）
- **LLM模型网关**（参考LiteLLM的统一接口）
- **知识库系统**（文档索引、倒排搜索）
- **工作流引擎**（触发器、动作、版本管理）
- **本地模型支持**（llama.cpp、MNN后端）
- **角色卡系统**（角色定义、PNG元数据、QR分享）
- **研究规划器**（任务分解、验证、聚合）
- **调试系统**（工具调用跟踪、会话管理）
- **成本追踪**（多租户统计、预算告警）
- **虚拟密钥管理**（速率限制、配额管理）
- **视图系统**（看板、表格、过滤器）
- **自我进化机制**（性能监控、自动优化）

---

## 项目结构

```
pyagent/
├── src/                          # 源代码目录
│   ├── main.py                   # 主入口文件
│   ├── interaction/              # 交互模块(v0.4.0重命名)
│   │   ├── heart_flow/           # 心流聊天核心
│   │   ├── persona/              # 个性系统(v0.3.0)
│   │   ├── planner/              # 动作规划器
│   │   └── replyer/              # 回复生成器
│   ├── execution/                # 执行模块(v0.4.0重命名)
│   │   ├── task.py               # 任务定义(v0.4.0)
│   │   ├── planner_agent.py      # 规划智能体(v0.4.0)
│   │   └── collaboration.py      # 协作模式(v0.4.0)
│   ├── agents/                   # 智能体系统(v0.8.0)
│   │   ├── base.py               # Agent基类
│   │   ├── registry.py           # 注册中心
│   │   └── executor.py           # 执行器
│   ├── human_tasks/              # 人工任务系统(v0.8.0)
│   │   ├── manager.py            # 任务管理器
│   │   └── task.py               # 任务模型
│   ├── calendar/                 # 日历管理(v0.8.0)
│   │   ├── manager.py            # 日历管理器
│   │   └── event.py              # 事件模型
│   ├── email/                    # 邮件客户端(v0.8.0)
│   │   └── client.py             # 邮件客户端
│   ├── voice/                    # 语音交互(v0.8.0)
│   │   ├── asr.py                # 语音识别
│   │   ├── tts.py                # 语音合成
│   │   └── processor.py          # 语音处理器
│   ├── browser/                  # 浏览器自动化(v0.8.0)
│   │   └── controller.py         # 浏览器控制器
│   ├── pdf/                      # PDF处理(v0.8.0)
│   │   └── parser.py             # PDF解析器
│   ├── storage/                  # 分布式存储(v0.8.0)
│   │   └── distributed.py        # 分布式存储核心
│   ├── mobile/                   # 移动端支持(v0.8.0)
│   │   └── backend.py            # 移动端后端
│   ├── memory/                   # 记忆系统
│   ├── todo/                     # AI原生Todo系统
│   ├── expression/               # 自我学习系统
│   ├── llm/                      # LLM客户端
│   │   └── gateway.py            # LLM模型网关(v0.8.0)
│   ├── im/                       # IM平台适配器
│   │   └── wechat/               # 微信适配器(v0.4.0)
│   ├── mcp/                      # MCP协议支持
│   └── web/                      # Web服务
├── tests/                        # 测试套件(v0.3.1)
│   ├── conftest.py               # 测试配置
│   ├── test_humanized.py         # 拟人化测试
│   ├── test_todo.py              # Todo测试
│   └── test_memory.py            # 记忆测试
├── frontend/                     # 前端代码(Vue.js)
├── config/                       # 配置文件
├── docs/                         # 文档目录
├── skills/                       # 技能目录
├── data/                         # 数据目录
├── requirements.txt              # 依赖列表
├── pyproject.toml               # 项目配置
├── README.md                    # 项目说明
├── CHANGELOG.md                 # 更新日志
└── AGENTS.md                    # 本文件
```

---

## 重要文档导航

### 入门文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **README** | [README.md](README.md) | 项目总览、快速开始、特性介绍 |
| **更新日志** | [CHANGELOG.md](CHANGELOG.md) | 版本更新记录、新功能说明 |
| **安装指南** | [README.md#快速开始](README.md#快速开始) | 环境要求、安装步骤 |

### 架构文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **架构设计** | [docs/architecture.md](docs/architecture.md) | 系统架构、模块关系、数据流 |
| **API文档** | [docs/api.md](docs/api.md) | REST API、WebSocket接口 |
| **配置文档** | [docs/configuration.md](docs/configuration.md) | 所有配置选项详解 |
| **部署文档** | [docs/deployment.md](docs/deployment.md) | 部署指南、IM平台接入 |
| **开发文档** | [docs/development.md](docs/development.md) | 开发指南、代码规范 |
| **测试文档** | [docs/testing.md](docs/testing.md) | 测试套件、运行方法(v0.3.1) |
| **前端文档** | [docs/frontend.md](docs/frontend.md) | 前端UI、暗色模式(v0.3.2) |

### 模块详细文档

#### v0.3.0 新增 - 拟人化系统
| 文档 | 路径 | 说明 |
|------|------|------|
| **拟人化系统** | [docs/modules/persona-system.md](docs/modules/persona-system.md) | 拟人化聊天智能体、情感表达、行为规划 |

#### v0.2.0 新增 - 核心系统
| 文档 | 路径 | 说明 |
|------|------|------|
| **Todo系统** | [docs/modules/todo-system.md](docs/modules/todo-system.md) | AI原生Todo列表、三级分类、验收文档 |
| **记忆系统** | [docs/modules/memory-system.md](docs/modules/memory-system.md) | 四级记忆架构、项目记忆域 |
| **Mate模式** | [docs/modules/mate-mode.md](docs/modules/mate-mode.md) | 推理可视化、预推理反思 |

#### v0.8.0 新增 - 扩展系统
| 文档 | 路径 | 说明 |
|------|------|------|
| **智能体系统** | [docs/modules/agent-system.md](docs/modules/agent-system.md) | Agent基类、注册中心、执行器 |
| **人工任务系统** | [docs/modules/human-tasks.md](docs/modules/human-tasks.md) | Human-in-the-loop任务管理 |
| **日历管理** | [docs/modules/calendar.md](docs/modules/calendar.md) | 事件管理、提醒、ICS支持 |
| **邮件客户端** | [docs/modules/email-client.md](docs/modules/email-client.md) | SMTP/IMAP邮件收发 |
| **语音交互** | [docs/modules/voice-interaction.md](docs/modules/voice-interaction.md) | ASR语音识别、TTS语音合成 |
| **浏览器自动化** | [docs/modules/browser-automation.md](docs/modules/browser-automation.md) | Playwright浏览器控制 |
| **PDF处理** | [docs/modules/pdf-processing.md](docs/modules/pdf-processing.md) | PDF解析、提取、转换 |
| **分布式存储** | [docs/modules/distributed-storage.md](docs/modules/distributed-storage.md) | 跨设备文件同步 |
| **LLM模型网关** | [docs/modules/llm-gateway.md](docs/modules/llm-gateway.md) | 多提供商统一接口 |
| **移动端支持** | [docs/modules/mobile-support.md](docs/modules/mobile-support.md) | Android/iOS/HarmonyOS支持 |

#### 基础模块
| 文档 | 路径 | 说明 |
|------|------|------|
| **Chat Agent** | [docs/modules/chat-agent.md](docs/modules/chat-agent.md) | 聊天Agent、心流架构 |
| **Executor Agent** | [docs/modules/executor-agent.md](docs/modules/executor-agent.md) | 执行Agent、ReAct引擎 |
| **LLM Client** | [docs/modules/llm-client-v2.md](docs/modules/llm-client-v2.md) | LLM客户端、分级模型、垂类模型 |
| **IM Adapter** | [docs/modules/im-adapter.md](docs/modules/im-adapter.md) | IM平台适配器 |
| **Device ID** | [docs/modules/device-id.md](docs/modules/device-id.md) | 设备ID系统 |
| **Unified Tool** | [docs/modules/unified-tool.md](docs/modules/unified-tool.md) | 统一工具调用接口 |
| **ClawHub** | [docs/modules/clawhub.md](docs/modules/clawhub.md) | Skill技能安装协议 |

---

## 快速导航

### 按角色查找文档

**如果你是新用户**:
1. [README.md](README.md) - 了解项目
2. [README.md#快速开始](README.md#快速开始) - 安装和运行
3. [docs/configuration.md](docs/configuration.md) - 配置项目

**如果你是开发者**:
1. [docs/architecture.md](docs/architecture.md) - 了解架构
2. [docs/development.md](docs/development.md) - 开发指南
3. [docs/api.md](docs/api.md) - API接口

**如果你是运维人员**:
1. [docs/deployment.md](docs/deployment.md) - 部署指南
2. [docs/configuration.md](docs/configuration.md) - 配置详解
3. [CHANGELOG.md](CHANGELOG.md) - 版本更新

**如果你需要进行构建打包**:
1. 查看"构建和打包"章节 - 自动化构建脚本使用
2. `build.ps1` - 一键构建wheel/EXE/APK
3. `.trae/memory/build-package.md` - 构建记忆文档

**如果你需要进行发布**:
1. 查看"发布前检查流程"章节 - 完整的发布检查清单
2. `pre-release.ps1` - 快速发布前检查脚本
3. 确保多端兼容性和测试通过

**如果你想了解特定功能**:
- Todo系统 → [docs/modules/todo-system.md](docs/modules/todo-system.md)
- 记忆系统 → [docs/modules/memory-system.md](docs/modules/memory-system.md)
- 拟人化聊天 → [docs/modules/persona-system.md](docs/modules/persona-system.md)
- Mate模式 → [docs/modules/mate-mode.md](docs/modules/mate-mode.md)
- 智能体系统 → [docs/modules/agent-system.md](docs/modules/agent-system.md)
- 人工任务系统 → [docs/modules/human-tasks.md](docs/modules/human-tasks.md)
- 日历管理 → [docs/modules/calendar.md](docs/modules/calendar.md)
- 邮件客户端 → [docs/modules/email-client.md](docs/modules/email-client.md)
- 语音交互 → [docs/modules/voice-interaction.md](docs/modules/voice-interaction.md)
- 浏览器自动化 → [docs/modules/browser-automation.md](docs/modules/browser-automation.md)
- PDF处理 → [docs/modules/pdf-processing.md](docs/modules/pdf-processing.md)
- 分布式存储 → [docs/modules/distributed-storage.md](docs/modules/distributed-storage.md)
- LLM模型网关 → [docs/modules/llm-gateway.md](docs/modules/llm-gateway.md)
- 移动端支持 → [docs/modules/mobile-support.md](docs/modules/mobile-support.md)

---

## 核心模块说明

### 1. 交互模块 (v0.4.0重命名)
**位置**: `src/interaction/`

让AI回复更加自然、像真人一样聊天：
- 10种情感类型（开心、悲伤、愤怒、惊讶等）
- 多种个性状态随机切换
- 智能行为规划（懂得何时说话）
- 主动问候机制

### 2. 执行模块 (v0.4.0重命名)
**位置**: `src/execution/`

任务执行引擎：
- ReAct推理引擎
- 任务概念（最小上下文单位）
- 规划智能体（创建和管理多个执行智能体）
- 多智能体协作模式（并行/串行/混合）
- 工具调用

### 3. AI原生Todo系统 (v0.2.0)
**位置**: `src/todo/`

三级分类的任务管理：
- Phase（阶段）→ Task（任务）→ Step（步骤）
- 自动更新进度
- 自动创建验收文档
- 阶段完成后自动反思

### 4. 四级记忆系统 (v0.2.0)
**位置**: `src/memory/`

分层记忆管理：
- 聊天记忆：日常→周度→月度→季度
- 工作记忆：项目记忆域 + 偏好记忆
- 自动整理和衰减

### 5. LLM客户端
**位置**: `src/llm/`

多模型支持：
- **基础模型**: 默认模型配置（必填）
- **分级模型**: strong/performance/cost_effective
- **垂类模型**: screen_operation/multimodal/自定义
- **任务类型映射**: 自动选择合适模型
- **多模态回退**: 自动处理多模态内容

### 6. 前端UI (v0.3.2)
**位置**: `frontend/`

Vue.js 3 构建的现代化Web界面：
- **暗色模式**: 支持深色/亮色主题切换
- **响应式设计**: 适配桌面和移动设备
- **现代化UI**: 聊天视图、任务视图、配置视图
- **流畅动画**: 消息动画、过渡效果
- **SVG图标**: 统一的图标系统
- **协作模式开关**: v0.4.0新增

### 7. 设备ID系统
**位置**: `src/device/`

设备识别和管理：
- **唯一标识**: 16位设备ID（SHA256哈希）
- **持久化存储**: 自动保存到文件
- **元数据管理**: 支持自定义设备信息
- **工具集成**: 工具调用时传递设备信息

### 8. 统一工具接口
**位置**: `src/tools/`

三阶段工具调用模型：
- **激活(Activate)**: 初始化资源
- **执行(Execute)**: 执行业务逻辑
- **休眠(Dormant)**: 释放资源
- **状态管理**: IDLE/ACTIVE/DORMANT/ERROR
- **自动生命周期**: 统一调用入口自动处理

### 9. 智能体系统 (v0.8.0)
**位置**: `src/agents/`

Agent 抽象基类和注册中心：
- **Agent 基类**: 定义 Agent 标准接口
- **Registry 注册中心**: 管理所有 Agent
- **Executor 执行器**: 调度 Agent 执行任务
- **能力声明**: Agent 声明可处理的任务类型

### 10. 人工任务系统 (v0.8.0)
**位置**: `src/human_tasks/`

专为人类用户设计的任务管理：
- **四级优先级**: 低/中/高/紧急
- **子任务支持**: 任务拆分管理
- **时间提醒**: 截止日期和提醒功能
- **统计功能**: 完成率、过期任务分析

### 11. 日历管理 (v0.8.0)
**位置**: `src/calendar/`

完整的日程管理功能：
- **事件管理**: CRUD 操作
- **重复规则**: 日/周/月/年重复
- **提醒功能**: 邮件/推送/短信提醒
- **ICS 支持**: 与主流日历软件兼容

### 12. 邮件客户端 (v0.8.0)
**位置**: `src/email/`

完整的邮件收发功能：
- **SMTP 发送**: SSL/TLS 加密
- **IMAP 接收**: 收取、搜索、管理
- **多格式支持**: 纯文本、HTML、混合内容
- **附件处理**: 多附件上传下载

### 13. 语音交互 (v0.8.0)
**位置**: `src/voice/`

语音识别和合成：
- **多 ASR 引擎**: Whisper、百度、阿里
- **多 TTS 引擎**: Edge TTS、百度、阿里
- **实时处理**: 流式语音识别和合成
- **多语言支持**: 中/英/日/韩等

### 14. 浏览器自动化 (v0.8.0)
**位置**: `src/browser/`

基于 Playwright 的浏览器控制：
- **多浏览器支持**: Chromium、Firefox、WebKit
- **页面操作**: 导航、点击、输入、截图
- **JavaScript 执行**: 页面脚本执行
- **会话管理**: Cookie 和 LocalStorage

### 15. PDF 处理 (v0.8.0)
**位置**: `src/pdf/`

PDF 文档解析和提取：
- **文本提取**: 精确提取文本和位置
- **表格识别**: 自动识别表格数据
- **图片提取**: 提取 PDF 中的图片
- **元数据读取**: 标题、作者、日期等

### 16. 分布式存储 (v0.8.0)
**位置**: `src/storage/`

跨设备文件存储和同步：
- **跨设备同步**: 文件自动同步到域内设备
- **冲突解决**: 智能处理多设备修改冲突
- **增量同步**: 只传输变更部分
- **版本历史**: 支持文件版本回溯

### 17. LLM 模型网关 (v0.8.0)
**位置**: `src/llm/gateway.py`

参考 LiteLLM 的统一接口：
- **多提供商支持**: OpenAI、Anthropic、DeepSeek、智谱等
- **自动路由**: 根据模型名自动选择提供商
- **故障转移**: 主提供商失败自动切换
- **统一计费**: 跨提供商统一计费接口

### 18. 移动端支持 (v0.8.0)
**位置**: `src/mobile/`

移动设备后端支持：
- **多平台支持**: Android、iOS、HarmonyOS
- **设备检测**: 自动检测移动环境和能力
- **屏幕控制**: 截图、点击、滑动操作
- **通知管理**: 读取和处理系统通知
- **短信收发**: 发送和接收短信

### 19. 知识库系统 (v0.9.7)
**位置**: `src/knowledge/`

文档索引和搜索系统：
- **文档索引**: 支持多种文档格式索引
- **倒排索引**: 高效的全文搜索
- **相关性计算**: TF-IDF、BM25算法
- **多租户隔离**: 支持多用户知识库

### 20. 工作流引擎 (v0.9.7)
**位置**: `src/workflow/`

自动化工作流系统：
- **触发器系统**: 定时、事件、Webhook、条件触发
- **动作系统**: HTTP请求、脚本执行、通知发送
- **版本管理**: 工作流版本控制和历史记录
- **执行监控**: 实时监控和错误处理

### 21. 本地模型支持 (v0.9.7)
**位置**: `src/local_model/`

本地LLM模型后端：
- **llama.cpp后端**: GGUF格式模型支持
- **MNN后端**: 移动端优化的推理引擎
- **模型管理**: 自动下载和配置
- **资源监控**: GPU/CPU资源使用监控

### 22. 角色卡系统 (v0.9.7)
**位置**: `src/persona/character_card.py`

AI角色定义和分享：
- **角色定义**: 名称、描述、性格、问候语
- **PNG元数据**: 角色卡嵌入PNG图片
- **QR码分享**: 快速分享和导入角色卡
- **兼容格式**: 支持主流角色卡格式

### 23. 研究规划器 (v0.9.7)
**位置**: `src/research/`

研究任务分解和验证：
- **任务分解**: 自动分解复杂研究任务
- **子任务验证**: 验证子任务完成质量
- **结果聚合**: 聚合多源研究结果
- **迭代优化**: 多轮迭代改进

### 24. 调试系统 (v0.9.7)
**位置**: `src/debug/`

工具调用调试和跟踪：
- **调用跟踪**: 记录所有工具调用
- **会话管理**: 管理调试会话
- **日志分析**: 执行日志分析
- **导出功能**: 调试信息导出

### 25. 成本追踪 (v0.9.7)
**位置**: `src/llm/gateway/cost_tracker.py`

LLM使用成本统计：
- **多租户统计**: 按租户统计成本
- **多维度分析**: 按模型、时间范围统计
- **预算限制**: 设置预算上限
- **告警机制**: 超预算自动告警

### 26. 虚拟密钥管理 (v0.9.7)
**位置**: `src/llm/gateway/key_manager.py`

API密钥管理：
- **虚拟密钥**: 生成和管理虚拟密钥
- **速率限制**: 请求频率控制
- **配额管理**: 使用配额管理
- **权限控制**: 密钥权限设置

### 27. 视图系统 (v0.9.7)
**位置**: `src/views/`

数据展示视图：
- **看板视图**: 拖拽式看板
- **表格视图**: 表格数据展示
- **过滤器**: 数据过滤和筛选
- **排序功能**: 多字段排序

### 28. 自我进化机制 (v0.9.7)
**位置**: `src/evolution/`

系统自我优化：
- **性能监控**: 实时性能监控
- **分析建议**: 自动生成优化建议
- **学习反馈**: 从用户反馈中学习
- **持续改进**: 自动应用改进

---

## 配置文件位置

| 配置 | 路径 | 说明 |
|------|------|------|
| 环境变量 | `.env` | API密钥、基础配置 |
| 模型配置 | `config/models.yaml` | LLM模型配置 |
| MCP配置 | `config/mcp.json` | MCP服务器配置 |
| Todo配置 | `config/todo.yaml` | Todo系统配置 |
| Mate模式 | `config/mate.yaml` | Mate模式配置 |
| 记忆系统 | `config/memory.yaml` | 记忆系统配置 |
| 拟人化 | `config/persona.yaml` | 拟人化配置 |
| IM平台 | `config/onebot.yaml` 等 | 各平台适配器配置 |
| 人工任务 | `config/human_tasks.yaml` | 人工任务系统配置 (v0.8.0) |
| 日历 | `config/calendar.yaml` | 日历管理配置 (v0.8.0) |
| 邮件 | `config/email.yaml` | 邮件客户端配置 (v0.8.0) |
| 语音 | `config/voice.yaml` | 语音交互配置 (v0.8.0) |
| 浏览器 | `config/browser.yaml` | 浏览器自动化配置 (v0.8.0) |
| PDF | `config/pdf.yaml` | PDF处理配置 (v0.8.0) |
| 存储 | `config/storage.yaml` | 分布式存储配置 (v0.8.0) |
| LLM网关 | `config/llm_gateway.yaml` | LLM模型网关配置 (v0.8.0) |
| 移动端 | `config/mobile.yaml` | 移动端支持配置 (v0.8.0) |

---

## 数据存储位置

```
data/
├── memory/           # 记忆数据
│   ├── chat/         # 聊天记忆
│   └── work/         # 工作记忆
├── todo/             # Todo数据
│   └── verifications/ # 验收文档
└── logs/             # 日志文件
```

---

## 测试套件

**v0.3.1 新增**: 完整的测试套件（28个测试用例全部通过）

### 测试文件位置

| 测试文件 | 路径 | 说明 |
|----------|------|------|
| **测试配置** | `tests/conftest.py` | pytest配置和fixture |
| **拟人化测试** | `tests/test_humanized.py` | 拟人化系统测试（14个测试） |
| **Todo测试** | `tests/test_todo.py` | Todo系统测试（10个测试） |
| **记忆测试** | `tests/test_memory.py` | 记忆系统测试（4个测试） |

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_humanized.py
pytest tests/test_todo.py
pytest tests/test_memory.py

# 运行并显示详细信息
pytest -v

# 运行并生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试覆盖范围

- **拟人化系统**: Prompt构建、情感推断、行为规划、对话管理
- **Todo系统**: 阶段/任务/步骤管理、自动更新、统计信息
- **记忆系统**: 聊天记忆存储、工作记忆存储、项目域管理

---

## 代码质量检查

项目提供了统一的代码质量检查脚本 `check.ps1`，可一键运行所有测试和代码风格检查。

### 脚本位置

`D:\agent\check.ps1`

### 检查工具

| 工具 | 说明 | 配置位置 |
|------|------|----------|
| **pytest** | 单元测试框架 | `pytest.ini` / `pyproject.toml` |
| **ruff** | 代码风格检查和格式化 | `pyproject.toml` |
| **mypy** | 静态类型检查 | `pyproject.toml` |
| **bandit** | 安全漏洞检查 | `pyproject.toml` |
| **pydocstyle** | 文档字符串检查 | `pyproject.toml` |

### 使用方法

```powershell
# 运行所有检查（测试 + 代码风格 + 类型检查 + 安全检查 + 文档检查）
.\check.ps1

# 跳过测试
.\check.ps1 -SkipTests

# 跳过代码风格检查
.\check.ps1 -SkipLint

# 跳过类型检查
.\check.ps1 -SkipTypeCheck

# 跳过安全检查
.\check.ps1 -SkipSecurity

# 跳过文档检查
.\check.ps1 -SkipDocs

# 自动修复代码风格问题
.\check.ps1 -Fix

# 生成测试覆盖率报告
.\check.ps1 -Coverage

# 显示详细输出
.\check.ps1 -Verbose

# 组合使用
.\check.ps1 -SkipTests -Fix
.\check.ps1 -Coverage -Verbose
```

### 检查结果

脚本运行后会显示汇总结果：
- `[PASS]` - 检查通过（绿色）
- `[WARN]` - 检查通过但有警告（黄色）
- `[FAIL]` - 检查失败（红色）

### Ruff 规则说明

项目启用了以下 Ruff 规则集：

| 规则集 | 说明 |
|--------|------|
| E | pycodestyle 错误 |
| F | pyflakes 错误 |
| W | pycodestyle 警告 |
| I | isort 导入排序 |
| N | PEP8 命名规范 |
| UP | pyupgrade 现代化语法 |
| B | flake8-bugbear 常见错误 |
| C4 | flake8-comprehensions 列表推导式 |
| DTZ | flake8-datetimez 时区处理 |
| T10 | flake8-debugger 调试语句 |
| PT | flake8-pytest-style pytest风格 |
| SIM | flake8-simplify 代码简化 |
| PL | pylint 规则 |
| RUF | ruff 特定规则 |

### 添加新测试

测试文件命名规范：`test_*.py`

测试类命名规范：`Test*`

测试函数命名规范：`test_*`

```python
# tests/test_example.py
import pytest

class TestExample:
    def test_something(self):
        assert True

    @pytest.mark.asyncio
    async def test_async_operation(self):
        result = await some_async_function()
        assert result is not None
```

### CI/CD 集成

可在 CI/CD 流程中集成检查脚本：

```yaml
# GitHub Actions 示例
- name: Run tests and lint
  run: |
    .\check.ps1 -Coverage
```

---

## 构建和打包

### 自动化构建脚本

项目提供了自动化构建脚本 `build.ps1`，可一键完成所有构建任务。

#### 脚本位置

`D:\agent\build.ps1`

#### 使用方法

```powershell
# 完整构建（清理 + wheel + EXE + APK）
.\build.ps1

# 只构建wheel包
.\build.ps1 -SkipExe -SkipApk

# 只构建EXE
.\build.ps1 -SkipWheel -SkipApk

# 只构建APK
.\build.ps1 -SkipWheel -SkipExe

# 不清理旧文件（增量构建）
.\build.ps1 -NoClean
```

#### 参数说明

| 参数 | 说明 |
|------|------|
| `-SkipWheel` | 跳过构建wheel包 |
| `-SkipExe` | 跳过构建EXE |
| `-SkipApk` | 跳过构建APK |
| `-NoClean` | 不清理旧的构建文件 |

#### 输出文件位置

| 构建类型 | 输出路径 |
|----------|----------|
| Wheel包 | `D:\agent\dist\pyagent-0.8.2-py3-none-any.whl` |
| EXE | `D:\agent\dist\exe\PyAgent\PyAgent.exe` |
| APK | `D:\agent\android\app\build\outputs\apk\debug\app-debug.apk` |

### 构建依赖环境

| 工具 | 版本 | 位置 |
|------|------|------|
| Python | 3.12.13 | `D:\agent\.venv` |
| PyInstaller | 6.19.0 | 虚拟环境中 |
| OpenJDK | 17.0.2 | `D:\jdk-17.0.2` |
| Android SDK | 34.0.0 | `D:\android-sdk` |
| Gradle | 8.7 | `D:\rub\gradle-8.7` |
| Kotlin | 1.9.0 | Android项目依赖 |
| Android Gradle Plugin | 8.2.0 | Android项目依赖 |

### 手动构建步骤

#### 构建Wheel包

```powershell
.venv\Scripts\python.exe -m build --wheel --outdir dist
```

#### 构建EXE

```powershell
.venv\Scripts\pyinstaller.exe --distpath dist\exe --workpath build\pyinstaller build\PyAgent.spec
```

#### 构建APK

```powershell
$env:JAVA_HOME = "D:\jdk-17.0.2"
$env:ANDROID_HOME = "D:\android-sdk"
D:\rub\gradle-8.7\bin\gradle.bat -p android assembleDebug --no-daemon
```

### Android项目结构

```
android/
├── app/
│   ├── src/main/
│   │   ├── java/com/pyagent/app/
│   │   │   ├── MainActivity.kt      # 主Activity
│   │   │   └── ui/theme/Theme.kt    # 主题配置
│   │   ├── res/                     # 资源文件
│   │   └── AndroidManifest.xml      # 清单文件
│   └── build.gradle.kts             # 应用构建配置
├── build.gradle.kts                 # 项目构建配置
├── settings.gradle.kts              # 项目设置
└── gradle.properties                # Gradle属性
```

### 构建优化建议

1. **EXE优化**
   - 使用`--onefile`打包成单个EXE文件
   - 使用`--windowed`创建无控制台窗口的应用
   - 使用UPX压缩减小体积

2. **APK优化**
   - 配置release签名用于发布
   - 启用代码混淆和资源压缩
   - 考虑集成ChaquoPy运行Python后端

3. **CI/CD集成**
   - 可将构建脚本集成到GitHub Actions
   - 配置自动版本号管理
   - 添加自动发布流程

---

## 发布前检查流程

在每次发布新版本前，必须按照以下流程进行严格检查，确保代码质量和多端兼容性。

### 1. 多端兼容性检查

项目支持移动端、桌面端和Web端，使用统一的后端，但每个端有独立的前端实现。

#### 平台架构

| 平台 | 前端技术 | 后端 | 说明 |
|------|----------|------|------|
| **Web端** | Vue.js 3 | Python (FastAPI) | 浏览器访问，响应式设计 |
| **桌面端** | Electron / Tauri | Python (FastAPI) | Windows/macOS/Linux客户端 |
| **移动端** | Android原生 (Kotlin) | Python (FastAPI) | Android APK |

#### 兼容性检查清单

| 检查项 | 说明 | 验证方法 |
|--------|------|----------|
| **API兼容性** | 确保后端API变更不影响各端前端 | 运行API测试套件 |
| **UI适配** | 检查各端UI是否正确显示 | 手动测试各端界面 |
| **功能一致性** | 确保核心功能在各端表现一致 | 功能测试矩阵 |
| **响应式设计** | Web端适配不同屏幕尺寸 | 浏览器响应式测试 |
| **移动端适配** | 检查移动端特有功能（通知、权限等） | 真机测试 |

#### 前端代码位置

```
frontend/           # Web端前端 (Vue.js)
├── src/
│   ├── views/      # 页面组件
│   ├── components/ # 通用组件
│   └── assets/     # 静态资源

android/            # 移动端前端 (Android原生)
├── app/src/main/
│   ├── java/       # Kotlin代码
│   └── res/        # 资源文件

desktop/            # 桌面端前端 (可选)
└── src/            # Electron/Tauri代码
```

### 2. 自动测试运行

运行位于项目根目录下的自动测试脚本，确保所有测试通过。

```powershell
# 运行完整测试套件
.\check.ps1

# 或单独运行测试
pytest

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

#### 测试失败处理

- **无论问题是否由新增模块导致**，都需要进行修复
- 修复后重新运行测试，确保全部通过
- 记录修复过程，更新相关文档

### 3. 代码提交规范

#### 提交到develop分支

所有开发工作必须提交到`develop`分支：

```powershell
# 确保在develop分支
git checkout develop

# 拉取最新代码
git pull origin develop

# 添加变更
git add .

# 提交（遵循Conventional Commits规范）
git commit -m "feat(module): description of changes"

# 推送到远程
git push origin develop
```

#### 提交前检查

- [ ] 代码通过所有测试
- [ ] 代码通过代码风格检查（ruff）
- [ ] 代码通过类型检查（mypy）
- [ ] 代码通过安全检查（bandit）
- [ ] 文档已更新（如有必要）
- [ ] CHANGELOG.md已更新

### 4. 构建测试

运行构建脚本，确保各平台构建成功。

```powershell
# 完整构建
.\build.ps1

# 或分步构建
.\build.ps1 -SkipExe -SkipApk    # 只构建wheel
.\build.ps1 -SkipWheel -SkipApk  # 只构建EXE
.\build.ps1 -SkipWheel -SkipExe  # 只构建APK
```

#### 构建验证清单

| 构建产物 | 验证内容 | 状态 |
|----------|----------|------|
| **Wheel包** | 安装测试、导入测试 | [ ] |
| **EXE** | 启动测试、功能测试 | [ ] |
| **APK** | 安装测试、运行测试 | [ ] |

### 5. 发布流程

#### 发布前准备

1. **版本号更新**
   - 更新`pyproject.toml`中的版本号
   - 更新`AGENTS.md`中的版本号
   - 更新`CHANGELOG.md`添加新版本记录

2. **文档更新**
   - 更新README.md（如有必要）
   - 更新API文档（如有变更）
   - 更新模块文档（如有新功能）

3. **创建发布分支**
   ```powershell
   git checkout -b release/v0.9.8 develop
   ```

#### 发布步骤

```powershell
# 1. 确保所有测试通过
.\check.ps1

# 2. 确保构建成功
.\build.ps1

# 3. 合并到main分支
git checkout main
git merge release/v0.9.8

# 4. 创建标签
git tag -a v0.9.8 -m "Release v0.9.8"

# 5. 推送到远程
git push origin main --tags

# 6. 合并回develop分支
git checkout develop
git merge release/v0.9.8
git push origin develop

# 7. 删除发布分支
git branch -d release/v0.9.8
```

#### 发布后验证

- [ ] GitHub Release已创建
- [ ] 构建产物已上传
- [ ] 文档已更新
- [ ] CHANGELOG已更新

### 6. 快速检查脚本

创建快速检查脚本 `pre-release.ps1`：

```powershell
# pre-release.ps1
Write-Host "=== 发布前检查 ===" -ForegroundColor Cyan

# 1. 运行测试
Write-Host "`n[1/4] 运行测试..." -ForegroundColor Yellow
.\check.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "测试失败，请修复后再发布" -ForegroundColor Red
    exit 1
}

# 2. 检查分支
Write-Host "`n[2/4] 检查分支..." -ForegroundColor Yellow
$branch = git branch --show-current
if ($branch -ne "develop") {
    Write-Host "警告: 当前不在develop分支，当前分支: $branch" -ForegroundColor Yellow
}

# 3. 检查未提交的更改
Write-Host "`n[3/4] 检查未提交的更改..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "存在未提交的更改:" -ForegroundColor Yellow
    Write-Host $status
}

# 4. 构建测试
Write-Host "`n[4/4] 构建测试..." -ForegroundColor Yellow
.\build.ps1 -SkipApk
if ($LASTEXITCODE -ne 0) {
    Write-Host "构建失败，请修复后再发布" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== 检查完成 ===" -ForegroundColor Green
Write-Host "可以进行发布流程" -ForegroundColor Green
```

### 7. 常见问题处理

| 问题 | 解决方案 |
|------|----------|
| 测试失败 | 查看错误日志，修复相关代码 |
| 构建失败 | 检查依赖、配置、环境变量 |
| API不兼容 | 更新API版本，通知前端团队 |
| 移动端适配问题 | 检查AndroidManifest.xml、权限配置 |
| 文档缺失 | 补充相关文档，更新CHANGELOG |

---

## 项目规范

详细的开发规范请参考 [docs/standards.md](docs/standards.md)，以下是规范概要：

### 代码规范

#### Python 代码规范

- 使用 Ruff 进行代码格式化和检查
- 所有公开函数必须添加类型注解
- 使用 Google 风格的文档字符串

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划线 | `chat_agent.py` |
| 类 | 大驼峰 | `ChatAgent` |
| 函数 | 小写+下划线 | `send_message()` |
| 常量 | 大写+下划线 | `MAX_RETRY_COUNT` |
| 私有 | 前缀下划线 | `_internal_func()` |

#### 前端代码规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件 | 大驼峰 | `ChatView` |
| 文件 | 小写+连字符 | `chat-view.vue` |
| 函数 | 小驼峰 | `sendMessage()` |
| 常量 | 大写+下划线 | `MAX_RETRY_COUNT` |

### 文档规范

详细的文档规范请参考 [docs/standards.md](docs/standards.md)，以下是规范概要：

#### 文档类型

| 文档类型 | 文件名 | 位置 | 用途 |
|----------|--------|------|------|
| README | `README.md` | 项目根目录 | 项目总览、快速开始 |
| CHANGELOG | `CHANGELOG.md` | 项目根目录 | 版本更新记录 |
| 架构文档 | `architecture.md` | `docs/` | 系统架构设计 |
| API 文档 | `api.md` | `docs/` | API 接口文档 |
| 配置文档 | `configuration.md` | `docs/` | 配置选项说明 |
| 部署文档 | `deployment.md` | `docs/` | 部署指南 |
| 模块文档 | `*.md` | `docs/modules/` | 模块详细文档 |

#### README 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 项目名称和徽章 | 必须 | 项目标题、版本徽章、许可证徽章 |
| 项目简介 | 必须 | 一句话描述项目功能 |
| 功能特性 | 必须 | 核心功能列表 |
| 快速开始 | 必须 | 安装和运行步骤 |
| 文档链接 | 必须 | 详细文档链接 |
| 许可证 | 必须 | 开源许可证 |

#### CHANGELOG 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 版本号和日期 | 必须 | 格式: `## [版本号] - YYYY-MM-DD` |
| 变更类型 | 必须 | 新增/变更/弃用/移除/修复/安全 |
| 变更描述 | 必须 | 清晰描述变更内容 |

#### API 文档必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 接口描述 | 必须 | 接口功能说明 |
| 请求方法/路径 | 必须 | GET/POST/PUT/DELETE |
| 请求参数 | 必须 | 参数说明表格 |
| 响应格式 | 必须 | 成功和错误响应 |
| 状态码说明 | 必须 | HTTP 状态码含义 |

#### Markdown 格式规范

- Markdown 文档必须有一级标题和目录
- 代码块必须指定语言
- 表格必须有表头行和分隔行
- 链接使用相对路径

### Git 分支体系

项目采用 Git Flow 分支模型进行版本管理。

#### 分支类型

| 分支类型 | 命名规则 | 说明 | 生命周期 |
|----------|----------|------|----------|
| **main** | `main` | 生产分支，只接受合并请求 | 永久 |
| **develop** | `develop` | 开发分支，日常开发基础 | 永久 |
| **feature** | `feature/<name>` | 功能分支，开发新功能 | 临时 |
| **hotfix** | `hotfix/<name>` | 热修复分支，紧急修复 | 临时 |
| **release** | `release/<version>` | 发布分支，版本准备 | 临时 |

#### 分支操作流程

```powershell
# 1. 开始新功能开发
git checkout develop
git checkout -b feature/new-feature

# 2. 功能开发完成后合并
git checkout develop
git merge feature/new-feature
git branch -d feature/new-feature

# 3. 准备发布
git checkout -b release/v0.9.0 develop
# 进行版本号更新、文档完善等
git checkout main
git merge release/v0.9.0
git tag -a v0.9.0 -m "Release v0.9.0"
git checkout develop
git merge release/v0.9.0
git branch -d release/v0.9.0

# 4. 紧急修复
git checkout -b hotfix/urgent-fix main
# 修复完成后
git checkout main
git merge hotfix/urgent-fix
git tag -a v0.8.1 -m "Hotfix v0.8.1"
git checkout develop
git merge hotfix/urgent-fix
git branch -d hotfix/urgent-fix
```

#### 分支命名规范

| 类型 | 命名示例 | 说明 |
|------|----------|------|
| 功能分支 | `feature/agent-system` | 新增智能体系统功能 |
| 功能分支 | `feature/voice-interaction` | 新增语音交互功能 |
| 热修复分支 | `hotfix/memory-leak` | 修复内存泄漏问题 |
| 热修复分支 | `hotfix/api-crash` | 修复API崩溃问题 |
| 发布分支 | `release/v0.9.0` | v0.9.0版本发布准备 |

### 提交规范

项目采用 Conventional Commits 规范进行提交信息管理。

#### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| **feat** | 新功能 | `feat(agents): add agent registry system` |
| **fix** | Bug修复 | `fix(memory): fix memory leak in chat history` |
| **docs** | 文档更新 | `docs(api): update API documentation` |
| **style** | 代码格式（不影响功能） | `style: format code with ruff` |
| **refactor** | 重构（不新增功能也不修复Bug） | `refactor(llm): simplify gateway implementation` |
| **test** | 测试相关 | `test(todo): add unit tests for todo system` |
| **chore** | 构建/工具/依赖更新 | `chore(deps): update dependencies` |
| **perf** | 性能优化 | `perf(memory): optimize memory usage` |
| **ci** | CI/CD配置 | `ci: add GitHub Actions workflow` |
| **revert** | 回滚提交 | `revert: revert previous commit` |

#### Scope 范围

常用的 scope 包括：

| Scope | 说明 |
|-------|------|
| `agents` | 智能体系统 |
| `memory` | 记忆系统 |
| `todo` | Todo系统 |
| `llm` | LLM客户端/网关 |
| `im` | IM平台适配器 |
| `mcp` | MCP协议 |
| `web` | Web服务 |
| `frontend` | 前端UI |
| `api` | API接口 |
| `config` | 配置相关 |
| `deps` | 依赖更新 |
| `build` | 构建系统 |

#### 提交示例

```bash
# 新功能
git commit -m "feat(agents): add agent base class and registry"

# Bug修复
git commit -m "fix(memory): resolve memory leak in chat history storage"

# 文档更新
git commit -m "docs(architecture): update system architecture diagram"

# 重构
git commit -m "refactor(llm): simplify model gateway implementation"

# 带详细说明的提交
git commit -m "feat(voice): add voice interaction support

- Add ASR engine integration (Whisper, Baidu, Ali)
- Add TTS engine integration (Edge TTS, Baidu, Ali)
- Support real-time streaming processing
- Add multi-language support (zh/en/ja/ko)

Closes #123"
```

#### 提交最佳实践

1. **原子提交**: 每个提交只做一件事
2. **清晰描述**: 提交信息要清晰描述变更内容
3. **引用Issue**: 关联相关的Issue编号
4. **避免大提交**: 将大改动拆分为多个小提交
5. **测试先行**: 确保提交的代码通过测试

### 版本号规范

格式: `MAJOR.MINOR.PATCH`

#### 版本号更新时机

| 版本号 | 更新时机 | 示例场景 |
|--------|----------|----------|
| **MAJOR** | 不兼容的 API 变更 | 删除公开 API、修改函数签名、更改配置格式、数据库迁移 |
| **MINOR** | 向后兼容的功能新增 | 新增模块、新增 API 端点、新增配置选项、功能增强 |
| **PATCH** | 向后兼容的问题修复 | Bug 修复、性能优化、文档更新、依赖更新 |

#### MAJOR 版本更新条件

- 删除或重命名公开 API
- 不兼容的配置变更
- 数据库迁移
- Python 最低版本要求变更

#### MINOR 版本更新条件

- 新增模块或子模块
- 新增 API 端点
- 新增配置选项
- 功能增强

#### PATCH 版本更新条件

- Bug 修复
- 性能优化
- 文档更新
- 依赖更新

#### 预发布版本

| 类型 | 格式 | 说明 |
|------|------|------|
| Alpha | `0.8.0-alpha.1` | 内部测试版本 |
| Beta | `0.8.0-beta.1` | 公开测试版本 |
| RC | `0.8.0-rc.1` | 发布候选版本 |

### 测试规范

- 测试文件命名: `test_*.py`
- 测试类命名: `Test*`
- 测试方法命名: `test_*`
- 核心模块覆盖率 >= 80%

### 安全规范

- 禁止硬编码敏感信息
- 使用环境变量存储密钥
- 日志输出前脱敏处理
- 使用参数化查询防止 SQL 注入

---

## 版本历史

- **v0.9.7** (2026-04-05) - 知识库系统、工作流引擎、本地模型支持、角色卡系统、研究规划器、调试系统、成本追踪、虚拟密钥管理、视图系统、自我进化机制
- **v0.8.0** (2025-04-03) - 智能体系统、人工介入任务、日历管理、邮件收发、语音交互、浏览器自动化、PDF处理、分布式存储、LLM模型网关、移动端支持
- **v0.7.0** (2026-03-30) - 原生文档编辑器、原生视频编辑器、域系统、Kimi通道、斜杠菜单
- **v0.6.0** (2025-03-29) - LLM模块重构、设备ID系统、统一工具调用、Mate模式简化、Web UI斜杠命令、ClawHub集成
- **v0.5.0** (2025-03-29) - 任务四状态系统、UI优化、热更新功能
- **v0.4.0** (2025-03-28) - 架构重构、多智能体协作模式、微信通道
- **v0.3.2** (2025-03-27) - UI优化、暗色模式支持
- **v0.3.1** (2025-03-27) - Bug修复、代码优化、完整测试套件
- **v0.3.0** (2025-03-27) - 拟人化聊天智能体
- **v0.2.1** (2025-03-27) - Bug修复和优化
- **v0.2.0** (2025-03-27) - AI原生Todo系统、Mate模式、四级记忆
- **v0.1.0** (2025-03-27) - 记忆系统优化、自我学习
- **v0.0.1** (2025-03-20) - 项目初始化

---

## 获取帮助

- 查看 [README.md](README.md) 了解项目概况
- 查看 [docs/architecture.md](docs/architecture.md) 了解系统架构
- 查看 [CHANGELOG.md](CHANGELOG.md) 了解最新更新
- 查看各模块文档了解详细功能

---

## 贡献

欢迎提交Issue和Pull Request！

**许可证**: GNU General Public License v3.0 (GPL-3.0)
