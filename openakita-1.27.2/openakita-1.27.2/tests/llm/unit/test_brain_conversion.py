"""
单元测试 - Brain 消息转换 (8 个)

UT-B01 ~ UT-B08

验证 Brain._convert_messages_to_llm 能正确处理 Anthropic 和 OpenAI 两种格式。
"""

import pytest
from openakita.llm.types import (
    ImageBlock,
    ImageContent,
    VideoBlock,
    VideoContent,
    AudioBlock,
    AudioContent,
    DocumentBlock,
    DocumentContent,
    TextBlock,
)

# Brain 依赖 anthropic SDK 和 settings，需要 mock 掉外部依赖
from unittest.mock import patch, MagicMock


@pytest.fixture
def brain_converter():
    """创建 Brain 实例用于测试 _convert_messages_to_llm。

    由于 Brain.__init__ 需要读取配置文件和初始化 LLMClient，
    我们 mock 掉外部依赖只保留转换逻辑。
    """
    with (
        patch("openakita.core.brain.settings") as mock_settings,
        patch("openakita.core.brain.get_default_config_path") as mock_config_path,
        patch("openakita.core.brain.LLMClient") as mock_client,
    ):
        mock_settings.max_tokens = 4096
        mock_settings.thinking_mode = "auto"
        mock_config_path.return_value = MagicMock(exists=MagicMock(return_value=False))
        mock_client.return_value = MagicMock(
            endpoints=[],
            providers={},
        )

        from openakita.core.brain import Brain

        brain = Brain()
        yield brain


class TestAnthropicFormatConversion:
    """Anthropic 格式消息转换测试"""

    def test_ut_b01_anthropic_image(self, brain_converter):
        """UT-B01: Anthropic image → ImageBlock"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": "abc123imagedata",
                        },
                    }
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        assert result[0].role == "user"
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], ImageBlock)
        assert content[0].image.media_type == "image/jpeg"
        assert content[0].image.data == "abc123imagedata"

    def test_ut_b02_anthropic_audio(self, brain_converter):
        """UT-B02: Anthropic audio → AudioBlock"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio",
                        "source": {
                            "type": "base64",
                            "media_type": "audio/wav",
                            "data": "audio_base64_data",
                            "format": "wav",
                        },
                    }
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], AudioBlock)
        assert content[0].audio.media_type == "audio/wav"
        assert content[0].audio.data == "audio_base64_data"
        assert content[0].audio.format == "wav"

    def test_ut_b03_anthropic_document(self, brain_converter):
        """UT-B03: Anthropic document → DocumentBlock"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": "pdf_base64_data",
                        },
                        "filename": "report.pdf",
                    }
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], DocumentBlock)
        assert content[0].document.media_type == "application/pdf"
        assert content[0].document.data == "pdf_base64_data"
        assert content[0].document.filename == "report.pdf"


class TestOpenAIFormatConversion:
    """OpenAI 格式消息转换测试"""

    def test_ut_b04_openai_image_url_data_url(self, brain_converter):
        """UT-B04: OpenAI image_url data URL → ImageBlock"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg"
                        },
                    }
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], ImageBlock)
        assert content[0].image.media_type == "image/png"
        assert content[0].image.data == "iVBORw0KGgoAAAANSUhEUg"

    def test_ut_b05_openai_image_url_remote(self, brain_converter):
        """UT-B05: OpenAI image_url remote URL → ImageBlock"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://example.com/photo.jpg"
                        },
                    }
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], ImageBlock)
        # 远程 URL 通过 ImageContent.from_url 解析
        assert content[0].image is not None

    def test_ut_b06_openai_video_url(self, brain_converter):
        """UT-B06: OpenAI video_url → VideoBlock"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": "data:video/mp4;base64,AAAAIGZ0eXBpc29t"
                        },
                    }
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], VideoBlock)
        assert content[0].video.media_type == "video/mp4"
        assert content[0].video.data == "AAAAIGZ0eXBpc29t"

    def test_ut_b07_openai_input_audio(self, brain_converter):
        """UT-B07: OpenAI input_audio → AudioBlock"""
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": "audio_pcm_base64",
                            "format": "wav",
                        },
                    }
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 1
        assert isinstance(content[0], AudioBlock)
        assert content[0].audio.data == "audio_pcm_base64"
        assert content[0].audio.format == "wav"
        assert content[0].audio.media_type == "audio/wav"


class TestMixedFormatConversion:
    """混合格式共存测试"""

    def test_ut_b08_mixed_formats(self, brain_converter):
        """UT-B08: 一条消息同时包含 Anthropic 和 OpenAI 格式块"""
        messages = [
            {
                "role": "user",
                "content": [
                    # Anthropic 格式 image
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": "anthropic_image_data",
                        },
                    },
                    # OpenAI 格式 image_url
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,openai_image_data"
                        },
                    },
                    # Anthropic 格式 document
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": "pdf_data",
                        },
                        "filename": "doc.pdf",
                    },
                    # OpenAI 格式 input_audio
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": "audio_data_mixed",
                            "format": "mp3",
                        },
                    },
                    # 文本块
                    {
                        "type": "text",
                        "text": "Analyze all of these",
                    },
                ],
            }
        ]

        result = brain_converter._convert_messages_to_llm(messages)

        assert len(result) == 1
        content = result[0].content
        assert isinstance(content, list)
        assert len(content) == 5

        # Anthropic image
        assert isinstance(content[0], ImageBlock)
        assert content[0].image.media_type == "image/jpeg"
        assert content[0].image.data == "anthropic_image_data"

        # OpenAI image_url
        assert isinstance(content[1], ImageBlock)
        assert content[1].image.media_type == "image/png"
        assert content[1].image.data == "openai_image_data"

        # Anthropic document
        assert isinstance(content[2], DocumentBlock)
        assert content[2].document.media_type == "application/pdf"

        # OpenAI input_audio
        assert isinstance(content[3], AudioBlock)
        assert content[3].audio.data == "audio_data_mixed"
        assert content[3].audio.format == "mp3"
        assert content[3].audio.media_type == "audio/mpeg"

        # Text
        assert isinstance(content[4], TextBlock)
        assert content[4].text == "Analyze all of these"
