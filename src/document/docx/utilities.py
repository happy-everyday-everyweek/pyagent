"""
OOXML 文档编辑工具类

提供基于行号的 XML 节点查找和 DOM 操作功能。
每个元素在解析时自动标注其原始行号和列号位置。

使用示例:
    editor = XMLEditor("document.xml")
    
    # 按行号或范围查找节点
    elem = editor.get_node(tag="w:r", line_number=519)
    elem = editor.get_node(tag="w:p", line_number=range(100, 200))
    
    # 按文本内容查找节点
    elem = editor.get_node(tag="w:p", contains="specific text")
    
    # 按属性查找节点
    elem = editor.get_node(tag="w:r", attrs={"w:id": "target"})
    
    # 组合过滤条件
    elem = editor.get_node(tag="w:p", line_number=range(1, 50), contains="text")
    
    # 替换、插入或操作节点
    new_elem = editor.replace_node(elem, "<w:r><w:t>new text</w:t></w:r>")
    editor.insert_after(new_elem, "<w:r><w:t>more</w:t></w:r>")
    
    # 保存更改
    editor.save()
"""

import html
from pathlib import Path

import defusedxml.minidom
import defusedxml.sax


class XMLEditor:
    """
    OOXML XML 文件编辑器，支持基于行号的节点查找。

    此类解析 XML 文件并跟踪每个元素的原始行号和列号位置。
    这使得可以通过原始文件中的行号查找节点，在使用 Read 工具输出时非常有用。

    属性:
        xml_path: 正在编辑的 XML 文件路径
        encoding: 检测到的 XML 文件编码 ('ascii' 或 'utf-8')
        dom: 解析后的 DOM 树，元素上带有 parse_position 属性
    """

    def __init__(self, xml_path):
        """
        使用 XML 文件路径初始化并进行行号跟踪解析。

        参数:
            xml_path: 要编辑的 XML 文件路径 (str 或 Path)

        异常:
            ValueError: 如果 XML 文件不存在
        """
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise ValueError(f"XML 文件未找到: {xml_path}")

        with open(self.xml_path, "rb") as f:
            header = f.read(200).decode("utf-8", errors="ignore")
        self.encoding = "ascii" if 'encoding="ascii"' in header else "utf-8"

        parser = _create_line_tracking_parser()
        self.dom = defusedxml.minidom.parse(str(self.xml_path), parser)

    def get_node(
        self,
        tag: str,
        attrs: dict[str, str] | None = None,
        line_number: int | range | None = None,
        contains: str | None = None,
    ):
        """
        通过标签和标识符获取 DOM 元素。

        通过原始文件中的行号或匹配属性值查找元素。
        必须找到且仅找到一个匹配项。

        参数:
            tag: XML 标签名 (例如 "w:del", "w:ins", "w:r")
            attrs: 要匹配的属性名值对字典 (例如 {"w:id": "1"})
            line_number: 原始 XML 文件中的行号 (int) 或行范围 (range)，从 1 开始
            contains: 元素内任意文本节点中必须包含的文本字符串。
                      支持实体表示法 (&#8220;) 和 Unicode 字符 (\u201c)。

        返回:
            defusedxml.minidom.Element: 匹配的 DOM 元素

        异常:
            ValueError: 如果未找到节点或找到多个匹配项

        示例:
            elem = editor.get_node(tag="w:r", line_number=519)
            elem = editor.get_node(tag="w:r", line_number=range(100, 200))
            elem = editor.get_node(tag="w:del", attrs={"w:id": "1"})
            elem = editor.get_node(tag="w:p", attrs={"w14:paraId": "12345678"})
            elem = editor.get_node(tag="w:commentRangeStart", attrs={"w:id": "0"})
            elem = editor.get_node(tag="w:p", contains="specific text")
            elem = editor.get_node(tag="w:t", contains="&#8220;Agreement")  # 实体表示法
            elem = editor.get_node(tag="w:t", contains="\u201cAgreement")   # Unicode 字符
        """
        matches = []
        for elem in self.dom.getElementsByTagName(tag):
            if line_number is not None:
                parse_pos = getattr(elem, "parse_position", (None,))
                elem_line = parse_pos[0]

                if isinstance(line_number, range):
                    if elem_line not in line_number:
                        continue
                elif elem_line != line_number:
                    continue

            if attrs is not None:
                if not all(
                    elem.getAttribute(attr_name) == attr_value
                    for attr_name, attr_value in attrs.items()
                ):
                    continue

            if contains is not None:
                elem_text = self._get_element_text(elem)
                normalized_contains = html.unescape(contains)
                if normalized_contains not in elem_text:
                    continue

            matches.append(elem)

        if not matches:
            filters = []
            if line_number is not None:
                line_str = (
                    f"行 {line_number.start}-{line_number.stop - 1}"
                    if isinstance(line_number, range)
                    else f"行 {line_number}"
                )
                filters.append(f"位于 {line_str}")
            if attrs is not None:
                filters.append(f"属性为 {attrs}")
            if contains is not None:
                filters.append(f"包含 '{contains}'")

            filter_desc = " ".join(filters) if filters else ""
            base_msg = f"节点未找到: <{tag}> {filter_desc}".strip()

            if contains:
                hint = "文本可能被拆分到多个元素中或使用了不同的措辞。"
            elif line_number:
                hint = "如果文档已被修改，行号可能已发生变化。"
            elif attrs:
                hint = "请验证属性值是否正确。"
            else:
                hint = "尝试添加过滤条件 (attrs, line_number, 或 contains)。"

            raise ValueError(f"{base_msg}。{hint}")
        if len(matches) > 1:
            raise ValueError(
                f"找到多个节点: <{tag}>。"
                f"添加更多过滤条件 (attrs, line_number, 或 contains) 以缩小搜索范围。"
            )
        return matches[0]

    def _get_element_text(self, elem):
        """
        递归提取元素中的所有文本内容。

        跳过仅包含空白字符（空格、制表符、换行符）的文本节点，
        这些通常代表 XML 格式而非文档内容。

        参数:
            elem: 要提取文本的 defusedxml.minidom.Element

        返回:
            str: 元素内所有非空白文本节点的连接文本
        """
        text_parts = []
        for node in elem.childNodes:
            if node.nodeType == node.TEXT_NODE:
                if node.data.strip():
                    text_parts.append(node.data)
            elif node.nodeType == node.ELEMENT_NODE:
                text_parts.append(self._get_element_text(node))
        return "".join(text_parts)

    def replace_node(self, elem, new_content):
        """
        用新的 XML 内容替换 DOM 元素。

        参数:
            elem: 要替换的 defusedxml.minidom.Element
            new_content: 包含替换 XML 的字符串

        返回:
            List[defusedxml.minidom.Node]: 所有插入的节点

        示例:
            new_nodes = editor.replace_node(old_elem, "<w:r><w:t>text</w:t></w:r>")
        """
        parent = elem.parentNode
        nodes = self._parse_fragment(new_content)
        for node in nodes:
            parent.insertBefore(node, elem)
        parent.removeChild(elem)
        return nodes

    def insert_after(self, elem, xml_content):
        """
        在 DOM 元素之后插入 XML 内容。

        参数:
            elem: 要在其后插入的 defusedxml.minidom.Element
            xml_content: 包含要插入 XML 的字符串

        返回:
            List[defusedxml.minidom.Node]: 所有插入的节点

        示例:
            new_nodes = editor.insert_after(elem, "<w:r><w:t>text</w:t></w:r>")
        """
        parent = elem.parentNode
        next_sibling = elem.nextSibling
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            if next_sibling:
                parent.insertBefore(node, next_sibling)
            else:
                parent.appendChild(node)
        return nodes

    def insert_before(self, elem, xml_content):
        """
        在 DOM 元素之前插入 XML 内容。

        参数:
            elem: 要在其前插入的 defusedxml.minidom.Element
            xml_content: 包含要插入 XML 的字符串

        返回:
            List[defusedxml.minidom.Node]: 所有插入的节点

        示例:
            new_nodes = editor.insert_before(elem, "<w:r><w:t>text</w:t></w:r>")
        """
        parent = elem.parentNode
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            parent.insertBefore(node, elem)
        return nodes

    def append_to(self, elem, xml_content):
        """
        将 XML 内容作为子节点追加到 DOM 元素。

        参数:
            elem: 要追加到的 defusedxml.minidom.Element
            xml_content: 包含要追加 XML 的字符串

        返回:
            List[defusedxml.minidom.Node]: 所有插入的节点

        示例:
            new_nodes = editor.append_to(elem, "<w:r><w:t>text</w:t></w:r>")
        """
        nodes = self._parse_fragment(xml_content)
        for node in nodes:
            elem.appendChild(node)
        return nodes

    def get_next_rid(self):
        """获取关系文件的下一个可用 rId。"""
        max_id = 0
        for rel_elem in self.dom.getElementsByTagName("Relationship"):
            rel_id = rel_elem.getAttribute("Id")
            if rel_id.startswith("rId"):
                try:
                    max_id = max(max_id, int(rel_id[3:]))
                except ValueError:
                    pass
        return f"rId{max_id + 1}"

    def save(self):
        """
        将编辑后的 XML 保存回文件。

        序列化 DOM 树并将其写回原始文件路径，
        保留原始编码 (ascii 或 utf-8)。
        """
        content = self.dom.toxml(encoding=self.encoding)
        self.xml_path.write_bytes(content)

    def _parse_fragment(self, xml_content):
        """
        解析 XML 片段并返回导入的节点列表。

        参数:
            xml_content: 包含 XML 片段的字符串

        返回:
            导入到此文档的 defusedxml.minidom.Node 对象列表

        异常:
            AssertionError: 如果片段不包含元素节点
        """
        root_elem = self.dom.documentElement
        namespaces = []
        if root_elem and root_elem.attributes:
            for i in range(root_elem.attributes.length):
                attr = root_elem.attributes.item(i)
                if attr.name.startswith("xmlns"):
                    namespaces.append(f'{attr.name}="{attr.value}"')

        ns_decl = " ".join(namespaces)
        wrapper = f"<root {ns_decl}>{xml_content}</root>"
        fragment_doc = defusedxml.minidom.parseString(wrapper)
        nodes = [
            self.dom.importNode(child, deep=True)
            for child in fragment_doc.documentElement.childNodes
        ]
        elements = [n for n in nodes if n.nodeType == n.ELEMENT_NODE]
        assert elements, "片段必须包含至少一个元素"
        return nodes


def _create_line_tracking_parser():
    """
    创建跟踪每个元素行号和列号的 SAX 解析器。

    通过猴子补丁方式修改 SAX 内容处理器，将底层 expat 解析器的
    当前行号和列号位置存储为每个元素的 parse_position 属性 (行, 列) 元组。

    返回:
        defusedxml.sax.xmlreader.XMLReader: 配置好的 SAX 解析器
    """

    def set_content_handler(dom_handler):
        def startElementNS(name, tagName, attrs):
            orig_start_cb(name, tagName, attrs)
            cur_elem = dom_handler.elementStack[-1]
            cur_elem.parse_position = (
                parser._parser.CurrentLineNumber,
                parser._parser.CurrentColumnNumber,
            )

        orig_start_cb = dom_handler.startElementNS
        dom_handler.startElementNS = startElementNS
        orig_set_content_handler(dom_handler)

    parser = defusedxml.sax.make_parser()
    orig_set_content_handler = parser.setContentHandler
    parser.setContentHandler = set_content_handler
    return parser
