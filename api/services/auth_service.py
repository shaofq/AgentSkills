# -*- coding: utf-8 -*-
"""用户认证服务"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt

from api.models.user import (
    UserCreate, UserUpdate, UserResponse, LoginResponse,
    TokenData, RoleEnum, get_permissions
)
from api.services.database import get_user_repository

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-" + secrets.token_hex(16))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """密码哈希"""
    salt = "lowcode-ai-salt"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password


def create_access_token(user_id: int, username: str, role: str, expires_delta: timedelta = None) -> str:
    """创建访问令牌"""
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[TokenData]:
    """解码访问令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            user_id=payload["user_id"],
            username=payload["username"],
            role=RoleEnum(payload["role"]),
            exp=datetime.fromtimestamp(payload["exp"])
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


class AuthService:
    """认证服务"""
    
    def __init__(self):
        self.user_repo = get_user_repository()
    
    def register(self, user_data: UserCreate) -> Tuple[bool, str, Optional[UserResponse]]:
        """用户注册"""
        # 检查用户名是否已存在
        existing = self.user_repo.get_by_username(user_data.username)
        if existing:
            return False, "用户名已存在", None
        
        # 创建用户
        hashed_pwd = hash_password(user_data.password)
        user = self.user_repo.create(
            username=user_data.username,
            hashed_password=hashed_pwd,
            email=user_data.email,
            display_name=user_data.display_name or user_data.username,
            role=user_data.role.value
        )
        
        return True, "注册成功", self._to_response(user)
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[LoginResponse]]:
        """用户登录"""
        user = self.user_repo.get_by_username(username)
        
        if not user:
            return False, "用户名或密码错误", None
        
        if not verify_password(password, user['hashed_password']):
            return False, "用户名或密码错误", None
        
        if not user['is_active']:
            return False, "账号已被禁用", None
        
        # 更新最后登录时间
        self.user_repo.update_last_login(user['id'])
        
        # 生成token
        token = create_access_token(
            user_id=user['id'],
            username=user['username'],
            role=user['role']
        )
        
        # 获取权限
        permissions = get_permissions(RoleEnum(user['role']))
        
        return True, "登录成功", LoginResponse(
            access_token=token,
            user=self._to_response(user),
            permissions=permissions
        )
    
    def get_current_user(self, token: str) -> Tuple[bool, str, Optional[UserResponse]]:
        """获取当前用户"""
        token_data = decode_access_token(token)
        if not token_data:
            return False, "无效或过期的令牌", None
        
        user = self.user_repo.get_by_id(token_data.user_id)
        if not user:
            return False, "用户不存在", None
        
        if not user['is_active']:
            return False, "账号已被禁用", None
        
        return True, "成功", self._to_response(user)
    
    def get_user_permissions(self, user_id: int) -> list:
        """获取用户权限"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return []
        return get_permissions(RoleEnum(user['role']))
    
    def _to_response(self, user: dict) -> UserResponse:
        """转换为响应模型"""
        return UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            display_name=user['display_name'],
            role=RoleEnum(user['role']),
            is_active=bool(user['is_active']),
            created_at=datetime.fromisoformat(user['created_at']) if user['created_at'] else datetime.now(),
            last_login=datetime.fromisoformat(user['last_login']) if user['last_login'] else None,
            credits=user.get('credits', 0) or 0
        )


class UserService:
    """用户管理服务"""
    
    def __init__(self):
        self.user_repo = get_user_repository()
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> list:
        """获取所有用户"""
        users = self.user_repo.get_all(skip, limit)
        return [self._to_response(u) for u in users]
    
    def get_user(self, user_id: int) -> Optional[UserResponse]:
        """获取单个用户"""
        user = self.user_repo.get_by_id(user_id)
        return self._to_response(user) if user else None
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Tuple[bool, str, Optional[UserResponse]]:
        """更新用户"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "用户不存在", None
        
        update_data = {}
        if user_data.email is not None:
            update_data['email'] = user_data.email
        if user_data.display_name is not None:
            update_data['display_name'] = user_data.display_name
        if user_data.role is not None:
            update_data['role'] = user_data.role.value
        if user_data.is_active is not None:
            update_data['is_active'] = 1 if user_data.is_active else 0
        if user_data.password:
            update_data['hashed_password'] = hash_password(user_data.password)
        
        updated = self.user_repo.update(user_id, **update_data)
        return True, "更新成功", self._to_response(updated)
    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """删除用户"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, "用户不存在"
        
        if user['role'] == 'admin':
            # 检查是否是最后一个管理员
            all_users = self.user_repo.get_all()
            admin_count = sum(1 for u in all_users if u['role'] == 'admin')
            if admin_count <= 1:
                return False, "不能删除最后一个管理员"
        
        self.user_repo.delete(user_id)
        return True, "删除成功"
    
    def _to_response(self, user: dict) -> UserResponse:
        """转换为响应模型"""
        return UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            display_name=user['display_name'],
            role=RoleEnum(user['role']),
            is_active=bool(user['is_active']),
            created_at=datetime.fromisoformat(user['created_at']) if user['created_at'] else datetime.now(),
            last_login=datetime.fromisoformat(user['last_login']) if user['last_login'] else None,
            credits=user.get('credits', 0) or 0
        )


# 全局服务实例
_auth_service: Optional[AuthService] = None
_user_service: Optional[UserService] = None


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


def get_user_service() -> UserService:
    """获取用户管理服务实例"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service


# ========== FastAPI 依赖注入 ==========
from fastapi import Depends, HTTPException, Header
from typing import Optional

async def get_current_user(authorization: str = Header(None)) -> dict:
    """获取当前登录用户（必须登录）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或token无效")
    
    token = authorization.replace("Bearer ", "")
    token_data = decode_access_token(token)
    
    if not token_data:
        raise HTTPException(status_code=401, detail="token已过期或无效")
    
    user_repo = get_user_repository()
    user = user_repo.get_by_id(token_data.user_id)
    
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return user


async def get_current_user_optional(authorization: str = Header(None)) -> Optional[dict]:
    """获取当前登录用户（可选，未登录返回None）"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    token_data = decode_access_token(token)
    
    if not token_data:
        return None
    
    user_repo = get_user_repository()
    user = user_repo.get_by_id(token_data.user_id)
    
    return user


def require_permission(permission: str):
    """权限检查依赖"""
    async def check_permission(current_user: dict = Depends(get_current_user)) -> dict:
        role = RoleEnum(current_user.get('role', 'viewer'))
        permissions = get_permissions(role)
        
        if "*" in permissions or permission in permissions:
            return current_user
        
        raise HTTPException(status_code=403, detail=f"权限不足，需要: {permission}")
    
    return check_permission
