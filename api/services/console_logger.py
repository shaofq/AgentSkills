# -*- coding: utf-8 -*-
"""
控制台日志捕获服务

用于捕获 print 输出并通过 SSE 推送到前端
"""
import sys
import asyncio
import threading
from io import StringIO
from typing import Callable, Optional, List
from datetime import datetime
from contextlib import contextmanager


class ConsoleCapture:
    """控制台输出捕获器"""
    
    def __init__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._callbacks: List[Callable[[str, str], None]] = []
        self._buffer = StringIO()
        self._lock = threading.Lock()
        self._capturing = False
    
    def add_callback(self, callback: Callable[[str, str], None]):
        """添加日志回调函数
        
        Args:
            callback: 回调函数，接收 (log_type, message) 参数
        """
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, str], None]):
        """移除日志回调函数"""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _notify_callbacks(self, log_type: str, message: str):
        """通知所有回调"""
        with self._lock:
            for callback in self._callbacks:
                try:
                    callback(log_type, message)
                except Exception:
                    pass
    
    def write(self, message: str):
        """写入消息"""
        if message.strip():
            self._notify_callbacks("stdout", message.rstrip())
        self._original_stdout.write(message)
    
    def flush(self):
        """刷新缓冲区"""
        self._original_stdout.flush()
    
    def start_capture(self):
        """开始捕获"""
        if not self._capturing:
            sys.stdout = self
            self._capturing = True
    
    def stop_capture(self):
        """停止捕获"""
        if self._capturing:
            sys.stdout = self._original_stdout
            self._capturing = False


class SessionLogger:
    """会话级别的日志记录器
    
    每个对话会话有独立的日志队列
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.logs: List[dict] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._active = True
    
    def add_log(self, log_type: str, message: str, source: str = "system"):
        """添加日志"""
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "type": log_type,
            "source": source,
            "message": message
        }
        self.logs.append(log_entry)
        
        # 非阻塞地放入队列
        try:
            self._queue.put_nowait(log_entry)
        except asyncio.QueueFull:
            pass
    
    async def get_log(self, timeout: float = 0.1) -> Optional[dict]:
        """获取日志（异步）"""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    def close(self):
        """关闭日志记录器"""
        self._active = False


# 全局控制台捕获器
_console_capture = ConsoleCapture()

# 会话日志管理
_session_loggers: dict[str, SessionLogger] = {}
_session_lock = threading.Lock()


def get_session_logger(session_id: str) -> SessionLogger:
    """获取或创建会话日志记录器"""
    with _session_lock:
        if session_id not in _session_loggers:
            _session_loggers[session_id] = SessionLogger(session_id)
        return _session_loggers[session_id]


def remove_session_logger(session_id: str):
    """移除会话日志记录器"""
    with _session_lock:
        if session_id in _session_loggers:
            _session_loggers[session_id].close()
            del _session_loggers[session_id]


@contextmanager
def capture_console_for_session(session_id: str):
    """上下文管理器：为特定会话捕获控制台输出
    
    Usage:
        with capture_console_for_session("session_123") as logger:
            print("This will be captured")
            # logger.logs 包含所有捕获的日志
    """
    logger = get_session_logger(session_id)
    
    def callback(log_type: str, message: str):
        logger.add_log(log_type, message, "console")
    
    _console_capture.add_callback(callback)
    _console_capture.start_capture()
    
    try:
        yield logger
    finally:
        _console_capture.remove_callback(callback)
        if not _console_capture._callbacks:
            _console_capture.stop_capture()
        remove_session_logger(session_id)


def log_to_session(session_id: str, message: str, log_type: str = "info", source: str = "system"):
    """向特定会话发送日志"""
    logger = get_session_logger(session_id)
    logger.add_log(log_type, message, source)
