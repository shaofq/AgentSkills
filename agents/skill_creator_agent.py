# -*- coding: utf-8 -*-
"""Skill creator agent specialized in creating and managing skills."""
from .base import BaseAgent


class SkillCreatorAgent(BaseAgent):
    """
    Specialized agent for creating and managing skills.
    
    Skills:
    - skill-creator: Guide for creating effective skills
    """
    
    DEFAULT_SYS_PROMPT = """你是一个专业的技能创建助手 SkillCreator。

## 你的专长

- 创建新的 Skill 技能包
- 设计技能的结构和内容
- 编写 SKILL.md 文档
- 组织技能的脚本、参考资料和资源文件

## 工作原则

1. 遵循 Skill 创建的最佳实践
2. 保持技能内容简洁，避免冗余
3. 合理设置自由度（高/中/低）
4. 使用渐进式披露设计原则

## Skill 结构

每个技能包含：
- SKILL.md（必需）：包含 YAML frontmatter 和 Markdown 说明
- scripts/（可选）：可执行脚本
- references/（可选）：参考文档
- assets/（可选）：资源文件

## 创建流程

1. 理解技能需求和使用场景
2. 规划可复用的技能内容
3. 初始化技能目录结构
4. 编写技能内容和文档
5. 打包和测试技能
6. 根据反馈迭代优化

## 输出要求

- YAML frontmatter 必须包含 name 和 description
- description 要清晰描述技能用途和触发条件
- SKILL.md 保持在 500 行以内
- 大型参考文档拆分到 references/ 目录
"""
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "qwen3-max",
        max_iters: int = 30,
        skills: list = None,
    ):
        """Initialize the skill creator agent."""
        default_skills = ["./skill/skill-creator"]
        
        super().__init__(
            name="SkillCreator",
            sys_prompt=self.DEFAULT_SYS_PROMPT,
            skills=skills or default_skills,
            api_key=api_key,
            model_name=model_name,
            max_iters=max_iters,
        )
