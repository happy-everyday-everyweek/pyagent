"""
PyAgent 文档编辑器模块测试

测试文档管理器和工具的基本功能。
"""

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.document.types import DocumentType, DocumentStatus
from src.document.metadata import DocumentMetadata
from src.document.manager import DocumentManager
from src.document.connector import OnlyOfficeConnector, OnlyOfficeConfig
from src.document.tools import DocumentTool
from src.tools.base import ToolContext


def test_types():
    print("Testing types...")
    assert DocumentType.WORD.value == "word"
    assert DocumentType.EXCEL.value == "excel"
    assert DocumentType.PPT.value == "ppt"
    assert DocumentStatus.DRAFT.value == "draft"
    assert DocumentStatus.EDITING.value == "editing"
    assert DocumentStatus.SAVED.value == "saved"
    assert DocumentStatus.EXPORTED.value == "exported"
    print("  Types test passed!")


def test_metadata():
    print("Testing metadata...")
    metadata = DocumentMetadata(
        document_id="test_doc_001",
        document_type=DocumentType.WORD,
        name="Test Document",
    )
    assert metadata.document_id == "test_doc_001"
    assert metadata.document_type == DocumentType.WORD
    assert metadata.name == "Test Document"
    assert metadata.status == DocumentStatus.DRAFT
    assert metadata.version == 1

    doc_dict = metadata.to_dict()
    assert doc_dict["document_id"] == "test_doc_001"
    assert doc_dict["document_type"] == "word"

    restored = DocumentMetadata.from_dict(doc_dict)
    assert restored.document_id == metadata.document_id
    assert restored.document_type == metadata.document_type
    print("  Metadata test passed!")


def test_manager():
    print("Testing manager...")
    with tempfile.TemporaryDirectory() as tmpdir:
        DocumentManager.reset_instance()
        manager = DocumentManager(data_dir=tmpdir)

        doc = manager.create_document(
            document_type=DocumentType.WORD,
            name="Test Word Document",
            author="Test Author",
            tags=["test", "document"],
        )
        assert doc.document_id is not None
        assert doc.name == "Test Word Document"
        assert doc.author == "Test Author"
        assert "test" in doc.tags

        retrieved = manager.get_document(doc.document_id)
        assert retrieved is not None
        assert retrieved.document_id == doc.document_id

        docs = manager.list_documents()
        assert len(docs) == 1

        stats = manager.get_statistics()
        assert stats["total"] == 1
        assert stats["by_type"]["word"] == 1

        success = manager.delete_document(doc.document_id)
        assert success

        docs = manager.list_documents()
        assert len(docs) == 0

    DocumentManager.reset_instance()
    print("  Manager test passed!")


def test_connector():
    print("Testing connector...")
    config = OnlyOfficeConfig(
        server_url="http://localhost:8080",
        secret_key="test_secret",
        jwt_enabled=True,
    )
    connector = OnlyOfficeConnector(config)

    key = connector._generate_document_key("doc_001", 1)
    assert len(key) == 32

    callback_result = connector.process_callback({
        "key": "test_key",
        "status": 2,
        "url": "http://example.com/document.docx",
    })
    assert callback_result["error"] == 0
    assert callback_result["saved"] is True

    print("  Connector test passed!")


async def test_tool():
    print("Testing tool...")
    with tempfile.TemporaryDirectory() as tmpdir:
        DocumentManager.reset_instance()
        manager = DocumentManager(data_dir=tmpdir)

        tool = DocumentTool(device_id="test_device")

        context = ToolContext(
            device_id="test_device",
            session_id="test_session",
            user_id="test_user",
        )

        activated = await tool.activate(context)
        assert activated

        result = await tool.call(
            context=context,
            action="create_document",
            document_type="word",
            name="Test Document via Tool",
            author="Tool Test",
        )
        if not result.success:
            print(f"Error: {result.error}")
        assert result.success
        assert result.data is not None
        assert "document_id" in result.data

        doc_id = result.data["document_id"]

        result = await tool.call(
            context=context,
            action="get_document",
            document_id=doc_id,
        )
        assert result.success
        assert result.data["metadata"]["name"] == "Test Document via Tool"

        result = await tool.call(
            context=context,
            action="list_documents",
        )
        assert result.success
        assert result.data["count"] == 1

        result = await tool.call(
            context=context,
            action="delete_document",
            document_id=doc_id,
        )
        assert result.success

        dormant = await tool.dormant(context)
        assert dormant

    DocumentManager.reset_instance()
    print("  Tool test passed!")


def main():
    print("=" * 50)
    print("Running Document Module Tests")
    print("=" * 50)

    test_types()
    test_metadata()
    test_manager()
    test_connector()
    asyncio.run(test_tool())

    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
