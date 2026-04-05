"""
PyAgent 文档模块 - PDF合并和拆分器

使用pypdf实现PDF文档的合并和拆分功能。
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFMerger:
    """PDF合并器"""

    def __init__(self):
        self._pypdf_available = self._check_pypdf()

    def _check_pypdf(self) -> bool:
        try:
            from pypdf import PdfReader, PdfWriter
            return True
        except ImportError:
            logger.warning("pypdf未安装，PDF合并功能不可用")
            return False

    def merge_pdfs(self, pdf_files: list[str], output_path: str) -> bool:
        """
        合并多个PDF文件
        
        Args:
            pdf_files: PDF文件路径列表
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """
        if not self._pypdf_available:
            logger.error("pypdf未安装")
            return False

        if not pdf_files:
            logger.error("没有提供PDF文件")
            return False

        try:
            from pypdf import PdfReader, PdfWriter

            writer = PdfWriter()

            for pdf_file in pdf_files:
                if not Path(pdf_file).exists():
                    logger.warning(f"文件不存在: {pdf_file}")
                    continue

                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as output:
                writer.write(output)

            logger.info(f"成功合并 {len(pdf_files)} 个PDF文件到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"合并PDF失败: {e}")
            return False

    def merge_with_metadata(self, pdf_files: list[str], output_path: str, metadata: dict[str, str] | None = None) -> bool:
        """
        合并PDF文件并添加元数据
        
        Args:
            pdf_files: PDF文件路径列表
            output_path: 输出文件路径
            metadata: 元数据字典（title, author, subject等）
            
        Returns:
            是否成功
        """
        if not self._pypdf_available:
            logger.error("pypdf未安装")
            return False

        try:
            from pypdf import PdfReader, PdfWriter

            writer = PdfWriter()

            for pdf_file in pdf_files:
                if not Path(pdf_file).exists():
                    logger.warning(f"文件不存在: {pdf_file}")
                    continue

                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)

            if metadata:
                writer.add_metadata({
                    "/Title": metadata.get("title", ""),
                    "/Author": metadata.get("author", ""),
                    "/Subject": metadata.get("subject", ""),
                    "/Creator": metadata.get("creator", "PyAgent PDF Merger"),
                })

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as output:
                writer.write(output)

            logger.info(f"成功合并PDF并添加元数据到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"合并PDF失败: {e}")
            return False

    def add_watermark(self, pdf_path: str, watermark_path: str, output_path: str) -> bool:
        """
        为PDF添加水印
        
        Args:
            pdf_path: 原PDF文件路径
            watermark_path: 水印PDF文件路径
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """
        if not self._pypdf_available:
            logger.error("pypdf未安装")
            return False

        try:
            from pypdf import PdfReader, PdfWriter

            if not Path(pdf_path).exists() or not Path(watermark_path).exists():
                logger.error("PDF文件或水印文件不存在")
                return False

            watermark = PdfReader(watermark_path).pages[0]
            reader = PdfReader(pdf_path)
            writer = PdfWriter()

            for page in reader.pages:
                page.merge_page(watermark)
                writer.add_page(page)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as output:
                writer.write(output)

            logger.info(f"成功添加水印到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"添加水印失败: {e}")
            return False

    def rotate_pages(self, pdf_path: str, output_path: str, rotation: int = 90, pages: list[int] | None = None) -> bool:
        """
        旋转PDF页面
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径
            rotation: 旋转角度（90, 180, 270）
            pages: 要旋转的页码列表，None表示所有页
            
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
            writer = PdfWriter()

            for idx, page in enumerate(reader.pages):
                if pages is None or (idx + 1) in pages:
                    page.rotate(rotation)
                writer.add_page(page)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as output:
                writer.write(output)

            logger.info(f"成功旋转页面并保存到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"旋转页面失败: {e}")
            return False


class PDFSplitter:
    """PDF拆分器"""

    def __init__(self):
        self._pypdf_available = self._check_pypdf()

    def _check_pypdf(self) -> bool:
        try:
            from pypdf import PdfReader, PdfWriter
            return True
        except ImportError:
            logger.warning("pypdf未安装，PDF拆分功能不可用")
            return False

    def split_by_page(self, pdf_path: str, output_dir: str) -> bool:
        """
        将PDF按页拆分为多个文件
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            
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
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            base_name = Path(pdf_path).stem

            for idx, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)

                output_file = output_path / f"{base_name}_page_{idx + 1}.pdf"
                with open(output_file, "wb") as output:
                    writer.write(output)

            logger.info(f"成功拆分PDF到 {output_dir}，共 {len(reader.pages)} 页")
            return True
        except Exception as e:
            logger.error(f"拆分PDF失败: {e}")
            return False

    def split_by_range(self, pdf_path: str, output_path: str, start_page: int, end_page: int) -> bool:
        """
        按页码范围拆分PDF
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径
            start_page: 起始页码（从1开始）
            end_page: 结束页码（包含）
            
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
            writer = PdfWriter()

            if start_page < 1 or end_page > len(reader.pages) or start_page > end_page:
                logger.error(f"页码范围无效: {start_page}-{end_page}，总页数: {len(reader.pages)}")
                return False

            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as output:
                writer.write(output)

            logger.info(f"成功提取第 {start_page}-{end_page} 页到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"按范围拆分PDF失败: {e}")
            return False

    def split_by_ranges(self, pdf_path: str, output_dir: str, ranges: list[tuple[int, int]]) -> bool:
        """
        按多个页码范围拆分PDF
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            ranges: 页码范围列表，每个元素为(start_page, end_page)
            
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
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            base_name = Path(pdf_path).stem

            for idx, (start_page, end_page) in enumerate(ranges):
                if start_page < 1 or end_page > len(reader.pages) or start_page > end_page:
                    logger.warning(f"跳过无效范围: {start_page}-{end_page}")
                    continue

                writer = PdfWriter()
                for page_num in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[page_num])

                output_file = output_path / f"{base_name}_part{idx + 1}_p{start_page}-{end_page}.pdf"
                with open(output_file, "wb") as output:
                    writer.write(output)

            logger.info(f"成功按范围拆分PDF到 {output_dir}")
            return True
        except Exception as e:
            logger.error(f"按多个范围拆分PDF失败: {e}")
            return False

    def extract_pages(self, pdf_path: str, output_path: str, pages: list[int]) -> bool:
        """
        提取指定页面
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出文件路径
            pages: 要提取的页码列表（从1开始）
            
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
            writer = PdfWriter()

            for page_num in pages:
                if 0 < page_num <= len(reader.pages):
                    writer.add_page(reader.pages[page_num - 1])
                else:
                    logger.warning(f"跳过无效页码: {page_num}")

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as output:
                writer.write(output)

            logger.info(f"成功提取 {len(pages)} 页到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"提取页面失败: {e}")
            return False

    def get_page_count(self, pdf_path: str) -> int:
        """
        获取PDF页数
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            页数
        """
        if not self._pypdf_available:
            logger.error("pypdf未安装")
            return 0

        try:
            from pypdf import PdfReader

            if not Path(pdf_path).exists():
                logger.error("PDF文件不存在")
                return 0

            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception as e:
            logger.error(f"获取页数失败: {e}")
            return 0
