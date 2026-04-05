"""
PyAgent 执行模块工具系统 - ZIM 文件解析器

解析 ZIM 格式的离线百科文件（如 Wikipedia）。
参考: https://wiki.openzim.org/wiki/ZIM_file_format
"""

import struct
import mmap
import os
from dataclasses import dataclass
from typing import Any, Optional
from pathlib import Path


@dataclass
class ZimHeader:
    """ZIM 文件头信息"""
    magic_number: int
    version: int
    uuid: bytes
    article_count: int
    cluster_count: int
    url_ptr_pos: int
    title_ptr_pos: int
    cluster_ptr_pos: int
    mime_list_pos: int
    main_page_index: int
    layout_page_index: int
    checksum_pos: int


@dataclass
class ZimArticle:
    """ZIM 文章信息"""
    index: int
    url: str
    title: str
    content_type: str
    content: Optional[bytes] = None
    redirect_index: Optional[int] = None


class ZimParser:
    """ZIM 文件解析器"""

    MAGIC_NUMBER = 0x44D495A
    HEADER_SIZE = 80
    MIME_TYPE_MAX = 256

    def __init__(self, zim_path: str):
        self.zim_path = Path(zim_path)
        self._file = None
        self._mmap = None
        self._header: Optional[ZimHeader] = None
        self._mime_types: list[str] = []
        self._url_index: dict[str, int] = {}
        self._title_index: dict[str, int] = {}

    def open(self) -> bool:
        """打开 ZIM 文件"""
        if not self.zim_path.exists():
            return False

        try:
            self._file = open(self.zim_path, "rb")
            self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
            self._parse_header()
            self._parse_mime_types()
            return True
        except Exception:
            self.close()
            return False

    def close(self) -> None:
        """关闭 ZIM 文件"""
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        if self._file:
            self._file.close()
            self._file = None

    def _parse_header(self) -> None:
        """解析 ZIM 文件头"""
        if not self._mmap:
            raise RuntimeError("ZIM file not open")

        header_data = self._mmap[:self.HEADER_SIZE]
        
        magic, version = struct.unpack("<II", header_data[0:8])
        if magic != self.MAGIC_NUMBER:
            raise ValueError(f"Invalid ZIM file: magic number mismatch")

        uuid = header_data[8:24]
        article_count, cluster_count = struct.unpack("<II", header_data[24:32])
        url_ptr_pos, title_ptr_pos = struct.unpack("<QQ", header_data[32:48])
        cluster_ptr_pos, mime_list_pos = struct.unpack("<QQ", header_data[48:64])
        main_page_index, layout_page_index = struct.unpack("<II", header_data[64:72])
        checksum_pos = struct.unpack("<Q", header_data[72:80])[0]

        self._header = ZimHeader(
            magic_number=magic,
            version=version,
            uuid=uuid,
            article_count=article_count,
            cluster_count=cluster_count,
            url_ptr_pos=url_ptr_pos,
            title_ptr_pos=title_ptr_pos,
            cluster_ptr_pos=cluster_ptr_pos,
            mime_list_pos=mime_list_pos,
            main_page_index=main_page_index,
            layout_page_index=layout_page_index,
            checksum_pos=checksum_pos
        )

    def _parse_mime_types(self) -> None:
        """解析 MIME 类型列表"""
        if not self._mmap or not self._header:
            return

        pos = self._header.mime_list_pos
        mime_types = []

        for _ in range(self.MIME_TYPE_MAX):
            end = self._mmap.find(b"\x00", pos)
            if end == -1 or end == pos:
                break
            mime_type = self._mmap[pos:end].decode("utf-8", errors="ignore")
            mime_types.append(mime_type)
            pos = end + 1

        self._mime_types = mime_types

    def _read_offset(self, pos: int) -> int:
        """读取偏移量"""
        if not self._mmap:
            return 0
        return struct.unpack("<Q", self._mmap[pos:pos + 8])[0]

    def _read_directory_entry(self, index: int) -> tuple:
        """读取目录条目"""
        if not self._mmap or not self._header:
            raise RuntimeError("ZIM file not open")

        url_ptr_pos = self._header.url_ptr_pos + index * 8
        entry_pos = self._read_offset(url_ptr_pos)

        cluster_offset = struct.unpack("<Q", self._mmap[entry_pos:entry_pos + 8])[0]
        blob_number = struct.unpack("<I", self._mmap[entry_pos + 8:entry_pos + 12])[0]
        
        redirect_flag = (cluster_offset >> 56) & 0x0F
        cluster_offset = cluster_offset & 0x00FFFFFFFFFFFFFF

        mime_type_idx = struct.unpack("<H", self._mmap[entry_pos + 12:entry_pos + 14])[0]
        
        url_len = self._mmap.find(b"\x00", entry_pos + 16)
        url = self._mmap[entry_pos + 16:url_len].decode("utf-8", errors="ignore") if url_len > entry_pos + 16 else ""
        
        title_start = url_len + 1 if url_len > entry_pos + 16 else entry_pos + 16
        title_len = self._mmap.find(b"\x00", title_start)
        title = self._mmap[title_start:title_len].decode("utf-8", errors="ignore") if title_len > title_start else ""

        mime_type = self._mime_types[mime_type_idx] if mime_type_idx < len(self._mime_types) else "unknown"

        return (
            cluster_offset,
            blob_number,
            redirect_flag,
            mime_type,
            url,
            title
        )

    def get_article_count(self) -> int:
        """获取文章总数"""
        return self._header.article_count if self._header else 0

    def search_articles(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """搜索文章"""
        if not self._mmap or not self._header:
            return []

        results = []
        query_lower = query.lower()

        for i in range(min(self._header.article_count, 10000)):
            try:
                _, _, redirect_flag, mime_type, url, title = self._read_directory_entry(i)
                
                if redirect_flag == 0 and "text/html" in mime_type:
                    if query_lower in title.lower() or query_lower in url.lower():
                        results.append({
                            "index": i,
                            "url": url,
                            "title": title,
                            "content_type": mime_type
                        })
                        if len(results) >= limit:
                            break
            except Exception:
                continue

        return results

    def get_article(self, index: int) -> Optional[ZimArticle]:
        """获取指定索引的文章内容"""
        if not self._mmap or not self._header:
            return None

        try:
            cluster_offset, blob_number, redirect_flag, mime_type, url, title = self._read_directory_entry(index)

            if redirect_flag != 0:
                redirect_index = blob_number
                return ZimArticle(
                    index=index,
                    url=url,
                    title=title,
                    content_type=mime_type,
                    redirect_index=redirect_index
                )

            cluster_data_offset = self._header.cluster_ptr_pos + cluster_offset * 8
            cluster_pos = self._read_offset(cluster_data_offset)

            compression = self._mmap[cluster_pos]
            cluster_pos += 1

            if compression == 0:
                content = self._read_uncompressed_blob(cluster_pos, blob_number)
            elif compression == 4:
                content = self._read_lzma_blob(cluster_pos, blob_number)
            else:
                content = None

            return ZimArticle(
                index=index,
                url=url,
                title=title,
                content_type=mime_type,
                content=content
            )
        except Exception:
            return None

    def _read_uncompressed_blob(self, cluster_pos: int, blob_number: int) -> Optional[bytes]:
        """读取未压缩的 blob"""
        if not self._mmap:
            return None

        offset_pos = cluster_pos + blob_number * 4
        blob_offset = struct.unpack("<I", self._mmap[offset_pos:offset_pos + 4])[0]
        next_offset = struct.unpack("<I", self._mmap[offset_pos + 4:offset_pos + 8])[0]
        
        blob_size = next_offset - blob_offset
        return self._mmap[cluster_pos + blob_offset:cluster_pos + next_offset]

    def _read_lzma_blob(self, cluster_pos: int, blob_number: int) -> Optional[bytes]:
        """读取 LZMA 压缩的 blob（简化实现）"""
        return None

    def get_info(self) -> dict[str, Any]:
        """获取 ZIM 文件信息"""
        if not self._header:
            return {}

        return {
            "path": str(self.zim_path),
            "version": self._header.version,
            "article_count": self._header.article_count,
            "cluster_count": self._header.cluster_count,
            "main_page_index": self._header.main_page_index,
            "file_size": self.zim_path.stat().st_size if self.zim_path.exists() else 0
        }

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
