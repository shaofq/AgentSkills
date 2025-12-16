# -*- coding: utf-8 -*-
"""Base agent class for all specialized agents."""
from typing import List, Optional
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_shell_command, execute_python_code, view_text_file


class BaseAgent:
    """Base class for creating specialized agents with skills."""
    
    def __init__(
        self,
        name: str,
        sys_prompt: str,
        skills: Optional[List[str]] = None,
        api_key: str = "",
        model_name: str = "qwen3-max",
        max_iters: int = 30,
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
        
        # Create the agent
        self.agent = ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=DashScopeChatModel(
                api_key=api_key,
                model_name=model_name,
                enable_thinking=False,
                stream=True,  # 流式输出
            ),
            formatter=DashScopeChatFormatter(),
            toolkit=self.toolkit,
            memory=InMemoryMemory(),
            max_iters=max_iters,
        )
    
    async def __call__(self, msg):
        """Process a message."""
        return await self.agent(msg)
    
    @property
    def sys_prompt(self):
        """Get the agent's system prompt."""
        return self.agent.sys_prompt
