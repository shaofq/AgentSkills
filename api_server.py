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
from pydantic import BaseModel

from agentscope.message import Msg
from agents.base import BaseAgent
from agents.router import RouterAgent

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
    ]


@app.get("/api/skills", response_model=List[str])
async def get_skills():
    """获取可用的技能列表"""
    skill_dir = "./skill"
    if os.path.exists(skill_dir):
        return [d for d in os.listdir(skill_dir) if os.path.isdir(os.path.join(skill_dir, d))]
    return ["amis-code-assistant", "pptx", "data-analysis"]


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
                skill_paths = [f"./skill/{s}" for s in config.get("skills", [])]
                agent = BaseAgent(
                    name=config.get("name", node["id"]),
                    sys_prompt=config.get("systemPrompt", ""),
                    skills=skill_paths,
                    api_key=API_KEY,
                    model_name=config.get("model", "qwen3-max"),
                    max_iters=config.get("maxIters", 30),
                )
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
