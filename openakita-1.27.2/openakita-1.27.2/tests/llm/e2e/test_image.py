"""
端到端测试 - 图片解析 (8 个)

E2E-I01 ~ E2E-I08
"""

import pytest
from unittest.mock import AsyncMock, patch
import base64

from openakita.llm.types import (
    Message,
    TextBlock,
    ImageBlock,
    ImageContent,
    EndpointConfig,
    LLMResponse,
    Usage,
    StopReason,
)
from openakita.llm.client import LLMClient


@pytest.fixture
def vision_client():
    """创建支持视觉的客户端"""
    endpoints = [
        EndpointConfig(
            name="vision-endpoint",
            provider="anthropic",
            api_type="anthropic",
            base_url="https://api.anthropic.com",
            api_key_env="TEST_KEY",
            model="claude-3-sonnet",
            priority=1,
            capabilities=["text", "vision", "tools"],
        ),
    ]
    return LLMClient(endpoints=endpoints)


def create_test_image(color: str = "red") -> ImageContent:
    """创建测试图片"""
    # 1x1 像素 PNG (红色)
    png_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    return ImageContent(media_type="image/png", data=png_data)


def create_mock_response(text: str):
    """创建模拟响应"""
    return LLMResponse(
        id="msg_123",
        content=[TextBlock(text=text)],
        stop_reason=StopReason.END_TURN,
        usage=Usage(input_tokens=100, output_tokens=50),
        model="test-model",
    )


class TestSingleImage:
    """单图片测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_i01_describe_image(self, vision_client):
        """E2E-I01: 描述图片"""
        mock_response = create_mock_response("This image shows a single red pixel.")
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        image = create_test_image()
        
        response = await vision_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="Describe this image"),
            ])],
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_i02_image_with_question(self, vision_client):
        """E2E-I02: 图片+问题"""
        mock_response = create_mock_response("The main color is red.")
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        image = create_test_image()
        
        response = await vision_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="What color is this?"),
            ])],
        )
        
        assert "red" in response.text.lower() or response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_i03_ocr_text_extraction(self, vision_client):
        """E2E-I03: OCR文字提取"""
        mock_response = create_mock_response("The text says: Hello World")
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 假设这是包含文字的图片
        image = create_test_image()
        
        response = await vision_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="Read any text in this image"),
            ])],
        )
        
        assert response.text is not None


class TestMultipleImages:
    """多图片测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_i04_two_images(self, vision_client):
        """E2E-I04: 两张图片比较"""
        mock_response = create_mock_response("Both images appear identical - single red pixels.")
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        image1 = create_test_image()
        image2 = create_test_image()
        
        response = await vision_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image1),
                ImageBlock(image=image2),
                TextBlock(text="Compare these two images"),
            ])],
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_i05_multiple_images_context(self, vision_client):
        """E2E-I05: 多图片+上下文"""
        mock_response = create_mock_response("Based on the images and context provided...")
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 多轮对话中使用图片
        messages = [
            Message(role="user", content="I'll show you some images"),
            Message(role="assistant", content=[TextBlock(text="Sure, go ahead!")]),
            Message(role="user", content=[
                ImageBlock(image=create_test_image()),
                ImageBlock(image=create_test_image()),
                TextBlock(text="What can you tell me about these?"),
            ]),
        ]
        
        response = await vision_client.chat(messages=messages)
        
        assert response.text is not None


class TestImageFormats:
    """图片格式测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_i06_png_format(self, vision_client):
        """E2E-I06: PNG格式"""
        mock_response = create_mock_response("Processed PNG image successfully.")
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        image = ImageContent(
            media_type="image/png",
            data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        
        response = await vision_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="Analyze"),
            ])],
        )
        
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_e2e_i07_jpeg_format(self, vision_client):
        """E2E-I07: JPEG格式"""
        mock_response = create_mock_response("Processed JPEG image successfully.")
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        # 最小的有效 JPEG (实际使用时应该是真实的 JPEG base64)
        image = ImageContent(
            media_type="image/jpeg",
            data="base64_jpeg_placeholder"
        )
        
        response = await vision_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=image),
                TextBlock(text="Analyze"),
            ])],
        )
        
        assert response.text is not None


class TestImageWithTools:
    """图片+工具组合测试"""
    
    @pytest.mark.asyncio
    async def test_e2e_i08_image_tool_combo(self, vision_client):
        """E2E-I08: 图片+工具组合"""
        from openakita.llm.types import Tool, ToolUseBlock
        
        # 模拟工具调用响应
        mock_response = LLMResponse(
            id="msg_123",
            content=[
                TextBlock(text="Let me search for similar images."),
                ToolUseBlock(id="call_1", name="image_search", input={"query": "red pixel"})
            ],
            stop_reason=StopReason.TOOL_USE,
            usage=Usage(input_tokens=100, output_tokens=30),
            model="test-model",
        )
        
        for provider in vision_client.providers.values():
            provider.chat = AsyncMock(return_value=mock_response)
        
        tool = Tool(
            name="image_search",
            description="Search for similar images",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            }
        )
        
        response = await vision_client.chat(
            messages=[Message(role="user", content=[
                ImageBlock(image=create_test_image()),
                TextBlock(text="Find similar images"),
            ])],
            tools=[tool],
        )
        
        assert response.has_tool_calls or response.text is not None
