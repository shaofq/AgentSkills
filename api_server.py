# -*- coding: utf-8 -*-
"""
智能体编排系统 API 服务

提供 RESTful API 用于：
1. 工作流管理（CRUD）
2. 工作流执行
3. 智能体和技能查询
"""
import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agentscope.message import Msg
from agents.base import BaseAgent, get_available_skills, create_agent_by_skills
from agents.simple import SimpleAgent
from agents.router import RouterAgent
from agents.policy_qa_agent import PolicyQAAgent
from agents.code_agent import CodeAgent
from agents.pptx_agent import PPTXAgent
from agents.ocr_agent import OCRAgent
from agents.skill_creator_agent import SkillCreatorAgent

app = FastAPI(title="智能体编排系统 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-547e87e8934f4737b972199090958ff2")

workflows_db: Dict[str, dict] = {}
executions_db: Dict[str, dict] = {}
predefined_workflows: Dict[str, dict] = {}
menu_bindings_config: dict = {}  # 存储完整配置（支持分组格式）

def load_menu_bindings():
    """加载菜单绑定配置"""
    global menu_bindings_config
    config_path = "./config/menu_bindings.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                menu_bindings_config = json.load(f)
                # 统计菜单项数量
                if "menuGroups" in menu_bindings_config:
                    total = sum(len(g.get("menus", [])) for g in menu_bindings_config.get("menuGroups", []))
                    print(f"[MenuBindings] 加载菜单绑定配置(分组格式): {total} 个菜单项")
                elif "menus" in menu_bindings_config:
                    print(f"[MenuBindings] 加载菜单绑定配置: {len(menu_bindings_config.get('menus', []))} 个菜单项")
        except Exception as e:
            print(f"[MenuBindings] 加载菜单绑定配置失败: {e}")
    else:
        print(f"[MenuBindings] 配置文件不存在: {config_path}")

