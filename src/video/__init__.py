"""
PyAgent 视频编辑器模块

实现视频编辑功能，包括项目管理、时间线编辑、媒体管理等。
"""

from .editor_core import EditorCore
from .manager import VideoManager, video_manager
from .project import VideoProject
from .tools import VideoTool
from .types import (
    Effect,
    EffectType,
    ExportFormat,
    ExportQuality,
    MediaFile,
    MediaType,
    SubtitleStyle,
    TimelineElement,
    Track,
    TrackType,
)

__all__ = [
    "EditorCore",
    "Effect",
    "EffectType",
    "ExportFormat",
    "ExportQuality",
    "MediaFile",
    "MediaType",
    "SubtitleStyle",
    "TimelineElement",
    "Track",
    "TrackType",
    "VideoManager",
    "VideoProject",
    "VideoTool",
    "video_manager",
]
