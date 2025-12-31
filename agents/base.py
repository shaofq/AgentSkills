# -*- coding: utf-8 -*-
"""Base agent class for all specialized agents."""
import os
import sys
import io
import asyncio
from typing import List, Optional, Dict, Any, Callable
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel, OpenAIChatModel
from config.settings import (
    MODEL_PROVIDER, AIGATEWAY_API_KEY, AIGATEWAY_BASE_URL, AIGATEWAY_MODEL,
    ZHIPU_API_KEY, ZHIPU_BASE_URL, ZHIPU_MODEL
)
from agentscope.tool import Toolkit, execute_shell_command, execute_python_code, view_text_file


# 技能目录的基础路径
SKILL_BASE_PATH = "./skill"

# 全局日志回调（用于捕获 agent 执行过程中的日志）
_log_callback: Optional[Callable[[str, str, str], None]] = None


def set_log_callback(callback: Optional[Callable[[str, str, str], None]]):
    """设置全局日志回调函数
    
    Args:
        callback: 回调函数，接收 (source, log_type, message) 参数
    """
    global _log_callback
    _log_callback = callback


def get_log_callback() -> Optional[Callable[[str, str, str], None]]:
    """获取全局日志回调函数"""
    return _log_callback


def emit_log(source: str, log_type: str, message: str):
    """发送日志到回调函数"""
    if _log_callback:
        try:
            _log_callback(source, log_type, message)
        except Exception:
            pass


def create_model(
    provider: str = "",
    api_key: str = "",
    model_name: str = "",
    base_url: str = "",
    **kwargs
):
    """
    根据提供商创建模型实例。
    
    Args:
        provider: 模型提供商 ("dashscope", "aigateway" 或 "zhipu")
        api_key: API 密钥
        model_name: 模型名称
        base_url: API 基础 URL
    """
    provider = provider or MODEL_PROVIDER
    
    if provider == "zhipu":
        # 使用智谱 GLM 模型
        actual_api_key = api_key or ZHIPU_API_KEY
        actual_base_url = base_url or ZHIPU_BASE_URL
        actual_model = model_name or ZHIPU_MODEL
        
        print(f"[create_model] Using Zhipu GLM with:")
        print(f"  - base_url: {actual_base_url}")
        print(f"  - model_name: {actual_model}")
        
        return OpenAIChatModel(
            api_key=actual_api_key,
            model_name=actual_model,
            client_kwargs={"base_url": actual_base_url},
            generate_kwargs={
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
            },
            stream=kwargs.get("stream", True),
        )
    elif provider == "aigateway":
        # 使用 agentscope 内置的 OpenAIChatModel
        actual_api_key = api_key or AIGATEWAY_API_KEY
        actual_base_url = base_url or AIGATEWAY_BASE_URL
        # 如果 model_name 是 DashScope 模型（如 qwen3-max），则使用 AIGATEWAY_MODEL
        if not model_name or model_name.startswith("qwen"):
            actual_model = AIGATEWAY_MODEL
        else:
            actual_model = model_name
        
        print(f"[create_model] Using OpenAIChatModel with:")
        print(f"  - api_key: {actual_api_key}")
        print(f"  - base_url: {actual_base_url}")
        print(f"  - model_name: {actual_model}")
        
        return OpenAIChatModel(
            api_key=actual_api_key,
            model_name=actual_model,
            client_kwargs={"base_url": actual_base_url},
            generate_kwargs={
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
            },
            stream=kwargs.get("stream", True),
        )
    else:
        # 默认使用 DashScope
        return DashScopeChatModel(
            api_key=api_key or AIGATEWAY_API_KEY,
            model_name=model_name or "qwen3-max",
            enable_thinking=kwargs.get("enable_thinking", True),
            stream=kwargs.get("stream", True),
        )


