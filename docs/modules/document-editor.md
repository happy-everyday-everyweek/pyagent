# 原生文档编辑器文档 v0.8.12

本文档详细描述 PyAgent v0.8.12 原生文档编辑器的设计和实现，支持 Word/Excel/PPT/PDF 的完整处理功能。

## 概述

v0.8.12 集成完整的文档处理功能，参考 openakita 项目迁移：

- Word 文档创建、编辑、批注、修订跟踪
- PowerPoint 演示文稿创建、编辑、幻灯片管理
- PDF 文本提取、表格提取、合并拆分、表单填写、OCR
- OOXML 文档底层操作（打包、解包、验证）
- ONLYOFFICE Docs 在线编辑集成

## 架构设计

```
src/document/
├── __init__.py           # 模块入口
├── manager.py            # 文档管理器（CRUD、格式转换、版本管理）
├── types.py              # 类型定义
├── metadata.py           # 元数据管理
├── connector.py          # ONLYOFFICE 连接器
├── tools.py              # 统一工具接口
├── docx/                 # Word 处理模块
│   ├── __init__.py
│   ├── editor.py         # 文档编辑器
│   ├── creator.py        # 文档创建器
│   ├── comment.py        # 批注管理器
│   ├── revision.py       # 修订跟踪器
│   ├── converter.py      # 格式转换器
│   └── utilities.py      # XML 编辑器
├── pptx/                 # PowerPoint 处理模块
│   ├── __init__.py
│   ├── creator.py        # 演示文稿创建器
│   ├── editor.py         # 演示文稿编辑器
│   ├── slide.py          # 幻灯片管理器
│   └── thumbnail.py      # 缩略图生成器
├── pdf/                  # PDF 处理模块
│   ├── __init__.py
│   ├── extractor.py      # 文本/表格提取器
│   ├── merger.py         # 合并/拆分器
│   ├── form.py           # 表单填写器
│   └── ocr.py            # OCR 处理器
└── ooxml/                # OOXML 工具模块
    ├── __init__.py
    ├── pack.py           # 打包工具
    ├── unpack.py         # 解包工具
    └── validate.py       # 验证工具
```

## 核心功能

### 1. Word 文档处理

#### 文档编辑器

```python
from src.document import Document

# 打开文档
doc = Document("document.docx")

# 获取所有文本
text = doc.get_all_text()

# 查找并替换
doc.find_replace("旧文本", "新文本")

# 保存文档
doc.save("edited.docx")
```

#### 批注管理

```python
from src.document import CommentManager

manager = CommentManager("document.docx")

# 添加批注
comment_id = manager.add_comment(
    text="这是批注内容",
    author="张三",
    target_text="目标文本"
)

# 获取所有批注
comments = manager.get_comments()

# 回复批注
manager.reply_to_comment(comment_id, "回复内容")

# 删除批注
manager.delete_comment(comment_id)
```

#### 修订跟踪

```python
from src.document import RevisionManager

manager = RevisionManager("document.docx")

# 获取所有修订
revisions = manager.get_revisions()

# 接受修订
manager.accept_revision(revision_id)

# 拒绝修订
manager.reject_revision(revision_id)

# 接受所有修订
manager.accept_all_revisions()
```

### 2. PowerPoint 演示文稿处理

#### 创建演示文稿

```python
from src.document import PptxCreator

creator = PptxCreator()

# 添加标题幻灯片
creator.add_title_slide("演示标题", "副标题")

# 添加内容幻灯片
creator.add_content_slide("章节标题", ["要点1", "要点2", "要点3"])

# 保存演示文稿
creator.save("presentation.pptx")
```

#### 编辑演示文稿

```python
from src.document import PptxEditor

editor = PptxEditor("presentation.pptx")

# 查找文本元素
elements = editor.find_text_elements(1)

# 修改文本
editor.set_text(1, "Title 1", "新标题")

# 复制幻灯片
new_idx = editor.duplicate_slide(1)

# 删除幻灯片
editor.delete_slide(2)

# 保存
editor.save("edited.pptx")
```

#### 幻灯片管理

```python
from src.document import SlideManager

manager = SlideManager("presentation.pptx")

# 列出幻灯片
slides = manager.list_slides()

# 移动幻灯片
manager.move_slide(1, 3)

# 从其他演示文稿复制幻灯片
manager.copy_slide_to("source.pptx", 1, 2)

# 保存
manager.save("reordered.pptx")
```

#### 缩略图生成

