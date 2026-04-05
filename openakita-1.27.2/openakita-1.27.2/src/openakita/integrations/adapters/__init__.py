"""API 适配器子包。"""

from openakita.integrations import BaseAPIAdapter, APIError, AuthenticationError, RateLimitError

__all__ = ["BaseAPIAdapter", "APIError", "AuthenticationError", "RateLimitError"]
