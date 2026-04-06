# PyAgent - Python智能体框架

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-happy--everyday--everyweek%2Fpyagent-black.svg)](https://github.com/happy-everyday-everyweek/pyagent)

PyAgent是一个企业级Python智能体框架，支持多平台IM集成、多智能体协作、ReAct推理引擎、MCP协议等高级特性。

---

## 核心特性

| 类别 | 特性 |
|------|------|
| **架构** | 多智能体架构（交互模块+执行模块）、ReAct推理引擎、热更新 |
| **IM支持** | QQ、钉钉、飞书、企业微信、微信、Kimi |
| **记忆系统** | 四级记忆架构（日常/周度/月度/季度）、项目记忆域 |
| **任务管理** | AI原生Todo系统、人工任务系统、日历管理 |
| **文档处理** | 原生文档编辑器（Word/Excel/PPT）、PDF处理 |
| **多媒体** | 原生视频编辑器、语音交互（ASR/TTS） |
| **自动化** | 浏览器自动化、工作流引擎 |
| **扩展** | MCP协议、ClawHub Skill、知识库系统 |

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+ (前端开发)
- 8GB+ 内存

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd pyagent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置API密钥
```

### 运行

```bash
# Web模式
python -m src.main --mode web --host 0.0.0.0 --port 8000

# IM模式
python -m src.main --mode im

# 同时运行Web和IM
python -m src.main --mode both
```

访问 http://localhost:8000 查看Web界面。

---

## 配置

### 必需配置

编辑 `.env` 文件配置LLM API密钥：

```env
# OpenAI
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o

# 或 DeepSeek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-chat

# 或 智谱AI
ZHIPU_API_KEY=your-key
ZHIPU_MODEL=glm-4
```

### 配置文件

| 配置 | 路径 | 说明 |
|------|------|------|
| 模型配置 | `config/models.yaml` | LLM模型配置 |
| MCP配置 | `config/mcp.json` | MCP服务器配置 |
| 记忆系统 | `config/memory.yaml` | 记忆系统配置 |
| 拟人化 | `config/persona.yaml` | 拟人化配置 |

详细配置请参考 [docs/configuration.md](docs/configuration.md)。

---

## 项目结构

```
pyagent/
├── src/                    # 源代码
│   ├── interaction/        # 交互模块
│   ├── execution/          # 执行模块
│   ├── agents/             # 智能体系统
│   ├── memory/             # 记忆系统
│   ├── todo/               # Todo系统
│   ├── llm/                # LLM客户端
│   ├── im/                 # IM适配器
│   └── web/                # Web服务
├── frontend/               # 前端代码(Vue.js)
├── config/                 # 配置文件
├── docs/                   # 文档目录
├── tests/                  # 测试套件
└── data/                   # 数据目录
```

---

## 自动化脚本

项目提供了一键自动化脚本，简化开发和构建流程：

### 代码检查

```powershell
# 一键运行所有检查（测试 + 代码风格 + 类型检查 + 安全检查）
.\check.ps1
```

### 构建

```powershell
# 一键构建（wheel + EXE + APK）
.\build.ps1
```

---

## 文档索引

### 入门

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 项目总览 |
| [CHANGELOG.md](CHANGELOG.md) | 版本更新记录 |
| [AGENTS.md](AGENTS.md) | 开发者指南 |

### 架构与开发

| 文档 | 说明 |
|------|------|
| [docs/architecture.md](docs/architecture.md) | 系统架构 |
| [docs/api.md](docs/api.md) | API文档 |
| [docs/configuration.md](docs/configuration.md) | 配置说明 |
| [docs/deployment.md](docs/deployment.md) | 部署指南 |
| [docs/development.md](docs/development.md) | 开发指南 |
| [docs/testing.md](docs/testing.md) | 测试文档 |

### 模块文档

详细模块文档位于 `docs/modules/` 目录，包括：
- [Todo系统](docs/modules/todo-system.md)
- [记忆系统](docs/modules/memory-system.md)
- [拟人化系统](docs/modules/persona-system.md)
- [智能体系统](docs/modules/agent-system.md)
- [LLM客户端](docs/modules/llm-client-v2.md)
- [更多模块...](docs/modules/)

---

## 许可证

GNU General Public License v3.0 - 详见 [LICENSE](LICENSE) 文件

---

**PyAgent - 让AI更智能，让协作更高效**
