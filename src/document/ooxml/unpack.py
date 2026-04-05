"""
OOXML 文档解包工具

将 Office 文档 (.docx, .pptx, .xlsx) 解压为格式化的 XML 文件，
便于人工阅读和编辑。
"""

import random
import zipfile
from pathlib import Path

import defusedxml.minidom


def unpack_document(
    input_file: str | Path,
    output_dir: str | Path,
    pretty_print: bool = True,
    suggest_rsid: bool = True,
) -> dict:
    """
    解压 Office 文档并格式化 XML 内容。

    参数:
        input_file: Office 文件路径 (.docx/.pptx/.xlsx)
        output_dir: 输出目录路径
        pretty_print: 是否格式化 XML (默认: True)
        suggest_rsid: 是否建议 RSID (仅对 .docx 有效，默认: True)

    返回:
        dict: 包含解压信息的字典，包括:
            - output_path: 解压后的目录路径
            - xml_files: XML 文件列表
            - suggested_rsid: 建议的 RSID (仅 .docx)

    异常:
        ValueError: 如果输入文件不存在或格式不支持

    示例:
        result = unpack_document("document.docx", "unpacked/")
        print(f"解压到: {result['output_path']}")
        print(f"建议 RSID: {result.get('suggested_rsid')}")
    """
    input_file = Path(input_file)
    output_dir = Path(output_dir)

    if not input_file.exists():
        raise ValueError(f"文件不存在: {input_file}")
    if input_file.suffix.lower() not in {".docx", ".pptx", ".xlsx"}:
        raise ValueError(f"不支持的文件格式: {input_file.suffix}")

    output_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_file, "r") as zf:
        zf.extractall(output_dir)

    xml_files = []
    for pattern in ["*.xml", "*.rels"]:
        for xml_file in output_dir.rglob(pattern):
            xml_files.append(str(xml_file.relative_to(output_dir)))
            if pretty_print:
                _pretty_print_xml(xml_file)

    result = {
        "output_path": str(output_dir),
        "xml_files": sorted(xml_files),
    }

    if suggest_rsid and input_file.suffix.lower() == ".docx":
        result["suggested_rsid"] = _generate_rsid()

    return result


def _pretty_print_xml(xml_file: Path) -> None:
    """
    格式化 XML 文件，使其更易于阅读。

    参数:
        xml_file: XML 文件路径
    """
    try:
        content = xml_file.read_text(encoding="utf-8")
        dom = defusedxml.minidom.parseString(content)
        pretty_xml = dom.toprettyxml(indent="  ", encoding="ascii")
        xml_file.write_bytes(pretty_xml)
    except Exception:
        pass


def _generate_rsid() -> str:
    """
    生成随机 8 字符十六进制 RSID。

    RSID 用于标识 Word 文档中的编辑会话。

    返回:
        str: 8 字符十六进制字符串
    """
    return "".join(random.choices("0123456789ABCDEF", k=8))


def get_document_type(unpacked_dir: str | Path) -> str | None:
    """
    根据解压后的目录内容判断文档类型。

    参数:
        unpacked_dir: 解压后的目录路径

    返回:
        str: 文档类型 ("docx", "pptx", "xlsx") 或 None

    示例:
        doc_type = get_document_type("unpacked/")
        print(f"文档类型: {doc_type}")
    """
    unpacked_dir = Path(unpacked_dir)

    if (unpacked_dir / "word" / "document.xml").exists():
        return "docx"
    if (unpacked_dir / "ppt" / "presentation.xml").exists():
        return "pptx"
    if (unpacked_dir / "xl" / "workbook.xml").exists():
        return "xlsx"

    return None


def list_relationships(unpacked_dir: str | Path) -> list[dict]:
    """
    列出文档中的所有关系。

    参数:
        unpacked_dir: 解压后的目录路径

    返回:
        list[dict]: 关系列表，每个元素包含:
            - id: 关系 ID
            - type: 关系类型
            - target: 目标路径

    示例:
        rels = list_relationships("unpacked/")
        for rel in rels:
            print(f"{rel['id']}: {rel['target']}")
    """
    unpacked_dir = Path(unpacked_dir)
    relationships = []

    rels_files = [
        unpacked_dir / "_rels" / ".rels",
        *unpacked_dir.rglob("_rels/*.rels"),
    ]

    for rels_file in rels_files:
        if not rels_file.exists():
            continue

        try:
            content = rels_file.read_text(encoding="utf-8")
            dom = defusedxml.minidom.parseString(content)

            for rel in dom.getElementsByTagName("Relationship"):
                relationships.append({
                    "id": rel.getAttribute("Id"),
                    "type": rel.getAttribute("Type"),
                    "target": rel.getAttribute("Target"),
                    "source": str(rels_file.relative_to(unpacked_dir)),
                })
        except Exception:
            pass

    return relationships
