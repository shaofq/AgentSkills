# -*- coding: utf-8 -*-
"""
工作流 CRUD 路由
"""
import uuid
from datetime import datetime
from typing import List, Dict
from fastapi import APIRouter, HTTPException

from api.models.workflow import Workflow, WorkflowExecution, ExecutionResult
from api.models.request import ExecuteRequest

router = APIRouter(prefix="/api/workflows", tags=["工作流管理"])

# 工作流数据库（内存存储）
workflows_db: Dict[str, dict] = {}
executions_db: Dict[str, dict] = {}


@router.get("", response_model=List[Workflow])
async def get_workflows():
    """获取所有工作流"""
    return list(workflows_db.values())


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str):
    """获取单个工作流"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return workflows_db[workflow_id]


@router.post("", response_model=Workflow)
async def create_workflow(workflow: Workflow):
    """创建工作流"""
    workflow.id = workflow.id or str(uuid.uuid4())
    workflow.createdAt = workflow.createdAt or datetime.now().isoformat()
    workflow.updatedAt = datetime.now().isoformat()
    workflows_db[workflow.id] = workflow.dict()
    return workflow


@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, workflow: Workflow):
    """更新工作流"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="工作流不存在")
    workflow.id = workflow_id
    workflow.updatedAt = datetime.now().isoformat()
    workflows_db[workflow_id] = workflow.dict()
    return workflow


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """删除工作流"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="工作流不存在")
    del workflows_db[workflow_id]
    return {"message": "删除成功"}


@router.get("/executions/{execution_id}", response_model=WorkflowExecution)
async def get_execution(execution_id: str):
    """获取执行状态"""
    if execution_id not in executions_db:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return executions_db[execution_id]
