# -*- coding: utf-8 -*-
"""
智能体相关数据模型
"""
from typing import List
from pydantic import BaseModel


class AgentConfig(BaseModel):
    """智能体配置"""
    id: str
    name: str
    type: str
    description: str
    systemPrompt: str
    skills: List[str]
    model: str = "qwen3-max"
    maxIters: int = 30
