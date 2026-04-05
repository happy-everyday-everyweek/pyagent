"""
PyAgent 邮件模块 - 邮件客户端

提供SMTP/IMAP邮件收发功能。
"""

import email
import imaplib
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import policy
from email.utils import parseaddr
from typing import Any


@dataclass
class Attachment:
    filename: str
    content_type: str
    size: int
    data: bytes | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
        }


@dataclass
class Email:
    message_id: str
    from_address: str
    to_addresses: list[str]
    subject: str
    body_text: str
    body_html: str = ""
    cc_addresses: list[str] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)
    received_at: datetime | None = None
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "from_address": self.from_address,
            "to_addresses": self.to_addresses,
            "cc_addresses": self.cc_addresses,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "attachments": [a.to_dict() for a in self.attachments],
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "flags": self.flags,
        }


class EmailClient:
    """邮件客户端"""

    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        imap_host: str = "",
        imap_port: int = 993,
        imap_user: str = "",
        imap_password: str = "",
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_user = imap_user
        self.imap_password = imap_password

        self._smtp_conn: smtplib.SMTP | None = None
        self._imap_conn: imaplib.IMAP4_SSL | None = None

    def connect_smtp(self) -> bool:
        try:
            self._smtp_conn = smtplib.SMTP(self.smtp_host, self.smtp_port)
            self._smtp_conn.starttls()
            self._smtp_conn.login(self.smtp_user, self.smtp_password)
            return True
        except Exception:
            return False

    def connect_imap(self) -> bool:
        try:
            self._imap_conn = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            self._imap_conn.login(self.imap_user, self.imap_password)
            return True
        except Exception:
            return False

    def disconnect(self) -> None:
        if self._smtp_conn:
            try:
                self._smtp_conn.quit()
            except Exception:
                pass
            self._smtp_conn = None

        if self._imap_conn:
            try:
                self._imap_conn.logout()
            except Exception:
                pass
            self._imap_conn = None

    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        body_html: str | None = None,
        cc: str | list[str] | None = None,
        attachments: list[str] | None = None,
    ) -> tuple[bool, str]:
        if not self._smtp_conn:
            if not self.connect_smtp():
                return False, "SMTP connection failed"

        to_list = [to] if isinstance(to, str) else to
        cc_list = [cc] if isinstance(cc, str) else (cc or [])

        msg = MIMEMultipart("alternative") if body_html else MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = subject

        if cc_list:
            msg["Cc"] = ", ".join(cc_list)

        msg.attach(MIMEText(body, "plain"))

        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        from email import encoders
                        encoders.encode_base64(part)
                        import os
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={os.path.basename(file_path)}",
                        )
                        msg.attach(part)
                except Exception:
                    pass

        try:
            recipients = to_list + cc_list
            self._smtp_conn.sendmail(self.smtp_user, recipients, msg.as_string())
            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)

    def get_emails(self, folder: str = "INBOX", limit: int = 20) -> list[Email]:
        if not self._imap_conn:
            if not self.connect_imap():
                return []

        try:
            self._imap_conn.select(folder)
            status, messages = self._imap_conn.search(None, "ALL")
            if status != "OK":
                return []

            email_ids = messages[0].split()
            emails: list[Email] = []

            for email_id in reversed(email_ids[-limit:]):
                status, msg_data = self._imap_conn.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                parsed = self._parse_email(raw_email)
                if parsed:
                    emails.append(parsed)

            return emails
        except Exception:
            return []

    def _parse_email(self, raw_email: bytes) -> Email | None:
        try:
            msg = email.message_from_bytes(raw_email, policy=policy.default)

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
                from email.utils import parsedate_to_datetime
                received_at = parsedate_to_datetime(date_str) if date_str else None
            except Exception:
                received_at = None

            flags: list[str] = []
            if "Seen" in str(msg.get("Flags", "")):
                flags.append("read")
            if "Answered" in str(msg.get("Flags", "")):
                flags.append("replied")
            if "Flagged" in str(msg.get("Flags", "")):
                flags.append("starred")

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
                flags=flags,
            )
        except Exception:
            return None

    def delete_email(self, message_id: str, folder: str = "INBOX") -> bool:
        if not self._imap_conn:
            if not self.connect_imap():
                return False

        try:
            self._imap_conn.select(folder)
            self._imap_conn.store(message_id, "+FLAGS", "\\Deleted")
            self._imap_conn.expunge()
            return True
        except Exception:
            return False

    def move_email(self, message_id: str, dest_folder: str, src_folder: str = "INBOX") -> bool:
        if not self._imap_conn:
            if not self.connect_imap():
                return False

        try:
            self._imap_conn.select(src_folder)
            self._imap_conn.copy(message_id, dest_folder)
            self._imap_conn.store(message_id, "+FLAGS", "\\Deleted")
            self._imap_conn.expunge()
            return True
        except Exception:
            return False

    def search_emails(self, query: str, folder: str = "INBOX") -> list[Email]:
        if not self._imap_conn:
            if not self.connect_imap():
                return []

        try:
            self._imap_conn.select(folder)
            status, messages = self._imap_conn.search(None, f'SUBJECT "{query}"')
            if status != "OK":
                return []

            email_ids = messages[0].split()
            emails: list[Email] = []

            for email_id in email_ids:
                status, msg_data = self._imap_conn.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                parsed = self._parse_email(raw_email)
                if parsed:
                    emails.append(parsed)

            return emails
        except Exception:
            return []


email_client = EmailClient()
