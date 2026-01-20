# -*- coding: utf-8 -*-
"""
危险品识别系统API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Depends
from fastapi.responses import Response
from typing import Optional, List

from api.models.hazmat import (
    ProcessStatus, HazmatResult, RuleCreate, RuleUpdate,
    ConfirmRequest, HistoryQuery, DocumentType, Annotation,
    AnnotationSubmit, RuleDraft
)
from api.services.hazmat_service import get_hazmat_service
from api.services.learning_service import learning_service
from api.routers.auth import get_current_user
from api.models.user import UserResponse

router = APIRouter(prefix="/api/hazmat", tags=["危险品识别"])


# ========== 文件管理 ==========

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """上传SDS文件"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持PDF文件")
    
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB限制
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
    
    service = get_hazmat_service()
    result = service.upload_file(file.filename, content)
    
    return {"success": True, "data": result}


@router.post("/analyze/{file_id}")
async def analyze_file(
    file_id: int,
    use_llm: bool = Query(default=True, description="是否使用大模型增强"),
    current_user: UserResponse = Depends(get_current_user)
):
    """分析SDS文件"""
    service = get_hazmat_service()
    
    try:
        result = service.analyze_file(file_id, use_llm)
        return {
            "success": True,
            "data": {
                "file_id": result.file_id,
                "result": result.result.value,
                "confidence": result.confidence,
                "extracted_info": result.extracted_info.model_dump() if result.extracted_info else None,
                "matched_rules": result.matched_rules,
                "suggestions": result.suggestions
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/confirm")
async def confirm_result(
    request: ConfirmRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """确认分析结果"""
    service = get_hazmat_service()
    
    try:
        corrections = None
        if request.corrections:
            corrections = [c.model_dump() for c in request.corrections]
        
        result = service.confirm_result(
            file_id=request.file_id,
            result=request.result,
            corrections=corrections,
            confirmed_by=current_user.username
        )
        
        # 如果用户选择创建规则
        if request.create_rule and request.rule_name and corrections:
            # 基于第一个修正创建规则
            correction = corrections[0]
            service.create_rule(
                name=request.rule_name,
                condition_field=correction['field_name'],
                condition_operator='equals',
                condition_value=correction['new_value'],
                result=request.result.value,
                description=f"基于用户修正自动创建",
                created_by=current_user.username
            )
        
        return {"success": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/files")
async def get_files(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = None,
    result: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取文件列表"""
    service = get_hazmat_service()
    skip = (page - 1) * page_size
    files, total = service.get_file_list(skip, page_size, status, result, keyword)
    
    return {
        "success": True,
        "data": {
            "items": files,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/files/{file_id}")
async def get_file(
    file_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取文件详情"""
    service = get_hazmat_service()
    file_record = service.get_file(file_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {"success": True, "data": file_record}


@router.get("/files/{file_id}/content")
async def get_file_content(
    file_id: int,
    token: Optional[str] = Query(default=None, description="认证令牌（用于iframe）")
):
    """获取文件内容（PDF）- 支持query参数token用于iframe预览"""
    # 验证token
    if token:
        from api.services.auth_service import AuthService
        auth_service = AuthService()
        user = auth_service.get_current_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
    else:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    service = get_hazmat_service()
    file_record = service.get_file(file_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    content = service.get_file_content(file_id)
    if not content:
        raise HTTPException(status_code=404, detail="文件内容不存在")
    
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{file_record["filename"]}"'}
    )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """删除文件"""
    service = get_hazmat_service()
    
    if service.delete_file(file_id):
        return {"success": True, "message": "文件已删除"}
    raise HTTPException(status_code=404, detail="文件不存在")


# ========== 规则管理 ==========

@router.get("/rules")
async def get_rules(
    include_inactive: bool = Query(default=False),
    rule_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取规则列表"""
    service = get_hazmat_service()
    rules = service.get_rules(include_inactive, rule_type)
    return {"success": True, "data": rules}


@router.get("/rules/{rule_id}")
async def get_rule(
    rule_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取规则详情"""
    service = get_hazmat_service()
    rule = service.get_rule(rule_id)
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    return {"success": True, "data": rule}


@router.post("/rules")
async def create_rule(
    request: RuleCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """创建规则"""
    service = get_hazmat_service()
    
    rule = service.create_rule(
        name=request.name,
        condition_field=request.condition_field,
        condition_operator=request.condition_operator,
        condition_value=request.condition_value,
        result=request.result.value,
        description=request.description,
        created_by=current_user.username
    )
    
    return {"success": True, "data": rule}


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    request: RuleUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新规则"""
    service = get_hazmat_service()
    
    update_data = request.model_dump(exclude_unset=True)
    if 'result' in update_data and update_data['result']:
        update_data['result'] = update_data['result'].value
    
    rule = service.update_rule(rule_id, **update_data)
    
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    return {"success": True, "data": rule}


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """删除规则（仅自定义规则）"""
    service = get_hazmat_service()
    
    if service.delete_rule(rule_id):
        return {"success": True, "message": "规则已删除"}
    raise HTTPException(status_code=400, detail="规则不存在或为内置规则")


@router.put("/rules/{rule_id}/toggle")
async def toggle_rule(
    rule_id: int,
    is_active: bool = Query(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """启用/禁用规则"""
    service = get_hazmat_service()
    
    rule = service.toggle_rule(rule_id, is_active)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    return {"success": True, "data": rule}


# ========== 统计 ==========

@router.get("/statistics")
async def get_statistics(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取统计信息"""
    service = get_hazmat_service()
    stats = service.get_statistics()
    return {"success": True, "data": stats}


# ========== 字段定义 ==========

@router.get("/field-definitions")
async def get_field_definitions():
    """获取可用的字段定义（用于创建规则）"""
    fields = [
        {"name": "product_name", "label": "产品名称", "type": "string"},
        {"name": "cas_number", "label": "CAS号", "type": "string"},
        {"name": "hazard_class", "label": "危险性类别", "type": "array"},
        {"name": "pictograms", "label": "象形图", "type": "array"},
        {"name": "signal_word", "label": "信号词", "type": "string"},
        {"name": "un_number", "label": "UN编号", "type": "string"},
        {"name": "proper_shipping_name", "label": "运输专用名称", "type": "string"},
        {"name": "hazard_statements", "label": "H声明", "type": "array"},
        {"name": "precautionary_statements", "label": "P声明", "type": "array"},
    ]
    
    operators = [
        {"name": "contains", "label": "包含", "description": "字段值包含指定文本"},
        {"name": "equals", "label": "等于", "description": "字段值完全等于指定文本"},
        {"name": "exists", "label": "存在", "description": "字段值非空"},
        {"name": "regex", "label": "正则匹配", "description": "使用正则表达式匹配"},
    ]
    
    return {
        "success": True,
        "data": {
            "fields": fields,
            "operators": operators
        }
    }


# ========== 智能文档学习与规则生成 ==========

@router.post("/learning/upload")
async def upload_learning_document(
    file: UploadFile = File(...),
    doc_type: str = Query(default="other", description="文档类型: sds/other"),
    current_user: UserResponse = Depends(get_current_user)
):
    """上传学习文档"""
    # 支持更多文件格式
    allowed_ext = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png', '.bmp']
    ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持: {', '.join(allowed_ext)}")
    
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
    
    doc_type_enum = DocumentType.SDS if doc_type == "sds" else DocumentType.OTHER
    doc_id = learning_service.upload_document(
        file.filename, content, doc_type_enum, 
        created_by=current_user.username
    )
    
    return {"success": True, "data": {"id": doc_id, "filename": file.filename}}


@router.post("/learning/{doc_id}/preprocess")
async def preprocess_learning_document(
    doc_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """AI预处理学习文档"""
    try:
        # 初始化LLM客户端
        service = get_hazmat_service()
        if service.parser.llm_client:
            learning_service.set_llm_client(service.parser.llm_client, service.parser.llm_model)
        
        result = learning_service.preprocess_document(doc_id)
        return {
            "success": True,
            "data": {
                "file_id": result.file_id,
                "raw_text": result.raw_text[:5000] if len(result.raw_text) > 5000 else result.raw_text,
                "raw_text_full_length": len(result.raw_text),
                "ai_highlights": [h.dict() for h in result.ai_highlights],
                "status": result.status.value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/{doc_id}")
async def get_learning_document(
    doc_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """获取学习文档详情"""
    doc = learning_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {
        "success": True,
        "data": {
            "id": doc.id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "doc_type": doc.doc_type.value,
            "status": doc.status.value,
            "raw_text": doc.raw_text[:5000] if doc.raw_text and len(doc.raw_text) > 5000 else doc.raw_text,
            "raw_text_full_length": len(doc.raw_text) if doc.raw_text else 0,
            "ai_highlights": doc.ai_highlights,
            "annotations": doc.annotations,
            "judgment": doc.judgment.value if doc.judgment else None,
            "created_at": doc.created_at,
            "created_by": doc.created_by
        }
    }


@router.get("/learning/{doc_id}/text")
async def get_learning_document_text(
    doc_id: int,
    offset: int = Query(default=0, description="文本偏移量"),
    limit: int = Query(default=10000, description="返回长度"),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取学习文档全文（分页）"""
    doc = learning_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    text = doc.raw_text or ""
    return {
        "success": True,
        "data": {
            "text": text[offset:offset+limit],
            "total_length": len(text),
            "offset": offset,
            "has_more": offset + limit < len(text)
        }
    }


@router.get("/learning/{doc_id}/file")
async def get_learning_document_file(
    doc_id: int,
    token: str = Query(default=None, description="认证令牌"),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取学习文档原始文件"""
    from fastapi.responses import FileResponse
    
    file_path = learning_service.get_document_file_path(doc_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    import os
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    # 根据文件类型设置正确的media_type
    media_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    media_type = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename
    )


@router.post("/learning/{doc_id}/annotations")
async def save_annotations(
    doc_id: int,
    data: AnnotationSubmit,
    current_user: UserResponse = Depends(get_current_user)
):
    """保存用户标注"""
    try:
        learning_service.save_annotations(
            doc_id, 
            data.annotations, 
            data.judgment,
            created_by=current_user.username
        )
        return {"success": True, "message": "标注已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/{doc_id}/generate-rules")
async def generate_rules(
    doc_id: int,
    basis_fields: List[str] = Query(default=[], description="判断依据字段列表"),
    current_user: UserResponse = Depends(get_current_user)
):
    """根据标注生成规则草稿"""
    try:
        result = learning_service.generate_rules(
            doc_id, 
            basis_fields,
            created_by=current_user.username
        )
        return {
            "success": True,
            "data": {
                "file_id": result.file_id,
                "rule_drafts": [r.dict() for r in result.rule_drafts]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 规则审核 ==========

@router.get("/rule-drafts")
async def get_rule_drafts(
    status: str = Query(default=None, description="状态筛选: pending_review/approved/rejected"),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取规则草稿列表"""
    drafts = learning_service.get_all_rule_drafts(status)
    return {"success": True, "data": drafts}


@router.get("/rule-drafts/pending")
async def get_pending_rule_drafts(
    current_user: UserResponse = Depends(get_current_user)
):
    """获取待审核的规则草稿"""
    drafts = learning_service.get_pending_rules()
    return {"success": True, "data": [d.dict() for d in drafts]}


@router.put("/rule-drafts/{rule_id}")
async def update_rule_draft(
    rule_id: int,
    request: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """更新规则草稿"""
    try:
        learning_service.update_rule_draft(
            rule_id,
            name=request.get('name'),
            description=request.get('description'),
            conditions=request.get('conditions'),
            result=request.get('result'),
            suggested_class=request.get('suggested_class')
        )
        return {"success": True, "message": "规则已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rule-drafts/{rule_id}/review")
async def review_rule_draft(
    rule_id: int,
    action: str = Query(..., description="操作: approve/reject/edit"),
    reason: str = Query(default=None, description="拒绝原因"),
    current_user: UserResponse = Depends(get_current_user)
):
    """审核规则草稿"""
    if action not in ['approve', 'reject', 'edit']:
        raise HTTPException(status_code=400, detail="无效的操作")
    
    try:
        learning_service.review_rule(
            rule_id, 
            action, 
            reviewed_by=current_user.username,
            reason=reason
        )
        
        action_label = {'approve': '已批准', 'reject': '已拒绝', 'edit': '已编辑'}
        return {"success": True, "message": f"规则{action_label.get(action, '')}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 标注字段定义 ==========

@router.get("/annotation-fields")
async def get_annotation_fields():
    """获取可用的标注字段定义"""
    fields = [
        {"name": "product_name", "label": "产品名称", "description": "化学品/产品的名称"},
        {"name": "cas_number", "label": "CAS号", "description": "化学物质登记号"},
        {"name": "un_number", "label": "UN编号", "description": "联合国危险货物编号"},
        {"name": "flash_point", "label": "闪点", "description": "物质闪点温度"},
        {"name": "boiling_point", "label": "沸点", "description": "物质沸点温度"},
        {"name": "hazard_class", "label": "危险类别", "description": "GHS/IMDG危险分类"},
        {"name": "packing_group", "label": "包装组", "description": "包装组别 I/II/III"},
        {"name": "ph_value", "label": "pH值", "description": "酸碱度"},
        {"name": "explosion_limit", "label": "爆炸极限", "description": "爆炸上/下限"},
        {"name": "hazard_keyword", "label": "危险性关键词", "description": "易燃、腐蚀性、有毒等"},
        {"name": "regulation_ref", "label": "法规引用", "description": "IATA DGR、IMDG Code等"},
    ]
    
    return {"success": True, "data": fields}
