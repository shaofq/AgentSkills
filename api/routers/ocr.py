# -*- coding: utf-8 -*-
"""
OCR 识别路由
"""
from fastapi import APIRouter, HTTPException
from agentscope.message import Msg

from api.models.request import OCRRequest, PolicyQARequest
from api.services.agent_manager import AgentManager
from api.services.token_logger import log_agent_call

router = APIRouter(prefix="/api/ocr", tags=["OCR识别"])


@router.post("/recognize")
async def ocr_recognize(request: OCRRequest):
    """OCR 识别 API"""
    try:
        print(f"[OCR] 收到识别请求: {request.file_path}")
        agent = AgentManager.get("ocr")
        
        result = await agent.recognize_file(
            file_path=request.file_path,
            dpi=request.dpi,
            prompt_mode=request.prompt_mode
        )
        
        print(f"[OCR] 识别完成: {len(result) if result else 0} 字符")
        
        # 记录 Token 消耗
        log_agent_call(
            agent_id="ocr-agent",
            agent_name="OCR识别",
            model="qwen3-max",
            input_text=request.file_path,
            output_text=result if result else "",
        )
        
        return {"success": True, "text": result}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def ocr_chat(request: PolicyQARequest):
    """OCR 智能体对话 API（支持自动检测文件路径）"""
    try:
        print(f"[OCR] 收到对话: {request.question}")
        agent = AgentManager.get("ocr")
        response = await agent(Msg("user", request.question, "user"))
        answer = response.content if hasattr(response, "content") else str(response)
        
        print(f"[OCR] 响应: {answer[:100] if answer else 'empty'}...")
        
        # 记录 Token 消耗
        log_agent_call(
            agent_id="ocr-agent",
            agent_name="OCR识别",
            model="qwen3-max",
            input_text=request.question,
            output_text=answer if isinstance(answer, str) else str(answer),
        )
        
        return {"success": True, "answer": answer}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
