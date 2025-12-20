# -*- coding: utf-8 -*-
"""
上下文构建服务

提供对话历史上下文构建功能，用于多轮对话场景。
"""
from typing import List, Optional


def build_context_prompt(
    history: List[dict],
    max_messages: int = 10,
    max_length: int = 500,
    prefix: str = "以下是之前的对话历史，请参考上下文理解用户需求：\n\n",
    suffix: str = "---\n\n当前用户需求: "
) -> str:
    """
    构建包含对话历史的上下文提示。
    
    Args:
        history: 对话历史列表，每条消息包含 role 和 content
        max_messages: 最多保留的消息数量
        max_length: 每条消息的最大长度
        prefix: 上下文前缀
        suffix: 上下文后缀
    
    Returns:
        构建好的上下文提示字符串，如果历史为空则返回空字符串
    """
    if not history:
        return ""
    
    context = prefix
    
    for msg in history[-max_messages:]:
        role = "用户" if msg.get("role") == "user" else "助手"
        content = msg.get("content", "")
        if len(content) > max_length:
            content = content[:max_length] + "..."
        context += f"{role}: {content}\n\n"
    
    context += suffix
    return context
