import copy
import uuid
from typing import Any

from .base import Command
from ..manager import video_manager
from ..types import TimelineElement, Track, TrackType, MediaType


class InsertElementCommand(Command):
    def __init__(
        self,
        project_id: str,
        element_data: dict[str, Any],
        track_id: str,
        start_time: float,
    ):
        self._project_id = project_id
        self._element_data = element_data
        self._track_id = track_id
        self._start_time = start_time
        self._element_id: str | None = None
        self._saved_track_state: list[dict[str, Any]] | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        track = project.get_track(self._track_id)
        if not track:
            return

        self._saved_track_state = [e.to_dict() for e in track.elements]

        element_id = str(uuid.uuid4())
        media_type = self._element_data.get("media_type")
        if isinstance(media_type, str):
            media_type = MediaType(media_type)

        element = TimelineElement(
            id=element_id,
            track_id=self._track_id,
            media_type=media_type or MediaType.VIDEO,
            name=self._element_data.get("name", "Element"),
            start_time=self._start_time,
            duration=self._element_data.get("duration", 5.0),
            trim_start=self._element_data.get("trim_start", 0),
            trim_end=self._element_data.get("trim_end", 0),
            volume=self._element_data.get("volume", 1.0),
            opacity=self._element_data.get("opacity", 1.0),
            position_x=self._element_data.get("position_x", 0),
            position_y=self._element_data.get("position_y", 0),
            scale_x=self._element_data.get("scale_x", 1.0),
            scale_y=self._element_data.get("scale_y", 1.0),
            rotation=self._element_data.get("rotation", 0),
            playback_rate=self._element_data.get("playback_rate", 1.0),
            reversed=self._element_data.get("reversed", False),
            properties=self._element_data.get("properties", {}),
        )

        track.elements.append(element)
        self._element_id = element_id
        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if not self._element_id:
            return

        project = video_manager.get_project(self._project_id)
        if not project:
            return

        track = project.get_track(self._track_id)
        if not track:
            return

        track.elements = [e for e in track.elements if e.id != self._element_id]
        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def get_element_id(self) -> str | None:
        return self._element_id


class DeleteElementsCommand(Command):
    def __init__(
        self,
        project_id: str,
        elements: list[dict[str, str]],
    ):
        self._project_id = project_id
        self._elements = elements
        self._saved_elements: list[dict[str, Any]] = []

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        self._saved_elements = []

        for element_ref in self._elements:
            track_id = element_ref.get("track_id")
            element_id = element_ref.get("element_id")

            track = project.get_track(track_id)
            if not track:
                continue

            for element in track.elements:
                if element.id == element_id:
                    self._saved_elements.append({
                        "track_id": track_id,
                        "element_data": element.to_dict(),
                    })
                    break

        for element_ref in self._elements:
            track_id = element_ref.get("track_id")
            element_id = element_ref.get("element_id")

            track = project.get_track(track_id)
            if not track:
                continue

            track.elements = [e for e in track.elements if e.id != element_id]

        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        for saved in self._saved_elements:
            track_id = saved["track_id"]
            element_data = saved["element_data"]

            track = project.get_track(track_id)
            if not track:
                continue

            element = TimelineElement.from_dict(element_data)
            track.elements.append(element)

        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()


class MoveElementCommand(Command):
    def __init__(
        self,
        project_id: str,
        source_track_id: str,
        target_track_id: str,
        element_id: str,
        new_start_time: float,
    ):
        self._project_id = project_id
        self._source_track_id = source_track_id
        self._target_track_id = target_track_id
        self._element_id = element_id
        self._new_start_time = new_start_time
        self._original_start_time: float | None = None
        self._original_track_id: str | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        source_track = project.get_track(self._source_track_id)
        target_track = project.get_track(self._target_track_id)

        if not source_track or not target_track:
            return

        element = None
        for e in source_track.elements:
            if e.id == self._element_id:
                element = e
                break

        if not element:
            return

        self._original_start_time = element.start_time
        self._original_track_id = self._source_track_id

        if self._source_track_id == self._target_track_id:
            element.start_time = self._new_start_time
        else:
            source_track.elements = [e for e in source_track.elements if e.id != self._element_id]
            element.track_id = self._target_track_id
            element.start_time = self._new_start_time
            target_track.elements.append(element)

        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if self._original_start_time is None or self._original_track_id is None:
            return

        project = video_manager.get_project(self._project_id)
        if not project:
            return

        target_track = project.get_track(self._target_track_id)
        original_track = project.get_track(self._original_track_id)

        if not target_track or not original_track:
            return

        element = None
        for e in target_track.elements:
            if e.id == self._element_id:
                element = e
                break

        if not element:
            return

        if self._source_track_id == self._target_track_id:
            element.start_time = self._original_start_time
        else:
            target_track.elements = [e for e in target_track.elements if e.id != self._element_id]
            element.track_id = self._original_track_id
            element.start_time = self._original_start_time
            original_track.elements.append(element)

        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()


