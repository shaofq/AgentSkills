# -*- coding: utf-8 -*-
"""OpenAI 兼容 API 模型包装类，支持 aigateway 等 OpenAI 兼容接口"""
import os
from typing import List, Dict, Any, Optional, Generator
from openai import OpenAI


class OpenAIChatModel:
    """
    OpenAI 兼容 API 的模型包装类。
    
    支持任何 OpenAI 兼容的 API 端点，如 aigateway、Azure OpenAI、本地 LLM 等。
    
    使用方式:
        model = OpenAIChatModel(
            api_key="your-api-key",
            base_url="https://aigateway.edgecloudapp.com/v1/{id}/{name}",
            model_name="claude-4.5-sonnet",
        )
    """
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model_name: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        enable_thinking: bool = False,
        **kwargs
    ):
        """
        初始化 OpenAI 兼容模型。
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出
            enable_thinking: 是否启用思考模式（某些模型支持）
        """
        self.api_key = api_key or os.environ.get("AIGATEWAY_API_KEY", "")
        self.base_url = base_url or os.environ.get("AIGATEWAY_BASE_URL", "")
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stream = stream
        self.enable_thinking = enable_thinking
        
        if not self.api_key:
            raise ValueError("API key is required. Set AIGATEWAY_API_KEY env or pass api_key parameter.")
        if not self.base_url:
            raise ValueError("Base URL is required. Set AIGATEWAY_BASE_URL env or pass base_url parameter.")
        
        # 调试日志：打印配置信息
        print(f"[OpenAIChatModel] Initializing with:")
        print(f"  - api_key: {self.api_key}")
        print(f"  - base_url: {self.base_url}")
        print(f"  - model_name: {self.model_name}")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
    
    async def __call__(self, messages: List[Dict[str, Any]], **kwargs) -> Any:
        """
        调用模型生成响应（异步方法，兼容 agentscope）。
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数（包括 tools, tool_choice 等）
            
        Returns:
            模型响应对象
        """
        # 合并默认参数和传入参数
        params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": kwargs.get("stream", self.stream),
        }
        
        # 处理 tools 和 tool_choice 参数（ReAct Agent 需要）
        if "tools" in kwargs and kwargs["tools"]:
            params["tools"] = kwargs["tools"]
            # 如果有 tools，暂时禁用流式输出以便正确处理 tool_calls
            params["stream"] = False
        if "tool_choice" in kwargs and kwargs["tool_choice"]:
            params["tool_choice"] = kwargs["tool_choice"]
        
        try:
            response = self.client.chat.completions.create(**params)
            
            if params["stream"]:
                return self._handle_stream_response(response)
            else:
                return self._handle_response(response)
                
        except Exception as e:
            raise RuntimeError(f"OpenAI API 调用失败: {e}")
    
    def _handle_response(self, response) -> "ModelResponse":
        """处理非流式响应，支持 tool_calls"""
        message = response.choices[0].message
        content = message.content or ""
        
        # 检查是否有 tool_calls
        tool_calls = getattr(message, 'tool_calls', None)
        
        return ModelResponse(
            text=content,
            raw_response=response,
            tool_calls=tool_calls,
        )
    
    def _handle_stream_response(self, response) -> "ModelResponse":
        """处理流式响应"""
        full_content = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                print(content, end="", flush=True)
        print()  # 换行
        
        return ModelResponse(
            text=full_content,
            raw_response=None,
            tool_calls=None,
        )
    
    def format_messages(self, messages: List[Any]) -> List[Dict[str, str]]:
        """
        将 agentscope 消息格式转换为 OpenAI 消息格式。
        
        Args:
            messages: agentscope 消息列表
            
        Returns:
            OpenAI 格式的消息列表
        """
        formatted = []
        for msg in messages:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                formatted.append({
                    "role": msg.role,
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                })
            elif isinstance(msg, dict):
                formatted.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        return formatted


class ModelResponse:
    """模型响应包装类，兼容 agentscope 格式，支持异步迭代"""
    
    def __init__(self, text: str, raw_response: Any = None, tool_calls: Any = None):
        self.text = text
        self.raw_response = raw_response
        self.tool_calls = tool_calls
        self._yielded = False
    
    def __str__(self):
        return self.text
    
    @property
    def content(self):
        return self.text
    
    @property
    def message(self):
        """兼容 OpenAI 响应格式"""
        return self
    
    def __aiter__(self):
        """支持 async for 迭代"""
        return self
    
    async def __anext__(self):
        """异步迭代器，返回自身作为唯一元素"""
        if self._yielded:
            raise StopAsyncIteration
        self._yielded = True
        return self


def create_openai_model(
    api_key: str = "",
    base_url: str = "",
    model_name: str = "",
    **kwargs
) -> OpenAIChatModel:
    """
    创建 OpenAI 兼容模型的工厂函数。
    
    Args:
        api_key: API 密钥，默认从环境变量 AIGATEWAY_API_KEY 获取
        base_url: API 基础 URL，默认从环境变量 AIGATEWAY_BASE_URL 获取
        model_name: 模型名称，默认从环境变量 AIGATEWAY_MODEL 获取
        
    Returns:
        OpenAIChatModel 实例
    """
    from config.settings import AIGATEWAY_API_KEY, AIGATEWAY_BASE_URL, AIGATEWAY_MODEL
    
    return OpenAIChatModel(
        api_key=api_key or AIGATEWAY_API_KEY,
        base_url=base_url or AIGATEWAY_BASE_URL,
        model_name=model_name or AIGATEWAY_MODEL,
        **kwargs
    )
