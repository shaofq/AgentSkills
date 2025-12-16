# -*- coding: utf-8 -*-
"""Router agent for dispatching tasks to specialized agents."""
from typing import Dict, Any
from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.message import Msg


class RouterAgent:
    """
    Router agent that analyzes user intent and dispatches to specialized agents.
    """
    
    # 意图到智能体的映射关键词
    INTENT_KEYWORDS = {
        "code_agent": [
            "代码", "code", "amis", "json", "配置", "表单", "页面", "组件",
            "react", "vue", "前端", "api", "接口", "开发", "编程"
        ],
        "pptx_agent": [
            "ppt", "pptx", "演示", "幻灯片", "slide", "presentation",
            "模板", "template", "演示文稿"
        ],
        "data_agent": [
            "数据", "data", "sql", "查询", "分析", "统计", "图表",
            "chart", "报表", "excel", "csv"
        ],
    }
    
    def __init__(
        self,
        agents: Dict[str, Any],
        api_key: str = "",
        model_name: str = "qwen3-max",
    ):
        """
        Initialize the router agent.
        
        Args:
            agents: Dictionary of agent_name -> agent_instance
            api_key: API key for the model
            model_name: Model name to use
        """
        self.agents = agents
        self.api_key = api_key
        self.model_name = model_name
        
        # Build agent descriptions for the prompt
        agent_descriptions = "\n".join([
            f"- {name}: {agent.agent.sys_prompt.split(chr(10))[0]}"
            for name, agent in agents.items()
        ])
        
        self.sys_prompt = f"""你是一个智能路由助手，负责分析用户请求并将其分发到合适的专业智能体。

## 可用的专业智能体

{agent_descriptions}

## 你的任务

1. 分析用户的请求内容
2. 判断应该由哪个智能体处理
3. 将请求转发给对应的智能体
4. 如果请求涉及多个领域，选择最相关的智能体

## 输出格式

直接输出智能体名称，如：code_agent、pptx_agent、data_agent
"""
    
    def _analyze_intent(self, message: str) -> str:
        """
        Analyze user intent based on keywords.
        
        Args:
            message: User message
            
        Returns:
            Agent name to handle the request
        """
        message_lower = message.lower()
        
        # Count keyword matches for each agent
        scores = {}
        for agent_name, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            scores[agent_name] = score
        
        # Return agent with highest score, default to code_agent
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "code_agent"
    
    async def route(self, msg: Msg) -> Any:
        """
        Route the message to the appropriate agent.
        
        Args:
            msg: User message
            
        Returns:
            Response from the specialized agent
        """
        # Analyze intent
        target_agent = self._analyze_intent(msg.content)
        
        print(f"\n[Router] 分析意图，分发到: {target_agent}")
        
        # Get the target agent
        if target_agent in self.agents:
            agent = self.agents[target_agent]
            return await agent(msg)
        else:
            # Fallback to first available agent
            first_agent = list(self.agents.values())[0]
            return await first_agent(msg)
    
    async def __call__(self, msg: Msg) -> Any:
        """Process a message through routing."""
        return await self.route(msg)
    
    async def sequential(self, msg: Msg, agent_sequence: list) -> Any:
        """
        串行协作：按顺序调用多个智能体，前一个的输出作为后一个的输入。
        
        Args:
            msg: 初始用户消息
            agent_sequence: 智能体名称列表，按执行顺序排列
            
        Returns:
            最后一个智能体的响应
            
        Example:
            # 先让 code_agent 生成代码，再让 pptx_agent 制作展示PPT
            await router.sequential(msg, ["code_agent", "pptx_agent"])
        """
        current_msg = msg
        result = None
        
        for i, agent_name in enumerate(agent_sequence, 1):
            if agent_name not in self.agents:
                print(f"[Router] 警告: 智能体 {agent_name} 不存在，跳过")
                continue
            
            print(f"\n[Router] 串行协作 ({i}/{len(agent_sequence)}): {agent_name}")
            
            agent = self.agents[agent_name]
            result = await agent(current_msg)
            
            # 将当前智能体的输出作为下一个智能体的输入
            if result and hasattr(result, 'content'):
                current_msg = Msg(agent_name, result.content, "assistant")
        
        return result
    
    async def parallel(self, msg: Msg, agent_names: list) -> list:
        """
        并行协作：同时调用多个智能体处理同一请求。
        
        Args:
            msg: 用户消息
            agent_names: 要并行调用的智能体名称列表
            
        Returns:
            所有智能体响应的列表
            
        Example:
            # 同时让多个智能体处理，然后合并结果
            results = await router.parallel(msg, ["code_agent", "data_agent"])
        """
        import asyncio
        
        print(f"\n[Router] 并行协作: {agent_names}")
        
        tasks = []
        for agent_name in agent_names:
            if agent_name in self.agents:
                tasks.append(self.agents[agent_name](msg))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
