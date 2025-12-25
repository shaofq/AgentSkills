# -*- coding: utf-8 -*-
"""Simple agent without tools for analysis tasks."""
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel, OpenAIChatModel
from agentscope.tool import Toolkit
from agentscope.message import Msg
from config.settings import MODEL_PROVIDER, AIGATEWAY_API_KEY, AIGATEWAY_BASE_URL, AIGATEWAY_MODEL


class SimpleAgent:
    """Simple agent without tools, only for analysis and conversation.
    
    Uses ReActAgent with empty toolkit and max_iters=1 to get direct response.
    """
    
    def __init__(
        self,
        name: str,
        sys_prompt: str,
        api_key: str = "",
        model_name: str = "",
        provider: str = "",
        base_url: str = "",
    ):
        """
        Initialize a simple agent without tools.
        
        Args:
            name: Agent name
            sys_prompt: System prompt for the agent
            api_key: API key for the model
            model_name: Model name to use
            provider: Model provider (dashscope or aigateway)
            base_url: API base URL (for aigateway)
        """
        self.name = name
        self._sys_prompt = sys_prompt
        
        # 根据 provider 创建模型
        provider = provider or MODEL_PROVIDER
        if provider == "aigateway":
            api_key = api_key or AIGATEWAY_API_KEY
            base_url = base_url or AIGATEWAY_BASE_URL
            model_name = model_name or AIGATEWAY_MODEL
            model = OpenAIChatModel(
                api_key=api_key,
                model_name=model_name,
                client_kwargs={"base_url": base_url},
                stream=True,
            )
        else:
            model = DashScopeChatModel(
                api_key=api_key,
                model_name=model_name or "qwen3-max",
                enable_thinking=False,
                stream=True,
            )
        
        # 使用 ReActAgent，但不注册任何工具，max_iters=1 直接返回
        self.agent = ReActAgent(
            name=name,
            sys_prompt=sys_prompt,
            model=model,
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
