"""
Word 文档批注管理模块

提供批注的添加、回复、删除和查询功能。
支持完整的 OOXML 批注规范。

使用示例:
    from src.document.docx.comment import CommentManager
    
    # 初始化
    manager = CommentManager('workspace/unpacked')
    
    # 添加批注
    comment_id = manager.add_comment(
        start_node, 
        end_node, 
        "这是批注内容"
    )
    
    # 回复批注
    reply_id = manager.reply_to_comment(
        parent_id=comment_id,
        text="这是回复内容"
    )
    
    # 获取所有批注
    comments = manager.get_all_comments()
    
    # 删除批注
    manager.delete_comment(comment_id)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.document.docx.editor import Document


@dataclass
class Comment:
    """批注数据类"""
    id: int
    text: str
    author: str
    initials: str
    date: str
    para_id: str
    parent_id: int | None = None
    replies: list["Comment"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "text": self.text,
            "author": self.author,
            "initials": self.initials,
            "date": self.date,
            "para_id": self.para_id,
            "parent_id": self.parent_id,
            "replies": [r.to_dict() for r in self.replies]
        }


class CommentManager:
    """
    Word 文档批注管理器。

    提供批注的完整生命周期管理，包括添加、回复、删除和查询。
    支持 OOXML 批注规范的所有特性。

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
        初始化批注管理器。

        参数:
            unpacked_dir: 解压后的 DOCX 目录路径
            author: 批注作者名称
            initials: 作者缩写
            rsid: 可选的 RSID
        """
        self.document = Document(
            unpacked_dir,
            author=author,
            initials=initials,
            rsid=rsid
        )
        self.unpacked_path = Path(unpacked_dir)

    def add_comment(
        self,
        start_node,
        end_node,
        text: str
    ) -> int:
        """
        添加批注。

        参数:
            start_node: 批注起始节点
            end_node: 批注结束节点
            text: 批注文本内容

        返回:
            新创建的批注 ID
        """
        return self.document.add_comment(
            start=start_node,
            end=end_node,
            text=text
        )

    def reply_to_comment(
        self,
        parent_id: int,
        text: str
    ) -> int:
        """
        回复现有批注。

        参数:
            parent_id: 父批注 ID
            text: 回复文本

        返回:
            新创建的回复批注 ID

        异常:
            ValueError: 如果父批注不存在
        """
        return self.document.reply_to_comment(
            parent_comment_id=parent_id,
            text=text
        )

    def get_comment(self, comment_id: int) -> Comment | None:
        """
        获取指定 ID 的批注。

        参数:
            comment_id: 批注 ID

        返回:
            Comment 对象，如果不存在则返回 None
        """
        comments_path = self.document.word_path / "comments.xml"
        if not comments_path.exists():
            return None

        editor = self.document["word/comments.xml"]

        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            cid = comment_elem.getAttribute("w:id")
            if cid and int(cid) == comment_id:
                return self._parse_comment_element(comment_elem)

        return None

    def get_all_comments(self) -> list[Comment]:
        """
        获取文档中的所有批注。

        返回:
            Comment 对象列表
        """
        comments_path = self.document.word_path / "comments.xml"
        if not comments_path.exists():
            return []

        editor = self.document["word/comments.xml"]
        comments = []

        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            comment = self._parse_comment_element(comment_elem)
            if comment:
                comments.append(comment)

        return comments

    def get_comment_thread(self, comment_id: int) -> list[Comment]:
        """
        获取批注线程（包含所有回复）。

        参数:
            comment_id: 根批注 ID

        返回:
            批注线程列表，第一个是根批注，后面是回复
        """
        root_comment = self.get_comment(comment_id)
        if not root_comment:
            return []

        thread = [root_comment]

        all_comments = self.get_all_comments()
        for comment in all_comments:
            if comment.parent_id == comment_id:
                root_comment.replies.append(comment)

        return thread

    def delete_comment(self, comment_id: int) -> bool:
        """
        删除批注。

        注意：此操作会同时删除该批注的所有回复。

        参数:
            comment_id: 要删除的批注 ID

        返回:
            是否成功删除
        """
        comments_path = self.document.word_path / "comments.xml"
        if not comments_path.exists():
            return False

        editor = self.document["word/comments.xml"]

        comment_elem = None
        for elem in editor.dom.getElementsByTagName("w:comment"):
            cid = elem.getAttribute("w:id")
            if cid and int(cid) == comment_id:
                comment_elem = elem
                break

        if not comment_elem:
            return False

        parent = comment_elem.parentNode
        parent.removeChild(comment_elem)

        self._remove_comment_ranges(comment_id)

        return True

    def update_comment(
        self,
        comment_id: int,
        new_text: str
    ) -> bool:
        """
        更新批注内容。

        参数:
            comment_id: 批注 ID
            new_text: 新的批注文本

        返回:
            是否成功更新
        """
        comments_path = self.document.word_path / "comments.xml"
        if not comments_path.exists():
            return False

        editor = self.document["word/comments.xml"]

        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            cid = comment_elem.getAttribute("w:id")
            if cid and int(cid) == comment_id:
                t_elems = comment_elem.getElementsByTagName("w:t")
                if t_elems:
                    t_elem = t_elems[0]
                    while t_elem.firstChild:
                        t_elem.removeChild(t_elem.firstChild)
                    t_elem.appendChild(
                        editor.dom.createTextNode(new_text)
                    )
                    return True

        return False

    def get_comments_by_author(self, author: str) -> list[Comment]:
        """
        获取指定作者的所有批注。

        参数:
            author: 作者名称

        返回:
            该作者的批注列表
        """
        all_comments = self.get_all_comments()
        return [c for c in all_comments if c.author == author]

    def get_comment_count(self) -> int:
        """
        获取批注总数。

        返回:
            批注数量
        """
        return len(self.get_all_comments())

    def save(self, destination: str | None = None, validate: bool = True) -> None:
        """
        保存更改。

        参数:
            destination: 可选的目标路径
            validate: 是否验证文档
        """
        self.document.save(destination=destination, validate=validate)

    def _parse_comment_element(self, elem) -> Comment | None:
        """解析批注元素为 Comment 对象"""
        comment_id = elem.getAttribute("w:id")
        if not comment_id:
            return None

        author = elem.getAttribute("w:author")
        initials = elem.getAttribute("w:initials")
        date = elem.getAttribute("w:date")

        text_parts = []
        for t_elem in elem.getElementsByTagName("w:t"):
            if t_elem.firstChild:
                text_parts.append(t_elem.firstChild.data)
        text = "".join(text_parts)

        para_id = ""
        for p_elem in elem.getElementsByTagName("w:p"):
            para_id = p_elem.getAttribute("w14:paraId")
            if para_id:
                break

        parent_id = None
        para_id_attr = elem.getAttribute("w15:paraIdParent")
        if para_id_attr:
            parent_id = self._find_comment_by_para_id(para_id_attr)

        return Comment(
            id=int(comment_id),
            text=text,
            author=author,
            initials=initials,
            date=date,
            para_id=para_id,
            parent_id=parent_id
        )

    def _find_comment_by_para_id(self, para_id: str) -> int | None:
        """根据 para_id 查找批注 ID"""
        comments_path = self.document.word_path / "comments.xml"
        if not comments_path.exists():
            return None

        editor = self.document["word/comments.xml"]

        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            for p_elem in comment_elem.getElementsByTagName("w:p"):
                if p_elem.getAttribute("w14:paraId") == para_id:
                    cid = comment_elem.getAttribute("w:id")
                    if cid:
                        return int(cid)

        return None

    def _remove_comment_ranges(self, comment_id: int) -> None:
        """删除文档中的批注范围标记"""
        doc_editor = self.document["word/document.xml"]

        for tag in ["w:commentRangeStart", "w:commentRangeEnd"]:
            elements_to_remove = []
            for elem in doc_editor.dom.getElementsByTagName(tag):
                if elem.getAttribute("w:id") == str(comment_id):
                    elements_to_remove.append(elem)

            for elem in elements_to_remove:
                parent = elem.parentNode
                parent.removeChild(elem)

        ref_elements = []
        for ref in doc_editor.dom.getElementsByTagName("w:commentReference"):
            if ref.getAttribute("w:id") == str(comment_id):
                ref_elements.append(ref)

        for ref in ref_elements:
            run = ref.parentNode
            if run and run.tagName == "w:r":
                parent = run.parentNode
                parent.removeChild(run)
