"""
PowerPoint 幻灯片缩略图生成器

提供将幻灯片转换为图片的功能。
支持生成单个幻灯片图片和缩略图网格。
"""

import subprocess
import tempfile
from pathlib import Path

from src.document.ooxml.unpack import unpack_document


class ThumbnailGenerator:
    """
    PowerPoint 幻灯片缩略图生成器。

    支持将幻灯片转换为图片，生成预览缩略图。

    示例:
        generator = ThumbnailGenerator("presentation.pptx")
        generator.generate_slide_image(1, "slide1.png")
        generator.generate_all_thumbnails("thumbnails/")
    """

    def __init__(self, document_path: str | Path):
        """
        初始化缩略图生成器。

        参数:
            document_path: 演示文稿路径

        示例:
            generator = ThumbnailGenerator("presentation.pptx")
        """
        self.document_path = Path(document_path)

    def generate_slide_image(
        self,
        slide_index: int,
        output_path: str | Path,
        width: int = 1920,
        height: int = 1080,
        format: str = "png",
    ) -> bool:
        """
        生成指定幻灯片的图片。

        使用 LibreOffice 将演示文稿转换为 PDF，然后提取指定页面。

        参数:
            slide_index: 幻灯片索引 (从 1 开始)
            output_path: 输出图片路径
            width: 图片宽度 (默认: 1920)
            height: 图片高度 (默认: 1080)
            format: 图片格式 (默认: png)

        返回:
            bool: 成功返回 True

        示例:
            generator.generate_slide_image(1, "slide1.png")
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)

            try:
                result = subprocess.run(
                    [
                        "soffice",
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(temp_dir),
                        str(self.document_path),
                    ],
                    capture_output=True,
                    timeout=60,
                    text=True,
                )

                pdf_path = temp_dir / f"{self.document_path.stem}.pdf"
                if not pdf_path.exists():
                    return False

                return self._extract_pdf_page(
                    pdf_path, slide_index, output_path, width, height, format
                )

            except FileNotFoundError:
                print("警告: 未找到 LibreOffice (soffice)")
                return False
            except subprocess.TimeoutExpired:
                print("错误: 转换超时")
                return False
            except Exception as e:
                print(f"错误: {e}")
                return False

    def _extract_pdf_page(
        self,
        pdf_path: Path,
        page_index: int,
        output_path: Path,
        width: int,
        height: int,
        format: str,
    ) -> bool:
        """
        从 PDF 提取指定页面并转换为图片。

        参数:
            pdf_path: PDF 文件路径
            page_index: 页面索引 (从 1 开始)
            output_path: 输出图片路径
            width: 图片宽度
            height: 图片高度
            format: 图片格式

        返回:
            bool: 成功返回 True
        """
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(
                str(pdf_path),
                first_page=page_index,
                last_page=page_index,
                dpi=150,
            )

            if not images:
                return False

            image = images[0]
            image = image.resize((width, height))

            if format.lower() == "jpg" or format.lower() == "jpeg":
                image.save(output_path, "JPEG", quality=95)
            else:
                image.save(output_path, format.upper())

            return True

        except ImportError:
            print("警告: 未安装 pdf2image，尝试使用 pdftoppm")
            return self._extract_with_pdftoppm(
                pdf_path, page_index, output_path, width, height, format
            )
        except Exception as e:
            print(f"错误: {e}")
            return False

    def _extract_with_pdftoppm(
        self,
        pdf_path: Path,
        page_index: int,
        output_path: Path,
        width: int,
        height: int,
        format: str,
    ) -> bool:
        """
        使用 pdftoppm 提取 PDF 页面。

        参数:
            pdf_path: PDF 文件路径
            page_index: 页面索引 (从 1 开始)
            output_path: 输出图片路径
            width: 图片宽度
            height: 图片高度
            format: 图片格式

        返回:
            bool: 成功返回 True
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)

                result = subprocess.run(
                    [
                        "pdftoppm",
                        "-f", str(page_index),
                        "-l", str(page_index),
                        "-png",
                        "-r", "150",
                        str(pdf_path),
                        str(temp_dir / "slide"),
                    ],
                    capture_output=True,
                    timeout=30,
                )

                temp_image = temp_dir / f"slide-{page_index}.png"
                if not temp_image.exists():
                    temp_image = temp_dir / f"slide{page_index}.png"

                if not temp_image.exists():
                    return False

                try:
                    from PIL import Image

                    image = Image.open(temp_image)
                    image = image.resize((width, height))

                    if format.lower() == "jpg" or format.lower() == "jpeg":
                        image.save(output_path, "JPEG", quality=95)
                    else:
                        image.save(output_path, format.upper())
                except ImportError:
                    import shutil as sh
                    sh.copy(temp_image, output_path)

                return True

        except FileNotFoundError:
            print("警告: 未找到 pdftoppm")
            return False
        except Exception as e:
            print(f"错误: {e}")
            return False

    def generate_all_thumbnails(
        self,
        output_dir: str | Path,
        width: int = 320,
        height: int = 180,
        format: str = "png",
    ) -> list[Path]:
        """
        生成所有幻灯片的缩略图。

        参数:
            output_dir: 输出目录路径
            width: 缩略图宽度 (默认: 320)
            height: 缩略图高度 (默认: 180)
            format: 图片格式 (默认: png)

        返回:
            list[Path]: 生成的缩略图路径列表

        示例:
            thumbnails = generator.generate_all_thumbnails("thumbnails/")
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        thumbnails = []

        slide_count = self._get_slide_count()

        for i in range(1, slide_count + 1):
            output_path = output_dir / f"slide_{i}.{format}"
            if self.generate_slide_image(i, output_path, width, height, format):
                thumbnails.append(output_path)

        return thumbnails

    def _get_slide_count(self) -> int:
        """
        获取幻灯片数量。

        返回:
            int: 幻灯片数量
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            unpacked_path = Path(temp_dir) / "unpacked"
            unpack_document(self.document_path, unpacked_path, suggest_rsid=False)

            slides_dir = unpacked_path / "ppt" / "slides"
            if not slides_dir.exists():
                return 0

            return len(list(slides_dir.glob("slide*.xml")))

    def generate_thumbnail_grid(
        self,
        output_path: str | Path,
        columns: int = 4,
        thumb_width: int = 320,
        thumb_height: int = 180,
        padding: int = 10,
        background_color: str = "#FFFFFF",
    ) -> bool:
        """
        生成幻灯片缩略图网格。

        参数:
            output_path: 输出图片路径
            columns: 每行列数 (默认: 4)
            thumb_width: 缩略图宽度 (默认: 320)
            thumb_height: 缩略图高度 (默认: 180)
            padding: 间距 (默认: 10)
            background_color: 背景颜色 (默认: 白色)

        返回:
            bool: 成功返回 True

        示例:
            generator.generate_thumbnail_grid("grid.png", columns=4)
        """
        try:
            from PIL import Image

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir = Path(temp_dir)
                thumbnails = self.generate_all_thumbnails(
                    temp_dir, thumb_width, thumb_height
                )

                if not thumbnails:
                    return False

                rows = (len(thumbnails) + columns - 1) // columns

                grid_width = columns * thumb_width + (columns + 1) * padding
                grid_height = rows * thumb_height + (rows + 1) * padding

                grid = Image.new("RGB", (grid_width, grid_height), background_color)

                for i, thumb_path in enumerate(thumbnails):
                    row = i // columns
                    col = i % columns

                    x = padding + col * (thumb_width + padding)
                    y = padding + row * (thumb_height + padding)

                    thumb = Image.open(thumb_path)
                    thumb = thumb.resize((thumb_width, thumb_height))
                    grid.paste(thumb, (x, y))

                grid.save(output_path)
                return True

        except ImportError:
            print("错误: 需要安装 Pillow 库")
            return False
        except Exception as e:
            print(f"错误: {e}")
            return False
