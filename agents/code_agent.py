# -*- coding: utf-8 -*-
"""Code generation agent specialized in amis and frontend development."""
from .base import BaseAgent


class CodeAgent(BaseAgent):
    """
    Specialized agent for code generation tasks.
    
    Skills:
    - amis-code-assistant: Generate amis low-code configurations
    - react-code: Generate React components (future)
    - api-design: Design RESTful APIs (future)
    """
    
    DEFAULT_SYS_PROMPT = """你是一个专业的代码生成助手 CodeMaster。

## 你的专长

- 生成 amis 低代码 JSON 配置
- 编写 React/Vue 组件代码
- 设计 RESTful API 接口

## 工作原则

1. 使用装备的技能来查阅文档和示例
2. 生成的代码必须符合规范，可直接运行
3. 提供清晰的代码注释和使用说明
4. 遵循最佳实践和设计模式

## 输出要求

- JSON 配置使用标准格式，确保语法正确
- 代码包含必要的导入语句
- 提供简要的使用说明
"""
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "qwen3-max",
        max_iters: int = 30,
        skills: list = None,
    ):
        """Initialize the code agent."""
        default_skills = ["./skills/amis-code-assistant"]
        
        super().__init__(
            name="CodeMaster",
            sys_prompt=self.DEFAULT_SYS_PROMPT,
            skills=skills or default_skills,
            api_key=api_key,
            model_name=model_name,
            max_iters=max_iters,
        )
