# LLM客户端文�?v0.8.0

本文档详细描述PyAgent v0.8.0 LLM客户端模块的设计和实现�?
## 概述

LLM Client是PyAgent系统中负责统一管理大语言模型调用的模块。它支持多模型配置、负载均衡和自动故障转移�?
## 核心组件

### 1. LLMClient (LLM客户�?

**文件**: `src/llm/client.py`

**职责**: 统一管理多模型调用，实现负载均衡和故障转移�?
#### 主要功能

- 多模型支�?- 负载均衡
- 自动故障转移
- 冷却机制
- 流式输出

#### 模型选择策略

```python
class LLMClient:
    def _select_model(
        self,
        exclude_models: set[str] | None = None,
        require_capability: str | None = None,
    ) -> str:
        """选择模型�?        
        策略:
        1. 排除已失败的模型
        2. 排除冷却中的模型
        3. 检查能力要�?        4. 根据策略选择:
           - random: 随机选择
           - balance: 基于token使用量均�?        """
```

#### 故障处理流程

```
模型调用失败
    �?    �?记录失败次数
    �?    �?增加惩罚分数
    �?    �?进入冷却�?(指数退�? 60s, 120s, 240s...)
    �?    �?自动切换到备用模�?    �?    �?定期重置冷却状�?```

#### 代码示例

```python
from src.llm.client import LLMClient, ModelConfig, AdapterType
from src.llm.adapters.base import Message

# 配置模型
models = [
    ModelConfig(
        name="openai-gpt4",
        adapter_type=AdapterType.OPENAI,
        model="gpt-4o",
        api_key="sk-xxx",
        priority=1,
        capabilities=["text", "vision", "tools"]
    ),
    ModelConfig(
        name="deepseek-chat",
        adapter_type=AdapterType.DEEPSEEK,
        model="deepseek-chat",
        api_key="sk-xxx",
        priority=2,
        capabilities=["text", "tools"]
    )
]

# 创建客户�?client = LLMClient(
    models=models,
    selection_strategy="balance"  # �?"random"
)

# 普通调�?messages = [Message(role="user", content="你好")]
response = await client.generate(messages=messages)
print(response.content)

# 流式调用
async for chunk in client.generate_stream(messages=messages):
    print(chunk.content, end="")

# 指定模型
response = await client.generate(
    messages=messages,
    model_name="openai-gpt4"
)

# 获取模型状�?status = client.get_model_status()
print(status)
```

---

### 2. 适配器系�?
#### 2.1 BaseAdapter (适配器基�?

**文件**: `src/llm/adapters/base.py`

```python
class BaseAdapter(ABC):
    """LLM适配器基类�?""
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成响应�?""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, request: LLMRequest
    ) -> AsyncIterator[StreamChunk]:
        """流式生成�?""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查�?""
        pass
```

#### 2.2 OpenAIAdapter

**文件**: `src/llm/adapters/openai_adapter.py`

支持提供�?
- OpenAI
- DeepSeek
- 智谱AI
- 其他OpenAI兼容API

#### 2.3 AnthropicAdapter

**文件**: `src/llm/adapters/anthropic_adapter.py`

支持模型:
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

---

### 3. 数据模型

#### 3.1 Message (消息)

```python
@dataclass
class Message:
    role: str       # system, user, assistant, tool
    content: str
    name: str = None  # 用于tool消息
```

#### 3.2 LLMRequest (请求)

```python
@dataclass
class LLMRequest:
    messages: List[Message]
    system: str = ""
    tools: List[Tool] = None
    max_tokens: int = 4096
    temperature: float = 1.0
    extra_params: dict = None
```

#### 3.3 LLMResponse (响应)

```python
@dataclass
class LLMResponse:
    content: str
    usage: TokenUsage
    model: str
    finish_reason: str
```

#### 3.4 Tool (工具)

```python
@dataclass
class Tool:
    type: str = "function"
    function: Function = None

@dataclass
class Function:
    name: str
    description: str
    parameters: dict
```

