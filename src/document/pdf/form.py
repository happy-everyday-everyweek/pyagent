"""
PyAgent 文档模块 - PDF表单填写器

使用pypdf实现PDF表单字段的提取和填写功能。
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FormFieldInfo:
    """表单字段信息"""
    field_id: str
    field_type: str
    page: int = 0
    rect: tuple[float, float, float, float] | None = None
    value: str = ""
    checked_value: str = ""
    unchecked_value: str = ""
    choice_options: list[dict[str, str]] = field(default_factory=list)
    radio_options: list[dict[str, Any]] = field(default_factory=list)


class PDFFormFiller:
    """PDF表单填写器"""

    def __init__(self):
        self._pypdf_available = self._check_pypdf()

    def _check_pypdf(self) -> bool:
        try:
            from pypdf import PdfReader, PdfWriter
            return True
        except ImportError:
            logger.warning("pypdf未安装，PDF表单填写功能不可用")
            return False

    def extract_fields(self, pdf_path: str) -> list[FormFieldInfo]:
        """
        提取PDF表单字段信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            表单字段信息列表
        """
        if not self._pypdf_available:
            logger.error("pypdf未安装")
            return []

        try:
            from pypdf import PdfReader

            if not Path(pdf_path).exists():
                logger.error("PDF文件不存在")
                return []

            reader = PdfReader(pdf_path)
            fields = reader.get_fields()

            if not fields:
                logger.info("PDF中没有表单字段")
                return []

            field_info_list = []
            possible_radio_names = set()

            for field_id, field in fields.items():
                if field.get("/Kids"):
                    if field.get("/FT") == "/Btn":
                        possible_radio_names.add(field_id)
                    continue

                field_info = self._make_field_dict(field, field_id)
                field_info_list.append(field_info)

            radio_fields = self._extract_radio_fields(reader, possible_radio_names)
            field_info_list.extend(radio_fields)

            for page_index, page in enumerate(reader.pages):
                annotations = page.get("/Annots", [])
                for ann in annotations:
                    field_id = self._get_full_annotation_field_id(ann)
                    for field_info in field_info_list:
                        if field_info.field_id == field_id:
                            field_info.page = page_index + 1
                            field_info.rect = ann.get("/Rect")

            logger.info(f"成功提取 {len(field_info_list)} 个表单字段")
            return field_info_list
        except Exception as e:
            logger.error(f"提取表单字段失败: {e}")
            return []

    def _make_field_dict(self, field: dict, field_id: str) -> FormFieldInfo:
        """创建字段信息对象"""
        field_info = FormFieldInfo(field_id=field_id, field_type="unknown")

        ft = field.get("/FT")
        if ft == "/Tx":
            field_info.field_type = "text"
        elif ft == "/Btn":
            field_info.field_type = "checkbox"
            states = field.get("/_States_", [])
            if len(states) == 2:
                if "/Off" in states:
                    field_info.checked_value = states[0] if states[0] != "/Off" else states[1]
                    field_info.unchecked_value = "/Off"
                else:
                    logger.warning(f"复选框 {field_id} 的状态值异常")
                    field_info.checked_value = states[0]
                    field_info.unchecked_value = states[1]
        elif ft == "/Ch":
            field_info.field_type = "choice"
            states = field.get("/_States_", [])
            field_info.choice_options = [
                {"value": state[0] if isinstance(state, (list, tuple)) and len(state) > 0 else str(state),
                 "text": state[1] if isinstance(state, (list, tuple)) and len(state) > 1 else str(state)}
                for state in states
            ]
        else:
            field_info.field_type = f"unknown ({ft})"

        return field_info

    def _get_full_annotation_field_id(self, annotation: dict) -> str | None:
        """获取完整的字段ID"""
        components = []
        while annotation:
            field_name = annotation.get("/T")
            if field_name:
                components.append(field_name)
            annotation = annotation.get("/Parent")
        return ".".join(reversed(components)) if components else None

    def _extract_radio_fields(self, reader, possible_radio_names: set) -> list[FormFieldInfo]:
        """提取单选按钮组字段"""
        radio_fields = []

        for page_index, page in enumerate(reader.pages):
            annotations = page.get("/Annots", [])
            for ann in annotations:
                field_id = self._get_full_annotation_field_id(ann)
                if field_id in possible_radio_names:
                    try:
                        on_values = [v for v in ann["/AP"]["/N"] if v != "/Off"]
                    except (KeyError, TypeError):
                        continue

                    if len(on_values) == 1:
                        rect = ann.get("/Rect")

                        existing_radio = None
                        for rf in radio_fields:
                            if rf.field_id == field_id:
                                existing_radio = rf
                                break

                        if existing_radio:
                            existing_radio.radio_options.append({
                                "value": on_values[0],
                                "rect": rect,
                            })
                        else:
                            radio_field = FormFieldInfo(
                                field_id=field_id,
                                field_type="radio_group",
                                page=page_index + 1,
                                radio_options=[{
                                    "value": on_values[0],
                                    "rect": rect,
                                }]
                            )
                            radio_fields.append(radio_field)

        return radio_fields

    def fill_fields(self, pdf_path: str, output_path: str, field_values: dict[str, Any]) -> bool:
        """
        填写PDF表单字段
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径
            field_values: 字段值字典 {field_id: value}
            
        Returns:
            是否成功
        """
        if not self._pypdf_available:
            logger.error("pypdf未安装")
            return False

        try:
            from pypdf import PdfReader, PdfWriter

            if not Path(pdf_path).exists():
                logger.error("PDF文件不存在")
                return False

            reader = PdfReader(pdf_path)
            existing_fields = self.extract_fields(pdf_path)
            fields_by_id = {f.field_id: f for f in existing_fields}

            has_error = False
            for field_id, value in field_values.items():
                existing_field = fields_by_id.get(field_id)
                if not existing_field:
                    logger.error(f"字段ID不存在: {field_id}")
                    has_error = True
                    continue

                error = self._validate_field_value(existing_field, value)
                if error:
                    logger.error(error)
                    has_error = True

            if has_error:
                logger.error("字段验证失败，终止填写")
                return False

            self._apply_pypdf_patch()

            writer = PdfWriter(clone_from=reader)

            fields_by_page = {}
            for field_id, value in field_values.items():
                existing_field = fields_by_id.get(field_id)
                if existing_field and existing_field.page > 0:
                    page = existing_field.page
                    if page not in fields_by_page:
                        fields_by_page[page] = {}
                    fields_by_page[page][field_id] = value

            for page, page_field_values in fields_by_page.items():
                writer.update_page_form_field_values(
                    writer.pages[page - 1],
                    page_field_values,
                    auto_regenerate=False
                )

            writer.set_need_appearances_writer(True)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as output:
                writer.write(output)

            logger.info(f"成功填写表单并保存到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"填写表单失败: {e}")
            return False

    def _validate_field_value(self, field_info: FormFieldInfo, value: Any) -> str | None:
        """验证字段值"""
        field_type = field_info.field_type
        field_id = field_info.field_id

        if field_type == "checkbox":
            if value != field_info.checked_value and value != field_info.unchecked_value:
                return f'复选框字段 "{field_id}" 的值无效。选中值: "{field_info.checked_value}"，未选中值: "{field_info.unchecked_value}"'
        elif field_type == "radio_group":
            option_values = [opt["value"] for opt in field_info.radio_options]
            if value not in option_values:
                return f'单选按钮组字段 "{field_id}" 的值无效。有效值: {option_values}'
        elif field_type == "choice":
            choice_values = [opt["value"] for opt in field_info.choice_options]
            if value not in choice_values:
                return f'选择字段 "{field_id}" 的值无效。有效值: {choice_values}'

        return None

    def _apply_pypdf_patch(self):
        """应用pypdf补丁以修复选项字段问题"""
        try:
            from pypdf.constants import FieldDictionaryAttributes
            from pypdf.generic import DictionaryObject

            original_get_inherited = DictionaryObject.get_inherited

            def patched_get_inherited(self, key: str, default=None):
                result = original_get_inherited(self, key, default)
                if key == FieldDictionaryAttributes.Opt:
                    if isinstance(result, list) and all(isinstance(v, list) and len(v) == 2 for v in result):
                        result = [r[0] for r in result]
                return result

            DictionaryObject.get_inherited = patched_get_inherited
        except Exception:
            pass

    def export_fields_to_json(self, pdf_path: str, json_path: str) -> bool:
        """
        导出表单字段信息为JSON文件
        
        Args:
            pdf_path: PDF文件路径
            json_path: 输出JSON文件路径
            
        Returns:
            是否成功
        """
        try:
            fields = self.extract_fields(pdf_path)

            fields_data = []
            for f in fields:
                field_dict = {
                    "field_id": f.field_id,
                    "type": f.field_type,
                    "page": f.page,
                    "rect": list(f.rect) if f.rect else None,
                }

                if f.field_type == "checkbox":
                    field_dict["checked_value"] = f.checked_value
                    field_dict["unchecked_value"] = f.unchecked_value
                elif f.field_type == "choice":
                    field_dict["choice_options"] = f.choice_options
                elif f.field_type == "radio_group":
                    field_dict["radio_options"] = f.radio_options

                fields_data.append(field_dict)

            output_file = Path(json_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(fields_data, f, indent=2, ensure_ascii=False)

            logger.info(f"成功导出 {len(fields)} 个字段到 {json_path}")
            return True
        except Exception as e:
            logger.error(f"导出字段信息失败: {e}")
            return False

    def fill_from_json(self, pdf_path: str, json_path: str, output_path: str) -> bool:
        """
        从JSON文件读取字段值并填写表单
        
        Args:
            pdf_path: PDF文件路径
            json_path: JSON字段值文件路径
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            if not Path(json_path).exists():
                logger.error("JSON文件不存在")
                return False

            with open(json_path, encoding="utf-8") as f:
                fields_data = json.load(f)

            field_values = {}
            for field in fields_data:
                if "value" in field and "field_id" in field:
                    field_values[field["field_id"]] = field["value"]

            return self.fill_fields(pdf_path, output_path, field_values)
        except Exception as e:
            logger.error(f"从JSON填写表单失败: {e}")
            return False
