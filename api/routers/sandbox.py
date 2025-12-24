# -*- coding: utf-8 -*-
"""
Sandbox API 路由

提供 AIO Sandbox 的 API 代理和状态管理
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from api.services.sandbox_service import get_sandbox_service, SandboxService

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
    执行 Sandbox Agent 任务
    
    简化版：直接调用 Sandbox 服务执行命令
    """
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
        message = request.message.strip()
        response_text = ""
        
        # 简单解析用户意图并执行
        if message.startswith("!") or message.startswith("shell:"):
            # 直接执行 shell 命令
            cmd = message.lstrip("!").replace("shell:", "").strip()
            result = service.exec_shell(cmd)
            if result.get("success"):
                response_text = f"命令执行成功:\n```\n{result.get('output', '')}\n```"
            else:
                response_text = f"命令执行失败: {result.get('error', '未知错误')}"
        
        elif message.startswith("python:") or "执行python" in message.lower():
            # 执行 Python 代码
            code = message.replace("python:", "").strip()
            if not code or "执行python" in message.lower():
                code = "print('Hello from Sandbox!')"
            result = service.execute_python(code)
            if result.get("success"):
                response_text = f"Python 执行结果:\n```\n{result.get('output', '')}\n```"
            else:
                response_text = f"执行失败: {result.get('error', '未知错误')}"
        
        elif "创建文件" in message or "写入文件" in message:
            # 创建示例文件
            filename = "/home/user/example.md"
            content = f"# 由 Manus AI 创建\n\n任务: {message}\n\n创建时间: {__import__('datetime').datetime.now()}"
            result = service.write_file(filename, content)
            if result.get("success"):
                response_text = f"✅ 文件已创建: {filename}"
            else:
                response_text = f"创建文件失败: {result.get('error', '未知错误')}"
        
        elif "列出文件" in message or "查看文件" in message:
            # 列出文件
            result = service.list_files("/home/user")
            if result.get("success"):
                files = result.get("files", [])
                response_text = f"📁 /home/user 目录下的文件:\n" + "\n".join([f"  - {f}" for f in files]) if files else "目录为空"
            else:
                response_text = f"列出文件失败: {result.get('error', '未知错误')}"
        
        else:
            # 默认：执行为 shell 命令
            result = service.exec_shell(message)
            if result.get("success"):
                output = result.get('output', '').strip()
                response_text = f"执行结果:\n```\n{output}\n```" if output else "✅ 命令已执行（无输出）"
            else:
                response_text = f"我收到了你的消息: \"{message}\"\n\n💡 提示：你可以尝试：\n- 输入 shell 命令（如 `ls -la`）\n- 输入 `python: print('hello')` 执行 Python\n- 说 \"创建文件\" 来创建示例文件"
        
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
        
        return {
            "success": True,
            "response": response_text,
            "files": files,
            "summary": f"已处理: {message[:30]}..." if len(message) > 30 else f"已处理: {message}",
            "suggested_questions": [
                "ls -la 查看文件",
                "python: import sys; print(sys.version)",
                "创建文件"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "response": f"执行出错: {str(e)}",
            "files": [],
            "summary": ""
        }