class SplitElementsCommand(Command):
    def __init__(
        self,
        project_id: str,
        elements: list[dict[str, str]],
        split_time: float,
        retain_side: str = "both",
    ):
        self._project_id = project_id
        self._elements = elements
        self._split_time = split_time
        self._retain_side = retain_side
        self._saved_state: list[dict[str, Any]] | None = None
        self._right_side_elements: list[dict[str, str]] = []

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        self._saved_state = [t.to_dict() for t in project.tracks]
        self._right_side_elements = []

        for element_ref in self._elements:
            track_id = element_ref.get("track_id")
            element_id = element_ref.get("element_id")

            track = project.get_track(track_id)
            if not track:
                continue

            element = None
            element_index = -1
            for i, e in enumerate(track.elements):
                if e.id == element_id:
                    element = e
                    element_index = i
                    break

            if not element:
                continue

            if self._split_time <= element.start_time or self._split_time >= element.get_end_time():
                continue

            relative_time = self._split_time - element.start_time
            left_duration = relative_time
            right_duration = element.duration - relative_time

            if self._retain_side == "left":
                element.duration = left_duration
                element.trim_end = element.trim_end + right_duration
            elif self._retain_side == "right":
                new_element_id = str(uuid.uuid4())
                new_element = TimelineElement(
                    id=new_element_id,
                    track_id=track_id,
                    media_type=element.media_type,
                    name=f"{element.name} (right)",
                    start_time=self._split_time,
                    duration=right_duration,
                    trim_start=element.trim_start + left_duration,
                    trim_end=element.trim_end,
                    volume=element.volume,
                    opacity=element.opacity,
                    position_x=element.position_x,
                    position_y=element.position_y,
                    scale_x=element.scale_x,
                    scale_y=element.scale_y,
                    rotation=element.rotation,
                    playback_rate=element.playback_rate,
                    reversed=element.reversed,
                    properties=copy.deepcopy(element.properties),
                )
                track.elements[element_index] = new_element
                self._right_side_elements.append({
                    "track_id": track_id,
                    "element_id": new_element_id,
                })
            else:
                new_element_id = str(uuid.uuid4())
                new_element = TimelineElement(
                    id=new_element_id,
                    track_id=track_id,
                    media_type=element.media_type,
                    name=f"{element.name} (right)",
                    start_time=self._split_time,
                    duration=right_duration,
                    trim_start=element.trim_start + left_duration,
                    trim_end=element.trim_end,
                    volume=element.volume,
                    opacity=element.opacity,
                    position_x=element.position_x,
                    position_y=element.position_y,
                    scale_x=element.scale_x,
                    scale_y=element.scale_y,
                    rotation=element.rotation,
                    playback_rate=element.playback_rate,
                    reversed=element.reversed,
                    properties=copy.deepcopy(element.properties),
                )
                element.duration = left_duration
                element.trim_end = element.trim_end + right_duration
                element.name = f"{element.name} (left)"
                track.elements.insert(element_index + 1, new_element)
                self._right_side_elements.append({
                    "track_id": track_id,
                    "element_id": new_element_id,
                })

        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if not self._saved_state:
            return

        project = video_manager.get_project(self._project_id)
        if not project:
            return

        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def get_right_side_elements(self) -> list[dict[str, str]]:
        return self._right_side_elements


