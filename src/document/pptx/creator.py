"""
PowerPoint 演示文稿创建器

提供基于模板或空白创建演示文稿的功能。
支持设置幻灯片布局、主题颜色、内容添加等。
"""

import shutil
import tempfile
from pathlib import Path

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document


class PptxCreator:
    """
    PowerPoint 演示文稿创建器。

    支持从模板创建或创建空白演示文稿，提供丰富的内容添加功能。

    属性:
        unpacked_path: 解压后的临时目录路径
        slides_count: 当前幻灯片数量

    示例:
        creator = PptxCreator()
        creator.add_title_slide("演示标题", "副标题")
        creator.add_content_slide("内容标题", ["要点1", "要点2"])
        creator.save("presentation.pptx")
    """

    SLIDE_LAYOUTS = {
        "title": "slideLayout1.xml",
        "title_content": "slideLayout2.xml",
        "section_header": "slideLayout3.xml",
        "two_content": "slideLayout4.xml",
        "comparison": "slideLayout5.xml",
        "title_only": "slideLayout6.xml",
        "blank": "slideLayout7.xml",
        "content_caption": "slideLayout8.xml",
    }

    def __init__(
        self,
        template_path: str | Path | None = None,
    ):
        """
        初始化演示文稿创建器。

        参数:
            template_path: 模板文件路径 (可选)，如果提供则基于模板创建

        示例:
            creator = PptxCreator()
            creator_from_template = PptxCreator("template.pptx")
        """
        self.temp_dir = tempfile.mkdtemp(prefix="pptx_creator_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"

        if template_path:
            unpack_document(template_path, self.unpacked_path, suggest_rsid=False)
        else:
            self._create_blank_presentation()

        self.slides_dir = self.unpacked_path / "ppt" / "slides"
        self._slides_count = self._count_slides()

    def _create_blank_presentation(self) -> None:
        """创建空白演示文稿的基础结构。"""
        self.unpacked_path.mkdir(parents=True, exist_ok=True)

        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
</Types>"""
        (self.unpacked_path / "[Content_Types].xml").write_text(content_types, encoding="utf-8")

        rels_dir = self.unpacked_path / "_rels"
        rels_dir.mkdir(exist_ok=True)

        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""
        (rels_dir / ".rels").write_text(rels, encoding="utf-8")

        ppt_dir = self.unpacked_path / "ppt"
        ppt_dir.mkdir(exist_ok=True)

        presentation = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId1"/>
  </p:sldIdLst>
  <p:sldSz cx="9144000" cy="6858000"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""
        (ppt_dir / "presentation.xml").write_text(presentation, encoding="utf-8")

        slides_dir = ppt_dir / "slides"
        slides_dir.mkdir(exist_ok=True)

        slide1 = self._create_slide_xml("标题幻灯片")
        (slides_dir / "slide1.xml").write_text(slide1, encoding="utf-8")

        slides_rels_dir = slides_dir / "_rels"
        slides_rels_dir.mkdir(exist_ok=True)

        slide1_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""
        (slides_rels_dir / "slide1.xml.rels").write_text(slide1_rels, encoding="utf-8")

        layouts_dir = ppt_dir / "slideLayouts"
        layouts_dir.mkdir(exist_ok=True)
        (layouts_dir / "slideLayout1.xml").write_text(
            self._create_layout_xml(), encoding="utf-8"
        )

        masters_dir = ppt_dir / "slideMasters"
        masters_dir.mkdir(exist_ok=True)
        (masters_dir / "slideMaster1.xml").write_text(
            self._create_master_xml(), encoding="utf-8"
        )

        ppt_rels_dir = ppt_dir / "_rels"
        ppt_rels_dir.mkdir(exist_ok=True)

        ppt_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
</Relationships>"""
        (ppt_rels_dir / "presentation.xml.rels").write_text(ppt_rels, encoding="utf-8")

    def _create_slide_xml(self, title: str = "") -> str:
        """创建幻灯片 XML 内容。"""
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Title 1"/>
          <p:cNvSpPr>
            <a:spLocks noGrp="1"/>
          </p:cNvSpPr>
          <p:nvPr>
            <p:ph type="title"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="zh-CN"/>
              <a:t>{title}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>"""

    def _create_layout_xml(self) -> str:
        """创建幻灯片布局 XML 内容。"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="title">
  <p:cSld name="Title Slide">
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sldLayout>"""

    def _create_master_xml(self) -> str:
        """创建幻灯片母版 XML 内容。"""
        return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap/>
</p:sldMaster>"""

    def _count_slides(self) -> int:
        """计算当前幻灯片数量。"""
        if not self.slides_dir.exists():
            return 0
        return len(list(self.slides_dir.glob("slide*.xml")))

    @property
    def slides_count(self) -> int:
        """当前幻灯片数量。"""
        return self._slides_count

    def add_title_slide(
        self,
        title: str,
        subtitle: str | None = None,
    ) -> int:
        """
        添加标题幻灯片。

        参数:
            title: 幻灯片标题
            subtitle: 副标题 (可选)

        返回:
            int: 新幻灯片的索引 (从 1 开始)

        示例:
            slide_idx = creator.add_title_slide("演示标题", "副标题")
        """
        return self._add_slide_with_content(title, subtitle)

    def add_content_slide(
        self,
        title: str,
        bullet_points: list[str] | None = None,
    ) -> int:
        """
        添加内容幻灯片。

        参数:
            title: 幻灯片标题
            bullet_points: 要点列表 (可选)

        返回:
            int: 新幻灯片的索引 (从 1 开始)

        示例:
            slide_idx = creator.add_content_slide("章节标题", ["要点1", "要点2"])
        """
        return self._add_slide_with_content(title, None, bullet_points)

    def _add_slide_with_content(
        self,
        title: str,
        subtitle: str | None = None,
        bullet_points: list[str] | None = None,
    ) -> int:
        """添加包含内容的幻灯片。"""
        self._slides_count += 1
        slide_num = self._slides_count

        slide_content = self._build_slide_content(title, subtitle, bullet_points)
        slide_path = self.slides_dir / f"slide{slide_num}.xml"
        slide_path.write_text(slide_content, encoding="utf-8")

        self._update_presentation_xml(slide_num)
        self._update_content_types(slide_num)

        return slide_num

    def _build_slide_content(
        self,
        title: str,
        subtitle: str | None,
        bullet_points: list[str] | None,
    ) -> str:
        """构建幻灯片 XML 内容。"""
        shapes = []

        shapes.append(f"""      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Title"/>
          <p:cNvSpPr/>
          <p:nvPr>
            <p:ph type="title"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="zh-CN"/>
              <a:t>{self._escape_xml(title)}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>""")

        if subtitle:
            shapes.append(f"""      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="3" name="Subtitle"/>
          <p:cNvSpPr/>
          <p:nvPr>
            <p:ph type="subTitle"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="zh-CN"/>
              <a:t>{self._escape_xml(subtitle)}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>""")

        if bullet_points:
            bullets_xml = []
            for i, point in enumerate(bullet_points, start=4):
                bullets_xml.append(f"""            <a:p>
              <a:pPr>
                <a:buFont typeface="Arial"/>
                <a:buChar char="•"/>
              </a:pPr>
              <a:r>
                <a:rPr lang="zh-CN"/>
                <a:t>{self._escape_xml(point)}</a:t>
              </a:r>
            </a:p>""")

            shapes.append(f"""      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="4" name="Content"/>
          <p:cNvSpPr/>
          <p:nvPr>
            <p:ph type="body"/>
          </p:nvPr>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
{chr(10).join(bullets_xml)}
        </p:txBody>
      </p:sp>""")

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpProp>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
          <a:chOff x="0" y="0"/>
          <a:chExt cx="0" cy="0"/>
        </a:xfrm>
      </p:grpSpProp>
{chr(10).join(shapes)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr>
    <a:masterClrMapping/>
  </p:clrMapOvr>
</p:sld>"""

    def _escape_xml(self, text: str) -> str:
        """转义 XML 特殊字符。"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def _update_presentation_xml(self, slide_num: int) -> None:
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

    def _update_content_types(self, slide_num: int) -> None:
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
        保存演示文稿到文件。

        参数:
            output_path: 输出文件路径
            validate: 是否验证文档 (默认: False)

        返回:
            bool: 保存成功返回 True

        示例:
            success = creator.save("presentation.pptx")
        """
        return pack_document(self.unpacked_path, output_path, validate=validate)

    def __del__(self):
        """清理临时目录。"""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
