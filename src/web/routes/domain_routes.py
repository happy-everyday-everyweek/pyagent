"""
PyAgent Web服务 - 域API路由

提供域管理的API接口。
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.device.domain_manager import domain_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/domain", tags=["domain"])


class CreateDomainRequest(BaseModel):
    name: str = "default"


class JoinDomainRequest(BaseModel):
    domain_id: str


class SyncRequest(BaseModel):
    data: dict[str, Any]
    branch: str = "main"


class DomainResponse(BaseModel):
    id: str
    name: str
    devices: list[str]
    created_at: str
    status: str


class DeviceResponse(BaseModel):
    id: str
    domain_id: str
    name: str
    status: str
    last_sync: str | None = None


@router.post("/create", response_model=DomainResponse)
async def create_domain(request: CreateDomainRequest) -> DomainResponse:
    domain_id = domain_manager.create_domain(name=request.name)
    domain_info = domain_manager.get_domain_info()

    if domain_info is None:
        raise HTTPException(status_code=500, detail="Failed to create domain")

    logger.info(f"Created domain: {domain_id} ({request.name})")

    return DomainResponse(
        id=domain_info.domain_id,
        name=domain_info.name,
        devices=domain_info.devices,
        created_at=domain_info.created_at,
        status="active"
    )


@router.post("/join")
async def join_domain(request: JoinDomainRequest) -> dict[str, Any]:
    success = domain_manager.join_domain(request.domain_id)

    if not success:
        raise HTTPException(status_code=404, detail="Domain not found or failed to join")

    domain_info = domain_manager.get_domain_info()
    device_id = domain_manager._device_id_manager.get_device_id()

    logger.info(f"Device {device_id} joined domain {request.domain_id}")

    return {
        "success": True,
        "domain_id": request.domain_id,
        "device_id": device_id,
        "domain_name": domain_info.name if domain_info else ""
    }


@router.get("/devices", response_model=list[DeviceResponse])
async def get_domain_devices() -> list[DeviceResponse]:
    domain_info = domain_manager.get_domain_info()

    if domain_info is None:
        return []

    device_records = domain_manager.get_domain_devices()

    return [
        DeviceResponse(
            id=record.device_id,
            domain_id=domain_info.domain_id,
            name=f"device_{record.device_id[:8]}",
            status=record.status,
            last_sync=record.last_seen
        )
        for record in device_records
    ]


@router.post("/sync")
async def sync_data(request: SyncRequest) -> dict[str, Any]:
    from datetime import datetime
    from uuid import uuid4

    domain_info = domain_manager.get_domain_info()

    if domain_info is None:
        raise HTTPException(status_code=400, detail="Not joined any domain")

    sync_id = str(uuid4())
    now = datetime.now().isoformat()

    logger.info(f"Syncing data to domain {domain_info.domain_id}, branch: {request.branch}")

    return {
        "success": True,
        "sync_id": sync_id,
        "domain_id": domain_info.domain_id,
        "branch": request.branch,
        "timestamp": now,
        "data_size": len(str(request.data))
    }


@router.get("/status")
async def get_domain_status() -> dict[str, Any]:
    domain_info = domain_manager.get_domain_info()

    if domain_info is None:
        return {
            "joined": False,
            "domain_id": None,
            "domain_name": None,
            "device_count": 0,
            "status": "disconnected"
        }

    return {
        "joined": True,
        "domain_id": domain_info.domain_id,
        "domain_name": domain_info.name,
        "device_count": domain_manager.get_device_count(),
        "status": "active",
        "created_at": domain_info.created_at
    }


@router.get("/list", response_model=list[DomainResponse])
async def list_domains() -> list[DomainResponse]:
    domain_info = domain_manager.get_domain_info()

    if domain_info is None:
        return []

    return [
        DomainResponse(
            id=domain_info.domain_id,
            name=domain_info.name,
            devices=domain_info.devices,
            created_at=domain_info.created_at,
            status="active"
        )
    ]


@router.delete("/{domain_id}")
async def leave_domain(domain_id: str) -> dict[str, Any]:
    current_domain_id = domain_manager.get_domain_id()

    if current_domain_id != domain_id:
        raise HTTPException(status_code=404, detail="Domain not found")

    success = domain_manager.leave_domain()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to leave domain")

    logger.info(f"Left domain: {domain_id}")

    return {"success": True, "domain_id": domain_id}
