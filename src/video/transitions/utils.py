import uuid
from ..types import Track, TrackTransition, TransitionType, TimelineElement

ADJACENCY_EPSILON = 0.05


def build_track_transition(
    transition_type: TransitionType,
    duration: float,
    from_element_id: str,
    to_element_id: str
) -> TrackTransition:
    return TrackTransition(
        id=str(uuid.uuid4()),
        type=transition_type,
        duration=duration,
        from_element_id=from_element_id,
        to_element_id=to_element_id,
    )


def add_transition_to_track(
    track: Track,
    transition: TrackTransition
) -> Track:
    transitions = track.transitions or []
    existing = None
    for t in transitions:
        if (t.from_element_id == transition.from_element_id and
            t.to_element_id == transition.to_element_id):
            existing = t
            break

    if existing:
        new_transitions = [
            transition if t.id == existing.id else t
            for t in transitions
        ]
    else:
        new_transitions = transitions + [transition]

    return Track(
        id=track.id,
        type=track.type,
        name=track.name,
        elements=track.elements,
        transitions=new_transitions,
        is_main=track.is_main,
        muted=track.muted,
        visible=track.visible,
        locked=track.locked,
        order=track.order,
        created_at=track.created_at,
        updated_at=track.updated_at,
    )


def remove_transition_from_track(
    track: Track,
    transition_id: str
) -> Track:
    transitions = track.transitions or []
    new_transitions = [t for t in transitions if t.id != transition_id]

    return Track(
        id=track.id,
        type=track.type,
        name=track.name,
        elements=track.elements,
        transitions=new_transitions,
        is_main=track.is_main,
        muted=track.muted,
        visible=track.visible,
        locked=track.locked,
        order=track.order,
        created_at=track.created_at,
        updated_at=track.updated_at,
    )


def are_elements_adjacent(
    element_a: TimelineElement,
    element_b: TimelineElement,
    threshold: float = ADJACENCY_EPSILON
) -> bool:
    end_a = element_a.start_time + element_a.duration
    gap = abs(element_b.start_time - end_a)
    return gap < threshold


def _find_adjacent_pairs(track: Track) -> list[tuple[TimelineElement, TimelineElement]]:
    sorted_elements = sorted(track.elements, key=lambda e: e.start_time)
    pairs: list[tuple[TimelineElement, TimelineElement]] = []

    for i in range(len(sorted_elements) - 1):
        current = sorted_elements[i]
        next_elem = sorted_elements[i + 1]
        if are_elements_adjacent(current, next_elem):
            pairs.append((current, next_elem))

    return pairs


def cleanup_transitions_for_track(track: Track) -> Track:
    transitions = track.transitions or []
    element_ids = {element.id for element in track.elements}
    pairs = _find_adjacent_pairs(track)
    valid_pair_keys = {f"{pair[0].id}:{pair[1].id}" for pair in pairs}

    valid_transitions = [
        transition for transition in transitions
        if (element_ids.issuperset({transition.from_element_id, transition.to_element_id}) and
            f"{transition.from_element_id}:{transition.to_element_id}" in valid_pair_keys)
    ]

    if len(valid_transitions) == len(transitions):
        return track

    return Track(
        id=track.id,
        type=track.type,
        name=track.name,
        elements=track.elements,
        transitions=valid_transitions,
        is_main=track.is_main,
        muted=track.muted,
        visible=track.visible,
        locked=track.locked,
        order=track.order,
        created_at=track.created_at,
        updated_at=track.updated_at,
    )


def get_transition_at_time(
    track: Track,
    time: float
) -> TrackTransition | None:
    transitions = track.transitions or []

    for transition in transitions:
        from_element = None
        to_element = None
        for element in track.elements:
            if element.id == transition.from_element_id:
                from_element = element
            elif element.id == transition.to_element_id:
                to_element = element

        if from_element and to_element:
            transition_start = from_element.start_time + from_element.duration - transition.duration / 2
            transition_end = to_element.start_time + transition.duration / 2

            if transition_start <= time <= transition_end:
                return transition

    return None
