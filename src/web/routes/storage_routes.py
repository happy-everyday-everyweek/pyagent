"""
PyAgent Web服务 - 存储API路由

提供分布式存储的API接口。
"""

import base64
import logging
import os
import tempfile
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from src.storage.distributed import get_distributed_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/storage", tags=["storage"])


class UploadResponse(BaseModel):
    file_id: str
    file_name: str
    size: int
    checksum: str
    status: str


class FileInfoResponse(BaseModel):
    file_id: str
    file_name: str
    file_path: str
    device_id: str
    size: int
    created_at: str
    modified_at: str
    checksum: str
    status: str
    tags: list[str]


class FileListResponse(BaseModel):
    files: list[FileInfoResponse]
    total: int


class SyncRequest(BaseModel):
    file_info: dict[str, Any]


class SearchRequest(BaseModel):
    query: str


class TagsUpdateRequest(BaseModel):
    tags: list[str]


def _get_default_file() -> Any:
    return File(...)


_DEFAULT_FILE = _get_default_file()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = _DEFAULT_FILE) -> UploadResponse:
    storage = get_distributed_storage()

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "file")[1]) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        metadata = storage.upload_file(tmp_path, broadcast=True)

        if metadata is None:
            raise HTTPException(status_code=500, detail="Failed to upload file")

        logger.info(f"File uploaded via API: {metadata.file_id}")

        return UploadResponse(
            file_id=metadata.file_id,
            file_name=metadata.file_name,
            size=metadata.size,
            checksum=metadata.checksum,
            status=metadata.status,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.get("/files", response_model=FileListResponse)
async def list_files(device_id: str | None = None) -> FileListResponse:
    storage = get_distributed_storage()

    files = storage.list_files(device_id)

    return FileListResponse(
        files=[
            FileInfoResponse(
                file_id=f.file_id,
                file_name=f.file_name,
                file_path=f.file_path,
                device_id=f.device_id,
                size=f.size,
                created_at=f.created_at,
                modified_at=f.modified_at,
                checksum=f.checksum,
                status=f.status,
                tags=f.tags,
            )
            for f in files
        ],
        total=len(files),
    )


@router.get("/files/{file_id}", response_model=FileInfoResponse)
async def get_file_info(file_id: str) -> FileInfoResponse:
    storage = get_distributed_storage()

    info = storage.get_file_info(file_id)

    if info is None:
        raise HTTPException(status_code=404, detail="File not found")

    metadata = info.get("metadata", {})

    return FileInfoResponse(
        file_id=metadata.get("file_id", ""),
        file_name=metadata.get("file_name", ""),
        file_path=metadata.get("file_path", ""),
        device_id=metadata.get("device_id", ""),
        size=metadata.get("size", 0),
        created_at=metadata.get("created_at", ""),
        modified_at=metadata.get("modified_at", ""),
        checksum=metadata.get("checksum", ""),
        status=metadata.get("status", ""),
        tags=metadata.get("tags", []),
    )


@router.get("/files/{file_id}/download")
async def download_file(file_id: str) -> dict[str, Any]:
    storage = get_distributed_storage()

    content, metadata = storage.get_file(file_id, pull_from_remote=False)

    if metadata is None:
        raise HTTPException(status_code=404, detail="File not found")

    if content is None:
        raise HTTPException(status_code=404, detail="File content not available locally")

    encoded_content = base64.b64encode(content).decode("utf-8")

    return {
        "file_id": metadata.file_id,
        "file_name": metadata.file_name,
        "content_base64": encoded_content,
        "size": metadata.size,
        "checksum": metadata.checksum,
    }


@router.delete("/files/{file_id}")
async def delete_file(file_id: str) -> dict[str, Any]:
    storage = get_distributed_storage()

    success = storage.delete_file(file_id, sync=True)

    if not success:
        raise HTTPException(status_code=404, detail="File not found or failed to delete")

    logger.info(f"File deleted via API: {file_id}")

    return {"success": True, "file_id": file_id}


@router.get("/recent")
async def get_recent_files(limit: int = 3) -> list[FileInfoResponse]:
    storage = get_distributed_storage()

    files = storage.get_recent_files(limit)

    return [
        FileInfoResponse(
            file_id=f.file_id,
            file_name=f.file_name,
            file_path=f.file_path,
            device_id=f.device_id,
            size=f.size,
            created_at=f.created_at,
            modified_at=f.modified_at,
            checksum=f.checksum,
            status=f.status,
            tags=f.tags,
        )
        for f in files
    ]


@router.get("/stats")
async def get_storage_stats() -> dict[str, Any]:
    storage = get_distributed_storage()

    return storage.get_storage_stats()


@router.post("/sync")
async def sync_file_metadata(request: SyncRequest) -> dict[str, Any]:
    storage = get_distributed_storage()

    success = storage.sync_file_from_metadata(request.file_info)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to sync file metadata")

    return {"success": True, "file_id": request.file_info.get("file_id")}


@router.post("/search", response_model=FileListResponse)
async def search_files(request: SearchRequest) -> FileListResponse:
    storage = get_distributed_storage()

    files = storage.search_files(request.query)

    return FileListResponse(
        files=[
            FileInfoResponse(
                file_id=f.file_id,
                file_name=f.file_name,
                file_path=f.file_path,
                device_id=f.device_id,
                size=f.size,
                created_at=f.created_at,
                modified_at=f.modified_at,
                checksum=f.checksum,
                status=f.status,
                tags=f.tags,
            )
            for f in files
        ],
        total=len(files),
    )


@router.put("/files/{file_id}/tags")
async def update_file_tags(file_id: str, request: TagsUpdateRequest) -> dict[str, Any]:
    storage = get_distributed_storage()

    success = storage.update_file_tags(file_id, request.tags)

    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"success": True, "file_id": file_id, "tags": request.tags}


@router.get("/files/{file_id}/exists")
async def check_file_exists(file_id: str) -> dict[str, Any]:
    storage = get_distributed_storage()

    exists = storage.check_file_exists(file_id)

    return {"file_id": file_id, "exists": exists}


@router.get("/files/{file_id}/checksum")
async def get_file_checksum(file_id: str) -> dict[str, Any]:
    storage = get_distributed_storage()

    checksum = storage.get_file_checksum(file_id)

    if checksum is None:
        raise HTTPException(status_code=404, detail="File not found")

    return {"file_id": file_id, "checksum": checksum}


@router.post("/export")
async def export_metadata() -> dict[str, Any]:
    storage = get_distributed_storage()

    export_path = "data/storage/metadata_export.json"
    success = storage.export_metadata(export_path)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to export metadata")

    return {"success": True, "export_path": export_path}


@router.post("/import")
async def import_metadata(file: UploadFile = _DEFAULT_FILE) -> dict[str, Any]:
    storage = get_distributed_storage()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        imported_count = storage.import_metadata(tmp_path)

        logger.info(f"Imported {imported_count} files via API")

        return {"success": True, "imported_count": imported_count}
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
