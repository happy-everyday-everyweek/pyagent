"""
PyAgent 语音模块 - 语音处理器
"""

import asyncio
from typing import Any, Callable

from .asr import ASRModule, ASRConfig


class VoiceProcessor:
    """语音处理器 - 实时语音交互"""

    def __init__(self, asr_config: ASRConfig | None = None):
        self.asr = ASRModule(asr_config)
        self._listening = False
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._speech_callbacks: list[Callable[[bytes], None]] = []
        self._transcription_callbacks: list[Callable[[str], None]] = []

    def on_speech_detected(self, callback: Callable[[bytes], None]) -> None:
        self._speech_callbacks.append(callback)

    def on_transcription_ready(self, callback: Callable[[str], None]) -> None:
        self._transcription_callbacks.append(callback)

    async def start_listening(self) -> None:
        if self._listening:
            return

        self._listening = True
        await self.asr.initialize()
        asyncio.create_task(self._process_loop())

    async def stop_listening(self) -> None:
        self._listening = False
        self.asr.shutdown()

    async def _process_loop(self) -> None:
        while self._listening:
            try:
                audio_data = await asyncio.wait_for(
                    self._audio_queue.get(),
                    timeout=0.1
                )
                await self.process_audio(audio_data)
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    async def process_audio(self, audio_data: bytes) -> str:
        for callback in self._speech_callbacks:
            try:
                callback(audio_data)
            except Exception:
                pass

        text = await self.asr.transcribe(audio_data)

        for callback in self._transcription_callbacks:
            try:
                callback(text)
            except Exception:
                pass

        return text

    def push_audio(self, audio_data: bytes) -> None:
        try:
            self._audio_queue.put_nowait(audio_data)
        except asyncio.QueueFull:
            pass

    def is_listening(self) -> bool:
        return self._listening

    def clear_queue(self) -> None:
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
