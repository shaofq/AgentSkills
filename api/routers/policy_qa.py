# -*- coding: utf-8 -*-
"""
制度问答路由
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from agentscope.message import Msg

from api.models.request import PolicyQARequest
from api.services.agent_manager import AgentManager

router = APIRouter(prefix="/api/policy-qa", tags=["制度问答"])


@router.post("")
async def policy_qa(request: PolicyQARequest):
    """制度问答 API（流式）"""
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'start', 'message': '正在查询制度...'})}\n\n"
            
            agent = AgentManager.get("policy_qa")
            response = await agent(Msg("user", request.question, "user"))
            answer = response.content if hasattr(response, "content") else str(response)
            
            yield f"data: {json.dumps({'type': 'answer', 'content': answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/sync")
async def policy_qa_sync(request: PolicyQARequest):
    """制度问答 API（同步版本）"""
    try:
        print(f"[PolicyQA] 收到问题: {request.question}")
        agent = AgentManager.get("policy_qa")
        print(f"[PolicyQA] 智能体已创建: {agent.name}")
        response = await agent(Msg("user", request.question, "user"))
        print(f"[PolicyQA] 收到响应: {type(response)}")
        answer = response.content if hasattr(response, "content") else str(response)
        print(f"[PolicyQA] 原始答案类型: {type(answer)}")
        
        # 如果 answer 是列表或 JSON 字符串，提取文本内容
        if isinstance(answer, list):
            texts = []
            for item in answer:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
                elif isinstance(item, str):
                    texts.append(item)
            answer = "\n".join(texts) if texts else str(answer)
        elif isinstance(answer, str):
            try:
                parsed = json.loads(answer)
                if isinstance(parsed, list):
                    texts = []
                    for item in parsed:
                        if isinstance(item, dict) and "text" in item:
                            texts.append(item["text"])
                        elif isinstance(item, str):
                            texts.append(item)
                    answer = "\n".join(texts) if texts else answer
            except json.JSONDecodeError:
                pass
        
        if isinstance(answer, str):
            answer = answer.replace('\\n', '\n').strip()
        
        print(f"[PolicyQA] 处理后答案: {answer[:100] if answer else 'empty'}...")
        
        return {"success": True, "answer": answer}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
