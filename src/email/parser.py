"""
PyAgent 邮件模块 - 邮件解析器
"""

import re
from email.message import Message
from typing import Any

from .client import Email, Attachment


class EmailParser:
    """邮件解析器"""

    @staticmethod
    def parse_email(raw_email: bytes) -> Email | None:
        import email
        from email.policy import default
        from email.utils import parseaddr, parsedate_to_datetime

        try:
            msg = email.message_from_bytes(raw_email, policy=default)

            from_addr = msg.get("From", "")
            _, from_email = parseaddr(from_addr)

            to_addrs = []
            to_header = msg.get("To", "")
            if to_header:
                for addr in to_header.split(","):
                    _, email_addr = parseaddr(addr.strip())
                    if email_addr:
                        to_addrs.append(email_addr)

            cc_addrs = []
            cc_header = msg.get("Cc", "")
            if cc_header:
                for addr in cc_header.split(","):
                    _, email_addr = parseaddr(addr.strip())
                    if email_addr:
                        cc_addrs.append(email_addr)

            body_text = ""
            body_html = ""
            attachments: list[Attachment] = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    if "attachment" in content_disposition:
                        filename = part.get_filename() or "unknown"
                        data = part.get_payload(decode=True)
                        attachments.append(Attachment(
                            filename=filename,
                            content_type=content_type,
                            size=len(data) if data else 0,
                            data=data,
                        ))
                    elif content_type == "text/plain" and not body_text:
                        payload = part.get_payload(decode=True)
                        body_text = payload.decode("utf-8", errors="ignore") if payload else ""
                    elif content_type == "text/html" and not body_html:
                        payload = part.get_payload(decode=True)
                        body_html = payload.decode("utf-8", errors="ignore") if payload else ""
            else:
                payload = msg.get_payload(decode=True)
                body_text = payload.decode("utf-8", errors="ignore") if payload else ""

            date_str = msg.get("Date", "")
            try:
                received_at = parsedate_to_datetime(date_str) if date_str else None
            except Exception:
                received_at = None

            return Email(
                message_id=msg.get("Message-ID", ""),
                from_address=from_email or from_addr,
                to_addresses=to_addrs,
                cc_addresses=cc_addrs,
                subject=msg.get("Subject", ""),
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
                received_at=received_at,
            )
        except Exception:
            return None

    @staticmethod
    def extract_attachments(email_obj: Email) -> list[Attachment]:
        return email_obj.attachments

    @staticmethod
    def extract_links(text: str) -> list[str]:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

    @staticmethod
    def extract_addresses(text: str) -> list[str]:
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return list(set(re.findall(email_pattern, text)))

    @staticmethod
    def extract_phone_numbers(text: str) -> list[str]:
        phone_pattern = r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        return re.findall(phone_pattern, text)
