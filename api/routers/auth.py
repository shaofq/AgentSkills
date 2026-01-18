# -*- coding: utf-8 -*-
"""用户认证和管理API路由"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List

from api.models.user import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    RoleEnum, get_permissions
)
from api.services.auth_service import (
    get_auth_service, get_user_service, decode_access_token
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ============= 依赖项 =============

async def get_current_user(authorization: Optional[str] = Header(None)) -> UserResponse:
    """获取当前登录用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    # 提取token
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    auth_service = get_auth_service()
    success, message, user = auth_service.get_current_user(token)
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    return user


async def require_admin(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """要求管理员权限"""
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def require_permission(permission: str):
    """要求特定权限的依赖项工厂"""
    async def check_permission(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        permissions = get_permissions(current_user.role)
        if "*" not in permissions and permission not in permissions:
            raise HTTPException(status_code=403, detail=f"缺少权限: {permission}")
        return current_user
    return check_permission


# ============= 公开接口 =============

@router.post("/login", response_model=dict)
async def login(request: LoginRequest):
    """用户登录"""
    auth_service = get_auth_service()
    success, message, response = auth_service.login(request.username, request.password)
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    return {
        "success": True,
        "message": message,
        "data": {
            "access_token": response.access_token,
            "token_type": response.token_type,
            "user": response.user.model_dump(),
            "permissions": response.permissions
        }
    }


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, _: UserResponse = Depends(require_admin)):
    """注册新用户（仅管理员）"""
    auth_service = get_auth_service()
    success, message, user = auth_service.register(user_data)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "data": user.model_dump()
    }


@router.get("/me", response_model=dict)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息"""
    auth_service = get_auth_service()
    permissions = auth_service.get_user_permissions(current_user.id)
    
    return {
        "success": True,
        "data": {
            "user": current_user.model_dump(),
            "permissions": permissions
        }
    }


@router.post("/change-password", response_model=dict)
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """修改密码"""
    from api.services.auth_service import verify_password, hash_password
    from api.services.database import get_user_repository
    
    user_repo = get_user_repository()
    user = user_repo.get_by_id(current_user.id)
    
    if not verify_password(old_password, user['hashed_password']):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    user_repo.update(current_user.id, hashed_password=hash_password(new_password))
    
    return {"success": True, "message": "密码修改成功"}


# ============= 用户管理接口（管理员） =============

@router.get("/users", response_model=dict)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _: UserResponse = Depends(require_admin)
):
    """获取用户列表（仅管理员）"""
    user_service = get_user_service()
    users = user_service.get_all_users(skip, limit)
    
    return {
        "success": True,
        "data": [u.model_dump() for u in users],
        "total": len(users)
    }


@router.get("/users/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    _: UserResponse = Depends(require_admin)
):
    """获取用户详情（仅管理员）"""
    user_service = get_user_service()
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "success": True,
        "data": user.model_dump()
    }


@router.put("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    _: UserResponse = Depends(require_admin)
):
    """更新用户（仅管理员）"""
    user_service = get_user_service()
    success, message, user = user_service.update_user(user_id, user_data)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "data": user.model_dump()
    }


@router.delete("/users/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    _: UserResponse = Depends(require_admin)
):
    """删除用户（仅管理员）"""
    user_service = get_user_service()
    success, message = user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}


@router.get("/roles", response_model=dict)
async def get_roles(_: UserResponse = Depends(get_current_user)):
    """获取角色列表"""
    roles = [
        {"value": RoleEnum.ADMIN.value, "label": "管理员", "description": "拥有所有权限"},
        {"value": RoleEnum.OPERATOR.value, "label": "操作员", "description": "可执行基础操作"},
        {"value": RoleEnum.VIEWER.value, "label": "查看者", "description": "只读权限"},
    ]
    return {"success": True, "data": roles}
