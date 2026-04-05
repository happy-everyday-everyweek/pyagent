"""Azure voice provider and streaming support."""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


class VoiceLanguage(Enum):
    CHINESE = "zh-CN"
    ENGLISH = "en-US"
    JAPANESE = "ja-JP"
    KOREAN = "ko-KR"
    FRENCH = "fr-FR"
    GERMAN = "de-DE"
    SPANISH = "es-ES"


@dataclass
class VoiceInfo:
    name: str
    language: VoiceLanguage
    gender: str
    sample_rate: int = 24000
    style: str | None = None


@dataclass
class SynthesisResult:
    audio_data: bytes
    duration_ms: int
    format: str = "wav"
    sample_rate: int = 24000


class BaseVoiceProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, voice: VoiceInfo, **kwargs: Any) -> SynthesisResult:
        pass

    @abstractmethod
    async def synthesize_stream(self, text: str, voice: VoiceInfo, **kwargs: Any) -> AsyncIterator[bytes]:
        pass


class AzureVoiceProvider(BaseVoiceProvider):
    """Azure Cognitive Services voice provider."""

    VOICES: dict[str, VoiceInfo] = {
        "zh-CN-XiaoxiaoNeural": VoiceInfo("Xiaoxiao", VoiceLanguage.CHINESE, "Female"),
        "zh-CN-YunxiNeural": VoiceInfo("Yunxi", VoiceLanguage.CHINESE, "Male"),
        "zh-CN-YunyangNeural": VoiceInfo("Yunyang", VoiceLanguage.CHINESE, "Male"),
        "en-US-JennyNeural": VoiceInfo("Jenny", VoiceLanguage.ENGLISH, "Female"),
        "en-US-GuyNeural": VoiceInfo("Guy", VoiceLanguage.ENGLISH, "Male"),
        "ja-JP-NanamiNeural": VoiceInfo("Nanami", VoiceLanguage.JAPANESE, "Female"),
        "ko-KR-SunHiNeural": VoiceInfo("SunHi", VoiceLanguage.KOREAN, "Female"),
    }

    def __init__(self, subscription_key: str | None = None, region: str = "eastasia"):
        self._subscription_key = subscription_key
        self._region = region
        self._endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

    async def synthesize(self, text: str, voice: VoiceInfo, **kwargs: Any) -> SynthesisResult:
        import httpx

        ssml = self._build_ssml(text, voice, **kwargs)

        headers = {
            "Ocp-Apim-Subscription-Key": self._subscription_key or "",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self._endpoint, content=ssml.encode("utf-8"), headers=headers)
            response.raise_for_status()

            audio_data = response.content
            duration_ms = int(len(text) * 150)

            return SynthesisResult(audio_data=audio_data, duration_ms=duration_ms, format="mp3")

    async def synthesize_stream(self, text: str, voice: VoiceInfo, **kwargs: Any) -> AsyncIterator[bytes]:
        result = await self.synthesize(text, voice, **kwargs)
        chunk_size = 4096
        for i in range(0, len(result.audio_data), chunk_size):
            yield result.audio_data[i : i + chunk_size]
            await asyncio.sleep(0.01)

    def _build_ssml(self, text: str, voice: VoiceInfo, **kwargs: Any) -> str:
        voice_name = kwargs.get("voice_name", f"{voice.language.value}-{voice.name}Neural")
        rate = kwargs.get("rate", "0%")
        pitch = kwargs.get("pitch", "0%")
        style = kwargs.get("style", voice.style)

        style_attr = f' style="{style}"' if style else ""

        return f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="{voice.language.value}">
            <voice name="{voice_name}"{style_attr}>
                <prosody rate="{rate}" pitch="{pitch}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """

    def list_voices(self, language: VoiceLanguage | None = None) -> list[VoiceInfo]:
        voices = list(self.VOICES.values())
        if language:
            voices = [v for v in voices if v.language == language]
        return voices


class StreamingProcessor:
    """Real-time streaming voice processing."""

    def __init__(self, provider: BaseVoiceProvider, buffer_size: int = 4096):
        self._provider = provider
        self._buffer_size = buffer_size
        self._is_streaming = False
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue()

    async def start_stream(self, voice: VoiceInfo, **kwargs: Any) -> None:
        self._is_streaming = True
        self._audio_queue = asyncio.Queue()

    async def push_text(self, text: str, voice: VoiceInfo, **kwargs: Any) -> None:
        if not self._is_streaming:
            return

        async for chunk in self._provider.synthesize_stream(text, voice, **kwargs):
            await self._audio_queue.put(chunk)

    async def pull_audio(self) -> AsyncIterator[bytes]:
        while self._is_streaming or not self._audio_queue.empty():
            try:
                chunk = await asyncio.wait_for(self._audio_queue.get(), timeout=1.0)
                yield chunk
            except asyncio.TimeoutError:
                continue

    async def stop_stream(self) -> None:
        self._is_streaming = False
        while not self._audio_queue.empty():
            self._audio_queue.get_nowait()


class MultilingualSupport:
    """Multilingual voice support."""

    LANGUAGE_VOICES: dict[VoiceLanguage, list[str]] = {
        VoiceLanguage.CHINESE: ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural"],
        VoiceLanguage.ENGLISH: ["en-US-JennyNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"],
        VoiceLanguage.JAPANESE: ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
        VoiceLanguage.KOREAN: ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"],
        VoiceLanguage.FRENCH: ["fr-FR-DeniseNeural", "fr-FR-HenriNeural"],
        VoiceLanguage.GERMAN: ["de-DE-KatjaNeural", "de-DE-ConradNeural"],
        VoiceLanguage.SPANISH: ["es-ES-ElviraNeural", "es-ES-AlvaroNeural"],
    }

    def __init__(self, provider: AzureVoiceProvider):
        self._provider = provider

    def detect_language(self, text: str) -> VoiceLanguage:
        chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        japanese_chars = sum(1 for c in text if "\u3040" <= c <= "\u309f" or "\u30a0" <= c <= "\u30ff")
        korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7af")

        total = len(text)
        if total == 0:
            return VoiceLanguage.ENGLISH

        if chinese_chars / total > 0.3:
            return VoiceLanguage.CHINESE
        if japanese_chars / total > 0.1:
            return VoiceLanguage.JAPANESE
        if korean_chars / total > 0.1:
            return VoiceLanguage.KOREAN

        return VoiceLanguage.ENGLISH

    def get_voice_for_language(self, language: VoiceLanguage, gender: str = "Female") -> str:
        voices = self.LANGUAGE_VOICES.get(language, self.LANGUAGE_VOICES[VoiceLanguage.ENGLISH])

        for voice in voices:
            if gender == "Female" and "Xiaoxiao" in voice or "Jenny" in voice or "Nanami" in voice or "SunHi" in voice:
                return voice
            elif gender == "Male" and ("Yunxi" in voice or "Guy" in voice or "Keita" in voice):
                return voice

        return voices[0]

    async def synthesize_auto(self, text: str, gender: str = "Female", **kwargs: Any) -> SynthesisResult:
        language = self.detect_language(text)
        voice_name = self.get_voice_for_language(language, gender)

        voice = self._provider.VOICES.get(voice_name)
        if not voice:
            voice = VoiceInfo(name=voice_name.split("-")[-1].replace("Neural", ""), language=language, gender=gender)

        return await self._provider.synthesize(text, voice, voice_name=voice_name, **kwargs)
