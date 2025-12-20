# -*- coding: utf-8 -*-
"""
技能创建路由
"""
from fastapi import APIRouter, HTTPException
from agentscope.message import Msg

from api.models.request import PolicyQARequest
from api.services.agent_manager import AgentManager

router = APIRouter(prefix="/api/skill-creator", tags=["技能创建"])


@router.post("/chat")
async def skill_creator_chat(request: PolicyQARequest):
    """技能创建智能体对话 API"""
    try:
        print(f"[SkillCreator] 收到请求: {request.question}")
        agent = AgentManager.get("skill_creator")
        response = await agent(Msg("user", request.question, "user"))
        answer = response.content if hasattr(response, "content") else str(response)
        
        print(f"[SkillCreator] 响应: {answer[:100] if answer else 'empty'}...")
        return answer
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
