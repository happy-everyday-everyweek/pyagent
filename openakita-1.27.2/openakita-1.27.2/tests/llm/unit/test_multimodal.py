"""
单元测试 - 多模态转换器 (18 个)

UT-V01 ~ UT-V18
"""

import pytest
from openakita.llm.types import (
    ImageContent,
    VideoContent,
    AudioContent,
    DocumentContent,
    ImageBlock,
    VideoBlock,
    AudioBlock,
    DocumentBlock,
    TextBlock,
    UnsupportedMediaError,
)
from openakita.llm.converters.multimodal import (
    convert_image_to_openai,
    convert_video_to_kimi,
    convert_content_blocks_to_openai,
    convert_content_blocks,
    convert_audio_to_openai,
    convert_audio_to_gemini,
    convert_audio_to_dashscope,
    convert_document_to_anthropic,
    convert_document_to_gemini,
    detect_media_type,
    detect_media_type_from_base64,
    has_images,
    has_videos,
)


class TestImageConversion:
    """图片转换测试"""
    
    def test_ut_v01_base64_conversion(self, sample_image_content):
        """UT-V01: 图片 base64 转换"""
        openai_format = convert_image_to_openai(sample_image_content)
        
        assert openai_format["type"] == "image_url"
        url = openai_format["image_url"]["url"]
        assert url.startswith("data:image/png;base64,")
    
    def test_ut_v02_url_conversion(self):
        """UT-V02: 图片 URL 转换"""
        image = ImageContent.from_url("https://example.com/image.jpg")
        
        # URL 类型直接使用
        assert image.media_type == "url"
        assert image.to_data_url() == "https://example.com/image.jpg"


class TestVideoConversion:
    """视频转换测试"""
    
    def test_ut_v03_base64_conversion(self):
        """UT-V03: 视频 base64 转换"""
        video = VideoContent(
            media_type="video/mp4",
            data="base64_video_content"
        )
        
        kimi_format = convert_video_to_kimi(video)
        
        assert kimi_format["type"] == "video_url"
        url = kimi_format["video_url"]["url"]
        assert url.startswith("data:video/mp4;base64,")


class TestMixedContent:
    """混合内容测试"""
    
    def test_ut_v04_image_text_mixed(self, sample_image_content):
        """UT-V04: 图片+文本混合"""
        blocks = [
            ImageBlock(image=sample_image_content),
            TextBlock(text="What's in this image?"),
        ]
        
        openai_content = convert_content_blocks_to_openai(blocks)
        
        assert isinstance(openai_content, list)
        assert len(openai_content) == 2
        assert openai_content[0]["type"] == "image_url"
        assert openai_content[1]["type"] == "text"
    
    def test_ut_v05_multiple_images(self, sample_image_content):
        """UT-V05: 多图片消息"""
        blocks = [
            ImageBlock(image=sample_image_content),
            ImageBlock(image=sample_image_content),
            TextBlock(text="Compare these images"),
        ]
        
        openai_content = convert_content_blocks_to_openai(blocks)
        
        assert len(openai_content) == 3
        assert openai_content[0]["type"] == "image_url"
        assert openai_content[1]["type"] == "image_url"
        assert openai_content[2]["type"] == "text"


class TestProviderSpecific:
    """服务商特定格式测试"""
    
    def test_ut_v06_kimi_video_format(self):
        """UT-V06: Kimi 视频格式"""
        video = VideoContent(media_type="video/mp4", data="abc123")
        blocks = [VideoBlock(video=video)]
        
        # Kimi 格式
        kimi_content = convert_content_blocks_to_openai(blocks, provider="moonshot")
        
        assert kimi_content[0]["type"] == "video_url"
        assert "video_url" in kimi_content[0]
    
    def test_ut_v07_unsupported_video_graceful_degradation(self):
        """UT-V07: 不支持视频端点 → 优雅降级为文本描述"""
        video = VideoContent(media_type="video/mp4", data="abc123")
        blocks = [VideoBlock(video=video)]
        
        # OpenAI 不支持视频 → 应降级为文本描述而非抛异常
        result = convert_content_blocks_to_openai(blocks, provider="openai")
        
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "视频" in result[0]["text"]


class TestMediaTypeDetection:
    """媒体类型检测测试"""
    
    def test_ut_v08_detect_formats(self):
        """UT-V08: 图片格式检测"""
        # JPEG magic bytes
        jpeg_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        assert detect_media_type(jpeg_data) == "image/jpeg"
        
        # PNG magic bytes
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        assert detect_media_type(png_data) == "image/png"
        
        # GIF magic bytes
        gif_data = b'GIF89a' + b'\x00' * 100
        assert detect_media_type(gif_data) == "image/gif"


