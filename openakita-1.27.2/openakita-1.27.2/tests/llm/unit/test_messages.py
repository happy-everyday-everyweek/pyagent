"""
单元测试 - 消息转换器 (15 个)

UT-M01 ~ UT-M15
"""

import pytest
from openakita.llm.types import (
    Message,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    ImageBlock,
    ImageContent,
    VideoBlock,
    VideoContent,
    AudioBlock,
    AudioContent,
    DocumentBlock,
    DocumentContent,
)
from openakita.llm.converters.messages import (
    convert_messages_to_openai,
    convert_messages_from_openai,
)


class TestAnthropicToInternal:
    """Anthropic 格式到内部格式转换"""
    
    def test_ut_m01_simple_text(self):
        """UT-M01: Anthropic→内部: 简单文本"""
        # Anthropic 格式消息（内部格式）
        messages = [
            Message(role="user", content="Hello")
        ]
        
        # 转换到 OpenAI 格式再转回来验证
        openai_msgs = convert_messages_to_openai(messages)
        
        assert len(openai_msgs) == 1
        assert openai_msgs[0]["role"] == "user"
        assert openai_msgs[0]["content"] == "Hello"
    
    def test_ut_m02_multi_turn(self):
        """UT-M02: Anthropic→内部: 多轮对话"""
        messages = [
            Message(role="user", content="What is 2+2?"),
            Message(role="assistant", content=[TextBlock(text="4")]),
            Message(role="user", content="Thanks"),
        ]
        
        openai_msgs = convert_messages_to_openai(messages)
        
        assert len(openai_msgs) == 3
        assert openai_msgs[0]["role"] == "user"
        assert openai_msgs[1]["role"] == "assistant"
        assert openai_msgs[2]["role"] == "user"
    
    def test_ut_m03_system_message(self):
        """UT-M03: Anthropic→内部: 系统消息"""
        messages = [
            Message(role="user", content="Hello")
        ]
        
        openai_msgs = convert_messages_to_openai(messages, system="You are helpful.")
        
        assert len(openai_msgs) == 2
        assert openai_msgs[0]["role"] == "system"
        assert openai_msgs[0]["content"] == "You are helpful."
        assert openai_msgs[1]["role"] == "user"
    
    def test_ut_m04_image_message(self, sample_image_content):
        """UT-M04: Anthropic→内部: 图片消息"""
        messages = [
            Message(role="user", content=[
                ImageBlock(image=sample_image_content),
                TextBlock(text="What's in this image?"),
            ])
        ]
        
        openai_msgs = convert_messages_to_openai(messages)
        
        assert len(openai_msgs) == 1
        content = openai_msgs[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["type"] == "image_url"
        assert content[1]["type"] == "text"


class TestInternalToOpenAI:
    """内部格式到 OpenAI 格式转换"""
    
    def test_ut_m05_simple_text(self):
        """UT-M05: 内部→OpenAI: 简单文本"""
        messages = [
            Message(role="user", content="Hello")
        ]
        
        openai_msgs = convert_messages_to_openai(messages)
        
        assert openai_msgs[0]["content"] == "Hello"
    
    def test_ut_m06_multi_turn(self):
        """UT-M06: 内部→OpenAI: 多轮对话"""
        messages = [
            Message(role="user", content="Hi"),
            Message(role="assistant", content=[TextBlock(text="Hello!")]),
            Message(role="user", content="How are you?"),
        ]
        
        openai_msgs = convert_messages_to_openai(messages)
        
        assert len(openai_msgs) == 3
        assert openai_msgs[0]["content"] == "Hi"
        assert openai_msgs[1]["content"] == "Hello!"
        assert openai_msgs[2]["content"] == "How are you?"
    
    def test_ut_m07_system_embedded(self):
        """UT-M07: 内部→OpenAI: 系统消息嵌入 messages"""
        messages = [Message(role="user", content="Test")]
        
        openai_msgs = convert_messages_to_openai(messages, system="Be helpful")
        
        # OpenAI 格式中 system 是第一条消息
        assert openai_msgs[0]["role"] == "system"
        assert openai_msgs[0]["content"] == "Be helpful"
    
    def test_ut_m08_image_format(self, sample_image_content):
        """UT-M08: 内部→OpenAI: 图片消息 image_url 格式"""
        messages = [
            Message(role="user", content=[
                ImageBlock(image=sample_image_content),
            ])
        ]
        
        openai_msgs = convert_messages_to_openai(messages)
        content = openai_msgs[0]["content"]
        
        assert content[0]["type"] == "image_url"
        assert "url" in content[0]["image_url"]
        assert content[0]["image_url"]["url"].startswith("data:image/")


class TestOpenAIToInternal:
    """OpenAI 格式到内部格式转换"""
    
    def test_ut_m09_simple_text(self):
        """UT-M09: OpenAI→内部: 简单文本"""
        openai_msgs = [
            {"role": "user", "content": "Hello"}
        ]
        
        messages, system = convert_messages_from_openai(openai_msgs)
        
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert system == ""
    
    def test_ut_m10_image_message(self):
        """UT-M10: OpenAI→内部: 图片消息"""
        openai_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this:"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc123"}}
                ]
            }
        ]
        
        messages, _ = convert_messages_from_openai(openai_msgs)
        
        assert len(messages) == 1
        assert isinstance(messages[0].content, list)
        assert len(messages[0].content) == 2


