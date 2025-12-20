# -*- coding: utf-8 -*-
"""
工作流相关数据模型
"""
from typing import List, Optional
from pydantic import BaseModel


class WorkflowNode(BaseModel):
    """工作流节点"""
    id: str
    type: str
    position: dict
    data: dict


class WorkflowEdge(BaseModel):
    """工作流边"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None


class Workflow(BaseModel):
    """工作流"""
    id: Optional[str] = None
    name: str
    description: str = ""
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


class ExecutionResult(BaseModel):
    """执行结果"""
    nodeId: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None


class WorkflowExecution(BaseModel):
    """工作流执行记录"""
    id: str
    workflowId: str
    status: str
    input: str
    results: List[ExecutionResult]
    startTime: str
    endTime: Optional[str] = None
