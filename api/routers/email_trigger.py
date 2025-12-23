# -*- coding: utf-8 -*-
"""邮件触发 API 路由"""
import os
import json
import asyncio
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from api.services.email_listener import EmailListener, EmailListenerManager, EmailMessage

router = APIRouter(prefix="/email", tags=["email-trigger"])

# 全局邮件监听管理器
_email_manager: Optional[EmailListenerManager] = None
_polling_task: Optional[asyncio.Task] = None


class EmailAccountConfig(BaseModel):
    """邮箱账户配置"""
    id: str
    name: str
    email: str
    imap_server: str
    imap_port: int = 993
    use_ssl: bool = True
    username: str
    password_env: str
    enabled: bool = True


class WorkflowBinding(BaseModel):
    """工作流绑定配置"""
    workflow_name: str
    conditions: dict = {}
    default: bool = False


class EmailTriggerConfig(BaseModel):
    """邮件触发配置"""
    enabled: bool = True
    poll_interval_seconds: int = 30
    email_accounts: List[dict] = []


class TestEmailRequest(BaseModel):
    """测试邮件连接请求"""
    imap_server: str
    imap_port: int = 993
    use_ssl: bool = True
    username: str
    password: str


class ManualFetchRequest(BaseModel):
    """手动拉取邮件请求"""
    account_id: str


async def workflow_trigger_callback(workflow_name: str, user_input: str, email_data: dict):
    """工作流触发回调函数
    
    当邮件匹配到工作流时，调用此函数触发工作流执行。
    """
    from api.routers.execution import run_predefined_workflow_internal
    
    try:
        # 调用工作流执行
        result = await run_predefined_workflow_internal(
            workflow_name=workflow_name,
            user_input=user_input,
            history_messages=[]
        )
        
        print(f"[EmailTrigger] 工作流 {workflow_name} 执行完成")
        return result
        
    except Exception as e:
        print(f"[EmailTrigger] 工作流 {workflow_name} 执行失败: {e}")
        raise


def get_email_manager() -> EmailListenerManager:
    """获取邮件监听管理器单例"""
    global _email_manager
    if _email_manager is None:
        _email_manager = EmailListenerManager()
        _email_manager.load_config()
        _email_manager.set_workflow_callback(workflow_trigger_callback)
    return _email_manager


@router.get("/config")
async def get_email_config():
    """获取邮件触发配置"""
    config_path = "config/email_triggers.json"
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 隐藏敏感信息
        for account in config.get("email_accounts", []):
            if "password_env" in account:
                account["password_configured"] = bool(os.environ.get(account["password_env"]))
        
        return {"success": True, "config": config}
    
    except FileNotFoundError:
        return {"success": False, "error": "配置文件不存在", "config": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def save_email_config(config: EmailTriggerConfig):
    """保存邮件触发配置"""
    config_path = "config/email_triggers.json"
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.dict(), f, ensure_ascii=False, indent=2)
        
        # 重新加载配置
        manager = get_email_manager()
        manager.load_config()
        
        return {"success": True, "message": "配置已保存"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_email_connection(request: TestEmailRequest):
    """测试邮箱连接"""
    import imaplib
    
    try:
        if request.use_ssl:
            imap = imaplib.IMAP4_SSL(request.imap_server, request.imap_port)
        else:
            imap = imaplib.IMAP4(request.imap_server, request.imap_port)
        
        imap.login(request.username, request.password)
        
        # 获取邮箱信息
        status, folders = imap.list()
        folder_count = len(folders) if status == "OK" else 0
        
        # 获取收件箱未读数
        imap.select("INBOX")
        status, messages = imap.search(None, "UNSEEN")
        unread_count = len(messages[0].split()) if status == "OK" and messages[0] else 0
        
        imap.logout()
        
        return {
            "success": True,
            "message": "连接成功",
            "details": {
                "folder_count": folder_count,
                "unread_count": unread_count
            }
        }
    
    except imaplib.IMAP4.error as e:
        return {"success": False, "message": f"IMAP 错误: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}


@router.post("/start")
async def start_email_listener(background_tasks: BackgroundTasks):
    """启动邮件监听服务"""
    global _polling_task
    
    manager = get_email_manager()
    
    if _polling_task and not _polling_task.done():
        return {"success": False, "message": "邮件监听服务已在运行"}
    
    if not manager.config.get("enabled", False):
        return {"success": False, "message": "邮件监听服务未启用，请先在配置中启用"}
    
    # 在后台启动监听
    _polling_task = asyncio.create_task(manager.start_all())
    
    return {
        "success": True,
        "message": "邮件监听服务已启动",
        "accounts": [acc.get("id") for acc in manager.config.get("email_accounts", []) if acc.get("enabled", True)]
    }


@router.post("/stop")
async def stop_email_listener():
    """停止邮件监听服务"""
    global _polling_task
    
    manager = get_email_manager()
    await manager.stop_all()
    
    if _polling_task:
        _polling_task.cancel()
        _polling_task = None
    
    return {"success": True, "message": "邮件监听服务已停止"}


@router.get("/status")
async def get_email_listener_status():
    """获取邮件监听服务状态"""
    global _polling_task
    
    manager = get_email_manager()
    
    is_running = _polling_task is not None and not _polling_task.done()
    
    listeners_status = []
    for account_id, listener in manager.listeners.items():
        listeners_status.append({
            "account_id": account_id,
            "is_running": listener.is_running,
            "connected": listener.imap is not None
        })
    
    return {
        "success": True,
        "is_running": is_running,
        "listeners": listeners_status,
        "config_enabled": manager.config.get("enabled", False)
    }


@router.post("/fetch")
async def manual_fetch_emails(request: ManualFetchRequest):
    """手动拉取指定账户的邮件"""
    manager = get_email_manager()
    
    # 查找账户配置
    account_config = None
    for acc in manager.config.get("email_accounts", []):
        if acc.get("id") == request.account_id:
            account_config = acc
            break
    
    if not account_config:
        raise HTTPException(status_code=404, detail=f"未找到账户: {request.account_id}")
    
    # 创建临时监听器
    listener = EmailListener(account_config)
    listener.set_workflow_callback(workflow_trigger_callback)
    
    try:
        connected = await listener.connect()
        if not connected:
            return {"success": False, "message": "连接邮箱失败"}
        
        results = await listener.process_emails()
        await listener.disconnect()
        
        return {
            "success": True,
            "message": f"处理了 {len(results)} 封邮件",
            "results": results
        }
    
    except Exception as e:
        await listener.disconnect()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_email_trigger_history(limit: int = 50):
    """获取邮件触发历史记录
    
    TODO: 实现持久化存储后，从数据库读取历史记录
    """
    return {
        "success": True,
        "message": "历史记录功能待实现",
        "history": []
    }
