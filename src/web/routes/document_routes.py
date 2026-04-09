"""
PyAgent Web服务 - 文档API路由

提供文档管理的完整API接口，支持 DOCX、PPTX、PDF、XLSX 四种文档类型。
"""

import logging
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/document", tags=["document"])

_document_store: dict[str, dict[str, Any]] = {}
_file_store: dict[str, Path] = Path(tempfile.mkdtemp(prefix="doc_store_"))


class CreateDocumentRequest(BaseModel):
    document_type: str
    name: str


class UpdateDocumentRequest(BaseModel):
    content: str | None = None
    name: str | None = None


class DocumentResponse(BaseModel):
    id: str
    name: str
    document_type: str
    content: str | None = None
    editor_url: str | None = None
    created_at: str
    updated_at: str


class DocxCreateRequest(BaseModel):
    name: str
    template: str | None = None


class DocxCommentRequest(BaseModel):
    text: str
    author: str = "System"
    target_text: str | None = None


class PptxCreateRequest(BaseModel):
    name: str
    template: str | None = None


class PptxSlideRequest(BaseModel):
    title: str
    subtitle: str | None = None
    bullet_points: list[str] | None = None


class PdfExtractRequest(BaseModel):
    file_path: str
    extract_tables: bool = False


class PdfMergeRequest(BaseModel):
    files: list[str]
    output_path: str


class PdfSplitRequest(BaseModel):
    file_path: str
    output_dir: str
    pages_per_file: int = 1


class PdfFormFillRequest(BaseModel):
    file_path: str
    output_path: str
    fields: dict[str, Any]


class PdfOcrRequest(BaseModel):
    file_path: str
    language: str = "chi_sim+eng"


class XlsxCreateRequest(BaseModel):
    name: str
    template: str | None = None


class XlsxSheetRequest(BaseModel):
    name: str
    position: int | None = None


class XlsxCellRequest(BaseModel):
    sheet_name: str
    cell_ref: str
    value: Any
    formula: str | None = None


class XlsxChartRequest(BaseModel):
    sheet_name: str
    chart_type: str
    data_range: str
    title: str | None = None
    position: str = "E2"


class ConvertRequest(BaseModel):
    target_format: str


