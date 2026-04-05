"""
PowerPoint 演示文稿编辑器

提供对现有演示文稿的编辑功能。
支持修改文本、形状、图片等内容。
"""

import shutil
import tempfile
from pathlib import Path

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document


class PptxEditor:
    """
    PowerPoint 演示文稿编辑器。

    提供对现有演示文稿的编辑功能，包括文本修改、
    形状编辑、幻灯片管理等。

    属性:
        unpacked_path: 解压后的临时目录路径
        slides_count: 当前幻灯片数量

    示例:
        editor = PptxEditor("presentation.pptx")
        editor.set_text(1, "Title 1", "新标题")
        editor.save("edited.pptx")
    """

    def __init__(self, document_path: str | Path):
        """
        初始化演示文稿编辑器。

        参数:
            document_path: 要编辑的演示文稿路径

        示例:
            editor = PptxEditor("presentation.pptx")
        """
        self.document_path = Path(document_path)
        self.temp_dir = tempfile.mkdtemp(prefix="pptx_editor_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"

        unpack_document(self.document_path, self.unpacked_path, suggest_rsid=False)

        self.slides_dir = self.unpacked_path / "ppt" / "slides"
        self._slides_count = self._count_slides()

    def _count_slides(self) -> int:
        """计算当前幻灯片数量。"""
        if not self.slides_dir.exists():
            return 0
        return len(list(self.slides_dir.glob("slide*.xml")))

    @property
    def slides_count(self) -> int:
        """当前幻灯片数量。"""
        return self._slides_count

    def get_slide_xml(self, slide_index: int) -> str | None:
        """
        获取指定幻灯片的 XML 内容。

        参数:
            slide_index: 幻灯片索引 (从 1 开始)

        返回:
            str: XML 内容，如果不存在返回 None

        示例:
            xml = editor.get_slide_xml(1)
        """
        slide_path = self.slides_dir / f"slide{slide_index}.xml"
        if slide_path.exists():
            return slide_path.read_text(encoding="utf-8")
        return None

    def set_slide_xml(self, slide_index: int, xml_content: str) -> bool:
        """
        设置指定幻灯片的 XML 内容。

        参数:
            slide_index: 幻灯片索引 (从 1 开始)
            xml_content: 新的 XML 内容

        返回:
            bool: 成功返回 True

        示例:
            editor.set_slide_xml(1, new_xml)
        """
        slide_path = self.slides_dir / f"slide{slide_index}.xml"
        if slide_path.exists():
            slide_path.write_text(xml_content, encoding="utf-8")
            return True
        return False

    def find_text_elements(self, slide_index: int) -> list[dict]:
        """
        查找幻灯片中的所有文本元素。

        参数:
            slide_index: 幻灯片索引 (从 1 开始)

        返回:
            list[dict]: 文本元素列表，每个元素包含:
                - name: 元素名称
                - text: 文本内容
                - type: 占位符类型 (如果有)

        示例:
            elements = editor.find_text_elements(1)
            for elem in elements:
                print(f"{elem['name']}: {elem['text']}")
        """
        import defusedxml.minidom

        slide_path = self.slides_dir / f"slide{slide_index}.xml"
        if not slide_path.exists():
            return []

        elements = []
        try:
            content = slide_path.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)

            for sp in dom.getElementsByTagName("p:sp"):
                elem_info = {"name": "", "text": "", "type": None}

                cNvPr = sp.getElementsByTagName("p:cNvPr")
                if cNvPr:
                    elem_info["name"] = cNvPr[0].getAttribute("name")

                nvPr = sp.getElementsByTagName("p:nvPr")
                if nvPr:
                    ph = nvPr[0].getElementsByTagName("p:ph")
                    if ph:
                        elem_info["type"] = ph[0].getAttribute("type")

                text_parts = []
                for t in sp.getElementsByTagName("a:t"):
                    if t.firstChild:
                        text_parts.append(t.firstChild.nodeValue or "")
                elem_info["text"] = "".join(text_parts)

                elements.append(elem_info)

        except Exception:
            pass

        return elements

    def set_text(
        self,
        slide_index: int,
        element_name: str,
        new_text: str,
    ) -> bool:
        """
        设置指定元素的文本内容。

        参数:
            slide_index: 幻灯片索引 (从 1 开始)
            element_name: 元素名称
            new_text: 新的文本内容

        返回:
            bool: 成功返回 True

        示例:
            editor.set_text(1, "Title 1", "新标题")
        """
        import defusedxml.minidom

        slide_path = self.slides_dir / f"slide{slide_index}.xml"
        if not slide_path.exists():
            return False

        try:
            content = slide_path.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)
            modified = False

            for sp in dom.getElementsByTagName("p:sp"):
                cNvPr = sp.getElementsByTagName("p:cNvPr")
                if cNvPr and cNvPr[0].getAttribute("name") == element_name:
                    for t in sp.getElementsByTagName("a:t"):
                        if t.firstChild:
                            t.firstChild.nodeValue = new_text
                            modified = True
                            break
                        text_node = dom.createTextNode(new_text)
                        t.appendChild(text_node)
                        modified = True
                        break

            if modified:
                slide_path.write_text(
                    dom.toxml(encoding="UTF-8").decode("utf-8"), encoding="utf-8"
                )
            return modified

        except Exception:
            return False

    def duplicate_slide(self, slide_index: int) -> int | None:
        """
        复制幻灯片。

        参数:
            slide_index: 要复制的幻灯片索引 (从 1 开始)

        返回:
            int: 新幻灯片的索引，失败返回 None

        示例:
            new_idx = editor.duplicate_slide(1)
        """
        slide_path = self.slides_dir / f"slide{slide_index}.xml"
        if not slide_path.exists():
            return None

        self._slides_count += 1
        new_slide_index = self._slides_count

        new_slide_path = self.slides_dir / f"slide{new_slide_index}.xml"
        shutil.copy(slide_path, new_slide_path)

        slide_rels_path = self.slides_dir / "_rels" / f"slide{slide_index}.xml.rels"
        if slide_rels_path.exists():
            new_rels_path = self.slides_dir / "_rels" / f"slide{new_slide_index}.xml.rels"
            shutil.copy(slide_rels_path, new_rels_path)

        self._update_presentation_for_new_slide(new_slide_index)
        self._update_content_types_for_new_slide(new_slide_index)

        return new_slide_index

    def _update_presentation_for_new_slide(self, slide_num: int) -> None:
        """更新 presentation.xml 以包含新幻灯片。"""
        pres_path = self.unpacked_path / "ppt" / "presentation.xml"
        if not pres_path.exists():
            return

        content = pres_path.read_text(encoding="utf-8")

        slide_id = 255 + slide_num
        new_sld_id = f'<p:sldId id="{slide_id}" r:id="rId{slide_num}"/>'

        if "</p:sldIdLst>" in content:
            content = content.replace("</p:sldIdLst>", f"  {new_sld_id}\n  </p:sldIdLst>")
            pres_path.write_text(content, encoding="utf-8")

        pres_rels_path = self.unpacked_path / "ppt" / "_rels" / "presentation.xml.rels"
        if pres_rels_path.exists():
            rels_content = pres_rels_path.read_text(encoding="utf-8")
            new_rel = f'<Relationship Id="rId{slide_num}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{slide_num}.xml"/>'
            rels_content = rels_content.replace(
                "</Relationships>", f"  {new_rel}\n</Relationships>"
            )
            pres_rels_path.write_text(rels_content, encoding="utf-8")

    def _update_content_types_for_new_slide(self, slide_num: int) -> None:
        """更新 [Content_Types].xml 以包含新幻灯片。"""
        ct_path = self.unpacked_path / "[Content_Types].xml"
        if not ct_path.exists():
            return

        content = ct_path.read_text(encoding="utf-8")
        new_override = f'<Override PartName="/ppt/slides/slide{slide_num}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'

        if f"/ppt/slides/slide{slide_num}.xml" not in content:
            content = content.replace("</Types>", f"  {new_override}\n</Types>")
            ct_path.write_text(content, encoding="utf-8")

    def delete_slide(self, slide_index: int) -> bool:
        """
        删除幻灯片。

        参数:
            slide_index: 要删除的幻灯片索引 (从 1 开始)

        返回:
            bool: 成功返回 True

        示例:
            editor.delete_slide(2)
        """
        slide_path = self.slides_dir / f"slide{slide_index}.xml"
        if not slide_path.exists():
            return False

        slide_path.unlink()

        slide_rels_path = self.slides_dir / "_rels" / f"slide{slide_index}.xml.rels"
        if slide_rels_path.exists():
            slide_rels_path.unlink()

        self._slides_count -= 1
        return True

    def save(
        self,
        output_path: str | Path,
        validate: bool = False,
    ) -> bool:
        """
        保存编辑后的演示文稿。

        参数:
            output_path: 输出文件路径
            validate: 是否验证文档 (默认: False)

        返回:
            bool: 保存成功返回 True

        示例:
            editor.save("edited.pptx")
        """
        return pack_document(self.unpacked_path, output_path, validate=validate)

    def __del__(self):
        """清理临时目录。"""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
