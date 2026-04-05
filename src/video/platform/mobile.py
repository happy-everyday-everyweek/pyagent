import json
import math
import os
import platform
import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from src.video.platform.base import PlatformAdapter, PlatformCapabilities


class GestureType(Enum):
    NONE = "none"
    PINCH = "pinch"
    PAN = "pan"
    ROTATE = "rotate"
    TAP = "tap"


@dataclass
class TouchPoint:
    x: float = 0.0
    y: float = 0.0
    timestamp: float = 0.0


@dataclass
class DeviceTier:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RendererConfig:
    renderer_type: str = "opengl_es"
    max_texture_size: int = 2048
    supports_vao: bool = False
    supports_instancing: bool = False
    max_render_targets: int = 1
    preferred_color_format: str = "rgba4444"
    depth_buffer_bits: int = 16
    antialiasing_samples: int = 0
    use_compressed_textures: bool = True
    texture_compression_format: str = "etc2"

    def to_dict(self) -> dict[str, Any]:
        return {
            "renderer_type": self.renderer_type,
            "max_texture_size": self.max_texture_size,
            "supports_vao": self.supports_vao,
            "supports_instancing": self.supports_instancing,
            "max_render_targets": self.max_render_targets,
            "preferred_color_format": self.preferred_color_format,
            "depth_buffer_bits": self.depth_buffer_bits,
            "antialiasing_samples": self.antialiasing_samples,
            "use_compressed_textures": self.use_compressed_textures,
            "texture_compression_format": self.texture_compression_format,
        }


