# -*- coding: utf-8 -*-
"""
服务层模块

提供公共服务：
- context_builder: 上下文构建
- classifier: 分类器服务
- agent_manager: 智能体管理器
"""
# 延迟导入，避免循环依赖和模块加载问题
__all__ = ['build_context_prompt', 'ClassifierService', 'AgentManager']

def __getattr__(name):
    if name == 'build_context_prompt':
        from .context_builder import build_context_prompt
        return build_context_prompt
    elif name == 'ClassifierService':
        from .classifier import ClassifierService
        return ClassifierService
    elif name == 'AgentManager':
        from .agent_manager import AgentManager
        return AgentManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