class BaseAgent:
    """Base class for creating specialized agents with skills."""
    
    def __init__(
        self,
        name: str,
        sys_prompt: str,
        skills: Optional[List[str]] = None,
        api_key: str = "",
        model_name: str = "",
        max_iters: int = 30,
        provider: str = "",
        base_url: str = "",
    ):
        """
        Initialize a specialized agent.
        
        Args:
            name: Agent name
            sys_prompt: System prompt for the agent
            skills: List of skill directory paths
            api_key: API key for the model
            model_name: Model name to use
            max_iters: Maximum iterations for ReAct loop
        """
        self.name = name
        self.skills = skills or []
        
        # Create toolkit
        self.toolkit = Toolkit()
        
        # Register basic tools
        self.toolkit.register_tool_function(execute_shell_command)
        self.toolkit.register_tool_function(execute_python_code)
        self.toolkit.register_tool_function(view_text_file)
        
        # Register skills
        for skill_path in self.skills:
            self.toolkit.register_agent_skill(skill_path)
        
        # Create the model based on provider
        model = create_model(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            base_url=base_url,
            enable_thinking=True,
            stream=True,
        )
        
        # Create the agent
        self.agent = ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=model,
            formatter=DashScopeChatFormatter(),
            toolkit=self.toolkit,
            memory=InMemoryMemory(),
            max_iters=max_iters,
        )
    
    async def __call__(self, msg):
        """Process a message with logging support."""
        # 发送开始日志
        emit_log(self.name, "info", f"开始处理请求...")
        
        # 捕获 stdout 输出
        original_stdout = sys.stdout
        captured_output = io.StringIO()
        
        class TeeOutput:
            """同时输出到原始 stdout 和捕获器，并发送日志"""
            def __init__(self, original, capture, agent_name):
                self.original = original
                self.capture = capture
                self.agent_name = agent_name
                self.buffer = ""
            
            def write(self, text):
                self.original.write(text)
                self.capture.write(text)
                # 按行发送日志
                self.buffer += text
                while "\n" in self.buffer:
                    line, self.buffer = self.buffer.split("\n", 1)
                    if line.strip():
                        emit_log(self.agent_name, "info", line.strip())
            
            def flush(self):
                self.original.flush()
                self.capture.flush()
        
        try:
            sys.stdout = TeeOutput(original_stdout, captured_output, self.name)
            result = await self.agent(msg)
            emit_log(self.name, "success", "处理完成")
            return result
        except Exception as e:
            emit_log(self.name, "error", f"执行错误: {str(e)}")
            raise
        finally:
            sys.stdout = original_stdout
    
    @property
    def sys_prompt(self):
        """Get the agent's system prompt."""
        return self.agent.sys_prompt


