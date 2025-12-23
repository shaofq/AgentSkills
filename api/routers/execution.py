# -*- coding: utf-8 -*-
"""
工作流执行路由
"""
import json
from typing import Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from agentscope.message import Msg

from api.models.request import PredefinedWorkflowRequest, WorkflowTestRequest
from api.services.context_builder import build_context_prompt
from api.services.classifier import ClassifierService
from api.services.agent_manager import AgentManager
from api.services.token_logger import log_agent_call
from api.services.console_logger import capture_console_for_session, log_to_session
from api.services.tool_executor import tool_executor
from api.utils.graph import get_execution_order
from agents.base import create_agent_by_skills, set_log_callback

router = APIRouter(prefix="/api/workflow", tags=["工作流执行"])

# 预定义工作流存储（由 config 模块加载）
predefined_workflows: Dict[str, dict] = {}


def set_predefined_workflows(workflows: Dict[str, dict]):
    """设置预定义工作流"""
    global predefined_workflows
    predefined_workflows = workflows


@router.post("/run")
async def run_predefined_workflow(request: PredefinedWorkflowRequest):
    """执行预定义工作流（同步返回最终结果）"""
    workflow_name = request.workflow_name
    user_input = request.input
    history = request.history or []
    
    if workflow_name not in predefined_workflows:
        raise HTTPException(status_code=404, detail=f"预定义工作流 '{workflow_name}' 不存在")
    
    workflow = predefined_workflows[workflow_name]
    api_key = AgentManager.get_api_key()
    
    try:
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        # 构建上下文提示
        context_prompt = build_context_prompt(history)
        
        agent_nodes = [n for n in nodes if n["type"] == "agent"]
        agents = {}
        
        for node in agent_nodes:
            config = node["data"].get("agentConfig", {})
            if config:
                agent = AgentManager.create_from_config(config, api_key)
                agents[node["id"]] = agent
                print(f"[Workflow] 创建智能体: {node['id']} -> {agent.__class__.__name__}")
        
        execution_order = get_execution_order(nodes, edges)
        
        current_input = context_prompt + user_input if context_prompt else user_input
        final_output = ""
        is_first_agent = True
        
        for node_id in execution_order:
            node = next((n for n in nodes if n["id"] == node_id), None)
            if not node:
                continue
            
            if node["type"] == "agent" and node_id in agents:
                agent = agents[node_id]
                print(f"[Workflow] 执行节点: {node_id}")
                agent_input = current_input if is_first_agent else current_input
                response = await agent(Msg("user", agent_input, "user"))
                output = response.content if hasattr(response, "content") else str(response)
                print(f"[Workflow] 节点 {node_id} 输出: {output[:100] if output else 'empty'}...")
                
                # 记录 Token 消耗
                agent_config = node["data"].get("agentConfig", {})
                agent_name = agent_config.get("name", node_id)
                model_name = agent_config.get("model", "qwen3-max")
                log_agent_call(
                    agent_id=node_id,
                    agent_name=agent_name,
                    model=model_name,
                    input_text=agent_input,
                    output_text=output if output else "",
                )
                
                current_input = output
                final_output = output
                is_first_agent = False
            elif node["type"] == "classifier":
                classifier_config = node["data"].get("classifierConfig", {})
                categories = classifier_config.get("categories", [])
                model = classifier_config.get("model", "qwen3-max")
                
                if categories:
                    classifier = ClassifierService(api_key)
                    matched = await classifier.classify(current_input, categories, model)
                    print(f"[Workflow] 分类器结果: {matched['name'] if matched else 'None'}")
            elif node["type"] == "tool":
                # 执行工具节点
                tool_config = node["data"].get("toolConfig", {})
                tool_type = tool_config.get("toolType", "")
                tool_params = tool_config.get("params", {})
                node_label = node["data"].get("label", node_id)
                
                print(f"[Workflow] 执行工具节点: {node_label}, 类型: {tool_type}")
                
                # 构建上下文变量
                context = {
                    "input": current_input,
                    "content": current_input,
                    "output": final_output,
                }
                
                result = tool_executor.execute(tool_type, tool_params, context)
                
                if result.get("success"):
                    output = json.dumps(result, ensure_ascii=False)
                    current_input = output
                    final_output = output
                    print(f"[Workflow] 工具执行成功: {result.get('message', '')}")
                else:
                    error_msg = result.get("error", "工具执行失败")
                    print(f"[Workflow] 工具执行失败: {error_msg}")
                    final_output = f"工具执行失败: {error_msg}"
            elif node["type"] == "input":
                current_input = user_input
            elif node["type"] == "output":
                final_output = current_input
        
        return final_output
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/stream")
async def run_predefined_workflow_stream(request: PredefinedWorkflowRequest):
    """执行预定义工作流（流式返回思考过程和结果）"""
    import asyncio
    from collections import deque
    import threading
    
    # 日志队列（线程安全）
    log_queue: deque = deque(maxlen=1000)
    log_lock = threading.Lock()
    
    def log_callback(source: str, log_type: str, message: str):
        """日志回调函数，将日志添加到队列"""
        with log_lock:
            log_queue.append({
                'source': source,
                'log_type': log_type,
                'message': message
            })
    
    def get_pending_logs():
        """获取并清空待发送的日志"""
        with log_lock:
            logs = list(log_queue)
            log_queue.clear()
            return logs
    
    async def event_generator():
        try:
            workflow_name = request.workflow_name
            user_input = request.input
            history = request.history or []
            api_key = AgentManager.get_api_key()
            
            # 设置日志回调
            set_log_callback(log_callback)
            
            if workflow_name not in predefined_workflows:
                yield f"data: {json.dumps({'type': 'error', 'message': f'工作流 {workflow_name} 不存在'})}\n\n"
                return
            
            workflow = predefined_workflows[workflow_name]
            nodes = workflow.get("nodes", [])
            edges = workflow.get("edges", [])
            
            yield f"data: {json.dumps({'type': 'thinking', 'message': '正在分析需求...'})}\n\n"
            yield f"data: {json.dumps({'type': 'console_log', 'source': 'system', 'log_type': 'info', 'message': f'开始执行工作流: {workflow_name}'})}\n\n"
            
            # 构建上下文提示
            context_prompt = ""
            print(f"[Debug] 收到历史消息数量: {len(history)}")
            for i, msg in enumerate(history):
                print(f"[Debug] history[{i}]: role={msg.get('role')}, content长度={len(msg.get('content', ''))}")
            if history:
                yield f"data: {json.dumps({'type': 'thinking', 'message': f'加载对话历史 ({len(history)} 条消息)...'})}\n\n"
                context_prompt = build_context_prompt(history)
                print(f"[Debug] context_prompt 长度: {len(context_prompt)}")
            
            # 创建智能体
            agent_nodes = [n for n in nodes if n["type"] == "agent"]
            skill_agent_nodes = [n for n in nodes if n["type"] == "skill-agent"]
            simple_agent_nodes = [n for n in nodes if n["type"] == "simple-agent"]
            agents = {}
            
            for node in agent_nodes:
                config = node["data"].get("agentConfig", {})
                if config:
                    agent_name = config.get("name", node["id"])
                    yield f"data: {json.dumps({'type': 'thinking', 'message': f'初始化智能体: {agent_name}'})}\n\n"
                    yield f"data: {json.dumps({'type': 'console_log', 'source': 'agent', 'log_type': 'info', 'message': f'[Agent] 创建智能体: {agent_name}'})}\n\n"
                    agent = AgentManager.create_from_config(config, api_key)
                    agents[node["id"]] = agent
            
            # 创建对话智能体（SimpleAgent）
            for node in simple_agent_nodes:
                config = node["data"].get("simpleAgentConfig", {})
                agent_name = config.get("name", "SimpleAgent")
                yield f"data: {json.dumps({'type': 'thinking', 'message': f'初始化对话智能体: {agent_name}'})}\n\n"
                from agents.simple import SimpleAgent
                agent = SimpleAgent(
                    name=agent_name,
                    sys_prompt=config.get("systemPrompt", ""),
                    api_key=api_key,
                    model_name=config.get("model", "qwen3-max"),
                )
                agents[node["id"]] = agent
            
            for node in skill_agent_nodes:
                skill_config = node["data"].get("skillAgentConfig", {})
                skills = skill_config.get("skills", [])
                if skills:
                    skill_names = ", ".join(skills)
                    yield f"data: {json.dumps({'type': 'thinking', 'message': f'初始化技能智能体: {skill_names}'})}\n\n"
                    model = skill_config.get("model", "qwen3-max")
                    max_iters = skill_config.get("maxIters", 30)
                    sys_prompt = skill_config.get("systemPrompt") or None
                    agent = create_agent_by_skills(
                        name=f"SkillAgent_{node['id']}",
                        skill_names=skills,
                        sys_prompt=sys_prompt,
                        api_key=api_key,
                        model_name=model,
                        max_iters=max_iters,
                    )
                    agents[node["id"]] = agent
            
            execution_order = get_execution_order(nodes, edges)
            yield f"data: {json.dumps({'type': 'thinking', 'message': f'执行顺序: {len(execution_order)} 个节点'})}\n\n"
            
            # 保存包含对话历史的完整输入
            full_input_with_history = context_prompt + user_input if context_prompt else user_input
            current_input = full_input_with_history
            print(f"[Debug] 发送给Agent的完整输入:\n{current_input}\n{'='*50}")
            final_output = ""
            
            # 记录分类器已执行的分支节点，避免重复执行
            executed_branch_nodes = set()
            
            for node_id in execution_order:
                # 如果该节点已经被分类器分支执行过，跳过
                if node_id in executed_branch_nodes:
                    continue
                    
                node = next((n for n in nodes if n["id"] == node_id), None)
                if not node:
                    continue
                
                node_type = node.get("type")
                node_label = node.get("data", {}).get("label", node_id)
                
                if node_type in ["agent", "skill-agent", "simple-agent"] and node_id in agents:
                    # 获取技能信息用于显示
                    skill_info = ""
                    if node_type == "skill-agent":
                        skill_config = node["data"].get("skillAgentConfig", {})
                        skills = skill_config.get("skills", [])
                        if skills:
                            skill_info = f" (技能: {', '.join(skills)})"
                    elif node_type == "simple-agent":
                        skill_info = " (对话模式)"
                    
                    yield f"data: {json.dumps({'type': 'node_start', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'正在执行: {node_label}{skill_info}'})}\n\n"
                    yield f"data: {json.dumps({'type': 'console_log', 'source': 'workflow', 'log_type': 'info', 'message': f'[Workflow] 执行节点: {node_label}{skill_info}'})}\n\n"
                    
                    agent = agents[node_id]
                    thinking_msg = f'{node_label} 正在思考...' if not skill_info else f'{node_label}{skill_info} 正在执行...'
                    yield f"data: {json.dumps({'type': 'thinking', 'message': thinking_msg})}\n\n"
                    yield f"data: {json.dumps({'type': 'console_log', 'source': 'agent', 'log_type': 'info', 'message': f'[Agent] {node_label}{skill_info} 正在处理输入...'})}\n\n"
                    
                    agent_input = current_input
                    response = await agent(Msg("user", agent_input, "user"))
                    output = response.content if hasattr(response, "content") else str(response)
                    
                    # 推送 agent 执行过程中收集的日志
                    pending_logs = get_pending_logs()
                    for log in pending_logs:
                        yield f"data: {json.dumps({'type': 'console_log', 'source': log['source'], 'log_type': log['log_type'], 'message': log['message']})}\n\n"
                    
                    # 推送输出日志
                    output_preview = str(output)[:100] + '...' if len(str(output)) > 100 else str(output)
                    yield f"data: {json.dumps({'type': 'console_log', 'source': 'agent', 'log_type': 'success', 'message': f'[Agent] {node_label} 输出: {output_preview}'})}\n\n"
                    
                    if isinstance(output, list):
                        output = output[0].get("text", str(output[0])) if output else ""
                    
                    # 记录 Token 消耗
                    if node_type == "agent":
                        agent_config = node["data"].get("agentConfig", {})
                        agent_name = agent_config.get("name", node_label)
                        model_name = agent_config.get("model", "qwen3-max")
                    elif node_type == "simple-agent":
                        simple_config = node["data"].get("simpleAgentConfig", {})
                        agent_name = simple_config.get("name", node_label)
                        model_name = simple_config.get("model", "qwen3-max")
                    else:
                        skill_config = node["data"].get("skillAgentConfig", {})
                        agent_name = node_label
                        model_name = skill_config.get("model", "qwen3-max")
                    
                    log_agent_call(
                        agent_id=node_id,
                        agent_name=agent_name,
                        model=model_name,
                        input_text=agent_input,
                        output_text=str(output) if output else "",
                    )
                    
                    yield f"data: {json.dumps({'type': 'node_complete', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'{node_label}{skill_info} 执行完成'})}\n\n"
                    
                    current_input = str(output)
                    final_output = str(output)
                    
                elif node_type == "classifier":
                    yield f"data: {json.dumps({'type': 'node_start', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'正在分类: {node_label}'})}\n\n"
                    
                    classifier_config = node["data"].get("classifierConfig", {})
                    categories = classifier_config.get("categories", [])
                    model = classifier_config.get("model", "qwen3-max")
                    
                    if categories:
                        yield f"data: {json.dumps({'type': 'thinking', 'message': '正在分析分类...'})}\n\n"
                        
                        classifier = ClassifierService(api_key)
                        matched = await classifier.classify(current_input, categories, model)
                        
                        print(f"Classifier: {matched['name'] if matched else 'None'}")
                        yield f"data: {json.dumps({'type': 'classifier_result', 'nodeId': node_id, 'nodeLabel': node_label, 'result': matched['name'] if matched else 'None'})}\n\n"
                        
                        # 根据分类结果选择下一个节点
                        if matched:
                            matched_category_id = matched.get("id")
                            
                            # 收集所有从分类器出发的分支节点，标记为需要跳过
                            for edge in edges:
                                if edge.get("source") == node_id and edge.get("sourceHandle"):
                                    branch_target = edge.get("target")
                                    # 如果不是匹配的分支，添加到跳过集合
                                    if edge.get("sourceHandle") != matched_category_id:
                                        executed_branch_nodes.add(branch_target)
                            
                            # 找到匹配的分支并执行
                            for edge in edges:
                                if edge.get("source") == node_id and edge.get("sourceHandle") == matched_category_id:
                                    target_node_id = edge.get("target")
                                    # 标记为已执行
                                    executed_branch_nodes.add(target_node_id)
                                    
                                    # 执行匹配的分支节点
                                    target_node = next((n for n in nodes if n["id"] == target_node_id), None)
                                    if target_node and target_node_id in agents:
                                        target_label = target_node.get("data", {}).get("label", target_node_id)
                                        target_type = target_node.get("type")
                                        
                                        # 获取技能信息用于显示
                                        branch_skill_info = ""
                                        if target_type == "skill-agent":
                                            branch_skill_config = target_node["data"].get("skillAgentConfig", {})
                                            branch_skills = branch_skill_config.get("skills", [])
                                            if branch_skills:
                                                branch_skill_info = f" (技能: {', '.join(branch_skills)})"
                                        elif target_type == "simple-agent":
                                            branch_skill_info = " (对话模式)"
                                        
                                        yield f"data: {json.dumps({'type': 'node_start', 'nodeId': target_node_id, 'nodeLabel': target_label, 'message': f'正在执行: {target_label}{branch_skill_info}'})}\n\n"
                                        thinking_msg = f'{target_label}{branch_skill_info} 正在执行...' if branch_skill_info else f'{target_label} 正在思考...'
                                        yield f"data: {json.dumps({'type': 'thinking', 'message': thinking_msg})}\n\n"
                                        
                                        agent = agents[target_node_id]
                                        # 使用完整输入（包含对话历史），而不是current_input
                                        branch_input = full_input_with_history
                                        print(f"[Debug] 分类器分支执行，输入长度: {len(branch_input)}")
                                        print(f"[Debug] 分类器分支输入内容:\n{branch_input[:500]}...")
                                        response = await agent(Msg("user", branch_input, "user"))
                                        output = response.content if hasattr(response, "content") else str(response)
                                        
                                        # 处理列表格式的响应，提取text字段
                                        if isinstance(output, list):
                                            output = output[0].get("text", str(output[0])) if output else ""
                                        
                                        pending_logs = get_pending_logs()
                                        for log in pending_logs:
                                            yield f"data: {json.dumps({'type': 'console_log', 'source': log['source'], 'log_type': log['log_type'], 'message': log['message']})}\n\n"
                                        
                                        skill_config = target_node["data"].get("skillAgentConfig", {})
                                        log_agent_call(
                                            agent_id=target_node_id,
                                            agent_name=target_label,
                                            model=skill_config.get("model", "qwen3-max"),
                                            input_text=current_input,
                                            output_text=str(output) if output else "",
                                        )
                                        
                                        yield f"data: {json.dumps({'type': 'node_complete', 'nodeId': target_node_id, 'nodeLabel': target_label, 'message': f'{target_label}{branch_skill_info} 执行完成'})}\n\n"
                                        
                                        current_input = str(output)
                                        final_output = str(output)
                                    break
                
                elif node_type == "tool":
                    # 执行工具节点
                    tool_config = node.get("data", {}).get("toolConfig", {})
                    tool_type = tool_config.get("toolType", "")
                    tool_params = tool_config.get("params", {})
                    
                    yield f"data: {json.dumps({'type': 'node_start', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'正在执行工具: {node_label}'})}\n\n"
                    yield f"data: {json.dumps({'type': 'thinking', 'message': f'执行工具 {node_label}...'})}\n\n"
                    
                    # 构建上下文变量
                    context = {
                        "input": current_input,
                        "content": current_input,
                        "output": final_output,
                    }
                    
                    result = tool_executor.execute(tool_type, tool_params, context)
                    
                    if result.get("success"):
                        output = json.dumps(result, ensure_ascii=False)
                        current_input = output
                        final_output = output
                        tool_msg = result.get("message", "")
                        yield f"data: {json.dumps({'type': 'console_log', 'source': 'tool', 'log_type': 'success', 'message': f'[Tool] {node_label} 执行成功: {tool_msg}'})}\n\n"
                    else:
                        error_msg = result.get("error", "工具执行失败")
                        yield f"data: {json.dumps({'type': 'console_log', 'source': 'tool', 'log_type': 'error', 'message': f'[Tool] {node_label} 执行失败: {error_msg}'})}\n\n"
                        final_output = f"工具执行失败: {error_msg}"
                    
                    yield f"data: {json.dumps({'type': 'node_complete', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'{node_label} 执行完成'})}\n\n"
                
                elif node_type == "input":
                    # 保持完整输入（包含对话历史），不要重置为只有user_input
                    current_input = full_input_with_history
                elif node_type == "output":
                    final_output = current_input
            
            yield f"data: {json.dumps({'type': 'console_log', 'source': 'system', 'log_type': 'success', 'message': '工作流执行完成'})}\n\n"
            yield f"data: {json.dumps({'type': 'content', 'content': final_output})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # 清理日志回调
            set_log_callback(None)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/test")
