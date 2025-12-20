# -*- coding: utf-8 -*-
"""
智能体相关路由
"""
from typing import List
from fastapi import APIRouter

from api.models.agent import AgentConfig

router = APIRouter(prefix="/api", tags=["智能体"])


@router.get("/agents", response_model=List[AgentConfig])
async def get_agents():
    """获取可用的智能体列表"""
    return [
        AgentConfig(
            id="router",
            name="Router",
            type="router",
            description="路由智能体 - 分析用户意图并分发任务",
            systemPrompt="你是一个智能路由助手，负责分析用户请求并将其分发到合适的专业智能体。",
            skills=[],
            model="qwen3-max",
            maxIters=10,
        ),
        AgentConfig(
            id="code_agent",
            name="CodeMaster",
            type="code",
            description="代码生成智能体 - 生成 amis 配置和前端代码",
            systemPrompt="你是一个专业的代码生成助手 CodeMaster。你的专长是生成 amis 低代码 JSON 配置、编写前端组件代码。",
            skills=["amis-code-assistant"],
            model="qwen3-max",
            maxIters=30,
        ),
        AgentConfig(
            id="pptx_agent",
            name="SlideCreator",
            type="pptx",
            description="PPT制作智能体 - 创建和编辑演示文稿",
            systemPrompt="你是一个专业的演示文稿制作助手 SlideCreator。你的专长是创建和编辑 PowerPoint 演示文稿。",
            skills=["pptx"],
            model="qwen3-max",
            maxIters=30,
        ),
        AgentConfig(
            id="data_agent",
            name="DataAnalyst",
            type="data",
            description="数据分析智能体 - 数据处理和可视化",
            systemPrompt="你是一个专业的数据分析助手 DataAnalyst。你的专长是数据分析、SQL查询和图表可视化。",
            skills=["data-analysis"],
            model="qwen3-max",
            maxIters=30,
        ),
        AgentConfig(
            id="policy_qa_agent",
            name="PolicyQA",
            type="policy",
            description="制度问答智能体 - 解答公司规章制度问题",
            systemPrompt="你是岸基科技公司的制度问答助手，专门负责解答员工关于公司规章制度的各类问题。",
            skills=["company-policy-qa"],
            model="qwen3-max",
            maxIters=10,
        ),
    ]
