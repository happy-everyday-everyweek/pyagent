"""
Word 文档编辑器

提供基于 XML 的底层文档编辑能力，支持批注、修订跟踪等功能。
自动为新元素应用 RSID、作者和日期属性。

使用示例:
    from src.document.docx.editor import Document
    
    # 初始化
    doc = Document('workspace/unpacked')
    doc = Document('workspace/unpacked', author="张三", initials="ZS")
    
    # 查找节点
    node = doc["word/document.xml"].get_node(tag="w:del", attrs={"w:id": "1"})
    node = doc["word/document.xml"].get_node(tag="w:p", line_number=10)
    
    # 添加批注
    doc.add_comment(start=node, end=node, text="批注内容")
    doc.reply_to_comment(parent_comment_id=0, text="回复内容")
    
    # 建议修订
    doc["word/document.xml"].suggest_deletion(node)  # 删除内容
    doc["word/document.xml"].revert_insertion(ins_node)  # 拒绝插入
    doc["word/document.xml"].revert_deletion(del_node)  # 拒绝删除
    
    # 保存
    doc.save()
"""

import html
import random
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from defusedxml import minidom

from src.document.docx.utilities import XMLEditor

TEMPLATE_DIR = Path(__file__).parent / "templates"


class DocxXMLEditor(XMLEditor):
    """
    自动应用 RSID、作者和日期属性的 XML 编辑器。

    在插入新内容时自动为支持的元素添加属性:
    - w:rsidR, w:rsidRDefault, w:rsidP (用于 w:p 和 w:r 元素)
    - w:author 和 w:date (用于 w:ins, w:del, w:comment 元素)
    - w:id (用于 w:ins 和 w:del 元素)

    属性:
        dom (defusedxml.minidom.Document): 用于直接操作的 DOM 文档
    """

    def __init__(
        self, xml_path, rsid: str, author: str = "Claude", initials: str = "C"
    ):
        """
        使用必需的 RSID 和可选的作者信息初始化。

        参数:
            xml_path: 要编辑的 XML 文件路径
            rsid: 自动应用到新元素的 RSID
            author: 修订和批注的作者名称 (默认: "Claude")
            initials: 作者缩写 (默认: "C")
        """
        super().__init__(xml_path)
        self.rsid = rsid
        self.author = author
        self.initials = initials

    def _get_next_change_id(self):
        """通过检查所有修订元素获取下一个可用的修订 ID。"""
        max_id = -1
        for tag in ("w:ins", "w:del"):
            elements = self.dom.getElementsByTagName(tag)
            for elem in elements:
                change_id = elem.getAttribute("w:id")
                if change_id:
                    try:
                        max_id = max(max_id, int(change_id))
                    except ValueError:
                        pass
        return max_id + 1

    def _ensure_w16du_namespace(self):
        """确保根元素上声明了 w16du 命名空间。"""
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16du"):
            root.setAttribute(
                "xmlns:w16du",
                "http://schemas.microsoft.com/office/word/2023/wordml/word16du",
            )

    def _ensure_w16cex_namespace(self):
        """确保根元素上声明了 w16cex 命名空间。"""
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w16cex"):
            root.setAttribute(
                "xmlns:w16cex",
                "http://schemas.microsoft.com/office/word/2018/wordml/cex",
            )

    def _ensure_w14_namespace(self):
        """确保根元素上声明了 w14 命名空间。"""
        root = self.dom.documentElement
        if not root.hasAttribute("xmlns:w14"):
            root.setAttribute(
                "xmlns:w14",
                "http://schemas.microsoft.com/office/word/2010/wordml",
            )

    def _inject_attributes_to_nodes(self, nodes):
        """
        将 RSID、作者和日期属性注入到适用的 DOM 节点。

        为支持的元素添加属性:
        - w:r: 获取 w:rsidR (如果在 w:del 内则获取 w:rsidDel)
        - w:p: 获取 w:rsidR, w:rsidRDefault, w:rsidP, w14:paraId, w14:textId
        - w:t: 如果文本有前导/尾随空白则获取 xml:space="preserve"
        - w:ins, w:del: 获取 w:id, w:author, w:date, w16du:dateUtc
        - w:comment: 获取 w:author, w:date, w:initials
        - w16cex:commentExtensible: 获取 w16cex:dateUtc

        参数:
            nodes: 要处理的 DOM 节点列表
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        def is_inside_deletion(elem):
            """检查元素是否在 w:del 元素内部。"""
            parent = elem.parentNode
            while parent:
                if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
                    return True
                parent = parent.parentNode
            return False

        def add_rsid_to_p(elem):
            if not elem.hasAttribute("w:rsidR"):
                elem.setAttribute("w:rsidR", self.rsid)
            if not elem.hasAttribute("w:rsidRDefault"):
                elem.setAttribute("w:rsidRDefault", self.rsid)
            if not elem.hasAttribute("w:rsidP"):
                elem.setAttribute("w:rsidP", self.rsid)
            if not elem.hasAttribute("w14:paraId"):
                self._ensure_w14_namespace()
                elem.setAttribute("w14:paraId", _generate_hex_id())
            if not elem.hasAttribute("w14:textId"):
                self._ensure_w14_namespace()
                elem.setAttribute("w14:textId", _generate_hex_id())

        def add_rsid_to_r(elem):
            if is_inside_deletion(elem):
                if not elem.hasAttribute("w:rsidDel"):
                    elem.setAttribute("w:rsidDel", self.rsid)
            elif not elem.hasAttribute("w:rsidR"):
                elem.setAttribute("w:rsidR", self.rsid)

        def add_tracked_change_attrs(elem):
            if not elem.hasAttribute("w:id"):
                elem.setAttribute("w:id", str(self._get_next_change_id()))
            if not elem.hasAttribute("w:author"):
                elem.setAttribute("w:author", self.author)
            if not elem.hasAttribute("w:date"):
                elem.setAttribute("w:date", timestamp)
            if elem.tagName in ("w:ins", "w:del") and not elem.hasAttribute(
                "w16du:dateUtc"
            ):
                self._ensure_w16du_namespace()
                elem.setAttribute("w16du:dateUtc", timestamp)

        def add_comment_attrs(elem):
            if not elem.hasAttribute("w:author"):
                elem.setAttribute("w:author", self.author)
            if not elem.hasAttribute("w:date"):
                elem.setAttribute("w:date", timestamp)
            if not elem.hasAttribute("w:initials"):
                elem.setAttribute("w:initials", self.initials)

        def add_comment_extensible_date(elem):
            if not elem.hasAttribute("w16cex:dateUtc"):
                self._ensure_w16cex_namespace()
                elem.setAttribute("w16cex:dateUtc", timestamp)

        def add_xml_space_to_t(elem):
            if (
                elem.firstChild
                and elem.firstChild.nodeType == elem.firstChild.TEXT_NODE
            ):
                text = elem.firstChild.data
                if text and (text[0].isspace() or text[-1].isspace()):
                    if not elem.hasAttribute("xml:space"):
                        elem.setAttribute("xml:space", "preserve")

        for node in nodes:
            if node.nodeType != node.ELEMENT_NODE:
                continue

            if node.tagName == "w:p":
                add_rsid_to_p(node)
            elif node.tagName == "w:r":
                add_rsid_to_r(node)
            elif node.tagName == "w:t":
                add_xml_space_to_t(node)
            elif node.tagName in ("w:ins", "w:del"):
                add_tracked_change_attrs(node)
            elif node.tagName == "w:comment":
                add_comment_attrs(node)
            elif node.tagName == "w16cex:commentExtensible":
                add_comment_extensible_date(node)

            for elem in node.getElementsByTagName("w:p"):
                add_rsid_to_p(elem)
            for elem in node.getElementsByTagName("w:r"):
                add_rsid_to_r(elem)
            for elem in node.getElementsByTagName("w:t"):
                add_xml_space_to_t(elem)
            for tag in ("w:ins", "w:del"):
                for elem in node.getElementsByTagName(tag):
                    add_tracked_change_attrs(elem)
            for elem in node.getElementsByTagName("w:comment"):
                add_comment_attrs(elem)
            for elem in node.getElementsByTagName("w16cex:commentExtensible"):
                add_comment_extensible_date(elem)

    def replace_node(self, elem, new_content):
        """替换节点并自动注入属性。"""
        nodes = super().replace_node(elem, new_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def insert_after(self, elem, xml_content):
        """在节点后插入并自动注入属性。"""
        nodes = super().insert_after(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def insert_before(self, elem, xml_content):
        """在节点前插入并自动注入属性。"""
        nodes = super().insert_before(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def append_to(self, elem, xml_content):
        """追加到节点并自动注入属性。"""
        nodes = super().append_to(elem, xml_content)
        self._inject_attributes_to_nodes(nodes)
        return nodes

    def revert_insertion(self, elem):
        """
        通过将插入内容包装为删除来拒绝插入。

        将 w:ins 内的所有运行包装在 w:del 中，将 w:t 转换为 w:delText。
        可以处理单个 w:ins 元素或包含多个 w:ins 的容器元素。

        参数:
            elem: 要处理的元素 (w:ins, w:p, w:body 等)

        返回:
            list: 包含已处理元素的列表

        异常:
            ValueError: 如果元素不包含 w:ins 元素

        示例:
            # 拒绝单个插入
            ins = doc["word/document.xml"].get_node(tag="w:ins", attrs={"w:id": "5"})
            doc["word/document.xml"].revert_insertion(ins)
            
            # 拒绝段落中的所有插入
            para = doc["word/document.xml"].get_node(tag="w:p", line_number=42)
            doc["word/document.xml"].revert_insertion(para)
        """
        ins_elements = []
        if elem.tagName == "w:ins":
            ins_elements.append(elem)
        else:
            ins_elements.extend(elem.getElementsByTagName("w:ins"))

        if not ins_elements:
            raise ValueError(
                f"revert_insertion 需要 w:ins 元素。"
                f"提供的元素 <{elem.tagName}> 不包含插入内容。"
            )

        for ins_elem in ins_elements:
            runs = list(ins_elem.getElementsByTagName("w:r"))
            if not runs:
                continue

            del_wrapper = self.dom.createElement("w:del")

            for run in runs:
                if run.hasAttribute("w:rsidR"):
                    run.setAttribute("w:rsidDel", run.getAttribute("w:rsidR"))
                    run.removeAttribute("w:rsidR")
                elif not run.hasAttribute("w:rsidDel"):
                    run.setAttribute("w:rsidDel", self.rsid)

                for t_elem in list(run.getElementsByTagName("w:t")):
                    del_text = self.dom.createElement("w:delText")
                    while t_elem.firstChild:
                        del_text.appendChild(t_elem.firstChild)
                    for i in range(t_elem.attributes.length):
                        attr = t_elem.attributes.item(i)
                        del_text.setAttribute(attr.name, attr.value)
                    t_elem.parentNode.replaceChild(del_text, t_elem)

            while ins_elem.firstChild:
                del_wrapper.appendChild(ins_elem.firstChild)

            ins_elem.appendChild(del_wrapper)

            self._inject_attributes_to_nodes([del_wrapper])

        return [elem]

    def revert_deletion(self, elem):
        """
        通过重新插入已删除内容来拒绝删除。

        在每个 w:del 之后创建 w:ins 元素，复制已删除内容并将
        w:delText 转换回 w:t。
        可以处理单个 w:del 元素或包含多个 w:del 的容器元素。

        参数:
            elem: 要处理的元素 (w:del, w:p, w:body 等)

        返回:
            list: 如果 elem 是 w:del，返回 [elem, new_ins]。否则返回 [elem]。

        异常:
            ValueError: 如果元素不包含 w:del 元素

        示例:
            # 拒绝单个删除 - 返回 [w:del, w:ins]
            del_elem = doc["word/document.xml"].get_node(tag="w:del", attrs={"w:id": "3"})
            nodes = doc["word/document.xml"].revert_deletion(del_elem)
            
            # 拒绝段落中的所有删除 - 返回 [para]
            para = doc["word/document.xml"].get_node(tag="w:p", line_number=42)
            nodes = doc["word/document.xml"].revert_deletion(para)
        """
        del_elements = []
        is_single_del = elem.tagName == "w:del"

        if is_single_del:
            del_elements.append(elem)
        else:
            del_elements.extend(elem.getElementsByTagName("w:del"))

        if not del_elements:
            raise ValueError(
                f"revert_deletion 需要 w:del 元素。"
                f"提供的元素 <{elem.tagName}> 不包含删除内容。"
            )

        created_insertion = None

        for del_elem in del_elements:
            runs = list(del_elem.getElementsByTagName("w:r"))
            if not runs:
                continue

            ins_elem = self.dom.createElement("w:ins")

            for run in runs:
                new_run = run.cloneNode(True)

                for del_text in list(new_run.getElementsByTagName("w:delText")):
                    t_elem = self.dom.createElement("w:t")
                    while del_text.firstChild:
                        t_elem.appendChild(del_text.firstChild)
                    for i in range(del_text.attributes.length):
                        attr = del_text.attributes.item(i)
                        t_elem.setAttribute(attr.name, attr.value)
                    del_text.parentNode.replaceChild(t_elem, del_text)

                if new_run.hasAttribute("w:rsidDel"):
                    new_run.setAttribute("w:rsidR", new_run.getAttribute("w:rsidDel"))
                    new_run.removeAttribute("w:rsidDel")
                elif not new_run.hasAttribute("w:rsidR"):
                    new_run.setAttribute("w:rsidR", self.rsid)

                ins_elem.appendChild(new_run)

            nodes = self.insert_after(del_elem, ins_elem.toxml())

            if is_single_del and nodes:
                created_insertion = nodes[0]

        if is_single_del and created_insertion:
            return [elem, created_insertion]
        return [elem]

    @staticmethod
    def suggest_paragraph(xml_content: str) -> str:
        """
        转换段落 XML 以添加插入修订包装。

        将运行包装在 <w:ins> 中，并为编号列表在 w:pPr 的 w:rPr 中添加 <w:ins/>。

        参数:
            xml_content: 包含 <w:p> 元素的 XML 字符串

        返回:
            str: 带有修订包装的转换后 XML
        """
        wrapper = f'<root xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">{xml_content}</root>'
        doc = minidom.parseString(wrapper)
        para = doc.getElementsByTagName("w:p")[0]

        pPr_list = para.getElementsByTagName("w:pPr")
        if not pPr_list:
            pPr = doc.createElement("w:pPr")
            para.insertBefore(
                pPr, para.firstChild
            ) if para.firstChild else para.appendChild(pPr)
        else:
            pPr = pPr_list[0]

        rPr_list = pPr.getElementsByTagName("w:rPr")
        if not rPr_list:
            rPr = doc.createElement("w:rPr")
            pPr.appendChild(rPr)
        else:
            rPr = rPr_list[0]

        ins_marker = doc.createElement("w:ins")
        rPr.insertBefore(
            ins_marker, rPr.firstChild
        ) if rPr.firstChild else rPr.appendChild(ins_marker)

        ins_wrapper = doc.createElement("w:ins")
        for child in [c for c in para.childNodes if c.nodeName != "w:pPr"]:
            para.removeChild(child)
            ins_wrapper.appendChild(child)
        para.appendChild(ins_wrapper)

        return para.toxml()

    def suggest_deletion(self, elem):
        """
        使用修订跟踪将 w:r 或 w:p 元素标记为已删除（原地 DOM 操作）。

        对于 w:r: 包装在 <w:del> 中，将 <w:t> 转换为 <w:delText>，保留 w:rPr
        对于 w:p (常规): 将内容包装在 <w:del> 中，将 <w:t> 转换为 <w:delText>
        对于 w:p (编号列表): 在 w:pPr 的 w:rPr 中添加 <w:del/>，将内容包装在 <w:del> 中

        参数:
            elem: 没有现有修订跟踪的 w:r 或 w:p DOM 元素

        返回:
            Element: 修改后的元素

        异常:
            ValueError: 如果元素有现有修订跟踪或结构无效
        """
        if elem.nodeName == "w:r":
            if elem.getElementsByTagName("w:delText"):
                raise ValueError("w:r 元素已包含 w:delText")

            for t_elem in list(elem.getElementsByTagName("w:t")):
                del_text = self.dom.createElement("w:delText")
                while t_elem.firstChild:
                    del_text.appendChild(t_elem.firstChild)
                for i in range(t_elem.attributes.length):
                    attr = t_elem.attributes.item(i)
                    del_text.setAttribute(attr.name, attr.value)
                t_elem.parentNode.replaceChild(del_text, t_elem)

            if elem.hasAttribute("w:rsidR"):
                elem.setAttribute("w:rsidDel", elem.getAttribute("w:rsidR"))
                elem.removeAttribute("w:rsidR")
            elif not elem.hasAttribute("w:rsidDel"):
                elem.setAttribute("w:rsidDel", self.rsid)

            del_wrapper = self.dom.createElement("w:del")
            parent = elem.parentNode
            parent.insertBefore(del_wrapper, elem)
            parent.removeChild(elem)
            del_wrapper.appendChild(elem)

            self._inject_attributes_to_nodes([del_wrapper])

            return del_wrapper

        if elem.nodeName == "w:p":
            if elem.getElementsByTagName("w:ins") or elem.getElementsByTagName("w:del"):
                raise ValueError("w:p 元素已包含修订跟踪")

            pPr_list = elem.getElementsByTagName("w:pPr")
            is_numbered = pPr_list and pPr_list[0].getElementsByTagName("w:numPr")

            if is_numbered:
                pPr = pPr_list[0]
                rPr_list = pPr.getElementsByTagName("w:rPr")

                if not rPr_list:
                    rPr = self.dom.createElement("w:rPr")
                    pPr.appendChild(rPr)
                else:
                    rPr = rPr_list[0]

                del_marker = self.dom.createElement("w:del")
                rPr.insertBefore(
                    del_marker, rPr.firstChild
                ) if rPr.firstChild else rPr.appendChild(del_marker)

            for t_elem in list(elem.getElementsByTagName("w:t")):
                del_text = self.dom.createElement("w:delText")
                while t_elem.firstChild:
                    del_text.appendChild(t_elem.firstChild)
                for i in range(t_elem.attributes.length):
                    attr = t_elem.attributes.item(i)
                    del_text.setAttribute(attr.name, attr.value)
                t_elem.parentNode.replaceChild(del_text, t_elem)

            for run in elem.getElementsByTagName("w:r"):
                if run.hasAttribute("w:rsidR"):
                    run.setAttribute("w:rsidDel", run.getAttribute("w:rsidR"))
                    run.removeAttribute("w:rsidR")
                elif not run.hasAttribute("w:rsidDel"):
                    run.setAttribute("w:rsidDel", self.rsid)

            del_wrapper = self.dom.createElement("w:del")
            for child in [c for c in elem.childNodes if c.nodeName != "w:pPr"]:
                elem.removeChild(child)
                del_wrapper.appendChild(child)
            elem.appendChild(del_wrapper)

            self._inject_attributes_to_nodes([del_wrapper])

            return elem

        raise ValueError(f"元素必须是 w:r 或 w:p，得到 {elem.nodeName}")


def _generate_hex_id() -> str:
    """
    生成用于段落/持久 ID 的随机 8 字符十六进制 ID。

    值被限制为小于 0x7FFFFFFF，符合 OOXML 规范:
    - paraId 必须 < 0x80000000
    - durableId 必须 < 0x7FFFFFFF
    我们对两者都使用更严格的约束 (0x7FFFFFFF)。
    """
    return f"{random.randint(1, 0x7FFFFFFE):08X}"


def _generate_rsid() -> str:
    """生成随机 8 字符十六进制 RSID。"""
    return "".join(random.choices("0123456789ABCDEF", k=8))


class Document:
    """管理解压后 Word 文档中的批注。"""

    def __init__(
        self,
        unpacked_dir,
        rsid=None,
        track_revisions=False,
        author="Claude",
        initials="C",
    ):
        """
        使用解压后 Word 文档目录的路径初始化。
        自动设置批注基础设施 (people.xml, RSIDs)。

        参数:
            unpacked_dir: 解压后 DOCX 目录的路径 (必须包含 word/ 子目录)
            rsid: 用于所有批注元素的可选 RSID。如果未提供，将生成一个。
            track_revisions: 如果为 True，在 settings.xml 中启用修订跟踪 (默认: False)
            author: 批注的默认作者名称 (默认: "Claude")
            initials: 批注的默认作者缩写 (默认: "C")
        """
        self.original_path = Path(unpacked_dir)

        if not self.original_path.exists() or not self.original_path.is_dir():
            raise ValueError(f"目录未找到: {unpacked_dir}")

        self.temp_dir = tempfile.mkdtemp(prefix="docx_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"
        shutil.copytree(self.original_path, self.unpacked_path)

        self.original_docx = Path(self.temp_dir) / "original.docx"
        self._pack_document(self.original_path, self.original_docx)

        self.word_path = self.unpacked_path / "word"

        self.rsid = rsid if rsid else _generate_rsid()
        print(f"使用 RSID: {self.rsid}")

        self.author = author
        self.initials = initials

        self._editors = {}

        self.comments_path = self.word_path / "comments.xml"
        self.comments_extended_path = self.word_path / "commentsExtended.xml"
        self.comments_ids_path = self.word_path / "commentsIds.xml"
        self.comments_extensible_path = self.word_path / "commentsExtensible.xml"

        self.existing_comments = self._load_existing_comments()
        self.next_comment_id = self._get_next_comment_id()

        self._document = self["word/document.xml"]

        self._setup_tracking(track_revisions=track_revisions)

        self._add_author_to_people(author)

    def _pack_document(self, source_dir, output_path):
        """将解压后的文档打包为 DOCX 文件。"""
        try:
            from ooxml.scripts.pack import pack_document
            pack_document(source_dir, output_path, validate=False)
        except ImportError:
            import zipfile
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        arc_name = file_path.relative_to(source_dir)
                        zf.write(file_path, arc_name)

    def __getitem__(self, xml_path: str) -> DocxXMLEditor:
        """
        获取或创建指定 XML 文件的 DocxXMLEditor。

        启用延迟加载编辑器的括号表示法:
            node = doc["word/document.xml"].get_node(tag="w:p", line_number=42)

        参数:
            xml_path: XML 文件的相对路径 (例如 "word/document.xml", "word/comments.xml")

        返回:
            指定文件的 DocxXMLEditor 实例

        异常:
            ValueError: 如果文件不存在

        示例:
            # 从 document.xml 获取节点
            node = doc["word/document.xml"].get_node(tag="w:del", attrs={"w:id": "1"})
            
            # 从 comments.xml 获取节点
            comment = doc["word/comments.xml"].get_node(tag="w:comment", attrs={"w:id": "0"})
        """
        if xml_path not in self._editors:
            file_path = self.unpacked_path / xml_path
            if not file_path.exists():
                raise ValueError(f"XML 文件未找到: {xml_path}")
            self._editors[xml_path] = DocxXMLEditor(
                file_path, rsid=self.rsid, author=self.author, initials=self.initials
            )
        return self._editors[xml_path]

    def add_comment(self, start, end, text: str) -> int:
        """
        添加从一个元素到另一个元素的批注。

        参数:
            start: 起始点的 DOM 元素
            end: 结束点的 DOM 元素
            text: 批注内容

        返回:
            创建的批注 ID

        示例:
            start_node = cm.get_document_node(tag="w:del", id="1")
            end_node = cm.get_document_node(tag="w:ins", id="2")
            cm.add_comment(start=start_node, end=end_node, text="说明")
        """
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        self._document.insert_before(start, self._comment_range_start_xml(comment_id))

        if end.tagName == "w:p":
            self._document.append_to(end, self._comment_range_end_xml(comment_id))
        else:
            self._document.insert_after(end, self._comment_range_end_xml(comment_id))

        self._add_to_comments_xml(
            comment_id, para_id, text, self.author, self.initials, timestamp
        )

        self._add_to_comments_extended_xml(para_id, parent_para_id=None)

        self._add_to_comments_ids_xml(para_id, durable_id)

        self._add_to_comments_extensible_xml(durable_id)

        self.existing_comments[comment_id] = {"para_id": para_id}

        self.next_comment_id += 1
        return comment_id

    def reply_to_comment(
        self,
        parent_comment_id: int,
        text: str,
    ) -> int:
        """
        回复现有批注。

        参数:
            parent_comment_id: 要回复的父批注的 w:id
            text: 回复文本

        返回:
            为回复创建的批注 ID

        示例:
            cm.reply_to_comment(parent_comment_id=0, text="我同意这个修改")
        """
        if parent_comment_id not in self.existing_comments:
            raise ValueError(f"未找到 id={parent_comment_id} 的父批注")

        parent_info = self.existing_comments[parent_comment_id]
        comment_id = self.next_comment_id
        para_id = _generate_hex_id()
        durable_id = _generate_hex_id()
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        parent_start_elem = self._document.get_node(
            tag="w:commentRangeStart", attrs={"w:id": str(parent_comment_id)}
        )
        parent_ref_elem = self._document.get_node(
            tag="w:commentReference", attrs={"w:id": str(parent_comment_id)}
        )

        self._document.insert_after(
            parent_start_elem, self._comment_range_start_xml(comment_id)
        )
        parent_ref_run = parent_ref_elem.parentNode
        self._document.insert_after(
            parent_ref_run, f'<w:commentRangeEnd w:id="{comment_id}"/>'
        )
        self._document.insert_after(
            parent_ref_run, self._comment_ref_run_xml(comment_id)
        )

        self._add_to_comments_xml(
            comment_id, para_id, text, self.author, self.initials, timestamp
        )

        self._add_to_comments_extended_xml(
            para_id, parent_para_id=parent_info["para_id"]
        )

        self._add_to_comments_ids_xml(para_id, durable_id)

        self._add_to_comments_extensible_xml(durable_id)

        self.existing_comments[comment_id] = {"para_id": para_id}

        self.next_comment_id += 1
        return comment_id

    def __del__(self):
        """删除时清理临时目录。"""
        if hasattr(self, "temp_dir") and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def validate(self) -> None:
        """
        根据 XSD 架构和修订规则验证文档。

        异常:
            ValueError: 如果验证失败。
        """
        try:
            from ooxml.scripts.validation.docx import DOCXSchemaValidator
            from ooxml.scripts.validation.redlining import RedliningValidator

            schema_validator = DOCXSchemaValidator(
                self.unpacked_path, self.original_docx, verbose=False
            )
            redlining_validator = RedliningValidator(
                self.unpacked_path, self.original_docx, verbose=False
            )

            if not schema_validator.validate():
                raise ValueError("架构验证失败")
            if not redlining_validator.validate():
                raise ValueError("修订验证失败")
        except ImportError:
            print("警告: ooxml 验证模块未安装，跳过验证")

    def save(self, destination=None, validate=True) -> None:
        """
        将所有修改的 XML 文件保存到磁盘并复制到目标目录。

        这将持久化通过 add_comment() 和 reply_to_comment() 所做的所有更改。

        参数:
            destination: 保存到的可选路径。如果为 None，保存回原始目录。
            validate: 如果为 True，保存前验证文档 (默认: True)。
        """
        if self.comments_path.exists():
            self._ensure_comment_relationships()
            self._ensure_comment_content_types()

        for editor in self._editors.values():
            editor.save()

        if validate:
            self.validate()

        target_path = Path(destination) if destination else self.original_path
        shutil.copytree(self.unpacked_path, target_path, dirs_exist_ok=True)

    def _get_next_comment_id(self):
        """获取下一个可用的批注 ID。"""
        if not self.comments_path.exists():
            return 0

        editor = self["word/comments.xml"]
        max_id = -1
        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            comment_id = comment_elem.getAttribute("w:id")
            if comment_id:
                try:
                    max_id = max(max_id, int(comment_id))
                except ValueError:
                    pass
        return max_id + 1

    def _load_existing_comments(self):
        """从文件加载现有批注以启用回复功能。"""
        if not self.comments_path.exists():
            return {}

        editor = self["word/comments.xml"]
        existing = {}

        for comment_elem in editor.dom.getElementsByTagName("w:comment"):
            comment_id = comment_elem.getAttribute("w:id")
            if not comment_id:
                continue

            para_id = None
            for p_elem in comment_elem.getElementsByTagName("w:p"):
                para_id = p_elem.getAttribute("w14:paraId")
                if para_id:
                    break

            if not para_id:
                continue

            existing[int(comment_id)] = {"para_id": para_id}

        return existing

    def _setup_tracking(self, track_revisions=False):
        """
        在解压目录中设置批注基础设施。

        参数:
            track_revisions: 如果为 True，在 settings.xml 中启用修订跟踪
        """
        people_file = self.word_path / "people.xml"
        self._update_people_xml(people_file)

        self._add_content_type_for_people(self.unpacked_path / "[Content_Types].xml")
        self._add_relationship_for_people(
            self.word_path / "_rels" / "document.xml.rels"
        )

        self._update_settings(
            self.word_path / "settings.xml", track_revisions=track_revisions
        )

    def _update_people_xml(self, path):
        """如果不存在则创建 people.xml。"""
        if not path.exists():
            shutil.copy(TEMPLATE_DIR / "people.xml", path)

    def _add_content_type_for_people(self, path):
        """如果尚未存在，将 people.xml 内容类型添加到 [Content_Types].xml。"""
        editor = self["[Content_Types].xml"]

        if self._has_override(editor, "/word/people.xml"):
            return

        root = editor.dom.documentElement
        override_xml = '<Override PartName="/word/people.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.people+xml"/>'
        editor.append_to(root, override_xml)

    def _add_relationship_for_people(self, path):
        """如果尚未存在，将 people.xml 关系添加到 document.xml.rels。"""
        editor = self["word/_rels/document.xml.rels"]

        if self._has_relationship(editor, "people.xml"):
            return

        root = editor.dom.documentElement
        root_tag = root.tagName
        prefix = root_tag.split(":")[0] + ":" if ":" in root_tag else ""
        next_rid = editor.get_next_rid()

        rel_xml = f'<{prefix}Relationship Id="{next_rid}" Type="http://schemas.microsoft.com/office/2011/relationships/people" Target="people.xml"/>'
        editor.append_to(root, rel_xml)

    def _update_settings(self, path, track_revisions=False):
        """
        在 settings.xml 中添加 RSID 并可选地启用修订跟踪。

        参数:
            path: settings.xml 的路径
            track_revisions: 如果为 True，添加 trackRevisions 元素

        按 OOXML 架构顺序放置元素:
        - trackRevisions: 早期 (在 defaultTabStop 之前)
        - rsids: 晚期 (在 compat 之后)
        """
        editor = self["word/settings.xml"]
        root = editor.get_node(tag="w:settings")
        prefix = root.tagName.split(":")[0] if ":" in root.tagName else "w"

        if track_revisions:
            track_revisions_exists = any(
                elem.tagName == f"{prefix}:trackRevisions"
                for elem in editor.dom.getElementsByTagName(f"{prefix}:trackRevisions")
            )

            if not track_revisions_exists:
                track_rev_xml = f"<{prefix}:trackRevisions/>"
                inserted = False
                for tag in [f"{prefix}:documentProtection", f"{prefix}:defaultTabStop"]:
                    elements = editor.dom.getElementsByTagName(tag)
                    if elements:
                        editor.insert_before(elements[0], track_rev_xml)
                        inserted = True
                        break
                if not inserted:
                    if root.firstChild:
                        editor.insert_before(root.firstChild, track_rev_xml)
                    else:
                        editor.append_to(root, track_rev_xml)

        rsids_elements = editor.dom.getElementsByTagName(f"{prefix}:rsids")

        if not rsids_elements:
            rsids_xml = f"""<{prefix}:rsids>
  <{prefix}:rsidRoot {prefix}:val="{self.rsid}"/>
  <{prefix}:rsid {prefix}:val="{self.rsid}"/>
