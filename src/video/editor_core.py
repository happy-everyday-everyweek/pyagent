"""
PyAgent 视频编辑器模块 - 编辑器核心

实现时间线管理、媒体管理、播放管理和渲染管理的适配器。
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid

from .project import VideoProject
from .types import (
    Track,
    TrackType,
    TimelineElement,
    MediaType,
    MediaFile,
    Effect,
    EffectType,
    ExportFormat,
    ExportQuality,
)
from .manager import video_manager
from .commands import CommandManager, Command
from .managers import SelectionManager, SaveManager


@dataclass
class PlaybackState:
    """播放状态"""
    is_playing: bool = False
    current_time: float = 0.0
    playback_rate: float = 1.0
    volume: float = 1.0
    muted: bool = False


@dataclass
class TimelineState:
    """时间线状态"""
    zoom_level: float = 1.0
    scroll_position: float = 0.0
    snap_enabled: bool = True
    snap_threshold: float = 0.5


class TimelineManager:
    """时间线管理器"""

    def __init__(self, project: VideoProject, selection: SelectionManager):
        self._project = project
        self._state = TimelineState()
        self._selection = selection

    def get_state(self) -> TimelineState:
        return self._state

    def set_zoom(self, level: float) -> None:
        self._state.zoom_level = max(0.1, min(10.0, level))

    def set_scroll(self, position: float) -> None:
        self._state.scroll_position = max(0, position)

    def split_element(
        self,
        element_id: str,
        split_time: float,
    ) -> tuple[TimelineElement | None, TimelineElement | None]:
        for track in self._project.tracks:
            for i, element in enumerate(track.elements):
                if element.id == element_id:
                    relative_time = split_time - element.start_time
                    if relative_time <= 0 or relative_time >= element.duration:
                        return None, None
                    first_element = TimelineElement(
                        id=str(uuid.uuid4()),
                        track_id=element.track_id,
                        media_type=element.media_type,
                        name=f"{element.name}_1",
                        start_time=element.start_time,
                        duration=relative_time,
                        trim_start=element.trim_start,
                        trim_end=element.trim_end,
                        volume=element.volume,
                        opacity=element.opacity,
                    )
                    second_element = TimelineElement(
                        id=str(uuid.uuid4()),
                        track_id=element.track_id,
                        media_type=element.media_type,
                        name=f"{element.name}_2",
                        start_time=split_time,
                        duration=element.duration - relative_time,
                        trim_start=element.trim_start + relative_time,
                        trim_end=element.trim_end,
                        volume=element.volume,
                        opacity=element.opacity,
                    )
                    track.elements.pop(i)
                    track.elements.append(first_element)
                    track.elements.append(second_element)
                    return first_element, second_element
        return None, None

    def delete_selected(self) -> int:
        deleted = 0
        selected_ids = self._selection.selected_elements
        for track in self._project.tracks:
            original_count = len(track.elements)
            track.elements = [
                e for e in track.elements
                if e.id not in selected_ids
            ]
            deleted += original_count - len(track.elements)
        self._selection.clear_selection()
        return deleted


class MediaManager:
    """媒体管理器"""

    def __init__(self, project: VideoProject):
        self._project = project
        self._media_dir = Path("data/videos/media")
        self._media_dir.mkdir(parents=True, exist_ok=True)

    def import_media(self, file_path: str) -> MediaFile | None:
        path = Path(file_path)
        if not path.exists():
            return None
        extension = path.suffix.lower()
        media_type = self._detect_media_type(extension)
        if media_type is None:
            return None
        media = MediaFile(
            id=str(uuid.uuid4()),
            name=path.stem,
            path=str(path.absolute()),
            media_type=media_type,
        )
        self._project.add_media(media)
        return media

    def _detect_media_type(self, extension: str) -> MediaType | None:
        video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
        audio_extensions = {".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"}
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        if extension in video_extensions:
            return MediaType.VIDEO
        elif extension in audio_extensions:
            return MediaType.AUDIO
        elif extension in image_extensions:
            return MediaType.IMAGE
        return None

    def get_media(self, media_id: str) -> MediaFile | None:
        return self._project.get_media(media_id)

    def list_media(self) -> list[MediaFile]:
        return self._project.media_files

    def remove_media(self, media_id: str) -> bool:
        return self._project.remove_media(media_id)

    def add_to_timeline(
        self,
        media_id: str,
        track_id: str,
        start_time: float,
    ) -> TimelineElement | None:
        media = self.get_media(media_id)
        if not media:
            return None
        track = self._project.get_track(track_id)
        if not track:
            return None
        duration = media.duration if media.duration > 0 else 5.0
        element = TimelineElement(
            id=str(uuid.uuid4()),
            track_id=track_id,
            media_type=media.media_type,
            name=media.name,
            start_time=start_time,
            duration=duration,
        )
        track.elements.append(element)
        self._project.calculate_duration()
        return element


class PlaybackManager:
    """播放管理器"""

    def __init__(self, project: VideoProject):
        self._project = project
        self._state = PlaybackState()

    def get_state(self) -> PlaybackState:
        return self._state

    def play(self) -> None:
        self._state.is_playing = True

    def pause(self) -> None:
        self._state.is_playing = False

    def stop(self) -> None:
        self._state.is_playing = False
        self._state.current_time = 0.0

    def seek(self, time: float) -> None:
        self._state.current_time = max(0, min(time, self._project.duration))

    def set_rate(self, rate: float) -> None:
        self._state.playback_rate = max(0.25, min(4.0, rate))

    def set_volume(self, volume: float) -> None:
        self._state.volume = max(0, min(1.0, volume))

    def toggle_mute(self) -> None:
        self._state.muted = not self._state.muted

    def get_elements_at_current_time(self) -> list[TimelineElement]:
        return self._project.get_elements_at_time(self._state.current_time)


class RendererManager:
    """渲染管理器"""

    def __init__(self, project: VideoProject):
        self._project = project
        self._output_dir = Path("data/videos/exports")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def render(
        self,
        format: ExportFormat = ExportFormat.MP4,
        quality: ExportQuality = ExportQuality.HIGH,
        output_path: str | None = None,
    ) -> str:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(
                self._output_dir / f"{self._project.name}_{timestamp}.{format.value}"
            )
        return output_path

    def get_render_settings(
        self,
        quality: ExportQuality,
    ) -> dict[str, Any]:
        settings = {
            ExportQuality.LOW: {
                "video_bitrate": "1M",
                "audio_bitrate": "128k",
                "resolution_scale": 0.5,
            },
            ExportQuality.MEDIUM: {
                "video_bitrate": "2.5M",
                "audio_bitrate": "192k",
                "resolution_scale": 0.75,
            },
            ExportQuality.HIGH: {
                "video_bitrate": "5M",
                "audio_bitrate": "256k",
                "resolution_scale": 1.0,
            },
            ExportQuality.ULTRA: {
                "video_bitrate": "10M",
                "audio_bitrate": "320k",
                "resolution_scale": 1.0,
            },
        }
        return settings.get(quality, settings[ExportQuality.HIGH])

    def estimate_render_time(self, quality: ExportQuality) -> float:
        base_time = self._project.duration
        multipliers = {
            ExportQuality.LOW: 0.5,
            ExportQuality.MEDIUM: 1.0,
            ExportQuality.HIGH: 2.0,
            ExportQuality.ULTRA: 4.0,
        }
        return base_time * multipliers.get(quality, 2.0)


class EditorCore:
    """编辑器核心 - 统一管理所有编辑器组件"""

    def __init__(self, project: VideoProject):
        self._project = project
        self._command = CommandManager()
        self._selection = SelectionManager()
        self._save = SaveManager()
        self._timeline = TimelineManager(project, self._selection)
        self._media = MediaManager(project)
        self._playback = PlaybackManager(project)
        self._renderer = RendererManager(project)

    @property
    def project(self) -> VideoProject:
        return self._project

    @property
    def command(self) -> CommandManager:
        return self._command

    @property
    def selection(self) -> SelectionManager:
        return self._selection

    @property
    def save(self) -> SaveManager:
        return self._save

    @property
    def timeline(self) -> TimelineManager:
        return self._timeline

    @property
    def media(self) -> MediaManager:
        return self._media

    @property
    def playback(self) -> PlaybackManager:
        return self._playback

    @property
    def renderer(self) -> RendererManager:
        return self._renderer

    def execute_command(self, command: Command) -> None:
        self._command.execute(command)
        self._save.mark_dirty()

    def undo(self) -> bool:
        result = self._command.undo()
        if result:
            self._save.mark_dirty()
        return result

    def redo(self) -> bool:
        result = self._command.redo()
        if result:
            self._save.mark_dirty()
        return result

    def can_undo(self) -> bool:
        return self._command.can_undo()

    def can_redo(self) -> bool:
        return self._command.can_redo()

    @classmethod
    def create(cls, name: str, width: int = 1920, height: int = 1080, fps: int = 30) -> "EditorCore":
        project = video_manager.create_project(name, width, height, fps)
        return cls(project)

    @classmethod
    def load(cls, project_id: str) -> "EditorCore | None":
        project = video_manager.get_project(project_id)
        if not project:
            return None
        return cls(project)

    def save_project(self) -> bool:
        return self._save.save(self._project)

    def export(
        self,
        format: ExportFormat = ExportFormat.MP4,
        quality: ExportQuality = ExportQuality.HIGH,
        output_path: str | None = None,
    ) -> str:
        return video_manager.export_project(
            self._project.project_id,
            format,
            quality,
            output_path,
        )

    def get_statistics(self) -> dict[str, Any]:
        return self._project.get_statistics()

    def start_auto_save(self) -> None:
        self._save.start()

    def stop_auto_save(self) -> None:
        self._save.stop()