def load_predefined_workflows():
    """加载预定义工作流"""
    workflow_dir = "./workflows"
    if os.path.exists(workflow_dir):
        for filename in os.listdir(workflow_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(workflow_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                        workflow_name = filename.replace('.json', '')
                        predefined_workflows[workflow_name] = workflow
                        print(f"[Workflow] 加载预定义工作流: {workflow_name}")
                except Exception as e:
                    print(f"[Workflow] 加载工作流失败 {filename}: {e}")

load_predefined_workflows()
load_menu_bindings()

# 验证工作流是否加载成功
print(f"[Startup] 工作流加载完成，共 {len(predefined_workflows)} 个: {list(predefined_workflows.keys())}")


def create_agent_from_config(config: dict, api_key: str):
    """根据配置创建 Agent 实例"""
    agent_type = config.get("type", "custom")
    agent_id = config.get("id", "")
    
    # 使用预定义的 Agent 类
    if agent_type == "code" or agent_id == "code_agent":
        return CodeAgent(
            api_key=api_key,
            model_name=config.get("model", "qwen3-max"),
            max_iters=config.get("maxIters", 30),
        )
    elif agent_type == "pptx" or agent_id == "pptx_agent":
        return PPTXAgent(
            api_key=api_key,
            model_name=config.get("model", "qwen3-max"),
            max_iters=config.get("maxIters", 30),
        )
    elif agent_type == "policy" or agent_id == "policy_qa_agent":
        return PolicyQAAgent(
            api_key=api_key,
            model_name=config.get("model", "qwen3-max"),
            max_iters=config.get("maxIters", 10),
        )
    elif agent_type == "router" or agent_id == "router":
        # 在工作流中，router 类型的节点应该作为普通的分析智能体
        # 而不是实际进行路由（因为工作流已经定义了执行顺序）
        return SimpleAgent(
            name=config.get("name", "Router"),
            sys_prompt=config.get("systemPrompt", "你是一个智能路由助手，负责分析用户请求并提供建议。"),
            api_key=api_key,
            model_name=config.get("model", "qwen3-max"),
        )
    else:
        # 自定义 Agent，使用 BaseAgent
        skill_paths = [f"./skill/{s}" for s in config.get("skills", [])]
        return BaseAgent(
            name=config.get("name", agent_id),
            sys_prompt=config.get("systemPrompt", ""),
            skills=skill_paths,
            api_key=api_key,
            model_name=config.get("model", "qwen3-max"),
            max_iters=config.get("maxIters", 30),
        )


class AgentConfig(BaseModel):
    id: str
    name: str
    type: str
    description: str
    systemPrompt: str
    skills: List[str]
    model: str = "qwen3-max"
    maxIters: int = 30


class WorkflowNode(BaseModel):
    id: str
    type: str
    position: dict
    data: dict


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class Workflow(BaseModel):
    id: Optional[str] = None
    name: str
    description: str = ""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class ExecuteRequest(BaseModel):
    input: str


class ExecutionResult(BaseModel):
    nodeId: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None


class WorkflowExecution(BaseModel):
    id: str
    workflowId: str
    status: str
    input: str
    results: List[ExecutionResult]
    startTime: str
    endTime: Optional[str] = None


@app.get("/api/agents", response_model=List[AgentConfig])
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




@app.get("/api/workflows", response_model=List[Workflow])
async def get_workflows():
    """获取所有工作流"""
    return list(workflows_db.values())


@app.get("/api/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str):
    """获取单个工作流"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflows_db[workflow_id]


@app.post("/api/workflows", response_model=Workflow)
async def create_workflow(workflow: Workflow):
    """创建工作流"""
    workflow.id = workflow.id or str(uuid.uuid4())
    workflow.createdAt = workflow.createdAt or datetime.now().isoformat()
    workflow.updatedAt = datetime.now().isoformat()
    workflows_db[workflow.id] = workflow.dict()
    return workflow


@app.put("/api/workflows/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, workflow: Workflow):
    """更新工作流"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="工作流不存在")
    workflow.id = workflow_id
    workflow.updatedAt = datetime.now().isoformat()
    workflows_db[workflow_id] = workflow.dict()
    return workflow


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """删除工作流"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="工作流不存在")
    del workflows_db[workflow_id]
    return {"message": "删除成功"}


@app.post("/api/workflows/{workflow_id}/execute", response_model=WorkflowExecution)
async def execute_workflow(workflow_id: str, request: ExecuteRequest):
    """执行工作流"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    workflow = workflows_db[workflow_id]
    execution_id = str(uuid.uuid4())
    
    execution = WorkflowExecution(
        id=execution_id,
        workflowId=workflow_id,
        status="running",
        input=request.input,
        results=[],
        startTime=datetime.now().isoformat(),
    )
    executions_db[execution_id] = execution.dict()
    
    asyncio.create_task(_run_workflow(execution_id, workflow, request.input))
    
    return execution


async def _run_workflow(execution_id: str, workflow: dict, user_input: str):
    """异步执行工作流"""
    try:
        nodes = workflow["nodes"]
        edges = workflow["edges"]
        results = []
        
        agent_nodes = [n for n in nodes if n["type"] == "agent"]
        
        agents = {}
        for node in agent_nodes:
            config = node["data"].get("agentConfig", {})
            if config:
                # 使用工厂函数创建 Agent
                agent = create_agent_from_config(config, API_KEY)
                agents[node["id"]] = agent
        
        execution_order = _get_execution_order(nodes, edges)
        
        current_input = user_input
        for node_id in execution_order:
            node = next((n for n in nodes if n["id"] == node_id), None)
            if not node:
                continue
            
            result = ExecutionResult(nodeId=node_id, status="running")
            
            try:
                if node["type"] == "agent" and node_id in agents:
                    agent = agents[node_id]
                    response = await agent(Msg("user", current_input, "user"))
                    result.output = response.content if hasattr(response, "content") else str(response)
                    result.status = "success"
                    current_input = result.output
                elif node["type"] == "input":
                    result.output = user_input
                    result.status = "success"
                elif node["type"] == "output":
                    result.output = current_input
                    result.status = "success"
                else:
                    result.status = "skipped"
            except Exception as e:
                result.status = "error"
                result.error = str(e)
            
            results.append(result.dict())
        
        executions_db[execution_id]["results"] = results
        executions_db[execution_id]["status"] = "completed"
        executions_db[execution_id]["endTime"] = datetime.now().isoformat()
        
    except Exception as e:
        executions_db[execution_id]["status"] = "failed"
        executions_db[execution_id]["endTime"] = datetime.now().isoformat()
        executions_db[execution_id]["results"].append({
            "nodeId": "system",
            "status": "error",
            "error": str(e),
        })


def _get_execution_order(nodes: List[dict], edges: List[dict]) -> List[str]:
    """根据边计算节点执行顺序（拓扑排序）"""
    in_degree = {n["id"]: 0 for n in nodes}
    adj = {n["id"]: [] for n in nodes}
    
    for edge in edges:
        adj[edge["source"]].append(edge["target"])
        in_degree[edge["target"]] += 1
    
    queue = [n for n in in_degree if in_degree[n] == 0]
    order = []
    
    while queue:
        node = queue.pop(0)
        order.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return order


@app.get("/api/executions/{execution_id}", response_model=WorkflowExecution)
async def get_execution(execution_id: str):
    """获取执行状态"""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return executions_db[execution_id]


class PredefinedWorkflowRequest(BaseModel):
    workflow_name: str
    input: str
    history: List[dict] = []  # 对话历史，用于上下文管理


@app.get("/api/menu-bindings")
async def get_menu_bindings():
    """获取菜单绑定配置"""
    return menu_bindings_config


@app.get("/api/skills")
async def get_skills():
    """获取所有可用的技能列表"""
    skills = get_available_skills()
    return {"skills": skills, "total": len(skills)}


class MenuBindingUpdate(BaseModel):
    menuId: str
    workflowName: Optional[str] = None


@app.post("/api/menu-bindings")
async def update_menu_binding(request: MenuBindingUpdate):
    """更新菜单绑定的工作流"""
    global menu_bindings_config
    
    # 支持分组格式
    all_menus = []
    if "menuGroups" in menu_bindings_config:
        for group in menu_bindings_config.get("menuGroups", []):
            all_menus.extend(group.get("menus", []))
    else:
        all_menus = menu_bindings_config.get("menus", [])
    
    for menu in all_menus:
        if menu.get("id") == request.menuId:
            menu["workflowName"] = request.workflowName
            # 保存到配置文件
            config_path = "./config/menu_bindings.json"
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(menu_bindings_config, f, ensure_ascii=False, indent=2)
                print(f"[MenuBindings] 更新菜单 {request.menuId} 绑定工作流: {request.workflowName}")
                return {"success": True, "message": "更新成功"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")
    
    raise HTTPException(status_code=404, detail=f"菜单 {request.menuId} 不存在")


@app.get("/api/workflows/debug")
async def debug_workflows():
    """调试：查看 predefined_workflows 的原始内容"""
    return {
        "keys": list(predefined_workflows.keys()),
        "count": len(predefined_workflows),
        "raw": predefined_workflows
    }


@app.get("/api/workflowsquery")
async def get_workflows_query():
    """获取所有已加载的预定义工作流列表，包含绑定的菜单信息"""
    print(f"\n[API /api/workflowsquery] 被调用")
    workflows = []
    
    # 获取所有菜单项（支持分组格式）
    all_menus = []
    if "menuGroups" in menu_bindings_config:
        for group in menu_bindings_config.get("menuGroups", []):
            all_menus.extend(group.get("menus", []))
    else:
        all_menus = menu_bindings_config.get("menus", [])
    
    # 构建工作流名称到菜单的映射
    workflow_to_menus = {}
    for menu in all_menus:
        wf_name = menu.get("workflowName")
        if wf_name:
            if wf_name not in workflow_to_menus:
                workflow_to_menus[wf_name] = []
            workflow_to_menus[wf_name].append({
                "id": menu.get("id"),
                "name": menu.get("name"),
                "icon": menu.get("icon")
            })
    
    for workflow_name, workflow in predefined_workflows.items():
        bound_menus = workflow_to_menus.get(workflow_name, [])
        workflow_info = {
            "name": workflow_name,
            "title": workflow.get("name", workflow_name),
            "description": workflow.get("description", ""),
            "nodeCount": len(workflow.get("nodes", [])),
            "edgeCount": len(workflow.get("edges", [])),
            "boundMenus": bound_menus
        }
        workflows.append(workflow_info)
    
    print(f"[API] 返回 {len(workflows)} 个工作流")
    return {"workflows": workflows, "total": len(workflows)}


@app.post("/api/workflow/run")
async def run_predefined_workflow(request: PredefinedWorkflowRequest):
    """执行预定义工作流（同步返回最终结果）"""
    workflow_name = request.workflow_name
    user_input = request.input
    history = request.history or []
    
    if workflow_name not in predefined_workflows:
        raise HTTPException(status_code=404, detail=f"预定义工作流 '{workflow_name}' 不存在")
    
    workflow = predefined_workflows[workflow_name]
    
    try:
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        # 构建上下文提示
        context_prompt = ""
        if history:
            context_prompt = "以下是之前的对话历史，请参考上下文理解用户需求：\n\n"
            for msg in history[-10:]:  # 只保留最近10条消息
                role = "用户" if msg.get("role") == "user" else "助手"
                content = msg.get("content", "")[:500]  # 限制每条消息长度
                context_prompt += f"{role}: {content}\n\n"
            context_prompt += "---\n\n当前用户需求: "
        
        agent_nodes = [n for n in nodes if n["type"] == "agent"]
        agents = {}
        
        for node in agent_nodes:
            config = node["data"].get("agentConfig", {})
            if config:
                # 使用工厂函数创建 Agent，优先使用预定义的 Agent 类
                agent = create_agent_from_config(config, API_KEY)
                agents[node["id"]] = agent
                print(f"[Workflow] 创建智能体: {node['id']} -> {agent.__class__.__name__}")
        
        execution_order = _get_execution_order(nodes, edges)
        
        # 第一个节点使用带上下文的输入
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
                # 只有第一个智能体节点使用带上下文的输入
                agent_input = current_input if is_first_agent else current_input
                response = await agent(Msg("user", agent_input, "user"))
                output = response.content if hasattr(response, "content") else str(response)
                print(f"[Workflow] 节点 {node_id} 输出: {output[:100] if output else 'empty'}...")
                current_input = output
                final_output = output
                is_first_agent = False
            elif node["type"] == "classifier":
                # 分类器节点：使用 LLM 分析输入并选择分类
                classifier_config = node["data"].get("classifierConfig", {})
                categories = classifier_config.get("categories", [])
                model = classifier_config.get("model", "qwen3-max")
                
                if categories:
                    # 构建分类提示词
                    category_list = "\n".join([f"{i+1}. {cat['name']}: {cat['description']}" for i, cat in enumerate(categories)])
                    classify_prompt = f"""请分析以下用户输入，并从给定的分类中选择最匹配的一个。

用户输入：{current_input}

可选分类：
{category_list}

请只返回最匹配的分类名称，不要返回其他内容。"""
                    
                    # 使用 LLM 进行分类
                    from agents.base import BaseAgent
                    classifier_agent = BaseAgent(
                        name="Classifier",
                        sys_prompt="你是一个分类助手，根据用户输入选择最匹配的分类。只返回分类名称，不要返回其他内容。",
                        api_key=API_KEY,
                        model_name=model,
                        max_iters=1,
                    )
                    response = await classifier_agent(Msg("user", classify_prompt, "user"))
                    result = response.content if hasattr(response, "content") else str(response)
                    result = result.strip()
                    
                    # 匹配分类
                    matched_category = None
                    for cat in categories:
                        if cat["name"] in result or result in cat["name"]:
                            matched_category = cat
                            break
                    
                    if not matched_category and categories:
                        matched_category = categories[0]  # 默认第一个分类
                    
                    print(f"[Workflow] 分类器结果: {result} -> 匹配分类: {matched_category['name'] if matched_category else 'None'}")
                    
                    # TODO: 根据分类结果路由到不同的下游节点
                    # 当前简化处理：继续执行
            elif node["type"] == "input":
                current_input = user_input
            elif node["type"] == "output":
                final_output = current_input
        
        return final_output
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/workflow/run/stream")
async def run_predefined_workflow_stream(request: PredefinedWorkflowRequest):
    """执行预定义工作流（流式返回思考过程和结果）"""
    async def event_generator():
        try:
            workflow_name = request.workflow_name
            user_input = request.input
            history = request.history or []
            
            if workflow_name not in predefined_workflows:
                yield f"data: {json.dumps({'type': 'error', 'message': f'工作流 {workflow_name} 不存在'})}\n\n"
                return
            
            workflow = predefined_workflows[workflow_name]
            nodes = workflow.get("nodes", [])
            edges = workflow.get("edges", [])
            
            yield f"data: {json.dumps({'type': 'thinking', 'message': '正在分析需求...'})}\n\n"
            
            # 构建上下文提示
            context_prompt = ""
            if history:
                yield f"data: {json.dumps({'type': 'thinking', 'message': f'加载对话历史 ({len(history)} 条消息)...'})}\n\n"
                context_prompt = "以下是之前的对话历史，请参考上下文理解用户需求：\n\n"
                for msg in history[-10:]:
                    role = "用户" if msg.get("role") == "user" else "助手"
                    content = msg.get("content", "")[:500]
                    context_prompt += f"{role}: {content}\n\n"
                context_prompt += "---\n\n当前用户需求: "
            
            # 创建智能体
            agent_nodes = [n for n in nodes if n["type"] == "agent"]
            skill_agent_nodes = [n for n in nodes if n["type"] == "skill-agent"]
            agents = {}
            
            for node in agent_nodes:
                config = node["data"].get("agentConfig", {})
                if config:
                    agent_name = config.get("name", node["id"])
                    yield f"data: {json.dumps({'type': 'thinking', 'message': f'初始化智能体: {agent_name}'})}\n\n"
                    agent = create_agent_from_config(config, API_KEY)
                    agents[node["id"]] = agent
            
            for node in skill_agent_nodes:
                skill_config = node["data"].get("skillAgentConfig", {})
                skills = skill_config.get("skills", [])
                if skills:
                    skill_names = ", ".join(skills)
                    yield f"data: {json.dumps({'type': 'thinking', 'message': f'初始化技能智能体: {skill_names}'})}\n\n"
                    model = skill_config.get("model", "qwen3-max")
                    max_iters = skill_config.get("maxIters", 30)
                    sys_prompt = skill_config.get("systemPrompt", "")
                    agent = create_agent_by_skills(
                        name=f"SkillAgent_{node['id']}",
                        skill_names=skills,
                        sys_prompt=sys_prompt,
                        api_key=API_KEY,
                        model_name=model,
                        max_iters=max_iters,
                    )
                    agents[node["id"]] = agent
            
            execution_order = _get_execution_order(nodes, edges)
            yield f"data: {json.dumps({'type': 'thinking', 'message': f'执行顺序: {len(execution_order)} 个节点'})}\n\n"
            
            current_input = context_prompt + user_input if context_prompt else user_input
            final_output = ""
            is_first_agent = True
            
            for node_id in execution_order:
                node = next((n for n in nodes if n["id"] == node_id), None)
                if not node:
                    continue
                
                node_type = node.get("type")
                node_label = node.get("data", {}).get("label", node_id)
                
                if node_type in ["agent", "skill-agent"] and node_id in agents:
                    yield f"data: {json.dumps({'type': 'node_start', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'正在执行: {node_label}'})}\n\n"
                    
                    agent = agents[node_id]
                    agent_input = current_input
                    
                    yield f"data: {json.dumps({'type': 'thinking', 'message': '智能体正在思考...'})}\n\n"
                    
                    response = await agent(Msg("user", agent_input, "user"))
                    output = response.content if hasattr(response, "content") else str(response)
                    
                    # 处理返回值可能是列表的情况
                    if isinstance(output, list):
                        output = output[0].get("text", str(output[0])) if output else ""
                    
                    yield f"data: {json.dumps({'type': 'node_complete', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'{node_label} 执行完成'})}\n\n"
                    
                    current_input = str(output)
                    final_output = str(output)
                    is_first_agent = False
                    
                elif node_type == "classifier":
                    yield f"data: {json.dumps({'type': 'node_start', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'正在分类: {node_label}'})}\n\n"
                    
                    classifier_config = node["data"].get("classifierConfig", {})
                    categories = classifier_config.get("categories", [])
                    model = classifier_config.get("model", "qwen3-max")
                    
                    if categories:
                        category_list = "\n".join([f"{i+1}. {cat['name']}: {cat['description']}" for i, cat in enumerate(categories)])
                        classify_prompt = f"""请分析以下用户输入，并从给定的分类中选择最匹配的一个。

用户输入：{current_input}

可选分类：
{category_list}

请只返回最匹配的分类名称，不要返回其他内容。"""
                        
                        from agents.base import BaseAgent
                        classifier_agent = BaseAgent(
                            name="Classifier",
                            sys_prompt="你是一个分类助手，根据用户输入选择最匹配的分类。只返回分类名称，不要返回其他内容。",
                            api_key=API_KEY,
                            model_name=model,
                            max_iters=1,
                        )
                        
                        yield f"data: {json.dumps({'type': 'thinking', 'message': '正在分析分类...'})}\n\n"
                        
                        response = await classifier_agent(Msg("user", classify_prompt, "user"))
                        result = response.content if hasattr(response, "content") else str(response)
                        result = str(result).strip()
                        
                        matched_category = None
                        for cat in categories:
                            if cat["name"] in result or result in cat["name"]:
                                matched_category = cat
                                break
                        
                        if not matched_category and categories:
                            matched_category = categories[0]
                        
                        yield f"data: {json.dumps({'type': 'classifier_result', 'nodeId': node_id, 'nodeLabel': node_label, 'result': matched_category['name'] if matched_category else 'None'})}\n\n"
                
                elif node_type == "input":
                    current_input = context_prompt + user_input if context_prompt else user_input
                    
                elif node_type == "output":
                    final_output = current_input
            
            # 发送最终结果
            yield f"data: {json.dumps({'type': 'content', 'content': final_output})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


class WorkflowTestRequest(BaseModel):
    workflow: dict
    input: str


@app.post("/api/workflow/test")
async def test_workflow(request: WorkflowTestRequest):
    """测试工作流（流式返回执行过程）"""
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
                    
                    # 使用工厂函数创建 Agent
                    agent = create_agent_from_config(config, API_KEY)
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
            context = {"original_input": user_input}  # 保存原始用户输入
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
                
                # 发送节点开始事件
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
                            # 确保 input_data 是字符串
                            input_str = str(input_data) if not isinstance(input_data, str) else input_data
                            result = condition_expr.lower() in input_str.lower()
                        else:
                            result = True
                        
                        context["condition_result"] = result
                        yield f"data: {json.dumps({'type': 'condition_result', 'nodeId': node_id, 'nodeLabel': node_label, 'result': result, 'expression': condition_expr})}\n\n"
                        output = input_data
                        
                    elif node_type == "classifier":
                        # 分类器节点：使用 LLM 分析输入并选择分类
                        classifier_config = node.get("data", {}).get("classifierConfig", {})
                        categories = classifier_config.get("categories", [])
                        model = classifier_config.get("model", "qwen3-max")
                        
                        if categories:
                            # 构建分类提示词
                            category_list = "\n".join([f"{i+1}. {cat['name']}: {cat['description']}" for i, cat in enumerate(categories)])
                            classify_prompt = f"""请分析以下用户输入，并从给定的分类中选择最匹配的一个。

用户输入：{input_data}

可选分类：
{category_list}

请只返回最匹配的分类名称，不要返回其他内容。"""
                            
                            # 使用 LLM 进行分类
                            from agents.base import BaseAgent
                            classifier_agent = BaseAgent(
                                name="Classifier",
                                sys_prompt="你是一个分类助手，根据用户输入选择最匹配的分类。只返回分类名称，不要返回其他内容。",
                                api_key=API_KEY,
                                model_name=model,
                                max_iters=1,
                            )
                            response = await classifier_agent(Msg("user", classify_prompt, "user"))
                            result = response.content if hasattr(response, "content") else str(response)
                            # 处理返回值可能是列表的情况
                            if isinstance(result, list):
                                result = result[0].get("text", str(result[0])) if result else ""
                            result = str(result).strip()
                            
                            # 匹配分类
                            matched_category = None
                            for cat in categories:
                                if cat["name"] in result or result in cat["name"]:
                                    matched_category = cat
                                    break
                            
                            if not matched_category and categories:
                                matched_category = categories[0]  # 默认第一个分类
                            
                            context["classifier_result"] = matched_category["id"] if matched_category else None
                            context["classifier_category_name"] = matched_category["name"] if matched_category else None
                            
                            yield f"data: {json.dumps({'type': 'classifier_result', 'nodeId': node_id, 'nodeLabel': node_label, 'result': matched_category['name'] if matched_category else 'None', 'input': input_data[:100]})}\n\n"
                        
                        output = input_data
                    
                    elif node_type == "skill-agent":
                        # 技能智能体节点：根据配置的技能动态创建智能体
                        skill_config = node.get("data", {}).get("skillAgentConfig", {})
                        skills = skill_config.get("skills", [])
                        model = skill_config.get("model", "qwen3-max")
                        max_iters = skill_config.get("maxIters", 30)
                        sys_prompt = skill_config.get("systemPrompt", "")
                        
                        if skills:
                            # 使用工厂函数创建智能体
                            skill_agent = create_agent_by_skills(
                                name=node_label,
                                skill_names=skills,
                                sys_prompt=sys_prompt if sys_prompt else None,
                                api_key=API_KEY,
                                model_name=model,
                                max_iters=max_iters,
                            )
                            
                            yield f"data: {json.dumps({'type': 'log', 'nodeId': node_id, 'nodeLabel': node_label, 'message': f'使用技能: {", ".join(skills)}'})}\n\n"
                            
                            response = await skill_agent(Msg("user", input_data, "user"))
                            result = response.content if hasattr(response, "content") else str(response)
                            # 处理返回值可能是列表的情况
                            if isinstance(result, list):
                                result = result[0].get("text", str(result[0])) if result else ""
                            output = str(result)
                        else:
                            output = input_data
                            yield f"data: {json.dumps({'type': 'log', 'nodeId': node_id, 'nodeLabel': node_label, 'message': '警告: 未配置技能'})}\n\n"
                    
                    elif node_type == "parallel":
                        context["parallel_mode"] = True
                        output = input_data
                    
                    # 发送节点完成事件
                    yield f"data: {json.dumps({'type': 'node_complete', 'nodeId': node_id, 'nodeLabel': node_label})}\n\n"
                    
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'node_error', 'nodeId': node_id, 'nodeLabel': node_label, 'error': str(e)})}\n\n"
                
                node_outputs[node_id] = output
                
                # 获取下游节点
                next_nodes = graph.get(node_id, [])
                
                if not next_nodes:
                    return
                
                # 处理条件分支
                if node_type == "condition":
                    condition_result = context.get("condition_result", True)
                    target_handle = "true" if condition_result else "false"
                    
                    # 条件分支后传递原始用户输入，而不是条件节点的输出
                    next_input = context.get("original_input", output)
                    
                    for next_node in next_nodes:
                        if next_node["handle"] == target_handle:
                            async for event in execute_from_node(next_node["target"], next_input):
                                yield event
                            return
                    
                    if next_nodes:
                        async for event in execute_from_node(next_nodes[0]["target"], next_input):
                            yield event
                
                # 处理分类器分支路由
                elif node_type == "classifier":
                    classifier_result = context.get("classifier_result")
                    next_input = context.get("original_input", output)
                    
                    # 根据分类结果选择对应的下游分支
                    matched = False
                    for next_node in next_nodes:
                        if next_node["handle"] == classifier_result:
                            async for event in execute_from_node(next_node["target"], next_input):
                                yield event
                            matched = True
                            break
                    
                    # 如果没有匹配到，执行第一个分支作为默认
                    if not matched and next_nodes:
                        async for event in execute_from_node(next_nodes[0]["target"], next_input):
                            yield event
                
                # 处理并行执行
                elif node_type == "parallel" or context.get("parallel_mode"):
                    yield f"data: {json.dumps({'type': 'parallel_start', 'nodeId': node_id, 'nodeLabel': node_label, 'branchCount': len(next_nodes)})}\n\n"
                    
                    # 并行执行所有分支
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
                
                # 串行执行
                else:
                    for next_node in next_nodes:
                        async for event in execute_from_node(next_node["target"], output):
                            yield event
            
            # 从起始节点开始执行
            for start_node in start_nodes:
                async for event in execute_from_node(start_node["id"], user_input):
                    yield event
            
            yield f"data: {json.dumps({'type': 'log', 'message': '工作流执行完成'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'log', 'message': f'执行失败: {str(e)}'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==================== 代码助手流式 API ====================

class CodeAssistantRequest(BaseModel):
    message: str
    history: List[dict] = []


@app.post("/api/code-assistant/stream")
async def code_assistant_stream(request: CodeAssistantRequest):
    """代码助手流式 API - 支持 amis 代码生成和实时预览"""
    async def event_generator():
        try:
            user_input = request.message
            history = request.history or []
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '正在分析需求...'})}\n\n"
            
            # 构建包含历史上下文的提示
            context_prompt = ""
            if history:
                context_prompt = "以下是之前的对话历史，请参考上下文理解用户需求：\n\n"
                for msg in history[-10:]:  # 只保留最近10条消息
                    role = "用户" if msg.get("role") == "user" else "助手"
                    content = msg.get("content", "")[:500]  # 限制每条消息长度
                    context_prompt += f"{role}: {content}\n\n"
                context_prompt += "---\n\n"
            
            # 创建代码生成智能体
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
                api_key=API_KEY,
                model_name="qwen3-max",
                max_iters=30,
            )
            
            yield f"data: {json.dumps({'type': 'thinking', 'message': '正在生成代码...'})}\n\n"
            
            # 构建完整的用户输入（包含上下文）
            full_input = context_prompt + "当前用户需求: " + user_input if context_prompt else user_input
            
            # 调用智能体
            response = await code_agent(Msg("user", full_input, "user"))
            result = response.content if hasattr(response, "content") else str(response)
            
            # 处理返回值可能是列表的情况
            if isinstance(result, list):
                result = result[0].get("text", str(result[0])) if result else ""
            
            # 尝试提取 JSON 代码块
            amis_json = None
            import re
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', str(result))
            if json_match:
                try:
                    amis_json = json.loads(json_match.group(1))
                    yield f"data: {json.dumps({'type': 'amis_code', 'code': amis_json})}\n\n"
                except json.JSONDecodeError:
                    pass
            
            # 发送完整响应
            yield f"data: {json.dumps({'type': 'content', 'content': str(result)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==================== 制度问答智能体 API ====================