</{prefix}:rsids>"""

            inserted = False
            compat_elements = editor.dom.getElementsByTagName(f"{prefix}:compat")
            if compat_elements:
                editor.insert_after(compat_elements[0], rsids_xml)
                inserted = True

            if not inserted:
                clr_elements = editor.dom.getElementsByTagName(
                    f"{prefix}:clrSchemeMapping"
                )
                if clr_elements:
                    editor.insert_before(clr_elements[0], rsids_xml)
                    inserted = True

            if not inserted:
                editor.append_to(root, rsids_xml)
        else:
            rsids_elem = rsids_elements[0]
            rsid_exists = any(
                elem.getAttribute(f"{prefix}:val") == self.rsid
                for elem in rsids_elem.getElementsByTagName(f"{prefix}:rsid")
            )

            if not rsid_exists:
                rsid_xml = f'<{prefix}:rsid {prefix}:val="{self.rsid}"/>'
                editor.append_to(rsids_elem, rsid_xml)

    def _add_to_comments_xml(
        self, comment_id, para_id, text, author, initials, timestamp
    ):
        """将单个批注添加到 comments.xml。"""
        if not self.comments_path.exists():
            shutil.copy(TEMPLATE_DIR / "comments.xml", self.comments_path)

        editor = self["word/comments.xml"]
        root = editor.get_node(tag="w:comments")

        escaped_text = (
            text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        comment_xml = f"""<w:comment w:id="{comment_id}">
  <w:p w14:paraId="{para_id}" w14:textId="77777777">
    <w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:annotationRef/></w:r>
    <w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{escaped_text}</w:t></w:r>
  </w:p>
