# 文档编辑器集成规范

## Why

PyAgent 项目现有的文档编辑器模块 (`src/document/`) 仅提供基础的文档管理功能和 ONLYOFFICE 连接器，缺少完整的文档创建、编辑和分析能力。需要将 openakita 项目中的完整文档处理功能迁移过来，实现 Word/Excel/PPT/PDF 的全功能支持。

## What Changes

### 新增模块

* **DOCX 处理模块** (`src/document/docx/`)

  * 文档创建（基于 docx-js）

  * 文档编辑（解包→编辑XML→打包）

  * 批注管理

  * 修订跟踪

  * 文档验证

  * 格式转换

* **PPTX 处理模块** (`src/document/pptx/`)

  * 演示文稿创建（基于 pptxgenjs）

  * 幻灯片管理

  * 缩略图生成

  * 设计模板

* **PDF 处理模块** (`src/document/pdf/`)

  * 文本提取

  * 表格提取

  * PDF 合并/拆分

  * 表单填写

  * OCR 支持

* **OOXML 工具模块** (`src/document/ooxml/`)

  * XML 编辑器

  * 模式验证

  * 打包/解包工具

### 增强现有模块

* **文档管理器** (`src/document/manager.py`)

  * 增加格式转换支持

  * 增加批注和修订管理

* **文档工具** (`src/document/tools.py`)

  * 增加高级编辑操作

  * 增加 AI 辅助功能集成

* **Web 路由** (`src/web/routes/document_routes.py`)

  * 增加完整的 REST API

  * 增加文件上传/下载

## Impact

* **受影响的模块**: `src/document/`, `src/web/routes/`, `src/tools/`

* **新增依赖**: `pypdf`, `pdfplumber`, `reportlab`, `defusedxml`, `python-docx` (可选)

* **外部工具**: `pandoc`, `LibreOffice` (可选), `poppler-utils`

## ADDED Requirements

### Requirement: DOCX 文档处理

系统应提供完整的 Word 文档处理能力。

#### Scenario: 创建新文档

* **WHEN** 用户请求创建 Word 文档

* **THEN** 系统使用 docx-js 或 python-docx 创建格式正确的文档

* **AND** 支持设置页面大小、边距、字体样式

* **AND** 支持添加标题、段落、列表、表格、图片

#### Scenario: 编辑现有文档

* **WHEN** 用户请求编辑 Word 文档

* **THEN** 系统解包文档为 XML

* **AND** 提供 XML 编辑接口

* **AND** 重新打包为有效文档

#### Scenario: 管理批注

* **WHEN** 用户添加/回复/删除批注

* **THEN** 系统正确更新 comments.xml 及相关文件

* **AND** 维护批注的父子关系

#### Scenario: 跟踪修订

* **WHEN** 用户启用修订跟踪

* **THEN** 系统记录所有插入和删除操作

* **AND** 支持接受/拒绝修订

### Requirement: PPTX 演示文稿处理

系统应提供完整的 PowerPoint 演示文稿处理能力。

#### Scenario: 创建演示文稿

* **WHEN** 用户请求创建演示文稿

* **THEN** 系统使用 pptxgenjs 创建演示文稿

* **AND** 支持设置幻灯片布局、主题颜色

* **AND** 支持添加文本、形状、图片、图表、表格

#### Scenario: 管理幻灯片

* **WHEN** 用户请求添加/删除/重排幻灯片

* **THEN** 系统正确更新演示文稿结构

* **AND** 维护幻灯片关系文件

#### Scenario: 生成缩略图

* **WHEN** 用户请求预览演示文稿

* **THEN** 系统生成幻灯片缩略图

* **AND** 支持指定分辨率和格式

### Requirement: PDF 文档处理

系统应提供完整的 PDF 文档处理能力。

#### Scenario: 提取文本

* **WHEN** 用户请求从 PDF 提取文本

* **THEN** 系统使用 pdfplumber 提取文本

* **AND** 保留文本布局信息

#### Scenario: 提取表格

* **WHEN** 用户请求从 PDF 提取表格

* **THEN** 系统识别并提取表格数据

* **AND** 支持导出为 Excel 或 CSV

#### Scenario: 合并/拆分 PDF

* **WHEN** 用户请求合并多个 PDF

* **THEN** 系统使用 pypdf 合并文档

* **WHEN** 用户请求拆分 PDF

* **THEN** 系统按页码范围拆分文档

#### Scenario: 填写表单

* **WHEN** 用户请求填写 PDF 表单

