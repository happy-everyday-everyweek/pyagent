"""
PyAgent 语音模块 - 视频旁白生成
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from .tts import TTSConfig, TTSModule


@dataclass
class NarrationSegment:
    text: str
    start_time: float
    end_time: float
    voice_id: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "voice_id": self.voice_id,
        }


@dataclass
class SubtitleEntry:
    index: int
    start_time: str
    end_time: str
    text: str

    def to_srt(self) -> str:
        return f"{self.index}\n{self.start_time} --> {self.end_time}\n{self.text}\n\n"


class VideoNarration:
    """视频旁白生成器"""

    def __init__(self, tts_config: TTSConfig | None = None):
        self.tts = TTSModule(tts_config)
        self._segments: list[NarrationSegment] = []
        self._audio_cache: dict[str, bytes] = {}

    async def generate_narration(
        self,
        text: str,
        duration: float,
        voice_id: str = "default"
    ) -> bytes:
        audio = await self.tts.synthesize(text, voice_id)
        self._audio_cache[text] = audio
        return audio

    def align_with_timeline(
        self,
        text_segments: list[str],
        timeline: list[dict[str, Any]]
    ) -> list[NarrationSegment]:
        segments: list[NarrationSegment] = []

        for i, text in enumerate(text_segments):
            if i < len(timeline):
                start = timeline[i].get("start", 0.0)
                end = timeline[i].get("end", start + 5.0)
            else:
                prev_end = segments[-1].end_time if segments else 0.0
                start = prev_end + 0.5
                end = start + 5.0

            segments.append(NarrationSegment(
                text=text,
                start_time=start,
                end_time=end,
                voice_id="default"
            ))

        self._segments = segments
        return segments

    def generate_subtitles(
        self,
        text: str,
        duration: float,
        max_chars_per_line: int = 40
    ) -> list[SubtitleEntry]:
        words = text.split()
        lines: list[str] = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars_per_line:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        if not lines:
            return []

        duration_per_line = duration / len(lines)
        entries: list[SubtitleEntry] = []

        for i, line in enumerate(lines):
            start_seconds = i * duration_per_line
            end_seconds = (i + 1) * duration_per_line

            start_time = self._format_time(start_seconds)
            end_time = self._format_time(end_seconds)

            entries.append(SubtitleEntry(
                index=i + 1,
                start_time=start_time,
                end_time=end_time,
                text=line
            ))

        return entries

    def _format_time(self, seconds: float) -> str:
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    async def export_audio(self, output_path: str) -> bool:
        try:
            all_audio = b""
            for segment in self._segments:
                if segment.text in self._audio_cache:
                    all_audio += self._audio_cache[segment.text]
                else:
                    audio = await self.tts.synthesize(segment.text, segment.voice_id)
                    all_audio += audio

            with open(output_path, "wb") as f:
                f.write(all_audio)
            return True
        except Exception:
            return False

    def export_subtitles(self, output_path: str) -> bool:
        try:
            entries = self.generate_subtitles(
                " ".join(s.text for s in self._segments),
                sum(s.end_time - s.start_time for s in self._segments)
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.writelines(entry.to_srt() for entry in entries)
            return True
        except Exception:
            return False

    def get_segments(self) -> list[NarrationSegment]:
        return self._segments.copy()

    def clear(self) -> None:
        self._segments.clear()
        self._audio_cache.clear()