class UpdateElementCommand(Command):
    def __init__(
        self,
        project_id: str,
        track_id: str,
        element_id: str,
        updates: dict[str, Any],
    ):
        self._project_id = project_id
        self._track_id = track_id
        self._element_id = element_id
        self._updates = updates
        self._original_values: dict[str, Any] = {}

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        track = project.get_track(self._track_id)
        if not track:
            return

        element = None
        for e in track.elements:
            if e.id == self._element_id:
                element = e
                break

        if not element:
            return

        for key in self._updates:
            if hasattr(element, key):
                self._original_values[key] = getattr(element, key)

        for key, value in self._updates.items():
            if hasattr(element, key):
                setattr(element, key, value)

        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if not self._original_values:
            return

        project = video_manager.get_project(self._project_id)
        if not project:
            return

        track = project.get_track(self._track_id)
        if not track:
            return

        element = None
        for e in track.elements:
            if e.id == self._element_id:
                element = e
                break

        if not element:
            return

        for key, value in self._original_values.items():
            setattr(element, key, value)

        project.update_timestamp()
        video_manager._save_projects()


class DuplicateElementsCommand(Command):
    def __init__(
        self,
        project_id: str,
        elements: list[dict[str, str]],
    ):
        self._project_id = project_id
        self._elements = elements
        self._duplicated_elements: list[dict[str, str]] = []
        self._saved_state: list[dict[str, Any]] | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        self._saved_state = [t.to_dict() for t in project.tracks]
        self._duplicated_elements = []

        for element_ref in self._elements:
            track_id = element_ref.get("track_id")
            element_id = element_ref.get("element_id")

            track = project.get_track(track_id)
            if not track:
                continue

            element = None
            for e in track.elements:
                if e.id == element_id:
                    element = e
                    break

            if not element:
                continue

            new_element_id = str(uuid.uuid4())
            new_element = TimelineElement(
                id=new_element_id,
                track_id=track_id,
                media_type=element.media_type,
                name=f"{element.name} (copy)",
                start_time=element.start_time,
                duration=element.duration,
                trim_start=element.trim_start,
                trim_end=element.trim_end,
                volume=element.volume,
                opacity=element.opacity,
                position_x=element.position_x,
                position_y=element.position_y,
                scale_x=element.scale_x,
                scale_y=element.scale_y,
                rotation=element.rotation,
                playback_rate=element.playback_rate,
                reversed=element.reversed,
                properties=copy.deepcopy(element.properties),
            )
            track.elements.append(new_element)
            self._duplicated_elements.append({
                "track_id": track_id,
                "element_id": new_element_id,
            })

        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if not self._saved_state:
            return

        project = video_manager.get_project(self._project_id)
        if not project:
            return

        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def get_duplicated_elements(self) -> list[dict[str, str]]:
        return self._duplicated_elements


class DetachAudioCommand(Command):
    def __init__(
        self,
        project_id: str,
        elements: list[dict[str, str]],
    ):
        self._project_id = project_id
        self._elements = elements
        self._saved_state: list[dict[str, Any]] | None = None
        self._created_audio_elements: list[dict[str, str]] = []

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        self._saved_state = [t.to_dict() for t in project.tracks]
        self._created_audio_elements = []

        audio_track = None
        for track in project.tracks:
            if track.type == TrackType.AUDIO:
                audio_track = track
                break

        if not audio_track:
            audio_track = Track(
                id=str(uuid.uuid4()),
                type=TrackType.AUDIO,
                name="Audio Track",
            )
            project.add_track(audio_track)

        for element_ref in self._elements:
            track_id = element_ref.get("track_id")
            element_id = element_ref.get("element_id")

            track = project.get_track(track_id)
            if not track or track.type != TrackType.VIDEO:
                continue

            element = None
            for e in track.elements:
                if e.id == element_id:
                    element = e
                    break

            if not element or element.media_type != MediaType.VIDEO:
                continue

            audio_element_id = str(uuid.uuid4())
            audio_element = TimelineElement(
                id=audio_element_id,
                track_id=audio_track.id,
                media_type=MediaType.AUDIO,
                name=f"{element.name} (audio)",
                start_time=element.start_time,
                duration=element.duration,
                trim_start=element.trim_start,
                trim_end=element.trim_end,
                volume=1.0,
                properties={"source_element_id": element_id},
            )
            audio_track.elements.append(audio_element)
            self._created_audio_elements.append({
                "track_id": audio_track.id,
                "element_id": audio_element_id,
            })

            element.volume = 0.0

        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        if not self._saved_state:
            return

        project = video_manager.get_project(self._project_id)
        if not project:
            return

        project.tracks = [Track.from_dict(t) for t in self._saved_state]
        project.calculate_duration()
        project.update_timestamp()
        video_manager._save_projects()
