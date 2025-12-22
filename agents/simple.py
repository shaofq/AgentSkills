# -*- coding: utf-8 -*-
"""Simple agent without tools for analysis tasks."""
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit
from agentscope.message import Msg


class SimpleAgent:
    """Simple agent without tools, only for analysis and conversation.
    
    Uses ReActAgent with empty toolkit and max_iters=1 to get direct response.
    """
    
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
        self._sys_prompt = sys_prompt
        
        # 使用 ReActAgent，但不注册任何工具，max_iters=1 直接返回
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
            toolkit=Toolkit(),  # 空工具箱
            memory=InMemoryMemory(),
            max_iters=1,  # 只执行一次，直接返回结果
        )
    
    async def __call__(self, msg):
        """Process a message."""
        result = await self.agent(msg)
        print(f"{self.name}: {result.content if hasattr(result, 'content') else result}")
        return result
    
    @property
    def sys_prompt(self):
        """Get the agent's system prompt."""
        return self._sys_prompt
