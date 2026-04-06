"""
PyAgent 移动端模块 - 验证码提取器
移植自 OpenKiwi VerificationCodeExtractor
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class VerificationCodeType(Enum):
    """验证码类型"""
    SMS = "sms"
    EMAIL = "email"
    APP = "app"
    UNKNOWN = "unknown"


@dataclass
class VerificationCode:
    """验证码数据结构"""
    code: str
    code_type: VerificationCodeType
    source: str
    source_number: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    expires_in: int | None = None
    raw_text: str = ""
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "code_type": self.code_type.value,
            "source": self.source,
            "source_number": self.source_number,
            "timestamp": self.timestamp.isoformat(),
            "expires_in": self.expires_in,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
        }


class VerificationCodeExtractor:
    """验证码提取器

    从通知文本中提取验证码，支持多种格式。
    移植自 OpenKiwi 的 VerificationCodeExtractor。
    """

    CODE_PATTERNS = [
        re.compile(r"(?:验证码|校验码|确认码|动态码|安全码|验证码是|校验码为)[:：]?\s*(\d{4,8})", re.IGNORECASE),
        re.compile(r"(?:code|Code|CODE|verification|Verification)[:：]?\s*(\d{4,8})"),
        re.compile(r"【[^】]+】.*?(\d{4,8}).*?(?:验证码|校验码)", re.IGNORECASE),
        re.compile(r"(\d{4,8}).*?(?:是您的|为您的|验证码|校验码|确认码)", re.IGNORECASE),
        re.compile(r"(?:您的|你的).*?验证码.*?(\d{4,8})", re.IGNORECASE),
        re.compile(r"(\d{6})\s*(?:是|为).*?验证码", re.IGNORECASE),
        re.compile(r"验证码.*?(\d{4,8})", re.IGNORECASE),
        re.compile(r"(\d{4,8})\s*$"),
    ]

    EXPIRY_PATTERNS = [
        re.compile(r"(\d+)\s*(?:分钟|min|分钟内)内有效"),
        re.compile(r"有效期(\d+)分钟"),
        re.compile(r"(\d+)\s*(?:秒|秒内)内有效"),
    ]

    SOURCE_PATTERNS = [
        (re.compile(r"【([^】]+)】"), 1),
        (re.compile(r"(\+?\d{11,15})"), 0),
        (re.compile(r"([\w\-]+@[\w\-]+\.[\w\-]+)"), 0),
    ]

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def extract(self, text: str, package_name: str = "") -> VerificationCode | None:
        """从文本中提取验证码

        Args:
            text: 通知文本
            package_name: 应用包名

        Returns:
            VerificationCode 或 None
        """
        if not text:
            return None

        code = self._extract_code(text)
        if not code:
            return None

        code_type = self._detect_code_type(package_name)
        source = self._extract_source(text)
        source_number = self._extract_source_number(text)
        expires_in = self._extract_expiry(text)

        return VerificationCode(
            code=code,
            code_type=code_type,
            source=source,
            source_number=source_number,
            expires_in=expires_in,
            raw_text=text,
            confidence=self._calculate_confidence(text, code),
        )

    def _extract_code(self, text: str) -> str | None:
        """提取验证码"""
        for pattern in self.CODE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return None

    def _detect_code_type(self, package_name: str) -> VerificationCodeType:
        """检测验证码类型"""
        if not package_name:
            return VerificationCodeType.UNKNOWN

        package_lower = package_name.lower()

        if any(app in package_lower for app in ["sms", "mms", "message", "android.mms"]):
            return VerificationCodeType.SMS

        if any(app in package_lower for app in ["email", "mail", "gmail"]):
            return VerificationCodeType.EMAIL

        if any(app in package_lower for app in ["alipay", "wechat", "taobao", "jd", "bank"]):
            return VerificationCodeType.APP

        return VerificationCodeType.UNKNOWN

    def _extract_source(self, text: str) -> str:
        """提取来源"""
        for pattern, group in self.SOURCE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(group)
        return "Unknown"

    def _extract_source_number(self, text: str) -> str | None:
        """提取来源号码"""
        phone_pattern = re.compile(r"(?:\+86)?1[3-9]\d{9}")
        match = phone_pattern.search(text)
        if match:
            return match.group()

        short_number_pattern = re.compile(r"1\d{4,5}")
        match = short_number_pattern.search(text)
        if match:
            return match.group()

        return None

    def _extract_expiry(self, text: str) -> int | None:
        """提取有效期（秒）"""
        for pattern in self.EXPIRY_PATTERNS:
            match = pattern.search(text)
            if match:
                value = int(match.group(1))
                if "分钟" in text or "min" in text.lower():
                    return value * 60
                return value
        return None

    def _calculate_confidence(self, text: str, code: str) -> float:
        """计算置信度"""
        confidence = 0.5

        if any(kw in text for kw in ["验证码", "校验码", "确认码", "code", "Code"]):
            confidence += 0.3

        if len(code) == 6:
            confidence += 0.1
        elif len(code) == 4:
            confidence += 0.05

        if any(kw in text for kw in ["有效", "分钟", "expire"]):
            confidence += 0.1

        return min(confidence, 1.0)


verification_code_extractor = VerificationCodeExtractor()
