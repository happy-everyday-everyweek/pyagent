# PyAgent 开发者指南

本文档面向开发者，提供项目结构、开发规范、构建流程和版本管理指南。

---

## 项目结构

```
pyagent/
├── src/                    # 源代码
│   ├── interaction/        # 交互模块 - 拟人化聊天、情感系统
│   ├── execution/          # 执行模块 - ReAct引擎、任务执行
│   ├── agents/             # 智能体系统 - Agent基类、注册中心
│   ├── human_tasks/        # 人工任务系统
│   ├── calendar/           # 日历管理
│   ├── email/              # 邮件客户端
│   ├── voice/              # 语音交互（ASR/TTS）
│   ├── browser/            # 浏览器自动化
│   ├── pdf/                # PDF处理
│   ├── storage/            # 分布式存储
│   ├── mobile/             # 移动端支持
│   ├── memory/             # 记忆系统
│   ├── todo/               # Todo系统
│   ├── llm/                # LLM客户端/网关
│   ├── im/                 # IM平台适配器
│   ├── mcp/                # MCP协议支持
│   └── web/                # Web服务
├── frontend/               # 前端代码(Vue.js)
├── config/                 # 配置文件
├── docs/                   # 文档目录
├── tests/                  # 测试套件
├── data/                   # 数据目录
├── skills/                 # 技能目录
└── android/                # Android项目
```

---

## 核心模块

| 模块 | 位置 | 说明 |
|------|------|------|
| 交互模块 | `src/interaction/` | 拟人化聊天、情感表达、行为规划 |
| 执行模块 | `src/execution/` | ReAct引擎、任务分解、多智能体协作 |
| 记忆系统 | `src/memory/` | 四级记忆架构、项目记忆域 |
| Todo系统 | `src/todo/` | 三级任务管理、自动验收 |
| LLM客户端 | `src/llm/` | 多模型支持、分级模型、网关 |
| 智能体系统 | `src/agents/` | Agent基类、注册中心、执行器 |

详细文档请参考 `docs/modules/` 目录。

---

## 配置文件

| 配置 | 路径 | 说明 |
|------|------|------|
| 环境变量 | `.env` | API密钥、基础配置 |
| 模型配置 | `config/models.yaml` | LLM模型配置 |
| MCP配置 | `config/mcp.json` | MCP服务器配置 |
| Todo配置 | `config/todo.yaml` | Todo系统配置 |
| 记忆系统 | `config/memory.yaml` | 记忆系统配置 |
| 拟人化 | `config/persona.yaml` | 拟人化配置 |

---

## 开发规范

### 代码规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划线 | `chat_agent.py` |
| 类 | 大驼峰 | `ChatAgent` |
| 函数 | 小写+下划线 | `send_message()` |
| 常量 | 大写+下划线 | `MAX_RETRY_COUNT` |

- 使用 Ruff 进行代码格式化和检查
- 所有公开函数必须添加类型注解
- 使用 Google 风格的文档字符串

### Git 分支

| 分支类型 | 命名规则 | 说明 |
|----------|----------|------|
| main | `main` | 生产分支 |
| develop | `develop` | 开发分支 |
| feature | `feature/<name>` | 功能分支 |
| hotfix | `hotfix/<name>` | 热修复分支 |
| release | `release/<version>` | 发布分支 |

### 提交规范

采用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

类型: feat/fix/docs/style/refactor/test/chore/perf
范围: agents/memory/todo/llm/im/mcp/web/api/config
```

示例：
- `feat(agents): add agent registry system`
- `fix(memory): resolve memory leak in chat history`
- `docs(api): update API documentation`

---

## 自动化脚本

项目提供了一键自动化脚本，简化开发和构建流程：

### 代码检查

```powershell
# 一键运行所有检查（测试 + 代码风格 + 类型检查 + 安全检查）
.\check.ps1

# 可选参数
.\check.ps1 -SkipTests      # 跳过测试
.\check.ps1 -Fix            # 自动修复代码风格问题
.\check.ps1 -Coverage       # 生成覆盖率报告
```

### 构建

```powershell
# 一键构建（wheel + EXE + APK）
.\build.ps1

# 可选参数
.\build.ps1 -SkipExe        # 跳过EXE构建
.\build.ps1 -SkipApk        # 跳过APK构建
.\build.ps1 -NoClean        # 增量构建
```

---

## 测试

```bash
# 运行所有测试
pytest

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

测试文件命名：`test_*.py`，测试类命名：`Test*`，测试函数命名：`test_*`

---

## 构建

### 输出位置

| 构建类型 | 输出路径 |
|----------|----------|
| Wheel包 | `dist/pyagent-*.whl` |
| EXE | `dist/exe/PyAgent/PyAgent.exe` |
| APK | `android/app/build/outputs/apk/` |

---

## 发布流程

### 发布前检查

1. 运行一键检查：`.\check.ps1`
2. 运行一键构建：`.\build.ps1`
3. 更新 CHANGELOG.md

### 发布步骤

```powershell
# 1. 创建发布分支
git checkout -b release/vX.X.X develop

# 2. 更新 CHANGELOG.md

# 3. 合并到main
git checkout main
git merge release/vX.X.X
git tag -a vX.X.X -m "Release vX.X.X"
git push origin main --tags

# 4. 合并回develop
git checkout develop
git merge release/vX.X.X
git push origin develop

# 5. 删除发布分支
git branch -d release/vX.X.X
```

---

## 版本号规范

格式：`MAJOR.MINOR.PATCH`

| 版本号 | 更新时机 |
|--------|----------|
| MAJOR | 不兼容的API变更 |
| MINOR | 向后兼容的功能新增 |
| PATCH | 向后兼容的问题修复 |

---

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 架构设计 | [docs/architecture.md](docs/architecture.md) | 系统架构 |
| API文档 | [docs/api.md](docs/api.md) | REST API、WebSocket |
| 配置文档 | [docs/configuration.md](docs/configuration.md) | 配置选项 |
| 部署文档 | [docs/deployment.md](docs/deployment.md) | 部署指南 |
| 开发文档 | [docs/development.md](docs/development.md) | 开发指南 |
| 测试文档 | [docs/testing.md](docs/testing.md) | 测试套件 |
| 模块文档 | [docs/modules/](docs/modules/) | 各模块详细文档 |

---

**许可证**: GNU General Public License v3.0 (GPL-3.0)