class TestEdgeCases:
    """边缘情况测试"""
    
    def test_ut_m11_empty_messages(self):
        """UT-M11: 空消息处理"""
        messages = []
        
        openai_msgs = convert_messages_to_openai(messages)
        
        assert openai_msgs == []
    
    def test_ut_m12_special_characters(self):
        """UT-M12: 特殊字符处理"""
        messages = [
            Message(role="user", content="Hello <world> & \"quotes\" 'apostrophe' \n\t")
        ]
        
        openai_msgs = convert_messages_to_openai(messages)
        
        # 特殊字符应保持原样
        assert '<world>' in openai_msgs[0]["content"]
        assert '&' in openai_msgs[0]["content"]
        assert '"quotes"' in openai_msgs[0]["content"]


class TestNewMediaTypes:
    """新媒体类型解析测试"""

    def test_ut_m13_video_url_to_video_block(self):
        """UT-M13: OpenAI video_url → VideoBlock"""
        openai_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this video:"},
                    {"type": "video_url", "video_url": {"url": "data:video/mp4;base64,AAAAIGZ0eXBpc29t"}},
                ]
            }
        ]

        messages, _ = convert_messages_from_openai(openai_msgs)

        assert len(messages) == 1
        content = messages[0].content
        assert isinstance(content, list)
        assert len(content) == 2
        assert isinstance(content[0], TextBlock)
        assert isinstance(content[1], VideoBlock)
        assert content[1].video.media_type == "video/mp4"
        assert content[1].video.data == "AAAAIGZ0eXBpc29t"

    def test_ut_m14_input_audio_to_audio_block(self):
        """UT-M14: OpenAI input_audio → AudioBlock"""
        openai_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "input_audio", "input_audio": {"data": "audio_base64_data", "format": "wav"}},
                ]
            }
        ]

        messages, _ = convert_messages_from_openai(openai_msgs)

        assert len(messages) == 1
        content = messages[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], AudioBlock)
        assert content[0].audio.data == "audio_base64_data"
        assert content[0].audio.format == "wav"
        assert content[0].audio.media_type == "audio/wav"

    def test_ut_m15_document_to_document_block(self):
        """UT-M15: Anthropic document → DocumentBlock"""
        openai_msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "document", "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": "pdf_base64_data",
                    }, "filename": "report.pdf"},
                ]
            }
        ]

        messages, _ = convert_messages_from_openai(openai_msgs)

        assert len(messages) == 1
        content = messages[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], DocumentBlock)
        assert content[0].document.data == "pdf_base64_data"
        assert content[0].document.media_type == "application/pdf"
        assert content[0].document.filename == "report.pdf"
