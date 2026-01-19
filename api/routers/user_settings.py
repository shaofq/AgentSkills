# -*- coding: utf-8 -*-
"""用户设置API"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import json

from api.services.database import get_database
from api.services.auth_service import get_current_user

router = APIRouter(prefix="/api/user-settings", tags=["用户设置"])


class SettingUpdate(BaseModel):
    """设置更新请求"""
    value: Any


class SettingResponse(BaseModel):
    """设置响应"""
    key: str
    value: Any
    updated_at: str


class UserSettingsService:
    """用户设置服务"""
    
    def __init__(self):
        self.db = get_database()
    
    def get_setting(self, user_id: int, key: str) -> Optional[Any]:
        """获取用户设置"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT setting_value FROM user_settings WHERE user_id = ? AND setting_key = ?',
                (user_id, key)
            )
            row = cursor.fetchone()
            if row and row['setting_value']:
                try:
                    return json.loads(row['setting_value'])
                except json.JSONDecodeError:
                    return row['setting_value']
            return None
    
    def set_setting(self, user_id: int, key: str, value: Any) -> bool:
        """保存用户设置"""
        now = datetime.now().isoformat()
        value_json = json.dumps(value, ensure_ascii=False) if value is not None else None
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # 使用 UPSERT 语法
            cursor.execute('''
                INSERT INTO user_settings (user_id, setting_key, setting_value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, setting_key) 
                DO UPDATE SET setting_value = ?, updated_at = ?
            ''', (user_id, key, value_json, now, now, value_json, now))
            conn.commit()
            return True
    
    def delete_setting(self, user_id: int, key: str) -> bool:
        """删除用户设置"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM user_settings WHERE user_id = ? AND setting_key = ?',
                (user_id, key)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_all_settings(self, user_id: int) -> Dict[str, Any]:
        """获取用户所有设置"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?',
                (user_id,)
            )
            result = {}
            for row in cursor.fetchall():
                key = row['setting_key']
                value = row['setting_value']
                if value:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
                else:
                    result[key] = None
            return result


# 服务单例
_settings_service: Optional[UserSettingsService] = None


def get_settings_service() -> UserSettingsService:
    global _settings_service
    if _settings_service is None:
        _settings_service = UserSettingsService()
    return _settings_service


# ========== API 路由 ==========

@router.get("")
async def get_all_settings(current_user: dict = Depends(get_current_user)):
    """获取当前用户的所有设置"""
    service = get_settings_service()
    settings = service.get_all_settings(current_user['id'])
    return {"settings": settings}


@router.get("/{key}")
async def get_setting(key: str, current_user: dict = Depends(get_current_user)):
    """获取指定设置"""
    service = get_settings_service()
    value = service.get_setting(current_user['id'], key)
    return {"key": key, "value": value}


@router.put("/{key}")
async def set_setting(key: str, data: SettingUpdate, current_user: dict = Depends(get_current_user)):
    """保存设置"""
    service = get_settings_service()
    service.set_setting(current_user['id'], key, data.value)
    return {"key": key, "value": data.value, "message": "设置已保存"}


@router.delete("/{key}")
async def delete_setting(key: str, current_user: dict = Depends(get_current_user)):
    """删除设置"""
    service = get_settings_service()
    deleted = service.delete_setting(current_user['id'], key)
    if not deleted:
        raise HTTPException(status_code=404, detail="设置不存在")
    return {"message": "设置已删除"}


# ========== 列映射配置专用API ==========

@router.get("/crew-compare/column-mapping")
async def get_column_mapping(current_user: dict = Depends(get_current_user)):
    """获取船员比对列映射配置"""
    service = get_settings_service()
    mapping = service.get_setting(current_user['id'], 'crew_compare_column_mapping')
    return {"mapping": mapping or {}}


@router.put("/crew-compare/column-mapping")
async def save_column_mapping(data: SettingUpdate, current_user: dict = Depends(get_current_user)):
    """保存船员比对列映射配置"""
    service = get_settings_service()
    service.set_setting(current_user['id'], 'crew_compare_column_mapping', data.value)
    return {"message": "列映射配置已保存", "mapping": data.value}