```python
from src.document import ThumbnailGenerator

generator = ThumbnailGenerator("presentation.pptx")

# 生成单个幻灯片图片
generator.generate_slide_image(1, "slide1.png")

# 生成所有缩略图
thumbnails = generator.generate_all_thumbnails("thumbnails/")

# 生成缩略图网格
generator.generate_thumbnail_grid("grid.png", columns=4)
```

### 3. Excel 文档处理

#### 创建工作簿

```python
from src.document import XlsxCreator

creator = XlsxCreator()

# 添加工作表
creator.add_sheet("数据")

# 设置单元格值
creator.set_cell("Sheet1", "A1", "标题")
creator.set_cell("数据", "B2", 100)
creator.set_cell("计算", "C1", 0, formula="=A1+B1")

# 保存工作簿
creator.save("workbook.xlsx")
```

#### 编辑工作簿

```python
from src.document import XlsxEditor

editor = XlsxEditor("workbook.xlsx")

# 列出工作表
sheets = editor.list_sheets()

# 获取单元格值
value = editor.get_cell("Sheet1", "A1")

# 获取范围数据
data = editor.get_range("Sheet1", "A1", "C3")

# 设置单元格值
editor.set_cell("Sheet1", "D1", "合计")

# 查找单元格
cells = editor.find_cells("Sheet1", "查找内容")

# 保存
editor.save("edited.xlsx")
```

#### 工作表管理

```python
from src.document import SheetManager

manager = SheetManager("workbook.xlsx")

# 列出工作表
sheets = manager.list_sheets()

# 重命名工作表
manager.rename_sheet("Sheet1", "数据")

# 添加工作表
manager.add_sheet("分析", position=0)

# 删除工作表
manager.delete_sheet("Sheet2")

# 移动工作表
manager.move_sheet("数据", 0)

# 复制工作表
manager.copy_sheet("数据", "数据副本")

# 保存
manager.save("managed.xlsx")
```

#### 图表管理

```python
from src.document import ChartManager

manager = ChartManager("workbook.xlsx")

# 添加图表
chart_id = manager.add_chart(
    sheet_name="数据",
    chart_type="bar",  # bar, line, pie, scatter, area, column
    data_range="A1:B10",
    title="销售数据",
    x_axis_title="月份",
    y_axis_title="销售额",
    position="E2",
    width=10,
    height=8
)

# 列出图表
charts = manager.list_charts()

# 删除图表
manager.delete_chart(1)

# 保存
manager.save("with_chart.xlsx")
```

### 4. PDF 文档处理

#### 文本和表格提取

```python
from src.document import PDFExtractor, TextExtractor, TableExtractor

# 统一接口
extractor = PDFExtractor()
result = extractor.extract("document.pdf")
print(result.text)
print(result.tables)

# 单独使用文本提取器
text_extractor = TextExtractor()
text = text_extractor.extract_text("document.pdf")
pages = text_extractor.extract_by_page("document.pdf")

# 单独使用表格提取器
table_extractor = TableExtractor()
tables = table_extractor.extract_tables("document.pdf")
table_extractor.export_to_excel(tables, "tables.xlsx")
```

#### 合并和拆分

```python
from src.document import PDFMerger, PDFSplitter

# 合并 PDF
merger = PDFMerger()
merger.merge_pdfs(["file1.pdf", "file2.pdf"], "merged.pdf")
merger.merge_with_metadata(
    ["file1.pdf", "file2.pdf"],
    "merged.pdf",
    title="合并文档",
    author="张三"
)

# 拆分 PDF
splitter = PDFSplitter()
splitter.split_by_page("input.pdf", "output_dir/")
splitter.split_by_range("input.pdf", [(1, 5), (6, 10)], "output_dir/")
```

#### 表单填写

```python
from src.document import PDFFormFiller

filler = PDFFormFiller()

# 提取表单字段
fields = filler.extract_fields("form.pdf")
for field in fields:
    print(f"{field.name}: {field.field_type}")

# 填写表单
filler.fill_fields("form.pdf", "filled.pdf", {
    "name": "张三",
    "email": "zhangsan@example.com",
    "agree": True
})

# 导出字段信息
filler.export_fields_json("form.pdf", "fields.json")
```

#### OCR 支持

```python
from src.document import PDFOCRProcessor

ocr = PDFOCRProcessor()

# OCR 识别
text = ocr.ocr_pdf("scanned.pdf", language="chi_sim+eng")

# 判断是否为扫描件
is_scanned = ocr.is_scanned("document.pdf")

# 获取可用语言
languages = ocr.get_available_languages()
```

