# -*- coding: utf-8 -*-
"""PPTX agent specialized in presentation creation and editing."""
from .base import BaseAgent


class PPTXAgent(BaseAgent):
    """
    Specialized agent for PowerPoint presentation tasks.
    
    Skills:
    - pptx: Create, edit, and analyze PowerPoint presentations
    """
    
    DEFAULT_SYS_PROMPT = """你是一个专业的演示文稿制作助手 SlideCreator。

## 你的专长

- 创建专业的 PowerPoint 演示文稿
- 编辑和优化现有 PPT 文件
- 设计美观的幻灯片布局
- 使用模板快速生成演示文稿

## 工作原则

1. 使用装备的技能来完成 PPT 相关任务
2. 遵循设计原则，确保视觉效果专业
3. 保持内容简洁，突出重点
4. 合理使用颜色和排版

## 输出要求

- 生成的 PPT 文件可直接使用
- 提供清晰的操作说明
- 说明设计思路和选择理由
"""
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "",
        max_iters: int = 30,
        skills: list = None,
        provider: str = "",
        base_url: str = "",
    ):
        """Initialize the PPTX agent."""
        default_skills = ["./skill/pptx"]
        
        super().__init__(
            name="SlideCreator",
            sys_prompt=self.DEFAULT_SYS_PROMPT,
            skills=skills or default_skills,
            api_key=api_key,
            model_name=model_name,
            max_iters=max_iters,
            provider=provider,
            base_url=base_url,
        )
