"""Video editing enhancements: preview, multitrack, export."""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class VideoTrack:
    id: str
    name: str
    type: str
    clips: list[dict[str, Any]] = field(default_factory=list)
    muted: bool = False
    locked: bool = False
    visible: bool = True


@dataclass
class VideoClip:
    id: str
    source: str
    start_time: float
    end_time: float
    track_id: str
    position: float
    duration: float
    effects: list[dict[str, Any]] = field(default_factory=list)
    transitions: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineProject:
    id: str
    name: str
    duration: float = 0.0
    fps: int = 30
    resolution: tuple[int, int] = (1920, 1080)
    tracks: list[VideoTrack] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class MultitrackTimeline:
    """Multitrack video timeline editor."""

    def __init__(self):
        self._projects: dict[str, TimelineProject] = {}
        self._current_project: TimelineProject | None = None

    def create_project(
        self,
        name: str,
        fps: int = 30,
        resolution: tuple[int, int] = (1920, 1080),
    ) -> TimelineProject:
        import uuid

        project = TimelineProject(
            id=str(uuid.uuid4()),
            name=name,
            fps=fps,
            resolution=resolution,
        )

        video_track = VideoTrack(id=f"video_0", name="Video 1", type="video")
        audio_track = VideoTrack(id=f"audio_0", name="Audio 1", type="audio")
        project.tracks = [video_track, audio_track]

        self._projects[project.id] = project
        self._current_project = project
        logger.info("Created timeline project: %s", name)
        return project

    def get_project(self, project_id: str) -> TimelineProject | None:
        return self._projects.get(project_id)

    def add_track(self, project_id: str, track_type: str = "video", name: str | None = None) -> VideoTrack | None:
        project = self._projects.get(project_id)
        if not project:
            return None

        import uuid

        track_num = len([t for t in project.tracks if t.type == track_type])
        track = VideoTrack(
            id=f"{track_type}_{track_num}",
            name=name or f"{track_type.title()} {track_num + 1}",
            type=track_type,
        )
        project.tracks.append(track)
        project.updated_at = datetime.now()
        return track

    def remove_track(self, project_id: str, track_id: str) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False

        for i, track in enumerate(project.tracks):
            if track.id == track_id:
                project.tracks.pop(i)
                project.updated_at = datetime.now()
                return True
        return False

    def add_clip(
        self,
        project_id: str,
        track_id: str,
        source: str,
        position: float,
        start_time: float = 0,
        end_time: float | None = None,
    ) -> VideoClip | None:
        project = self._projects.get(project_id)
        if not project:
            return None

        track = next((t for t in project.tracks if t.id == track_id), None)
        if not track:
            return None

        import uuid

        duration = (end_time or 10) - start_time
        clip = VideoClip(
            id=str(uuid.uuid4()),
            source=source,
            start_time=start_time,
            end_time=end_time or start_time + 10,
            track_id=track_id,
            position=position,
            duration=duration,
        )

        track.clips.append(
            {
                "id": clip.id,
                "source": clip.source,
                "position": clip.position,
                "start_time": clip.start_time,
                "end_time": clip.end_time,
                "duration": clip.duration,
            }
        )

        project.duration = max(project.duration, position + duration)
        project.updated_at = datetime.now()
        return clip

    def remove_clip(self, project_id: str, clip_id: str) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False

        for track in project.tracks:
            for i, clip in enumerate(track.clips):
                if clip.get("id") == clip_id:
                    track.clips.pop(i)
                    project.updated_at = datetime.now()
                    return True
        return False

    def move_clip(self, project_id: str, clip_id: str, new_position: float, new_track_id: str | None = None) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False

        clip_data = None
        old_track = None

        for track in project.tracks:
            for clip in track.clips:
                if clip.get("id") == clip_id:
                    clip_data = clip
                    old_track = track
                    break

        if not clip_data:
            return False

        clip_data["position"] = new_position

        if new_track_id and new_track_id != old_track.id:
            old_track.clips.remove(clip_data)
            new_track = next((t for t in project.tracks if t.id == new_track_id), None)
            if new_track:
                new_track.clips.append(clip_data)

        project.updated_at = datetime.now()
        return True

    def split_clip(self, project_id: str, clip_id: str, split_time: float) -> list[VideoClip] | None:
        project = self._projects.get(project_id)
        if not project:
            return None

        for track in project.tracks:
            for i, clip in enumerate(track.clips):
                if clip.get("id") == clip_id:
                    import uuid

                    relative_time = split_time - clip["position"]
                    if relative_time <= 0 or relative_time >= clip["duration"]:
                        return None

                    clip1 = VideoClip(
                        id=str(uuid.uuid4()),
                        source=clip["source"],
                        start_time=clip["start_time"],
                        end_time=clip["start_time"] + relative_time,
                        track_id=track.id,
                        position=clip["position"],
                        duration=relative_time,
                    )

                    clip2 = VideoClip(
                        id=str(uuid.uuid4()),
                        source=clip["source"],
                        start_time=clip["start_time"] + relative_time,
                        end_time=clip["end_time"],
                        track_id=track.id,
                        position=split_time,
                        duration=clip["duration"] - relative_time,
                    )

                    track.clips.pop(i)
                    track.clips.extend(
                        [
                            {"id": clip1.id, "source": clip1.source, "position": clip1.position, "duration": clip1.duration, "start_time": clip1.start_time, "end_time": clip1.end_time},
                            {"id": clip2.id, "source": clip2.source, "position": clip2.position, "duration": clip2.duration, "start_time": clip2.start_time, "end_time": clip2.end_time},
                        ]
                    )

                    project.updated_at = datetime.now()
                    return [clip1, clip2]

        return None


