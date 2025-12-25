# -*- coding: utf-8 -*-
"""
代码助手路由
"""
import json
import re
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from agentscope.message import Msg

from api.models.request import CodeAssistantRequest
from api.services.context_builder import build_context_prompt
from agents.base import create_agent_by_skills
from api.services.agent_manager import AgentManager
from api.services.token_logger import log_agent_call

router = APIRouter(prefix="/api/code-assistant", tags=["代码助手"])


@router.post("/stream")
async def code_assistant_stream(request: CodeAssistantRequest):
    """代码助手流式 API - 支持 amis 代码生成和实时预览"""
    async def event_generator():
        try:
            user_input = request.message
            history = request.history or []
            
            yield f"data: {json.dumps({'type': 'start', 'message': '正在分析需求...'})}\n\n"
            
            # 构建包含历史上下文的提示
            context_prompt = build_context_prompt(history)
            
            # 创建代码生成智能体（使用环境变量配置的 provider）
            code_agent = create_agent_by_skills(
                name="CodeAssistant",
                skill_names=["amis-generator"],
                sys_prompt="""你是一个专业的 amis 低代码配置生成助手。
你的任务是根据用户需求生成 amis JSON 配置。

输出要求：
1. 生成的 JSON 必须是有效的 amis 配置
2. 使用 ```json 代码块包裹 JSON 配置
3. 在 JSON 之前简要说明设计思路
4. 确保生成的配置可以直接在 amis 中渲染
5. 如果用户要求修改之前的配置，请基于上下文进行修改

常用组件：
- form: 表单
- table: 表格/CRUD
- page: 页面容器
- cards: 卡片列表
- chart: 图表
""",
                max_iters=30,
            )
            
            yield f"data: {json.dumps({'type': 'thinking', 'message': '正在生成代码...'})}\n\n"
            
            full_input = context_prompt + "当前用户需求: " + user_input if context_prompt else user_input
            
            response = await code_agent(Msg("user", full_input, "user"))
            result = response.content if hasattr(response, "content") else str(response)
            
            if isinstance(result, list):
                result = result[0].get("text", str(result[0])) if result else ""
            
            # 记录 Token 消耗
            from config.settings import MODEL_PROVIDER, AIGATEWAY_MODEL, DEFAULT_MODEL
            current_model = AIGATEWAY_MODEL if MODEL_PROVIDER == "aigateway" else DEFAULT_MODEL
            log_agent_call(
                agent_id="code-agent",
                agent_name="代码助手",
                model=current_model,
                input_text=full_input,
                output_text=str(result) if result else "",
            )
            
            # 尝试提取 JSON 代码块
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', str(result))
            if json_match:
                try:
                    amis_json = json.loads(json_match.group(1))
                    yield f"data: {json.dumps({'type': 'amis_code', 'code': amis_json})}\n\n"
                except json.JSONDecodeError:
                    pass
            
            yield f"data: {json.dumps({'type': 'content', 'content': str(result)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
