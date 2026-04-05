"""
PowerPoint 幻灯片管理器

提供幻灯片的添加、删除、重排等管理功能。
"""

import shutil
import tempfile
from pathlib import Path

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document


class SlideManager:
    """
    PowerPoint 幻灯片管理器。

    提供幻灯片的增删改查和重排功能。

    属性:
        unpacked_path: 解压后的临时目录路径
        slides: 幻灯片信息列表

    示例:
        manager = SlideManager("presentation.pptx")
        slides = manager.list_slides()
        manager.move_slide(1, 3)
        manager.save("reordered.pptx")
    """

    def __init__(self, document_path: str | Path):
        """
        初始化幻灯片管理器。

        参数:
            document_path: 演示文稿路径

        示例:
            manager = SlideManager("presentation.pptx")
        """
        self.document_path = Path(document_path)
        self.temp_dir = tempfile.mkdtemp(prefix="pptx_slide_manager_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"

        unpack_document(self.document_path, self.unpacked_path, suggest_rsid=False)

        self.slides_dir = self.unpacked_path / "ppt" / "slides"

    def list_slides(self) -> list[dict]:
        """
        列出所有幻灯片信息。

        返回:
            list[dict]: 幻灯片信息列表，每个元素包含:
                - index: 幻灯片索引 (从 1 开始)
                - path: 幻灯片文件路径
                - size: 文件大小 (字节)

        示例:
            slides = manager.list_slides()
            for slide in slides:
                print(f"幻灯片 {slide['index']}: {slide['size']} 字节")
        """
        slides = []

        if not self.slides_dir.exists():
            return slides

        for slide_file in sorted(self.slides_dir.glob("slide*.xml")):
            try:
                index = int(slide_file.stem.replace("slide", ""))
                slides.append({
                    "index": index,
                    "path": str(slide_file),
                    "size": slide_file.stat().st_size,
                })
            except ValueError:
                continue

        return slides

    def get_slide_count(self) -> int:
        """
        获取幻灯片数量。

        返回:
            int: 幻灯片数量

        示例:
            count = manager.get_slide_count()
        """
        return len(self.list_slides())

    def move_slide(self, from_index: int, to_index: int) -> bool:
        """
        移动幻灯片位置。

        参数:
            from_index: 原位置索引 (从 1 开始)
            to_index: 目标位置索引 (从 1 开始)

        返回:
            bool: 成功返回 True

        示例:
            manager.move_slide(1, 3)
        """
        slides = self.list_slides()
        if not slides:
            return False

        if from_index < 1 or from_index > len(slides):
            return False
        if to_index < 1 or to_index > len(slides):
            return False

        if from_index == to_index:
            return True

        slide_files = sorted(self.slides_dir.glob("slide*.xml"))
        rels_files = sorted(self.slides_dir.glob("_rels/slide*.xml.rels"))

        temp_slide = self.slides_dir / "slide_temp.xml"
        temp_rels = self.slides_dir / "_rels" / "slide_temp.xml.rels"

        from_file = self.slides_dir / f"slide{from_index}.xml"
        from_rels = self.slides_dir / "_rels" / f"slide{from_index}.xml.rels"

        if not from_file.exists():
            return False

        shutil.copy(from_file, temp_slide)
        if from_rels.exists():
            shutil.copy(from_rels, temp_rels)

        if from_index < to_index:
            for i in range(from_index, to_index):
                src = self.slides_dir / f"slide{i + 1}.xml"
                dst = self.slides_dir / f"slide{i}.xml"
                if src.exists():
                    shutil.move(src, dst)

                src_rels = self.slides_dir / "_rels" / f"slide{i + 1}.xml.rels"
                dst_rels = self.slides_dir / "_rels" / f"slide{i}.xml.rels"
                if src_rels.exists():
                    shutil.move(src_rels, dst_rels)
        else:
            for i in range(from_index, to_index, -1):
                src = self.slides_dir / f"slide{i - 1}.xml"
                dst = self.slides_dir / f"slide{i}.xml"
                if src.exists():
                    shutil.move(src, dst)

                src_rels = self.slides_dir / "_rels" / f"slide{i - 1}.xml.rels"
                dst_rels = self.slides_dir / "_rels" / f"slide{i}.xml.rels"
                if src_rels.exists():
                    shutil.move(src_rels, dst_rels)

        shutil.move(temp_slide, self.slides_dir / f"slide{to_index}.xml")
        if temp_rels.exists():
            shutil.move(temp_rels, self.slides_dir / "_rels" / f"slide{to_index}.xml.rels")

        return True

    def copy_slide_to(
        self,
        source_path: str | Path,
        slide_index: int,
        insert_index: int,
    ) -> bool:
        """
        从另一个演示文稿复制幻灯片。

        参数:
            source_path: 源演示文稿路径
            slide_index: 源幻灯片索引 (从 1 开始)
            insert_index: 插入位置索引 (从 1 开始)

        返回:
            bool: 成功返回 True

        示例:
            manager.copy_slide_to("source.pptx", 1, 2)
        """
        source_path = Path(source_path)
        if not source_path.exists():
            return False

        source_temp_dir = tempfile.mkdtemp(prefix="pptx_source_")
        source_unpacked = Path(source_temp_dir) / "unpacked"

        try:
            unpack_document(source_path, source_unpacked, suggest_rsid=False)

            source_slides_dir = source_unpacked / "ppt" / "slides"
            source_slide = source_slides_dir / f"slide{slide_index}.xml"
            source_rels = source_slides_dir / "_rels" / f"slide{slide_index}.xml.rels"

            if not source_slide.exists():
                return False

            slides = self.list_slides()
            new_index = len(slides) + 1

            target_slide = self.slides_dir / f"slide{new_index}.xml"
            target_rels = self.slides_dir / "_rels" / f"slide{new_index}.xml.rels"

            shutil.copy(source_slide, target_slide)
            if source_rels.exists():
                shutil.copy(source_rels, target_rels)

            self._update_presentation_for_new_slide(new_index)
            self._update_content_types_for_new_slide(new_index)

            if insert_index < new_index:
                self.move_slide(new_index, insert_index)

            return True

        finally:
            shutil.rmtree(source_temp_dir, ignore_errors=True)

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

    def save(
        self,
        output_path: str | Path,
        validate: bool = False,
    ) -> bool:
        """
        保存修改后的演示文稿。

        参数:
            output_path: 输出文件路径
            validate: 是否验证文档 (默认: False)

        返回:
            bool: 保存成功返回 True

        示例:
            manager.save("output.pptx")
        """
        return pack_document(self.unpacked_path, output_path, validate=validate)

    def __del__(self):
        """清理临时目录。"""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
