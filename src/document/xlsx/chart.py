"""
Excel 图表管理器

提供在工作簿中创建和管理图表的功能。
支持柱状图、折线图、饼图、散点图等常见图表类型。
"""

import re
import shutil
import tempfile
from pathlib import Path
from typing import ClassVar

import defusedxml.minidom

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document


class ChartManager:
    """
    Excel 图表管理器。

    提供在工作表中创建和管理图表的功能。

    示例:
        manager = ChartManager("workbook.xlsx")
        manager.add_chart(
            sheet_name="数据",
            chart_type="bar",
            data_range="A1:B10",
            title="销售数据"
        )
        manager.save("with_chart.xlsx")
    """

    CHART_TYPES: ClassVar[dict[str, str]] = {
        "bar": "barChart",
        "line": "lineChart",
        "pie": "pieChart",
        "scatter": "scatterChart",
        "area": "areaChart",
        "column": "barChart",
    }

    def __init__(self, document_path: str | Path):
        """
        初始化图表管理器。

        参数:
            document_path: 工作簿文件路径

        示例:
            manager = ChartManager("workbook.xlsx")
        """
        self.document_path = Path(document_path)
        self.temp_dir = tempfile.mkdtemp(prefix="xlsx_chart_manager_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"

        unpack_document(self.document_path, self.unpacked_path, suggest_rsid=False)

        self.xl_dir = self.unpacked_path / "xl"
        self.worksheets_dir = self.xl_dir / "worksheets"
        self.charts_dir = self.xl_dir / "charts"
        self.drawings_dir = self.xl_dir / "drawings"
        self.sheets: dict[str, int] = {}
        self._chart_count = 0
        self._scan_sheets()

    def _scan_sheets(self) -> None:
        """扫描现有工作表。"""
        workbook_path = self.xl_dir / "workbook.xml"
        if not workbook_path.exists():
            return

        try:
            content = workbook_path.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)

            for sheet in dom.getElementsByTagName("sheet"):
                name = sheet.getAttribute("name")
                sheet_id = int(sheet.getAttribute("sheetId"))
                self.sheets[name] = sheet_id
        except Exception:
            pass

        self.charts_dir.mkdir(exist_ok=True)
        self.drawings_dir.mkdir(exist_ok=True)

        existing_charts = list(self.charts_dir.glob("chart*.xml"))
        self._chart_count = len(existing_charts)

    def add_chart(
        self,
        sheet_name: str,
        chart_type: str,
        data_range: str,
        title: str | None = None,
        x_axis_title: str | None = None,
        y_axis_title: str | None = None,
        position: str = "E2",
        width: int = 10,
        height: int = 8,
    ) -> str | None:
        """
        添加图表到工作表。

        参数:
            sheet_name: 工作表名称
            chart_type: 图表类型 (bar, line, pie, scatter, area, column)
            data_range: 数据范围 (如 "A1:B10")
            title: 图表标题 (可选)
            x_axis_title: X 轴标题 (可选)
            y_axis_title: Y 轴标题 (可选)
            position: 图表位置 (默认: E2)
            width: 图表宽度 (默认: 10)
            height: 图表高度 (默认: 8)

        返回:
            str: 图表 ID，失败返回 None

        示例:
            chart_id = manager.add_chart("数据", "bar", "A1:B10", title="销售数据")
        """
        if sheet_name not in self.sheets:
            return None

        if chart_type not in self.CHART_TYPES:
            return None

        self._chart_count += 1
        chart_id = self._chart_count

        self._create_chart_file(
            chart_id, chart_type, data_range,
            title, x_axis_title, y_axis_title
        )

        self._create_drawing_file(sheet_name, chart_id, position, width, height)

        self._update_content_types(chart_id)

        return f"chart{chart_id}"

    def _create_chart_file(
        self,
        chart_id: int,
        chart_type: str,
        data_range: str,
        title: str | None,
        x_axis_title: str | None,
        y_axis_title: str | None,
    ) -> None:
        """创建图表 XML 文件。"""
        chart_type_xml = self.CHART_TYPES[chart_type]
        is_bar = chart_type in ("bar", "column")
        is_pie = chart_type == "pie"

        title_xml = ""
        if title:
            title_xml = f"""<c:title>
    <c:tx>
      <c:rich>
        <a:bodyPr/>
        <a:lstStyle/>
        <a:p>
          <a:r>
            <a:rPr lang="zh-CN"/>
            <a:t>{title}</a:t>
          </a:r>
        </a:p>
      </c:rich>
    </c:tx>
  </c:title>"""

        x_axis_xml = ""
        y_axis_xml = ""
        if not is_pie:
            x_axis_xml = """<c:catAx>
    <c:axId val="1"/>
    <c:scaling/>
    <c:delete val="0"/>
    <c:axPos val="b"/>
    <c:majorTickMark val="out"/>
    <c:minorTickMark val="none"/>
    <c:tickLblPos val="nextTo"/>
    <c:crossAx val="2"/>
    <c:crosses val="autoZero"/>
  </c:catAx>"""
            y_axis_xml = """<c:valAx>
    <c:axId val="2"/>
    <c:scaling/>
    <c:delete val="0"/>
    <c:axPos val="l"/>
    <c:majorTickMark val="out"/>
    <c:minorTickMark val="none"/>
    <c:tickLblPos val="nextTo"/>
    <c:crossAx val="1"/>
    <c:crosses val="autoZero"/>
  </c:valAx>"""

        bar_dir = ""
        if is_bar:
            bar_dir = '<c:barDir val="col"/>' if chart_type == "column" else '<c:barDir val="bar"/>'

        chart_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<c:chartSpace xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <c:chart>
    {title_xml}
    <c:plotArea>
      <c:{chart_type_xml}>
        {bar_dir}
        <c:ser>
          <c:idx val="0"/>
          <c:order val="0"/>
          <c:tx>
            <c:v>系列1</c:v>
          </c:tx>
          <c:cat>
            <c:strRef>
              <c:f>{data_range}</c:f>
            </c:strRef>
          </c:cat>
          <c:val>
            <c:numRef>
              <c:f>{data_range}</c:f>
            </c:numRef>
          </c:val>
        </c:ser>
      </c:{chart_type_xml}>
      {x_axis_xml}
      {y_axis_xml}
    </c:plotArea>
    <c:legend>
      <c:legendPos val="r"/>
    </c:legend>
  </c:chart>
