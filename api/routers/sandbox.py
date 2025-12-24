# -*- coding: utf-8 -*-
"""
Sandbox API 路由

提供 AIO Sandbox 的 API 代理和状态管理
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from api.services.sandbox_service import get_sandbox_service, SandboxService
from api.services.recording_service import get_recording_service

router = APIRouter(prefix="/sandbox", tags=["Sandbox"])


# ==================== 请求模型 ====================

class ShellExecRequest(BaseModel):
    command: str
    cwd: Optional[str] = None


class FileReadRequest(BaseModel):
    file_path: str


class FileWriteRequest(BaseModel):
    file_path: str
    content: str


class FileListRequest(BaseModel):
    directory: str


class CodeExecuteRequest(BaseModel):
    code: str
    language: str = "python"


class BrowserGotoRequest(BaseModel):
    url: str


# ==================== API 端点 ====================

@router.get("/status")
async def get_sandbox_status():
    """获取 Sandbox 状态"""
    service = get_sandbox_service()
    return service.get_status()


@router.get("/urls")
async def get_sandbox_urls():
    """获取 Sandbox 各服务的 URL"""
    service = get_sandbox_service()
    return {
        "vnc": service.get_vnc_url(),
        "vscode": service.get_vscode_url(),
        "docs": service.get_docs_url(),
        "base": service.base_url,
    }


@router.post("/shell/exec")
async def exec_shell(request: ShellExecRequest):
    """执行 Shell 命令"""
    service = get_sandbox_service()
    result = service.exec_shell(request.command, request.cwd)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/file/read")
async def read_file(request: FileReadRequest):
    """读取文件"""
    service = get_sandbox_service()
    result = service.read_file(request.file_path)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/file/write")
async def write_file(request: FileWriteRequest):
    """写入文件"""
    service = get_sandbox_service()
    result = service.write_file(request.file_path, request.content)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/file/list")
async def list_files(request: FileListRequest):
    """列出目录"""
    service = get_sandbox_service()
    result = service.list_files(request.directory)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/code/execute")
async def execute_code(request: CodeExecuteRequest):
    """执行代码"""
    service = get_sandbox_service()
    if request.language == "python":
        result = service.execute_python(request.code)
    else:
        # 其他语言通过 shell 执行
        result = service.exec_shell(f"echo '{request.code}' | node")
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/browser/goto")
async def browser_goto(request: BrowserGotoRequest):
    """浏览器导航"""
    service = get_sandbox_service()
    result = service.browser_goto(request.url)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/browser/screenshot")
async def browser_screenshot():
    """浏览器截图"""
    service = get_sandbox_service()
    result = service.browser_screenshot()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/browser/info")
async def get_browser_info():
    """获取浏览器信息"""
    service = get_sandbox_service()
    result = service.get_browser_info()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


# ==================== Agent 执行 ====================

class AgentExecuteRequest(BaseModel):
    message: str
    use_sandbox: bool = True


@router.post("/agents/sandbox/execute")
async def execute_sandbox_agent(request: AgentExecuteRequest):
    """
    执行 SandboxUse 智能体任务
    
    智能体会分析用户指令，自动调用相应的 AIO Sandbox API：
    - Shell 命令执行
    - 文件操作（读取、写入、列出目录）
    - Python 代码执行
    - 浏览器操作（导航、截图、点击、输入等）
    """
    import os
    from agentscope.message import Msg
    from agents.sandbox_agent import get_sandbox_agent, get_sandbox_tools
    
    service = get_sandbox_service()
    
    # 检查 Sandbox 连接
    if not service.health_check():
        return {
            "success": False,
            "response": "Sandbox 服务未启动，请先启动 AIO Sandbox 容器",
            "files": [],
            "summary": ""
        }
    
    try:
        # 获取 API 密钥
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        
        # 获取录制服务
        recording_service = get_recording_service()
        
        # 如果正在录制，记录用户输入
        if recording_service.is_recording():
            # 截图
            screenshot = None
            try:
                screenshot_result = service.browser_screenshot()
                if screenshot_result.get("success"):
                    screenshot = screenshot_result.get("screenshot")
            except:
                pass
            
            recording_service.add_step(
                step_type="user_input",
                content=request.message,
                screenshot=screenshot
            )
        
        # 获取 SandboxUse 智能体
        agent = get_sandbox_agent(
            api_key=api_key,
            model_name="qwen3-max",
            sandbox_url=service.base_url
        )
        
        # 创建用户消息并执行
        user_msg = Msg("user", request.message, "user")
        result = await agent(user_msg)
        
        # 提取响应内容（确保是字符串）
        response_text = ""
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, str):
                response_text = content
            elif isinstance(content, list):
                # 可能是 [{type: 'text', text: '...'}] 格式
                response_text = "\n".join(
                    c.get('text', '') if isinstance(c, dict) else str(c) 
                    for c in content
                )
            else:
                response_text = str(content)
        else:
            response_text = str(result)
        
        # 如果正在录制，记录 AI 响应
        if recording_service.is_recording():
            # 截图
            screenshot = None
            try:
                screenshot_result = service.browser_screenshot()
                if screenshot_result.get("success"):
                    screenshot = screenshot_result.get("screenshot")
            except:
                pass
            
            recording_service.add_step(
                step_type="ai_response",
                content=response_text,
                screenshot=screenshot
            )
        
        # 获取文件列表
        files = []
        try:
            file_result = service.list_files("/home/user")
            if file_result.get("success"):
                files = [
                    {"name": f, "path": f"/home/user/{f}", "size": "-"}
                    for f in file_result.get("files", [])
                ]
        except Exception:
            pass
        
        # 根据响应内容判断应该切换到哪个标签页
        active_tab = "vnc"  # 默认屏幕
        response_lower = response_text.lower()
        if "命令执行" in response_text or "shell" in response_lower or "ls" in response_lower:
            active_tab = "terminal"
        elif "文件内容" in response_text or "读取文件" in response_text or "编辑" in response_text:
            active_tab = "editor"
        elif "浏览器" in response_text or "导航" in response_text or "网页" in response_text:
            active_tab = "vnc"
        
        return {
            "success": True,
            "response": response_text,
            "files": files,
            "active_tab": active_tab,
            "summary": f"已处理: {request.message[:30]}..." if len(request.message) > 30 else f"已处理: {request.message}",
            "suggested_questions": [
                "帮我查看当前目录的文件",
                "执行 Python 代码打印系统信息",
                "打开浏览器访问百度"
            ]
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "response": f"执行出错: {str(e)}",
            "files": [],
            "summary": ""
        }


# ==================== 录制回放 API ====================

class RecordingStartRequest(BaseModel):
    name: Optional[str] = None


@router.post("/recording/start")
async def start_recording(request: RecordingStartRequest = None):
    """开始录制"""
    service = get_recording_service()
    
    if service.is_recording():
        return {
            "success": False,
            "message": "已有录制正在进行中",
            "recording_id": service.get_current_recording_id()
        }
    
    name = request.name if request else None
    recording_id = service.start_recording(name)
    
    return {
        "success": True,
        "message": "录制已开始",
        "recording_id": recording_id
    }


@router.post("/recording/stop")
async def stop_recording():
    """停止录制"""
    service = get_recording_service()
    
    if not service.is_recording():
        return {
            "success": False,
            "message": "当前没有进行中的录制"
        }
    
    recording = service.stop_recording()
    
    return {
        "success": True,
        "message": "录制已保存",
        "recording": {
            "id": recording["id"],
            "name": recording["name"],
            "duration": recording["duration"],
            "steps_count": len(recording["steps"])
        }
    }


@router.get("/recording/status")
async def get_recording_status():
    """获取录制状态"""
    service = get_recording_service()
    
    return {
        "is_recording": service.is_recording(),
        "recording_id": service.get_current_recording_id()
    }


@router.get("/recordings")
async def list_recordings():
    """列出所有录制"""
    service = get_recording_service()
    recordings = service.list_recordings()
    
    return {
        "success": True,
        "recordings": recordings
    }


@router.get("/recording/{recording_id}")
async def get_recording(recording_id: str):
    """获取录制详情（用于回放）"""
    service = get_recording_service()
    recording = service.get_recording(recording_id)
    
    if recording is None:
        raise HTTPException(status_code=404, detail="录制不存在")
    
    return {
        "success": True,
        "recording": recording
    }


@router.delete("/recording/{recording_id}")
async def delete_recording(recording_id: str):
    """删除录制"""
    service = get_recording_service()
    
    if service.delete_recording(recording_id):
        return {"success": True, "message": "录制已删除"}
    else:
        raise HTTPException(status_code=404, detail="录制不存在")
