"""
PyAgent 邮件模块

提供邮件收发和管理功能。
"""

from .ai_assistant import ActionItem, AIEmailAssistant, EmailCategory, EmailUrgency
from .client import Attachment, Email, EmailClient
from .parser import EmailParser
from .templates import EmailTemplate, TemplateManager

__all__ = [
    "AIEmailAssistant",
    "ActionItem",
    "Attachment",
    "Email",
    "EmailCategory",
    "EmailClient",
    "EmailParser",
    "EmailTemplate",
    "EmailUrgency",
    "TemplateManager",
]
