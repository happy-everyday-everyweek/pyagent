"""
OOXML 文档打包工具

将解压后的目录打包为 .docx、.pptx 或 .xlsx 文件。
支持 XML 格式化还原和文档验证。
"""

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import defusedxml.minidom


def pack_document(
    input_dir: str | Path,
    output_file: str | Path,
    validate: bool = False,
    original_file: str | Path | None = None,
) -> bool:
    """
    将目录打包为 Office 文档 (.docx/.pptx/.xlsx)。

    参数:
        input_dir: 解压后 Office 文档目录的路径
        output_file: 输出 Office 文件的路径
        validate: 如果为 True，使用 soffice 进行验证 (默认: False)
        original_file: 原始文件路径，用于验证比较 (可选)

    返回:
        bool: 成功返回 True，验证失败返回 False

    异常:
        ValueError: 如果输入目录不存在或输出文件格式不支持

    示例:
        success = pack_document("unpacked/", "output.docx", validate=True)
    """
    input_dir = Path(input_dir)
    output_file = Path(output_file)

    if not input_dir.is_dir():
        raise ValueError(f"{input_dir} 不是目录")
    if output_file.suffix.lower() not in {".docx", ".pptx", ".xlsx"}:
        raise ValueError(f"{output_file} 必须是 .docx、.pptx 或 .xlsx 文件")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_content_dir = Path(temp_dir) / "content"
        shutil.copytree(input_dir, temp_content_dir)

        for pattern in ["*.xml", "*.rels"]:
            for xml_file in temp_content_dir.rglob(pattern):
                _condense_xml(xml_file)

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in temp_content_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(temp_content_dir))

        if validate:
            if not _validate_document(output_file):
                output_file.unlink()
                return False

    return True


def _validate_document(doc_path: Path) -> bool:
    """
    通过使用 soffice 转换为 HTML 来验证文档。

    参数:
        doc_path: 文档路径

    返回:
        bool: 验证成功返回 True，失败返回 False
    """
    match doc_path.suffix.lower():
        case ".docx":
            filter_name = "html:HTML"
        case ".pptx":
            filter_name = "html:impress_html_Export"
        case ".xlsx":
            filter_name = "html:HTML (StarCalc)"
        case _:
            return True

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
                    str(doc_path),
                ],
                capture_output=True,
                timeout=30,
                text=True,
            )
            if not (Path(temp_dir) / f"{doc_path.stem}.html").exists():
                error_msg = result.stderr.strip() or "文档验证失败"
                print(f"验证错误: {error_msg}")
                return False
            return True
        except FileNotFoundError:
            print("警告: 未找到 soffice，跳过验证")
            return True
        except subprocess.TimeoutExpired:
            print("验证错误: 转换超时")
            return False
        except Exception as e:
            print(f"验证错误: {e}")
            return False


def _condense_xml(xml_file: Path) -> None:
    """
    移除不必要的空白和注释，压缩 XML 文件。

    参数:
        xml_file: XML 文件路径
    """
    try:
        with open(xml_file, encoding="utf-8") as f:
            dom = defusedxml.minidom.parse(f)

        for element in dom.getElementsByTagName("*"):
            if element.tagName.endswith(":t"):
                continue

            for child in list(element.childNodes):
                if (
                    child.nodeType == child.TEXT_NODE
                    and child.nodeValue
                    and child.nodeValue.strip() == ""
                ) or child.nodeType == child.COMMENT_NODE:
                    element.removeChild(child)

        with open(xml_file, "wb") as f:
            f.write(dom.toxml(encoding="UTF-8"))
    except Exception:
        pass
