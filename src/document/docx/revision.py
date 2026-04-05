"""
Word 文档修订跟踪模块

提供修订跟踪功能，包括接受、拒绝修订和查看修订历史。
支持完整的 OOXML 修订规范。

使用示例:
    from src.document.docx.revision import RevisionManager
    
    # 初始化
    manager = RevisionManager('workspace/unpacked')
    
    # 获取所有修订
    revisions = manager.get_all_revisions()
    
    # 接受修订
    manager.accept_revision(revision_id=1)
    
    # 拒绝修订
    manager.reject_revision(revision_id=2)
    
    # 接受所有修订
    manager.accept_all_revisions()
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.document.docx.editor import Document, DocxXMLEditor


class RevisionType(Enum):
    """修订类型枚举"""
    INSERTION = "insertion"
    DELETION = "deletion"
    FORMAT_CHANGE = "format_change"


@dataclass
class Revision:
    """修订数据类"""
    id: int
    revision_type: RevisionType
    author: str
    date: str
    text: str = ""
    position: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "type": self.revision_type.value,
            "author": self.author,
            "date": self.date,
            "text": self.text,
            "position": self.position
        }


class RevisionManager:
    """
    Word 文档修订跟踪管理器。

    提供修订的完整生命周期管理，包括查看、接受和拒绝修订。
    支持 OOXML 修订规范的所有特性。

    属性:
        document: Document 实例
        unpacked_path: 解压后的文档路径
    """

    def __init__(
        self,
        unpacked_dir,
        author: str = "Claude",
        initials: str = "C",
        rsid: str | None = None
    ):
        """
        初始化修订管理器。

        参数:
            unpacked_dir: 解压后的 DOCX 目录路径
            author: 作者名称
            initials: 作者缩写
            rsid: 可选的 RSID
        """
        self.document = Document(
            unpacked_dir,
            author=author,
            initials=initials,
            rsid=rsid,
            track_revisions=True
        )
        self.unpacked_path = Path(unpacked_dir)

    def get_revision(self, revision_id: int) -> Revision | None:
        """
        获取指定 ID 的修订。

        参数:
            revision_id: 修订 ID

        返回:
            Revision 对象，如果不存在则返回 None
        """
        doc_editor = self.document["word/document.xml"]

        for tag, rev_type in [("w:ins", RevisionType.INSERTION), ("w:del", RevisionType.DELETION)]:
            for elem in doc_editor.dom.getElementsByTagName(tag):
                rid = elem.getAttribute("w:id")
                if rid and int(rid) == revision_id:
                    return self._parse_revision_element(elem, rev_type)

        return None

    def get_all_revisions(self) -> list[Revision]:
        """
        获取文档中的所有修订。

        返回:
            Revision 对象列表
        """
        doc_editor = self.document["word/document.xml"]
        revisions = []

        for tag, rev_type in [("w:ins", RevisionType.INSERTION), ("w:del", RevisionType.DELETION)]:
            for elem in doc_editor.dom.getElementsByTagName(tag):
                revision = self._parse_revision_element(elem, rev_type)
                if revision:
                    revisions.append(revision)

        return sorted(revisions, key=lambda r: r.id)

    def get_revisions_by_author(self, author: str) -> list[Revision]:
        """
        获取指定作者的所有修订。

        参数:
            author: 作者名称

        返回:
            该作者的修订列表
        """
        all_revisions = self.get_all_revisions()
        return [r for r in all_revisions if r.author == author]

    def get_revisions_by_type(self, revision_type: RevisionType) -> list[Revision]:
        """
        获取指定类型的所有修订。

        参数:
            revision_type: 修订类型

        返回:
            该类型的修订列表
        """
        all_revisions = self.get_all_revisions()
        return [r for r in all_revisions if r.revision_type == revision_type]

    def accept_revision(self, revision_id: int) -> bool:
        """
        接受修订。

        对于插入：保留插入的内容，移除 w:ins 包装
        对于删除：永久删除内容

        参数:
            revision_id: 修订 ID

        返回:
            是否成功接受
        """
        revision = self.get_revision(revision_id)
        if not revision:
            return False

        doc_editor = self.document["word/document.xml"]

        if revision.revision_type == RevisionType.INSERTION:
            return self._accept_insertion(doc_editor, revision_id)
        if revision.revision_type == RevisionType.DELETION:
            return self._accept_deletion(doc_editor, revision_id)

        return False

    def reject_revision(self, revision_id: int) -> bool:
        """
        拒绝修订。

        对于插入：删除插入的内容
        对于删除：恢复删除的内容

        参数:
            revision_id: 修订 ID

        返回:
            是否成功拒绝
        """
        revision = self.get_revision(revision_id)
        if not revision:
            return False

        doc_editor = self.document["word/document.xml"]

        if revision.revision_type == RevisionType.INSERTION:
            return self._reject_insertion(doc_editor, revision_id)
        if revision.revision_type == RevisionType.DELETION:
            return self._reject_deletion(doc_editor, revision_id)

        return False

    def accept_all_revisions(self) -> int:
        """
        接受所有修订。

        返回:
            成功接受的修订数量
        """
        revisions = self.get_all_revisions()
        accepted_count = 0

        for revision in reversed(revisions):
            if self.accept_revision(revision.id):
                accepted_count += 1

        return accepted_count

    def reject_all_revisions(self) -> int:
        """
        拒绝所有修订。

        返回:
            成功拒绝的修订数量
        """
        revisions = self.get_all_revisions()
        rejected_count = 0

        for revision in reversed(revisions):
            if self.reject_revision(revision.id):
                rejected_count += 1

        return rejected_count

    def get_revision_count(self) -> int:
        """
        获取修订总数。

        返回:
            修订数量
        """
        return len(self.get_all_revisions())

    def has_revisions(self) -> bool:
        """
        检查文档是否有修订。

        返回:
            是否有修订
        """
        return self.get_revision_count() > 0

    def suggest_deletion(self, elem) -> bool:
        """
        建议删除指定元素。

        参数:
            elem: 要删除的 DOM 元素 (w:r 或 w:p)

        返回:
            是否成功标记删除
        """
        doc_editor = self.document["word/document.xml"]
        try:
            doc_editor.suggest_deletion(elem)
            return True
        except ValueError:
            return False

    def suggest_insertion(self, xml_content: str, position_elem, after: bool = True) -> bool:
        """
        建议插入内容。

        参数:
            xml_content: 要插入的 XML 内容
            position_elem: 定位元素
            after: 是否在定位元素之后插入

        返回:
            是否成功标记插入
        """
        doc_editor = self.document["word/document.xml"]
        try:
            wrapped_content = f"<w:ins>{xml_content}</w:ins>"
            if after:
                doc_editor.insert_after(position_elem, wrapped_content)
            else:
                doc_editor.insert_before(position_elem, wrapped_content)
            return True
        except Exception:
            return False

    def save(self, destination: str | None = None, validate: bool = True) -> None:
        """
        保存更改。

        参数:
            destination: 可选的目标路径
            validate: 是否验证文档
        """
        self.document.save(destination=destination, validate=validate)

    def _parse_revision_element(self, elem, rev_type: RevisionType) -> Revision | None:
        """解析修订元素为 Revision 对象"""
        revision_id = elem.getAttribute("w:id")
        if not revision_id:
            return None

        author = elem.getAttribute("w:author")
        date = elem.getAttribute("w:date")

        text_parts = []
        text_tag = "w:delText" if rev_type == RevisionType.DELETION else "w:t"
        for t_elem in elem.getElementsByTagName(text_tag):
            if t_elem.firstChild:
                text_parts.append(t_elem.firstChild.data)
        text = "".join(text_parts)

        return Revision(
            id=int(revision_id),
            revision_type=rev_type,
            author=author,
            date=date,
            text=text
        )

    def _accept_insertion(self, doc_editor: DocxXMLEditor, revision_id: int) -> bool:
        """接受插入修订"""
        for elem in doc_editor.dom.getElementsByTagName("w:ins"):
            if elem.getAttribute("w:id") == str(revision_id):
                parent = elem.parentNode
                while elem.firstChild:
                    child = elem.firstChild
                    elem.removeChild(child)
                    parent.insertBefore(child, elem)
                parent.removeChild(elem)
                return True
        return False

    def _accept_deletion(self, doc_editor: DocxXMLEditor, revision_id: int) -> bool:
        """接受删除修订"""
        for elem in doc_editor.dom.getElementsByTagName("w:del"):
            if elem.getAttribute("w:id") == str(revision_id):
                parent = elem.parentNode
                parent.removeChild(elem)
                return True
        return False

    def _reject_insertion(self, doc_editor: DocxXMLEditor, revision_id: int) -> bool:
        """拒绝插入修订（删除插入的内容）"""
        for elem in doc_editor.dom.getElementsByTagName("w:ins"):
            if elem.getAttribute("w:id") == str(revision_id):
                parent = elem.parentNode
                parent.removeChild(elem)
                return True
        return False

    def _reject_deletion(self, doc_editor: DocxXMLEditor, revision_id: int) -> bool:
        """拒绝删除修订（恢复删除的内容）"""
        for elem in doc_editor.dom.getElementsByTagName("w:del"):
            if elem.getAttribute("w:id") == str(revision_id):
                doc_editor.revert_deletion(elem)
                return True
        return False