async def test_workflow(request: WorkflowTestRequest):
    """测试工作流（流式返回执行过程）"""
    import asyncio
    api_key = AgentManager.get_api_key()
    
    async def event_generator():
        try:
            workflow = request.workflow
            user_input = request.input
            nodes = workflow.get("nodes", [])
            edges = workflow.get("edges", [])
            
            yield f"data: {json.dumps({'type': 'log', 'message': '开始执行工作流测试...'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '输入内容: ' + user_input})}\n\n"
            
            # 创建智能体
            agents = {}
            agent_nodes = [n for n in nodes if n["type"] == "agent"]
            
            for node in agent_nodes:
                config = node["data"].get("agentConfig", {})
                if config:
                    node_label = node["data"].get("label", node["id"])
                    msg = f"初始化智能体: {config.get('name', node['id'])}"
                    yield f"data: {json.dumps({'type': 'log', 'nodeId': node['id'], 'nodeLabel': node_label, 'message': msg})}\n\n"
                    
                    agent = AgentManager.create_from_config(config, api_key)
                    agents[node["id"]] = agent
            
            # 构建邻接图
            graph = {n["id"]: [] for n in nodes}
            for edge in edges:
                source = edge.get("source")
                target = edge.get("target")
                source_handle = edge.get("sourceHandle")
                if source and target and source in graph:
                    graph[source].append({
                        "target": target,
                        "handle": source_handle
                    })
            
            # 找到起始节点
            start_nodes = [n for n in nodes if n.get("type") == "input"]
            if not start_nodes:
                yield f"data: {json.dumps({'type': 'log', 'message': '错误: 未找到输入节点'})}\n\n"
                return
            
            # 执行工作流
            context = {"original_input": user_input}
            node_outputs = {}
            visited = set()
            
            async def execute_from_node(node_id: str, input_data: str):
                if node_id in visited:
                    return
                
                visited.add(node_id)
                node = next((n for n in nodes if n["id"] == node_id), None)
                if not node:
                    return
                
                node_type = node.get("type")
                node_label = node.get("data", {}).get("label", node_id)
                
                yield f"data: {json.dumps({'type': 'node_start', 'nodeId': node_id, 'nodeLabel': node_label})}\n\n"
                
                output = input_data
                
                try:
                    if node_type == "input":
                        output = input_data
                        
                    elif node_type == "output":
                        output = input_data
                        yield f"data: {json.dumps({'type': 'output', 'content': output})}\n\n"
                        
                    elif node_type == "agent" and node_id in agents:
                        agent = agents[node_id]
                        response = await agent(Msg("user", input_data, "user"))
                        output = response.content if hasattr(response, "content") else str(response)
                        
                    elif node_type == "condition":
                        condition_config = node.get("data", {}).get("conditionConfig", {})
                        condition_expr = condition_config.get("expression", "")
                        
                        if condition_expr:
                            input_str = str(input_data) if not isinstance(input_data, str) else input_data
                            result = condition_expr.lower() in input_str.lower()
                        else:
                            result = True
                        
                        context["condition_result"] = result
                        yield f"data: {json.dumps({'type': 'condition_result', 'nodeId': node_id, 'nodeLabel': node_label, 'result': result, 'expression': condition_expr})}\n\n"
                        output = input_data
                        
                    elif node_type == "classifier":
                        classifier_config = node.get("data", {}).get("classifierConfig", {})
                        categories = classifier_config.get("categories", [])
                        model = classifier_config.get("model", "qwen3-max")
                        
                        if categories:
                            classifier = ClassifierService(api_key)
                            matched_category = await classifier.classify(input_data, categories, model)
                            
                            context["classifier_result"] = matched_category["id"] if matched_category else None
                            context["classifier_category_name"] = matched_category["name"] if matched_category else None
                            
                            yield f"data: {json.dumps({'type': 'classifier_result', 'nodeId': node_id, 'nodeLabel': node_label, 'result': matched_category['name'] if matched_category else 'None', 'input': input_data[:100]})}\n\n"
                        
                        output = input_data
                    
                    elif node_type == "skill-agent":
                        skill_config = node.get("data", {}).get("skillAgentConfig", {})
                        skills = skill_config.get("skills", [])
                        model = skill_config.get("model", "qwen3-max")
                        max_iters = skill_config.get("maxIters", 30)
                        sys_prompt = skill_config.get("systemPrompt", "")
                        
                        if skills:
                            skill_agent = create_agent_by_skills(
                                name=node_label,
                                skill_names=skills,
                                sys_prompt=sys_prompt if sys_prompt else None,
                                api_key=api_key,
                                model_name=model,
                                max_iters=max_iters,
                            )
                            
                            yield f"data: {json.dumps({'type': 'log', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'使用技能: {chr(44).join(skills)}'})}\n\n"
                            
                            response = await skill_agent(Msg("user", input_data, "user"))
                            result = response.content if hasattr(response, "content") else str(response)
                            if isinstance(result, list):
                                result = result[0].get("text", str(result[0])) if result else ""
                            output = str(result)
                        else:
                            output = input_data
                            yield f"data: {json.dumps({'type': 'log', 'nodeId': node_id, 'nodeLabel': node_label, 'message': '警告: 未配置技能'})}\n\n"
                    
                    elif node_type == "parallel":
                        context["parallel_mode"] = True
                        output = input_data
                    
                    elif node_type == "tool":
                        # 执行工具节点
                        tool_config = node.get("data", {}).get("toolConfig", {})
                        tool_type = tool_config.get("toolType", "")
                        tool_params = tool_config.get("params", {})
                        
                        yield f"data: {json.dumps({'type': 'log', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'执行工具: {tool_type}'})}\n\n"
                        
                        # 构建上下文变量
                        tool_context = {
                            "input": input_data,
                            "content": input_data,
                            "output": input_data,
                        }
                        
                        result = tool_executor.execute(tool_type, tool_params, tool_context)
                        
                        if result.get("success"):
                            output = json.dumps(result, ensure_ascii=False)
                            tool_msg = result.get("message", "")
                            yield f"data: {json.dumps({'type': 'log', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'工具执行成功: {tool_msg}'})}\n\n"
                        else:
                            error_msg = result.get("error", "工具执行失败")
                            yield f"data: {json.dumps({'type': 'log', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'工具执行失败: {error_msg}'})}\n\n"
                            output = f"工具执行失败: {error_msg}"
                    
                    yield f"data: {json.dumps({'type': 'node_complete', 'nodeId': node_id, 'nodeLabel': node_label})}\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'node_error', 'nodeId': node_id, 'nodeLabel': node_label, 'error': str(e)})}\n\n"
                
                node_outputs[node_id] = output
                
                next_nodes = graph.get(node_id, [])
                
                if not next_nodes:
                    return
                
                if node_type == "condition":
                    condition_result = context.get("condition_result", True)
                    target_handle = "true" if condition_result else "false"
                    next_input = context.get("original_input", output)
                    
                    for next_node in next_nodes:
                        if next_node["handle"] == target_handle:
                            async for event in execute_from_node(next_node["target"], next_input):
                                yield event
                            return
                    
                    if next_nodes:
                        async for event in execute_from_node(next_nodes[0]["target"], next_input):
                            yield event
                
                elif node_type == "classifier":
                    classifier_result = context.get("classifier_result")
                    next_input = context.get("original_input", output)
                    
                    print(f"[Debug] 分类器结果: {classifier_result}")
                    print(f"[Debug] 下一节点列表: {next_nodes}")
                    
                    matched = False
                    for next_node in next_nodes:
                        print(f"[Debug] 检查边: handle={next_node['handle']}, target={next_node['target']}")
                        if next_node["handle"] == classifier_result:
                            print(f"[Debug] 匹配成功，执行节点: {next_node['target']}")
                            async for event in execute_from_node(next_node["target"], next_input):
                                yield event
                            matched = True
                            break
                    
                    if not matched and next_nodes:
                        print(f"[Debug] 未匹配，执行默认节点: {next_nodes[0]['target']}")
                        async for event in execute_from_node(next_nodes[0]["target"], next_input):
                            yield event
                
                elif node_type == "parallel" or context.get("parallel_mode"):
                    yield f"data: {json.dumps({'type': 'parallel_start', 'nodeId': node_id, 'nodeLabel': node_label, 'branchCount': len(next_nodes)})}\n\n"
                    
                    tasks = []
                    for next_node in next_nodes:
                        async def execute_branch(target_id):
                            results = []
                            async for event in execute_from_node(target_id, output):
                                results.append(event)
                            return results
                        tasks.append(execute_branch(next_node["target"]))
                    
                    all_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for results in all_results:
                        if isinstance(results, list):
                            for event in results:
                                yield event
                
                else:
                    for next_node in next_nodes:
                        async for event in execute_from_node(next_node["target"], output):
                            yield event
            
            for start_node in start_nodes:
                async for event in execute_from_node(start_node["id"], user_input):
                    yield event
            
            yield f"data: {json.dumps({'type': 'log', 'message': '工作流执行完成'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'log', 'message': f'执行失败: {str(e)}'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def run_predefined_workflow_internal(
    workflow_name: str,
    user_input: str,
    history_messages: list = None
) -> dict:
    """内部调用工作流执行（非流式，用于邮件触发等场景）
    
    Args:
        workflow_name: 工作流名称
        user_input: 用户输入
        history_messages: 历史消息列表
        
    Returns:
        执行结果字典
    """
    from api.services.context_builder import build_context_prompt
    
    if workflow_name not in predefined_workflows:
        return {"success": False, "error": f"工作流 '{workflow_name}' 不存在"}
    
    workflow = predefined_workflows[workflow_name]
    api_key = AgentManager.get_api_key()
    
    try:
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        # 构建上下文
        history = history_messages or []
        context_prompt = build_context_prompt(history)
        
        # 创建智能体
        agent_nodes = [n for n in nodes if n["type"] == "agent"]
        skill_agent_nodes = [n for n in nodes if n["type"] == "skill-agent"]
        simple_agent_nodes = [n for n in nodes if n["type"] == "simple-agent"]
        
        agents = {}
        
        for node in agent_nodes:
            config = node["data"].get("agentConfig", {})
            if config:
                agent = AgentManager.create_from_config(config, api_key)
                agents[node["id"]] = agent
        
        for node in skill_agent_nodes:
            config = node["data"].get("skillAgentConfig", {})
            skills = config.get("skills", [])
            if skills:
                agent = create_agent_by_skills(
                    name=config.get("name", "SkillAgent"),
                    skill_names=skills,
                    sys_prompt=config.get("systemPrompt", ""),
                    api_key=api_key,
                    model_name=config.get("model", "qwen3-max"),
                    max_iters=config.get("maxIters", 30)
                )
                agents[node["id"]] = agent
        
        for node in simple_agent_nodes:
            config = node["data"].get("simpleAgentConfig", {})
            from agents.simple import SimpleAgent
            agent = SimpleAgent(
                name=config.get("name", "SimpleAgent"),
                sys_prompt=config.get("systemPrompt", ""),
                api_key=api_key,
                model_name=config.get("model", "qwen3-max"),
            )
            agents[node["id"]] = agent
        
        # 获取执行顺序
        execution_order = get_execution_order(nodes, edges)
        
        current_input = context_prompt + user_input if context_prompt else user_input
        full_input_with_history = current_input
        final_output = ""
        executed_branch_nodes = set()
        skipped_branch_nodes = set()
        
        # 收集分类器的所有分支目标节点
        classifier_nodes = [n for n in nodes if n.get("type") == "classifier"]
        for classifier_node in classifier_nodes:
            classifier_id = classifier_node["id"]
            for edge in edges:
                if edge.get("source") == classifier_id and edge.get("sourceHandle"):
                    target_id = edge.get("target")
                    if target_id:
                        skipped_branch_nodes.add(target_id)
        
        # 执行工作流
        for node_id in execution_order:
            if node_id in executed_branch_nodes:
                continue
            
            # 跳过未被分类器选中的分支节点
            if node_id in skipped_branch_nodes:
                continue
            
            node = next((n for n in nodes if n["id"] == node_id), None)
            if not node:
                continue
            
            node_type = node.get("type")
            node_label = node.get("data", {}).get("label", node_id)
            
            if node_type == "input":
                current_input = user_input
                print(f"[Internal Workflow] 输入节点: {node_label}")
            
            elif node_type in ["agent", "skill-agent", "simple-agent"] and node_id in agents:
                agent = agents[node_id]
                print(f"[Internal Workflow] 执行节点: {node_label}")
                
                agent_input = full_input_with_history
                response = await agent(Msg("user", agent_input, "user"))
                
                output = response.content if hasattr(response, "content") else str(response)
                if isinstance(output, list):
                    text_parts = [item.get("text", "") for item in output if isinstance(item, dict) and "text" in item]
                    output = "\n".join(text_parts) if text_parts else str(output)
                
                current_input = output
                final_output = output
                print(f"[Internal Workflow] 节点 {node_label} 输出: {output[:100] if output else 'empty'}...")
            
            elif node_type == "tool":
                # 执行工具节点
                tool_config = node.get("data", {}).get("toolConfig", {})
                tool_type = tool_config.get("toolType", "")
                tool_params = tool_config.get("params", {})
                
                print(f"[Internal Workflow] 执行工具节点: {node_label}, 类型: {tool_type}")
                
                # 构建上下文变量，包括上游节点输出
                context = {
                    "input": current_input,
                    "content": current_input,
                    "output": final_output,
                }
                
                # 执行工具
                result = tool_executor.execute(tool_type, tool_params, context)
                
                if result.get("success"):
                    output = json.dumps(result, ensure_ascii=False)
                    current_input = output
                    final_output = output
                    print(f"[Internal Workflow] 工具执行成功: {result.get('message', '')}")
                else:
                    error_msg = result.get("error", "工具执行失败")
                    print(f"[Internal Workflow] 工具执行失败: {error_msg}")
                    final_output = f"工具执行失败: {error_msg}"
            
            elif node_type == "classifier":
                classifier_config = node.get("data", {}).get("classifierConfig", {})
                categories = classifier_config.get("categories", [])
                model = classifier_config.get("model", "qwen3-max")
                
                classifier = ClassifierService(api_key=api_key, default_model=model)
                result = await classifier.classify(current_input, categories)
                matched_category = result.get("id") if result else None
                
                print(f"[Internal Workflow] 分类结果: {matched_category}")
                
                # 查找匹配的分支并执行
                for edge in edges:
                    if edge.get("source") == node_id and edge.get("sourceHandle") == matched_category:
                        target_node_id = edge.get("target")
                        target_node = next((n for n in nodes if n["id"] == target_node_id), None)
                        
                        if target_node and target_node_id in agents:
                            # 从跳过集合中移除，标记为已执行
                            skipped_branch_nodes.discard(target_node_id)
                            executed_branch_nodes.add(target_node_id)
                            
                            agent = agents[target_node_id]
                            target_label = target_node.get("data", {}).get("label", target_node_id)
                            print(f"[Internal Workflow] 执行分支节点: {target_label}")
                            
                            response = await agent(Msg("user", full_input_with_history, "user"))
                            output = response.content if hasattr(response, "content") else str(response)
                            
                            if isinstance(output, list):
                                text_parts = [item.get("text", "") for item in output if isinstance(item, dict) and "text" in item]
                                output = "\n".join(text_parts) if text_parts else str(output)
                            
                            current_input = output
                            final_output = output
                            print(f"[Internal Workflow] 分支节点 {target_label} 输出: {output[:100] if output else 'empty'}...")
                        break
            
            elif node_type == "output":
                print(f"[Internal Workflow] 输出节点: {node_label}")
        
        return {
            "success": True,
            "workflow_name": workflow_name,
            "output": final_output
        }
    
    except Exception as e:
        print(f"[Internal Workflow] 执行失败: {e}")
        return {
            "success": False,
            "workflow_name": workflow_name,
            "error": str(e)
        }