@router.post("/create", response_model=DocumentResponse)
async def create_document(request: CreateDocumentRequest) -> DocumentResponse:
    if request.document_type not in ["word", "excel", "ppt", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid document type")

    doc_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    document = {
        "id": doc_id,
        "name": request.name,
        "document_type": request.document_type,
        "content": None,
        "editor_url": None,
        "created_at": now,
        "updated_at": now
    }

    _document_store[doc_id] = document

    logger.info(f"Created document: {doc_id} ({request.document_type})")

    return DocumentResponse(**document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str) -> DocumentResponse:
    if document_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(**_document_store[document_id])


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, request: UpdateDocumentRequest) -> DocumentResponse:
    if document_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[document_id]

    if request.content is not None:
        document["content"] = request.content
    if request.name is not None:
        document["name"] = request.name

    document["updated_at"] = datetime.now().isoformat()

    logger.info(f"Updated document: {document_id}")

    return DocumentResponse(**document)


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> dict[str, Any]:
    if document_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    del _document_store[document_id]

    logger.info(f"Deleted document: {document_id}")

    return {"success": True, "document_id": document_id}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    doc_id = str(uuid.uuid4())
    file_path = _file_store / f"{doc_id}_{file.filename}"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    suffix = Path(file.filename).suffix.lower()
    doc_type_map = {
        ".docx": "word",
        ".doc": "word",
        ".xlsx": "excel",
        ".xls": "excel",
        ".pptx": "ppt",
        ".ppt": "ppt",
        ".pdf": "pdf",
    }

    document = {
        "id": doc_id,
        "name": file.filename,
        "document_type": doc_type_map.get(suffix, "unknown"),
        "file_path": str(file_path),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    _document_store[doc_id] = document

    return {"success": True, "document_id": doc_id, "filename": file.filename}


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    if document_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[document_id]
    file_path = document.get("file_path")

    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    from fastapi.responses import FileResponse

    return FileResponse(
        path=file_path,
        filename=document.get("name", "document"),
        media_type="application/octet-stream"
    )


@router.post("/{document_id}/convert")
async def convert_document(document_id: str, request: ConvertRequest) -> dict[str, Any]:
    if document_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[document_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import DocumentManager

    manager = DocumentManager()
    output_path = manager.convert_document(document_id, request.target_format)

    if not output_path:
        raise HTTPException(status_code=500, detail="Conversion failed")

    return {"success": True, "output_path": output_path}


# ==================== DOCX API ====================

@router.post("/docx/create")
async def create_docx(request: DocxCreateRequest) -> dict[str, Any]:
    from src.document import DocxCreator

    doc_id = str(uuid.uuid4())
    output_path = _file_store / f"{doc_id}_{request.name}.docx"

    creator = DocxCreator(request.template)
    creator.save(output_path)

    document = {
        "id": doc_id,
        "name": request.name,
        "document_type": "word",
        "file_path": str(output_path),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    _document_store[doc_id] = document

    return {"success": True, "document_id": doc_id}


@router.post("/docx/{doc_id}/comments")
async def add_docx_comment(doc_id: str, request: DocxCommentRequest) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import CommentManager

    manager = CommentManager(file_path)
    comment_id = manager.add_comment(request.text, request.author, request.target_text)
    manager.save(file_path)

    return {"success": True, "comment_id": comment_id}


@router.get("/docx/{doc_id}/comments")
async def get_docx_comments(doc_id: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import CommentManager

    manager = CommentManager(file_path)
    comments = manager.get_comments()

    return {"success": True, "comments": comments}


@router.get("/docx/{doc_id}/revisions")
async def get_docx_revisions(doc_id: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import RevisionManager

    manager = RevisionManager(file_path)
    revisions = manager.get_revisions()

    return {"success": True, "revisions": revisions}


@router.post("/docx/{doc_id}/revisions/{rev_id}/accept")
async def accept_docx_revision(doc_id: str, rev_id: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import RevisionManager

    manager = RevisionManager(file_path)
    result = manager.accept_revision(rev_id)
    manager.save(file_path)

    return {"success": result}


@router.post("/docx/{doc_id}/revisions/{rev_id}/reject")
async def reject_docx_revision(doc_id: str, rev_id: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import RevisionManager

    manager = RevisionManager(file_path)
    result = manager.reject_revision(rev_id)
    manager.save(file_path)

    return {"success": result}


# ==================== PPTX API ====================

@router.post("/pptx/create")
async def create_pptx(request: PptxCreateRequest) -> dict[str, Any]:
    from src.document import PptxCreator

    doc_id = str(uuid.uuid4())
    output_path = _file_store / f"{doc_id}_{request.name}.pptx"

    creator = PptxCreator(request.template)
    creator.save(output_path)

    document = {
        "id": doc_id,
        "name": request.name,
        "document_type": "ppt",
        "file_path": str(output_path),
        "slides_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    _document_store[doc_id] = document

    return {"success": True, "document_id": doc_id}


@router.post("/pptx/{doc_id}/slides")
async def add_pptx_slide(doc_id: str, request: PptxSlideRequest) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import PptxCreator

    creator = PptxCreator(file_path)

    if request.subtitle:
        slide_idx = creator.add_title_slide(request.title, request.subtitle)
    else:
        slide_idx = creator.add_content_slide(request.title, request.bullet_points)

    creator.save(file_path)

    document["slides_count"] = creator.slides_count
    document["updated_at"] = datetime.now().isoformat()

    return {"success": True, "slide_index": slide_idx}


@router.get("/pptx/{doc_id}/slides")
async def list_pptx_slides(doc_id: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import SlideManager

    manager = SlideManager(file_path)
    slides = manager.list_slides()

    return {"success": True, "slides": slides}


@router.delete("/pptx/{doc_id}/slides/{slide_idx}")
async def delete_pptx_slide(doc_id: str, slide_idx: int) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import PptxEditor

    editor = PptxEditor(file_path)
    result = editor.delete_slide(slide_idx)
    editor.save(file_path)

    return {"success": result}


@router.get("/pptx/{doc_id}/thumbnails")
async def generate_pptx_thumbnails(doc_id: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import ThumbnailGenerator

    output_dir = _file_store / f"{doc_id}_thumbnails"
    output_dir.mkdir(exist_ok=True)

    generator = ThumbnailGenerator(file_path)
    thumbnails = generator.generate_all_thumbnails(output_dir)

    return {"success": True, "thumbnails": [str(t) for t in thumbnails]}


# ==================== PDF API ====================

@router.post("/pdf/extract")
async def extract_pdf(request: PdfExtractRequest) -> dict[str, Any]:
    if not Path(request.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    from src.document import PDFExtractor

    extractor = PDFExtractor()
    result = extractor.extract(request.file_path)

    response = {
        "success": True,
        "text": result.text,
    }

    if request.extract_tables:
        response["tables"] = [t.to_dict() for t in result.tables]

    return response


@router.post("/pdf/merge")
async def merge_pdf(request: PdfMergeRequest) -> dict[str, Any]:
    for f in request.files:
        if not Path(f).exists():
            raise HTTPException(status_code=404, detail=f"File not found: {f}")

    from src.document import PDFMerger

    merger = PDFMerger()
    result = merger.merge_pdfs(request.files, request.output_path)

    return {"success": result, "output_path": request.output_path}


@router.post("/pdf/split")
async def split_pdf(request: PdfSplitRequest) -> dict[str, Any]:
    if not Path(request.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    from src.document import PDFSplitter

    splitter = PDFSplitter()
    result = splitter.split_by_page(request.file_path, request.output_dir)

    return {"success": result, "output_dir": request.output_dir}


@router.post("/pdf/form/fill")
async def fill_pdf_form(request: PdfFormFillRequest) -> dict[str, Any]:
    if not Path(request.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    from src.document import PDFFormFiller

    filler = PDFFormFiller()
    result = filler.fill_fields(request.file_path, request.output_path, request.fields)

    return {"success": result, "output_path": request.output_path}


@router.post("/pdf/ocr")
async def ocr_pdf(request: PdfOcrRequest) -> dict[str, Any]:
    if not Path(request.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    from src.document import PDFOCRProcessor

    processor = PDFOCRProcessor()
    text = processor.ocr_pdf(request.file_path, request.language)

    return {"success": True, "text": text}


# ==================== XLSX API ====================

@router.post("/xlsx/create")
async def create_xlsx(request: XlsxCreateRequest) -> dict[str, Any]:
    from src.document import XlsxCreator

    doc_id = str(uuid.uuid4())
    output_path = _file_store / f"{doc_id}_{request.name}.xlsx"

    creator = XlsxCreator(request.template)
    creator.save(output_path)

    document = {
        "id": doc_id,
        "name": request.name,
        "document_type": "excel",
        "file_path": str(output_path),
        "sheets": ["Sheet1"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    _document_store[doc_id] = document

    return {"success": True, "document_id": doc_id}


@router.post("/xlsx/{doc_id}/sheets")
async def add_xlsx_sheet(doc_id: str, request: XlsxSheetRequest) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import SheetManager

    manager = SheetManager(file_path)
    result = manager.add_sheet(request.name, request.position)
    manager.save(file_path)

    if result:
        if request.name not in document.get("sheets", []):
            document.setdefault("sheets", []).append(request.name)
        document["updated_at"] = datetime.now().isoformat()

    return {"success": result}


@router.get("/xlsx/{doc_id}/sheets")
async def list_xlsx_sheets(doc_id: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import SheetManager

    manager = SheetManager(file_path)
    sheets = manager.list_sheets()

    return {"success": True, "sheets": sheets}


@router.post("/xlsx/{doc_id}/cells")
async def set_xlsx_cell(doc_id: str, request: XlsxCellRequest) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import XlsxEditor

    editor = XlsxEditor(file_path)
    result = editor.set_cell(request.sheet_name, request.cell_ref, request.value, request.formula)
    editor.save(file_path)

    document["updated_at"] = datetime.now().isoformat()

    return {"success": result}


@router.get("/xlsx/{doc_id}/cells")
async def get_xlsx_cell(doc_id: str, sheet_name: str, cell_ref: str) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import XlsxEditor

    editor = XlsxEditor(file_path)
    value = editor.get_cell(sheet_name, cell_ref)

    return {"success": True, "value": value}


@router.post("/xlsx/{doc_id}/charts")
async def add_xlsx_chart(doc_id: str, request: XlsxChartRequest) -> dict[str, Any]:
    if doc_id not in _document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    document = _document_store[doc_id]
    file_path = document.get("file_path")

    if not file_path:
        raise HTTPException(status_code=400, detail="No file associated with document")

    from src.document import ChartManager

    manager = ChartManager(file_path)
    chart_id = manager.add_chart(
        request.sheet_name,
        request.chart_type,
        request.data_range,
        request.title,
        position=request.position
    )
    manager.save(file_path)

    document["updated_at"] = datetime.now().isoformat()

    return {"success": True, "chart_id": chart_id}
