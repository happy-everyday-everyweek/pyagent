"""
PyAgent 语音模块 - 语音识别(ASR)
"""

import asyncio
import logging
import os
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_FORMATS = [
    ".mp3", ".m4a", ".mp4", ".wav", ".aac", ".ogg",
    ".opus", ".flac", ".wma", ".webm", ".m4b"
]


@dataclass
class ASRConfig:
    language: str = "zh-CN"
    model: str = "default"
    enable_vad: bool = True
    vad_threshold: float = 0.5
    sample_rate: int = 16000
    engine: str = "auto"
    whisper_model: str = "base"
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"
    use_ffmpeg: bool = True
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"


class ASRError(Exception):
    """ASR模块异常"""


class AudioProcessingError(ASRError):
    """音频处理异常"""


class ASREngineError(ASRError):
    """ASR引擎异常"""


class ASRModule:
    """语音识别模块"""

    def __init__(self, config: ASRConfig | None = None):
        self.config = config or ASRConfig()
        self._hotwords: dict[str, float] = {}
        self._supported_languages = [
            "zh-CN", "zh-TW", "en-US", "en-GB", "ja-JP", "ko-KR",
            "fr-FR", "de-DE", "es-ES", "pt-BR", "ru-RU", "ar-SA"
        ]
        self._initialized = False
        self._engine = None
        self._engine_type = None
        self._ffmpeg_semaphore: threading.Semaphore | None = None
        self._setup_ffmpeg_semaphore()

    def _setup_ffmpeg_semaphore(self):
        """设置FFmpeg并发限制"""
        max_concurrency = int(os.getenv("PYAGENT_FFMPEG_MAX_CONCURRENCY", "4"))
        if max_concurrency > 0:
            self._ffmpeg_semaphore = threading.Semaphore(max_concurrency)

    def initialize(self) -> bool:
        """初始化ASR引擎"""
        if self._initialized:
            return True

        try:
            self._engine_type = self._detect_engine()
            self._initialize_engine()
            self._initialized = True
            logger.info(f"ASR引擎初始化成功: {self._engine_type}")
            return True
        except Exception as e:
            logger.error(f"ASR引擎初始化失败: {e}")
            self._initialized = False
            return False

    def _detect_engine(self) -> str:
        """检测可用的ASR引擎"""
        if self.config.engine != "auto":
            return self.config.engine

        engines = ["faster_whisper", "whisper", "dummy"]

        for engine in engines:
            if engine == "faster_whisper":
                try:
                    import faster_whisper
                    return "faster_whisper"
                except ImportError:
                    continue
            elif engine == "whisper":
                try:
                    import whisper
                    return "whisper"
                except ImportError:
                    continue
            elif engine == "dummy":
                return "dummy"

        raise ASREngineError("没有可用的ASR引擎，请安装 faster-whisper 或 openai-whisper")

    def _initialize_engine(self):
        """初始化具体的ASR引擎"""
        if self._engine_type == "faster_whisper":
            self._init_faster_whisper()
        elif self._engine_type == "whisper":
            self._init_whisper()
        elif self._engine_type == "dummy":
            self._init_dummy()
        else:
            raise ASREngineError(f"不支持的引擎类型: {self._engine_type}")

    def _init_faster_whisper(self):
        """初始化faster-whisper引擎"""
        try:
            from faster_whisper import WhisperModel

            device = self._get_device()
            compute_type = self._get_compute_type(device)

            logger.info(f"加载faster-whisper模型: {self.config.whisper_model}, device={device}, compute_type={compute_type}")

            self._engine = WhisperModel(
                self.config.whisper_model,
                device=device,
                compute_type=compute_type
            )
        except ImportError:
            raise ASREngineError("faster-whisper未安装，请运行: pip install faster-whisper")

    def _init_whisper(self):
        """初始化openai-whisper引擎"""
        try:
            import whisper

            device = self._get_device()
            logger.info(f"加载whisper模型: {self.config.whisper_model}, device={device}")

            self._engine = whisper.load_model(
                self.config.whisper_model,
                device=device
            )
        except ImportError:
            raise ASREngineError("openai-whisper未安装，请运行: pip install openai-whisper")

    def _init_dummy(self):
        """初始化dummy引擎（占位符）"""
        logger.warning("使用dummy引擎，将返回占位符文本")
        self._engine = None

    def _get_device(self) -> str:
        """获取计算设备"""
        if self.config.whisper_device != "auto":
            return self.config.whisper_device

        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        return "cpu"

    def _get_compute_type(self, device: str) -> str:
        """获取计算类型"""
        if self.config.whisper_compute_type != "auto":
            return self.config.whisper_compute_type

        if device == "cuda":
            return "float16"
        if device == "mps":
            return "float32"
        return "int8"

    def shutdown(self) -> None:
        """关闭ASR引擎"""
        if self._engine is not None:
            if self._engine_type == "faster_whisper" or self._engine_type == "whisper":
                pass

            self._engine = None

        self._initialized = False
        logger.info("ASR引擎已关闭")

    async def transcribe(self, audio_data: bytes) -> str:
        """转录音频数据"""
        if not self._initialized:
            if not self.initialize():
                raise ASRError("ASR引擎初始化失败")

        return await self._do_transcribe(audio_data)

    async def _do_transcribe(self, audio_data: bytes) -> str:
        """执行音频转录"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
                tmp_file.write(audio_data)

            try:
                processed_audio, sample_rate = await self._preprocess_audio(tmp_path)

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as processed_file:
                    processed_path = processed_file.name

                try:
                    import soundfile as sf
                    sf.write(processed_path, processed_audio, sample_rate)

                    result = await self._transcribe_with_engine(processed_path)
                    return result
                finally:
                    if os.path.exists(processed_path):
                        os.unlink(processed_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"音频转录失败: {e}")
            raise ASRError(f"音频转录失败: {e}")

    async def _transcribe_with_engine(self, audio_path: str) -> str:
        """使用引擎进行转录"""
        if self._engine_type == "faster_whisper":
            return await self._transcribe_faster_whisper(audio_path)
        if self._engine_type == "whisper":
            return await self._transcribe_whisper(audio_path)
        if self._engine_type == "dummy":
            return await self._transcribe_dummy(audio_path)
        raise ASREngineError(f"不支持的引擎类型: {self._engine_type}")

    async def _transcribe_faster_whisper(self, audio_path: str) -> str:
        """使用faster-whisper转录"""
        def _transcribe():
            language = self._convert_language_code(self.config.language)

            segments, info = self._engine.transcribe(
                audio_path,
                language=language,
                vad_filter=self.config.enable_vad,
                vad_parameters={
                    "threshold": self.config.vad_threshold
                } if self.config.enable_vad else None,
                hotwords=self._build_hotwords_string() if self._hotwords else None
            )

            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)

            return "".join(text_parts).strip()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _transcribe)

    async def _transcribe_whisper(self, audio_path: str) -> str:
        """使用openai-whisper转录"""
        def _transcribe():
            language = self._convert_language_code(self.config.language)

            result = self._engine.transcribe(
                audio_path,
                language=language,
                hotwords=self._build_hotwords_string() if self._hotwords else None
            )

            return result["text"].strip()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _transcribe)

    async def _transcribe_dummy(self, audio_path: str) -> str:
        """使用dummy引擎转录（占位符）"""
        await asyncio.sleep(0.1)
        return "[语音转文字结果]"

    def _convert_language_code(self, lang_code: str) -> str:
        """转换语言代码格式"""
        lang_map = {
            "zh-CN": "zh",
            "zh-TW": "zh",
            "en-US": "en",
            "en-GB": "en",
            "ja-JP": "ja",
            "ko-KR": "ko",
            "fr-FR": "fr",
            "de-DE": "de",
            "es-ES": "es",
            "pt-BR": "pt",
            "ru-RU": "ru",
            "ar-SA": "ar"
        }
        return lang_map.get(lang_code, lang_code.split("-", maxsplit=1)[0] if "-" in lang_code else lang_code)

    def _build_hotwords_string(self) -> str:
        """构建热词字符串"""
        if not self._hotwords:
            return ""

        hotword_parts = []
        for word, boost in self._hotwords.items():
            hotword_parts.append(f"{word}:{boost}")

        return " ".join(hotword_parts)

    async def _preprocess_audio(self, audio_path: str) -> tuple:
        """预处理音频文件"""
        if not self.config.use_ffmpeg:
            return await self._load_audio_simple(audio_path)

        return await self._load_audio_ffmpeg(audio_path)

    async def _load_audio_simple(self, audio_path: str) -> tuple:
        """简单加载音频（不使用FFmpeg）"""
        try:
            import librosa
            import soundfile as sf

            audio_data, sr = sf.read(audio_path)

            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)

            if sr != self.config.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.config.sample_rate)
                sr = self.config.sample_rate

            return audio_data.astype("float32"), sr

        except Exception as e:
            raise AudioProcessingError(f"音频加载失败: {e}")

    async def _load_audio_ffmpeg(self, audio_path: str) -> tuple:
        """使用FFmpeg加载音频"""
        def _load():
            cmd = [
                self.config.ffmpeg_path,
                "-loglevel", "error",
                "-nostdin",
                "-threads", "0",
                "-i", audio_path,
                "-f", "s16le",
                "-ac", "1",
                "-acodec", "pcm_s16le",
                "-ar", str(self.config.sample_rate),
                "-"
            ]

            if self._ffmpeg_semaphore:
                with self._ffmpeg_semaphore:
                    result = run(cmd, capture_output=True, check=True)
            else:
                result = run(cmd, capture_output=True, check=True)

            import numpy as np
            audio_data = np.frombuffer(result.stdout, np.int16).flatten().astype(np.float32) / 32768.0

            return audio_data, self.config.sample_rate

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _load)
        except CalledProcessError as e:
            raise AudioProcessingError(f"FFmpeg处理失败: {e.stderr.decode() if e.stderr else str(e)}")
        except FileNotFoundError:
            logger.warning("FFmpeg未找到，回退到简单加载")
            return await self._load_audio_simple(audio_path)
        except Exception as e:
            raise AudioProcessingError(f"音频处理失败: {e}")

    async def transcribe_file(self, file_path: str) -> str:
        """转录音频文件"""
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"音频文件不存在: {file_path}")

            if path.suffix.lower() not in SUPPORTED_AUDIO_FORMATS:
                logger.warning(f"可能不支持的音频格式: {path.suffix}")

            if self._engine_type in ["faster_whisper", "whisper"]:
                return await self._transcribe_with_engine(str(path))
            with open(file_path, "rb") as f:
                audio_data = f.read()
            return await self.transcribe(audio_data)

        except Exception as e:
            logger.error(f"文件转录失败: {e}")
            raise ASRError(f"文件转录失败: {e}")

    async def transcribe_stream(
        self,
        audio_stream: Any,
        callback: Callable[[str], None] | None = None
    ) -> str:
        """转录音频流"""
        result = ""
        async for chunk in audio_stream:
            text = await self.transcribe(chunk)
            if callback:
                callback(text)
            result += text
        return result

    def set_language(self, language: str) -> bool:
        """设置识别语言"""
        if language in self._supported_languages:
            self.config.language = language
            return True
        return False

    def add_hotwords(self, hotwords: dict[str, float]) -> None:
        """添加热词"""
        self._hotwords.update(hotwords)

    def remove_hotword(self, word: str) -> None:
        """移除热词"""
        if word in self._hotwords:
            del self._hotwords[word]

    def get_supported_languages(self) -> list[str]:
        """获取支持的语言列表"""
        return self._supported_languages.copy()

    def get_config(self) -> ASRConfig:
        """获取当前配置"""
        return self.config

    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            "engine_type": self._engine_type,
            "initialized": self._initialized,
            "language": self.config.language,
            "model": self.config.whisper_model,
            "device": self._get_device() if self._initialized else None,
            "hotwords_count": len(self._hotwords)
        }
