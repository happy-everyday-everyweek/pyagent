# PyAgent 项目规范文档 v0.8.0

本文档定义了 PyAgent 项目的所有开发规范，包括代码规范、文档规范、格式规范、提交规范等。

---

## 目录

- [一、代码规范](#一代码规范)
  - [1. Python 代码规范](#1-python-代码规范)
  - [2. TypeScript/Vue 代码规范](#2-typescriptvue-代码规范)
  - [3. Kotlin 代码规范](#3-kotlin-代码规范)
- [二、文档规范](#二文档规范)
  - [1. 文档类型总览](#1-文档类型总览)
  - [2. README 文档规范](#2-readme-文档规范)
  - [3. CHANGELOG 文档规范](#3-changelog-文档规范)
  - [4. 架构文档规范](#4-架构文档规范)
  - [5. API 文档规范](#5-api-文档规范)
  - [6. 模块文档规范](#6-模块文档规范)
  - [7. 配置文档规范](#7-配置文档规范)
  - [8. 部署文档规范](#8-部署文档规范)
  - [9. 故障排查文档规范](#9-故障排查文档规范)
  - [10. Markdown 通用格式规范](#10-markdown-通用格式规范)
- [三、格式规范](#三格式规范)
  - [1. 文件命名规范](#1-文件命名规范)
  - [2. 目录结构规范](#2-目录结构规范)
  - [3. 配置文件规范](#3-配置文件规范)
- [四、提交规范](#四提交规范)
  - [1. Git 提交规范](#1-git-提交规范)
  - [2. 分支管理规范](#2-分支管理规范)
  - [3. 版本号规范](#3-版本号规范)
- [五、测试规范](#五测试规范)
  - [1. 单元测试规范](#1-单元测试规范)
  - [2. 集成测试规范](#2-集成测试规范)
  - [3. 测试命名规范](#3-测试命名规范)
- [六、安全规范](#六安全规范)
  - [1. 敏感信息处理](#1-敏感信息处理)
  - [2. 输入验证规范](#2-输入验证规范)
  - [3. 权限控制规范](#3-权限控制规范)
- [七、日志规范](#七日志规范)
  - [1. 日志级别规范](#1-日志级别规范)
  - [2. 日志格式规范](#2-日志格式规范)
  - [3. 日志存储规范](#3-日志存储规范)
- [八、注释规范](#八注释规范)
  - [1. Python 注释规范](#1-python-注释规范)
  - [2. 前端注释规范](#2-前端注释规范)
  - [3. 配置注释规范](#3-配置注释规范)

---

## 一、代码规范

### 1. Python 代码规范

#### 1.1 基本风格

项目使用 Ruff 进行代码格式化和检查，遵循 PEP 8 规范。

```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .

# 自动修复
ruff check . --fix
```

#### 1.2 类型注解

所有公开函数必须添加类型注解：

```python
from typing import Optional, Dict, Any, List
from collections.abc import Callable

def process_message(
    message: str,
    user_id: str,
    context: Optional[Dict[str, Any]] = None,
    callbacks: List[Callable[[str], None]] | None = None
) -> str:
    """处理消息"""
    pass
```

#### 1.3 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划线 | `chat_agent.py` |
| 包 | 小写+下划线 | `interaction/` |
| 类 | 大驼峰 | `ChatAgent` |
| 函数 | 小写+下划线 | `send_message()` |
| 方法 | 小写+下划线 | `_internal_func()` |
| 常量 | 大写+下划线 | `MAX_RETRY_COUNT` |
| 变量 | 小写+下划线 | `user_name` |
| 私有属性 | 前缀单下划线 | `_internal_state` |
| 保护属性 | 前缀单下划线 | `_protected_value` |
| 特殊方法 | 前后双下划线 | `__init__` |

#### 1.4 导入规范

```python
# 标准库
import os
import sys
from typing import Optional, Dict, Any
from collections.abc import Callable

# 第三方库
import pytest
from fastapi import FastAPI, HTTPException

# 本地模块
from src.llm.client import LLMClient
from src.memory.types import MemoryLevel
```

导入顺序：
1. 标准库（按字母排序）
2. 第三方库（按字母排序）
3. 本地模块（按字母排序）
4. 各组之间空一行

#### 1.5 类定义规范

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class AgentStatus(Enum):
    """智能体状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentCapability:
    """智能体能力定义"""
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


class BaseVerticalAgent(ABC):
    """垂类智能体基类"""
    
    name: str = "base_agent"
    description: str = "基础智能体"
    
    def __init__(
        self,
        capabilities: list[AgentCapability],
        llm_client: Any | None = None
    ):
        self.capabilities = capabilities
        self.llm_client = llm_client
        self._status = AgentStatus.IDLE
        self._initialized = False
    
    @property
    def status(self) -> AgentStatus:
        """获取当前状态"""
        return self._status
    
    @abstractmethod
    async def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """处理请求"""
        pass
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self._status.value,
        }
```

#### 1.6 异步函数规范

```python
import asyncio
from typing import AsyncGenerator

async def fetch_data(url: str) -> dict[str, Any]:
    """异步获取数据"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def process_batch(items: list[str]) -> list[dict]:
    """并行处理批量数据"""
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)

async def stream_results(count: int) -> AsyncGenerator[str, None]:
    """异步生成器"""
    for i in range(count):
        await asyncio.sleep(0.1)
        yield f"result_{i}"
```

#### 1.7 异常处理规范

```python
class PyAgentError(Exception):
    """基础异常类"""
    pass


class ValidationError(PyAgentError):
    """验证错误"""
    pass


class LLMError(PyAgentError):
    """LLM 相关错误"""
    pass


async def safe_process(data: dict[str, Any]) -> dict[str, Any]:
    """安全的处理函数"""
    try:
        if not data:
            raise ValidationError("数据不能为空")
        
        result = await process_internal(data)
        return {"success": True, "data": result}
    
    except ValidationError as e:
        logger.warning(f"验证失败: {e}")
        return {"success": False, "error": str(e)}
    
    except LLMError as e:
        logger.error(f"LLM 错误: {e}")
        return {"success": False, "error": "服务暂时不可用"}
    
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        return {"success": False, "error": "内部错误"}
```

#### 1.8 工具类规范

所有工具必须继承 `UnifiedTool` 基类：

```python
from abc import abstractmethod
from src.tools.base import UnifiedTool, ToolContext, ToolResult

class MyTool(UnifiedTool):
    """我的自定义工具"""
    
    name = "my_tool"
    description = "工具描述"
    
    async def activate(self, context: ToolContext) -> bool:
        """激活工具，初始化资源"""
        return True
    
    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """执行工具逻辑"""
        try:
            result = await self._do_work(**kwargs)
            return ToolResult(
                success=True,
                output=result,
                data={"details": "..."}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def dormant(self, context: ToolContext) -> bool:
        """休眠工具，释放资源"""
        return True
    
    async def _do_work(self, **kwargs) -> str:
        """内部工作方法"""
        pass
```

---

### 2. TypeScript/Vue 代码规范

#### 2.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | 小写+连字符 | `chat-view.vue` |
| 组件 | 大驼峰 | `ChatView` |
| 函数 | 小驼峰 | `sendMessage()` |
| 变量 | 小驼峰 | `userName` |
| 常量 | 大写+下划线 | `MAX_RETRY_COUNT` |
| 接口 | 大驼峰+I前缀 | `IMessage` |
| 类型 | 大驼峰 | `MessageType` |

#### 2.2 Vue 组件规范

```vue
<template>
  <div class="chat-view">
    <div v-for="message in messages" :key="message.id" class="message">
      {{ message.content }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Message } from '@/types'

const props = defineProps<{
  chatId: string
}>()

const emit = defineEmits<{
  (e: 'send', message: string): void
  (e: 'close'): void
}>()

const messages = ref<Message[]>([])
const isLoading = ref(false)

const messageCount = computed(() => messages.value.length)

onMounted(async () => {
  await loadMessages()
})

async function loadMessages(): Promise<void> {
  isLoading.value = true
  try {
    messages.value = await fetchMessages(props.chatId)
  } finally {
    isLoading.value = false
  }
}

async function fetchMessages(chatId: string): Promise<Message[]> {
  // 实现
  return []
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.message {
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 8px;
}
</style>
```

#### 2.3 TypeScript 类型规范

```typescript
// types/index.ts

export enum MessageType {
  TEXT = 'text',
  IMAGE = 'image',
  FILE = 'file',
  SYSTEM = 'system'
}

export interface IMessage {
  id: string
  content: string
  type: MessageType
  senderId: string
  timestamp: number
  metadata?: Record<string, unknown>
}

export interface IChatSession {
  id: string
  title: string
  messages: IMessage[]
  createdAt: Date
  updatedAt: Date
}

export type MessageHandler = (message: IMessage) => void

export interface IChatService {
  sendMessage(chatId: string, content: string): Promise<IMessage>
  getMessages(chatId: string): Promise<IMessage[]>
  onMessage(handler: MessageHandler): () => void
}
```

---

### 3. Kotlin 代码规范

#### 3.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | 大驼峰 | `MainActivity.kt` |
| 类 | 大驼峰 | `MainActivity` |
| 函数 | 小驼峰 | `sendMessage()` |
| 变量 | 小驼峰 | `userName` |
| 常量 | 全大写+下划线 | `MAX_RETRY_COUNT` |

#### 3.2 类定义规范

```kotlin
package com.pyagent.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier

class MainActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PyAgentTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainScreen()
                }
            }
        }
    }
}
```

---

## 二、文档规范

### 1. 文档类型总览

| 文档类型 | 文件名 | 位置 | 用途 |
|----------|--------|------|------|
| README | `README.md` | 项目根目录 | 项目总览、快速开始 |
| CHANGELOG | `CHANGELOG.md` | 项目根目录 | 版本更新记录 |
| 架构文档 | `architecture.md` | `docs/` | 系统架构设计 |
| API 文档 | `api.md` | `docs/` | API 接口文档 |
| 配置文档 | `configuration.md` | `docs/` | 配置选项说明 |
| 部署文档 | `deployment.md` | `docs/` | 部署指南 |
| 开发文档 | `development.md` | `docs/` | 开发指南 |
| 测试文档 | `testing.md` | `docs/` | 测试说明 |
| 规范文档 | `standards.md` | `docs/` | 开发规范 |
| 模块文档 | `*.md` | `docs/modules/` | 模块详细文档 |
| 故障排查 | `troubleshooting.md` | `docs/` | 问题排查指南 |
| 最佳实践 | `best-practices.md` | `docs/` | 最佳实践指南 |

---

### 2. README 文档规范

#### 2.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 项目名称和徽章 | 必须 | 项目标题、版本徽章、许可证徽章 |
| 项目简介 | 必须 | 一句话描述项目功能 |
| 功能特性 | 必须 | 核心功能列表 |
| 快速开始 | 必须 | 安装和运行步骤 |
| 环境要求 | 必须 | 运行环境要求 |
| 安装步骤 | 必须 | 详细安装指南 |
| 基本用法 | 必须 | 简单使用示例 |
| 配置说明 | 推荐 | 基本配置说明 |
| 文档链接 | 必须 | 详细文档链接 |
| 贡献指南 | 推荐 | 如何贡献代码 |
| 许可证 | 必须 | 开源许可证 |

#### 2.2 README 模板

```markdown
# 项目名称

[![版本](https://img.shields.io/badge/version-0.8.0-blue.svg)](CHANGELOG.md)
[![许可证](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)]()

简短的项目描述，说明项目的主要功能和用途。

## 功能特性

- 功能一：功能描述
- 功能二：功能描述
- 功能三：功能描述

## 环境要求

- Python 3.10+
- Node.js 18+ (前端开发)
- 其他依赖...

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/user/project.git
cd project

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置
vim .env
```

### 运行

```bash
python -m src.main
```

## 基本用法

```python
from src.module import Client

client = Client()
result = client.do_something()
print(result)
```

## 文档

- [架构文档](docs/architecture.md)
- [API 文档](docs/api.md)
- [配置文档](docs/configuration.md)
- [部署文档](docs/deployment.md)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 GPL-3.0 许可证 - 详见 [LICENSE](LICENSE) 文件。
```

---

### 3. CHANGELOG 文档规范

#### 3.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 版本号和日期 | 必须 | 格式: `## [版本号] - YYYY-MM-DD` |
| 变更类型 | 必须 | 新增/变更/弃用/移除/修复/安全 |
| 变更描述 | 必须 | 清晰描述变更内容 |
| 兼容性说明 | 推荐 | 版本兼容性信息 |
| 升级指南 | 推荐 | 版本升级步骤 |

#### 3.2 变更类型说明

| 类型 | 说明 |
|------|------|
| 新增 (Added) | 新增功能 |
| 变更 (Changed) | 现有功能的变更 |
| 弃用 (Deprecated) | 即将移除的功能 |
| 移除 (Removed) | 已移除的功能 |
| 修复 (Fixed) | Bug 修复 |
| 安全 (Security) | 安全相关修复 |

#### 3.3 CHANGELOG 模板

```markdown
# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [0.8.0] - 2026-04-05

### 新增功能

- 新增功能一的描述
- 新增功能二的描述

### 变更

- 变更内容一的描述
- 变更内容二的描述

### 弃用

- 弃用功能一的描述（将在 v0.9.0 移除）

### 移除

- 移除功能一的描述

### 修复

- 修复问题一的描述
- 修复问题二的描述

### 安全

- 安全修复一的描述

---

## [0.7.0] - 2026-03-30

### 新增功能

...

---

## 版本兼容性说明

| 版本 | 兼容性 |
|------|--------|
| v0.8.0 | 不兼容 v0.7.x |
| v0.7.0 | 兼容 v0.6.x |

### 升级指南

#### 从 v0.7.x 升级到 v0.8.0

1. 备份数据目录
2. 更新代码到 v0.8.0
3. 添加新配置文件
4. 重启服务
```

---

### 4. 架构文档规范

#### 4.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 概述 | 必须 | 系统整体介绍 |
| 系统架构图 | 必须 | 架构示意图 |
| 模块说明 | 必须 | 各模块职责 |
| 数据流图 | 推荐 | 数据流转过程 |
| 技术栈 | 必须 | 使用的技术 |
| 设计决策 | 推荐 | 重要设计决策说明 |

#### 4.2 架构文档模板

```markdown
# 系统架构文档

## 概述

简要描述系统的整体架构设计思路和核心特点。

## 系统架构图

\`\`\`
┌─────────────────────────────────────────────────────────┐
│                      前端层 (Frontend)                    │
│                    Vue.js 3 + TypeScript                  │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                      API 网关层                           │
│                    FastAPI + WebSocket                    │
└─────────────────────────────────────────────────────────┘
                              │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   交互模块       │ │   执行模块       │ │   记忆模块       │
│  interaction    │ │   execution     │ │    memory       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
\`\`\`

## 核心模块

### 交互模块 (Interaction)

**职责**: 处理用户交互，生成自然语言回复

**位置**: `src/interaction/`

**核心组件**:
- 心流聊天核心 (`heart_flow/`)
- 个性系统 (`persona/`)
- 动作规划器 (`planner/`)
- 回复生成器 (`reply/`)

### 执行模块 (Execution)

**职责**: 执行具体任务，调用工具

**位置**: `src/execution/`

**核心组件**:
- ReAct 推理引擎 (`react_engine.py`)
- 任务管理 (`task.py`)
- 规划智能体 (`planner.py`)

## 数据流

\`\`\`
用户消息 → IM适配器 → 意图分析 → 路由分发
    → 交互模块/执行模块 → LLM调用 → 回复生成 → IM适配器 → 用户
\`\`\`

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Vue.js | 3.x |
| 后端 | FastAPI | 0.100+ |
| 数据库 | SQLite/PostgreSQL | - |
| 缓存 | Redis | 7.x |
| 消息队列 | - | - |

## 设计决策

### 决策一：采用多智能体架构

**背景**: 需要支持复杂任务的并行处理

**决策**: 采用交互模块 + 执行模块的双模块架构

**影响**: 提高了任务处理效率，但增加了系统复杂度
```

---

### 5. API 文档规范

#### 5.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 接口描述 | 必须 | 接口功能说明 |
| 请求方法 | 必须 | GET/POST/PUT/DELETE |
| 请求路径 | 必须 | API 路径 |
| 请求参数 | 必须 | 参数说明表格 |
| 请求示例 | 必须 | JSON 示例 |
| 响应格式 | 必须 | 成功和错误响应 |
| 响应示例 | 必须 | JSON 示例 |
| 状态码说明 | 必须 | HTTP 状态码含义 |
| 调用示例 | 推荐 | curl/代码示例 |

#### 5.2 API 文档模板

```markdown
# API 文档

## 概述

API 基础信息：
- 基础 URL: `http://localhost:8000`
- API 版本: `v1`
- 认证方式: Bearer Token

## 认证

所有 API 请求需要在 Header 中携带 Token：

\`\`\`
Authorization: Bearer <your_token>
\`\`\`

---

## 消息接口

### 发送消息

发送消息到指定聊天。

**请求**

\`\`\`
POST /api/v1/messages
\`\`\`

**请求头**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Content-Type | string | 是 | application/json |
| Authorization | string | 是 | Bearer Token |

**请求体**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| chat_id | string | 是 | - | 聊天ID，格式: chat_xxx |
| content | string | 是 | - | 消息内容，最大 10000 字符 |
| message_type | string | 否 | text | 消息类型: text/image/file |

**请求示例**

\`\`\`json
{
  "chat_id": "chat_123",
  "content": "Hello, World!",
  "message_type": "text"
}
\`\`\`

**响应**

成功响应 (200):

\`\`\`json
{
  "success": true,
  "data": {
    "message_id": "msg_xxx",
    "chat_id": "chat_123",
    "content": "Hello, World!",
    "timestamp": 1234567890
  }
}
\`\`\`

错误响应 (400):

\`\`\`json
{
  "success": false,
  "error": {
    "code": "INVALID_CHAT_ID",
    "message": "聊天ID格式无效"
  }
}
\`\`\`

**状态码说明**

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**调用示例**

\`\`\`bash
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"chat_id": "chat_123", "content": "Hello"}'
\`\`\`

\`\`\`python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/messages",
    headers={"Authorization": "Bearer your_token"},
    json={"chat_id": "chat_123", "content": "Hello"}
)
print(response.json())
\`\`\`
```

---

### 6. 模块文档规范

#### 6.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 模块概述 | 必须 | 模块功能简介 |
| 快速开始 | 必须 | 基本使用示例 |
| 安装说明 | 必须 | 依赖安装 |
| API 参考 | 必须 | 类和方法说明 |
| 配置说明 | 必须 | 配置文件说明 |
| 使用示例 | 必须 | 完整示例代码 |
| 注意事项 | 推荐 | 使用注意点 |
| 相关文档 | 推荐 | 相关链接 |

#### 6.2 模块文档模板

```markdown
# 模块名称

## 概述

简要描述模块的功能、用途和核心特性。

**版本**: v1.0.0

**位置**: `src/module_name/`

## 快速开始

\`\`\`python
from src.module_name import ModuleClass

# 创建实例
client = ModuleClass(config={"key": "value"})

# 基本使用
result = client.do_something("input")
print(result)
\`\`\`

## 安装

\`\`\`bash
# 安装基础依赖
pip install pyagent[module_name]

# 或安装完整版
pip install pyagent[all]
\`\`\`

## API 参考

### ModuleClass

模块主类，提供核心功能。

**初始化参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| config | dict | {} | 配置字典 |
| api_key | str | None | API 密钥 |

**属性**

| 属性 | 类型 | 说明 |
|------|------|------|
| name | str | 模块名称 |
| version | str | 模块版本 |

**方法**

#### do_something(input: str) -> str

执行某项操作。

**参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| input | str | 是 | 输入内容 |

**返回值**

返回处理结果字符串。

**异常**

| 异常 | 说明 |
|------|------|
| ValidationError | 输入验证失败 |
| RuntimeError | 执行失败 |

**示例**

\`\`\`python
result = client.do_something("hello")
# 输出: "Result: hello"
\`\`\`

## 配置

配置文件位置: `config/module_name.yaml`

\`\`\`yaml
# 模块配置
module_name:
  # 必填配置
  api_key: "your-api-key"
  
  # 可选配置
  timeout: 30
  retry_count: 3
\`\`\`

## 完整示例

\`\`\`python
import asyncio
from src.module_name import ModuleClass

async def main():
    # 初始化
    client = ModuleClass(
        config={
            "api_key": "your-key",
            "timeout": 30
        }
    )
    
    # 执行操作
    result = await client.async_operation("input")
    print(f"结果: {result}")
    
    # 清理资源
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
\`\`\`

## 注意事项

1. 注意事项一
2. 注意事项二

## 相关文档

- [相关模块](related-module.md)
- [配置文档](../configuration.md)
```

---

### 7. 配置文档规范

#### 7.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 配置文件列表 | 必须 | 所有配置文件位置 |
| 环境变量 | 必须 | 环境变量说明 |
| 配置项说明 | 必须 | 每个配置项详细说明 |
| 默认值 | 必须 | 配置项默认值 |
| 配置示例 | 必须 | 完整配置示例 |

#### 7.2 配置文档模板

```markdown
# 配置文档

## 概述

本文档说明 PyAgent 的所有配置选项。

## 配置文件位置

| 配置文件 | 位置 | 说明 |
|----------|------|------|
| 环境变量 | `.env` | API 密钥、敏感信息 |
| 模型配置 | `config/models.yaml` | LLM 模型配置 |
| MCP 配置 | `config/mcp.json` | MCP 服务器配置 |
| Todo 配置 | `config/todo.yaml` | Todo 系统配置 |

## 环境变量

创建 `.env` 文件：

\`\`\`bash
# API 密钥（必填）
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=ds-xxx

# 服务配置（可选）
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
\`\`\`

### 环境变量说明

| 变量名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| OPENAI_API_KEY | string | 是 | - | OpenAI API 密钥 |
| DEEPSEEK_API_KEY | string | 否 | - | DeepSeek API 密钥 |
| HOST | string | 否 | 0.0.0.0 | 服务监听地址 |
| PORT | int | 否 | 8000 | 服务监听端口 |
| LOG_LEVEL | string | 否 | INFO | 日志级别 |

## 模型配置

文件: `config/models.yaml`

\`\`\`yaml
# 基础模型配置（必填）
base_model:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 4096

# 分级模型配置（可选）
tier_models:
  strong:
    provider: zhipu
    model: glm-5
  performance:
    provider: deepseek
    model: deepseek-chat
\`\`\`

### 模型配置说明

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| provider | string | 是 | - | 提供商: openai/anthropic/zhipu/deepseek |
| model | string | 是 | - | 模型名称 |
| temperature | float | 否 | 0.7 | 温度参数，范围 0-2 |
| max_tokens | int | 否 | 4096 | 最大输出 token 数 |
```

---

### 8. 部署文档规范

#### 8.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 环境要求 | 必须 | 硬件和软件要求 |
| 安装步骤 | 必须 | 详细安装步骤 |
| 配置说明 | 必须 | 部署配置 |
| 启动方式 | 必须 | 启动命令 |
| 健康检查 | 必须 | 服务检查方法 |
| 常见问题 | 推荐 | 部署问题解决 |

#### 8.2 部署文档模板

```markdown
# 部署文档

## 环境要求

### 硬件要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 存储 | 10 GB | 50 GB+ |

### 软件要求

| 软件 | 版本要求 |
|------|----------|
| Python | 3.10+ |
| Redis | 7.0+ (可选) |
| PostgreSQL | 14+ (可选) |

## 安装步骤

### 1. 准备环境

\`\`\`bash
# 创建用户
sudo useradd -m -s /bin/bash pyagent

# 创建目录
sudo mkdir -p /opt/pyagent
sudo chown pyagent:pyagent /opt/pyagent
\`\`\`

### 2. 安装依赖

\`\`\`bash
# 切换用户
su - pyagent

# 克隆代码
git clone https://github.com/user/pyagent.git /opt/pyagent
cd /opt/pyagent

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
\`\`\`

### 3. 配置

\`\`\`bash
# 复制配置文件
cp .env.example .env

# 编辑配置
vim .env
\`\`\`

### 4. 启动服务

\`\`\`bash
# 直接启动
python -m src.main

# 使用 gunicorn (生产环境)
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
\`\`\`

## Systemd 服务

创建服务文件 `/etc/systemd/system/pyagent.service`:

\`\`\`ini
[Unit]
Description=PyAgent Service
After=network.target

[Service]
Type=simple
User=pyagent
WorkingDirectory=/opt/pyagent
ExecStart=/opt/pyagent/.venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
\`\`\`

启动服务:

\`\`\`bash
sudo systemctl daemon-reload
sudo systemctl enable pyagent
sudo systemctl start pyagent
\`\`\`

## 健康检查

\`\`\`bash
# 检查服务状态
curl http://localhost:8000/health

# 预期响应
{"status": "healthy", "version": "0.8.0"}
\`\`\`

## Docker 部署

\`\`\`bash
# 构建镜像
docker build -t pyagent:latest .

# 运行容器
docker run -d \
  --name pyagent \
  -p 8000:8000 \
  -v /data/pyagent:/app/data \
  --env-file .env \
  pyagent:latest
\`\`\`
```

---

### 9. 故障排查文档规范

#### 9.1 必须包含的内容

| 章节 | 必须性 | 说明 |
|------|--------|------|
| 常见问题 | 必须 | FAQ 列表 |
| 错误代码 | 必须 | 错误码说明 |
| 排查步骤 | 必须 | 问题排查流程 |
| 日志分析 | 必须 | 日志查看方法 |
| 联系支持 | 推荐 | 获取帮助方式 |

#### 9.2 故障排查文档模板

```markdown
# 故障排查文档

## 常见问题

### Q1: 服务启动失败

**症状**: 服务无法启动，报错 `Address already in use`

**原因**: 端口被占用

**解决方案**:

\`\`\`bash
# 查找占用端口的进程
lsof -i :8000

# 终止进程
kill -9 <PID>

# 或更换端口
PORT=8001 python -m src.main
\`\`\`

### Q2: LLM 调用超时

**症状**: 请求超时，报错 `TimeoutError`

**原因**: 网络问题或 API 响应慢

**解决方案**:

1. 检查网络连接
2. 增加超时时间:

\`\`\`yaml
# config/models.yaml
base_model:
  timeout: 60  # 增加到 60 秒
\`\`\`

## 错误代码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| E001 | 配置文件缺失 | 检查配置文件是否存在 |
| E002 | API 密钥无效 | 检查 API 密钥是否正确 |
| E003 | 数据库连接失败 | 检查数据库配置 |
| E004 | 内存不足 | 增加系统内存 |

## 排查步骤

### 1. 检查日志

\`\`\`bash
# 查看最新日志
tail -f data/logs/pyagent.log

# 搜索错误
grep -i error data/logs/pyagent.log
\`\`\`

### 2. 检查配置

\`\`\`bash
# 验证配置文件
python -c "from src.config import validate; validate()"

# 检查环境变量
env | grep -E 'API_KEY|HOST|PORT'
\`\`\`

### 3. 检查网络

\`\`\`bash
# 测试 API 连接
curl -I https://api.openai.com

# 测试本地服务
curl http://localhost:8000/health
\`\`\`

## 日志分析

### 日志位置

\`\`\`
data/logs/
├── pyagent.log      # 主日志
├── error.log        # 错误日志
└── access.log       # 访问日志
\`\`\`

### 日志级别

| 级别 | 说明 |
|------|------|
| DEBUG | 调试信息 |
| INFO | 正常信息 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

## 获取帮助

- GitHub Issues: https://github.com/user/pyagent/issues
- 文档: https://docs.pyagent.io
```

---

### 10. Markdown 通用格式规范

#### 10.1 标题层级

- 一级标题 (`#`): 文档标题，每个文档只有一个
- 二级标题 (`##`): 主要章节
- 三级标题 (`###`): 子章节
- 四级标题 (`####`): 细节内容
- 避免使用五级及以上标题

#### 10.2 代码块规范

\`\`\`markdown
代码块必须指定语言：

\`\`\`python
def hello():
    print("Hello, World!")
\`\`\`

行内代码使用反引号：`function_name()`
\`\`\`

#### 10.3 表格规范

\`\`\`markdown
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容 | 内容 | 内容 |
| 内容 | 内容 | 内容 |
\`\`\`

表格必须有表头行和分隔行。

#### 10.4 链接规范

\`\`\`markdown
内部链接使用相对路径：
[开发文档](development.md)

外部链接使用完整URL：
[Python官网](https://www.python.org/)

代码引用使用标准格式：
[base.py](src/agents/base.py)
[base.py:L10-20](src/agents/base.py#L10-L20)
\`\`\`

#### 10.5 列表规范

\`\`\`markdown
无序列表：
- 项目一
- 项目二
  - 子项目一
  - 子项目二

有序列表：
1. 步骤一
2. 步骤二
   1. 子步骤一
   2. 子步骤二

任务列表：
- [x] 已完成
- [ ] 未完成
\`\`\`

---

## 三、格式规范

### 1. 文件命名规范

#### 1.1 Python 文件

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写+下划线 | `chat_agent.py` |
| 测试 | test_前缀 | `test_chat_agent.py` |
| 配置 | 小写+下划线 | `models.yaml` |
| 脚本 | 小写+下划线 | `build_script.py` |

#### 1.2 前端文件

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件 | 大驼峰 | `ChatView.vue` |
| 页面 | 大驼峰+View后缀 | `HomeView.vue` |
| 样式 | 小写+连字符 | `chat-view.css` |
| 工具 | 小写+连字符 | `date-utils.ts` |

#### 1.3 配置文件

| 类型 | 规范 | 示例 |
|------|------|------|
| YAML | 小写+下划线 | `models.yaml` |
| JSON | 小写+下划线 | `mcp.json` |
| TOML | 小写 | `pyproject.toml` |
| ENV | 大写+下划线 | `.env` |

---

### 2. 目录结构规范

#### 2.1 源代码目录

```
src/
├── __init__.py              # 包初始化
├── main.py                  # 主入口
├── agents/                  # 智能体模块
│   ├── __init__.py
│   ├── base.py             # 基类
│   └── registry.py         # 注册中心
├── llm/                     # LLM 模块
│   ├── __init__.py
│   ├── client.py
│   └── adapters/
│       ├── __init__.py
│       └── openai_adapter.py
└── tools/                   # 工具模块
    ├── __init__.py
    └── base.py
```

#### 2.2 文档目录

```
docs/
├── architecture.md          # 架构文档
├── api.md                   # API 文档
├── configuration.md         # 配置文档
├── deployment.md            # 部署文档
├── development.md           # 开发文档
├── testing.md               # 测试文档
├── standards.md             # 规范文档
└── modules/                 # 模块文档
    ├── agent-system.md
    ├── llm-client.md
    └── memory-system.md
```

#### 2.3 配置目录

```
config/
├── models.yaml              # 模型配置
├── mcp.json                 # MCP 配置
├── todo.yaml                # Todo 配置
├── memory.yaml              # 记忆配置
└── persona.yaml             # 拟人化配置
```

---

### 3. 配置文件规范

#### 3.1 YAML 配置规范

```yaml
# 配置文件必须有注释说明

# 模型配置
models:
  # 基础模型（必填）
  base:
    provider: openai
    model: gpt-4o
    temperature: 0.7
  
  # 分级模型（可选）
  tiers:
    strong:
      provider: zhipu
      model: glm-5
    performance:
      provider: deepseek
      model: deepseek-chat

# 功能开关
features:
  enable_memory: true
  enable_todo: true
  max_retries: 3
```

#### 3.2 JSON 配置规范

```json
{
  "mcp_servers": {
    "description": "MCP 服务器配置",
    "servers": [
      {
        "name": "filesystem",
        "command": "mcp-server-filesystem",
        "args": ["--root", "/data"]
      }
    ]
  }
}
```

#### 3.3 环境变量规范

```bash
# .env 文件

# API 密钥
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=ds-xxx

# 服务配置
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# 功能开关
ENABLE_MCP=true
ENABLE_MEMORY=true
```

---

## 四、提交规范

### 1. Git 提交规范

#### 1.1 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 1.2 类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(chat): 添加消息撤回功能 |
| fix | 修复 Bug | fix(llm): 修复超时重试问题 |
| docs | 文档更新 | docs(api): 更新 API 文档 |
| style | 代码格式 | style: 格式化代码 |
| refactor | 重构 | refactor(memory): 重构存储逻辑 |
| test | 测试 | test(todo): 添加单元测试 |
| chore | 构建/工具 | chore: 更新依赖版本 |
| perf | 性能优化 | perf: 优化消息处理速度 |

#### 1.3 完整示例

```
feat(chat): 添加消息撤回功能

- 实现消息撤回 API
- 添加撤回权限检查
- 更新前端撤回按钮
- 添加撤回消息的数据库记录

Closes #123
```

---

### 2. 分支管理规范

#### 2.1 分支命名

| 分支类型 | 命名规范 | 示例 |
|----------|----------|------|
| 主分支 | main | main |
| 开发分支 | develop | develop |
| 功能分支 | feature/* | feature/chat-revoke |
| 修复分支 | bugfix/* | bugfix/llm-timeout |
| 发布分支 | release/* | release/v0.8.0 |
| 热修复分支 | hotfix/* | hotfix/critical-fix |

#### 2.2 分支流程

```
main
  │
  ├── release/v0.8.0 ──→ 合并到 main
  │
develop
  │
  ├── feature/chat-revoke ──→ 合并到 develop
  │
  └── bugfix/llm-timeout ──→ 合并到 develop
```

---

### 3. 版本号规范

#### 3.1 语义化版本

格式: `MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

#### 3.2 版本号更新时机

| 版本号 | 更新时机 | 示例场景 |
|--------|----------|----------|
| **MAJOR** | 不兼容的 API 变更 | 删除公开 API、修改函数签名、更改配置格式、数据库迁移 |
| **MINOR** | 向后兼容的功能新增 | 新增模块、新增 API 端点、新增配置选项、功能增强 |
| **PATCH** | 向后兼容的问题修复 | Bug 修复、性能优化、文档更新、依赖更新 |

#### 3.3 版本号更新详细说明

##### MAJOR 版本更新 (X.0.0)

**必须更新 MAJOR 版本的情况**：

1. **删除或重命名公开 API**
   - 删除公开函数、类或方法
   - 重命名公开 API（函数名、类名、参数名）
   - 更改函数签名（参数顺序、参数类型）

2. **不兼容的配置变更**
   - 删除配置项
   - 更改配置文件格式
   - 更改配置项的默认值导致行为变化

3. **数据库迁移**
   - 数据库结构变更需要迁移脚本
   - 数据格式不兼容

4. **依赖重大变更**
   - Python 最低版本要求变更
   - 核心依赖库主版本升级

**示例**：
```
v0.8.0 → v1.0.0
- 重命名模块：chat_agent → interaction
- 删除废弃 API：old_function() 已移除
- 配置格式变更：models.yaml 结构重构
```

##### MINOR 版本更新 (0.X.0)

**必须更新 MINOR 版本的情况**：

1. **新增功能**
   - 新增模块或子模块
   - 新增 API 端点
   - 新增配置选项
   - 新增工具或命令

2. **功能增强**
   - 现有功能添加新参数
   - 性能优化（不影响 API）
   - 新增可选功能

3. **向后兼容的变更**
   - 新增默认参数
   - 新增返回字段
   - 新增配置项（有合理默认值）

**示例**：
```
v0.8.0 → v0.9.0
- 新增模块：src/video/ 视频编辑器
- 新增 API：POST /api/video/render
- 新增配置：config/video.yaml
```

##### PATCH 版本更新 (0.0.X)

**必须更新 PATCH 版本的情况**：

1. **Bug 修复**
   - 修复功能缺陷
   - 修复安全漏洞
   - 修复文档错误

2. **性能优化**
   - 代码优化（不改变行为）
   - 内存优化
   - 响应时间优化

3. **文档更新**
   - 文档修正
   - 示例代码更新
   - 注释完善

4. **依赖更新**
   - 补丁版本依赖更新
   - 开发依赖更新

**示例**：
```
v0.8.0 → v0.8.1
- 修复：LLM 调用超时问题
- 修复：内存泄漏问题
- 文档：更新 API 文档示例
```

#### 3.4 版本号更新流程

1. **确定版本类型**
   - 评估变更内容
   - 确定是否向后兼容
   - 选择 MAJOR/MINOR/PATCH

2. **更新版本号**
   - 更新 `pyproject.toml` 中的版本号
   - 更新 `src/__init__.py` 中的 `__version__`
   - 更新 `frontend/package.json` 中的版本号

3. **更新 CHANGELOG**
   - 添加新版本条目
   - 记录所有变更内容
   - 标注不兼容变更

4. **创建 Git 标签**
   ```bash
   git tag -a v0.8.0 -m "Release v0.8.0"
   git push origin v0.8.0
   ```

#### 3.5 预发布版本

**格式**: `MAJOR.MINOR.PATCH-PRERELEASE`

| 类型 | 格式 | 说明 |
|------|------|------|
| Alpha | `0.8.0-alpha.1` | 内部测试版本 |
| Beta | `0.8.0-beta.1` | 公开测试版本 |
| RC | `0.8.0-rc.1` | 发布候选版本 |

**示例**：
```
v0.8.0-alpha.1  # 第一个内部测试版本
v0.8.0-alpha.2  # 第二个内部测试版本
v0.8.0-beta.1   # 第一个公开测试版本
v0.8.0-rc.1     # 第一个发布候选版本
v0.8.0          # 正式发布版本
```

#### 3.6 版本兼容性说明

在 CHANGELOG 中必须说明版本兼容性：

```markdown
## 版本兼容性说明

| 版本 | 兼容性 |
|------|--------|
| v0.8.0 | **不兼容** v0.7.x（新增大量模块） |
| v0.7.2 | 完全兼容 v0.7.x |
| v0.7.1 | 完全兼容 v0.7.0 |
```

#### 3.7 版本示例

| 版本 | 说明 |
|------|------|
| 0.8.0 | 新增多个模块，向后兼容 |
| 0.8.1 | 修复 Bug |
| 1.0.0 | 首个稳定版本 |
| 2.0.0 | API 重大变更，不兼容 v1.x |

---

## 五、测试规范

### 1. 单元测试规范

#### 1.1 测试文件组织

```python
# tests/test_module.py

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.module import MyClass

class TestMyClass:
    """MyClass 测试类"""
    
    @pytest.fixture
    def instance(self):
        """创建测试实例"""
        return MyClass(config={"test": True})
    
    @pytest.fixture
    def mock_dependency(self):
        """模拟依赖"""
        return Mock(return_value="mocked")
    
    def test_initialization(self, instance):
        """测试初始化"""
        assert instance.config["test"] is True
    
    def test_process(self, instance, mock_dependency):
        """测试处理方法"""
        with patch('src.module.dependency', mock_dependency):
            result = instance.process("input")
            assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_method(self, instance):
        """测试异步方法"""
        result = await instance.async_process("input")
        assert result is not None
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
        ("", ""),
    ])
    def test_multiple_cases(self, instance, input, expected):
        """测试多个案例"""
        result = instance.process(input)
        assert result == expected
```

#### 1.2 测试命名规范

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| 测试文件 | test_前缀 | `test_chat_agent.py` |
| 测试类 | Test前缀 | `TestChatAgent` |
| 测试方法 | test_前缀 | `test_send_message()` |

---

### 2. 集成测试规范

```python
# tests/integration/test_chat_flow.py

import pytest
from src.main import create_app

@pytest.fixture
async def app():
    """创建测试应用"""
    app = create_app(config={"testing": True})
    yield app
    await app.shutdown()

@pytest.fixture
async def client(app):
    """创建测试客户端"""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_chat_flow(client):
    """测试完整聊天流程"""
    # 1. 发送消息
    response = await client.post("/api/messages", json={
        "chat_id": "test_chat",
        "content": "Hello"
    })
    assert response.status_code == 200
    
    # 2. 获取回复
    data = response.json()
    assert data["success"] is True
    assert "message_id" in data["data"]
```

---

### 3. 测试命名规范

#### 3.1 测试方法命名

```python
# 格式: test_<method>_<scenario>_<expected_result>

def test_send_message_with_valid_input_returns_success():
    pass

def test_send_message_with_empty_input_raises_error():
    pass

def test_send_message_when_rate_limited_returns_error():
    pass
```

#### 3.2 测试覆盖要求

| 类型 | 覆盖率要求 |
|------|-----------|
| 核心模块 | >= 80% |
| 工具模块 | >= 70% |
| API 路由 | >= 60% |

---

## 六、安全规范

### 1. 敏感信息处理

#### 1.1 禁止硬编码

```python
# 错误示例
api_key = "sk-xxx"  # 禁止

# 正确示例
import os
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set")
```

#### 1.2 日志脱敏

```python
import logging

def sanitize_for_log(text: str) -> str:
    """脱敏敏感信息"""
    import re
    # 脱敏 API 密钥
    text = re.sub(r'sk-[a-zA-Z0-9]{20,}', 'sk-***', text)
    # 脱敏手机号
    text = re.sub(r'1[3-9]\d{9}', '1***', text)
    return text

logger.info(f"Processing request: {sanitize_for_log(content)}")
```

#### 1.3 配置文件安全

```bash
# .env 文件不要提交到版本控制
# .gitignore
.env
.env.local
.env.*.local
*.pem
*.key
```

---

### 2. 输入验证规范

#### 2.1 Pydantic 验证

```python
from pydantic import BaseModel, validator, Field
import re
import bleach

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=10000)
    chat_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$')
    
    @validator('message')
    def sanitize_message(cls, v):
        """清理 HTML 标签"""
        return bleach.clean(v, tags=[], strip=True)
    
    @validator('chat_id')
    def validate_chat_id(cls, v):
        """验证格式"""
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
            raise ValueError('Invalid chat_id format')
        return v
```

#### 2.2 SQL 注入防护

```python
# 使用参数化查询
async def get_user(user_id: str):
    query = "SELECT * FROM users WHERE id = $1"
    return await db.fetchrow(query, user_id)

# 禁止字符串拼接
# BAD: query = f"SELECT * FROM users WHERE id = '{user_id}'"
```

---

### 3. 权限控制规范

```python
from functools import wraps
from fastapi import HTTPException, Request

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    async def decorated(request: Request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            raise HTTPException(status_code=401, detail="Missing token")
        
        user = validate_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        request.state.user = user
        return await f(request, *args, **kwargs)
    return decorated

def require_role(role: str):
    """角色检查装饰器"""
    def decorator(f):
        @wraps(f)
        async def decorated(request: Request, *args, **kwargs):
            user = request.state.user
            if user.role != role:
                raise HTTPException(status_code=403, detail="Forbidden")
            return await f(request, *args, **kwargs)
        return decorated
    return decorator
```

---

## 七、日志规范

### 1. 日志级别规范

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 调试信息 | 变量值、执行路径 |
| INFO | 正常信息 | 服务启动、请求处理 |
| WARNING | 警告信息 | 配置缺失、降级处理 |
| ERROR | 错误信息 | 异常、失败操作 |
| CRITICAL | 严重错误 | 服务崩溃、数据丢失 |

### 2. 日志格式规范

```python
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON 格式日志"""
    
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }, ensure_ascii=False)

# 配置日志
logger = logging.getLogger('pyagent')
logger.setLevel(logging.INFO)

# 文件日志
file_handler = RotatingFileHandler(
    'data/logs/pyagent.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(JSONFormatter())
logger.addHandler(file_handler)
```

### 3. 日志存储规范

```
data/logs/
├── pyagent.log           # 主日志
├── pyagent.log.1         # 轮转日志
├── pyagent.log.2
├── access.log            # 访问日志
├── error.log             # 错误日志
└── debug.log             # 调试日志（开发环境）
```

---

## 八、注释规范

### 1. Python 注释规范

#### 1.1 模块注释

```python
"""
PyAgent 模块名称 - 简短描述

详细描述模块的功能、使用场景和注意事项。

Example:
    from src.module import ModuleClass
    
    client = ModuleClass()
    result = client.do_something()
"""
```

#### 1.2 类注释

```python
class ChatAgent:
    """聊天智能体
    
    负责处理用户消息并生成回复。
    
    Attributes:
        name: 智能体名称
        model: 使用的模型
        memory: 记忆管理器
    
    Example:
        >>> agent = ChatAgent(name="assistant")
        >>> response = await agent.process("Hello")
    """
```

#### 1.3 方法注释

```python
async def send_message(
    self,
    chat_id: str,
    content: str,
    message_type: str = "text"
) -> dict[str, Any]:
    """发送消息到指定聊天
    
    Args:
        chat_id: 聊天ID，格式为 chat_xxx
        content: 消息内容，最大长度 10000
        message_type: 消息类型，可选 text/image/file
    
    Returns:
        包含 message_id 和 timestamp 的字典
    
    Raises:
        ValidationError: 参数验证失败
        LLMError: LLM 调用失败
    
    Example:
        >>> result = await agent.send_message("chat_123", "Hello")
        >>> print(result["message_id"])
        msg_xxx
    """
    pass
```

---

### 2. 前端注释规范

#### 2.1 组件注释

```vue
<script setup lang="ts">
/**
 * 聊天视图组件
 * 
 * 显示聊天消息列表并处理消息发送。
 * 
 * @component ChatView
 * @example
 * <ChatView chat-id="chat_123" @send="handleSend" />
 */
</script>
```

#### 2.2 函数注释

```typescript
/**
 * 发送消息到服务器
 * 
 * @param chatId - 聊天ID
 * @param content - 消息内容
 * @returns 发送结果
 * @throws {Error} 网络错误时抛出
 * 
 * @example
 * const result = await sendMessage('chat_123', 'Hello')
 */
async function sendMessage(chatId: string, content: string): Promise<Message> {
  // 实现
}
```

---

### 3. 配置注释规范

#### 3.1 YAML 注释

```yaml
# 模型配置
models:
  # 基础模型配置（必填）
  # 这是默认使用的模型
  base:
    provider: openai      # 提供商: openai/anthropic/zhipu/deepseek
    model: gpt-4o         # 模型名称
    temperature: 0.7      # 温度参数，范围 0-2
```

#### 3.2 JSON 注释

JSON 不支持注释，使用 JSONC 或单独的说明文件：

```jsonc
{
  "mcp_servers": {
    "servers": [
      {
        "name": "filesystem",
        "command": "mcp-server-filesystem"
      }
    ]
  }
}
```

---

## 附录

### A. 检查清单

#### 代码提交前检查

- [ ] 代码通过 ruff 格式化
- [ ] 代码通过 ruff 检查
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 单元测试通过
- [ ] 无敏感信息泄露

#### 文档发布前检查

- [ ] Markdown 格式正确
- [ ] 链接有效
- [ ] 代码示例可运行
- [ ] 版本号已更新

### B. 工具配置

#### ruff 配置 (pyproject.toml)

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

#### mypy 配置 (pyproject.toml)

```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
```

---

**PyAgent v0.8.0 - 让AI更智能，让协作更高效**
