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
        
        sys_prompt = """你是一个专业的意图分类助手。你的任务是准确理解用户的真实意图，并将其归类到最合适的类别。

分类原则：
1. 关注用户的核心需求，而非表面用词
2. "咨询"、"查询"、"了解"、"问"等词通常表示信息获取类需求
3. "生成"、"创建"、"开发"、"编写代码"、"做一个页面"等词通常表示技术开发类需求
4. 如果用户询问某个制度、政策、规定的具体内容，属于信息咨询
5. 如果用户要求制作工具、系统、页面、程序，属于技术开发

输出要求：
- 只输出分类名称，不要输出任何解释或其他内容
- 分类名称必须与给定选项完全一致"""
        
        return BaseAgent(
            name="Classifier",
            sys_prompt=sys_prompt,
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
            f"- **{cat['name']}**: {cat.get('description', '')}" 
            for cat in categories
        ])
        
        classify_prompt = f"""请分析用户输入的真实意图，并选择最匹配的分类。

## 用户输入
{input_text}

## 可选分类
{category_list}

## 分类决策
请根据用户的核心需求进行分类。注意区分：
- 如果用户是在"询问/咨询/了解"某个信息或规定，选择信息咨询类
- 如果用户是要"制作/开发/生成"某个功能或代码，选择技术开发类

请直接输出分类名称："""
        
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
