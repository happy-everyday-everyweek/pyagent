"""
Excel 工作簿创建器

提供创建新 Excel 工作簿的功能。
支持从模板创建或创建空白工作簿。
"""

import re
import shutil
import tempfile
from pathlib import Path

import defusedxml.minidom

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document


class XlsxCreator:
    """
    Excel 工作簿创建器。

    支持创建空白工作簿或从模板创建，
    提供工作表管理、数据写入等功能。

    示例:
        creator = XlsxCreator()
        creator.add_sheet("数据")
        creator.set_cell("数据", "A1", "标题")
        creator.save("workbook.xlsx")
    """

    def __init__(
        self,
        template_path: str | Path | None = None,
    ):
        """
        初始化工作簿创建器。

        参数:
            template_path: 模板文件路径 (可选)

        示例:
            creator = XlsxCreator()
            creator_from_template = XlsxCreator("template.xlsx")
        """
        self.temp_dir = tempfile.mkdtemp(prefix="xlsx_creator_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"
        self.sheets: dict[str, int] = {}
        self._current_sheet_id = 1

        if template_path:
            unpack_document(template_path, self.unpacked_path, suggest_rsid=False)
        else:
            self._create_blank_workbook()

        self.xl_dir = self.unpacked_path / "xl"
        self.worksheets_dir = self.xl_dir / "worksheets"
        self._scan_sheets()

    def _create_blank_workbook(self) -> None:
        """创建空白工作簿的基础结构。"""
        self.unpacked_path.mkdir(parents=True, exist_ok=True)

        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""
        (self.unpacked_path / "[Content_Types].xml").write_text(content_types, encoding="utf-8")

        rels_dir = self.unpacked_path / "_rels"
        rels_dir.mkdir(exist_ok=True)

        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
        (rels_dir / ".rels").write_text(rels, encoding="utf-8")

        xl_dir = self.unpacked_path / "xl"
        xl_dir.mkdir(exist_ok=True)

        workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""
        (xl_dir / "workbook.xml").write_text(workbook, encoding="utf-8")

        xl_rels_dir = xl_dir / "_rels"
        xl_rels_dir.mkdir(exist_ok=True)

        workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>"""
        (xl_rels_dir / "workbook.xml.rels").write_text(workbook_rels, encoding="utf-8")

        worksheets_dir = xl_dir / "worksheets"
        worksheets_dir.mkdir(exist_ok=True)

        sheet1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
</worksheet>"""
        (worksheets_dir / "sheet1.xml").write_text(sheet1, encoding="utf-8")

        styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1">
    <font>
      <sz val="11"/>
      <name val="Calibri"/>
    </font>
  </fonts>
  <fills count="2">
    <fill>
      <patternFill patternType="none"/>
    </fill>
    <fill>
      <patternFill patternType="gray125"/>
    </fill>
  </fills>
  <borders count="1">
    <border>
      <left/>
      <right/>
      <top/>
      <bottom/>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
  </cellXfs>
</styleSheet>"""
        (xl_dir / "styles.xml").write_text(styles, encoding="utf-8")

        shared_strings = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="0" uniqueCount="0"/>"""
        (xl_dir / "sharedStrings.xml").write_text(shared_strings, encoding="utf-8")

        self.sheets["Sheet1"] = 1
        self._current_sheet_id = 2

    def _scan_sheets(self) -> None:
        """扫描现有工作表。"""
        workbook_path = self.unpacked_path / "xl" / "workbook.xml"
        if not workbook_path.exists():
            return

        try:
            content = workbook_path.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)

            for sheet in dom.getElementsByTagName("sheet"):
                name = sheet.getAttribute("name")
                sheet_id = int(sheet.getAttribute("sheetId"))
                self.sheets[name] = sheet_id
                if sheet_id >= self._current_sheet_id:
                    self._current_sheet_id = sheet_id + 1
        except Exception:
            pass

    def add_sheet(
        self,
        name: str,
        position: int | None = None,
    ) -> int:
        """
        添加新工作表。

        参数:
            name: 工作表名称
            position: 插入位置 (可选，默认添加到最后)

        返回:
            int: 工作表 ID

        示例:
            sheet_id = creator.add_sheet("数据")
        """
        if name in self.sheets:
            raise ValueError(f"工作表 '{name}' 已存在")

        sheet_id = self._current_sheet_id
        self._current_sheet_id += 1
        self.sheets[name] = sheet_id

        worksheets_dir = self.unpacked_path / "xl" / "worksheets"
        worksheets_dir.mkdir(exist_ok=True)

        sheet_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