* **THEN** 系统识别可填写字段

* **AND** 支持填写文本、复选框、单选按钮

### Requirement: OOXML 工具集

系统应提供 OOXML 文档的底层操作工具。

#### Scenario: 打包/解包文档

* **WHEN** 用户请求解包 OOXML 文档

* **THEN** 系统提取所有 XML 文件

* **AND** 格式化 XML 便于编辑

* **WHEN** 用户请求打包文档

* **THEN** 系统验证并创建有效文档

#### Scenario: 验证文档

* **WHEN** 用户请求验证文档

* **THEN** 系统检查 XML 模式合规性

* **AND** 报告验证错误和警告

### Requirement: 统一工具接口

文档工具应遵循 PyAgent 的统一工具接口。

#### Scenario: 工具生命周期

* **WHEN** 调用文档工具

* **THEN** 系统执行 activate → execute → dormant 流程

* **AND** 正确管理工具状态

#### Scenario: AI 辅助集成

* **WHEN** 用户请求 AI 辅助功能

* **THEN** 系统调用 LLM 进行内容分析

* **AND** 提供改写、翻译、摘要等功能

## MODIFIED Requirements

### Requirement: 文档管理器增强

原有的文档管理器需要支持更多操作。

#### Scenario: 格式转换

* **WHEN** 用户请求转换文档格式

* **THEN** 系统支持 docx↔pdf、pptx↔pdf 等转换

* **AND** 使用 LibreOffice 或 pandoc 作为转换引擎

#### Scenario: 版本管理

* **WHEN** 用户保存文档

* **THEN** 系统可选创建版本快照

* **AND** 支持恢复到历史版本

## REMOVED Requirements

无移除的需求。现有功能保持兼容。

## 技术架构

```
src/document/
├── __init__.py
├── manager.py          # 文档管理器（增强）
├── types.py            # 类型定义
├── metadata.py         # 元数据管理
├── connector.py        # ONLYOFFICE 连接器
├── tools.py            # 统一工具接口（增强）
├── docx/               # Word 处理模块（新增）
│   ├── __init__.py
│   ├── creator.py      # 文档创建
│   ├── editor.py       # 文档编辑
│   ├── comment.py      # 批注管理
│   ├── revision.py     # 修订跟踪
│   ├── converter.py    # 格式转换
│   └── templates/      # 模板文件
├── pptx/               # PowerPoint 处理模块（新增）
│   ├── __init__.py
│   ├── creator.py      # 演示文稿创建
│   ├── editor.py       # 演示文稿编辑
│   ├── slide.py        # 幻灯片管理
│   ├── thumbnail.py    # 缩略图生成
│   └── templates/      # 设计模板
├── pdf/                # PDF 处理模块（新增）
│   ├── __init__.py
│   ├── extractor.py    # 文本/表格提取
│   ├── merger.py       # 合并/拆分
│   ├── form.py         # 表单填写
│   └── ocr.py          # OCR 支持
└── ooxml/              # OOXML 工具模块（新增）
    ├── __init__.py
    ├── pack.py         # 打包工具
    ├── unpack.py       # 解包工具
    ├── validate.py     # 验证工具
    ├── xml_editor.py   # XML 编辑器
    └── schemas/        # XSD 模式文件
```

## 依赖要求

### Python 包

```
pypdf>=4.0.0
pdfplumber>=0.10.0
reportlab>=4.0.0
defusedxml>=0.7.0
python-docx>=1.1.0  # 可选，用于高级操作
python-pptx>=0.6.23 # 可选，用于高级操作
pytesseract>=0.3.10 # OCR 支持
pdf2image>=1.16.0   # PDF 转图片
Pillow>=10.0.0      # 图像处理
```

### 外部工具

* **pandoc**: 文档格式转换

* **LibreOffice**: 高级格式转换

* **poppler-utils**: PDF 命令行工具

* **Tesseract**: OCR 引擎

## 迁移来源

从 `openakita-1.27.2/openakita-1.27.2/skills/` 迁移：

1. **docx/** → `src/document/docx/`

   * `scripts/document.py` → `editor.py`, `comment.py`, `revision.py`

   * `scripts/office/` → `ooxml/`

   * `ooxml/schemas/` → `ooxml/schemas/`

   * `templates/` → `docx/templates/`

2. **pptx/** → `src/document/pptx/`

   * `scripts/` → 各功能模块

   * `ooxml/schemas/` → 共享 ooxml/schemas/

3. **pdf/** → `src/document/pdf/`

   * `scripts/` → 各功能模块

