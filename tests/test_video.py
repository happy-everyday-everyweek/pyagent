"""
PyAgent 视频编辑器模块测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.video import (
    MediaType,
    TrackType,
    TimelineElement,
    Track,
    ExportFormat,
    ExportQuality,
    MediaFile,
    SubtitleStyle,
    EffectType,
    Effect,
    VideoProject,
    VideoManager,
    video_manager,
    EditorCore,
    VideoTool,
)
from src.tools.base import ToolContext
import asyncio


def test_types():
    print("Testing types...")
    element = TimelineElement(
        id="test-element-1",
        track_id="track-1",
        media_type=MediaType.VIDEO,
        name="Test Video",
        start_time=0,
        duration=10,
    )
    assert element.get_end_time() == 10
    assert element.media_type == MediaType.VIDEO
    
    track = Track(
        id="track-1",
        type=TrackType.VIDEO,
        name="Video Track",
        elements=[element],
    )
    assert track.get_duration() == 10
    assert track.type == TrackType.VIDEO
    
    effect = Effect(
        id="effect-1",
        type=EffectType.FILTER,
        name="Blur",
        duration=5,
    )
    assert effect.type == EffectType.FILTER
    
    print("  Types test passed!")


def test_project():
    print("Testing project...")
    project = VideoProject(
        project_id="test-project-1",
        name="Test Project",
        canvas_width=1920,
        canvas_height=1080,
        fps=30,
    )
    
    track = Track(
        id="track-1",
        type=TrackType.VIDEO,
        name="Video Track",
    )
    project.add_track(track)
    
    assert len(project.tracks) == 1
    assert project.get_track("track-1") is not None
    
    media = MediaFile(
        id="media-1",
        name="test.mp4",
        path="/path/to/test.mp4",
        media_type=MediaType.VIDEO,
    )
    project.add_media(media)
    
    assert len(project.media_files) == 1
    assert project.get_media("media-1") is not None
    
    valid, errors = project.validate()
    assert valid
    
    stats = project.get_statistics()
    assert stats["name"] == "Test Project"
    assert stats["total_tracks"] == 1
    
    print("  Project test passed!")


def test_manager():
    print("Testing manager...")
    manager = VideoManager()
    
    project = manager.create_project(
        name="Manager Test Project",
        width=1280,
        height=720,
        fps=24,
    )
    
    assert project.project_id is not None
    assert project.name == "Manager Test Project"
    assert project.canvas_width == 1280
    assert project.canvas_height == 720
    assert project.fps == 24
    
    retrieved = manager.get_project(project.project_id)
    assert retrieved is not None
    assert retrieved.project_id == project.project_id
    
    projects = manager.list_projects()
    assert len(projects) >= 1
    
    stats = manager.get_statistics()
    assert stats["total_projects"] >= 1
    
    manager.delete_project(project.project_id)
    assert manager.get_project(project.project_id) is None
    
    print("  Manager test passed!")


def test_editor_core():
    print("Testing editor core...")
    editor = EditorCore.create("Editor Test Project")
    
    assert editor.project is not None
    assert editor.project.name == "Editor Test Project"
    
    assert editor.timeline is not None
    assert editor.media is not None
    assert editor.playback is not None
    assert editor.renderer is not None
    
    editor.playback.play()
    assert editor.playback.get_state().is_playing
    
    editor.playback.pause()
    assert not editor.playback.get_state().is_playing
    
    element = TimelineElement(
        id="elem-1",
        track_id=editor.project.tracks[0].id,
        media_type=MediaType.VIDEO,
        name="Test Element",
        start_time=0,
        duration=10,
    )
    editor.project.tracks[0].elements.append(element)
    editor.project.calculate_duration()
    
    editor.playback.seek(5.0)
    assert editor.playback.get_state().current_time == 5.0
    
    settings = editor.renderer.get_render_settings(ExportQuality.HIGH)
    assert settings["video_bitrate"] == "5M"
    
    stats = editor.get_statistics()
    assert stats["name"] == "Editor Test Project"
    
    video_manager.delete_project(editor.project.project_id)
    
    print("  Editor core test passed!")


async def test_video_tool():
    print("Testing video tool...")
    tool = VideoTool(device_id="test-device")
    context = ToolContext(device_id="test-device", session_id="test-session")
    
    result = await tool.activate(context)
    assert result
    
    result = await tool.call(context, action="create_project", name="Tool Test Project")
    if not result.success:
        print(f"  Error: {result.error}")
    assert result.success
    project_id = result.data["project_id"]
    
    result = await tool.call(context, action="list_projects")
    assert result.success
    assert result.data["count"] >= 1
    
    result = await tool.call(context, action="get_project", project_id=project_id)
    assert result.success
    assert result.data["project_id"] == project_id
    
    result = await tool.call(context, action="add_track", project_id=project_id, track_type="audio")
    assert result.success
    
    result = await tool.call(context, action="get_statistics", project_id=project_id)
    assert result.success
    
    result = await tool.call(context, action="export_video", project_id=project_id)
    assert result.success
    
    result = await tool.dormant(context)
    assert result
    
    video_manager.delete_project(project_id)
    
    print("  Video tool test passed!")


def main():
    print("=" * 50)
    print("Running Video Module Tests")
    print("=" * 50)
    
    test_types()
    test_project()
    test_manager()
    test_editor_core()
    asyncio.run(test_video_tool())
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