class PolicyQARequest(BaseModel):
    question: str


# 全局制度问答智能体实例
policy_qa_agent = None


def get_policy_qa_agent():
    """获取或创建制度问答智能体"""
    global policy_qa_agent
    if policy_qa_agent is None:
        try:
            print("[PolicyQA] 正在创建智能体...")
            policy_qa_agent = PolicyQAAgent(
                api_key=API_KEY,
                model_name="qwen3-max",
                max_iters=10,
            )
            print("[PolicyQA] 智能体创建成功")
        except Exception as e:
            import traceback
            print(f"[PolicyQA] 智能体创建失败: {e}")
            traceback.print_exc()
            raise
    
    return policy_qa_agent


@app.post("/api/policy-qa")
async def policy_qa(request: PolicyQARequest):
    """制度问答 API"""
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'start', 'message': '正在查询制度...'})}\n\n"
            
            agent = get_policy_qa_agent()
            response = await agent(Msg("user", request.question, "user"))
            answer = response.content if hasattr(response, "content") else str(response)
            
            yield f"data: {json.dumps({'type': 'answer', 'content': answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/policy-qa/sync")
async def policy_qa_sync(request: PolicyQARequest):
    """制度问答 API（同步版本）"""
    try:
        print(f"[PolicyQA] 收到问题: {request.question}")
        agent = get_policy_qa_agent()
        print(f"[PolicyQA] 智能体已创建: {agent.name}")
        response = await agent(Msg("user", request.question, "user"))
        print(f"[PolicyQA] 收到响应: {type(response)}")
        answer = response.content if hasattr(response, "content") else str(response)
        print(f"[PolicyQA] 原始答案类型: {type(answer)}")
        
        # 如果 answer 是列表或 JSON 字符串，提取文本内容
        if isinstance(answer, list):
            # 从列表中提取 text 字段
            texts = []
            for item in answer:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
                elif isinstance(item, str):
                    texts.append(item)
            answer = "\n".join(texts) if texts else str(answer)
        elif isinstance(answer, str):
            # 尝试解析 JSON 字符串
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
                pass  # 不是 JSON，保持原样
        
        # 格式化答案，处理换行和 Markdown
        if isinstance(answer, str):
            # 将转义的换行符转换为实际换行
            answer = answer.replace('\\n', '\n')
            
            answer = answer.strip()
        
        print(f"[PolicyQA] 处理后答案: {answer[:100] if answer else 'empty'}...")
        
        return {"success": True, "answer": answer}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== OCR 识别智能体 API ====================

