"""
PyAgent 视频编辑器模块 - 视频管理器

管理视频项目的创建、查询、更新、删除和导出。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .project import VideoProject
from .types import ExportFormat, ExportQuality, MediaType, TimelineElement, Track, TrackType


class VideoManager:
    """视频管理器 - 单例模式"""

    _instance: "VideoManager | None" = None

    def __new__(cls) -> "VideoManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._projects: dict[str, VideoProject] = {}
        self._data_dir = Path("data/videos")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._load_projects()

    def _load_projects(self) -> None:
        projects_file = self._data_dir / "projects.json"
        if projects_file.exists():
            try:
                with open(projects_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for project_data in data.get("projects", []):
                        project = VideoProject.from_dict(project_data)
                        self._projects[project.project_id] = project
            except Exception:
                self._projects = {}

    def _save_projects(self) -> bool:
        projects_file = self._data_dir / "projects.json"
        try:
            data = {
                "projects": [p.to_dict() for p in self._projects.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(projects_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def create_project(
        self,
        name: str,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        domain_id: str | None = None,
    ) -> VideoProject:
        project = VideoProject(
            project_id=str(uuid.uuid4()),
            name=name,
            canvas_width=width,
            canvas_height=height,
            fps=fps,
            domain_id=domain_id,
        )
        video_track = Track(
            id=str(uuid.uuid4()),
            type=TrackType.VIDEO,
            name="Video Track 1",
            order=0,
        )
        audio_track = Track(
            id=str(uuid.uuid4()),
            type=TrackType.AUDIO,
            name="Audio Track 1",
            order=1,
        )
        project.add_track(video_track)
        project.add_track(audio_track)
        self._projects[project.project_id] = project
        self._save_projects()
        return project

    def get_project(self, project_id: str) -> VideoProject | None:
        return self._projects.get(project_id)

    def update_project(self, project_id: str, data: dict[str, Any]) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        if "name" in data:
            project.name = data["name"]
        if "description" in data:
            project.description = data["description"]
        if "tags" in data:
            project.tags = data["tags"]
        if "metadata" in data:
            project.metadata.update(data["metadata"])
        if "canvas_width" in data:
            project.canvas_width = data["canvas_width"]
        if "canvas_height" in data:
            project.canvas_height = data["canvas_height"]
        if "fps" in data:
            project.fps = data["fps"]
        project.update_timestamp()
        return self._save_projects()

    def delete_project(self, project_id: str) -> bool:
        if project_id not in self._projects:
            return False
        del self._projects[project_id]
        return self._save_projects()

    def list_projects(self) -> list[VideoProject]:
        return list(self._projects.values())

    def list_projects_by_domain(self, domain_id: str) -> list[VideoProject]:
        return [
            p for p in self._projects.values()
            if p.domain_id == domain_id
        ]

    def export_project(
        self,
        project_id: str,
        format: ExportFormat = ExportFormat.MP4,
        quality: ExportQuality = ExportQuality.HIGH,
        output_path: str | None = None,
    ) -> str:
        project = self._projects.get(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        if not output_path:
            output_dir = self._data_dir / "exports"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"{project.name}_{timestamp}.{format.value}")
        return output_path

    def add_track_to_project(
        self,
        project_id: str,
        track_type: TrackType,
        name: str | None = None,
    ) -> Track | None:
        project = self._projects.get(project_id)
        if not project:
            return None
        track = Track(
            id=str(uuid.uuid4()),
            type=track_type,
            name=name or f"{track_type.value.title()} Track {len(project.tracks) + 1}",
        )
        project.add_track(track)
        self._save_projects()
        return track

    def add_element_to_track(
        self,
        project_id: str,
        track_id: str,
        media_type: MediaType,
        name: str,
        start_time: float,
        duration: float,
        properties: dict[str, Any] | None = None,
    ) -> TimelineElement | None:
        project = self._projects.get(project_id)
        if not project:
            return None
        track = project.get_track(track_id)
        if not track:
            return None
        element = TimelineElement(
            id=str(uuid.uuid4()),
            track_id=track_id,
            media_type=media_type,
            name=name,
            start_time=start_time,
            duration=duration,
            properties=properties or {},
        )
        track.elements.append(element)
        project.calculate_duration()
        project.update_timestamp()
        self._save_projects()
        return element

    def remove_element_from_track(
        self,
        project_id: str,
        track_id: str,
        element_id: str,
    ) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        track = project.get_track(track_id)
        if not track:
            return False
        for i, element in enumerate(track.elements):
            if element.id == element_id:
                track.elements.pop(i)
                project.calculate_duration()
                project.update_timestamp()
                self._save_projects()
                return True
        return False

    def move_element(
        self,
        project_id: str,
        element_id: str,
        new_track_id: str,
        new_start_time: float,
    ) -> bool:
        project = self._projects.get(project_id)
        if not project:
            return False
        element = None
        old_track = None
        for track in project.tracks:
            for e in track.elements:
                if e.id == element_id:
                    element = e
                    old_track = track
                    break
            if element:
                break
        if not element or not old_track:
            return False
        new_track = project.get_track(new_track_id)
        if not new_track:
            return False
        old_track.elements.remove(element)
        element.track_id = new_track_id
        element.start_time = new_start_time
        new_track.elements.append(element)
        project.calculate_duration()
        project.update_timestamp()
        self._save_projects()
        return True

    def get_statistics(self) -> dict[str, Any]:
        total_duration = sum(p.duration for p in self._projects.values())
        total_tracks = sum(len(p.tracks) for p in self._projects.values())
        total_elements = sum(
            len(e) for p in self._projects.values()
            for t in p.tracks for e in t.elements
        )
        return {
            "total_projects": len(self._projects),
            "total_duration": total_duration,
            "total_tracks": total_tracks,
            "total_elements": total_elements,
        }


video_manager = VideoManager()
