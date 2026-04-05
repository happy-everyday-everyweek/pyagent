# PyAgent LLM 模型网关

**版本**: v0.8.0  
**模块路径**: `src/llm/gateway.py`  
**最后更新**: 2025-04-03

---

## 概述

LLM 模型网关是 PyAgent v0.8.0 引入的全新模块，参考 LiteLLM 设计，提供统一的接口访问多个 LLM 提供商。支持 OpenAI、Anthropic、DeepSeek、智谱、Moonshot 等多家提供商，实现模型自动路由、故障转移和统一计费。

### 核心特性

- **多提供商支持**: OpenAI、Anthropic、DeepSeek、智谱、Moonshot、百度、阿里等
- **统一接口**: 一致的 API 调用方式
- **自动路由**: 根据模型名称自动选择提供商
- **故障转移**: 主提供商失败时自动切换
- **流式响应**: 支持流式输出
- **嵌入向量**: 支持文本嵌入

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Model Gateway                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 ModelGateway                        │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │   Provider   │  │   Adapter    │                │   │
│  │  │   Registry   │  │    Layer     │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  │                                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐                │   │
│  │  │   Fallback   │  │  Rate Limit  │                │   │
│  │  │   Handler    │  │   Control    │                │   │
│  │  └──────────────┘  └──────────────┘                │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Provider Adapters                      │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │   │
│  │  │ OpenAI │ │Anthropic│ │DeepSeek│ │ Zhipu  │ ...   │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 模型网关 (ModelGateway)

**位置**: `src/llm/gateway.py`

```python
from src.llm.gateway import ModelGateway, model_gateway, ProviderType, ProviderInfo

# 使用全局实例
gateway = model_gateway

# 或创建新实例
from src.llm.gateway import ModelGatewayConfig
gateway = ModelGateway(ModelGatewayConfig(
    enable_fallback=True,
    default_timeout=60,
    max_retries=3
))
```

#### 主要方法

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `register_provider()` | 注册提供商 | `None` |
| `get_provider()` | 获取提供商信息 | `ProviderInfo \| None` |
| `list_providers()` | 列出所有提供商 | `list[ProviderInfo]` |
| `chat()` | 发送聊天请求 | `dict` |
| `chat_stream()` | 流式聊天 | `AsyncIterator[dict]` |
| `embeddings()` | 获取文本嵌入 | `list[list[float]]` |
| `health_check()` | 健康检查 | `dict[str, bool]` |
| `get_supported_models()` | 获取支持的模型 | `list[str]` |

---

### 2. 提供商类型

```python
class ProviderType(Enum):
    OPENAI = "openai"           # OpenAI (GPT-4, GPT-3.5)
    ANTHROPIC = "anthropic"     # Anthropic (Claude)
    DEEPSEEK = "deepseek"       # DeepSeek
    ZHIPU = "zhipu"             # 智谱 AI (GLM)
    MOONSHOT = "moonshot"       # Moonshot
    BAIDU = "baidu"             # 百度 (文心)
    ALIBABA = "alibaba"         # 阿里 (通义千问)
    LOCAL = "local"             # 本地模型
    CUSTOM = "custom"           # 自定义
```

---

### 3. 提供商信息

```python
@dataclass
class ProviderInfo:
    name: str                   # 提供商名称
    provider_type: ProviderType # 类型
    base_url: str               # API 基础 URL
    api_key: str                # API 密钥
    default_model: str          # 默认模型
    supports_streaming: bool    # 支持流式
    supports_tools: bool        # 支持工具调用
    supports_vision: bool       # 支持视觉
    max_context_length: int     # 最大上下文长度
    rate_limit_rpm: int         # 每分钟请求限制
    rate_limit_tpm: int         # 每分钟 Token 限制
```

---

## 使用示例

### 注册提供商

