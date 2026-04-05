"""
PyAgent 视频编辑器模块 - 视频项目

定义视频项目的数据结构和管理方法。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from .types import Track, MediaFile, ExportFormat, ExportQuality


@dataclass
class VideoProject:
    """视频项目"""
    project_id: str
    name: str
    canvas_width: int = 1920
    canvas_height: int = 1080
    fps: int = 30
    duration: float = 0.0
    tracks: list[Track] = field(default_factory=list)
    media_files: list[MediaFile] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    domain_id: str | None = None
    description: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.project_id:
            self.project_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "fps": self.fps,
            "duration": self.duration,
            "tracks": [t.to_dict() for t in self.tracks],
            "media_files": [m.to_dict() for m in self.media_files],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "domain_id": self.domain_id,
            "description": self.description,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VideoProject":
        tracks = [Track.from_dict(t) for t in data.get("tracks", [])]
        media_files = [MediaFile.from_dict(m) for m in data.get("media_files", [])]
        return cls(
            project_id=data.get("project_id", str(uuid.uuid4())),
            name=data["name"],
            canvas_width=data.get("canvas_width", 1920),
            canvas_height=data.get("canvas_height", 1080),
            fps=data.get("fps", 30),
            duration=data.get("duration", 0.0),
            tracks=tracks,
            media_files=media_files,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            domain_id=data.get("domain_id"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now().isoformat()

    def calculate_duration(self) -> float:
        if not self.tracks:
            return 0.0
        max_duration = 0.0
        for track in self.tracks:
            track_duration = track.get_duration()
            if track_duration > max_duration:
                max_duration = track_duration
        self.duration = max_duration
        return self.duration

    def add_track(self, track: Track) -> None:
        track.order = len(self.tracks)
        self.tracks.append(track)
        self.update_timestamp()

    def remove_track(self, track_id: str) -> bool:
        for i, track in enumerate(self.tracks):
            if track.id == track_id:
                self.tracks.pop(i)
                for j, t in enumerate(self.tracks):
                    t.order = j
                self.update_timestamp()
                return True
        return False

    def get_track(self, track_id: str) -> Track | None:
        for track in self.tracks:
            if track.id == track_id:
                return track
        return None

    def add_media(self, media: MediaFile) -> None:
        self.media_files.append(media)
        self.update_timestamp()

    def remove_media(self, media_id: str) -> bool:
        for i, media in enumerate(self.media_files):
            if media.id == media_id:
                self.media_files.pop(i)
                self.update_timestamp()
                return True
        return False

    def get_media(self, media_id: str) -> MediaFile | None:
        for media in self.media_files:
            if media.id == media_id:
                return media
        return None

    def get_all_elements(self) -> list:
        elements = []
        for track in self.tracks:
            elements.extend(track.elements)
        return elements

    def get_elements_at_time(self, time: float) -> list:
        elements = []
        for track in self.tracks:
            if not track.visible or track.muted:
                continue
            for element in track.elements:
                if element.start_time <= time < element.get_end_time():
                    elements.append(element)
        return elements

    def validate(self) -> tuple[bool, list[str]]:
        errors = []
        if not self.name:
            errors.append("Project name is required")
        if self.canvas_width <= 0:
            errors.append("Canvas width must be positive")
        if self.canvas_height <= 0:
            errors.append("Canvas height must be positive")
        if self.fps <= 0:
            errors.append("FPS must be positive")
        for track in self.tracks:
            for element in track.elements:
                if element.duration <= 0:
                    errors.append(f"Element {element.id} has invalid duration")
                if element.start_time < 0:
                    errors.append(f"Element {element.id} has negative start time")
        return len(errors) == 0, errors

    def get_statistics(self) -> dict[str, Any]:
        total_elements = sum(len(t.elements) for t in self.tracks)
        video_tracks = sum(1 for t in self.tracks if t.type.value == "video")
        audio_tracks = sum(1 for t in self.tracks if t.type.value == "audio")
        text_tracks = sum(1 for t in self.tracks if t.type.value == "text")
        return {
            "project_id": self.project_id,
            "name": self.name,
            "duration": self.duration,
            "total_tracks": len(self.tracks),
            "video_tracks": video_tracks,
            "audio_tracks": audio_tracks,
            "text_tracks": text_tracks,
            "total_elements": total_elements,
            "total_media_files": len(self.media_files),
            "canvas_size": f"{self.canvas_width}x{self.canvas_height}",
            "fps": self.fps,
        }

    def clone(self, new_name: str) -> "VideoProject":
        return VideoProject(
            project_id=str(uuid.uuid4()),
            name=new_name,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            fps=self.fps,
            duration=self.duration,
            tracks=[Track.from_dict(t.to_dict()) for t in self.tracks],
            media_files=[MediaFile.from_dict(m.to_dict()) for m in self.media_files],
            domain_id=self.domain_id,
            description=self.description,
            tags=self.tags.copy(),
            metadata=self.metadata.copy(),
        )
