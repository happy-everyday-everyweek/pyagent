"""
Excel 工作表管理器

提供工作表的添加、删除、重命名、复制等管理功能。
"""

import re
import shutil
import tempfile
from pathlib import Path

import defusedxml.minidom

from src.document.ooxml.pack import pack_document
from src.document.ooxml.unpack import unpack_document


class SheetManager:
    """
    Excel 工作表管理器。

    提供工作表的增删改查和重排功能。

    示例:
        manager = SheetManager("workbook.xlsx")
        manager.rename_sheet("Sheet1", "数据")
        manager.move_sheet("数据", 0)
        manager.save("managed.xlsx")
    """

    def __init__(self, document_path: str | Path):
        """
        初始化工作表管理器。

        参数:
            document_path: 工作簿文件路径

        示例:
            manager = SheetManager("workbook.xlsx")
        """
        self.document_path = Path(document_path)
        self.temp_dir = tempfile.mkdtemp(prefix="xlsx_sheet_manager_")
        self.unpacked_path = Path(self.temp_dir) / "unpacked"

        unpack_document(self.document_path, self.unpacked_path, suggest_rsid=False)

        self.xl_dir = self.unpacked_path / "xl"
        self.worksheets_dir = self.xl_dir / "worksheets"
        self.sheets: dict[str, int] = {}
        self._sheet_order: list[str] = []
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
                self._sheet_order.append(name)
        except Exception:
            pass

    def list_sheets(self) -> list[dict]:
        """
        列出所有工作表信息。

        返回:
            list[dict]: 工作表信息列表，每个元素包含:
                - name: 工作表名称
                - sheet_id: 工作表 ID
                - index: 位置索引

        示例:
            sheets = manager.list_sheets()
        """
        result = []
        for i, name in enumerate(self._sheet_order):
            if name in self.sheets:
                result.append({
                    "name": name,
                    "sheet_id": self.sheets[name],
                    "index": i,
                })
        return result

    def add_sheet(
        self,
        name: str,
        position: int | None = None,
    ) -> bool:
        """
        添加新工作表。

        参数:
            name: 工作表名称
            position: 插入位置 (可选)

        返回:
            bool: 成功返回 True

        示例:
            manager.add_sheet("新工作表")
        """
        if name in self.sheets:
            return False

        new_id = max(self.sheets.values(), default=0) + 1
        self.sheets[name] = new_id

        if position is not None and 0 <= position < len(self._sheet_order):
            self._sheet_order.insert(position, name)
        else:
            self._sheet_order.append(name)

        self._create_sheet_file(new_id)
        self._update_workbook_xml()

        return True

    def _create_sheet_file(self, sheet_id: int) -> None:
        """创建新工作表文件。"""
        self.worksheets_dir.mkdir(exist_ok=True)

        sheet_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData/>
