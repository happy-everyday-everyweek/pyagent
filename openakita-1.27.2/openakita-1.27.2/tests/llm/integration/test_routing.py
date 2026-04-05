"""
集成测试 - 端点切换和能力分流 (15 个)

IT-S01 ~ IT-S10, IT-R01 ~ IT-R05
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from openakita.llm.types import (
    LLMRequest,
    LLMResponse,
    Message,
    TextBlock,
    ImageBlock,
    VideoBlock,
    AudioBlock,
    DocumentBlock,
    ImageContent,
    VideoContent,
    AudioContent,
    DocumentContent,
    EndpointConfig,
    Usage,
    StopReason,
    UnsupportedMediaError,
    AllEndpointsFailedError,
    LLMError,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def multi_endpoint_client():
    """创建多端点客户端"""
    endpoints = [
        EndpointConfig(
            name="claude-primary",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_KEY",
            model="claude-3-sonnet",
            priority=1,
            capabilities=["text", "vision", "tools"],
        ),
        EndpointConfig(
            name="qwen-backup",
            provider="dashscope",
            api_type="openai",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="DASHSCOPE_KEY",
            model="qwen-plus",
            priority=2,
            capabilities=["text", "tools", "thinking"],
        ),
        EndpointConfig(
            name="kimi-video",
            provider="moonshot",
            api_type="openai",
            base_url="https://api.moonshot.cn/v1",
            api_key_env="MOONSHOT_KEY",
            model="kimi-k2.5",
            priority=10,
            capabilities=["text", "vision", "video", "tools"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


def mock_successful_response():
    """创建模拟成功响应"""
    return LLMResponse(
        id="test-123",
        content=[TextBlock(text="Success!")],
        stop_reason=StopReason.END_TURN,
        usage=Usage(input_tokens=10, output_tokens=5),
        model="test-model",
    )


class TestPrioritySelection:
    """优先级选择测试"""
    
    @pytest.mark.asyncio
    async def test_it_s01_priority_selection(self, multi_endpoint_client):
        """IT-S01: 按优先级选择"""
        # Mock 所有 provider 的 chat 方法
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        # 应该使用优先级最高的端点 (claude-primary)
        assert multi_endpoint_client.providers["claude-primary"].chat.called


class TestCapabilityFiltering:
    """能力过滤测试"""
    
    @pytest.mark.asyncio
    async def test_it_s02_vision_filtering(self, multi_endpoint_client):
        """IT-S02: Vision 能力过滤"""
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())
        
        image = ImageContent(media_type="image/png", data="abc123")
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="Describe"),
            ])],
        )
        
        # 应该选择支持 vision 的端点
        # claude-primary 和 kimi-video 都支持 vision，应该选 claude-primary（优先级更高）
        assert multi_endpoint_client.providers["claude-primary"].chat.called
    
    @pytest.mark.asyncio
    async def test_it_s03_video_filtering(self, multi_endpoint_client):
        """IT-S03: Video 能力过滤"""
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())
        
        video = VideoContent(media_type="video/mp4", data="video_data")
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content=[
                VideoBlock(video=video),
                TextBlock(text="Describe"),
            ])],
        )
        
        # 只有 kimi-video 支持视频
        assert multi_endpoint_client.providers["kimi-video"].chat.called
    
    @pytest.mark.asyncio
    async def test_it_s04_tools_filtering(self, multi_endpoint_client):
        """IT-S04: Tools 能力过滤"""
        from openakita.llm.types import Tool
        
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())
        
        tool = Tool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}}
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Use tool")],
            tools=[tool],
        )
        
        # 所有三个端点都支持 tools，应该选优先级最高的
        assert multi_endpoint_client.providers["claude-primary"].chat.called
    
    @pytest.mark.asyncio
    async def test_it_s05_thinking_filtering(self, multi_endpoint_client):
        """IT-S05: Thinking 能力过滤"""
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Think deeply")],
            enable_thinking=True,
        )
        
        # 只有 qwen-backup 支持 thinking
        assert multi_endpoint_client.providers["qwen-backup"].chat.called
    
    @pytest.mark.asyncio
    async def test_it_s06_combined_filtering(self, multi_endpoint_client):
        """IT-S06: 组合能力过滤"""
        from openakita.llm.types import Tool
        
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())
        
        image = ImageContent(media_type="image/png", data="abc123")
        tool = Tool(
            name="analyze",
            description="Analyze image",
            input_schema={"type": "object", "properties": {}}
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="Analyze this"),
            ])],
            tools=[tool],
        )
        
        # 需要 vision + tools，claude-primary 和 kimi-video 都满足
        # 应该选 claude-primary（优先级更高）
        assert multi_endpoint_client.providers["claude-primary"].chat.called


class TestFallback:
    """降级处理测试"""
    
    @pytest.mark.asyncio
    async def test_it_s07_no_match_fallback(self, multi_endpoint_client):
        """IT-S07: 无匹配降级"""
        # 创建一个需要不存在能力的请求
        # 移除所有端点的 thinking 能力来测试降级
        for name, provider in multi_endpoint_client.providers.items():
            provider.config.capabilities = ["text"]  # 只保留 text
            provider.chat = AsyncMock(return_value=mock_successful_response())
        
        # 请求 thinking 但没有端点支持
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Think")],
            enable_thinking=True,
        )
        
        # 应该警告但使用首选端点
        assert multi_endpoint_client.providers["claude-primary"].chat.called
    
    @pytest.mark.asyncio
    async def test_it_s08_video_no_match_soft_degradation(self):
        """IT-S08: Video 无匹配 → 软降级（不再抛异常）"""
        endpoints = [
            EndpointConfig(
                name="no-video",
                provider="anthropic",
                api_type="anthropic",
                base_url="https://api.anthropic.com",
                api_key_env="API_KEY",
                model="claude-3-sonnet",
                priority=1,
                capabilities=["text", "vision"],  # 没有 video
            ),
        ]
        client = LLMClient(endpoints=endpoints)

        for name, provider in client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())

        video = VideoContent(media_type="video/mp4", data="video_data")

        # 不再抛 UnsupportedMediaError，而是软降级
        response = await client.chat(
            messages=[Message(role="user", content=[
                VideoBlock(video=video),
                TextBlock(text="Describe"),
            ])],
        )
        assert response is not None


class TestFailover:
    """故障切换测试"""
    
    @pytest.mark.asyncio
    async def test_it_s09_auto_failover(self, multi_endpoint_client):
        """IT-S09: 故障自动切换"""
        # 第一个端点失败
        multi_endpoint_client.providers["claude-primary"].chat = AsyncMock(
            side_effect=LLMError("Connection failed")
        )
        # 第二个端点成功
        multi_endpoint_client.providers["qwen-backup"].chat = AsyncMock(
            return_value=mock_successful_response()
        )
        multi_endpoint_client.providers["kimi-video"].chat = AsyncMock(
            return_value=mock_successful_response()
        )
        
        response = await multi_endpoint_client.chat(
            messages=[Message(role="user", content="Hello")],
        )
        
        # 应该切换到 qwen-backup
        assert multi_endpoint_client.providers["qwen-backup"].chat.called
    
    @pytest.mark.asyncio
    async def test_it_s10_all_failed(self, multi_endpoint_client):
        """IT-S10: 全部故障"""
        # 所有端点都失败
        for name, provider in multi_endpoint_client.providers.items():
            provider.chat = AsyncMock(side_effect=LLMError("Failed"))
        
        with pytest.raises(AllEndpointsFailedError):
            await multi_endpoint_client.chat(
                messages=[Message(role="user", content="Hello")],
            )


# ── IT-R01 ~ IT-R05: audio/pdf 端点筛选和软降级 ──


@pytest.fixture
def audio_pdf_client():
    """创建含 audio/pdf 能力端点的客户端"""
    endpoints = [
        EndpointConfig(
            name="text-only",
            provider="openai",
            api_type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="KEY1",
            model="gpt-4o",
            priority=1,
            capabilities=["text", "vision", "tools"],
        ),
        EndpointConfig(
            name="gemini-full",
            provider="google",
            api_type="openai",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            api_key_env="KEY2",
            model="gemini-2.0-flash",
            priority=5,
            capabilities=["text", "vision", "tools", "audio", "pdf"],
        ),
        EndpointConfig(
            name="claude-pdf",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="KEY3",
            model="claude-3-sonnet",
            priority=3,
            capabilities=["text", "vision", "tools", "pdf"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


class TestAudioPdfFiltering:
    """audio/pdf 端点筛选测试"""

    @pytest.mark.asyncio
    async def test_it_r01_audio_filtering(self, audio_pdf_client):
        """IT-R01: require_audio=True 只选择有 audio 能力的端点"""
        for name, provider in audio_pdf_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())

        audio = AudioContent(media_type="audio/wav", data="test_audio", format="wav")
        response = await audio_pdf_client.chat(
            messages=[Message(role="user", content=[
                AudioBlock(audio=audio),
                TextBlock(text="Transcribe"),
            ])],
        )

        # 只有 gemini-full 支持 audio
        assert audio_pdf_client.providers["gemini-full"].chat.called

    @pytest.mark.asyncio
    async def test_it_r02_pdf_filtering(self, audio_pdf_client):
        """IT-R02: require_pdf=True 选择有 pdf 能力的端点"""
        for name, provider in audio_pdf_client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())

        doc = DocumentContent(media_type="application/pdf", data="pdf_data", filename="test.pdf")
        response = await audio_pdf_client.chat(
            messages=[Message(role="user", content=[
                DocumentBlock(document=doc),
                TextBlock(text="Summarize"),
            ])],
        )

        # claude-pdf (priority=3) 和 gemini-full (priority=5) 都支持 pdf
        # 应该选优先级更高的 claude-pdf
        assert audio_pdf_client.providers["claude-pdf"].chat.called

    @pytest.mark.asyncio
    async def test_it_r03_audio_soft_degradation(self):
        """IT-R03: 无 audio 端点 → 软降级（警告但不报错）"""
        endpoints = [
            EndpointConfig(
                name="no-audio",
                provider="openai",
                api_type="openai",
                base_url="https://api.openai.com/v1",
                api_key_env="KEY",
                model="gpt-4o",
                priority=1,
                capabilities=["text", "vision"],
            ),
        ]
        client = LLMClient(endpoints=endpoints)

        for name, provider in client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())

        audio = AudioContent(media_type="audio/wav", data="test_audio", format="wav")

        # 不应抛异常，应软降级
        response = await client.chat(
            messages=[Message(role="user", content=[
                AudioBlock(audio=audio),
                TextBlock(text="Transcribe"),
            ])],
        )

        assert response is not None
        assert client.providers["no-audio"].chat.called

    @pytest.mark.asyncio
    async def test_it_r04_pdf_soft_degradation(self):
        """IT-R04: 无 pdf 端点 → 软降级"""
        endpoints = [
            EndpointConfig(
                name="no-pdf",
                provider="openai",
                api_type="openai",
                base_url="https://api.openai.com/v1",
                api_key_env="KEY",
                model="gpt-4o",
                priority=1,
                capabilities=["text", "vision"],
            ),
        ]
        client = LLMClient(endpoints=endpoints)

        for name, provider in client.providers.items():
            provider.chat = AsyncMock(return_value=mock_successful_response())

        doc = DocumentContent(media_type="application/pdf", data="pdf_data", filename="test.pdf")

        # 不应抛异常
        response = await client.chat(
            messages=[Message(role="user", content=[
                DocumentBlock(document=doc),
                TextBlock(text="Summarize"),
            ])],
        )

        assert response is not None
        assert client.providers["no-pdf"].chat.called

    def test_it_r05_has_any_endpoint_with_capability(self, audio_pdf_client):
        """IT-R05: has_any_endpoint_with_capability 正确检测"""
        assert audio_pdf_client.has_any_endpoint_with_capability("audio") is True
        assert audio_pdf_client.has_any_endpoint_with_capability("pdf") is True
        assert audio_pdf_client.has_any_endpoint_with_capability("text") is True

        # 创建无 audio 的客户端
        endpoints = [
            EndpointConfig(
                name="basic",
                provider="openai",
                api_type="openai",
                base_url="https://api.openai.com/v1",
                api_key_env="KEY",
                model="gpt-4",
                priority=1,
                capabilities=["text"],
            ),
        ]
        basic_client = LLMClient(endpoints=endpoints)
        assert basic_client.has_any_endpoint_with_capability("audio") is False
        assert basic_client.has_any_endpoint_with_capability("pdf") is False
