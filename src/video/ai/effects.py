from dataclasses import dataclass
from typing import Optional
import random


@dataclass
class EffectRecommendation:
    effect_type: str
    effect_name: str
    confidence: float
    parameters: dict
    reason: str


class EffectRecommendationService:
    def __init__(self, max_suggestions: int = 5):
        self.max_suggestions = max_suggestions
        self._available_transitions = [
            "fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down",
            "slide-left", "slide-right", "slide-up", "slide-down", "zoom-in", "zoom-out"
        ]
        self._available_filters = [
            "brightness", "contrast", "saturation", "vintage", "black_white",
            "sepia", "warm", "cool", "dramatic", "soft"
        ]

    def analyze_video_style(self, video_path: str) -> dict:
        return {
            "brightness": random.uniform(0.8, 1.2),
            "contrast": random.uniform(0.9, 1.1),
            "saturation": random.uniform(0.85, 1.15),
            "motion_intensity": random.uniform(0.0, 1.0),
            "scene_count": random.randint(5, 20),
            "dominant_colors": ["#336699", "#99CCFF", "#FFCC00"],
            "style": random.choice(["cinematic", "documentary", "vlog", "commercial"])
        }

    def recommend_transitions(
        self,
        video_path: str,
        scene_count: Optional[int] = None
    ) -> list[EffectRecommendation]:
        style = self.analyze_video_style(video_path)
        recommendations = []
        transitions = random.sample(
            self._available_transitions,
            min(self.max_suggestions, len(self._available_transitions))
        )
        for trans in transitions:
            confidence = random.uniform(0.6, 0.95)
            recommendations.append(EffectRecommendation(
                effect_type="transition",
                effect_name=trans,
                confidence=confidence,
                parameters={"duration": random.uniform(0.3, 1.0)},
                reason=f"Matches {style['style']} style"
            ))
        return sorted(recommendations, key=lambda x: x.confidence, reverse=True)

    def recommend_filters(self, video_path: str) -> list[EffectRecommendation]:
        style = self.analyze_video_style(video_path)
        recommendations = []
        filters = random.sample(
            self._available_filters,
            min(self.max_suggestions, len(self._available_filters))
        )
        for filt in filters:
            confidence = random.uniform(0.5, 0.9)
            params = {}
            if filt == "brightness":
                params["value"] = random.uniform(0.8, 1.2)
            elif filt == "contrast":
                params["value"] = random.uniform(0.9, 1.1)
            elif filt == "saturation":
                params["value"] = random.uniform(0.7, 1.3)
            recommendations.append(EffectRecommendation(
                effect_type="filter",
                effect_name=filt,
                confidence=confidence,
                parameters=params,
                reason=f"Enhances {style['style']} aesthetic"
            ))
        return sorted(recommendations, key=lambda x: x.confidence, reverse=True)

    def recommend_music(self, video_path: str, mood: Optional[str] = None) -> list[dict]:
        style = self.analyze_video_style(video_path)
        detected_mood = mood or random.choice(["happy", "sad", "energetic", "calm", "dramatic"])
        music_library = {
            "happy": ["upbeat_pop", "sunny_acoustic", "cheerful_ukulele"],
            "sad": ["melancholic_piano", "emotional_strings", "somber_ambient"],
            "energetic": ["electronic_beat", "rock_anthem", "fast_tempo"],
            "calm": ["ambient_pad", "soft_piano", "nature_sounds"],
            "dramatic": ["orchestral_epic", "cinematic_drone", "tension_build"]
        }
        tracks = music_library.get(detected_mood, music_library["calm"])
        return [
            {
                "track_name": track,
                "mood": detected_mood,
                "duration": random.uniform(120, 300),
                "bpm": random.randint(60, 140),
                "confidence": random.uniform(0.7, 0.95)
            }
            for track in tracks
        ]

    def get_all_recommendations(self, video_path: str) -> dict:
        return {
            "transitions": self.recommend_transitions(video_path),
            "filters": self.recommend_filters(video_path),
            "music": self.recommend_music(video_path),
            "style_analysis": self.analyze_video_style(video_path)
        }
