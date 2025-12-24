# -*- coding: utf-8 -*-
"""
AIO Sandbox 服务模块

提供与 AIO Sandbox 的集成，实现类似 Manus 的功能：
- Shell 命令执行
- 文件操作
- 代码执行
- 浏览器自动化
- VNC 可视化
"""
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class SandboxActionType(str, Enum):
    """Sandbox 操作类型"""
    SHELL = "shell"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_LIST = "file_list"
    CODE_EXECUTE = "code_execute"
    BROWSER_GOTO = "browser_goto"
    BROWSER_SCREENSHOT = "browser_screenshot"
    BROWSER_CLICK = "browser_click"


@dataclass
class SandboxAction:
    """Sandbox 操作记录"""
    action_type: SandboxActionType
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


@dataclass
class SandboxTask:
    """Sandbox 任务"""
    task_id: str
    title: str
    status: str = "running"  # running, completed, failed
    actions: List[SandboxAction] = field(default_factory=list)
    files: List[str] = field(default_factory=list)


class SandboxService:
    """AIO Sandbox 服务类"""
    
    def __init__(self, base_url: str = "http://localhost:988"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=60.0)
        self._home_dir: Optional[str] = None
        self._current_task: Optional[SandboxTask] = None
    
    @property
    def home_dir(self) -> str:
        """获取 Sandbox 的 home 目录"""
        if not self._home_dir:
            try:
                resp = self.client.get(f"{self.base_url}/v1/sandbox/context")
                if resp.status_code == 200:
                    self._home_dir = resp.json().get("home_dir", "/home/user")
            except Exception:
                self._home_dir = "/home/user"
        return self._home_dir
    
    def get_vnc_url(self) -> str:
        """获取 VNC 可视化地址"""
        return f"{self.base_url}/vnc/index.html?autoconnect=true"
    
    def get_vscode_url(self) -> str:
        """获取 VSCode Server 地址"""
        return f"{self.base_url}/code-server/"
    
    def get_docs_url(self) -> str:
        """获取 API 文档地址"""
        return f"{self.base_url}/v1/docs"
    
    # ==================== Shell 操作 ====================
    
    def exec_shell(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """执行 Shell 命令"""
        try:
            payload = {"command": command}
            if cwd:
                payload["cwd"] = cwd
            
            resp = self.client.post(
                f"{self.base_url}/v1/shell/exec",
                json=payload
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "output": data.get("data", {}).get("output", ""),
                    "exit_code": data.get("data", {}).get("exit_code", 0)
                }
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== 文件操作 ====================
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """读取文件内容"""
        try:
            resp = self.client.post(
                f"{self.base_url}/v1/file/read",
                json={"file": file_path}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "content": data.get("data", {}).get("content", "")
                }
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        try:
            resp = self.client.post(
                f"{self.base_url}/v1/file/write",
                json={"file": file_path, "content": content}
            )
            
            if resp.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_files(self, directory: str) -> Dict[str, Any]:
        """列出目录文件"""
        try:
            resp = self.client.post(
                f"{self.base_url}/v1/file/list",
                json={"directory": directory}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "files": data.get("data", {}).get("files", [])
                }
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== 代码执行 ====================
    
    def execute_python(self, code: str) -> Dict[str, Any]:
        """通过 Jupyter 执行 Python 代码"""
        try:
            resp = self.client.post(
                f"{self.base_url}/v1/jupyter/execute",
                json={"code": code}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "output": data.get("data", {}).get("output", ""),
                    "result": data.get("data", {}).get("result")
                }
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== 浏览器操作 ====================
    
    def browser_goto(self, url: str) -> Dict[str, Any]:
        """浏览器导航到指定 URL"""
        try:
            resp = self.client.post(
                f"{self.base_url}/v1/browser/goto",
                json={"url": url}
            )
            
            if resp.status_code == 200:
                return {"success": True}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def browser_screenshot(self) -> Dict[str, Any]:
        """浏览器截图"""
        try:
            resp = self.client.post(f"{self.base_url}/v1/browser/screenshot")
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "screenshot": data.get("data", {}).get("screenshot", "")
                }
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_browser_info(self) -> Dict[str, Any]:
        """获取浏览器信息（包括 CDP URL）"""
        try:
            resp = self.client.get(f"{self.base_url}/v1/browser/info")
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "cdp_url": data.get("data", {}).get("cdp_url", ""),
                    "ws_url": data.get("data", {}).get("ws_url", "")
                }
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== 健康检查 ====================
    
    def health_check(self) -> bool:
        """检查 Sandbox 服务是否可用"""
        try:
            # AIO Sandbox 没有 /v1/health 端点，用 shell exec 测试
            resp = self.client.post(
                f"{self.base_url}/v1/shell/exec",
                json={"command": "echo ok"},
                timeout=5.0
            )
            return resp.status_code == 200
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Sandbox 状态信息"""
        is_healthy = self.health_check()
        return {
            "available": is_healthy,
            "base_url": self.base_url,
            "vnc_url": self.get_vnc_url() if is_healthy else None,
            "vscode_url": self.get_vscode_url() if is_healthy else None,
            "docs_url": self.get_docs_url() if is_healthy else None,
        }


# 全局单例
_sandbox_service: Optional[SandboxService] = None


def get_sandbox_service(base_url: str = "http://localhost:988") -> SandboxService:
    """获取 Sandbox 服务单例"""
    global _sandbox_service
    if _sandbox_service is None:
        _sandbox_service = SandboxService(base_url)
    return _sandbox_service
