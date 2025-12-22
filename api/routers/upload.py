# -*- coding: utf-8 -*-
"""
文件上传路由
"""
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

# 上传文件存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件
    
    Returns:
        file_path: 文件的绝对路径
        file_name: 原始文件名
        file_size: 文件大小（字节）
    """
    try:
        # 生成唯一文件名
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        
        # 保存文件
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"[Upload] 文件上传成功: {file.filename} -> {file_path}")
        
        return {
            "success": True,
            "file_path": os.path.abspath(file_path),
            "file_name": file.filename,
            "file_size": len(content)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_uploads():
    """列出已上传的文件"""
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    files.append({
                        "name": filename,
                        "path": os.path.abspath(file_path),
                        "size": os.path.getsize(file_path),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
        return {"success": True, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