class TouchGestureHandler:
    GESTURE_THRESHOLD_PINCH = 10.0
    GESTURE_THRESHOLD_ROTATE = 5.0
    GESTURE_THRESHOLD_PAN = 5.0
    GESTURE_THRESHOLD_TAP_TIME = 300
    GESTURE_THRESHOLD_TAP_DISTANCE = 10.0

    def __init__(self):
        self._touch_points: list[TouchPoint] = []
        self._initial_distance: float = 0.0
        self._initial_angle: float = 0.0
        self._initial_center: tuple[float, float] = (0.0, 0.0)
        self._current_gesture: GestureType = GestureType.NONE
        self._scale: float = 1.0
        self._rotation: float = 0.0
        self._translation: tuple[float, float] = (0.0, 0.0)
        self._start_time: float = 0.0
        self._start_point: TouchPoint | None = None
        self._prev_point: TouchPoint | None = None
        self._is_multi_touch: bool = False
        self._touch_ids: set[int] = set()

    def on_touch_start(self, x: float, y: float, touch_id: int = 0) -> None:
        timestamp = datetime.now().timestamp() * 1000
        point = TouchPoint(x=x, y=y, timestamp=timestamp)

        self._touch_ids.add(touch_id)

        if len(self._touch_ids) == 1:
            self._start_time = timestamp
            self._start_point = point
            self._prev_point = point
            self._current_gesture = GestureType.NONE
            self._scale = 1.0
            self._rotation = 0.0
            self._translation = (0.0, 0.0)
        elif len(self._touch_ids) == 2:
            self._is_multi_touch = True
            self._touch_points = [self._start_point, point]
            self._initial_distance = self._calculate_distance(
                self._touch_points[0], self._touch_points[1]
            )
            self._initial_angle = self._calculate_angle(
                self._touch_points[0], self._touch_points[1]
            )
            self._initial_center = self._calculate_center(
                self._touch_points[0], self._touch_points[1]
            )
            self._current_gesture = GestureType.NONE

    def on_touch_move(self, x: float, y: float, touch_id: int = 0) -> None:
        timestamp = datetime.now().timestamp() * 1000
        point = TouchPoint(x=x, y=y, timestamp=timestamp)

        if self._is_multi_touch and len(self._touch_ids) >= 2:
            if touch_id == 0 or touch_id == min(self._touch_ids):
                self._touch_points[0] = point
            else:
                self._touch_points[1] = point

            current_distance = self._calculate_distance(
                self._touch_points[0], self._touch_points[1]
            )
            current_angle = self._calculate_angle(
                self._touch_points[0], self._touch_points[1]
            )
            current_center = self._calculate_center(
                self._touch_points[0], self._touch_points[1]
            )

            if self._initial_distance > 0:
                self._scale = current_distance / self._initial_distance

            angle_delta = current_angle - self._initial_angle
            while angle_delta > 180:
                angle_delta -= 360
            while angle_delta < -180:
                angle_delta += 360
            self._rotation = angle_delta

            self._translation = (
                current_center[0] - self._initial_center[0],
                current_center[1] - self._initial_center[1],
            )

            scale_delta = abs(self._scale - 1.0) * 100
            rotation_delta = abs(self._rotation)
            translation_delta = math.sqrt(
                self._translation[0] ** 2 + self._translation[1] ** 2
            )

            if scale_delta > self.GESTURE_THRESHOLD_PINCH:
                self._current_gesture = GestureType.PINCH
            elif rotation_delta > self.GESTURE_THRESHOLD_ROTATE:
                self._current_gesture = GestureType.ROTATE
            elif translation_delta > self.GESTURE_THRESHOLD_PAN:
                self._current_gesture = GestureType.PAN
        else:
            if self._start_point:
                dx = x - self._start_point.x
                dy = y - self._start_point.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > self.GESTURE_THRESHOLD_PAN:
                    self._current_gesture = GestureType.PAN
                    self._translation = (dx, dy)

            self._prev_point = point

    def on_touch_end(self, touch_id: int = 0) -> None:
        self._touch_ids.discard(touch_id)

        if len(self._touch_ids) == 0:
            if self._current_gesture == GestureType.NONE and self._start_point:
                timestamp = datetime.now().timestamp() * 1000
                duration = timestamp - self._start_time

                if duration < self.GESTURE_THRESHOLD_TAP_TIME and self._prev_point:
                    dx = self._prev_point.x - self._start_point.x
                    dy = self._prev_point.y - self._start_point.y
                    distance = math.sqrt(dx * dx + dy * dy)

                    if distance < self.GESTURE_THRESHOLD_TAP_DISTANCE:
                        self._current_gesture = GestureType.TAP

            self._is_multi_touch = False
            self._touch_points = []

    def get_gesture(self) -> GestureType:
        return self._current_gesture

    def get_scale(self) -> float:
        return self._scale

    def get_rotation(self) -> float:
        return self._rotation

    def get_translation(self) -> tuple[float, float]:
        return self._translation

    def reset(self) -> None:
        self._touch_points = []
        self._initial_distance = 0.0
        self._initial_angle = 0.0
        self._initial_center = (0.0, 0.0)
        self._current_gesture = GestureType.NONE
        self._scale = 1.0
        self._rotation = 0.0
        self._translation = (0.0, 0.0)
        self._start_time = 0.0
        self._start_point = None
        self._prev_point = None
        self._is_multi_touch = False
        self._touch_ids = set()

    def _calculate_distance(self, p1: TouchPoint, p2: TouchPoint) -> float:
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return math.sqrt(dx * dx + dy * dy)

    def _calculate_angle(self, p1: TouchPoint, p2: TouchPoint) -> float:
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return math.degrees(math.atan2(dy, dx))

    def _calculate_center(self, p1: TouchPoint, p2: TouchPoint) -> tuple[float, float]:
        return ((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)


class PerformanceOptimizer:
    TIER_CONFIGS = {
        DeviceTier.LOW: {
            "preview_resolution": (640, 360),
            "preview_fps": 15,
            "max_effects": 2,
            "max_tracks": 3,
            "thumbnail_quality": 50,
            "use_proxy": True,
            "proxy_resolution": (480, 270),
        },
        DeviceTier.MEDIUM: {
            "preview_resolution": (1280, 720),
            "preview_fps": 24,
            "max_effects": 4,
            "max_tracks": 5,
            "thumbnail_quality": 70,
            "use_proxy": True,
            "proxy_resolution": (640, 360),
        },
        DeviceTier.HIGH: {
            "preview_resolution": (1920, 1080),
            "preview_fps": 30,
            "max_effects": 8,
            "max_tracks": 10,
            "thumbnail_quality": 90,
            "use_proxy": False,
            "proxy_resolution": (1280, 720),
        },
    }

    def __init__(self):
        self._device_tier: str = DeviceTier.MEDIUM
        self._cpu_cores: int = 4
        self._total_memory_mb: int = 2048
        self._gpu_info: dict[str, Any] = {}
        self._screen_density: int = 320
        self._is_detected: bool = False

    def detect_device_tier(self) -> str:
        if self._is_detected:
            return self._device_tier

        self._detect_hardware_info()

        score = 0

        if self._cpu_cores >= 8:
            score += 3
        elif self._cpu_cores >= 6:
            score += 2
        elif self._cpu_cores >= 4:
            score += 1

        if self._total_memory_mb >= 8192:
            score += 3
        elif self._total_memory_mb >= 4096:
            score += 2
        elif self._total_memory_mb >= 2048:
            score += 1

        if self._screen_density >= 480:
            score += 2
        elif self._screen_density >= 320:
            score += 1

        gpu_renderer = self._gpu_info.get("renderer", "").lower()
        high_end_gpus = ["adreno 6", "adreno 7", "mali-g7", "mali-g8", "apple gpu"]
        mid_end_gpus = ["adreno 5", "mali-g5", "mali-g6"]

        for gpu in high_end_gpus:
            if gpu in gpu_renderer:
                score += 3
                break
        else:
            for gpu in mid_end_gpus:
                if gpu in gpu_renderer:
                    score += 2
                    break

        if score >= 8:
            self._device_tier = DeviceTier.HIGH
        elif score >= 5:
            self._device_tier = DeviceTier.MEDIUM
        else:
            self._device_tier = DeviceTier.LOW

        self._is_detected = True
        return self._device_tier

    def _detect_hardware_info(self) -> None:
        self._cpu_cores = os.cpu_count() or 4

        try:
            if platform.system().lower() == "linux":
                meminfo_path = "/proc/meminfo"
                if os.path.exists(meminfo_path):
                    with open(meminfo_path, "r") as f:
                        for line in f:
                            if line.startswith("MemTotal:"):
                                kb = int(line.split()[1])
                                self._total_memory_mb = kb // 1024
                                break
        except Exception:
            self._total_memory_mb = 2048

        try:
            if "ANDROID_ROOT" in os.environ:
                result = subprocess.run(
                    ["getprop", "ro.sf.lcd_density"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    self._screen_density = int(result.stdout.strip())
        except Exception:
            self._screen_density = 320

        try:
            if os.path.exists("/sys/class/kgsl/kgsl-3d0/gpu_model"):
                with open("/sys/class/kgsl/kgsl-3d0/gpu_model", "r") as f:
                    self._gpu_info["renderer"] = f.read().strip()
            elif os.path.exists("/sys/class/misc/mali0/device/gpuinfo"):
                with open("/sys/class/misc/mali0/device/gpuinfo", "r") as f:
                    self._gpu_info["renderer"] = f.read().strip()
        except Exception:
            pass

    def get_optimal_preview_resolution(self) -> tuple[int, int]:
        tier = self.detect_device_tier()
        return self.TIER_CONFIGS[tier]["preview_resolution"]

    def get_optimal_preview_fps(self) -> int:
        tier = self.detect_device_tier()
        return self.TIER_CONFIGS[tier]["preview_fps"]

    def should_reduce_quality(self) -> bool:
        tier = self.detect_device_tier()
        return tier == DeviceTier.LOW

    def get_max_effects(self) -> int:
        tier = self.detect_device_tier()
        return self.TIER_CONFIGS[tier]["max_effects"]

    def get_max_tracks(self) -> int:
        tier = self.detect_device_tier()
        return self.TIER_CONFIGS[tier]["max_tracks"]

    def get_thumbnail_quality(self) -> int:
        tier = self.detect_device_tier()
        return self.TIER_CONFIGS[tier]["thumbnail_quality"]

    def should_use_proxy(self) -> bool:
        tier = self.detect_device_tier()
        return self.TIER_CONFIGS[tier]["use_proxy"]

    def get_proxy_resolution(self) -> tuple[int, int]:
        tier = self.detect_device_tier()
        return self.TIER_CONFIGS[tier]["proxy_resolution"]

    def get_device_info(self) -> dict[str, Any]:
        return {
            "tier": self._device_tier,
            "cpu_cores": self._cpu_cores,
            "total_memory_mb": self._total_memory_mb,
            "screen_density": self._screen_density,
            "gpu_info": self._gpu_info,
        }


class OfflineStorage:
    TABLE_PROJECTS = "projects"
    TABLE_MEDIA_CACHE = "media_cache"
    TABLE_SYNC_QUEUE = "sync_queue"

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            data_dir = Path("data/video/mobile")
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "offline.db")

        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._is_initialized: bool = False

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_tables(self) -> None:
        if self._is_initialized:
            return

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_PROJECTS} (
                project_id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                sync_status TEXT DEFAULT 'pending',
                server_id TEXT
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_MEDIA_CACHE} (
                media_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                local_path TEXT NOT NULL,
                remote_url TEXT,
                cache_size INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL
            )
        """)

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_SYNC_QUEUE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                data TEXT,
                created_at REAL NOT NULL,
                retry_count INTEGER DEFAULT 0,
                last_error TEXT
            )
        """)

        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_projects_updated ON {self.TABLE_PROJECTS}(updated_at)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_media_project ON {self.TABLE_MEDIA_CACHE}(project_id)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_sync_project ON {self.TABLE_SYNC_QUEUE}(project_id)"
        )

        conn.commit()
        self._is_initialized = True

    def save_project(self, project_id: str, data: dict[str, Any]) -> bool:
        self._ensure_tables()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            now = datetime.now().timestamp()
            data_json = json.dumps(data, ensure_ascii=False)

            cursor.execute(
                f"SELECT project_id FROM {self.TABLE_PROJECTS} WHERE project_id = ?",
                (project_id,),
            )

            if cursor.fetchone():
                cursor.execute(
                    f"""
                    UPDATE {self.TABLE_PROJECTS}
                    SET data = ?, updated_at = ?, sync_status = 'pending'
                    WHERE project_id = ?
                    """,
                    (data_json, now, project_id),
                )
            else:
                cursor.execute(
                    f"""
                    INSERT INTO {self.TABLE_PROJECTS} (project_id, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (project_id, data_json, now, now),
                )

            conn.commit()
            return True

        except Exception:
            return False

    def load_project(self, project_id: str) -> dict[str, Any] | None:
        self._ensure_tables()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"SELECT data FROM {self.TABLE_PROJECTS} WHERE project_id = ?",
                (project_id,),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row["data"])

            return None

        except Exception:
            return None

    def list_projects(self) -> list[dict[str, Any]]:
        self._ensure_tables()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT project_id, created_at, updated_at, sync_status
                FROM {self.TABLE_PROJECTS}
                ORDER BY updated_at DESC
                """
            )

            projects = []
            for row in cursor.fetchall():
                projects.append(
                    {
                        "project_id": row["project_id"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "sync_status": row["sync_status"],
                    }
                )

            return projects

        except Exception:
            return []

    def delete_project(self, project_id: str) -> bool:
        self._ensure_tables()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM {self.TABLE_MEDIA_CACHE} WHERE project_id = ?",
                (project_id,),
            )

            cursor.execute(
                f"DELETE FROM {self.TABLE_SYNC_QUEUE} WHERE project_id = ?",
                (project_id,),
            )

            cursor.execute(
                f"DELETE FROM {self.TABLE_PROJECTS} WHERE project_id = ?",
                (project_id,),
            )

            conn.commit()
            return True

        except Exception:
            return False

    def sync_to_server(self) -> dict[str, Any]:
        self._ensure_tables()

        result = {
            "synced": 0,
            "failed": 0,
            "pending": 0,
            "errors": [],
        }

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT project_id, data, updated_at
                FROM {self.TABLE_PROJECTS}
                WHERE sync_status = 'pending'
                ORDER BY updated_at ASC
                """
            )

            pending_projects = cursor.fetchall()
            result["pending"] = len(pending_projects)

            for row in pending_projects:
                project_id = row["project_id"]
                data = json.loads(row["data"])

                sync_success = self._perform_sync(project_id, data)

                if sync_success:
                    cursor.execute(
                        f"""
                        UPDATE {self.TABLE_PROJECTS}
                        SET sync_status = 'synced'
                        WHERE project_id = ?
                        """,
                        (project_id,),
                    )
                    result["synced"] += 1
                else:
                    cursor.execute(
                        f"""
                        UPDATE {self.TABLE_PROJECTS}
                        SET sync_status = 'error'
                        WHERE project_id = ?
                        """,
                        (project_id,),
                    )
                    result["failed"] += 1
                    result["errors"].append(project_id)

            conn.commit()

        except Exception as e:
            result["errors"].append(str(e))

        return result

    def _perform_sync(self, project_id: str, data: dict[str, Any]) -> bool:
        return True

    def cache_media(
        self,
        media_id: str,
        project_id: str,
        local_path: str,
        remote_url: str | None = None,
    ) -> bool:
        self._ensure_tables()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            now = datetime.now().timestamp()
            cache_size = 0

            if os.path.exists(local_path):
                cache_size = os.path.getsize(local_path)

            cursor.execute(
                f"""
                INSERT OR REPLACE INTO {self.TABLE_MEDIA_CACHE}
                (media_id, project_id, local_path, remote_url, cache_size, created_at, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (media_id, project_id, local_path, remote_url, cache_size, now, now),
            )

            conn.commit()
            return True

        except Exception:
            return False

    def get_cached_media(self, media_id: str) -> dict[str, Any] | None:
        self._ensure_tables()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"SELECT * FROM {self.TABLE_MEDIA_CACHE} WHERE media_id = ?",
                (media_id,),
            )

            row = cursor.fetchone()
            if row:
                now = datetime.now().timestamp()
                cursor.execute(
                    f"""
                    UPDATE {self.TABLE_MEDIA_CACHE}
                    SET last_accessed = ?
                    WHERE media_id = ?
                    """,
                    (now, media_id),
                )
                conn.commit()

                return dict(row)

            return None

        except Exception:
            return None

    def clear_cache(self, max_age_days: int = 7) -> int:
        self._ensure_tables()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now().timestamp() - (max_age_days * 86400)

            cursor.execute(
                f"SELECT local_path FROM {self.TABLE_MEDIA_CACHE} WHERE last_accessed < ?",
                (cutoff,),
            )

            deleted = 0
            for row in cursor.fetchall():
                try:
                    if os.path.exists(row["local_path"]):
                        os.remove(row["local_path"])
                        deleted += 1
                except Exception:
                    pass

            cursor.execute(
                f"DELETE FROM {self.TABLE_MEDIA_CACHE} WHERE last_accessed < ?",
                (cutoff,),
            )

            conn.commit()
            return deleted

        except Exception:
            return 0

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