</w:comment>"""
        editor.append_to(root, comment_xml)

    def _add_to_comments_extended_xml(self, para_id, parent_para_id):
        """将单个批注添加到 commentsExtended.xml。"""
        if not self.comments_extended_path.exists():
            shutil.copy(
                TEMPLATE_DIR / "commentsExtended.xml", self.comments_extended_path
            )

        editor = self["word/commentsExtended.xml"]
        root = editor.get_node(tag="w15:commentsEx")

        if parent_para_id:
            xml = f'<w15:commentEx w15:paraId="{para_id}" w15:paraIdParent="{parent_para_id}" w15:done="0"/>'
        else:
            xml = f'<w15:commentEx w15:paraId="{para_id}" w15:done="0"/>'
        editor.append_to(root, xml)

    def _add_to_comments_ids_xml(self, para_id, durable_id):
        """将单个批注添加到 commentsIds.xml。"""
        if not self.comments_ids_path.exists():
            shutil.copy(TEMPLATE_DIR / "commentsIds.xml", self.comments_ids_path)

        editor = self["word/commentsIds.xml"]
        root = editor.get_node(tag="w16cid:commentsIds")

        xml = f'<w16cid:commentId w16cid:paraId="{para_id}" w16cid:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    def _add_to_comments_extensible_xml(self, durable_id):
        """将单个批注添加到 commentsExtensible.xml。"""
        if not self.comments_extensible_path.exists():
            shutil.copy(
                TEMPLATE_DIR / "commentsExtensible.xml", self.comments_extensible_path
            )

        editor = self["word/commentsExtensible.xml"]
        root = editor.get_node(tag="w16cex:commentsExtensible")

        xml = f'<w16cex:commentExtensible w16cex:durableId="{durable_id}"/>'
        editor.append_to(root, xml)

    def _comment_range_start_xml(self, comment_id):
        """生成批注范围起始的 XML。"""
        return f'<w:commentRangeStart w:id="{comment_id}"/>'

    def _comment_range_end_xml(self, comment_id):
        """生成带有引用运行的批注范围结束 XML。"""
        return f"""<w:commentRangeEnd w:id="{comment_id}"/>