### 4. OOXML 工具

#### 打包和解包

```python
from src.document import pack_document, unpack_document

# 解包文档
result = unpack_document("document.docx", "unpacked/")
print(f"解压到: {result['output_path']}")
print(f"XML 文件: {result['xml_files']}")

# 编辑 XML 文件...

# 打包文档
pack_document("unpacked/", "edited.docx", validate=True)
```

#### 文档验证

```python
from src.document import validate_document

# 验证文档
valid, errors = validate_document("document.docx")
if not valid:
    for error in errors:
        print(f"错误: {error}")
```

### 5. 文档管理器

```python
from src.document import DocumentManager, DocumentType

manager = DocumentManager()

# 创建文档
metadata = manager.create_document(
    document_type=DocumentType.WORD,
    name="我的文档",
    author="张三",
    tags=["重要", "工作"]
)

# 获取文档
doc = manager.get_document(metadata.document_id)

# 格式转换
output = manager.convert_document(metadata.document_id, "pdf")

# 批注管理
comments = manager.get_document_comments(metadata.document_id)
manager.add_document_comment(metadata.document_id, "这是批注")

# 修订管理
revisions = manager.get_document_revisions(metadata.document_id)
manager.accept_revision(metadata.document_id, revision_id)

# 版本管理
version_id = manager.create_version_snapshot(metadata.document_id, "重要修改")
versions = manager.list_versions(metadata.document_id)
manager.restore_version(metadata.document_id, version_id)
```

## API 接口

### Word 文档 API

```http
POST /api/documents/word/create
Content-Type: application/json

{
  "name": "新文档",
  "template": "blank"
}
```

```http
POST /api/documents/word/{document_id}/comments
Content-Type: application/json

{
  "text": "批注内容",
  "author": "张三",
  "target_text": "目标文本"
}
```

### PowerPoint API

```http
POST /api/documents/ppt/create
Content-Type: application/json

{
  "name": "新演示文稿",
  "template": "blank"
}
```

```http
POST /api/documents/ppt/{document_id}/slides
Content-Type: application/json

{
  "title": "幻灯片标题",
  "bullet_points": ["要点1", "要点2"]
}
```

### PDF API

```http
POST /api/documents/pdf/extract
Content-Type: application/json

{
  "file_path": "document.pdf",
  "extract_tables": true
}
```

```http
POST /api/documents/pdf/merge
Content-Type: application/json

{
  "files": ["file1.pdf", "file2.pdf"],
  "output_path": "merged.pdf"
}
```

## 配置文件

### 文档配置

```yaml
# config/document.yaml

onlyoffice:
  enabled: true
  document_server_url: "http://localhost:8080"
  jwt_secret: "${ONLYOFFICE_JWT_SECRET}"

pdf:
  ocr_enabled: true
  ocr_language: "chi_sim+eng"
  default_dpi: 150

conversion:
  libreoffice_path: "soffice"
  timeout: 60
```

## 依赖要求

### Python 包

```
pypdf>=4.0.0
pdfplumber>=0.10.0
reportlab>=4.0.0
defusedxml>=0.7.0
python-docx>=1.1.0
python-pptx>=0.6.23
pytesseract>=0.3.10
pdf2image>=1.16.0
Pillow>=10.0.0
```

### 外部工具（可选）

- **LibreOffice**: 文档格式转换
- **Tesseract**: OCR 文字识别
- **poppler-utils**: PDF 命令行工具

## 故障排除

### LibreOffice 连接失败

**现象**: 格式转换失败
**解决**:
1. 检查 LibreOffice 是否安装
2. 验证 `soffice` 命令是否可用
3. 检查超时设置

### OCR 识别失败

**现象**: OCR 无结果
**解决**:
1. 检查 Tesseract 是否安装
2. 验证语言包是否安装
3. 检查图片质量

### PDF 提取失败

**现象**: 无法提取文本或表格
**解决**:
1. 检查 PDF 是否加密
2. 验证 PDF 是否为扫描件
3. 尝试使用 OCR

## 最佳实践

1. **大文件处理**: 分批处理大型 PDF 文件
2. **内存管理**: 及时释放文档对象
3. **错误处理**: 捕获并处理异常
4. **版本管理**: 重要修改前创建版本快照
5. **格式兼容**: 导出前检查格式兼容性
