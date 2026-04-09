from typing import Optional

from .base import Transition
from .fade import DissolveTransition, FadeTransition
from .slide import SlideTransition
from .wipe import WipeTransition
from .zoom import ZoomInTransition, ZoomOutTransition

TRANSITION_REGISTRY: dict[str, type[Transition]] = {
    "fade": FadeTransition,
    "dissolve": DissolveTransition,
    "wipe-left": lambda duration: WipeTransition(duration, "left"),
    "wipe-right": lambda duration: WipeTransition(duration, "right"),
    "wipe-up": lambda duration: WipeTransition(duration, "up"),
    "wipe-down": lambda duration: WipeTransition(duration, "down"),
    "slide-left": lambda duration: SlideTransition(duration, "left"),
    "slide-right": lambda duration: SlideTransition(duration, "right"),
    "slide-up": lambda duration: SlideTransition(duration, "up"),
    "slide-down": lambda duration: SlideTransition(duration, "down"),
    "zoom-in": ZoomInTransition,
    "zoom-out": ZoomOutTransition,
}


def get_transition(transition_type: str, duration: float = 0.5) -> Transition | None:
    transition_factory = TRANSITION_REGISTRY.get(transition_type)
    if transition_factory is None:
        return None
    if callable(transition_factory) and not isinstance(transition_factory, type):
        return transition_factory(duration)
    return transition_factory(duration)


__all__ = [
    "TRANSITION_REGISTRY",
    "DissolveTransition",
    "FadeTransition",
    "SlideTransition",
    "Transition",
    "WipeTransition",
    "ZoomInTransition",
    "ZoomOutTransition",
    "get_transition",
]