class TestHelperFunctions:
    """辅助函数测试"""
    
    def test_has_images(self, sample_image_content):
        """测试 has_images"""
        with_image = [ImageBlock(image=sample_image_content), TextBlock(text="test")]
        without_image = [TextBlock(text="test")]
        
        assert has_images(with_image) == True
        assert has_images(without_image) == False
        assert has_images("plain string") == False
    
    def test_has_videos(self):
        """测试 has_videos"""
        video = VideoContent(media_type="video/mp4", data="test")
        with_video = [VideoBlock(video=video)]
        without_video = [TextBlock(text="test")]
        
        assert has_videos(with_video) == True
        assert has_videos(without_video) == False


class TestAudioConversion:
    """音频转换测试"""

    def test_ut_v09_audio_to_openai(self, sample_audio_content):
        """UT-V09: convert_audio_to_openai → input_audio 格式"""
        result = convert_audio_to_openai(sample_audio_content)

        assert result["type"] == "input_audio"
        assert "input_audio" in result
        assert result["input_audio"]["format"] == "wav"
        assert len(result["input_audio"]["data"]) > 0

    def test_ut_v10_audio_to_gemini(self, sample_audio_content):
        """UT-V10: convert_audio_to_gemini → data URL 格式"""
        result = convert_audio_to_gemini(sample_audio_content)

        assert result["type"] == "image_url"
        url = result["image_url"]["url"]
        assert url.startswith("data:audio/wav;base64,")

    def test_ut_v11_audio_to_dashscope(self, sample_audio_content):
        """UT-V11: convert_audio_to_dashscope → audio_url 格式"""
        result = convert_audio_to_dashscope(sample_audio_content)

        assert result["type"] == "audio_url"
        url = result["audio_url"]["url"]
        assert url.startswith("data:audio/wav;base64,")


class TestDocumentConversion:
    """文档转换测试"""

    def test_ut_v12_document_to_anthropic(self, sample_document_content):
        """UT-V12: convert_document_to_anthropic → document + base64 格式"""
        result = convert_document_to_anthropic(sample_document_content)

        assert result["type"] == "document"
        assert result["source"]["type"] == "base64"
        assert result["source"]["media_type"] == "application/pdf"
        assert len(result["source"]["data"]) > 0

    def test_ut_v13_document_to_gemini(self, sample_document_content):
        """UT-V13: convert_document_to_gemini → data URL 格式"""
        result = convert_document_to_gemini(sample_document_content)

        assert result["type"] == "image_url"
        url = result["image_url"]["url"]
        assert url.startswith("data:application/pdf;base64,")


class TestGracefulDegradation:
    """优雅降级测试"""

    def test_ut_v14_video_degradation(self):
        """UT-V14: 不支持视频的端点 → 降级为文本"""
        video = VideoContent(media_type="video/mp4", data="abc123")
        blocks = [VideoBlock(video=video)]

        result = convert_content_blocks(blocks, provider="openai")

        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "视频" in result[0]["text"]

    def test_ut_v15_audio_degradation(self, sample_audio_content):
        """UT-V15: 不支持音频的端点 → 降级为文本"""
        blocks = [AudioBlock(audio=sample_audio_content)]

        result = convert_content_blocks(blocks, provider="anthropic")

        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "音频" in result[0]["text"]

    def test_ut_v16_document_degradation(self, sample_document_content):
        """UT-V16: 不支持文档的端点 → 降级为文本"""
        blocks = [DocumentBlock(document=sample_document_content)]

        result = convert_content_blocks(blocks, provider="openai")

        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert "文档" in result[0]["text"]

    def test_ut_v17_mixed_multimodal(self, sample_image_content, sample_audio_content, sample_document_content):
        """UT-V17: 混合多模态消息正确分发到各转换器"""
        video = VideoContent(media_type="video/mp4", data="video_data")
        blocks = [
            TextBlock(text="Check all these"),
            ImageBlock(image=sample_image_content),
            VideoBlock(video=video),
            AudioBlock(audio=sample_audio_content),
            DocumentBlock(document=sample_document_content),
        ]

        # Google provider 支持所有模态
        result = convert_content_blocks(blocks, provider="google")

        assert len(result) == 5
        assert result[0]["type"] == "text"
        assert result[1]["type"] == "image_url"
        assert result[2]["type"] == "image_url"  # Gemini video uses image_url
        assert result[3]["type"] == "image_url"  # Gemini audio uses image_url
        assert result[4]["type"] == "image_url"  # Gemini document uses image_url

    def test_ut_v18_alias_identity(self):
        """UT-V18: convert_content_blocks_to_openai 是 convert_content_blocks 的别名"""
        assert convert_content_blocks_to_openai is convert_content_blocks
