# -*- coding: utf-8 -*-
"""VL OCR 识别 API 路由"""
import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.vl_ocr_agent import get_vl_ocr_agent
from api.services.file_monitor import get_file_monitor_service
from api.services.token_logger import log_agent_call


router = APIRouter(prefix="/api/vl-ocr", tags=["VL OCR识别"])


# ============= 请求模型 =============

class OCRRecognizeRequest(BaseModel):
    """OCR 识别请求"""
    file_path: str
    dpi: int = 150
    return_positions: bool = True


class WatchDirRequest(BaseModel):
    """监控目录请求"""
    path: str
    name: str = ""
    auto_process: bool = True


class ScanDirRequest(BaseModel):
    """扫描目录请求"""
    path: str


class ProcessFileRequest(BaseModel):
    """处理文件请求"""
    file_path: str


# ============= OCR 识别接口 =============

@router.post("/recognize")
async def recognize_file(request: OCRRecognizeRequest):
    """
    识别文件内容（PDF 或图片）。
    
    返回文本内容和定位信息。
    """
    try:
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {request.file_path}")
        
        print(f"[VL-OCR] 开始识别: {request.file_path}")
        
        agent = get_vl_ocr_agent()
        result = await agent.recognize(
            file_path=request.file_path,
            dpi=request.dpi,
            return_positions=request.return_positions,
        )
        
        # 记录 Token 消耗
        log_agent_call(
            agent_id="vl-ocr-agent",
            agent_name="VL OCR识别",
            model="qwen-vl-max-latest",
            input_text=request.file_path,
            output_text=result.get("full_text", "")[:500] if result else "",
        )
        
        print(f"[VL-OCR] 识别完成")
        return {"success": True, "data": result}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-and-recognize")
async def upload_and_recognize(
    file: UploadFile = File(...),
    dpi: int = 150,
    return_positions: bool = True,
):
    """
    上传文件并识别。
    """
    try:
        # 保存上传的文件
        upload_dir = Path("/tmp/vl_ocr_uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"[VL-OCR] 文件已上传: {file_path}")
        
        # 识别文件
        agent = get_vl_ocr_agent()
        result = await agent.recognize(
            file_path=str(file_path),
            dpi=dpi,
            return_positions=return_positions,
        )
        
        # 记录 Token 消耗
        log_agent_call(
            agent_id="vl-ocr-agent",
            agent_name="VL OCR识别",
            model="qwen-vl-max-latest",
            input_text=file.filename,
            output_text=result.get("full_text", "")[:500] if result else "",
        )
        
        return {"success": True, "data": result, "file_path": str(file_path)}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============= 文件监控接口 =============

@router.get("/monitor/status")
async def get_monitor_status():
    """获取监控服务状态"""
    service = get_file_monitor_service()
    return {"success": True, "data": service.get_status()}


@router.post("/monitor/start")
async def start_monitor():
    """启动监控服务"""
    service = get_file_monitor_service()
    
    # 设置 OCR 回调
    agent = get_vl_ocr_agent()
    service.set_ocr_callback(lambda path: agent.recognize(path))
    
    result = service.start()
    return result


@router.post("/monitor/stop")
async def stop_monitor():
    """停止监控服务"""
    service = get_file_monitor_service()
    result = service.stop()
    return result


@router.get("/monitor/dirs")
async def get_watch_dirs():
    """获取监控目录列表"""
    service = get_file_monitor_service()
    return {"success": True, "data": service.get_watch_dirs()}


@router.post("/monitor/dirs")
async def add_watch_dir(request: WatchDirRequest):
    """添加监控目录"""
    service = get_file_monitor_service()
    result = service.add_watch_dir(
        path=request.path,
        name=request.name,
        auto_process=request.auto_process,
    )
    return result


@router.delete("/monitor/dirs")
async def remove_watch_dir(path: str):
    """移除监控目录"""
    service = get_file_monitor_service()
    result = service.remove_watch_dir(path)
    return result


@router.post("/monitor/scan")
async def scan_directory(request: ScanDirRequest):
    """扫描目录中已存在的文件"""
    service = get_file_monitor_service()
    
    if not os.path.isdir(request.path):
        raise HTTPException(status_code=404, detail=f"目录不存在: {request.path}")
    
    files = service.scan_existing_files(request.path)
    return {
        "success": True,
        "data": {
            "path": request.path,
            "files": files,
            "count": len(files)
        }
    }


@router.post("/monitor/process")
async def process_file(request: ProcessFileRequest):
    """手动处理单个文件"""
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {request.file_path}")
    
    agent = get_vl_ocr_agent()
    result = await agent.recognize(request.file_path)
    
    # 保存到结果列表
    service = get_file_monitor_service()
    from datetime import datetime
    service.ocr_results[request.file_path] = {
        "file_path": request.file_path,
        "result": result,
        "processed_at": datetime.now().isoformat(),
        "status": "completed"
    }
    
    return {"success": True, "data": result}


# ============= 识别结果接口 =============

@router.get("/results")
async def get_results(limit: int = 50):
    """获取识别结果列表"""
    service = get_file_monitor_service()
    results = service.get_results(limit)
    return {"success": True, "data": results}


@router.delete("/results")
async def clear_results():
    """清除所有识别结果缓存"""
    service = get_file_monitor_service()
    count = len(service.ocr_results)
    service.ocr_results.clear()
    return {"success": True, "message": f"已清除 {count} 条识别结果"}


@router.get("/results/{file_path:path}")
async def get_result(file_path: str):
    """获取单个文件的识别结果"""
    service = get_file_monitor_service()
    
    # URL 解码
    import urllib.parse
    file_path = urllib.parse.unquote(file_path)
    
    result = service.get_result(file_path)
    if not result:
        raise HTTPException(status_code=404, detail="未找到该文件的识别结果")
    
    return {"success": True, "data": result}


# ============= 文件预览接口 =============

def convert_pdf_to_image(pdf_path: str, page: int = 0, dpi: int = 150) -> str:
    """将 PDF 页面转换为图片，返回图片路径"""
    import fitz  # PyMuPDF
    
    doc = fitz.open(pdf_path)
    if page >= len(doc):
        page = 0
    
    pdf_page = doc[page]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = pdf_page.get_pixmap(matrix=mat)
    
    # 保存为临时图片
    temp_dir = Path("/tmp/vl_ocr_preview")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    image_path = temp_dir / f"{Path(pdf_path).stem}_page_{page + 1}.png"
    pix.save(str(image_path))
    doc.close()
    
    # 打印图片尺寸用于调试
    print(f"[Preview] PDF 转图片完成: {image_path}, 尺寸: {pix.width}x{pix.height}")
    
    return str(image_path)


@router.get("/preview")
async def preview_file(path: str, page: int = 0):
    """
    获取文件预览（PDF 转换为图片返回，便于定位标注）。
    """
    import urllib.parse
    file_path = urllib.parse.unquote(path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    
    ext = Path(file_path).suffix.lower()
    
    # PDF 文件转换为图片
    if ext == ".pdf":
        try:
            # 使用与 OCR 相同的 DPI 参数
            image_path = convert_pdf_to_image(file_path, page, dpi=150)
            return FileResponse(
                image_path,
                media_type="image/png",
                headers={"Content-Disposition": "inline"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF 转换失败: {e}")
    
    # 图片文件直接返回
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={"Content-Disposition": "inline"}
    )
