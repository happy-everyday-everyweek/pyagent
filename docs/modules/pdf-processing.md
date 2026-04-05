# PyAgent PDF 处理系统

**版本**: v0.8.0  
**模块路径**: `src/pdf/`  
**最后更新**: 2025-04-03

---

## 概述

PDF 处理系统是 PyAgent v0.8.0 引入的全新模块，提供完整的 PDF 文档解析、提取和转换功能。基于 PyMuPDF (fitz) 实现，支持文本提取、表格识别、图片提取、元数据读取等高级功能。

### 核心特性

- **文本提取**: 精确提取 PDF 文本内容和位置信息
- **表格识别**: 自动识别和提取 PDF 中的表格数据
- **图片提取**: 提取 PDF 中的图片资源
- **元数据读取**: 读取标题、作者、创建日期等元数据
- **大纲解析**: 提取 PDF 书签和目录结构
- **多格式支持**: 支持从文件或字节数据解析

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    PDF Processing System                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 PDFParser                           │   │
│  │                                                     │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐       │   │
│  │  │   Text    │  │   Table   │  │   Image   │       │   │
│  │  │ Extraction│  │Extraction │  │ Extraction│       │   │
│  │  └───────────┘  └───────────┘  └───────────┘       │   │
│  │                                                     │   │
│  │  ┌───────────┐  ┌───────────┐                      │   │
│  │  │  Outline  │  │  Metadata │                      │   │
│  │  │Extraction │  │  Reading  │                      │   │
│  │  └───────────┘  └───────────┘                      │   │
│  └─────────────────────────────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 PDFDocument                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ PDFPage  │  │   Table  │  │   Image  │          │   │
│  │  │  (页面)  │  │  (表格)  │  │  (图片)  │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. PDF 解析器 (PDFParser)

**位置**: `src/pdf/parser.py`

```python
from src.pdf.parser import PDFParser, pdf_parser

# 使用全局实例
parser = pdf_parser

# 或创建新实例
parser = PDFParser()
```

#### 主要方法

| 方法 | 功能 | 返回值 |
|------|------|--------|
| `parse()` | 解析 PDF 文件 | `PDFDocument \| None` |
| `parse_bytes()` | 解析 PDF 字节数据 | `PDFDocument \| None` |
| `get_page_count()` | 获取页数 | `int` |
| `get_page()` | 获取指定页面 | `PDFPage \| None` |
| `get_metadata()` | 获取元数据 | `dict` |
| `get_outline()` | 获取大纲 | `list[OutlineItem]` |

---

### 2. 数据模型

#### PDFDocument

```python
@dataclass
class PDFDocument:
    file_path: str              # 文件路径
    page_count: int             # 页数
    metadata: dict              # 元数据
    pages: list[PDFPage]        # 页面列表
    outline: list[OutlineItem]  # 大纲/书签
    tables: list[Table]         # 所有表格
    images: list[Image]         # 所有图片
```

#### PDFPage

```python
@dataclass
class PDFPage:
    page_num: int               # 页码
    width: float                # 页面宽度
    height: float               # 页面高度
    text: str                   # 页面文本
    blocks: list[TextBlock]     # 文本块列表
    tables: list[Table]         # 页面表格
    images: list[Image]         # 页面图片
```

#### TextBlock

```python
@dataclass
class TextBlock:
    x: float            # X 坐标
    y: float            # Y 坐标
    width: float        # 宽度
    height: float       # 高度
    text: str           # 文本内容
    font_name: str      # 字体名称
    font_size: float    # 字体大小
```

#### Table

```python
@dataclass
class Table:
    page_num: int               # 所在页码
    x: int                      # X 坐标
    y: int                      # Y 坐标
    rows: int                   # 行数
    cols: int                   # 列数
    data: list[list[str]]       # 表格数据
    bbox: tuple[float, ...]     # 边界框
```

#### Image

```python
@dataclass
class Image:
    page_num: int       # 所在页码
    x: int              # X 坐标
    y: int              # Y 坐标
    width: int          # 宽度
    height: int         # 高度
    format: str         # 格式
    data: bytes         # 图片数据
```

#### OutlineItem

```python
@dataclass
class OutlineItem:
    title: str                  # 标题
    level: int                  # 层级
    page_num: int               # 目标页码
    children: list[OutlineItem] # 子项
```

---

## 使用示例

### 基础文本提取

```python
from src.pdf.parser import PDFParser

parser = PDFParser()

# 解析 PDF
doc = parser.parse("document.pdf")
if doc:
    print(f"页数: {doc.page_count}")
    
    # 提取所有文本
    full_text = "\n".join(page.text for page in doc.pages)
    print(full_text)
    
    # 提取单页文本
    first_page = doc.pages[0]
    print(f"第一页文本:\n{first_page.text}")
```

### 表格提取

```python
from src.pdf.parser import PDFParser

parser = PDFParser()
doc = parser.parse("report.pdf")

if doc and doc.tables:
    print(f"找到 {len(doc.tables)} 个表格")
    
    for i, table in enumerate(doc.tables):
        print(f"\n表格 {i+1} (第 {table.page_num} 页):")
        print(f"尺寸: {table.rows} 行 x {table.cols} 列")
        
        for row in table.data:
            print(" | ".join(row))
```