</worksheet>"""
        (self.worksheets_dir / f"sheet{sheet_id}.xml").write_text(sheet_xml, encoding="utf-8")

        self._update_content_types(sheet_id)
        self._update_workbook_rels(sheet_id)

    def _update_content_types(self, sheet_id: int) -> None:
        """更新 Content_Types.xml。"""
        ct_path = self.unpacked_path / "[Content_Types].xml"
        content = ct_path.read_text(encoding="utf-8")

        new_override = f'<Override PartName="/xl/worksheets/sheet{sheet_id}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'

        if f"/xl/worksheets/sheet{sheet_id}.xml" not in content:
            content = content.replace("</Types>", f"  {new_override}\n</Types>")
            ct_path.write_text(content, encoding="utf-8")

    def _update_workbook_rels(self, sheet_id: int) -> None:
        """更新 workbook.xml.rels。"""
        rels_path = self.xl_dir / "_rels" / "workbook.xml.rels"
        if not rels_path.exists():
            rels_path.parent.mkdir(exist_ok=True)
            rels_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>"""
            rels_path.write_text(rels_content, encoding="utf-8")

        content = rels_path.read_text(encoding="utf-8")

        matches = re.findall(r'Id="(rId\d+)"', content)
        max_rid = max([int(m.replace("rId", "")) for m in matches], default=0)

        rid = f"rId{max_rid + 1}"
        new_rel = f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{sheet_id}.xml"/>'

        content = content.replace("</Relationships>", f"  {new_rel}\n</Relationships>")
        rels_path.write_text(content, encoding="utf-8")

    def _update_workbook_xml(self) -> None:
        """更新 workbook.xml。"""
        workbook_path = self.xl_dir / "workbook.xml"
        content = workbook_path.read_text(encoding="utf-8")

        dom = defusedxml.minidom.parseString(content)

        sheets_elem = dom.getElementsByTagName("sheets")
        if not sheets_elem:
            return

        sheets_elem = sheets_elem[0]

        for child in list(sheets_elem.childNodes):
            if child.nodeType == child.ELEMENT_NODE:
                sheets_elem.removeChild(child)

        rels_path = self.xl_dir / "_rels" / "workbook.xml.rels"
        rels_content = rels_path.read_text(encoding="utf-8")

        rid_map = {}
        for match in re.finditer(r'Id="(rId\d+)".*Target="worksheets/sheet(\d+)\.xml"', rels_content):
            rid, sheet_id = match.groups()
            rid_map[int(sheet_id)] = rid

        for i, name in enumerate(self._sheet_order):
            if name in self.sheets:
                sheet_id = self.sheets[name]
                rid = rid_map.get(sheet_id, f"rId{i + 1}")

                sheet_elem = dom.createElement("sheet")
                sheet_elem.setAttribute("name", name)
                sheet_elem.setAttribute("sheetId", str(sheet_id))
                sheet_elem.setAttribute("r:id", rid)
                sheets_elem.appendChild(sheet_elem)

        workbook_path.write_text(dom.toxml(encoding="UTF-8").decode("utf-8"), encoding="utf-8")

    def delete_sheet(self, name: str) -> bool:
        """
        删除工作表。

        参数:
            name: 工作表名称

        返回:
            bool: 成功返回 True

        示例:
            manager.delete_sheet("Sheet1")
        """
        if name not in self.sheets:
            return False

        if len(self._sheet_order) <= 1:
            return False

        sheet_id = self.sheets[name]
        del self.sheets[name]
        self._sheet_order.remove(name)

        sheet_path = self.worksheets_dir / f"sheet{sheet_id}.xml"
        if sheet_path.exists():
            sheet_path.unlink()

        self._update_workbook_xml()

        return True

    def rename_sheet(
        self,
        old_name: str,
        new_name: str,
    ) -> bool:
        """
        重命名工作表。

        参数:
            old_name: 原名称
            new_name: 新名称

        返回:
            bool: 成功返回 True

        示例:
            manager.rename_sheet("Sheet1", "数据")
        """
        if old_name not in self.sheets:
            return False

        if new_name in self.sheets:
            return False

        sheet_id = self.sheets[old_name]
        del self.sheets[old_name]
        self.sheets[new_name] = sheet_id

        index = self._sheet_order.index(old_name)
        self._sheet_order[index] = new_name

        self._update_workbook_xml()

        return True

    def move_sheet(
        self,
        name: str,
        new_position: int,
    ) -> bool:
        """
        移动工作表位置。

        参数:
            name: 工作表名称
            new_position: 新位置索引

        返回:
            bool: 成功返回 True

        示例:
            manager.move_sheet("数据", 0)
        """
        if name not in self.sheets:
            return False

        if new_position < 0 or new_position >= len(self._sheet_order):
            return False

        current_position = self._sheet_order.index(name)
        self._sheet_order.pop(current_position)
        self._sheet_order.insert(new_position, name)

        self._update_workbook_xml()

        return True

    def copy_sheet(
        self,
        source_name: str,
        new_name: str,
        position: int | None = None,
    ) -> bool:
        """
        复制工作表。

        参数:
            source_name: 源工作表名称
            new_name: 新工作表名称
            position: 插入位置 (可选)

        返回:
            bool: 成功返回 True

        示例:
            manager.copy_sheet("数据", "数据副本")
        """
        if source_name not in self.sheets:
            return False

        if new_name in self.sheets:
            return False

        source_id = self.sheets[source_name]
        new_id = max(self.sheets.values()) + 1

        source_path = self.worksheets_dir / f"sheet{source_id}.xml"
        if source_path.exists():
            new_path = self.worksheets_dir / f"sheet{new_id}.xml"
            shutil.copy(source_path, new_path)

        self.sheets[new_name] = new_id

        if position is not None and 0 <= position < len(self._sheet_order):
            self._sheet_order.insert(position, new_name)
        else:
            self._sheet_order.append(new_name)

        self._update_content_types(new_id)
        self._update_workbook_rels(new_id)
        self._update_workbook_xml()

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
            manager.save("managed.xlsx")
        """
        return pack_document(self.unpacked_path, output_path, validate=validate)

    def __del__(self):
        """清理临时目录。"""
        if hasattr(self, "temp_dir"):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