<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>"""

    def _comment_ref_run_xml(self, comment_id):
        """生成批注引用运行的 XML。"""
        return f"""<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="{comment_id}"/>
</w:r>"""

    def _has_relationship(self, editor, target):
        """检查具有给定目标的关系是否存在。"""
        for rel_elem in editor.dom.getElementsByTagName("Relationship"):
            if rel_elem.getAttribute("Target") == target:
                return True
        return False

    def _has_override(self, editor, part_name):
        """检查具有给定部件名称的覆盖是否存在。"""
        for override_elem in editor.dom.getElementsByTagName("Override"):
            if override_elem.getAttribute("PartName") == part_name:
                return True
        return False

    def _has_author(self, editor, author):
        """检查作者是否已存在于 people.xml 中。"""
        for person_elem in editor.dom.getElementsByTagName("w15:person"):
            if person_elem.getAttribute("w15:author") == author:
                return True
        return False

    def _add_author_to_people(self, author):
        """将作者添加到 people.xml（在初始化期间调用）。"""
        people_path = self.word_path / "people.xml"

        if not people_path.exists():
            raise ValueError("_setup_tracking 后 people.xml 应该存在")

        editor = self["word/people.xml"]
        root = editor.get_node(tag="w15:people")

        if self._has_author(editor, author):
            return

        escaped_author = html.escape(author, quote=True)
        person_xml = f"""<w15:person w15:author="{escaped_author}">
  <w15:presenceInfo w15:providerId="None" w15:userId="{escaped_author}"/>
