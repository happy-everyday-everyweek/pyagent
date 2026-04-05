"""
PyAgent 邮件客户端测试
"""

import pytest
from datetime import datetime

from src.email.client import Attachment, Email, EmailClient


class TestAttachment:
    """测试附件"""

    def test_attachment_creation(self):
        attachment = Attachment(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024
        )
        assert attachment.filename == "test.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.size == 1024

    def test_attachment_to_dict(self):
        attachment = Attachment(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            data=b"test data"
        )
        data = attachment.to_dict()
        assert data["filename"] == "test.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["size"] == 1024


class TestEmail:
    """测试邮件"""

    def test_email_creation(self):
        email = Email(
            message_id="<test@example.com>",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="Test body"
        )
        assert email.message_id == "<test@example.com>"
        assert email.from_address == "sender@example.com"
        assert email.subject == "Test Subject"

    def test_email_to_dict(self):
        email = Email(
            message_id="<test@example.com>",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="Test body",
            body_html="<p>Test body</p>"
        )
        data = email.to_dict()
        assert data["message_id"] == "<test@example.com>"
        assert data["from_address"] == "sender@example.com"
        assert data["subject"] == "Test Subject"
        assert data["body_text"] == "Test body"
        assert data["body_html"] == "<p>Test body</p>"

    def test_email_with_attachments(self):
        attachment = Attachment(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024
        )
        email = Email(
            message_id="<test@example.com>",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body_text="Test body",
            attachments=[attachment]
        )
        assert len(email.attachments) == 1


class TestEmailClient:
    """测试邮件客户端"""

    def test_client_creation(self):
        client = EmailClient(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="password",
            imap_host="imap.example.com",
            imap_port=993,
            imap_user="user@example.com",
            imap_password="password"
        )
        assert client.smtp_host == "smtp.example.com"
        assert client.smtp_port == 587
        assert client.imap_host == "imap.example.com"

    def test_client_default_values(self):
        client = EmailClient()
        assert client.smtp_port == 587
        assert client.imap_port == 993

    def test_disconnect(self):
        client = EmailClient()
        client.disconnect()
        assert client._smtp_conn is None
        assert client._imap_conn is None

    def test_send_email_without_connection(self):
        client = EmailClient()
        success, message = client.send_email(
            to="recipient@example.com",
            subject="Test",
            body="Test body"
        )
        assert success is False
        assert "connection failed" in message.lower()

    def test_get_emails_without_connection(self):
        client = EmailClient()
        emails = client.get_emails()
        assert emails == []

    def test_delete_email_without_connection(self):
        client = EmailClient()
        result = client.delete_email("1")
        assert result is False

    def test_move_email_without_connection(self):
        client = EmailClient()
        result = client.move_email("1", "Archive")
        assert result is False

    def test_search_emails_without_connection(self):
        client = EmailClient()
        emails = client.search_emails("test")
        assert emails == []


class TestEmailClientIntegration:
    """邮件客户端集成测试（模拟测试）"""

    @pytest.mark.asyncio
    async def test_client_lifecycle(self):
        client = EmailClient(
            smtp_host="smtp.example.com",
            imap_host="imap.example.com"
        )

        client.disconnect()

        assert client._smtp_conn is None
        assert client._imap_conn is None
