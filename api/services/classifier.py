# -*- coding: utf-8 -*-
"""
分类器服务

提供通用的 LLM 分类功能，用于工作流中的分类器节点。
"""
from typing import List, Dict, Optional, Any


class ClassifierService:
    """分类器服务，使用 LLM 进行文本分类"""
    
    def __init__(self, api_key: str, default_model: str = "qwen3-max"):
        """
        初始化分类器服务。
        
        Args:
            api_key: API 密钥
            default_model: 默认使用的模型
        """
        self.api_key = api_key
        self.default_model = default_model
        self._agent = None
    
    def _get_agent(self, model: str = None):
        """获取或创建分类智能体"""
        from agents.base import BaseAgent
        
        return BaseAgent(
            name="Classifier",
            sys_prompt="你是一个分类助手，根据用户输入选择最匹配的分类。只返回分类名称，不要返回其他内容。",
            api_key=self.api_key,
            model_name=model or self.default_model,
            max_iters=1,
        )
    
    async def classify(
        self,
        input_text: str,
        categories: List[Dict[str, str]],
        model: str = None
    ) -> Optional[Dict[str, str]]:
        """
        对输入文本进行分类。
        
        Args:
            input_text: 待分类的文本
            categories: 分类列表，每个分类包含 id, name, description
            model: 使用的模型，默认使用初始化时的模型
        
        Returns:
            匹配的分类字典，如果没有匹配则返回第一个分类
        """
        if not categories:
            return None
        
        # 构建分类提示词
        category_list = "\n".join([
            f"{i+1}. {cat['name']}: {cat.get('description', '')}" 
            for i, cat in enumerate(categories)
        ])
        
        classify_prompt = f"""请分析以下用户输入，并从给定的分类中选择最匹配的一个。

用户输入：{input_text}

可选分类：
{category_list}

请只返回最匹配的分类名称，不要返回其他内容。"""
        
        # 调用 LLM 进行分类
        from agentscope.message import Msg
        agent = self._get_agent(model)
        response = await agent(Msg("user", classify_prompt, "user"))
        result = response.content if hasattr(response, "content") else str(response)
        
        # 处理返回值可能是列表的情况
        if isinstance(result, list):
            result = result[0].get("text", str(result[0])) if result else ""
        result = str(result).strip()
        
        # 匹配分类
        matched_category = None
        for cat in categories:
            if cat["name"] in result or result in cat["name"]:
                matched_category = cat
                break
        
        # 如果没有匹配，返回第一个分类作为默认
        if not matched_category and categories:
            matched_category = categories[0]
        
        return matched_category