</w15:person>"""
        editor.append_to(root, person_xml)

    def _ensure_comment_relationships(self):
        """确保 word/_rels/document.xml.rels 具有批注关系。"""
        editor = self["word/_rels/document.xml.rels"]

        if self._has_relationship(editor, "comments.xml"):
            return

        root = editor.dom.documentElement
        root_tag = root.tagName
        prefix = root_tag.split(":")[0] + ":" if ":" in root_tag else ""
        next_rid_num = int(editor.get_next_rid()[3:])

        rels = [
            (
                next_rid_num,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
                "comments.xml",
            ),
            (
                next_rid_num + 1,
                "http://schemas.microsoft.com/office/2011/relationships/commentsExtended",
                "commentsExtended.xml",
            ),
            (
                next_rid_num + 2,
                "http://schemas.microsoft.com/office/2016/09/relationships/commentsIds",
                "commentsIds.xml",
            ),
            (
                next_rid_num + 3,
                "http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible",
                "commentsExtensible.xml",
            ),
        ]

        for rel_id, rel_type, target in rels:
            rel_xml = f'<{prefix}Relationship Id="rId{rel_id}" Type="{rel_type}" Target="{target}"/>'
            editor.append_to(root, rel_xml)

    def _ensure_comment_content_types(self):
        """确保 [Content_Types].xml 具有批注内容类型。"""
        editor = self["[Content_Types].xml"]

        if self._has_override(editor, "/word/comments.xml"):
            return

        root = editor.dom.documentElement

        overrides = [
            (
                "/word/comments.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
            ),
            (
                "/word/commentsExtended.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtended+xml",
            ),
            (
                "/word/commentsIds.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsIds+xml",
            ),
            (
                "/word/commentsExtensible.xml",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtensible+xml",
            ),
        ]

        for part_name, content_type in overrides:
            override_xml = (
                f'<Override PartName="{part_name}" ContentType="{content_type}"/>'
            )
            editor.append_to(root, override_xml)