</c:chartSpace>"""

        (self.charts_dir / f"chart{chart_id}.xml").write_text(chart_xml, encoding="utf-8")

    def _create_drawing_file(
        self,
        sheet_name: str,
        chart_id: int,
        position: str,
        width: int,
        height: int,
    ) -> None:
        """创建绘图文件。"""
        sheet_id = self.sheets[sheet_name]

        drawings_rels_dir = self.drawings_dir / "_rels"
        drawings_rels_dir.mkdir(exist_ok=True)

        col = 0
        row = 0
        match = re.match(r"([A-Z]+)(\d+)", position.upper())
        if match:
            col_str, row_str = match.groups()
            row = int(row_str) - 1
            for char in col_str:
                col = col * 26 + (ord(char) - ord("A"))

        drawing_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <xdr:twoCellAnchor>
    <xdr:from>
      <xdr:col>{col}</xdr:col>
      <xdr:colOff>0</xdr:colOff>
      <xdr:row>{row}</xdr:row>
      <xdr:rowOff>0</xdr:rowOff>
    </xdr:from>
    <xdr:to>
      <xdr:col>{col + width}</xdr:col>
      <xdr:colOff>0</xdr:colOff>
      <xdr:row>{row + height}</xdr:row>
      <xdr:rowOff>0</xdr:rowOff>
    </xdr:to>
    <xdr:graphicFrame macro="">
      <xdr:nvGraphicFramePr>
        <xdr:cNvPr id="{chart_id}" name="图表 {chart_id}"/>
      </xdr:nvGraphicFramePr>
      <xdr:xfrm>
        <a:off x="0" y="0"/>
        <a:ext cx="0" cy="0"/>
      </xdr:xfrm>
      <a:graphic>
        <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">
          <c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" r:id="rId1"/>
        </a:graphicData>
      </a:graphic>
    </xdr:graphicFrame>
  </xdr:twoCellAnchor>
</xdr:wsDr>"""

        drawing_path = self.drawings_dir / f"drawing{sheet_id}.xml"
        drawing_path.write_text(drawing_xml, encoding="utf-8")

        drawing_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart{chart_id}.xml"/>
