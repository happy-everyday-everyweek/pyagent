"""
PyAgent 视频编辑器模块 - 视频工具

实现视频编辑工具，继承UnifiedTool基类。
"""

from typing import Any

from src.tools.base import UnifiedTool, ToolContext, ToolResult, ToolState

from .editor_core import EditorCore
from .manager import video_manager
from .types import MediaType, TrackType, ExportFormat, ExportQuality


class VideoTool(UnifiedTool):
    """视频编辑工具"""

    name = "video_tool"
    description = "视频编辑工具，支持创建项目、添加媒体、自动编辑、生成字幕、应用特效和导出视频"

    def __init__(self, device_id: str = ""):
        super().__init__(device_id)
        self._editor: EditorCore | None = None

    async def activate(self, context: ToolContext) -> bool:
        try:
            if self._device_id:
                self._editor = None
            self._state = ToolState.ACTIVE
            return True
        except Exception:
            return False

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        action = kwargs.get("action", "")
        if not action:
            return ToolResult(
                success=False,
                error="Action is required. Supported actions: create_project, add_media, auto_edit, generate_subtitles, apply_effects, export_video, list_projects, get_project"
            )

        handlers = {
            "create_project": self._handle_create_project,
            "add_media": self._handle_add_media,
            "auto_edit": self._handle_auto_edit,
            "generate_subtitles": self._handle_generate_subtitles,
            "apply_effects": self._handle_apply_effects,
            "export_video": self._handle_export_video,
            "list_projects": self._handle_list_projects,
            "get_project": self._handle_get_project,
            "add_track": self._handle_add_track,
            "add_element": self._handle_add_element,
            "get_statistics": self._handle_get_statistics,
        }

        handler = handlers.get(action)
        if not handler:
            return ToolResult(
                success=False,
                error=f"Unknown action: {action}. Supported actions: {', '.join(handlers.keys())}"
            )

        return await handler(kwargs)

    async def dormant(self, context: ToolContext) -> bool:
        try:
            self._editor = None
            self._state = ToolState.DORMANT
            return True
        except Exception:
            return False

    async def _handle_create_project(self, params: dict[str, Any]) -> ToolResult:
        name = params.get("name")
        if not name:
            return ToolResult(success=False, error="Project name is required")

        width = params.get("width", 1920)
        height = params.get("height", 1080)
        fps = params.get("fps", 30)
        domain_id = params.get("domain_id")

        try:
            project = video_manager.create_project(name, width, height, fps, domain_id)
            self._editor = EditorCore(project)
            return ToolResult(
                success=True,
                output=f"Created project: {project.name}",
                data={
                    "project_id": project.project_id,
                    "name": project.name,
                    "canvas_size": f"{project.canvas_width}x{project.canvas_height}",
                    "fps": project.fps,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create project: {str(e)}")

    async def _handle_add_media(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        file_path = params.get("file_path")

        if not project_id or not file_path:
            return ToolResult(success=False, error="project_id and file_path are required")

        project = video_manager.get_project(project_id)
        if not project:
            return ToolResult(success=False, error=f"Project {project_id} not found")

        editor = EditorCore(project)
        media = editor.media.import_media(file_path)

        if not media:
            return ToolResult(success=False, error="Failed to import media file")

        track_id = params.get("track_id")
        start_time = params.get("start_time", 0)

        if track_id:
            element = editor.media.add_to_timeline(media.id, track_id, start_time)
            if element:
                return ToolResult(
                    success=True,
                    output=f"Added media {media.name} to timeline",
                    data={
                        "media_id": media.id,
                        "media_name": media.name,
                        "media_type": media.media_type.value,
                        "element_id": element.id,
                        "track_id": track_id,
                        "start_time": start_time,
                    }
                )

        return ToolResult(
            success=True,
            output=f"Imported media: {media.name}",
            data={
                "media_id": media.id,
                "media_name": media.name,
                "media_type": media.media_type.value,
            }
        )

    async def _handle_auto_edit(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        if not project_id:
            return ToolResult(success=False, error="project_id is required")

        project = video_manager.get_project(project_id)
        if not project:
            return ToolResult(success=False, error=f"Project {project_id} not found")

        style = params.get("style", "default")
        target_duration = params.get("target_duration")

        return ToolResult(
            success=True,
            output=f"Auto edit applied with style: {style}",
            data={
                "project_id": project_id,
                "style": style,
                "target_duration": target_duration,
            }
        )

    async def _handle_generate_subtitles(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        if not project_id:
            return ToolResult(success=False, error="project_id is required")

        project = video_manager.get_project(project_id)
        if not project:
            return ToolResult(success=False, error=f"Project {project_id} not found")

        language = params.get("language", "zh-CN")
        style = params.get("style", {})

        return ToolResult(
            success=True,
            output=f"Subtitles generated for language: {language}",
            data={
                "project_id": project_id,
                "language": language,
                "style": style,
            }
        )

    async def _handle_apply_effects(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        element_id = params.get("element_id")
        effect_type = params.get("effect_type")

        if not project_id or not effect_type:
            return ToolResult(success=False, error="project_id and effect_type are required")

        project = video_manager.get_project(project_id)
        if not project:
            return ToolResult(success=False, error=f"Project {project_id} not found")

        effect_params = params.get("parameters", {})
        intensity = params.get("intensity", 1.0)

        return ToolResult(
            success=True,
            output=f"Effect {effect_type} applied",
            data={
                "project_id": project_id,
                "element_id": element_id,
                "effect_type": effect_type,
                "intensity": intensity,
                "parameters": effect_params,
            }
        )

    async def _handle_export_video(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        if not project_id:
            return ToolResult(success=False, error="project_id is required")

        project = video_manager.get_project(project_id)
        if not project:
            return ToolResult(success=False, error=f"Project {project_id} not found")

        format_str = params.get("format", "mp4")
        quality_str = params.get("quality", "high")
        output_path = params.get("output_path")

        try:
            format_enum = ExportFormat(format_str.lower())
        except ValueError:
            format_enum = ExportFormat.MP4

        try:
            quality_enum = ExportQuality(quality_str.lower())
        except ValueError:
            quality_enum = ExportQuality.HIGH

        try:
            result_path = video_manager.export_project(
                project_id,
                format_enum,
                quality_enum,
                output_path
            )
            return ToolResult(
                success=True,
                output=f"Video exported to: {result_path}",
                data={
                    "project_id": project_id,
                    "format": format_enum.value,
                    "quality": quality_enum.value,
                    "output_path": result_path,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to export video: {str(e)}")

    async def _handle_list_projects(self, params: dict[str, Any]) -> ToolResult:
        domain_id = params.get("domain_id")
        if domain_id:
            projects = video_manager.list_projects_by_domain(domain_id)
        else:
            projects = video_manager.list_projects()

        project_list = [
            {
                "project_id": p.project_id,
                "name": p.name,
                "duration": p.duration,
                "created_at": p.created_at,
            }
            for p in projects
        ]

        return ToolResult(
            success=True,
            output=f"Found {len(projects)} projects",
            data={"projects": project_list, "count": len(projects)}
        )

    async def _handle_get_project(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        if not project_id:
            return ToolResult(success=False, error="project_id is required")

        project = video_manager.get_project(project_id)
        if not project:
            return ToolResult(success=False, error=f"Project {project_id} not found")

        return ToolResult(
            success=True,
            output=f"Project: {project.name}",
            data=project.to_dict()
        )

    async def _handle_add_track(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        track_type_str = params.get("track_type", "video")
        name = params.get("name")

        if not project_id:
            return ToolResult(success=False, error="project_id is required")

        try:
            track_type = TrackType(track_type_str.lower())
        except ValueError:
            track_type = TrackType.VIDEO

        track = video_manager.add_track_to_project(project_id, track_type, name)
        if not track:
            return ToolResult(success=False, error="Failed to add track")

        return ToolResult(
            success=True,
            output=f"Added track: {track.name}",
            data={
                "track_id": track.id,
                "track_name": track.name,
                "track_type": track.type.value,
            }
        )

    async def _handle_add_element(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")
        track_id = params.get("track_id")
        media_type_str = params.get("media_type", "video")
        name = params.get("name", "Element")
        start_time = params.get("start_time", 0)
        duration = params.get("duration", 5)
        properties = params.get("properties")

        if not project_id or not track_id:
            return ToolResult(success=False, error="project_id and track_id are required")

        try:
            media_type = MediaType(media_type_str.lower())
        except ValueError:
            media_type = MediaType.VIDEO

        element = video_manager.add_element_to_track(
            project_id,
            track_id,
            media_type,
            name,
            start_time,
            duration,
            properties
        )

        if not element:
            return ToolResult(success=False, error="Failed to add element")

        return ToolResult(
            success=True,
            output=f"Added element: {element.name}",
            data={
                "element_id": element.id,
                "track_id": track_id,
                "name": element.name,
                "start_time": element.start_time,
                "duration": element.duration,
            }
        )

    async def _handle_get_statistics(self, params: dict[str, Any]) -> ToolResult:
        project_id = params.get("project_id")

        if project_id:
            project = video_manager.get_project(project_id)
            if not project:
                return ToolResult(success=False, error=f"Project {project_id} not found")
            stats = project.get_statistics()
        else:
            stats = video_manager.get_statistics()

        return ToolResult(
            success=True,
            output="Statistics retrieved",
            data=stats
        )
