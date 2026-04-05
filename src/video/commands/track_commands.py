import uuid
from typing import Any

from ..manager import video_manager
from ..types import Track, TrackType
from .base import Command


class AddTrackCommand(Command):
    def __init__(
        self,
        project_id: str,
        track_type: TrackType,
        index: int | None = None,
        name: str | None = None,
    ):
        self._project_id = project_id
        self._track_type = track_type
        self._index = index
        self._name = name
        self._track_id = str(uuid.uuid4())
        self._saved_state: list[dict[str, Any]] | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        self._saved_state = [t.to_dict() for t in project.tracks]
        track_name = self._name or f"{self._track_type.value.title()} Track {len(project.tracks) + 1}"
        new_track = Track(
            id=self._track_id,
            type=self._track_type,
            name=track_name,
        )
        if self._index is not None and 0 <= self._index <= len(project.tracks):
            new_track.order = self._index
            project.tracks.insert(self._index, new_track)
            for i, t in enumerate(project.tracks):
                t.order = i
        else:
            project.add_track(new_track)
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if self._saved_state is None:
            return
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.update_timestamp()
        video_manager._save_projects()

    def get_track_id(self) -> str:
        return self._track_id

    @property
    def description(self) -> str:
        return f"Add {self._track_type.value} track"


class RemoveTrackCommand(Command):
    def __init__(self, project_id: str, track_id: str):
        self._project_id = project_id
        self._track_id = track_id
        self._saved_state: list[dict[str, Any]] | None = None
        self._removed_track_data: dict[str, Any] | None = None
        self._removed_index: int | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        self._saved_state = [t.to_dict() for t in project.tracks]
        for i, track in enumerate(project.tracks):
            if track.id == self._track_id:
                if track.is_main:
                    return
                self._removed_track_data = track.to_dict()
                self._removed_index = i
                project.tracks.pop(i)
                for j, t in enumerate(project.tracks):
                    t.order = j
                project.update_timestamp()
                video_manager._save_projects()
                return

    def undo(self) -> None:
        if self._saved_state is None or self._removed_track_data is None:
            return
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.update_timestamp()
        video_manager._save_projects()

    @property
    def description(self) -> str:
        return f"Remove track {self._track_id}"


class ReorderTracksCommand(Command):
    def __init__(self, project_id: str, track_ids: list[str]):
        self._project_id = project_id
        self._new_order = track_ids
        self._saved_state: list[dict[str, Any]] | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        self._saved_state = [t.to_dict() for t in project.tracks]
        track_map = {t.id: t for t in project.tracks}
        reordered_tracks: list[Track] = []
        for track_id in self._new_order:
            if track_id in track_map:
                reordered_tracks.append(track_map[track_id])
        for track_id in track_map:
            if track_id not in self._new_order:
                reordered_tracks.append(track_map[track_id])
        for i, t in enumerate(reordered_tracks):
            t.order = i
        project.tracks = reordered_tracks
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if self._saved_state is None:
            return
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.update_timestamp()
        video_manager._save_projects()

    @property
    def description(self) -> str:
        return "Reorder tracks"


class ToggleTrackMuteCommand(Command):
    def __init__(self, project_id: str, track_id: str):
        self._project_id = project_id
        self._track_id = track_id
        self._saved_state: list[dict[str, Any]] | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        self._saved_state = [t.to_dict() for t in project.tracks]
        track = project.get_track(self._track_id)
        if not track:
            return
        if track.type == TrackType.VIDEO or track.type == TrackType.AUDIO:
            track.muted = not track.muted
            track.updated_at = track.updated_at
            project.update_timestamp()
            video_manager._save_projects()

    def undo(self) -> None:
        if self._saved_state is None:
            return
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.update_timestamp()
        video_manager._save_projects()

    @property
    def description(self) -> str:
        return f"Toggle mute for track {self._track_id}"


class ToggleTrackVisibilityCommand(Command):
    def __init__(self, project_id: str, track_id: str):
        self._project_id = project_id
        self._track_id = track_id
        self._saved_state: list[dict[str, Any]] | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        self._saved_state = [t.to_dict() for t in project.tracks]
        track = project.get_track(self._track_id)
        if not track:
            return
        if not track.is_main:
            track.visible = not track.visible
            track.updated_at = track.updated_at
            project.update_timestamp()
            video_manager._save_projects()

    def undo(self) -> None:
        if self._saved_state is None:
            return
        project = video_manager.get_project(self._project_id)
        if not project:
            return
        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.update_timestamp()
        video_manager._save_projects()

    @property
    def description(self) -> str:
        return f"Toggle visibility for track {self._track_id}"
