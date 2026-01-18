# -*- coding: utf-8 -*-
"""船员护照比对 API 路由"""
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.services.crew_compare_service import get_crew_compare_service


router = APIRouter(prefix="/api/crew-compare", tags=["船员护照比对"])

# 上传目录
UPLOAD_DIR = Path("/tmp/crew_compare_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============= 请求模型 =============

class CreateSessionResponse(BaseModel):
    success: bool
    session_id: str


class CompareRequest(BaseModel):
    session_id: str


# ============= API 接口 =============

@router.post("/session", response_model=CreateSessionResponse)
async def create_session():
    """创建新的比对会话"""
    service = get_crew_compare_service()
    session_id = service.create_session()
    return {"success": True, "session_id": session_id}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话状态"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 返回会话摘要（不包含大数据）
    return {
        "success": True,
        "data": {
            "id": session["id"],
            "status": session["status"],
            "created_at": session["created_at"],
            "excel_loaded": session["excel_data"] is not None,
            "crew_count": len(session["excel_data"]) if session["excel_data"] else 0,
            "passport_count": len(session["passports"]),
            "has_results": len(session.get("compare_results", [])) > 0,
            "stats": session.get("stats")
        }
    }


@router.post("/upload-excel/{session_id}")
async def upload_excel(
    session_id: str,
    file: UploadFile = File(...)
):
    """上传 Excel 船员名单"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="请上传 Excel 文件 (.xlsx 或 .xls)")
    
    # 保存文件
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = session_dir / file.filename
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 解析 Excel
    result = service.parse_excel(session_id, str(file_path))
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"success": True, "data": result}


@router.post("/upload-passports/{session_id}")
async def upload_passports(
    session_id: str,
    files: List[UploadFile] = File(...)
):
    """批量上传护照图片"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 保存文件
    session_dir = UPLOAD_DIR / session_id / "passports"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for file in files:
        # 验证文件类型
        ext = Path(file.filename).suffix.lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            continue
        
        file_path = session_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        saved_files.append({
            "filename": file.filename,
            "path": str(file_path),
            "status": "uploaded"
        })
    
    return {
        "success": True,
        "count": len(saved_files),
        "files": saved_files
    }


@router.post("/recognize/{session_id}/{filename}")
async def recognize_passport(session_id: str, filename: str):
    """识别单个护照图片"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    file_path = UPLOAD_DIR / session_id / "passports" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    result = await service.add_passport(session_id, str(file_path))
    
    return {"success": True, "data": result}


@router.post("/recognize-all/{session_id}")
async def recognize_all_passports(session_id: str):
    """识别所有已上传的护照图片"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    passport_dir = UPLOAD_DIR / session_id / "passports"
    
    if not passport_dir.exists():
        raise HTTPException(status_code=400, detail="未上传护照图片")
    
    results = []
    for file_path in passport_dir.iterdir():
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            result = await service.add_passport(session_id, str(file_path))
            results.append({
                "filename": file_path.name,
                "result": result
            })
    
    return {
        "success": True,
        "count": len(results),
        "results": results
    }


@router.post("/compare/{session_id}")
async def compare(session_id: str):
    """执行比对"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    result = service.compare(session_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/results/{session_id}")
async def get_results(session_id: str):
    """获取比对结果"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "success": True,
        "data": {
            "results": session.get("compare_results", []),
            "stats": session.get("stats"),
            "crew_list": session.get("excel_data", []),
            "passports": session.get("passports", {})
        }
    }


@router.get("/export/{session_id}")
async def export_report(session_id: str):
    """导出比对报告"""
    service = get_crew_compare_service()
    session = service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 生成报告文件
    output_path = UPLOAD_DIR / session_id / f"比对报告_{session_id}.xlsx"
    result = service.export_report(session_id, str(output_path))
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return FileResponse(
        str(output_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"船员护照比对报告_{session_id}.xlsx"
    )


@router.get("/passport-image/{session_id}/{filename}")
async def get_passport_image(session_id: str, filename: str):
    """获取护照图片"""
    file_path = UPLOAD_DIR / session_id / "passports" / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 确定媒体类型
    ext = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }
    
    return FileResponse(
        str(file_path),
        media_type=media_types.get(ext, "image/jpeg")
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话及相关文件"""
    service = get_crew_compare_service()
    
    # 删除会话数据
    if session_id in service.sessions:
        del service.sessions[session_id]
    
    # 删除上传文件
    session_dir = UPLOAD_DIR / session_id
    if session_dir.exists():
        shutil.rmtree(session_dir)
    
    return {"success": True, "message": "会话已删除"}


# ============= 历史记录接口 =============

@router.get("/history")
async def get_history(limit: int = 50):
    """获取操作历史记录"""
    service = get_crew_compare_service()
    history = service.get_history(limit)
    return {"success": True, "data": history, "count": len(history)}


@router.get("/history/{session_id}")
async def get_session_history(session_id: str):
    """获取指定会话的历史记录"""
    service = get_crew_compare_service()
    history = service.get_session_history(session_id)
    return {"success": True, "data": history, "count": len(history)}


# ============= 比对字段配置接口 =============

class CompareFieldConfig(BaseModel):
    excel_field: str
    passport_field: str
    label: str
    enabled: bool = True


class UpdateCompareFieldsRequest(BaseModel):
    fields: List[CompareFieldConfig]


@router.get("/compare-fields/{session_id}")
async def get_compare_fields(session_id: str):
    """获取比对字段配置"""
    service = get_crew_compare_service()
    fields = service.get_compare_fields(session_id)
    return {"success": True, "data": fields}


@router.put("/compare-fields/{session_id}")
async def update_compare_fields(session_id: str, request: UpdateCompareFieldsRequest):
    """更新比对字段配置"""
    service = get_crew_compare_service()
    
    # 转换为字典列表
    fields = [f.dict() for f in request.fields]
    result = service.update_compare_fields(session_id, fields)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/excel-columns/{session_id}")
async def get_excel_columns(session_id: str):
    """获取Excel中可用的列名"""
    service = get_crew_compare_service()
    columns = service.get_available_excel_columns(session_id)
    return {"success": True, "data": columns}


@router.get("/default-compare-fields")
async def get_default_compare_fields():
    """获取默认比对字段配置"""
    service = get_crew_compare_service()
    return {"success": True, "data": service.DEFAULT_COMPARE_FIELDS}


# ============= Excel列映射配置接口 =============

@router.get("/column-mapping/{session_id}")
async def get_column_mapping(session_id: str):
    """获取当前列映射配置"""
    service = get_crew_compare_service()
    result = service.get_column_mapping(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


class UpdateColumnMappingRequest(BaseModel):
    mapping: dict


@router.put("/column-mapping/{session_id}")
async def update_column_mapping(session_id: str, request: UpdateColumnMappingRequest):
    """更新列映射配置"""
    service = get_crew_compare_service()
    result = service.update_column_mapping(session_id, request.mapping)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============= 护照识别结果编辑接口 =============

class UpdatePassportRequest(BaseModel):
    updates: dict


@router.put("/passport/{session_id}/{passport_no}")
async def update_passport_result(session_id: str, passport_no: str, request: UpdatePassportRequest):
    """手动编辑护照识别结果"""
    service = get_crew_compare_service()
    result = service.update_passport_result(session_id, passport_no, request.updates)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============= 单张重新识别接口 =============

@router.post("/re-recognize/{session_id}/{filename}")
async def re_recognize_passport(session_id: str, filename: str):
    """重新识别单张护照"""
    service = get_crew_compare_service()
    result = service.recognize_single_passport(session_id, filename)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
