"""
PyAgent 视频编辑器模块 - 类型定义

定义视频编辑相关的数据类型和枚举。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MediaType(Enum):
    """媒体类型"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    STICKER = "sticker"


class TrackType(Enum):
    """轨道类型"""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    STICKER = "sticker"


class ExportFormat(Enum):
    """导出格式"""
    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"
    AVI = "avi"
    GIF = "gif"


class ExportQuality(Enum):
    """导出质量"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class EffectType(Enum):
    """特效类型"""
    TRANSITION = "transition"
    FILTER = "filter"
    OVERLAY = "overlay"
    ANIMATION = "animation"
    COLOR_CORRECTION = "color_correction"


class TransitionType(Enum):
    """转场类型"""
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE_LEFT = "wipe-left"
    WIPE_RIGHT = "wipe-right"
    WIPE_UP = "wipe-up"
    WIPE_DOWN = "wipe-down"
    SLIDE_LEFT = "slide-left"
    SLIDE_RIGHT = "slide-right"
    SLIDE_UP = "slide-up"
    SLIDE_DOWN = "slide-down"
    ZOOM_IN = "zoom-in"
    ZOOM_OUT = "zoom-out"


@dataclass
class Transform:
    """变换属性"""
    scale: float = 1.0
    position: dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    rotate: float = 0.0
    flip_x: bool = False
    flip_y: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "scale": self.scale,
            "position": self.position,
            "rotate": self.rotate,
            "flip_x": self.flip_x,
            "flip_y": self.flip_y,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transform":
        return cls(
            scale=data.get("scale", 1.0),
            position=data.get("position", {"x": 0.0, "y": 0.0}),
            rotate=data.get("rotate", 0.0),
            flip_x=data.get("flip_x", False),
            flip_y=data.get("flip_y", False),
        )


@dataclass
class TrackTransition:
    """轨道转场"""
    id: str
    type: TransitionType
    duration: float = 0.5
    from_element_id: str = ""
    to_element_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "duration": self.duration,
            "from_element_id": self.from_element_id,
            "to_element_id": self.to_element_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrackTransition":
        return cls(
            id=data["id"],
            type=TransitionType(data["type"]),
            duration=data.get("duration", 0.5),
            from_element_id=data.get("from_element_id", ""),
            to_element_id=data.get("to_element_id", ""),
        )


@dataclass
class TimelineElement:
    """时间线元素"""
    id: str
    track_id: str
    media_type: MediaType
    name: str
    start_time: float
    duration: float
    trim_start: float = 0
    trim_end: float = 0
    volume: float = 1.0
    opacity: float = 1.0
    position_x: float = 0
    position_y: float = 0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0
    transform: Transform = field(default_factory=Transform)
    playback_rate: float = 1.0
    reversed: bool = False
    properties: dict[str, Any] = field(default_factory=dict)
    effects: list["Effect"] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "track_id": self.track_id,
            "media_type": self.media_type.value,
            "name": self.name,
            "start_time": self.start_time,
            "duration": self.duration,
            "trim_start": self.trim_start,
            "trim_end": self.trim_end,
            "volume": self.volume,
            "opacity": self.opacity,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "scale_x": self.scale_x,
            "scale_y": self.scale_y,
            "rotation": self.rotation,
            "transform": self.transform.to_dict(),
            "playback_rate": self.playback_rate,
            "reversed": self.reversed,
            "properties": self.properties,
            "effects": [e.to_dict() for e in self.effects],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimelineElement":
        effects = [Effect.from_dict(e) for e in data.get("effects", [])]
        transform_data = data.get("transform")
        transform = Transform.from_dict(transform_data) if transform_data else Transform()
        return cls(
            id=data["id"],
            track_id=data["track_id"],
            media_type=MediaType(data["media_type"]),
            name=data["name"],
            start_time=data["start_time"],
            duration=data["duration"],
            trim_start=data.get("trim_start", 0),
            trim_end=data.get("trim_end", 0),
            volume=data.get("volume", 1.0),
            opacity=data.get("opacity", 1.0),
            position_x=data.get("position_x", 0),
            position_y=data.get("position_y", 0),
            scale_x=data.get("scale_x", 1.0),
            scale_y=data.get("scale_y", 1.0),
            rotation=data.get("rotation", 0),
            transform=transform,
            playback_rate=data.get("playback_rate", 1.0),
            reversed=data.get("reversed", False),
            properties=data.get("properties", {}),
            effects=effects,
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
        )

    def get_end_time(self) -> float:
        return self.start_time + self.duration


@dataclass
class StickerElement:
    """贴纸元素"""
    id: str
    type: str = "sticker"
    name: str = ""
    start_time: float = 0
    duration: float = 0
    trim_start: float = 0
    trim_end: float = 0
    icon_name: str = ""
    transform: Transform = field(default_factory=Transform)
    opacity: float = 1.0
    color: str | None = None
    hidden: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "start_time": self.start_time,
            "duration": self.duration,
            "trim_start": self.trim_start,
            "trim_end": self.trim_end,
            "icon_name": self.icon_name,
            "transform": self.transform.to_dict(),
            "opacity": self.opacity,
            "color": self.color,
            "hidden": self.hidden,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StickerElement":
        transform_data = data.get("transform")
        transform = Transform.from_dict(transform_data) if transform_data else Transform()
        return cls(
            id=data["id"],
            type=data.get("type", "sticker"),
            name=data.get("name", ""),
            start_time=data.get("start_time", 0),
            duration=data.get("duration", 0),
            trim_start=data.get("trim_start", 0),
            trim_end=data.get("trim_end", 0),
            icon_name=data.get("icon_name", ""),
            transform=transform,
            opacity=data.get("opacity", 1.0),
            color=data.get("color"),
            hidden=data.get("hidden", False),
        )

    def get_end_time(self) -> float:
        return self.start_time + self.duration


@dataclass
class Track:
    """轨道"""
    id: str
    type: TrackType
    name: str
    elements: list[TimelineElement] = field(default_factory=list)
    transitions: list[TrackTransition] = field(default_factory=list)
    is_main: bool = False
    muted: bool = False
    visible: bool = True
    locked: bool = False
    order: int = 0
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "elements": [e.to_dict() for e in self.elements],
            "transitions": [t.to_dict() for t in self.transitions],
            "is_main": self.is_main,
            "muted": self.muted,
            "visible": self.visible,
            "locked": self.locked,
            "order": self.order,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Track":
        elements = [TimelineElement.from_dict(e) for e in data.get("elements", [])]
        transitions = [TrackTransition.from_dict(t) for t in data.get("transitions", [])]
        return cls(
            id=data["id"],
            type=TrackType(data["type"]),
            name=data["name"],
            elements=elements,
            transitions=transitions,
            is_main=data.get("is_main", False),
            muted=data.get("muted", False),
            visible=data.get("visible", True),
            locked=data.get("locked", False),
            order=data.get("order", 0),
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
        )

    def get_duration(self) -> float:
        if not self.elements:
            return 0.0
        return max(e.get_end_time() for e in self.elements)


@dataclass
class MediaFile:
    """媒体文件"""
    id: str
    name: str
    path: str
    media_type: MediaType
    duration: float = 0
    width: int = 0
    height: int = 0
    fps: float = 0
    bitrate: int = 0
    codec: str = ""
    size: int = 0
    thumbnail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "media_type": self.media_type.value,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "bitrate": self.bitrate,
            "codec": self.codec,
            "size": self.size,
            "thumbnail": self.thumbnail,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MediaFile":
        return cls(
            id=data["id"],
            name=data["name"],
            path=data["path"],
            media_type=MediaType(data["media_type"]),
            duration=data.get("duration", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
            fps=data.get("fps", 0),
            bitrate=data.get("bitrate", 0),
            codec=data.get("codec", ""),
            size=data.get("size", 0),
            thumbnail=data.get("thumbnail", ""),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().timestamp()),
        )


@dataclass
class SubtitleStyle:
    """字幕样式"""
    font_family: str = "Arial"
    font_size: int = 24
    color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = 0.5
    position: str = "bottom"
    margin_bottom: int = 50
    bold: bool = False
    italic: bool = False
    outline_color: str = "#000000"
    outline_width: int = 2

    def to_dict(self) -> dict[str, Any]:
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "background_color": self.background_color,
            "background_opacity": self.background_opacity,
            "position": self.position,
            "margin_bottom": self.margin_bottom,
            "bold": self.bold,
            "italic": self.italic,
            "outline_color": self.outline_color,
            "outline_width": self.outline_width,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubtitleStyle":
        return cls(
            font_family=data.get("font_family", "Arial"),
            font_size=data.get("font_size", 24),
            color=data.get("color", "#FFFFFF"),
            background_color=data.get("background_color", "#000000"),
            background_opacity=data.get("background_opacity", 0.5),
            position=data.get("position", "bottom"),
            margin_bottom=data.get("margin_bottom", 50),
            bold=data.get("bold", False),
            italic=data.get("italic", False),
            outline_color=data.get("outline_color", "#000000"),
            outline_width=data.get("outline_width", 2),
        )


@dataclass
class Effect:
    """特效"""
    id: str
    type: EffectType
    name: str
    start_time: float = 0
    duration: float = 0
    intensity: float = 1.0
    parameters: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "start_time": self.start_time,
            "duration": self.duration,
            "intensity": self.intensity,
            "parameters": self.parameters,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Effect":
        return cls(
            id=data["id"],
            type=EffectType(data["type"]),
            name=data["name"],
            start_time=data.get("start_time", 0),
            duration=data.get("duration", 0),
            intensity=data.get("intensity", 1.0),
            parameters=data.get("parameters", {}),
            created_at=data.get("created_at", datetime.now().timestamp()),
        )