class OCRRequest(BaseModel):
    file_path: str
    dpi: int = 144
    prompt_mode: str = "prompt_layout_all_en"


# 全局 OCR 智能体实例
ocr_agent = None


def get_ocr_agent():
    """获取或创建 OCR 智能体"""
    global ocr_agent
    if ocr_agent is None:
        try:
            print("[OCR] 正在创建智能体...")
            ocr_agent = OCRAgent(
                api_key=API_KEY,
                model_name="qwen3-max",
                max_iters=10,
            )
            print("[OCR] 智能体创建成功")
        except Exception as e:
            import traceback
            print(f"[OCR] 智能体创建失败: {e}")
            traceback.print_exc()
            raise
    
    return ocr_agent


@app.post("/api/ocr/recognize")
async def ocr_recognize(request: OCRRequest):
    """OCR 识别 API"""
    try:
        print(f"[OCR] 收到识别请求: {request.file_path}")
        agent = get_ocr_agent()
        
        # 调用 OCR 识别
        result = await agent.recognize_file(
            file_path=request.file_path,
            dpi=request.dpi,
            prompt_mode=request.prompt_mode
        )
        
        print(f"[OCR] 识别完成: {len(result) if result else 0} 字符")
        return {"success": True, "text": result}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ocr/chat")
