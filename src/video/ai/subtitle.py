from dataclasses import dataclass


@dataclass
class SubtitleSegment:
    index: int
    start_time: float
    end_time: float
    text: str
    confidence: float = 1.0


@dataclass
class SubtitleStyle:
    font_family: str = "Arial"
    font_size: int = 24
    color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = 0.5
    position: str = "bottom"
    margin_bottom: int = 50


class SubtitleService:
    def __init__(self, provider: str = "whisper", language: str = "auto"):
        self.provider = provider
        self.language = language
        self._segments: list[SubtitleSegment] = []

    def generate_subtitles(
        self,
        video_path: str,
        language: str | None = None,
        auto_translate: bool = False,
        target_languages: list[str] | None = None
    ) -> list[SubtitleSegment]:
        lang = language or self.language
        self._segments = []
        sample_texts = [
            "Hello, welcome to this video.",
            "Today we will explore some interesting topics.",
            "Let's get started with the main content.",
            "This is an example subtitle segment.",
            "Thank you for watching."
        ]
        for i, text in enumerate(sample_texts):
            self._segments.append(SubtitleSegment(
                index=i + 1,
                start_time=i * 3.0,
                end_time=i * 3.0 + 2.5,
                text=text,
                confidence=0.95
            ))
        result = self._segments
        if auto_translate and target_languages:
            result = self._translate_subtitles(result, target_languages[0])
        return result

    def _translate_subtitles(
        self,
        segments: list[SubtitleSegment],
        target_language: str
    ) -> list[SubtitleSegment]:
        translated = []
        translations = {
            "zh": ["你好，欢迎观看这个视频。", "今天我们将探索一些有趣的话题。", "让我们开始主要内容。", "这是一个示例字幕片段。", "感谢观看。"],
            "ja": ["こんにちは、このビデオへようこそ。", "今日は興味深いトピックを探求します。", "メインコンテンツを始めましょう。", "これはサンプルの字幕です。", "ご視聴ありがとうございます。"],
            "en": segments
        }
        target_texts = translations.get(target_language, segments)
        for i, seg in enumerate(segments):
            text = target_texts[i] if i < len(target_texts) else seg.text
            if isinstance(text, SubtitleSegment):
                text = text.text
            translated.append(SubtitleSegment(
                index=seg.index,
                start_time=seg.start_time,
                end_time=seg.end_time,
                text=text,
                confidence=seg.confidence
            ))
        return translated

    def edit_subtitle(
        self,
        index: int,
        text: str | None = None,
        start_time: float | None = None,
        end_time: float | None = None
    ) -> SubtitleSegment | None:
        for i, seg in enumerate(self._segments):
            if seg.index == index:
                new_text = text if text is not None else seg.text
                new_start = start_time if start_time is not None else seg.start_time
                new_end = end_time if end_time is not None else seg.end_time
                self._segments[i] = SubtitleSegment(
                    index=index,
                    start_time=new_start,
                    end_time=new_end,
                    text=new_text,
                    confidence=seg.confidence
                )
                return self._segments[i]
        return None

    def export_srt(self, output_path: str) -> bool:
        try:
            lines = []
            for seg in self._segments:
                lines.append(str(seg.index))
                start_h = int(seg.start_time // 3600)
                start_m = int((seg.start_time % 3600) // 60)
                start_s = seg.start_time % 60
                end_h = int(seg.end_time // 3600)
                end_m = int((seg.end_time % 3600) // 60)
                end_s = seg.end_time % 60
                lines.append(f"{start_h:02d}:{start_m:02d}:{start_s:06.3f} --> {end_h:02d}:{end_m:02d}:{end_s:06.3f}")
                lines.append(seg.text)
                lines.append("")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception:
            return False

    def export_vtt(self, output_path: str) -> bool:
        try:
            lines = ["WEBVTT", ""]
            for seg in self._segments:
                start_h = int(seg.start_time // 3600)
                start_m = int((seg.start_time % 3600) // 60)
                start_s = seg.start_time % 60
                end_h = int(seg.end_time // 3600)
                end_m = int((seg.end_time % 3600) // 60)
                end_s = seg.end_time % 60
                lines.append(f"{start_h:02d}:{start_m:02d}:{start_s:06.3f} --> {end_h:02d}:{end_m:02d}:{end_s:06.3f}")
                lines.append(seg.text)
                lines.append("")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception:
            return False

    def get_segments(self) -> list[SubtitleSegment]:
        return self._segments
