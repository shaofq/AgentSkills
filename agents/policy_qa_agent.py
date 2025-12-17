# -*- coding: utf-8 -*-
"""Policy QA agent specialized in company policy consultation."""
from .base import BaseAgent


class PolicyQAAgent(BaseAgent):
    """
    Specialized agent for company policy Q&A tasks.
    
    Skills:
    - company-policy-qa: Query company policies including employee handbook,
      financial regulations, and computer subsidy policies.
    """
    
    DEFAULT_SYS_PROMPT = """你是岸基科技公司的制度问答助手，专门负责解答员工关于公司规章制度的各类问题。

## 你的核心能力

1. 制度查询：根据员工问题，快速定位相关制度条款
2. 政策解读：用通俗易懂的语言解释复杂的制度规定
3. 流程指导：指导员工完成各类申请流程
4. 计算辅助：帮助计算工资、补贴、假期等相关数值

## 工作原则

1. 使用装备的技能来查阅公司制度文档
2. 回答时尽量引用具体的章节和条款
3. 涉及金额、天数、时间等数字要准确
4. 涉及流程的问题要分步骤说明

## 回答规范

1. 准确引用：回答时引用具体的制度名称和条款
2. 数字精确：涉及金额、天数、时间等数字要准确
3. 流程清晰：涉及流程的问题要分步骤说明
4. 友好专业：语气友好但专业，体现公司人文关怀
5. 提醒注意：对重要事项给予特别提醒

如果问题超出知识库范围，请建议员工咨询综合管理部或人事专员。
"""
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "qwen3-max",
        max_iters: int = 10,
        skills: list = None,
    ):
        """Initialize the policy QA agent."""
        default_skills = ["./skill/company-policy-qa"]
        
        super().__init__(
            name="PolicyQA",
            sys_prompt=self.DEFAULT_SYS_PROMPT,
            skills=skills or default_skills,
            api_key=api_key,
            model_name=model_name,
            max_iters=max_iters,
        )