### 图片提取

```python
from src.pdf.parser import PDFParser
import os

parser = PDFParser()
doc = parser.parse("document.pdf")

if doc and doc.images:
    os.makedirs("extracted_images", exist_ok=True)
    
    for i, img in enumerate(doc.images):
        if img.data:
            filename = f"extracted_images/image_{i}.{img.format}"
            with open(filename, "wb") as f:
                f.write(img.data)
            print(f"已保存: {filename}")
```

### 元数据读取

```python
from src.pdf.parser import PDFParser

parser = PDFParser()
doc = parser.parse("document.pdf")

if doc:
    metadata = doc.metadata
    print(f"""
PDF 元数据:
===========
标题: {metadata.get('title', 'N/A')}
作者: {metadata.get('author', 'N/A')}
主题: {metadata.get('subject', 'N/A')}
创建者: {metadata.get('creator', 'N/A')}
生产者: {metadata.get('producer', 'N/A')}
创建日期: {metadata.get('creationDate', 'N/A')}
""")
```

### 大纲/书签提取

```python
from src.pdf.parser import PDFParser

parser = PDFParser()
doc = parser.parse("book.pdf")

def print_outline(items, indent=0):
    for item in items:
        print("  " * indent + f"- {item.title} (第 {item.page_num} 页)")
        if item.children:
            print_outline(item.children, indent + 1)

if doc and doc.outline:
    print("目录结构:")
    print_outline(doc.outline)
```

### 从字节数据解析

```python
from src.pdf.parser import PDFParser

parser = PDFParser()

# 从网络或数据库读取 PDF 数据
with open("document.pdf", "rb") as f:
    pdf_bytes = f.read()

# 解析字节数据
doc = parser.parse_bytes(pdf_bytes)
if doc:
    print(f"成功解析 PDF，共 {doc.page_count} 页")
```

---

## API 接口

### REST API

#### 上传并解析 PDF
```http
POST /api/pdf/parse
Content-Type: multipart/form-data

file: <document.pdf>
```

#### 提取文本
```http
POST /api/pdf/extract-text
Content-Type: multipart/form-data

file: <document.pdf>
page: 1  # 可选，指定页码
```

#### 提取表格
```http
POST /api/pdf/extract-tables
Content-Type: multipart/form-data

file: <document.pdf>
```

#### 提取图片
```http
POST /api/pdf/extract-images
Content-Type: multipart/form-data

file: <document.pdf>
```

---

## 配置选项

```yaml
# config/pdf.yaml
pdf:
  extraction:
    text:
      preserve_layout: true    # 保留布局
      extract_blocks: true     # 提取文本块
    tables:
      enabled: true            # 启用表格提取
      min_rows: 2              # 最小行数
      min_cols: 2              # 最小列数
    images:
      enabled: true            # 启用图片提取
      min_size: 1024           # 最小图片大小（字节）
```

---

## 依赖安装

```bash
# 安装 PyMuPDF (fitz)
pip install PyMuPDF

# 或安装完整依赖
pip install pymupdf pandas
```

---

## 最佳实践

### 1. 大文件处理

```python
from src.pdf.parser import PDFParser

parser = PDFParser()

# 逐页处理大文件
doc = parser.parse("large.pdf")
for page in doc.pages:
    # 处理每一页
    process_page(page)
    # 及时释放内存
    del page
```

### 2. 错误处理

```python
from src.pdf.parser import PDFParser

parser = PDFParser()

try:
    doc = parser.parse("document.pdf")
    if doc is None:
        print("PDF 解析失败")
    else:
        process_document(doc)
except Exception as e:
    print(f"处理 PDF 时出错: {e}")
```

### 3. 文本块位置分析

```python
from src.pdf.parser import PDFParser

parser = PDFParser()
doc = parser.parse("document.pdf")

if doc:
    for page in doc.pages:
        for block in page.blocks:
            # 根据位置判断内容类型
            if block.y < 100:  # 页面顶部
                print(f"页眉: {block.text}")
            elif block.y > page.height - 100:  # 页面底部
                print(f"页脚: {block.text}")
            else:
                print(f"正文: {block.text}")
```

---

## 故障排除

### 常见问题

**Q: PyMuPDF 未安装？**  
A: 运行 `pip install PyMuPDF`

**Q: 中文显示乱码？**  
A: 确保 PDF 使用标准字体，或安装相应字体包。

**Q: 表格识别不准确？**  
A: 复杂表格可能需要手动调整或使用专门的表格识别工具。

---

## 更新日志

### v0.8.0 (2025-04-03)

- 初始版本发布
- 支持文本提取
- 支持表格识别
- 支持图片提取
- 支持元数据读取
- 支持大纲解析

---

## 相关文档

- [PyMuPDF 文档](https://pymupdf.readthedocs.io/)
- [API 文档](../api.md) - 完整 API 参考
