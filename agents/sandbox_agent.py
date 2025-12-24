# -*- coding: utf-8 -*-
"""
SandboxUse 智能体

基于 AIO Sandbox 的智能体，能够根据用户指令执行：
- Shell 命令执行
- 文件操作（读取、写入、列出目录）
- Python 代码执行
- 浏览器操作（导航、截图、点击、输入等）
"""
import os
import json
import httpx
from typing import Optional, Dict, Any, List
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, ToolResponse
from agentscope.message import TextBlock


class SandboxTools:
    """AIO Sandbox 工具集"""
    
    def __init__(self, base_url: str = "http://localhost:988"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=60.0)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送请求到 Sandbox API"""
        try:
            url = f"{self.base_url}{endpoint}"
            if method.upper() == "GET":
                resp = self.client.get(url, **kwargs)
            else:
                resp = self.client.post(url, **kwargs)
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局工具实例
_sandbox_tools: Optional[SandboxTools] = None


def get_sandbox_tools(base_url: str = "http://localhost:988") -> SandboxTools:
    """获取 Sandbox 工具实例"""
    global _sandbox_tools
    if _sandbox_tools is None:
        _sandbox_tools = SandboxTools(base_url)
    return _sandbox_tools


def make_response(text: str, tool_name: str = "") -> ToolResponse:
    """创建 ToolResponse 对象，并在录制时自动添加步骤"""
    # 如果正在录制，添加工具调用步骤
    try:
        from api.services.recording_service import get_recording_service
        from api.services.sandbox_service import get_sandbox_service
        
        recording_service = get_recording_service()
        if recording_service.is_recording():
            # 获取截图
            screenshot = None
            try:
                sandbox_service = get_sandbox_service()
                screenshot_result = sandbox_service.browser_screenshot()
                if screenshot_result.get("success"):
                    screenshot = screenshot_result.get("screenshot")
            except:
                pass
            
            # 添加工具调用步骤
            recording_service.add_step(
                step_type="tool_call",
                content=f"[{tool_name}] {text}" if tool_name else text,
                screenshot=screenshot
            )
    except:
        pass
    
    # agentscope 期望 block 包含 type 字段
    return ToolResponse(content=[{"type": "text", "text": text}])


# ==================== Shell 工具 ====================

def sandbox_shell(command: str, cwd: str = "/home/user") -> ToolResponse:
    """
    在 Sandbox 中执行 Shell 命令。
    
    Args:
        command: 要执行的 shell 命令，如 "ls -la", "pwd", "cat file.txt" 等
        cwd: 工作目录，默认为 /home/user
        
    Returns:
        命令执行结果，包含输出内容或错误信息
        
    Example:
        >>> sandbox_shell("ls -la")
        >>> sandbox_shell("echo 'Hello World'")
        >>> sandbox_shell("python --version")
    """
    tools = get_sandbox_tools()
    payload = {"command": command}
    if cwd:
        payload["cwd"] = cwd
    
    result = tools._request("POST", "/v1/shell/exec", json=payload)
    
    if result.get("success"):
        data = result.get("data", {})
        output = data.get("output", "")
        exit_code = data.get("exit_code", 0)
        if exit_code == 0:
            text = f"命令执行成功:\n{output}" if output else "命令执行成功（无输出）"
        else:
            text = f"命令执行完成（退出码: {exit_code}）:\n{output}"
    else:
        text = f"命令执行失败: {result.get('error', '未知错误')}"
    return make_response(text, "shell")


# ==================== 文件操作工具 ====================

def sandbox_file_read(file_path: str) -> ToolResponse:
    """
    读取 Sandbox 中的文件内容。
    
    Args:
        file_path: 文件的完整路径，如 "/home/user/example.txt"
        
    Returns:
        文件内容或错误信息
        
    Example:
        >>> sandbox_file_read("/home/user/readme.md")
        >>> sandbox_file_read("/home/user/.bashrc")
    """
    tools = get_sandbox_tools()
    result = tools._request("POST", "/v1/file/read", json={"file": file_path})
    
    if result.get("success"):
        content = result.get("data", {}).get("content", "")
        text = f"文件内容:\n{content}"
    else:
        text = f"读取文件失败: {result.get('error', '未知错误')}"
    return make_response(text, "file_read")


def sandbox_file_write(file_path: str, content: str) -> ToolResponse:
    """
    在 Sandbox 中写入文件。
    
    Args:
        file_path: 文件的完整路径，如 "/home/user/output.txt"
        content: 要写入的内容
        
    Returns:
        操作结果
        
    Example:
        >>> sandbox_file_write("/home/user/hello.txt", "Hello World!")
        >>> sandbox_file_write("/home/user/script.py", "print('hello')")
    """
    tools = get_sandbox_tools()
    result = tools._request("POST", "/v1/file/write", json={"file": file_path, "content": content})
    
    if result.get("success"):
        text = f"文件已成功写入: {file_path}"
    else:
        text = f"写入文件失败: {result.get('error', '未知错误')}"
    return make_response(text, "file_write")


def sandbox_file_list(directory: str = "/home/user") -> ToolResponse:
    """
    列出 Sandbox 中指定目录的文件和子目录。
    
    Args:
        directory: 目录路径，默认为 /home/user
        
    Returns:
        目录内容列表
        
    Example:
        >>> sandbox_file_list("/home/user")
        >>> sandbox_file_list("/tmp")
    """
    tools = get_sandbox_tools()
    result = tools._request("POST", "/v1/file/list", json={"directory": directory})
    
    if result.get("success"):
        files = result.get("data", {}).get("files", [])
        if files:
            text = f"目录 {directory} 内容:\n" + "\n".join([f"  - {f}" for f in files])
        else:
            text = f"目录 {directory} 为空"
    else:
        text = f"列出目录失败: {result.get('error', '未知错误')}"
    return make_response(text, "file_list")


# ==================== Python 代码执行工具 ====================

def sandbox_python(code: str) -> ToolResponse:
    """
    在 Sandbox 中执行 Python 代码（通过 Jupyter）。
    
    Args:
        code: Python 代码字符串
        
    Returns:
        代码执行结果
        
    Example:
        >>> sandbox_python("print('Hello World')")
        >>> sandbox_python("import sys; print(sys.version)")
        >>> sandbox_python("import pandas as pd; df = pd.DataFrame({'a': [1,2,3]}); print(df)")
    """
    tools = get_sandbox_tools()
    result = tools._request("POST", "/v1/jupyter/execute", json={"code": code})
    
    if result.get("success"):
        data = result.get("data", {})
        output = data.get("output", "")
        exec_result = data.get("result")
        
        text = "Python 执行结果:\n"
        if output:
            text += output
        if exec_result:
            text += f"\n返回值: {exec_result}"
        if not output and not exec_result:
            text = "代码执行成功（无输出）"
    else:
        text = f"Python 执行失败: {result.get('error', '未知错误')}"
    return make_response(text, "python")


# ==================== 浏览器操作工具 ====================

def sandbox_browser_goto(url: str) -> ToolResponse:
    """
    控制 Sandbox 中的浏览器导航到指定 URL。
    
    通过在浏览器地址栏输入 URL 并回车来实现导航。
    
    Args:
        url: 目标网址，如 "https://www.baidu.com"
        
    Returns:
        操作结果
        
    Example:
        >>> sandbox_browser_goto("https://www.google.com")
        >>> sandbox_browser_goto("https://github.com")
    """
    tools = get_sandbox_tools()
    
    # AIO Sandbox 通过 GUI actions 实现浏览器导航
    # 1. 使用快捷键 Ctrl+L 聚焦地址栏
    # 2. 输入 URL
    # 3. 按回车键
    
    steps = []
    
    # 检查 actions API 返回格式: {"status":"success"} 或 {"success":true}
    def is_success(r):
        return r.get("status") == "success" or r.get("success", False)
    
    # Step 1: Ctrl+L 聚焦地址栏
    result1 = tools._request("POST", "/v1/browser/actions", json={
        "action_type": "HOTKEY",
        "keys": ["ctrl", "l"]
    })
    steps.append(("聚焦地址栏", is_success(result1)))
    
    # Step 2: 输入 URL
    result2 = tools._request("POST", "/v1/browser/actions", json={
        "action_type": "TYPING",
        "text": url,
        "use_clipboard": True
    })
    steps.append(("输入URL", is_success(result2)))
    
    # Step 3: 按回车键
    result3 = tools._request("POST", "/v1/browser/actions", json={
        "action_type": "PRESS",
        "key": "enter"
    })
    steps.append(("按回车", is_success(result3)))
    
    # 检查所有步骤是否成功
    all_success = all(s[1] for s in steps)
    if all_success:
        text = f"浏览器已导航到: {url}"
    else:
        failed = [s[0] for s in steps if not s[1]]
        text = f"浏览器导航部分失败: {', '.join(failed)}"
    
    return make_response(text, "browser_goto")


def sandbox_browser_screenshot() -> ToolResponse:
    """
    对 Sandbox 中的浏览器进行截图。
    
    Returns:
        截图结果信息（base64 图像数据会很长，这里只返回状态）
        
    Example:
        >>> sandbox_browser_screenshot()
    """
    tools = get_sandbox_tools()
    result = tools._request("POST", "/v1/browser/screenshot")
    
    if result.get("success"):
        screenshot = result.get("data", {}).get("screenshot", "")
        if screenshot:
            text = f"截图成功，图像大小: {len(screenshot)} 字符 (base64编码)"
        else:
            text = "截图成功"
    else:
        text = f"截图失败: {result.get('error', '未知错误')}"
    return make_response(text, "browser_screenshot")


def sandbox_browser_click(x: int, y: int, num_clicks: int = 1) -> ToolResponse:
    """
    在 Sandbox 浏览器中点击指定坐标位置。
    
    Args:
        x: 点击位置的 X 坐标
        y: 点击位置的 Y 坐标
        num_clicks: 点击次数，1 为单击，2 为双击
        
    Returns:
        操作结果
        
    Example:
        >>> sandbox_browser_click(500, 300)
        >>> sandbox_browser_click(100, 200, num_clicks=2)
    """
    tools = get_sandbox_tools()
    action = {
        "action_type": "CLICK",
        "x": x,
        "y": y,
        "num_clicks": num_clicks
    }
    result = tools._request("POST", "/v1/browser/actions", json=action)
    
    if result.get("status") == "success" or result.get("success"):
        text = f"已点击位置 ({x}, {y})"
    else:
        text = f"点击操作失败: {result.get('error', '未知错误')}"
    return make_response(text, "browser_click")


def sandbox_browser_type(text: str) -> ToolResponse:
    """
    在 Sandbox 浏览器中输入文本。
    
    Args:
        text: 要输入的文本内容
        
    Returns:
        操作结果
        
    Example:
        >>> sandbox_browser_type("Hello World")
        >>> sandbox_browser_type("搜索关键词")
    """
    tools = get_sandbox_tools()
    action = {
        "action_type": "TYPING",
        "text": text,
        "use_clipboard": False
    }
    result = tools._request("POST", "/v1/browser/actions", json=action)
    
    if result.get("status") == "success" or result.get("success"):
        response_text = f"已输入文本: {text}"
    else:
        response_text = f"输入操作失败: {result.get('error', '未知错误')}"
    return make_response(response_text, "browser_type")


def sandbox_browser_scroll(dx: int = 0, dy: int = 100) -> ToolResponse:
    """
    在 Sandbox 浏览器中滚动页面。
    
    Args:
        dx: 水平滚动距离，正值向右，负值向左
        dy: 垂直滚动距离，正值向下，负值向上
        
    Returns:
        操作结果
        
    Example:
        >>> sandbox_browser_scroll(0, 300)  # 向下滚动
        >>> sandbox_browser_scroll(0, -200)  # 向上滚动
    """
    tools = get_sandbox_tools()
    action = {
        "action_type": "SCROLL",
        "dx": dx,
        "dy": dy
    }
    result = tools._request("POST", "/v1/browser/actions", json=action)
    
    if result.get("status") == "success" or result.get("success"):
        text = f"已滚动页面 (dx={dx}, dy={dy})"
    else:
        text = f"滚动操作失败: {result.get('error', '未知错误')}"
    return make_response(text, "browser_scroll")


def sandbox_browser_hotkey(keys: str) -> ToolResponse:
    """
    在 Sandbox 浏览器中执行快捷键组合。
    
    Args:
        keys: 快捷键组合，用逗号分隔，如 "ctrl,c" 或 "ctrl,shift,s"
        
    Returns:
        操作结果
        
    Example:
        >>> sandbox_browser_hotkey("ctrl,c")  # 复制
        >>> sandbox_browser_hotkey("ctrl,v")  # 粘贴
        >>> sandbox_browser_hotkey("ctrl,a")  # 全选
    """
    tools = get_sandbox_tools()
    key_list = [k.strip() for k in keys.split(",")]
    action = {
        "action_type": "HOTKEY",
        "keys": key_list
    }
    result = tools._request("POST", "/v1/browser/actions", json=action)
    
    if result.get("status") == "success" or result.get("success"):
        text = f"已执行快捷键: {keys}"
    else:
        text = f"快捷键操作失败: {result.get('error', '未知错误')}"
    return make_response(text, "browser_hotkey")


def sandbox_browser_info() -> ToolResponse:
    """
    获取 Sandbox 浏览器的信息，包括 CDP URL 等。
    
    Returns:
        浏览器信息
        
    Example:
        >>> sandbox_browser_info()
    """
    tools = get_sandbox_tools()
    result = tools._request("GET", "/v1/browser/info")
    
    if result.get("success"):
        data = result.get("data", {})
        cdp_url = data.get("cdp_url", "")
        viewport = data.get("viewport", {})
        text = f"浏览器信息:\n  CDP URL: {cdp_url}\n  视口: {viewport}"
    else:
        text = f"获取浏览器信息失败: {result.get('error', '未知错误')}"
    return make_response(text, "browser_info")


# ==================== Sandbox 信息工具 ====================

def sandbox_status() -> ToolResponse:
    """
    获取 Sandbox 的状态信息。
    
    Returns:
        Sandbox 状态信息
        
    Example:
        >>> sandbox_status()
    """
    tools = get_sandbox_tools()
    
    # 测试连接
    result = tools._request("POST", "/v1/shell/exec", json={"command": "echo 'Sandbox OK'"})
    
    if result.get("success"):
        text = f"Sandbox 状态: 正常运行\n  地址: {tools.base_url}\n  VNC: {tools.base_url}/vnc/\n  VSCode: {tools.base_url}/code-server/"
    else:
        text = f"Sandbox 状态: 连接失败 - {result.get('error', '未知错误')}"
    return make_response(text, "sandbox_status")


# ==================== SandboxUse 智能体类 ====================

class SandboxUseAgent:
    """
    SandboxUse 智能体
    
    能够根据用户指令，智能分析意图并调用相应的 AIO Sandbox API：
    - Shell 命令执行
    - 文件操作
    - Python 代码执行
    - 浏览器自动化操作
    """
    
    SYSTEM_PROMPT = """你是一个强大的 Sandbox 操作助手，能够在 AIO Sandbox 环境中执行各种操作。