async def ocr_chat(request: PolicyQARequest):
    """OCR 智能体对话 API（支持自动检测文件路径）"""
    try:
        print(f"[OCR] 收到对话: {request.question}")
        agent = get_ocr_agent()
        response = await agent(Msg("user", request.question, "user"))
        answer = response.content if hasattr(response, "content") else str(response)
        
        print(f"[OCR] 响应: {answer[:100] if answer else 'empty'}...")
        return {"success": True, "answer": answer}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 技能创建智能体 API ====================

# 全局技能创建智能体实例
skill_creator_agent = None


def get_skill_creator_agent():
    """获取或创建技能创建智能体"""
    global skill_creator_agent
    if skill_creator_agent is None:
        try:
            print("[SkillCreator] 正在创建智能体...")
            skill_creator_agent = SkillCreatorAgent(
                api_key=API_KEY,
                model_name="qwen3-max",
                max_iters=30,
            )
            print("[SkillCreator] 智能体创建成功")
        except Exception as e:
            import traceback
            print(f"[SkillCreator] 智能体创建失败: {e}")
            traceback.print_exc()
            raise
    
    return skill_creator_agent


@app.post("/api/skill-creator/chat")
async def skill_creator_chat(request: PolicyQARequest):
    """技能创建智能体对话 API"""
    try:
        print(f"[SkillCreator] 收到请求: {request.question}")
        agent = get_skill_creator_agent()
        response = await agent(Msg("user", request.question, "user"))
        answer = response.content if hasattr(response, "content") else str(response)
        
        print(f"[SkillCreator] 响应: {answer[:100] if answer else 'empty'}...")
        return answer
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # 启动前验证工作流加载状态
    print("\n" + "="*50)
    print("启动前验证:")
    print(f"predefined_workflows 长度: {len(predefined_workflows)}")
    print(f"predefined_workflows 键: {list(predefined_workflows.keys())}")
    print(f"predefined_workflows 内存地址: {id(predefined_workflows)}")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