</Relationships>"""

        (drawings_rels_dir / f"drawing{sheet_id}.xml.rels").write_text(drawing_rels, encoding="utf-8")

        self._update_sheet_drawing(sheet_id)

    def _update_sheet_drawing(self, sheet_id: int) -> None:
        """更新工作表的绘图引用。"""
        sheet_path = self.worksheets_dir / f"sheet{sheet_id}.xml"
        if not sheet_path.exists():
            return

        content = sheet_path.read_text(encoding="utf-8")

        if "drawing" not in content:
            drawing_ref = '<drawing r:id="rId1"/>'

            if "</worksheet>" in content:
                content = content.replace("</worksheet>", f"  {drawing_ref}\n</worksheet>")
                sheet_path.write_text(content, encoding="utf-8")

        self._update_sheet_rels(sheet_id)

    def _update_sheet_rels(self, sheet_id: int) -> None:
        """更新工作表关系文件。"""
        sheet_rels_dir = self.worksheets_dir / "_rels"
        sheet_rels_dir.mkdir(exist_ok=True)

        sheet_rels_path = sheet_rels_dir / f"sheet{sheet_id}.xml.rels"

        if sheet_rels_path.exists():
            content = sheet_rels_path.read_text(encoding="utf-8")
        else:
            content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""

        if f"drawing{sheet_id}.xml" not in content:
            new_rel = f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing{sheet_id}.xml"/>'
            content = content.replace("</Relationships>", f"  {new_rel}\n</Relationships>")
            sheet_rels_path.write_text(content, encoding="utf-8")

    def _update_content_types(self, chart_id: int) -> None:
        """更新 Content_Types.xml。"""
        ct_path = self.unpacked_path / "[Content_Types].xml"
        content = ct_path.read_text(encoding="utf-8")

        chart_override = f'<Override PartName="/xl/charts/chart{chart_id}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>'
        drawing_override = f'<Override PartName="/xl/drawings/drawing{chart_id}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>'

        if f"/xl/charts/chart{chart_id}.xml" not in content:
            content = content.replace("</Types>", f"  {chart_override}\n  {drawing_override}\n</Types>")
            ct_path.write_text(content, encoding="utf-8")

    def list_charts(self) -> list[dict]:
        """
        列出所有图表。

        返回:
            list[dict]: 图表信息列表

        示例:
            charts = manager.list_charts()
        """
        charts = []

        for chart_file in self.charts_dir.glob("chart*.xml"):
            try:
                chart_id = int(chart_file.stem.replace("chart", ""))
                charts.append({
                    "id": chart_id,
                    "path": str(chart_file),
                })
            except ValueError:
                continue

        return charts

    def delete_chart(self, chart_id: int) -> bool:
        """
        删除图表。

        参数:
            chart_id: 图表 ID

        返回:
            bool: 成功返回 True

        示例:
            manager.delete_chart(1)
        """
        chart_path = self.charts_dir / f"chart{chart_id}.xml"
        if not chart_path.exists():
            return False

        chart_path.unlink()
        return True

    def save(
        self,
        output_path: str | Path,
        validate: bool = False,
    ) -> bool:
        """
        保存修改后的工作簿。

        参数:
            output_path: 输出文件路径
            validate: 是否验证文档 (默认: False)

        返回:
            bool: 保存成功返回 True

        示例:
            manager.save("with_chart.xlsx")
        """
        return pack_document(self.unpacked_path, output_path, validate=validate)

    def __del__(self):
        """清理临时目录。"""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