你可以使用以下工具：

**Shell 操作:**
- `sandbox_shell`: 执行任意 Shell 命令

**文件操作:**
- `sandbox_file_read`: 读取文件内容
- `sandbox_file_write`: 写入/创建文件
- `sandbox_file_list`: 列出目录内容

**Python 代码执行:**
- `sandbox_python`: 执行 Python 代码

**浏览器操作:**
- `sandbox_browser_goto`: 导航到指定 URL
- `sandbox_browser_screenshot`: 截取屏幕
- `sandbox_browser_click`: 点击指定坐标
- `sandbox_browser_type`: 输入文本
- `sandbox_browser_scroll`: 滚动页面
- `sandbox_browser_hotkey`: 执行快捷键
- `sandbox_browser_info`: 获取浏览器信息

**系统信息:**
- `sandbox_status`: 获取 Sandbox 状态

请根据用户的指令，分析需要执行的操作，然后调用相应的工具完成任务。
在执行复杂任务时，可以组合多个工具依次执行。

注意事项：
1. 文件路径默认在 /home/user 目录下
2. 执行命令前可以先用 sandbox_file_list 查看目录结构
3. 浏览器操作需要先用 sandbox_browser_goto 打开网页
4. 回复时请说明你执行了什么操作以及结果
"""
    
    def __init__(
        self,
        name: str = "SandboxUse",
        api_key: str = "",
        model_name: str = "qwen3-max",
        max_iters: int = 10,
        sandbox_url: str = "http://localhost:988"
    ):
        """
        初始化 SandboxUse 智能体
        
        Args:
            name: 智能体名称
            api_key: API 密钥
            model_name: 模型名称
            max_iters: 最大迭代次数
            sandbox_url: Sandbox 服务地址
        """
        self.name = name
        self.sandbox_url = sandbox_url
        
        # 初始化 Sandbox 工具
        global _sandbox_tools
        _sandbox_tools = SandboxTools(sandbox_url)
        
        # 创建工具集
        self.toolkit = Toolkit()
        
        # 注册所有 Sandbox 工具
        self.toolkit.register_tool_function(sandbox_shell)
        self.toolkit.register_tool_function(sandbox_file_read)
        self.toolkit.register_tool_function(sandbox_file_write)
        self.toolkit.register_tool_function(sandbox_file_list)
        self.toolkit.register_tool_function(sandbox_python)
        self.toolkit.register_tool_function(sandbox_browser_goto)
        self.toolkit.register_tool_function(sandbox_browser_screenshot)
        self.toolkit.register_tool_function(sandbox_browser_click)
        self.toolkit.register_tool_function(sandbox_browser_type)
        self.toolkit.register_tool_function(sandbox_browser_scroll)
        self.toolkit.register_tool_function(sandbox_browser_hotkey)
        self.toolkit.register_tool_function(sandbox_browser_info)
        self.toolkit.register_tool_function(sandbox_status)
        
        # 创建 ReAct Agent
        self.agent = ReActAgent(
            name=name,
            sys_prompt=self.SYSTEM_PROMPT,
            model=DashScopeChatModel(
                api_key=api_key,
                model_name=model_name,
                enable_thinking=True,
                stream=True,
            ),
            formatter=DashScopeChatFormatter(),
            toolkit=self.toolkit,
            memory=InMemoryMemory(),
            max_iters=max_iters,
        )
    
    async def __call__(self, msg):
        """处理用户消息"""
        return await self.agent(msg)
    
    def health_check(self) -> bool:
        """检查 Sandbox 连接状态"""
        tools = get_sandbox_tools()
        result = tools._request("POST", "/v1/shell/exec", json={"command": "echo ok"})
        return result.get("success", False)


# 全局智能体实例
_sandbox_agent: Optional[SandboxUseAgent] = None


def get_sandbox_agent(
    api_key: str = "",
    model_name: str = "qwen3-max",
    sandbox_url: str = "http://localhost:988"
) -> SandboxUseAgent:
    """获取 SandboxUse 智能体单例"""
    global _sandbox_agent
    if _sandbox_agent is None:
        _sandbox_agent = SandboxUseAgent(
            api_key=api_key,
            model_name=model_name,
            sandbox_url=sandbox_url
        )
    return _sandbox_agent
