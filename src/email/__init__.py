"""
PyAgent 邮件模块

提供邮件收发和管理功能。
"""

from .client import Email, EmailClient, Attachment
from .parser import EmailParser
from .templates import EmailTemplate, TemplateManager
from .ai_assistant import AIEmailAssistant, EmailCategory, EmailUrgency, ActionItem

__all__ = [
    "Email",
    "EmailClient",
    "Attachment",
    "EmailParser",
    "EmailTemplate",
    "TemplateManager",
    "AIEmailAssistant",
    "EmailCategory",
    "EmailUrgency",
    "ActionItem",
]
