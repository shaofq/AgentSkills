# -*- coding: utf-8 -*-
"""用户和权限数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    """角色枚举"""
    ADMIN = "admin"          # 管理员 - 所有权限
    OPERATOR = "operator"    # 操作员 - 基础操作权限
    VIEWER = "viewer"        # 查看者 - 只读权限


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    display_name: Optional[str] = Field(None, description="显示名称")
    role: RoleEnum = Field(default=RoleEnum.OPERATOR, description="角色")
    is_active: bool = Field(default=True, description="是否激活")


class UserCreate(UserBase):
    """创建用户请求"""
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """数据库中的用户"""
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    permissions: List[str]


class TokenData(BaseModel):
    """Token数据"""
    user_id: int
    username: str
    role: RoleEnum
    exp: datetime


# 角色权限映射
ROLE_PERMISSIONS = {
    RoleEnum.ADMIN: [
        "user:create", "user:read", "user:update", "user:delete",
        "workflow:create", "workflow:read", "workflow:update", "workflow:delete", "workflow:execute",
        "crew_compare:read", "crew_compare:write", "crew_compare:export",
        "settings:read", "settings:write",
        "history:read", "history:delete",
        "*"  # 所有权限
    ],
    RoleEnum.OPERATOR: [
        "user:read",
        "workflow:read", "workflow:execute",
        "crew_compare:read", "crew_compare:write", "crew_compare:export",
        "history:read",
    ],
    RoleEnum.VIEWER: [
        "user:read",
        "workflow:read",
        "crew_compare:read",
        "history:read",
    ]
}


def get_permissions(role: RoleEnum) -> List[str]:
    """获取角色权限列表"""
    return ROLE_PERMISSIONS.get(role, [])
