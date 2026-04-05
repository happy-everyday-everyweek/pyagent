"""
ASR语音识别模块测试
"""

import pytest
import asyncio
import tempfile
import wave
import numpy as np
from pathlib import Path

from src.voice.asr import ASRModule, ASRConfig, ASRError, AudioProcessingError


class TestASRConfig:
    """测试ASR配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = ASRConfig()
        assert config.language == "zh-CN"
        assert config.model == "default"
        assert config.enable_vad is True
        assert config.vad_threshold == 0.5
        assert config.sample_rate == 16000
        assert config.engine == "auto"
        assert config.whisper_model == "base"
        assert config.whisper_device == "auto"
        assert config.whisper_compute_type == "auto"
        assert config.use_ffmpeg is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = ASRConfig(
            language="en-US",
            model="custom",
            enable_vad=False,
            vad_threshold=0.7,
            sample_rate=24000,
            engine="whisper",
            whisper_model="small",
            whisper_device="cuda",
            whisper_compute_type="float16"
        )
        assert config.language == "en-US"
        assert config.model == "custom"
        assert config.enable_vad is False
        assert config.vad_threshold == 0.7
        assert config.sample_rate == 24000
        assert config.engine == "whisper"
        assert config.whisper_model == "small"
        assert config.whisper_device == "cuda"
        assert config.whisper_compute_type == "float16"


class TestASRModule:
    """测试ASR模块"""

    @pytest.fixture
    def asr_module(self):
        """创建ASR模块实例"""
        config = ASRConfig(engine="dummy")
        return ASRModule(config)

    @pytest.fixture
    def sample_audio_file(self):
        """创建测试音频文件"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        duration = 1.0
        sample_rate = 16000
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t)
        audio = (audio * 32767).astype(np.int16)
        
        with wave.open(tmp_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())
        
        yield tmp_path
        
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    def test_initialization(self, asr_module):
        """测试初始化"""
        assert asr_module._initialized is False
        assert asr_module.initialize() is True
        assert asr_module._initialized is True
        assert asr_module._engine_type == "dummy"

    def test_shutdown(self, asr_module):
        """测试关闭"""
        asr_module.initialize()
        assert asr_module._initialized is True
        asr_module.shutdown()
        assert asr_module._initialized is False

    @pytest.mark.asyncio
    async def test_transcribe_with_dummy_engine(self, asr_module, sample_audio_file):
        """测试使用dummy引擎转录"""
        asr_module.initialize()
        
        with open(sample_audio_file, 'rb') as f:
            audio_data = f.read()
        
        result = await asr_module.transcribe(audio_data)
        assert result == "[语音转文字结果]"

    @pytest.mark.asyncio
    async def test_transcribe_file_with_dummy_engine(self, asr_module, sample_audio_file):
        """测试使用dummy引擎转录文件"""
        asr_module.initialize()
        result = await asr_module.transcribe_file(sample_audio_file)
        assert result == "[语音转文字结果]"

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found(self, asr_module):
        """测试文件不存在的情况"""
        asr_module.initialize()
        with pytest.raises(ASRError):
            await asr_module.transcribe_file("nonexistent.wav")

    def test_set_language(self, asr_module):
        """测试设置语言"""
        assert asr_module.set_language("en-US") is True
        assert asr_module.config.language == "en-US"
        
        assert asr_module.set_language("invalid") is False
        assert asr_module.config.language == "en-US"

    def test_add_remove_hotwords(self, asr_module):
        """测试添加和移除热词"""
        asr_module.add_hotwords({"test": 1.5, "demo": 2.0})
        assert "test" in asr_module._hotwords
        assert "demo" in asr_module._hotwords
        assert asr_module._hotwords["test"] == 1.5
        
        asr_module.remove_hotword("test")
        assert "test" not in asr_module._hotwords
        assert "demo" in asr_module._hotwords

    def test_get_supported_languages(self, asr_module):
        """测试获取支持的语言列表"""
        languages = asr_module.get_supported_languages()
        assert isinstance(languages, list)
        assert "zh-CN" in languages
        assert "en-US" in languages
        assert len(languages) > 0

    def test_get_config(self, asr_module):
        """测试获取配置"""
        config = asr_module.get_config()
        assert isinstance(config, ASRConfig)
        assert config.language == "zh-CN"

    def test_get_engine_info(self, asr_module):
        """测试获取引擎信息"""
        asr_module.initialize()
        info = asr_module.get_engine_info()
        assert isinstance(info, dict)
        assert "engine_type" in info
        assert "initialized" in info
        assert "language" in info
        assert "model" in info
        assert info["engine_type"] == "dummy"
        assert info["initialized"] is True

    def test_convert_language_code(self, asr_module):
        """测试语言代码转换"""
        assert asr_module._convert_language_code("zh-CN") == "zh"
        assert asr_module._convert_language_code("en-US") == "en"
        assert asr_module._convert_language_code("ja-JP") == "ja"
        assert asr_module._convert_language_code("unknown") == "unknown"

    def test_build_hotwords_string(self, asr_module):
        """测试构建热词字符串"""
        asr_module.add_hotwords({"test": 1.5, "demo": 2.0})
        hotwords_str = asr_module._build_hotwords_string()
        assert "test:1.5" in hotwords_str
        assert "demo:2.0" in hotwords_str
        
        asr_module._hotwords = {}
        assert asr_module._build_hotwords_string() == ""


class TestASREngines:
    """测试ASR引擎检测"""

    def test_detect_dummy_engine(self):
        """测试检测dummy引擎"""
        config = ASRConfig(engine="dummy")
        asr = ASRModule(config)
        engine_type = asr._detect_engine()
        assert engine_type == "dummy"

    def test_auto_detect_engine(self):
        """测试自动检测引擎"""
        config = ASRConfig(engine="auto")
        asr = ASRModule(config)
        engine_type = asr._detect_engine()
        assert engine_type in ["faster_whisper", "whisper", "dummy"]


class TestAudioProcessing:
    """测试音频处理"""

    @pytest.fixture
    def asr_module(self):
        """创建ASR模块实例"""
        config = ASRConfig(engine="dummy", use_ffmpeg=False)
        return ASRModule(config)

    @pytest.fixture
    def sample_audio_file(self):
        """创建测试音频文件"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        duration = 1.0
        sample_rate = 16000
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t)
        audio = (audio * 32767).astype(np.int16)
        
        with wave.open(tmp_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())
        
        yield tmp_path
        
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()

    @pytest.mark.asyncio
    async def test_load_audio_simple(self, asr_module, sample_audio_file):
        """测试简单加载音频"""
        audio_data, sample_rate = await asr_module._load_audio_simple(sample_audio_file)
        assert isinstance(audio_data, np.ndarray)
        assert audio_data.dtype == np.float32
        assert sample_rate == 16000
        assert len(audio_data) > 0

    @pytest.mark.asyncio
    async def test_preprocess_audio(self, asr_module, sample_audio_file):
        """测试音频预处理"""
        audio_data, sample_rate = await asr_module._preprocess_audio(sample_audio_file)
        assert isinstance(audio_data, np.ndarray)
        assert audio_data.dtype == np.float32
        assert sample_rate == 16000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
