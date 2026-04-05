"""
Excel 工作簿编辑器

提供对现有 Excel 工作簿的编辑功能。
支持读取、修改单元格数据和格式。
"""

import re
import shutil
import tempfile
from pathlib import Path

import defusedxml.minidom

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document


class XlsxEditor:
    """
    Excel 工作簿编辑器。

    提供对现有工作簿的编辑功能，包括读取和修改单元格、
    管理工作表、设置格式等。

    示例:
        editor = XlsxEditor("workbook.xlsx")
        value = editor.get_cell("Sheet1", "A1")
        editor.set_cell("Sheet1", "B1", 100)
        editor.save("edited.xlsx")
    """

    def __init__(self, document_path: str | Path):
        """
        初始化工作簿编辑器。

        参数:
            document_path: 工作簿文件路径

        示例:
            editor = XlsxEditor("workbook.xlsx")
        """
        self.document_path = Path(document_path)
        self.temp_dir = tempfile.mkdtemp(prefix="xlsx_editor_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"

        unpack_document(self.document_path, self.unpacked_path, suggest_rsid=False)

        self.xl_dir = self.unpacked_path / "xl"
        self.worksheets_dir = self.xl_dir / "worksheets"
        self.sheets: dict[str, int] = {}
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

    def list_sheets(self) -> list[str]:
        """
        列出所有工作表名称。

        返回:
            list[str]: 工作表名称列表

        示例:
            sheets = editor.list_sheets()
        """
        return list(self.sheets.keys())

    def get_cell(
        self,
        sheet_name: str,
        cell_ref: str,
    ) -> str | int | float | bool | None:
        """
        获取单元格值。

        参数:
            sheet_name: 工作表名称
            cell_ref: 单元格引用 (如 "A1", "B2")

        返回:
            单元格值，如果不存在返回 None

        示例:
            value = editor.get_cell("Sheet1", "A1")
        """
        if sheet_name not in self.sheets:
            return None

        sheet_id = self.sheets[sheet_name]
        sheet_path = self.worksheets_dir / f"sheet{sheet_id}.xml"

        if not sheet_path.exists():
            return None

        try:
            content = sheet_path.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)

            for row in dom.getElementsByTagName("row"):
                for cell in row.getElementsByTagName("c"):
                    if cell.getAttribute("r") == cell_ref.upper():
                        return self._extract_cell_value(cell)

            return None

        except Exception:
            return None

    def _extract_cell_value(self, cell) -> str | int | float | bool | None:
        """从单元格元素提取值。"""
        cell_type = cell.getAttribute("t")

        if cell_type == "inlineStr":
            is_elem = cell.getElementsByTagName("is")
            if is_elem:
                t_elem = is_elem[0].getElementsByTagName("t")
                if t_elem and t_elem[0].firstChild:
                    return t_elem[0].firstChild.nodeValue
        elif cell_type == "b":
            v_elem = cell.getElementsByTagName("v")
            if v_elem and v_elem[0].firstChild:
                return v_elem[0].firstChild.nodeValue == "1"
        elif cell_type == "str":
            f_elem = cell.getElementsByTagName("f")
            if f_elem and f_elem[0].firstChild:
                return f"={f_elem[0].firstChild.nodeValue}"
            v_elem = cell.getElementsByTagName("v")
            if v_elem and v_elem[0].firstChild:
                return v_elem[0].firstChild.nodeValue
        else:
            v_elem = cell.getElementsByTagName("v")
            if v_elem and v_elem[0].firstChild:
                value = v_elem[0].firstChild.nodeValue
                try:
                    if "." in value:
                        return float(value)
                    return int(value)
                except ValueError:
                    return value

        return None

    def get_range(
        self,
        sheet_name: str,
        start_cell: str,
        end_cell: str,
    ) -> list[list[str | int | float | bool | None]]:
        """
        获取单元格范围的值。

        参数:
            sheet_name: 工作表名称
            start_cell: 起始单元格 (如 "A1")
            end_cell: 结束单元格 (如 "C3")

        返回:
            list[list]: 二维数组，每行是一个列表

        示例:
            values = editor.get_range("Sheet1", "A1", "C3")
        """

        def parse_cell(cell: str) -> tuple[int, int]:
            match = re.match(r"([A-Z]+)(\d+)", cell.upper())
            if not match:
                return (1, 1)
            col_str, row_str = match.groups()

            col = 0
            for char in col_str:
                col = col * 26 + (ord(char) - ord("A") + 1)

            return (int(row_str), col)

        start_row, start_col = parse_cell(start_cell)
        end_row, end_col = parse_cell(end_cell)

        result = []
        for row in range(start_row, end_row + 1):
            row_values = []
            for col in range(start_col, end_col + 1):
                col_letter = ""
                c = col
                while c > 0:
                    c -= 1
                    col_letter = chr(ord("A") + c % 26) + col_letter
                    c //= 26
                cell_ref = f"{col_letter}{row}"
                row_values.append(self.get_cell(sheet_name, cell_ref))
            result.append(row_values)

        return result

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
            cell_ref: 单元格引用
            value: 单元格值
            formula: 公式 (可选)

        返回:
            bool: 成功返回 True

        示例:
            editor.set_cell("Sheet1", "A1", "标题")
        """
        if sheet_name not in self.sheets:
            return False

        sheet_id = self.sheets[sheet_name]
        sheet_path = self.worksheets_dir / f"sheet{sheet_id}.xml"

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

            match = re.search(r"\d+", cell_ref)
            row_num = int(match.group()) if match else 1

            row = None
            for r in sheet_data.getElementsByTagName("row"):
                if r.getAttribute("r") == str(row_num):
                    row = r
                    break

            if not row:
                row = dom.createElement("row")
                row.setAttribute("r", str(row_num))
                sheet_data.appendChild(row)

            cell = None
            for c in row.getElementsByTagName("c"):
                if c.getAttribute("r") == cell_ref.upper():
                    cell = c
                    break

            if not cell:
                cell = dom.createElement("c")
                cell.setAttribute("r", cell_ref.upper())
                row.appendChild(cell)

            self._set_cell_value(dom, cell, value, formula)

            sheet_path.write_text(dom.toxml(encoding="UTF-8").decode("utf-8"), encoding="utf-8")
            return True

        except Exception:
            return False

    def _set_cell_value(self, dom, cell, value, formula: str | None) -> None:
        """设置单元格值。"""
        for child in list(cell.childNodes):
            cell.removeChild(child)

        if formula:
            cell.setAttribute("t", "str")
            f_elem = dom.createElement("f")
            f_text = dom.createTextNode(formula)
            f_elem.appendChild(f_text)
            cell.appendChild(f_elem)
        elif isinstance(value, str):
            cell.setAttribute("t", "inlineStr")
            is_elem = dom.createElement("is")
            t_elem = dom.createElement("t")
            text = dom.createTextNode(value)
            t_elem.appendChild(text)
            is_elem.appendChild(t_elem)
            cell.appendChild(is_elem)
        elif isinstance(value, bool):
            cell.setAttribute("t", "b")
            v_elem = dom.createElement("v")
            v_text = dom.createTextNode("1" if value else "0")
            v_elem.appendChild(v_text)
            cell.appendChild(v_elem)
        else:
            v_elem = dom.createElement("v")
            v_text = dom.createTextNode(str(value))
            v_elem.appendChild(v_text)
            cell.appendChild(v_elem)

    def find_cells(
        self,
        sheet_name: str,
        search_value: str,
    ) -> list[str]:
        """
        查找包含指定值的单元格。

        参数:
            sheet_name: 工作表名称
            search_value: 要查找的值

        返回:
            list[str]: 匹配的单元格引用列表

        示例:
            cells = editor.find_cells("Sheet1", "查找内容")
        """
        if sheet_name not in self.sheets:
            return []

        sheet_id = self.sheets[sheet_name]
        sheet_path = self.worksheets_dir / f"sheet{sheet_id}.xml"

        if not sheet_path.exists():
            return []

        matches = []

        try:
            content = sheet_path.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)

            for row in dom.getElementsByTagName("row"):
                for cell in row.getElementsByTagName("c"):
                    cell_ref = cell.getAttribute("r")
                    value = self._extract_cell_value(cell)
                    if value is not None and str(value) == search_value:
                        matches.append(cell_ref)

        except Exception:
            pass

        return matches

    def save(
        self,
        output_path: str | Path,
        validate: bool = False,
    ) -> bool:
        """
        保存编辑后的工作簿。

        参数:
            output_path: 输出文件路径
            validate: 是否验证文档 (默认: False)

        返回:
            bool: 保存成功返回 True

        示例:
            editor.save("edited.xlsx")
        """
        return pack_document(self.unpacked_path, output_path, validate=validate)

    def __del__(self):
        """清理临时目录。"""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
