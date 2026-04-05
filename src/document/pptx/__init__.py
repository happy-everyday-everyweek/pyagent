"""
PyAgent PPTX 文档处理模块

提供 PowerPoint 演示文稿的创建、编辑和管理功能。
支持 OOXML 标准的完整操作。

主要功能:
- 演示文稿创建: 从模板或空白创建演示文稿
- 幻灯片管理: 添加、删除、重排幻灯片
- 内容编辑: 修改文本、形状、图片等
- 缩略图生成: 生成幻灯片预览图
"""

from src.document.pptx.creator import PptxCreator
from src.document.pptx.editor import PptxEditor
from src.document.pptx.slide import SlideManager
from src.document.pptx.thumbnail import ThumbnailGenerator

__all__ = [
    "PptxCreator",
    "PptxEditor",
    "SlideManager",
    "ThumbnailGenerator",
]
