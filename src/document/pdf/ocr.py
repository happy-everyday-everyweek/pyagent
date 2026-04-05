"""
PyAgent 文档模块 - PDF OCR处理器

使用pytesseract和pdf2image实现扫描PDF的OCR识别功能。
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PDFOCRProcessor:
    """PDF OCR处理器"""

    def __init__(self):
        self._pytesseract_available = self._check_pytesseract()
        self._pdf2image_available = self._check_pdf2image()

    def _check_pytesseract(self) -> bool:
        try:
            import pytesseract
            return True
        except ImportError:
            logger.warning("pytesseract未安装，OCR功能不可用")
            return False

    def _check_pdf2image(self) -> bool:
        try:
            from pdf2image import convert_from_path
            return True
        except ImportError:
            logger.warning("pdf2image未安装，PDF转图片功能不可用")
            return False

    def ocr_pdf(self, pdf_path: str, language: str = "chi_sim+eng", pages: list[int] | None = None) -> str:
        """
        对PDF进行OCR识别
        
        Args:
            pdf_path: PDF文件路径
            language: OCR语言（如 "chi_sim" 中文简体, "eng" 英文, "chi_sim+eng" 中英文）
            pages: 要识别的页码列表，None表示所有页
            
        Returns:
            识别的文本内容
        """
        if not self._pytesseract_available or not self._pdf2image_available:
            logger.error("pytesseract或pdf2image未安装")
            return ""

        try:
            import pytesseract
            from pdf2image import convert_from_path

            if not Path(pdf_path).exists():
                logger.error("PDF文件不存在")
                return ""

            logger.info(f"开始OCR处理: {pdf_path}")

            dpi = 200
            images = convert_from_path(pdf_path, dpi=dpi)

            if pages:
                images = [images[i] for i in range(len(images)) if i + 1 in pages]

            text_parts = []
            for idx, image in enumerate(images):
                page_num = idx + 1 if not pages else pages[idx]
                logger.info(f"正在处理第 {page_num} 页...")

                page_text = pytesseract.image_to_string(image, lang=language)
                text_parts.append(f"=== 第 {page_num} 页 ===\n{page_text}")

            result = "\n\n".join(text_parts)
            logger.info(f"OCR处理完成，共识别 {len(images)} 页")
            return result
        except Exception as e:
            logger.error(f"OCR处理失败: {e}")
            return ""

    def ocr_pdf_to_file(self, pdf_path: str, output_path: str, language: str = "chi_sim+eng") -> bool:
        """
        对PDF进行OCR识别并保存为文本文件
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文本文件路径
            language: OCR语言
            
        Returns:
            是否成功
        """
        text = self.ocr_pdf(pdf_path, language)

        if not text:
            logger.error("OCR识别失败，没有生成文本")
            return False

        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            logger.info(f"OCR结果已保存到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存OCR结果失败: {e}")
            return False

    def ocr_page(self, pdf_path: str, page_num: int, language: str = "chi_sim+eng") -> str:
        """
        对PDF的单页进行OCR识别
        
        Args:
            pdf_path: PDF文件路径
            page_num: 页码（从1开始）
            language: OCR语言
            
        Returns:
            识别的文本内容
        """
        return self.ocr_pdf(pdf_path, language, pages=[page_num])

    def pdf_to_images(self, pdf_path: str, output_dir: str, max_dim: int = 1000, dpi: int = 200) -> bool:
        """
        将PDF转换为图片
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            max_dim: 图片最大尺寸（宽度或高度）
            dpi: 转换DPI
            
        Returns:
            是否成功
        """
        if not self._pdf2image_available:
            logger.error("pdf2image未安装")
            return False

        try:
            from pdf2image import convert_from_path

            if not Path(pdf_path).exists():
                logger.error("PDF文件不存在")
                return False

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            images = convert_from_path(pdf_path, dpi=dpi)

            for idx, image in enumerate(images):
                width, height = image.size
                if width > max_dim or height > max_dim:
                    scale_factor = min(max_dim / width, max_dim / height)
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    image = image.resize((new_width, new_height))

                image_file = output_path / f"page_{idx + 1}.png"
                image.save(image_file)
                logger.info(f"保存第 {idx + 1} 页到 {image_file}")

            logger.info(f"成功转换 {len(images)} 页到 {output_dir}")
            return True
        except Exception as e:
            logger.error(f"PDF转图片失败: {e}")
            return False

    def ocr_image(self, image_path: str, language: str = "chi_sim+eng") -> str:
        """
        对图片进行OCR识别
        
        Args:
            image_path: 图片文件路径
            language: OCR语言
            
        Returns:
            识别的文本内容
        """
        if not self._pytesseract_available:
            logger.error("pytesseract未安装")
            return ""

        try:
            import pytesseract
            from PIL import Image

            if not Path(image_path).exists():
                logger.error("图片文件不存在")
                return ""

            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=language)

            logger.info(f"图片OCR识别完成: {image_path}")
            return text
        except Exception as e:
            logger.error(f"图片OCR识别失败: {e}")
            return ""

    def ocr_with_coordinates(self, pdf_path: str, language: str = "chi_sim+eng") -> list[dict[str, Any]]:
        """
        对PDF进行OCR识别并返回文本坐标
        
        Args:
            pdf_path: PDF文件路径
            language: OCR语言
            
        Returns:
            文本块列表，每个元素包含文本和坐标信息
        """
        if not self._pytesseract_available or not self._pdf2image_available:
            logger.error("pytesseract或pdf2image未安装")
            return []

        try:
            import pytesseract
            from pdf2image import convert_from_path

            if not Path(pdf_path).exists():
                logger.error("PDF文件不存在")
                return []

            dpi = 200
            images = convert_from_path(pdf_path, dpi=dpi)

            all_blocks = []
            for page_idx, image in enumerate(images):
                page_num = page_idx + 1
                width, height = image.size

                data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)

                for i in range(len(data["text"])):
                    text = data["text"][i].strip()
                    if text:
                        block = {
                            "page": page_num,
                            "text": text,
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "width": data["width"][i],
                            "height": data["height"][i],
                            "confidence": data["conf"][i],
                        }
                        all_blocks.append(block)

            logger.info(f"OCR识别完成，共提取 {len(all_blocks)} 个文本块")
            return all_blocks
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return []

    def is_scanned_pdf(self, pdf_path: str, text_threshold: int = 100) -> bool:
        """
        判断PDF是否为扫描件
        
        Args:
            pdf_path: PDF文件路径
            text_threshold: 文本字符数阈值，低于此值认为是扫描件
            
        Returns:
            是否为扫描件
        """
        try:
            import pdfplumber

            if not Path(pdf_path).exists():
                logger.error("PDF文件不存在")
                return False

            total_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    total_text += text

            is_scanned = len(total_text.strip()) < text_threshold
            logger.info(f"PDF文本长度: {len(total_text.strip())}，判断为{'扫描件' if is_scanned else '正常PDF'}")
            return is_scanned
        except Exception as e:
            logger.warning(f"判断PDF类型失败: {e}")
            return False

    def get_available_languages(self) -> list[str]:
        """
        获取可用的OCR语言列表
        
        Returns:
            语言代码列表
        """
        if not self._pytesseract_available:
            logger.error("pytesseract未安装")
            return []

        try:
            import pytesseract
            langs = pytesseract.get_languages()
            logger.info(f"可用的OCR语言: {langs}")
            return langs
        except Exception as e:
            logger.error(f"获取OCR语言列表失败: {e}")
            return []
