# -*- coding: utf-8 -*-
"""
AIO Sandbox 工具函数

提供给 Agent 调用的沙箱操作工具
"""
import httpx
from typing import Optional

SANDBOX_BASE_URL = "http://localhost:988"


def sandbox_shell(command: str, cwd: Optional[str] = None) -> str:
    """
    在沙箱中执行 Shell 命令
    
    Args:
        command: 要执行的 Shell 命令
        cwd: 工作目录（可选）
    
    Returns:
        命令执行的输出结果
    """
    try:
        payload = {"command": command}
        if cwd:
            payload["cwd"] = cwd
        
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{SANDBOX_BASE_URL}/v1/shell/exec", json=payload)
            
            if resp.status_code == 200:
                data = resp.json()
                output = data.get("data", {}).get("output", "")
                exit_code = data.get("data", {}).get("exit_code", 0)
                if exit_code != 0:
                    return f"[Exit Code: {exit_code}]\n{output}"
                return output
            else:
                return f"[Error] HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"[Error] {str(e)}"


def sandbox_python(code: str) -> str:
    """
    在沙箱的 Jupyter 环境中执行 Python 代码
    
    Args:
        code: 要执行的 Python 代码
    
    Returns:
        代码执行的输出结果
    """
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                f"{SANDBOX_BASE_URL}/v1/jupyter/execute",
                json={"code": code}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                output = data.get("data", {}).get("output", "")
                result = data.get("data", {}).get("result")
                if result:
                    return f"{output}\n[Result]: {result}"
                return output
            else:
                return f"[Error] HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"[Error] {str(e)}"


def sandbox_file_write(file_path: str, content: str) -> str:
    """
    在沙箱中写入文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
    
    Returns:
        操作结果
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{SANDBOX_BASE_URL}/v1/file/write",
                json={"file": file_path, "content": content}
            )
            
            if resp.status_code == 200:
                return f"[Success] 文件已写入: {file_path}"
            else:
                return f"[Error] HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"[Error] {str(e)}"


def sandbox_file_read(file_path: str) -> str:
    """
    读取沙箱中的文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件内容
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{SANDBOX_BASE_URL}/v1/file/read",
                json={"file": file_path}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("content", "")
            else:
                return f"[Error] HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"[Error] {str(e)}"


def sandbox_file_list(directory: str = "/home/user") -> str:
    """
    列出沙箱中的目录内容
    
    Args:
        directory: 目录路径
    
    Returns:
        目录内容列表
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{SANDBOX_BASE_URL}/v1/file/list",
                json={"directory": directory}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                files = data.get("data", {}).get("files", [])
                if files:
                    return "\n".join([f"- {f}" for f in files])
                return "[Empty directory]"
            else:
                return f"[Error] HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"[Error] {str(e)}"


def sandbox_browser_goto(url: str) -> str:
    """
    控制沙箱浏览器访问指定 URL
    
    Args:
        url: 目标 URL
    
    Returns:
        操作结果
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{SANDBOX_BASE_URL}/v1/browser/goto",
                json={"url": url}
            )
            
            if resp.status_code == 200:
                return f"[Success] 浏览器已导航到: {url}"
            else:
                return f"[Error] HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"[Error] {str(e)}"


def sandbox_browser_screenshot() -> str:
    """
    对沙箱浏览器当前页面截图
    
    Returns:
        截图的 base64 数据或错误信息
    """
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{SANDBOX_BASE_URL}/v1/browser/screenshot")
            
            if resp.status_code == 200:
                data = resp.json()
                screenshot = data.get("data", {}).get("screenshot", "")
                if screenshot:
                    return f"[Screenshot captured] data:image/png;base64,{screenshot[:100]}..."
                return "[Success] Screenshot captured"
            else:
                return f"[Error] HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return f"[Error] {str(e)}"
