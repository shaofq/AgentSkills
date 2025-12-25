"""
沙箱录制服务 - 录制和回放智能体操作
"""
import os
import json
import time
import uuid
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class RecordingStep:
    """录制步骤"""
    timestamp: float  # 时间戳
    step_type: str  # 类型: user_input, tool_call, tool_result, ai_response
    content: Any  # 内容
    screenshot: Optional[str] = None  # base64 截图
    tool_name: Optional[str] = None  # 工具名称
    tool_input: Optional[Dict] = None  # 工具输入参数
    tool_output: Optional[str] = None  # 工具原始输出
    file_content: Optional[str] = None  # 文件内容（用于file_read/file_write）
    shell_command: Optional[str] = None  # Shell 命令
    shell_output: Optional[str] = None  # Shell 输出


@dataclass
class Recording:
    """录制会话"""
    id: str
    name: str
    created_at: str
    duration: float = 0
    steps: List[Dict] = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []


class RecordingService:
    """录制服务"""
    
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'recordings')
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前录制会话
        self._current_recording: Optional[Recording] = None
        self._start_time: float = 0
    
    def start_recording(self, name: str = None) -> str:
        """开始新录制"""
        recording_id = str(uuid.uuid4())[:8]
        if name is None:
            name = f"录制_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self._current_recording = Recording(
            id=recording_id,
            name=name,
            created_at=datetime.now().isoformat(),
            steps=[]
        )
        self._start_time = time.time()
        
        return recording_id
    
    def stop_recording(self) -> Optional[Dict]:
        """停止录制并保存"""
        if self._current_recording is None:
            return None
        
        self._current_recording.duration = time.time() - self._start_time
        
        # 保存到文件
        recording_data = asdict(self._current_recording)
        file_path = self.storage_dir / f"{self._current_recording.id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(recording_data, f, ensure_ascii=False, indent=2)
        
        result = recording_data
        self._current_recording = None
        self._start_time = 0
        
        return result
    
    def add_step(
        self, 
        step_type: str, 
        content: Any, 
        screenshot: str = None,
        tool_name: str = None,
        tool_input: Dict = None,
        tool_output: str = None,
        file_content: str = None,
        shell_command: str = None,
        shell_output: str = None
    ) -> bool:
        """添加录制步骤
        
        Args:
            step_type: 步骤类型 (user_input, tool_call, ai_response)
            content: 内容描述
            screenshot: base64 截图
            tool_name: 工具名称
            tool_input: 工具输入参数
            tool_output: 工具原始输出
            file_content: 文件内容（用于file_read/file_write）
            shell_command: Shell 命令
            shell_output: Shell 输出
        """
        if self._current_recording is None:
            return False
        
        step = RecordingStep(
            timestamp=time.time() - self._start_time,
            step_type=step_type,
            content=content,
            screenshot=screenshot,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            file_content=file_content,
            shell_command=shell_command,
            shell_output=shell_output
        )
        
        self._current_recording.steps.append(asdict(step))
        return True
    
    def is_recording(self) -> bool:
        """是否正在录制"""
        return self._current_recording is not None
    
    def get_current_recording_id(self) -> Optional[str]:
        """获取当前录制 ID"""
        if self._current_recording:
            return self._current_recording.id
        return None
    
    def list_recordings(self) -> List[Dict]:
        """列出所有录制"""
        recordings = []
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recordings.append({
                        'id': data['id'],
                        'name': data['name'],
                        'created_at': data['created_at'],
                        'duration': data.get('duration', 0),
                        'steps_count': len(data.get('steps', []))
                    })
            except Exception:
                pass
        
        # 按创建时间倒序
        recordings.sort(key=lambda x: x['created_at'], reverse=True)
        return recordings
    
    def get_recording(self, recording_id: str) -> Optional[Dict]:
        """获取录制详情"""
        file_path = self.storage_dir / f"{recording_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_recording(self, recording_id: str) -> bool:
        """删除录制"""
        file_path = self.storage_dir / f"{recording_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False


# 全局实例
_recording_service: Optional[RecordingService] = None


def get_recording_service() -> RecordingService:
    """获取录制服务实例"""
    global _recording_service
    if _recording_service is None:
        _recording_service = RecordingService()
    return _recording_service
