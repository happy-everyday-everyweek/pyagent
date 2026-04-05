"""
OOXML 文档验证工具

提供 Office 文档的 XML 模式验证功能。
支持 DOCX、PPTX、XLSX 文档的验证。
"""

import subprocess
import tempfile
from pathlib import Path

import defusedxml.minidom


def validate_document(
    document_path: str | Path,
    verbose: bool = False,
) -> tuple[bool, list[str]]:
    """
    验证 Office 文档的结构和内容。

    参数:
        document_path: Office 文档路径
        verbose: 是否输出详细信息

    返回:
        tuple[bool, list[str]]: (是否有效, 错误消息列表)

    示例:
        valid, errors = validate_document("document.docx")
        if not valid:
            for error in errors:
                print(f"错误: {error}")
    """
    document_path = Path(document_path)
    errors = []

    if not document_path.exists():
        return False, [f"文件不存在: {document_path}"]

    suffix = document_path.suffix.lower()
    if suffix not in {".docx", ".pptx", ".xlsx"}:
        return False, [f"不支持的文件格式: {suffix}"]

    try:
        import zipfile
        with zipfile.ZipFile(document_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".xml") or name.endswith(".rels"):
                    try:
                        content = zf.read(name)
                        defusedxml.minidom.parseString(content)
                    except Exception as e:
                        errors.append(f"XML 解析错误 ({name}): {e}")
    except zipfile.BadZipFile:
        errors.append("无效的 ZIP 文件格式")
        return False, errors
    except Exception as e:
        errors.append(f"文件读取错误: {e}")
        return False, errors

    if errors:
        return False, errors

    return True, []


def validate_xml_schema(
    xml_path: str | Path,
    schema_path: str | Path | None = None,
) -> tuple[bool, list[str]]:
    """
    验证 XML 文件是否符合指定的模式。

    参数:
        xml_path: XML 文件路径
        schema_path: XSD 模式文件路径 (可选)

    返回:
        tuple[bool, list[str]]: (是否有效, 错误消息列表)

    示例:
        valid, errors = validate_xml_schema("document.xml", "schema.xsd")
    """
    xml_path = Path(xml_path)
    errors = []

    if not xml_path.exists():
        return False, [f"XML 文件不存在: {xml_path}"]

    try:
        content = xml_path.read_text(encoding="utf-8")
        defusedxml.minidom.parseString(content)
    except Exception as e:
        errors.append(f"XML 解析错误: {e}")
        return False, errors

    if schema_path:
        schema_path = Path(schema_path)
        if not schema_path.exists():
            errors.append(f"模式文件不存在: {schema_path}")
            return False, errors

    return True, []


def validate_with_libreoffice(
    document_path: str | Path,
    timeout: int = 30,
) -> tuple[bool, list[str]]:
    """
    使用 LibreOffice 验证文档。

    通过尝试将文档转换为 HTML 来验证其有效性。

    参数:
        document_path: Office 文档路径
        timeout: 超时时间（秒）

    返回:
        tuple[bool, list[str]]: (是否有效, 错误消息列表)

    示例:
        valid, errors = validate_with_libreoffice("document.docx")
    """
    document_path = Path(document_path)
    errors = []

    if not document_path.exists():
        return False, [f"文件不存在: {document_path}"]

    suffix = document_path.suffix.lower()
    match suffix:
        case ".docx":
            filter_name = "html:HTML"
        case ".pptx":
            filter_name = "html:impress_html_Export"
        case ".xlsx":
            filter_name = "html:HTML (StarCalc)"
        case _:
            return False, [f"不支持的文件格式: {suffix}"]

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to",
                    filter_name,
                    "--outdir",
                    temp_dir,
                    str(document_path),
                ],
                capture_output=True,
                timeout=timeout,
                text=True,
            )

            output_file = Path(temp_dir) / f"{document_path.stem}.html"
            if not output_file.exists():
                error_msg = result.stderr.strip() or "文档验证失败"
                errors.append(error_msg)
                return False, errors

            return True, []

        except FileNotFoundError:
            errors.append("未找到 LibreOffice (soffice)，请确保已安装")
            return False, errors
        except subprocess.TimeoutExpired:
            errors.append(f"验证超时 ({timeout}秒)")
            return False, errors
        except Exception as e:
            errors.append(f"验证错误: {e}")
            return False, errors


def check_document_structure(
    document_path: str | Path,
) -> tuple[bool, list[str], dict]:
    """
    检查 Office 文档的基本结构。

    验证文档是否包含必需的文件和目录。

    参数:
        document_path: Office 文档路径

    返回:
        tuple[bool, list[str], dict]: (是否有效, 错误消息列表, 结构信息)

    示例:
        valid, errors, info = check_document_structure("document.docx")
        print(f"文档类型: {info.get('type')}")
        print(f"文件数量: {info.get('file_count')}")
    """
    document_path = Path(document_path)
    errors = []
    info = {"file_count": 0, "xml_files": 0, "type": None}

    if not document_path.exists():
        return False, [f"文件不存在: {document_path}"], info

    suffix = document_path.suffix.lower()
    required_files = []

    match suffix:
        case ".docx":
            required_files = ["word/document.xml", "[Content_Types].xml"]
            info["type"] = "docx"
        case ".pptx":
            required_files = ["ppt/presentation.xml", "[Content_Types].xml"]
            info["type"] = "pptx"
        case ".xlsx":
            required_files = ["xl/workbook.xml", "[Content_Types].xml"]
            info["type"] = "xlsx"
        case _:
            return False, [f"不支持的文件格式: {suffix}"], info

    try:
        import zipfile
        with zipfile.ZipFile(document_path, "r") as zf:
            names = zf.namelist()
            info["file_count"] = len(names)
            info["xml_files"] = sum(1 for n in names if n.endswith(".xml"))

            for req_file in required_files:
                if req_file not in names:
                    errors.append(f"缺少必需文件: {req_file}")

    except zipfile.BadZipFile:
        errors.append("无效的 ZIP 文件格式")
    except Exception as e:
        errors.append(f"文件读取错误: {e}")

    return len(errors) == 0, errors, info
