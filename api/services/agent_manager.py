# -*- coding: utf-8 -*-
"""
智能体管理器

提供智能体的单例管理和工厂创建功能。
"""
import os
from typing import Dict, Any, Optional

from agents.base import BaseAgent, create_agent_by_skills
from agents.simple import SimpleAgent
from agents.policy_qa_agent import PolicyQAAgent
from agents.code_agent import CodeAgent
from agents.pptx_agent import PPTXAgent
from agents.ocr_agent import OCRAgent
from agents.skill_creator_agent import SkillCreatorAgent


class AgentManager:
    """智能体单例管理器"""
    
    _instances: Dict[str, Any] = {}
    _api_key: str = None
    
    @classmethod
    def set_api_key(cls, api_key: str):
        """设置 API 密钥"""
        cls._api_key = api_key
    
    @classmethod
    def get_api_key(cls) -> str:
        """获取 API 密钥"""
        if cls._api_key is None:
            cls._api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        return cls._api_key
    
    @classmethod
    def get(cls, agent_type: str, **kwargs) -> Any:
        """
        获取或创建智能体实例（单例模式）。
        
        Args:
            agent_type: 智能体类型 (policy_qa, ocr, skill_creator, code, pptx)
            **kwargs: 创建智能体的额外参数
        
        Returns:
            智能体实例
        """
        if agent_type not in cls._instances:
            cls._instances[agent_type] = cls._create(agent_type, **kwargs)
        return cls._instances[agent_type]
    
    @classmethod
    def _create(cls, agent_type: str, **kwargs) -> Any:
        """创建智能体实例"""
        api_key = kwargs.get("api_key") or cls.get_api_key()
        model = kwargs.get("model", "qwen3-max")
        max_iters = kwargs.get("max_iters", 30)
        
        if agent_type == "policy_qa":
            print("[AgentManager] 创建 PolicyQAAgent...")
            return PolicyQAAgent(
                api_key=api_key,
                model_name=model,
                max_iters=kwargs.get("max_iters", 10),
            )
        elif agent_type == "ocr":
            print("[AgentManager] 创建 OCRAgent...")
            return OCRAgent(
                api_key=api_key,
                model_name=model,
                max_iters=kwargs.get("max_iters", 10),
            )
        elif agent_type == "skill_creator":
            print("[AgentManager] 创建 SkillCreatorAgent...")
            return SkillCreatorAgent(
                api_key=api_key,
                model_name=model,
                max_iters=max_iters,
            )
        elif agent_type == "code":
            print("[AgentManager] 创建 CodeAgent...")
            return CodeAgent(
                api_key=api_key,
                model_name=model,
                max_iters=max_iters,
            )
        elif agent_type == "pptx":
            print("[AgentManager] 创建 PPTXAgent...")
            return PPTXAgent(
                api_key=api_key,
                model_name=model,
                max_iters=max_iters,
            )
        else:
            raise ValueError(f"未知的智能体类型: {agent_type}")
    
    @classmethod
    def create_from_config(cls, config: dict, api_key: str = None) -> Any:
        """
        根据配置创建智能体实例（非单例）。
        
        Args:
            config: 智能体配置字典
            api_key: API 密钥
        
        Returns:
            智能体实例
        """
        api_key = api_key or cls.get_api_key()
        agent_type = config.get("type", "custom")
        agent_id = config.get("id", "")
        model = config.get("model", "qwen3-max")
        max_iters = config.get("maxIters", 30)
        
        # 使用预定义的 Agent 类
        if agent_type == "code" or agent_id == "code_agent":
            return CodeAgent(
                api_key=api_key,
                model_name=model,
                max_iters=max_iters,
            )
        elif agent_type == "pptx" or agent_id == "pptx_agent":
            return PPTXAgent(
                api_key=api_key,
                model_name=model,
                max_iters=max_iters,
            )
        elif agent_type == "policy" or agent_id == "policy_qa_agent":
            return PolicyQAAgent(
                api_key=api_key,
                model_name=model,
                max_iters=config.get("maxIters", 10),
            )
        elif agent_type == "router" or agent_id == "router":
            return SimpleAgent(
                name=config.get("name", "Router"),
                sys_prompt=config.get("systemPrompt", "你是一个智能路由助手，负责分析用户请求并提供建议。"),
                api_key=api_key,
                model_name=model,
            )
        else:
            # 自定义 Agent，使用 BaseAgent
            skill_paths = [f"./skill/{s}" for s in config.get("skills", [])]
            return BaseAgent(
                name=config.get("name", agent_id),
                sys_prompt=config.get("systemPrompt", ""),
                skills=skill_paths,
                api_key=api_key,
                model_name=model,
                max_iters=max_iters,
            )
    
    @classmethod
    def clear(cls):
        """清除所有缓存的智能体实例"""
        cls._instances.clear()
