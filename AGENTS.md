# PyAgent AI 开发指南

本文档面向 AI 助手，提供项目架构、开发工作流和代码规范指南。

---

## 项目架构

本项目采用**三端架构**：Web端、移动端、桌面端，共享统一后端服务。

```
PyAgent
├── 后端 (统一)
│   └── src/                    # Python 后端源代码
│       ├── interaction/        # 交互模块
│       ├── execution/          # 执行模块
│       ├── agents/             # 智能体系统
│       ├── memory/             # 记忆系统
│       ├── llm/                # LLM客户端
│       └── ...
│
├── 前端 (三端独立)
│   ├── frontend/               # Web端 (Vue.js)
│   ├── android/                # 移动端 (原生Android)
│   └── desktop/                # 桌面端 (待实现)
│
└── 共享资源
    ├── config/                 # 配置文件
    ├── skills/                 # 技能目录
    └── docs/                   # 文档目录
```

### 三端说明

| 端 | 技术栈 | 位置 | 构建输出 |
|---|--------|------|----------|
| Web端 | Vue.js | `frontend/` | 静态文件 |
| 移动端 | 原生Android | `android/` | APK文件 |
| 桌面端 | 待实现 | `desktop/` | EXE文件 |

**重要原则**：
- 后端代码统一，所有端共享相同的 API 接口
- 每个端有自己的前端实现，需独立适配 UI
- 修改任何文件后必须更新版本号

---

## 开发工作流

### 新增功能流程

若你需要新增功能，请在发布前按照以下流程进行检查：

#### 1. 多端兼容性检查
- 项目支持移动端、桌面端和 Web 端
- 确保你的每一次更新兼容各个端
- 为每个端提供适配的 UI 界面
- 项目使用统一的后端，但每个端有自己的不同的前端

#### 2. 运行自动测试
- 运行位于项目根目录下的自动测试脚本：`pytest`
- 无论有何种问题，是否由你新增模块导致，你都需要对其进行修复

#### 3. 代码提交
- 提交到 `develop` 分支
- 遵循提交规范：`<type>(<scope>): <subject>`

#### 4. 构建测试
- 运行构建：`python -m build`
- 测试是否还有问题

#### 5. 修复问题
- 如果构建失败了，修复问题

#### 6. 创建 Release
- 创建新的 Releases
- 将构建好的 EXE 文件和 APK 文件上传

#### 7. 合并到主分支
- 创建一个 PR，把 `develop` 分支合并到 `main` 分支

### 修复问题流程

修复问题与新增功能工作流类似，遵循相同的检查和测试步骤。

---

## 代码规范

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划线 | `chat_agent.py` |
| 类 | 大驼峰 | `ChatAgent` |
| 函数 | 小写+下划线 | `send_message()` |
| 常量 | 大写+下划线 | `MAX_RETRY_COUNT` |

### 提交规范

```
<type>(<scope>): <subject>

类型: feat/fix/docs/style/refactor/test/chore/perf
范围: agents/memory/todo/llm/im/mcp/web/api/config
```

---

## 版本管理

### 版本号规范

格式：`MAJOR.MINOR.PATCH`

| 版本号 | 更新时机 |
|--------|----------|
| MAJOR | 不兼容的API变更 |
| MINOR | 向后兼容的功能新增 |
| PATCH | 向后兼容的问题修复 |

### 每次修改必须更新版本

**重要**：每次修改任何文件都必须更新版本号，并记录到 CHANGELOG.md。

---

## 构建输出

| 构建类型 | 输出路径 |
|----------|----------|
| Wheel包 | `dist/pyagent-*.whl` |
| EXE | `dist/exe/PyAgent/PyAgent.exe` |
| APK | `android/app/build/outputs/apk/` |

---

## 快速命令

```powershell
# 运行测试
pytest

# 构建项目
python -m build

# 代码检查
ruff check .
```

---

**注意**：本文档面向 AI 助手，人类开发者请参考 docs/development.md