---

## 支持的模�?
| 提供�?| 适配�?| 模型 | 能力 |
|--------|--------|------|------|
| OpenAI | OpenAIAdapter | gpt-4o | text, vision, tools |
| OpenAI | OpenAIAdapter | gpt-4-turbo | text, vision, tools |
| OpenAI | OpenAIAdapter | gpt-3.5-turbo | text, tools |
| DeepSeek | OpenAIAdapter | deepseek-chat | text, tools |
| DeepSeek | OpenAIAdapter | deepseek-coder | text, tools, code |
| 智谱AI | OpenAIAdapter | glm-4 | text, tools |
| 智谱AI | OpenAIAdapter | glm-4-flash | text |
| Anthropic | AnthropicAdapter | claude-3-opus | text, vision, tools |
| Anthropic | AnthropicAdapter | claude-3-sonnet | text, vision, tools |
| Anthropic | AnthropicAdapter | claude-3-haiku | text, vision |

---

## 配置

### 环境变量配置

```env
# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# DeepSeek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat

# 智谱AI
ZHIPU_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
ZHIPU_MODEL=glm-4

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### 配置文件

```yaml
# config/models.yaml
models:
  strong:
    provider: openai
    model: gpt-4o
    api_key: ${OPENAI_API_KEY}
    base_url: ${OPENAI_BASE_URL}
    priority: 1
    max_tokens: 4096
    temperature: 0.7
    timeout: 180
    max_retries: 3
    retry_delay: 1.0
    enabled: true
    capabilities:
      - text
      - vision
      - tools
```

---

## 扩展开�?
### 创建自定义适配�?
```python
from src.llm.adapters.base import BaseAdapter, LLMRequest, LLMResponse

class CustomAdapter(BaseAdapter):
    """自定义适配器�?""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        model: str = "default",
        timeout: int = 180
    ):
        self.api_key = api_key
        self.base_url = base_url or "https://api.custom.com"
        self.model = model
        self.timeout = timeout
        self._client = None
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成响应�?""
        # 1. 构建请求
        payload = self._build_payload(request)
        
        # 2. 发送请�?        response = await self._send_request(payload)
        
        # 3. 解析响应
        return self._parse_response(response)
    
    async def generate_stream(
        self, request: LLMRequest
    ) -> AsyncIterator[StreamChunk]:
        """流式生成�?""
        # 实现流式生成逻辑
        pass
    
    async def health_check(self) -> bool:
        """健康检查�?""
        try:
            await self.generate(
                LLMRequest(messages=[Message(role="user", content="hi")])
            )
            return True
        except Exception:
            return False
```

---

## 性能优化

### 1. 连接�?
```python
import httpx

# 使用连接�?client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20
    )
)
```

### 2. 响应缓存

```python
from functools import lru_cache

class CachedLLMClient:
    def __init__(self, client: LLMClient):
        self._client = client
        self._cache = {}
    
    async def generate(self, messages: list, **kwargs) -> LLMResponse:
        cache_key = self._get_cache_key(messages, kwargs)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        response = await self._client.generate(messages, **kwargs)
        self._cache[cache_key] = response
        
        return response
```

### 3. 批量处理

```python
async def batch_generate(
    client: LLMClient,
    requests: List[List[Message]]
) -> List[LLMResponse]:
    """批量生成�?""
    tasks = [client.generate(req) for req in requests]
    return await asyncio.gather(*tasks)
```

---

## 错误处理

### 异常类型

| 异常 | 说明 | 处理建议 |
|------|------|----------|
| LLMError | 通用错误 | 检查配�?|
| NetworkError | 网络错误 | 检查网络连�?|
| RateLimitError | 速率限制 | 降低请求频率 |
| AuthenticationError | 认证错误 | 检查API密钥 |
| AllModelsFailedError | 所有模型失�?| 检查所有配�?|

### 重试策略

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def generate_with_retry(client, messages):
    return await client.generate(messages)
```
