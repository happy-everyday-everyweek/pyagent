import uuid

from ..manager import video_manager
from ..types import MediaType, TrackTransition, TransitionType
from .base import Command

ADJACENCY_EPSILON = 0.05


def _are_elements_adjacent(from_element, to_element) -> bool:
    from_end = from_element.start_time + from_element.duration
    gap = abs(to_element.start_time - from_end)
    return gap < ADJACENCY_EPSILON


class AddTransitionCommand(Command):
    def __init__(
        self,
        project_id: str,
        track_id: str,
        from_element_id: str,
        to_element_id: str,
        transition_type: TransitionType,
        duration: float = 0.5,
    ):
        self._project_id = project_id
        self._track_id = track_id
        self._from_element_id = from_element_id
        self._to_element_id = to_element_id
        self._transition_type = transition_type
        self._duration = duration
        self._transition_id: str | None = None
        self._existing_transition: TrackTransition | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            raise ValueError(f"Project {self._project_id} not found")

        track = project.get_track(self._track_id)
        if not track:
            raise ValueError(f"Track {self._track_id} not found")

        from_element = None
        to_element = None
        for element in track.elements:
            if element.id == self._from_element_id:
                from_element = element
            elif element.id == self._to_element_id:
                to_element = element

        if not from_element:
            raise ValueError(f"From element {self._from_element_id} not found")
        if not to_element:
            raise ValueError(f"To element {self._to_element_id} not found")

        if from_element.media_type not in (MediaType.VIDEO, MediaType.IMAGE):
            raise ValueError("From element must be video or image")
        if to_element.media_type not in (MediaType.VIDEO, MediaType.IMAGE):
            raise ValueError("To element must be video or image")

        if not _are_elements_adjacent(from_element, to_element):
            raise ValueError("Elements are not adjacent")

        for transition in track.transitions:
            if (transition.from_element_id == self._from_element_id and
                transition.to_element_id == self._to_element_id):
                self._existing_transition = transition
                break

        if self._transition_id:
            transition = TrackTransition(
                id=self._transition_id,
                type=self._transition_type,
                duration=self._duration,
                from_element_id=self._from_element_id,
                to_element_id=self._to_element_id,
            )
        else:
            self._transition_id = str(uuid.uuid4())
            transition = TrackTransition(
                id=self._transition_id,
                type=self._transition_type,
                duration=self._duration,
                from_element_id=self._from_element_id,
                to_element_id=self._to_element_id,
            )

        if self._existing_transition:
            for i, t in enumerate(track.transitions):
                if t.id == self._existing_transition.id:
                    track.transitions[i] = transition
                    break
        else:
            track.transitions.append(transition)

        project.update_timestamp()
        video_manager._save_projects()

    def undo(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            return

        track = project.get_track(self._track_id)
        if not track:
            return

        if self._existing_transition:
            for i, t in enumerate(track.transitions):
                if t.id == self._transition_id:
                    track.transitions[i] = self._existing_transition
                    break
        else:
            track.transitions = [
                t for t in track.transitions if t.id != self._transition_id
            ]

        project.update_timestamp()
        video_manager._save_projects()

    def get_transition_id(self) -> str | None:
        return self._transition_id

    @property
    def description(self) -> str | None:
        return f"Add {self._transition_type.value} transition"


class RemoveTransitionCommand(Command):
    def __init__(
        self,
        project_id: str,
        track_id: str,
        transition_id: str,
    ):
        self._project_id = project_id
        self._track_id = track_id
        self._transition_id = transition_id
        self._removed_transition: TrackTransition | None = None

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            raise ValueError(f"Project {self._project_id} not found")

        track = project.get_track(self._track_id)
        if not track:
            raise ValueError(f"Track {self._track_id} not found")

        for i, transition in enumerate(track.transitions):
            if transition.id == self._transition_id:
                self._removed_transition = transition
                track.transitions.pop(i)
                project.update_timestamp()
                video_manager._save_projects()
                return

        raise ValueError(f"Transition {self._transition_id} not found")

    def undo(self) -> None:
        if not self._removed_transition:
            return

        project = video_manager.get_project(self._project_id)
        if not project:
            return

        track = project.get_track(self._track_id)
        if not track:
            return

        track.transitions.append(self._removed_transition)
        project.update_timestamp()
        video_manager._save_projects()

    @property
    def description(self) -> str | None:
        return f"Remove transition {self._transition_id}"


class UpdateTransitionCommand(Command):
    def __init__(
        self,
        project_id: str,
        track_id: str,
        transition_id: str,
        updates: dict,
    ):
        self._project_id = project_id
        self._track_id = track_id
        self._transition_id = transition_id
        self._updates = updates
        self._original_values: dict = {}

    def execute(self) -> None:
        project = video_manager.get_project(self._project_id)
        if not project:
            raise ValueError(f"Project {self._project_id} not found")

        track = project.get_track(self._track_id)
        if not track:
            raise ValueError(f"Track {self._track_id} not found")

        transition = None
        for t in track.transitions:
            if t.id == self._transition_id:
                transition = t
                break

        if not transition:
            raise ValueError(f"Transition {self._transition_id} not found")

        self._original_values = {}

        if "type" in self._updates:
            self._original_values["type"] = transition.type
            transition.type = self._updates["type"]

        if "duration" in self._updates:
            self._original_values["duration"] = transition.duration
            transition.duration = self._updates["duration"]

        if "from_element_id" in self._updates:
            self._original_values["from_element_id"] = transition.from_element_id
            transition.from_element_id = self._updates["from_element_id"]

        if "to_element_id" in self._updates:
            self._original_values["to_element_id"] = transition.to_element_id
            transition.to_element_id = self._updates["to_element_id"]

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

        transition = None
        for t in track.transitions:
            if t.id == self._transition_id:
                transition = t
                break

        if not transition:
            return

        for key, value in self._original_values.items():
            if key == "type":
                transition.type = value
            elif key == "duration":
                transition.duration = value
            elif key == "from_element_id":
                transition.from_element_id = value
            elif key == "to_element_id":
                transition.to_element_id = value

        project.update_timestamp()
        video_manager._save_projects()

    @property
    def description(self) -> str | None:
        return f"Update transition {self._transition_id}"