class MobileAdapter(PlatformAdapter):
    def __init__(self):
        super().__init__()
        self._storage: OfflineStorage | None = None
        self._performance_optimizer: PerformanceOptimizer | None = None
        self._gesture_handler: TouchGestureHandler | None = None
        self._renderer_config: RendererConfig | None = None

    def get_platform_name(self) -> str:
        return "mobile"

    def detect_capabilities(self) -> PlatformCapabilities:
        optimizer = PerformanceOptimizer()
        tier = optimizer.detect_device_tier()

        capabilities = PlatformCapabilities(
            can_hardware_encode=self._detect_hardware_encode(),
            can_gpu_render=self._detect_gpu_render(),
            max_preview_fps=optimizer.get_optimal_preview_fps(),
            max_resolution=optimizer.get_optimal_preview_resolution(),
            supports_touch=True,
            supports_offline=True,
            storage_type="sqlite",
            renderer_type="opengl_es",
        )

        self.capabilities = capabilities
        return capabilities

    def _detect_hardware_encode(self) -> bool:
        try:
            if "ANDROID_ROOT" in os.environ:
                if os.path.exists("/dev/video33"):
                    return True
                if os.path.exists("/system/lib/libstagefright.so"):
                    return True
        except Exception:
            pass

        return False

    def _detect_gpu_render(self) -> bool:
        try:
            if os.path.exists("/dev/kgsl-3d0"):
                return True
            if os.path.exists("/dev/mali"):
                return True
            if os.path.exists("/dev/pvr"):
                return True
        except Exception:
            pass

        return False

    def get_storage(self) -> OfflineStorage:
        if self._storage is None:
            self._storage = OfflineStorage()
        return self._storage

    def get_renderer_config(self) -> dict[str, Any]:
        if self._renderer_config is None:
            optimizer = PerformanceOptimizer()
            tier = optimizer.detect_device_tier()

            if tier == DeviceTier.HIGH:
                self._renderer_config = RendererConfig(
                    renderer_type="opengl_es",
                    max_texture_size=4096,
                    supports_vao=True,
                    supports_instancing=True,
                    max_render_targets=4,
                    preferred_color_format="rgba8888",
                    depth_buffer_bits=24,
                    antialiasing_samples=4,
                    use_compressed_textures=True,
                    texture_compression_format="etc2",
                )
            elif tier == DeviceTier.MEDIUM:
                self._renderer_config = RendererConfig(
                    renderer_type="opengl_es",
                    max_texture_size=2048,
                    supports_vao=True,
                    supports_instancing=False,
                    max_render_targets=2,
                    preferred_color_format="rgba565",
                    depth_buffer_bits=16,
                    antialiasing_samples=2,
                    use_compressed_textures=True,
                    texture_compression_format="etc2",
                )
            else:
                self._renderer_config = RendererConfig(
                    renderer_type="opengl_es",
                    max_texture_size=1024,
                    supports_vao=False,
                    supports_instancing=False,
                    max_render_targets=1,
                    preferred_color_format="rgba4444",
                    depth_buffer_bits=16,
                    antialiasing_samples=0,
                    use_compressed_textures=True,
                    texture_compression_format="etc1",
                )

        return self._renderer_config.to_dict()

    def get_gesture_handler(self) -> TouchGestureHandler:
        if self._gesture_handler is None:
            self._gesture_handler = TouchGestureHandler()
        return self._gesture_handler

    def get_performance_optimizer(self) -> PerformanceOptimizer:
        if self._performance_optimizer is None:
            self._performance_optimizer = PerformanceOptimizer()
        return self._performance_optimizer

    def cleanup(self) -> None:
        if self._storage:
            self._storage.close()
            self._storage = None