```python
from src.llm.gateway import model_gateway, ProviderInfo, ProviderType

# 注册 OpenAI
gateway.register_provider(ProviderInfo(
    name="openai",
    provider_type=ProviderType.OPENAI,
    base_url="https://api.openai.com/v1",
    api_key="sk-xxx",
    default_model="gpt-4o",
    supports_streaming=True,
    supports_tools=True,
    supports_vision=True,
    max_context_length=128000,
    rate_limit_rpm=60,
    rate_limit_tpm=100000
))

# 注册 DeepSeek
gateway.register_provider(ProviderInfo(
    name="deepseek",
    provider_type=ProviderType.DEEPSEEK,
    base_url="https://api.deepseek.com/v1",
    api_key="sk-xxx",
    default_model="deepseek-chat",
    supports_streaming=True,
    supports_tools=True,
    max_context_length=64000
))

# 注册智谱
gateway.register_provider(ProviderInfo(
    name="zhipu",
    provider_type=ProviderType.ZHIPU,
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key="xxx",
    default_model="glm-4",
    supports_streaming=True,
    supports_tools=True,
    supports_vision=True
))
```

### 发送聊天请求

```python
import asyncio
from src.llm.gateway import model_gateway

async def chat_example():
    # 简单请求
    response = await model_gateway.chat(
        messages=[
            {"role": "system", "content": "你是一个有用的助手。"},
            {"role": "user", "content": "你好，请介绍一下 Python。"}
        ],
        model="gpt-4o"
    )
    print(response["choices"][0]["message"]["content"])
    
    # 指定提供商
    response = await model_gateway.chat(
        messages=[{"role": "user", "content": "你好"}],
        model="deepseek-chat",
        provider="deepseek"
    )
    
    # 带参数的请求
    response = await model_gateway.chat(
        messages=[{"role": "user", "content": "写一首诗"}],
        model="glm-4",
        temperature=0.7,
        max_tokens=500,
        top_p=0.9
    )

asyncio.run(chat_example())
```

### 流式响应

```python
import asyncio
from src.llm.gateway import model_gateway

async def stream_example():
    async for chunk in model_gateway.chat_stream(
        messages=[{"role": "user", "content": "讲一个故事"}],
        model="gpt-4o"
    ):
        if "choices" in chunk:
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                print(delta["content"], end="", flush=True)
    print()

asyncio.run(stream_example())
```

### 文本嵌入

```python
import asyncio
from src.llm.gateway import model_gateway

async def embedding_example():
    embeddings = await model_gateway.embeddings(
        texts=[
            "这是一段文本",
            "这是另一段文本"
        ],
        model="text-embedding-ada-002",
        provider="openai"
    )
    
    for i, emb in enumerate(embeddings):
        print(f"文本 {i+1} 的嵌入维度: {len(emb)}")

asyncio.run(embedding_example())
```

### 健康检查

```python
import asyncio
from src.llm.gateway import model_gateway

async def health_check():
    results = await model_gateway.health_check()
    
    for provider, is_healthy in results.items():
        status = "正常" if is_healthy else "异常"
        print(f"{provider}: {status}")

asyncio.run(health_check())
```

### 获取支持的模型

```python
# OpenAI 支持的模型
openai_models = model_gateway.get_supported_models("openai")
print("OpenAI 模型:", openai_models)

# Anthropic 支持的模型
anthropic_models = model_gateway.get_supported_models("anthropic")
print("Anthropic 模型:", anthropic_models)
```

---

## 自动路由

网关会根据模型名称自动检测提供商：

```python
# 自动路由到 OpenAI
await model_gateway.chat(messages=msgs, model="gpt-4o")
await model_gateway.chat(messages=msgs, model="gpt-3.5-turbo")

# 自动路由到 Anthropic
await model_gateway.chat(messages=msgs, model="claude-3-opus-20240229")

# 自动路由到 DeepSeek
await model_gateway.chat(messages=msgs, model="deepseek-chat")

# 自动路由到智谱
await model_gateway.chat(messages=msgs, model="glm-4")

# 自动路由到 Moonshot
await model_gateway.chat(messages=msgs, model="moonshot-v1-8k")
```

