"""
PyAgent 语音模块

提供语音识别(ASR)和语音合成(TTS)功能。
"""

from .asr import ASRModule
from .tts import TTSModule, VoiceInfo
from .processor import VoiceProcessor
from .video_narration import VideoNarration

__all__ = [
    "ASRModule",
    "TTSModule",
    "VoiceInfo",
    "VoiceProcessor",
    "VideoNarration",
]
