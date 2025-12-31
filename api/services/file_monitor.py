# -*- coding: utf-8 -*-
"""文件夹监控服务 - 自动监控目录中的 PDF 和图片文件"""
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent


class OCRFileHandler(FileSystemEventHandler):
    """OCR 文件事件处理器"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
    
    def __init__(self, callback: Callable[[str], None]):
        """
        初始化处理器。
        
        Args:
            callback: 文件检测回调函数，接收文件路径
        """
        self.callback = callback
        self.processed_files = set()
    
    def _is_supported_file(self, file_path: str) -> bool:
        """检查是否为支持的文件类型"""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory and self._is_supported_file(event.src_path):
            # 避免重复处理
            if event.src_path not in self.processed_files:
                self.processed_files.add(event.src_path)
                print(f"[FileMonitor] 检测到新文件: {event.src_path}")
                self.callback(event.src_path)
    
    def on_modified(self, event):
        """文件修改事件（某些系统创建文件会先触发修改事件）"""
        if not event.is_directory and self._is_supported_file(event.src_path):
            if event.src_path not in self.processed_files:
                self.processed_files.add(event.src_path)
                print(f"[FileMonitor] 检测到文件变更: {event.src_path}")
                self.callback(event.src_path)


class FileMonitorService:
    """文件夹监控服务"""
    
    def __init__(self):
        """初始化监控服务"""
        self.observers: Dict[str, Observer] = {}
        self.watch_dirs: Dict[str, dict] = {}
        self.is_running = False
        self.pending_files: List[str] = []
        self.ocr_results: Dict[str, dict] = {}
        self.ocr_callback: Optional[Callable] = None
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # 配置文件路径
        self.config_path = Path(__file__).parent.parent.parent / "config" / "file_monitor.json"
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载监控配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.watch_dirs = config.get("watch_dirs", {})
                    print(f"[FileMonitor] 加载配置: {len(self.watch_dirs)} 个监控目录")
            except Exception as e:
                print(f"[FileMonitor] 加载配置失败: {e}")
                self.watch_dirs = {}
    
    def _save_config(self):
        """保存监控配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "watch_dirs": self.watch_dirs,
                    "updated_at": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            print(f"[FileMonitor] 配置已保存")
        except Exception as e:
            print(f"[FileMonitor] 保存配置失败: {e}")
    
    def add_watch_dir(self, path: str, name: str = "", auto_process: bool = True) -> dict:
        """
        添加监控目录。
        
        Args:
            path: 目录路径
            name: 目录名称（可选）
            auto_process: 是否自动处理文件
            
        Returns:
            添加结果
        """
        path = str(Path(path).resolve())
        
        if not os.path.isdir(path):
            return {"success": False, "error": f"目录不存在: {path}"}
        
        if path in self.watch_dirs:
            return {"success": False, "error": "目录已在监控列表中"}
        
        self.watch_dirs[path] = {
            "name": name or Path(path).name,
            "path": path,
            "auto_process": auto_process,
            "created_at": datetime.now().isoformat(),
            "status": "stopped"
        }
        
        self._save_config()
        
        return {
            "success": True,
            "message": f"已添加监控目录: {path}",
            "dir_info": self.watch_dirs[path]
        }
    
    def remove_watch_dir(self, path: str) -> dict:
        """
        移除监控目录。
        
        Args:
            path: 目录路径
            
        Returns:
            移除结果
        """
        path = str(Path(path).resolve())
        
        if path not in self.watch_dirs:
            return {"success": False, "error": "目录不在监控列表中"}
        
        # 如果正在监控，先停止
        if path in self.observers:
            self.observers[path].stop()
            self.observers[path].join()
            del self.observers[path]
        
        del self.watch_dirs[path]
        self._save_config()
        
        return {"success": True, "message": f"已移除监控目录: {path}"}
    
    def get_watch_dirs(self) -> List[dict]:
        """获取所有监控目录"""
        return list(self.watch_dirs.values())
    
    def _on_file_detected(self, file_path: str):
        """文件检测回调（在 watchdog 线程中调用）"""
        self.pending_files.append(file_path)
        
        # 如果设置了 OCR 回调，则在主事件循环中调度任务
        if self.ocr_callback and self._main_loop:
            # 使用 run_coroutine_threadsafe 在主事件循环中调度异步任务
            asyncio.run_coroutine_threadsafe(
                self._process_file(file_path),
                self._main_loop
            )
    
    async def _process_file(self, file_path: str):
        """处理检测到的文件"""
        if self.ocr_callback:
            try:
                result = await self.ocr_callback(file_path)
                self.ocr_results[file_path] = {
                    "file_path": file_path,
                    "result": result,
                    "processed_at": datetime.now().isoformat(),
                    "status": "completed"
                }
                print(f"[FileMonitor] 文件处理完成: {file_path}")
            except Exception as e:
                self.ocr_results[file_path] = {
                    "file_path": file_path,
                    "error": str(e),
                    "processed_at": datetime.now().isoformat(),
                    "status": "failed"
                }
                print(f"[FileMonitor] 文件处理失败: {file_path}, 错误: {e}")
    
    def set_ocr_callback(self, callback: Callable):
        """设置 OCR 处理回调"""
        self.ocr_callback = callback
    
    def start(self) -> dict:
        """启动所有监控"""
        if self.is_running:
            return {"success": False, "error": "监控服务已在运行"}
        
        # 保存当前事件循环引用，用于跨线程调度异步任务
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None
        
        started = []
        for path, config in self.watch_dirs.items():
            if os.path.isdir(path):
                handler = OCRFileHandler(self._on_file_detected)
                observer = Observer()
                observer.schedule(handler, path, recursive=True)
                observer.start()
                
                self.observers[path] = observer
                self.watch_dirs[path]["status"] = "running"
                started.append(path)
                print(f"[FileMonitor] 开始监控: {path}")
        
        self.is_running = True
        self._save_config()
        
        return {
            "success": True,
            "message": f"已启动 {len(started)} 个目录监控",
            "started_dirs": started
        }
    
    def stop(self) -> dict:
        """停止所有监控"""
        if not self.is_running:
            return {"success": False, "error": "监控服务未运行"}
        
        for path, observer in self.observers.items():
            observer.stop()
            observer.join()
            if path in self.watch_dirs:
                self.watch_dirs[path]["status"] = "stopped"
        
        self.observers.clear()
        self.is_running = False
        self._save_config()
        
        return {"success": True, "message": "监控服务已停止"}
    
    def get_status(self) -> dict:
        """获取服务状态"""
        return {
            "is_running": self.is_running,
            "watch_dirs_count": len(self.watch_dirs),
            "active_observers": len(self.observers),
            "pending_files": len(self.pending_files),
            "processed_files": len(self.ocr_results),
            "watch_dirs": self.get_watch_dirs()
        }
    
    def get_results(self, limit: int = 50) -> List[dict]:
        """获取识别结果列表"""
        results = list(self.ocr_results.values())
        # 按处理时间倒序
        results.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
        return results[:limit]
    
    def get_result(self, file_path: str) -> Optional[dict]:
        """获取单个文件的识别结果"""
        return self.ocr_results.get(file_path)
    
    def scan_existing_files(self, path: str) -> List[str]:
        """扫描目录中已存在的文件"""
        path = Path(path)
        if not path.is_dir():
            return []
        
        supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
        files = []
        
        for file in path.rglob("*"):
            if file.is_file() and file.suffix.lower() in supported_extensions:
                files.append(str(file))
        
        return files


# 单例实例
_file_monitor_service: Optional[FileMonitorService] = None


def get_file_monitor_service() -> FileMonitorService:
    """获取文件监控服务单例"""
    global _file_monitor_service
    if _file_monitor_service is None:
        _file_monitor_service = FileMonitorService()
    return _file_monitor_service