---

## 故障转移

```python
from src.llm.gateway import ModelGateway, ModelGatewayConfig

# 启用故障转移
gateway = ModelGateway(ModelGatewayConfig(
    enable_fallback=True,
    fallback_order=["openai", "deepseek", "zhipu"],
    max_retries=3,
    retry_delay=1.0
))

# 如果 OpenAI 失败，自动切换到 DeepSeek
response = await gateway.chat(
    messages=[{"role": "user", "content": "你好"}],
    model="gpt-4o"  # 会尝试 fallback_order 中的其他提供商
)
```

---

## API 接口

### REST API

#### 聊天
```http
POST /api/llm/chat
Content-Type: application/json

{
  "messages": [
    {"role": "system", "content": "你是一个助手。"},
    {"role": "user", "content": "你好"}
  ],
  "model": "gpt-4o",
  "temperature": 0.7,
  "max_tokens": 500
}
```

#### 流式聊天
```http
POST /api/llm/chat/stream
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "讲个故事"}],
  "model": "gpt-4o"
}
```

#### 文本嵌入
```http
POST /api/llm/embeddings
Content-Type: application/json

{
  "texts": ["文本1", "文本2"],
  "model": "text-embedding-ada-002"
}
```

#### 健康检查
```http
GET /api/llm/health
```

---

## 配置选项

```yaml
# config/llm_gateway.yaml
llm_gateway:
  enable_fallback: true
  default_timeout: 60
  max_retries: 3
  retry_delay: 1.0
  
  providers:
    - name: "openai"
      type: "openai"
      base_url: "https://api.openai.com/v1"
      api_key: "${OPENAI_API_KEY}"
      default_model: "gpt-4o"
      
    - name: "deepseek"
      type: "deepseek"
      base_url: "https://api.deepseek.com/v1"
      api_key: "${DEEPSEEK_API_KEY}"
      default_model: "deepseek-chat"
      
    - name: "zhipu"
      type: "zhipu"
      base_url: "https://open.bigmodel.cn/api/paas/v4"
      api_key: "${ZHIPU_API_KEY}"
      default_model: "glm-4"
  
  fallback_order:
    - "openai"
    - "deepseek"
    - "zhipu"
```

---

## 最佳实践

### 1. 错误处理

```python
import asyncio
from src.llm.gateway import model_gateway

async def safe_chat():
    try:
        response = await model_gateway.chat(
            messages=[{"role": "user", "content": "你好"}],
            model="gpt-4o"
        )
        return response
    except ValueError as e:
        print(f"提供商错误: {e}")
    except Exception as e:
        print(f"请求失败: {e}")

asyncio.run(safe_chat())
```

### 2. 超时设置

```python
from src.llm.gateway import ModelGateway, ModelGatewayConfig

gateway = ModelGateway(ModelGatewayConfig(
    default_timeout=30  # 30秒超时
))
```

### 3. 多提供商负载均衡

```python
import random
from src.llm.gateway import model_gateway

providers = ["openai", "deepseek", "zhipu"]
chosen = random.choice(providers)

response = await model_gateway.chat(
    messages=[{"role": "user", "content": "你好"}],
    model="gpt-4o",
    provider=chosen
)
```

---

## 故障排除

### 常见问题

**Q: API 密钥错误？**  
A: 检查 `api_key` 是否正确配置，确保密钥有相应权限。

**Q: 模型不可用？**  
A: 检查模型名称是否正确，或该提供商是否支持此模型。

**Q: 流式响应中断？**  
A: 检查网络连接，或增加超时时间。

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持多提供商
- 支持统一接口
- 支持自动路由
- 支持故障转移
- 支持流式响应
- 支持文本嵌入

---

## 相关文档

- [LiteLLM 文档](https://docs.litellm.ai/)
- [LLM 客户端](./llm-client-v2.md) - 原有 LLM 客户端
- [API 文档](../api.md) - 完整 API 参考
