# 统一LLM客户端创建任务

## 任务概述
在 D:\agent\src\llm 目录下创建统一LLM客户端，支持多种LLM提供商。

## 完成路径

### 1. 创建的文件列表

| 文件路径 | 描述 |
|---------|------|
| `src/llm/adapters/__init__.py` | 适配器模块导出 |
| `src/llm/adapters/base.py` | 适配器基类和数据类型定义 |
| `src/llm/adapters/openai_adapter.py` | OpenAI兼容适配器 |
| `src/llm/adapters/anthropic_adapter.py` | Anthropic适配器 |
| `src/llm/client.py` | 统一LLM客户端 |
| `src/llm/__init__.py` | 模块导出 |

### 2. 主要类和方法签名

#### base.py
```python
class BaseAdapter(ABC):
    name: str
    def __init__(self, api_key, base_url, model, timeout, max_retries, retry_delay)
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]
    
    async def health_check(self) -> bool

@dataclass
class LLMRequest:
    messages: list[Message]
    system: str = ""
    tools: list[Tool] | None = None
    max_tokens: int = 4096
    temperature: float = 1.0
    extra_params: dict | None = None

@dataclass
class LLMResponse:
    id: str
    content: str
    stop_reason: StopReason
    usage: Usage
    model: str
    tool_calls: list[ToolCall]
    reasoning_content: str | None
```

#### openai_adapter.py
```python
class OpenAIAdapter(BaseAdapter):
    name = "openai"
    
    # 支持的提供商
    PROVIDER_BASE_URLS = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    }
    
    def __init__(self, api_key, base_url, model, timeout, max_retries, retry_delay, provider)
```

#### anthropic_adapter.py
```python
class AnthropicAdapter(BaseAdapter):
    name = "anthropic"
    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    
    def __init__(self, api_key, base_url, model, timeout, max_retries, retry_delay)
```

#### client.py
```python
class LLMClient:
    def __init__(self, models: list[ModelConfig], selection_strategy, max_retries, retry_delay)
    
    async def generate(
        self,
        messages: list[Message],
        system: str = "",
        tools: list[Tool] | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        model_name: str | None = None,
        require_capability: str | None = None,
        extra_params: dict | None = None,
    ) -> LLMResponse
    
    async def generate_stream(...) -> AsyncIterator[StreamChunk]
    
    async def health_check(self) -> dict[str, bool]
    
    def get_model_status(self) -> dict[str, dict]
    
    def reset_cooldowns(self)
    
    async def close(self)

@dataclass
class ModelConfig:
    name: str
    adapter_type: AdapterType  # OPENAI, DEEPSEEK, ZHIPU, ANTHROPIC
    model: str
    api_key: str
    base_url: str | None = None
    priority: int = 1
    max_tokens: int = 4096
    temperature: float = 1.0
    timeout: int = 180
    max_retries: int = 3
    retry_delay: float = 1.0
    enabled: bool = True
    capabilities: list[str] = field(default_factory=lambda: ["text"])
```

### 3. 核心特性

1. **适配器模式**: 通过BaseAdapter抽象类统一不同LLM提供商的接口
2. **故障切换**: 当一个模型失败时自动切换到下一个可用模型
3. **重试机制**: 支持配置重试次数和延迟
4. **负载均衡**: 支持balance(负载均衡)和random(随机)两种选择策略
5. **冷却机制**: 失败的模型会进入冷却期，避免频繁重试
6. **能力过滤**: 支持根据能力(text, vision, tools等)筛选模型
7. **流式输出**: 支持generate_stream方法进行流式响应

### 4. 使用示例

```python
from src.llm import LLMClient, ModelConfig, AdapterType, Message

# 创建客户端
models = [
    ModelConfig(
        name="gpt4",
        adapter_type=AdapterType.OPENAI,
        model="gpt-4o",
        api_key="sk-xxx",
        priority=1,
        capabilities=["text", "vision", "tools"],
    ),
    ModelConfig(
        name="claude",
        adapter_type=AdapterType.ANTHROPIC,
        model="claude-sonnet-4-20250514",
        api_key="sk-xxx",
        priority=2,
        capabilities=["text", "vision", "tools"],
    ),
]

client = LLMClient(models=models)

# 生成响应
response = await client.generate(
    messages=[Message(role="user", content="Hello!")],
    system="You are a helpful assistant.",
)

# 流式生成
async for chunk in client.generate_stream(
    messages=[Message(role="user", content="Hello!")],
):
    print(chunk.content, end="")
```

## 可优化方向

1. **配置文件支持**: 添加从YAML/JSON配置文件加载模型配置的功能
2. **使用统计持久化**: 将使用统计保存到数据库
3. **成本计算**: 添加token成本计算功能
4. **并发控制**: 添加全局并发限制，防止API限流
5. **缓存机制**: 对相同请求添加缓存支持
6. **更多适配器**: 添加对Gemini、通义千问等更多模型的支持
7. **工具调用优化**: 改进工具调用的格式转换和处理
8. **多模态支持**: 完善图片、音频、视频等多模态内容的处理

## 参考设计

- MaiBot的`src/llm_models/utils_model.py`中的`LLMRequest`类
- OpenAkita的`src/openakita/llm/client.py`中的`LLMClient`类
