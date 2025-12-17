# -*- coding: utf-8 -*-
"""Simple agent without tools for analysis tasks."""
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit


class SimpleAgent:
    """Simple agent without tools, only for analysis and conversation."""
    
    def __init__(
        self,
        name: str,
        sys_prompt: str,
        api_key: str = "",
        model_name: str = "qwen3-max",
    ):
        """
        Initialize a simple agent without tools.
        
        Args:
            name: Agent name
            sys_prompt: System prompt for the agent
            api_key: API key for the model
            model_name: Model name to use
        """
        self.name = name
        
        # Create empty toolkit (no tools registered)
        self.toolkit = Toolkit()
        
        # Create the agent with empty toolkit
        self.agent = ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=DashScopeChatModel(
                api_key=api_key,
                model_name=model_name,
                enable_thinking=False,
                stream=True,
            ),
            formatter=DashScopeChatFormatter(),
            toolkit=self.toolkit,
            memory=InMemoryMemory(),
            max_iters=1,  # 只执行一次，不需要工具循环
        )
    
    async def __call__(self, msg):
        """Process a message."""
        return await self.agent(msg)
    
    @property
    def sys_prompt(self):
        """Get the agent's system prompt."""
        return self.agent.sys_prompt
