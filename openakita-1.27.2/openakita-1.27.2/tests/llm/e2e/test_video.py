"""
端到端测试 - 视频理解 (6 个)

E2E-V01 ~ E2E-V06
"""

import pytest
from unittest.mock import AsyncMock

from openakita.llm.types import (
    Message,
    TextBlock,
    VideoBlock,
    VideoContent,
    EndpointConfig,
    LLMResponse,
    Usage,
    StopReason,
    UnsupportedMediaError,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def video_client():
    """创建支持视频的客户端"""
    endpoints = [
        EndpointConfig(
            name="kimi-video",
            provider="moonshot",
            api_type="openai",
            base_url="https://api.moonshot.cn/v1",
            api_key_env="MOONSHOT_KEY",
            model="kimi-k2.5",
            priority=1,
            capabilities=["text", "vision", "video", "tools"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


@pytest.fixture
def no_video_client():
    """创建不支持视频的客户端"""
    endpoints = [
        EndpointConfig(
            name="no-video",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_KEY",
            model="claude-3-sonnet",
            priority=1,
            capabilities=["text", "vision"],  # 没有 video
        ),
    ]
    return LLMClient(endpoints=endpoints)


def create_test_video() -> VideoContent:
    """创建测试视频"""
    return VideoContent(
        media_type="video/mp4",
        data="base64_video_placeholder"
    )


def create_mock_response(text: str):
    """创建模拟响应"""
    return LLMResponse(
        id="msg_123",
        content=[TextBlock(text=text)],
        stop_reason=StopReason.END_TURN,
        usage=Usage(input_tokens=500, output_tokens=100),
        model="kimi-k2.5",
    )


class TestVideoUnderstanding:
    """视频理解测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_v01_describe_video(self, video_client):
        """E2E-V01: 描述视频内容"""
        mock_response = create_mock_response(
            "This video shows a person walking in a park. "
            "The scene is peaceful with trees and flowers."
        )
        
        for provider in video_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        video = create_test_video()
        
        response = await video_client.chat(
            messages=[Message(role="user", content=[
                VideoBlock(video=video),
                TextBlock(text="Describe what's happening in this video"),
            ])],
        )
        
        assert response.text is not None
        assert len(response.text) > 0
    
    @pytest.mark.asyncio
    async def test_e2e_v02_video_with_question(self, video_client):
        """E2E-V02: 视频+问题"""
        mock_response = create_mock_response("There are 3 people visible in the video.")
        
        for provider in video_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        video = create_test_video()
        
        response = await video_client.chat(
            messages=[Message(role="user", content=[
                VideoBlock(video=video),
                TextBlock(text="How many people are in this video?"),
            ])],
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_v03_video_summarize(self, video_client):
        """E2E-V03: 视频摘要"""
        mock_response = create_mock_response(
            "Summary: A cooking tutorial showing how to make pasta. "
            "Duration: approximately 5 minutes. "
            "Key steps: boiling water, adding pasta, preparing sauce."
        )
        
        for provider in video_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        video = create_test_video()
        
        response = await video_client.chat(
            messages=[Message(role="user", content=[
                VideoBlock(video=video),
                TextBlock(text="Summarize this video"),
            ])],
        )
        
        assert response.text is not None


class TestVideoRouting:
    """视频路由测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_v04_video_endpoint_selection(self, video_client):
        """E2E-V04: 视频端点选择"""
        mock_response = create_mock_response("Video processed by Kimi.")
        
        for provider in video_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        video = create_test_video()
        
        response = await video_client.chat(
            messages=[Message(role="user", content=[
                VideoBlock(video=video),
                TextBlock(text="Analyze"),
            ])],
        )
        
        # 应该选择支持视频的端点
        assert video_client.providers["kimi-video"].chat.called
    
    @pytest.mark.asyncio
    async def test_e2e_v05_no_video_support_error(self, no_video_client):
        """E2E-V05: 无视频支持报错"""
        video = create_test_video()
        
        with pytest.raises(UnsupportedMediaError):
            await no_video_client.chat(
                messages=[Message(role="user", content=[
                    VideoBlock(video=video),
                    TextBlock(text="Analyze"),
                ])],
            )


class TestVideoFormats:
    """视频格式测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_v06_mp4_format(self, video_client):
        """E2E-V06: MP4格式"""
        mock_response = create_mock_response("MP4 video processed successfully.")
        
        for provider in video_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        video = VideoContent(
            media_type="video/mp4",
            data="base64_mp4_data"
        )
        
        response = await video_client.chat(
            messages=[Message(role="user", content=[
                VideoBlock(video=video),
                TextBlock(text="Analyze this video"),
            ])],
        )
        
        assert response.text is not None