def get_available_skills() -> List[Dict[str, Any]]:
    """
    获取所有可用的技能列表。
    
    Returns:
        技能信息列表，每个技能包含 name, path, description
    """
    skills = []
    
    if not os.path.exists(SKILL_BASE_PATH):
        return skills
    
    for skill_dir_name in os.listdir(SKILL_BASE_PATH):
        skill_path = os.path.join(SKILL_BASE_PATH, skill_dir_name)
        skill_md_path = os.path.join(skill_path, "SKILL.md")
        
        if os.path.isdir(skill_path) and os.path.exists(skill_md_path):
            # 读取 SKILL.md 获取 name 和 description
            skill_name = skill_dir_name  # 默认使用目录名
            description = ""
            try:
                with open(skill_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.strip().split("\n")
                    
                    # 解析 YAML frontmatter 格式 (--- 包裹的 YAML 块)
                    in_frontmatter = False
                    for line in lines:
                        line_stripped = line.strip()
                        
                        if line_stripped == "---":
                            if not in_frontmatter:
                                in_frontmatter = True
                                continue
                            else:
                                # frontmatter 结束
                                break
                        
                        if in_frontmatter:
                            # 解析 YAML 格式的 name 和 description
                            if line_stripped.startswith("name:"):
                                skill_name = line_stripped[5:].strip()
                            elif line_stripped.startswith("description:"):
                                description = line_stripped[12:].strip()
                    
                    # 如果没有 frontmatter，尝试旧的解析方式
                    if not description:
                        for line in lines:
                            line_stripped = line.strip()
                            if line_stripped.startswith("# "):
                                description = line_stripped[2:].strip()
                                break
                            elif line_stripped and not line_stripped.startswith("---"):
                                description = line_stripped[:100]
                                break
            except Exception:
                pass
            
            skills.append({
                "name": skill_name,
                "path": skill_path,
                "description": description,
            })
    
    return skills


def create_agent_by_skills(
    name: str,
    skill_names: List[str],
    sys_prompt: Optional[str] = None,
    api_key: str = "",
    model_name: str = "",
    max_iters: int = 30,
    provider: str = "",
    base_url: str = "",
) -> BaseAgent:
    """
    根据技能名称动态创建智能体的工厂函数。
    
    Args:
        name: 智能体名称
        skill_names: 技能名称列表（不需要完整路径，只需技能目录名）
        sys_prompt: 系统提示词，如果不提供则自动生成
        api_key: API 密钥
        model_name: 模型名称
        max_iters: 最大迭代次数
        provider: 模型提供商 ("dashscope" 或 "aigateway")
        base_url: API 基础 URL (仅 aigateway 需要)
        
    Returns:
        配置好的 BaseAgent 实例
        
    Example:
        >>> agent = create_agent_by_skills(
        ...     name="BookingAgent",
        ...     skill_names=["booking-skill"],
        ...     api_key="your-api-key",
        ... )
        >>> response = await agent(Msg("user", "我要订舱", "user"))
    """
    # 将技能名称转换为完整路径
    skill_paths = []
    skill_descriptions = []
    
    for skill_name in skill_names:
        # 支持完整路径或仅技能名称
        if os.path.isabs(skill_name) or skill_name.startswith("./"):
            skill_path = skill_name
        else:
            skill_path = os.path.join(SKILL_BASE_PATH, skill_name)
        
        if os.path.exists(skill_path):
            skill_paths.append(skill_path)
            
            # 读取技能描述用于生成系统提示词
            skill_md_path = os.path.join(skill_path, "SKILL.md")
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        lines = content.strip().split("\n")
                        for line in lines:
                            line = line.strip()
                            if line.startswith("# "):
                                skill_descriptions.append(line[2:].strip())
                                break
                except Exception:
                    skill_descriptions.append(skill_name)
            else:
                skill_descriptions.append(skill_name)
        else:
            print(f"[Warning] 技能路径不存在: {skill_path}")
    
    # 如果没有提供系统提示词，自动生成
    if not sys_prompt:
        if skill_descriptions:
            skills_text = "、".join(skill_descriptions)
            sys_prompt = f"""你是一个专业的智能助手 {name}，具备以下技能：
{skills_text}

请根据用户的需求，灵活运用你的技能来帮助用户完成任务。
在回答时请保持专业、友好，并确保信息准确。"""
        else:
            sys_prompt = f"你是一个专业的智能助手 {name}，请帮助用户完成各种任务。"
    
    return BaseAgent(
        name=name,
        sys_prompt=sys_prompt,
        skills=skill_paths,
        api_key=api_key,
        model_name=model_name,
        max_iters=max_iters,
        provider=provider,
        base_url=base_url,
    )


def create_agent_from_config(config: Dict[str, Any], api_key: str = "") -> BaseAgent:
    """
    根据配置字典创建智能体。
    
    Args:
        config: 智能体配置字典，包含以下字段：
            - name: 智能体名称
            - skills: 技能名称列表
            - systemPrompt: 系统提示词（可选）
            - model: 模型名称（可选，默认 qwen3-max）
            - maxIters: 最大迭代次数（可选，默认 30）
        api_key: API 密钥
        
    Returns:
        配置好的 BaseAgent 实例
        
    Example:
        >>> config = {
        ...     "name": "BookingAgent",
        ...     "skills": ["booking-skill"],
        ...     "systemPrompt": "你是订舱助手",
        ...     "model": "qwen3-max",
        ... }
        >>> agent = create_agent_from_config(config, api_key="your-key")
    """
    name = config.get("name", "Agent")
    skills = config.get("skills", [])
    sys_prompt = config.get("systemPrompt") or config.get("sys_prompt")
    model_name = config.get("model") or config.get("model_name", "qwen3-max")
    max_iters = config.get("maxIters") or config.get("max_iters", 30)
    provider = config.get("provider", "")
    base_url = config.get("base_url") or config.get("baseUrl", "")
    
    return create_agent_by_skills(
        name=name,
        skill_names=skills,
        sys_prompt=sys_prompt,
        api_key=api_key,
        model_name=model_name,
        max_iters=max_iters,
        provider=provider,
        base_url=base_url,
    )
