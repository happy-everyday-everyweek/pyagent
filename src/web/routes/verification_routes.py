"""
PyAgent Web服务 - IM验证管理API

提供验证状态查询和管理接口。
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.im.verification.manager import verification_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/verification", tags=["verification"])


class VerifiedUserResponse(BaseModel):
    """已验证用户响应"""
    user_id: str
    platform: str
    verified_at: str
    nickname: Optional[str] = None


class VerificationStatusResponse(BaseModel):
    """验证状态响应"""
    user_id: str
    is_verified: bool
    verified_at: Optional[str] = None
    platform: Optional[str] = None


class RevokeRequest(BaseModel):
    """撤销验证请求"""
    user_id: str
    reason: Optional[str] = None


class RevokeResponse(BaseModel):
    """撤销验证响应"""
    success: bool
    message: str


class VerificationListResponse(BaseModel):
    """验证列表响应"""
    total: int
    users: list[VerifiedUserResponse]


@router.get("/status/{user_id}", response_model=VerificationStatusResponse)
async def get_verification_status(user_id: str) -> VerificationStatusResponse:
    """
    获取用户验证状态
    
    Args:
        user_id: 用户ID
        
    Returns:
        VerificationStatusResponse: 验证状态
    """
    verified_user = verification_manager.get_verified_user(user_id)
    
    if verified_user:
        return VerificationStatusResponse(
            user_id=user_id,
            is_verified=True,
            verified_at=verified_user.verified_at.isoformat(),
            platform=verified_user.platform
        )
    
    return VerificationStatusResponse(
        user_id=user_id,
        is_verified=False
    )


@router.get("/list", response_model=VerificationListResponse)
async def list_verified_users(
    platform: Optional[str] = Query(None, description="平台筛选")
) -> VerificationListResponse:
    """
    获取已验证用户列表
    
    Args:
        platform: 平台筛选（可选）
        
    Returns:
        VerificationListResponse: 已验证用户列表
    """
    if platform:
        users = verification_manager.get_verified_users_by_platform(platform)
    else:
        users = verification_manager.get_all_verified_users()
    
    user_list = [
        VerifiedUserResponse(
            user_id=user_id,
            platform=user.platform,
            verified_at=user.verified_at.isoformat(),
            nickname=user.nickname
        )
        for user_id, user in users.items()
    ]
    
    return VerificationListResponse(
        total=len(user_list),
        users=user_list
    )


@router.post("/revoke", response_model=RevokeResponse)
async def revoke_verification(request: RevokeRequest) -> RevokeResponse:
    """
    撤销用户验证状态
    
    Args:
        request: 撤销请求
        
    Returns:
        RevokeResponse: 撤销结果
    """
    success, message = verification_manager.revoke_verification(request.user_id)
    
    if success:
        logger.info(f"Verification revoked for user {request.user_id}: {request.reason}")
    
    return RevokeResponse(
        success=success,
        message=message
    )


@router.post("/cleanup")
async def cleanup_expired_sessions() -> dict[str, Any]:
    """
    清理过期的验证会话
    
    Returns:
        dict: 清理结果
    """
    count = verification_manager.cleanup_expired_sessions()
    
    return {
        "success": True,
        "cleaned_count": count,
        "message": f"已清理 {count} 个过期会话"
    }


@router.get("/stats")
async def get_verification_stats() -> dict[str, Any]:
    """
    获取验证统计信息
    
    Returns:
        dict: 统计信息
    """
    all_users = verification_manager.get_all_verified_users()
    
    platform_stats: dict[str, int] = {}
    for user in all_users.values():
        platform = user.platform
        platform_stats[platform] = platform_stats.get(platform, 0) + 1
    
    return {
        "total_verified_users": len(all_users),
        "by_platform": platform_stats,
        "pending_sessions": len(verification_manager._sessions)
    }
