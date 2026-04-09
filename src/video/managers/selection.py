from collections.abc import Callable

from ..types import TimelineElement, Track


class SelectionManager:
    def __init__(self):
        self._selected_elements: set[str] = set()
        self._selected_tracks: set[str] = set()
        self._listeners: set[Callable[[], None]] = set()

    @property
    def selected_elements(self) -> set[str]:
        return self._selected_elements.copy()

    @property
    def selected_tracks(self) -> set[str]:
        return self._selected_tracks.copy()

    def select_element(self, element_id: str, add: bool = False) -> None:
        if not add:
            self._selected_elements.clear()
        if element_id in self._selected_elements:
            self._selected_elements.discard(element_id)
        else:
            self._selected_elements.add(element_id)
        self._notify()

    def deselect_element(self, element_id: str) -> None:
        if element_id in self._selected_elements:
            self._selected_elements.discard(element_id)
            self._notify()

    def select_track(self, track_id: str, add: bool = False) -> None:
        if not add:
            self._selected_tracks.clear()
        if track_id in self._selected_tracks:
            self._selected_tracks.discard(track_id)
        else:
            self._selected_tracks.add(track_id)
        self._notify()

    def deselect_track(self, track_id: str) -> None:
        if track_id in self._selected_tracks:
            self._selected_tracks.discard(track_id)
            self._notify()

    def clear_selection(self) -> None:
        self._selected_elements.clear()
        self._selected_tracks.clear()
        self._notify()

    def get_selected_elements(self, project) -> list[TimelineElement]:
        elements: list[TimelineElement] = []
        for track in project.tracks:
            for element in track.elements:
                if element.id in self._selected_elements:
                    elements.append(element)
        return elements

    def get_selected_tracks(self, project) -> list[Track]:
        tracks: list[Track] = []
        for track in project.tracks:
            if track.id in self._selected_tracks:
                tracks.append(track)
        return tracks

    def has_selection(self) -> bool:
        return bool(self._selected_elements) or bool(self._selected_tracks)

    def has_element_selection(self) -> bool:
        return bool(self._selected_elements)

    def has_track_selection(self) -> bool:
        return bool(self._selected_tracks)

    def select_all_elements(self, project) -> None:
        self._selected_elements.clear()
        for track in project.tracks:
            for element in track.elements:
                self._selected_elements.add(element.id)
        self._notify()

    def select_all_tracks(self, project) -> None:
        self._selected_tracks.clear()
        for track in project.tracks:
            self._selected_tracks.add(track.id)
        self._notify()

    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def _notify(self) -> None:
        for listener in self._listeners:
            listener()