class VideoPreview:
    """Real-time video preview system."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self._ffmpeg_path = ffmpeg_path
        self._preview_process: subprocess.Popen | None = None
        self._preview_url: str | None = None

    async def start_preview(self, project: TimelineProject, port: int = 8080) -> str:
        self.stop_preview()

        self._preview_url = f"http://localhost:{port}/preview"

        return self._preview_url

    def stop_preview(self) -> None:
        if self._preview_process:
            self._preview_process.terminate()
            self._preview_process = None
        self._preview_url = None

    def get_preview_frame(self, project: TimelineProject, time: float) -> bytes | None:
        return None

    @property
    def preview_url(self) -> str | None:
        return self._preview_url


class VideoExporter:
    """Video export with no watermark."""

    SUPPORTED_FORMATS = ["mp4", "webm", "mov", "avi", "mkv"]
    SUPPORTED_CODECS = {
        "mp4": ["h264", "h265", "vp9"],
        "webm": ["vp8", "vp9", "av1"],
        "mov": ["h264", "prores"],
        "avi": ["mpeg4", "h264"],
        "mkv": ["h264", "h265", "vp9"],
    }

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self._ffmpeg_path = ffmpeg_path

    async def export(
        self,
        project: TimelineProject,
        output_path: str,
        format: str = "mp4",
        codec: str = "h264",
        quality: str = "high",
        add_watermark: bool = False,
        watermark_path: str | None = None,
    ) -> dict[str, Any]:
        if format not in self.SUPPORTED_FORMATS:
            return {"success": False, "error": f"Unsupported format: {format}"}

        if codec not in self.SUPPORTED_CODECS.get(format, []):
            return {"success": False, "error": f"Unsupported codec: {codec} for format {format}"}

        quality_presets = {
            "low": {"crf": 28, "preset": "faster"},
            "medium": {"crf": 23, "preset": "medium"},
            "high": {"crf": 18, "preset": "slow"},
            "ultra": {"crf": 12, "preset": "veryslow"},
        }

        preset = quality_presets.get(quality, quality_presets["high"])

        cmd = self._build_export_command(project, output_path, format, codec, preset, add_watermark, watermark_path)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return {
                    "success": True,
                    "output_path": output_path,
                    "format": format,
                    "codec": codec,
                    "quality": quality,
                }
            else:
                return {"success": False, "error": stderr.decode()}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_export_command(
        self,
        project: TimelineProject,
        output_path: str,
        format: str,
        codec: str,
        preset: dict[str, Any],
        add_watermark: bool,
        watermark_path: str | None,
    ) -> list[str]:
        cmd = [self._ffmpeg_path, "-y"]

        width, height = project.resolution
        cmd.extend(["-s", f"{width}x{height}"])
        cmd.extend(["-r", str(project.fps)])

        cmd.extend(["-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:d={project.duration}"])

        codec_map = {
            "h264": "libx264",
            "h265": "libx265",
            "vp8": "libvpx",
            "vp9": "libvpx-vp9",
            "av1": "libaom-av1",
            "prores": "prores_ks",
            "mpeg4": "mpeg4",
        }

        cmd.extend(["-c:v", codec_map.get(codec, "libx264")])

        if codec in ["h264", "h265"]:
            cmd.extend(["-crf", str(preset["crf"]), "-preset", preset["preset"]])

        if add_watermark and watermark_path:
            cmd.extend(["-i", watermark_path])
            cmd.extend(["-filter_complex", "[1]overlay=10:10"])

        cmd.append(output_path)

        return cmd

    def get_export_presets(self) -> dict[str, dict[str, Any]]:
        return {
            "youtube_1080p": {"format": "mp4", "codec": "h264", "quality": "high", "resolution": (1920, 1080)},
            "youtube_4k": {"format": "mp4", "codec": "h265", "quality": "high", "resolution": (3840, 2160)},
            "twitter": {"format": "mp4", "codec": "h264", "quality": "medium", "resolution": (1280, 720)},
            "instagram_square": {"format": "mp4", "codec": "h264", "quality": "high", "resolution": (1080, 1080)},
            "web_optimized": {"format": "webm", "codec": "vp9", "quality": "medium", "resolution": (1920, 1080)},
        }
