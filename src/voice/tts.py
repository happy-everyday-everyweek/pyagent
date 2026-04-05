"""
PyAgent 语音模块 - 语音合成(TTS)
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class VoiceInfo:
    voice_id: str
    name: str
    language: str
    gender: str
    preview_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "language": self.language,
            "gender": self.gender,
            "preview_url": self.preview_url,
        }


@dataclass
class TTSConfig:
    voice_id: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    sample_rate: int = 22050


class TTSModule:
    """语音合成模块"""

    def __init__(self, config: TTSConfig | None = None):
        self.config = config or TTSConfig()
        self._voices: list[VoiceInfo] = [
            VoiceInfo("default", "默认女声", "zh-CN", "female"),
            VoiceInfo("male-zh", "中文男声", "zh-CN", "male"),
            VoiceInfo("female-en", "English Female", "en-US", "female"),
            VoiceInfo("male-en", "English Male", "en-US", "male"),
            VoiceInfo("female-ja", "日本語女性", "ja-JP", "female"),
            VoiceInfo("female-ko", "한국어 여성", "ko-KR", "female"),
        ]
        self._current_voice = self.config.voice_id
        self._initialized = False

    def initialize(self) -> bool:
        self._initialized = True
        return True

    def shutdown(self) -> None:
        self._initialized = False

    async def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        if not self._initialized:
            self.initialize()

        voice = voice_id or self._current_voice
        return await self._do_synthesize(text, voice)

    async def _do_synthesize(self, text: str, voice_id: str) -> bytes:
        await asyncio.sleep(0.1)
        return b""

    async def synthesize_to_file(
        self,
        text: str,
        file_path: str,
        voice_id: str | None = None
    ) -> bool:
        try:
            audio_data = await self.synthesize(text, voice_id)
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(audio_data)
            return True
        except Exception:
            return False

    def get_voices(self) -> list[VoiceInfo]:
        return self._voices.copy()

    def set_voice(self, voice_id: str) -> bool:
        for voice in self._voices:
            if voice.voice_id == voice_id:
                self._current_voice = voice_id
                self.config.voice_id = voice_id
                return True
        return False

    def set_speed(self, speed: float) -> None:
        self.config.speed = max(0.5, min(2.0, speed))

    def set_pitch(self, pitch: float) -> None:
        self.config.pitch = max(0.5, min(2.0, pitch))

    def set_volume(self, volume: float) -> None:
        self.config.volume = max(0.0, min(1.0, volume))

    async def stream_synthesize(self, text: str, chunk_size: int = 1024):
        audio_data = await self.synthesize(text)
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]

    def get_config(self) -> TTSConfig:
        return self.config