</worksheet>"""
        (worksheets_dir / f"sheet{sheet_id}.xml").write_text(sheet_xml, encoding="utf-8")

        self._update_workbook_xml(name, sheet_id, position)
        self._update_workbook_rels(sheet_id)
        self._update_content_types(sheet_id)

        return sheet_id

    def _update_workbook_xml(self, name: str, sheet_id: int, position: int | None) -> None:
        """更新 workbook.xml 以包含新工作表。"""
        workbook_path = self.unpacked_path / "xl" / "workbook.xml"
        content = workbook_path.read_text(encoding="utf-8")

        rid = self._get_next_rid()

        new_sheet = f'<sheet name="{name}" sheetId="{sheet_id}" r:id="{rid}"/>'

        if "</sheets>" in content:
            content = content.replace("</sheets>", f"  {new_sheet}\n  </sheets>")
            workbook_path.write_text(content, encoding="utf-8")

    def _get_next_rid(self) -> str:
        """获取下一个关系 ID。"""
        rels_path = self.xl_dir / "_rels" / "workbook.xml.rels"
        if not rels_path.exists():
            return None

        content = rels_path.read_text(encoding="utf-8")
        max_rid = 0

        matches = re.findall(r'Id="(rId\d+)"', content)
        for match in matches:
            rid_num = int(match.replace("rId", ""))
            max_rid = max(max_rid, rid_num)

        return f"rId{max_rid + 1}"

    def _update_workbook_rels(self, sheet_id: int) -> None:
        """更新 workbook.xml.rels 以包含新工作表关系。"""
        rels_path = self.unpacked_path / "xl" / "_rels" / "workbook.xml.rels"
        content = rels_path.read_text(encoding="utf-8")

        rid = self._get_next_rid()
        new_rel = f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{sheet_id}.xml"/>'

        content = content.replace("</Relationships>", f"  {new_rel}\n</Relationships>")
        rels_path.write_text(content, encoding="utf-8")

    def _update_content_types(self, sheet_id: int) -> None:
        """更新 [Content_Types].xml 以包含新工作表。"""
        ct_path = self.unpacked_path / "[Content_Types].xml"
        content = ct_path.read_text(encoding="utf-8")

        new_override = f'<Override PartName="/xl/worksheets/sheet{sheet_id}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'

        if f"/xl/worksheets/sheet{sheet_id}.xml" not in content:
            content = content.replace("</Types>", f"  {new_override}\n</Types>")
            ct_path.write_text(content, encoding="utf-8")

    def set_cell(
        self,
        sheet_name: str,
        cell_ref: str,
        value: str | float | bool,
        formula: str | None = None,
    ) -> bool:
        """
        设置单元格值。

        参数:
            sheet_name: 工作表名称
            cell_ref: 单元格引用 (如 "A1", "B2")
            value: 单元格值
            formula: 公式 (可选)

        返回:
            bool: 成功返回 True

        示例:
            creator.set_cell("Sheet1", "A1", "标题")
            creator.set_cell("数据", "B2", 100)
            creator.set_cell("计算", "C1", 0, formula="=A1+B1")
        """
        if sheet_name not in self.sheets:
            return False

        sheet_id = self.sheets[sheet_name]
        sheet_path = self.unpacked_path / "xl" / "worksheets" / f"sheet{sheet_id}.xml"

        if not sheet_path.exists():
            return False

        try:
            content = sheet_path.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)

            sheet_data = dom.getElementsByTagName("sheetData")
            if not sheet_data:
                sheet_data = dom.createElement("sheetData")
                dom.documentElement.appendChild(sheet_data)
            else:
                sheet_data = sheet_data[0]

            row_num = self._extract_row_num(cell_ref)

            row = self._get_or_create_row(dom, sheet_data, row_num)

            cell = self._get_or_create_cell(dom, row, cell_ref)

            self._set_cell_value(dom, cell, value, formula)

            sheet_path.write_text(dom.toxml(encoding="UTF-8").decode("utf-8"), encoding="utf-8")
            return True

        except Exception:
            return False

    def _extract_row_num(self, cell_ref: str) -> int:
        """从单元格引用提取行号。"""
        match = re.search(r"\d+", cell_ref)
        return int(match.group()) if match else 1

    def _extract_col_num(self, cell_ref: str) -> int:
        """从单元格引用提取列号。"""
        match = re.match(r"([A-Z]+)", cell_ref.upper())
        if not match:
            return 1

        col_str = match.group(1)
        col_num = 0
        for char in col_str:
            col_num = col_num * 26 + (ord(char) - ord("A") + 1)
        return col_num

    def _get_or_create_row(self, dom, sheet_data, row_num: int):
        """获取或创建行元素。"""
        for row in sheet_data.getElementsByTagName("row"):
            if row.getAttribute("r") == str(row_num):
                return row

        row = dom.createElement("row")
        row.setAttribute("r", str(row_num))
        sheet_data.appendChild(row)
        return row

    def _get_or_create_cell(self, dom, row, cell_ref: str):
        """获取或创建单元格元素。"""
        for cell in row.getElementsByTagName("c"):
            if cell.getAttribute("r") == cell_ref.upper():
                return cell

        cell = dom.createElement("c")
        cell.setAttribute("r", cell_ref.upper())
        row.appendChild(cell)
        return cell

    def _set_cell_value(self, dom, cell, value, formula: str | None) -> None:
        """设置单元格值。"""
        if formula:
            cell.setAttribute("t", "str")
            f_elem = dom.createElement("f")
            f_text = dom.createTextNode(formula)
            f_elem.appendChild(f_text)

            for old_f in cell.getElementsByTagName("f"):
                cell.removeChild(old_f)
            cell.appendChild(f_elem)
        elif isinstance(value, str):
            cell.setAttribute("t", "inlineStr")
            for old_v in cell.getElementsByTagName("v"):
                cell.removeChild(old_v)
            for old_is in cell.getElementsByTagName("is"):
                cell.removeChild(old_is)

            is_elem = dom.createElement("is")
            t_elem = dom.createElement("t")
            text = dom.createTextNode(value)
            t_elem.appendChild(text)
            is_elem.appendChild(t_elem)
            cell.appendChild(is_elem)
        elif isinstance(value, bool):
            cell.setAttribute("t", "b")
            for old_v in cell.getElementsByTagName("v"):
                cell.removeChild(old_v)
            v_elem = dom.createElement("v")
            v_text = dom.createTextNode("1" if value else "0")
            v_elem.appendChild(v_text)
            cell.appendChild(v_elem)
        else:
            for old_v in cell.getElementsByTagName("v"):
                cell.removeChild(old_v)
            v_elem = dom.createElement("v")
            v_text = dom.createTextNode(str(value))
            v_elem.appendChild(v_text)
            cell.appendChild(v_elem)

    def save(
        self,
        output_path: str | Path,
        validate: bool = False,
    ) -> bool:
        """
        保存工作簿。

        参数:
            output_path: 输出文件路径
            validate: 是否验证文档 (默认: False)

        返回:
            bool: 保存成功返回 True

        示例:
            creator.save("workbook.xlsx")
        """
        return pack_document(self.unpacked_path, output_path, validate=validate)

    def __del__(self):
        """清理临时目录。"""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
