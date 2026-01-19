# -*- coding: utf-8 -*-
"""积分管理API"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from api.services.database import get_database, get_user_repository
from api.services.auth_service import get_current_user, require_permission

router = APIRouter(prefix="/api/credits", tags=["积分管理"])


# ========== 数据模型 ==========

class CreditInfo(BaseModel):
    """积分信息"""
    user_id: int
    username: str
    credits: int
    

class CreditLog(BaseModel):
    """积分记录"""
    id: int
    user_id: int
    amount: int
    balance: int
    action: str
    description: Optional[str]
    created_at: str


class CreditAdjustRequest(BaseModel):
    """积分调整请求"""
    user_id: int = Field(..., description="用户ID")
    amount: int = Field(..., description="调整数量，正数增加，负数减少")
    action: str = Field(..., description="操作类型，如：recharge, consume, admin_adjust")
    description: Optional[str] = Field(None, description="操作说明")


class CreditSetRequest(BaseModel):
    """设置积分请求"""
    user_id: int = Field(..., description="用户ID")
    credits: int = Field(..., ge=0, description="积分数量")
    description: Optional[str] = Field(None, description="操作说明")


# ========== 积分服务 ==========

class CreditService:
    """积分服务"""
    
    def __init__(self):
        self.db = get_database()
        self.user_repo = get_user_repository()
    
    def get_user_credits(self, user_id: int) -> Optional[int]:
        """获取用户积分"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return user.get('credits', 0)
    
    def set_credits(self, user_id: int, credits: int, admin_user: str = None, description: str = None) -> bool:
        """设置用户积分"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False
        
        old_credits = user.get('credits', 0)
        amount = credits - old_credits
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 更新用户积分
            cursor.execute('UPDATE users SET credits = ?, updated_at = ? WHERE id = ?',
                          (credits, datetime.now().isoformat(), user_id))
            # 记录日志
            cursor.execute('''
                INSERT INTO credit_logs (user_id, amount, balance, action, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, credits, 'admin_set', 
                  description or f"管理员{admin_user or ''}设置积分为{credits}", 
                  datetime.now().isoformat()))
            conn.commit()
        return True
    
    def adjust_credits(self, user_id: int, amount: int, action: str, description: str = None) -> tuple[bool, int, str]:
        """调整用户积分
        返回：(成功与否, 当前余额, 错误信息)
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False, 0, "用户不存在"
        
        current_credits = user.get('credits', 0)
        new_credits = current_credits + amount
        
        # 检查积分是否足够（扣减时）
        if new_credits < 0:
            return False, current_credits, f"积分不足，当前积分: {current_credits}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 更新用户积分
            cursor.execute('UPDATE users SET credits = ?, updated_at = ? WHERE id = ?',
                          (new_credits, datetime.now().isoformat(), user_id))
            # 记录日志
            cursor.execute('''
                INSERT INTO credit_logs (user_id, amount, balance, action, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, amount, new_credits, action, description, datetime.now().isoformat()))
            conn.commit()
        
        return True, new_credits, ""
    
    def consume_credits(self, user_id: int, amount: int, action: str, description: str = None) -> tuple[bool, int, str]:
        """消费积分（扣减）"""
        if amount > 0:
            amount = -amount  # 确保是负数
        return self.adjust_credits(user_id, amount, action, description)
    
    def get_credit_logs(self, user_id: int, limit: int = 50) -> List[dict]:
        """获取积分记录"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM credit_logs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_users_credits(self) -> List[dict]:
        """获取所有用户积分信息"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, display_name, credits, role FROM users ORDER BY id')
            return [dict(row) for row in cursor.fetchall()]


# 全局服务实例
_credit_service: Optional[CreditService] = None

def get_credit_service() -> CreditService:
    global _credit_service
    if _credit_service is None:
        _credit_service = CreditService()
    return _credit_service


# ========== API路由 ==========

@router.get("/me", summary="获取当前用户积分")
async def get_my_credits(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户的积分信息"""
    service = get_credit_service()
    credits = service.get_user_credits(current_user['id'])
    return {
        "success": True,
        "data": {
            "user_id": current_user['id'],
            "username": current_user['username'],
            "credits": credits or 0
        }
    }


@router.get("/me/logs", summary="获取当前用户积分记录")
async def get_my_credit_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """获取当前用户的积分变动记录"""
    service = get_credit_service()
    logs = service.get_credit_logs(current_user['id'], limit)
    return {
        "success": True,
        "data": logs
    }


@router.get("/users", summary="获取所有用户积分（管理员）")
async def get_all_credits(current_user: dict = Depends(require_permission("user:read"))):
    """获取所有用户的积分信息（需要管理员权限）"""
    service = get_credit_service()
    users = service.get_all_users_credits()
    return {
        "success": True,
        "data": users
    }


@router.get("/user/{user_id}", summary="获取指定用户积分（管理员）")
async def get_user_credits(
    user_id: int,
    current_user: dict = Depends(require_permission("user:read"))
):
    """获取指定用户的积分信息"""
    service = get_credit_service()
    credits = service.get_user_credits(user_id)
    if credits is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user_repo = get_user_repository()
    user = user_repo.get_by_id(user_id)
    
    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "username": user['username'],
            "credits": credits
        }
    }


@router.get("/user/{user_id}/logs", summary="获取指定用户积分记录（管理员）")
async def get_user_credit_logs(
    user_id: int,
    limit: int = 50,
    current_user: dict = Depends(require_permission("user:read"))
):
    """获取指定用户的积分变动记录"""
    service = get_credit_service()
    logs = service.get_credit_logs(user_id, limit)
    return {
        "success": True,
        "data": logs
    }


@router.post("/set", summary="设置用户积分（管理员）")
async def set_user_credits(
    request: CreditSetRequest,
    current_user: dict = Depends(require_permission("settings:write"))
):
    """设置用户积分（需要管理员权限）"""
    service = get_credit_service()
    success = service.set_credits(
        request.user_id, 
        request.credits, 
        current_user['username'],
        request.description
    )
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "success": True,
        "message": f"已将用户积分设置为 {request.credits}"
    }


@router.post("/adjust", summary="调整用户积分（管理员）")
async def adjust_user_credits(
    request: CreditAdjustRequest,
    current_user: dict = Depends(require_permission("settings:write"))
):
    """调整用户积分（需要管理员权限）"""
    service = get_credit_service()
    success, balance, error = service.adjust_credits(
        request.user_id,
        request.amount,
        request.action,
        request.description
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "success": True,
        "message": f"积分调整成功",
        "data": {
            "balance": balance
        }
    }
