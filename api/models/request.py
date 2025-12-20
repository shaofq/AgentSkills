# -*- coding: utf-8 -*-
"""
请求数据模型
"""
from typing import List, Optional
from pydantic import BaseModel


class ExecuteRequest(BaseModel):
    """工作流执行请求"""
    input: str


class PredefinedWorkflowRequest(BaseModel):
    """预定义工作流执行请求"""
    workflow_name: str
    input: str
    history: List[dict] = []


class WorkflowTestRequest(BaseModel):
    """工作流测试请求"""
    workflow: dict
    input: str


class CodeAssistantRequest(BaseModel):
    """代码助手请求"""
    message: str
    history: List[dict] = []


class PolicyQARequest(BaseModel):
    """制度问答请求"""
    question: str


class OCRRequest(BaseModel):
    """OCR 识别请求"""
    file_path: str
    dpi: int = 144
    prompt_mode: str = "prompt_layout_all_en"


class MenuBindingUpdate(BaseModel):
    """菜单绑定更新请求"""
    menuId: str
    workflowName: Optional[str] = None
