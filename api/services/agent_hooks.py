# -*- coding: utf-8 -*-
"""AgentScope 钩子函数 - 捕获智能体执行信息"""
import os
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional, Callable, List
from pathlib import Path

# 日志目录
LOG_DIR = Path("./logs/agent_execution")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 回放日志目录
REPLAY_LOG_DIR = Path("./logs/agent_replay")
REPLAY_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 会话起始时间记录（用于计算相对时间戳）
_session_start_times: Dict[str, float] = {}

# 配置文件日志记录器
_file_logger: Optional[logging.Logger] = None
_session_loggers: Dict[str, logging.Logger] = {}

# 全局回调函数（用于 WebSocket 推送）
_global_callback: Optional[Callable[[str, str, Dict], None]] = None


def get_file_logger() -> logging.Logger:
    """获取文件日志记录器"""
    global _file_logger
    if _file_logger is None:
        _file_logger = logging.getLogger("agent_execution")
        _file_logger.setLevel(logging.DEBUG)
        
        # 创建每日日志文件
        log_file = LOG_DIR / f"agent_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        _file_logger.addHandler(handler)
        
        # 避免重复日志
        _file_logger.propagate = False
    
    return _file_logger


def get_session_logger(session_id: str) -> logging.Logger:
    """获取会话专用日志记录器"""
    if session_id not in _session_loggers:
        logger = logging.getLogger(f"agent_session_{session_id}")
        logger.setLevel(logging.DEBUG)
        
        log_file = LOG_DIR / f"session_{session_id}.log"
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        
        _session_loggers[session_id] = logger
    
    return _session_loggers[session_id]


def set_global_callback(callback: Optional[Callable[[str, str, Dict], None]]):
    """设置全局回调函数（用于 WebSocket 推送）"""
    global _global_callback
    _global_callback = callback


def log_agent_event(
    agent_name: str,
    event_type: str,
    data: Dict[str, Any],
    session_id: Optional[str] = None
):
    """记录智能体事件（JSON 格式，详细）
    
    Args:
        agent_name: 智能体名称
        event_type: 事件类型 (reasoning, acting, tool_call, tool_result, reply)
        data: 事件数据
        session_id: 会话ID（可选）
    """
    logger = get_file_logger()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "event": event_type,
        "data": data
    }
    
    # 写入文件日志
    log_message = json.dumps(log_entry, ensure_ascii=False)
    logger.info(log_message)
    
    # 如果有会话ID，也写入会话日志
    if session_id:
        session_logger = get_session_logger(session_id)
        session_logger.info(log_message)
    
    # 调用全局回调（WebSocket 推送）
    if _global_callback:
        try:
            _global_callback(agent_name, event_type, data)
        except Exception as e:
            logger.error(f"回调执行失败: {e}")


def log_agent_event_simple(agent_name: str, content: str, session_id: Optional[str] = None):
    """简化格式记录智能体输出（类似控制台格式）
    
    Args:
        agent_name: 智能体名称
        content: 输出内容
        session_id: 会话ID（可选）
    """
    logger = get_file_logger()
    # 格式: AgentName: content
    logger.info(f"{agent_name}: {content}")
    
    # 同时记录回放格式日志
    if session_id:
        log_replay_step(session_id, agent_name, content)


# ============= 回放日志函数 =============

def start_replay_session(session_id: str, agent_name: str, user_input: str = ""):
    """开始一个新的回放会话
    
    Args:
        session_id: 会话ID
        agent_name: 智能体名称
        user_input: 用户输入
    """
    _session_start_times[session_id] = time.time()
    
    # 创建回放日志文件
    replay_file = REPLAY_LOG_DIR / f"{session_id}.jsonl"
    
    # 写入会话元数据
    meta = {
        "type": "session_meta",
        "session_id": session_id,
        "agent_name": agent_name,
        "start_time": datetime.now().isoformat(),
        "user_input": user_input,
        "timestamp": 0
    }
    
    with open(replay_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")


def log_replay_step(
    session_id: str,
    agent_name: str,
    content: str,
    step_type: str = "ai_response"
):
    """记录回放步骤
    
    Args:
        session_id: 会话ID
        agent_name: 智能体名称
        content: 内容
        step_type: 步骤类型 (user_input, tool_call, tool_result, ai_response)
    """
    if session_id not in _session_start_times:
        _session_start_times[session_id] = time.time()
    
    # 计算相对时间戳
    relative_timestamp = time.time() - _session_start_times[session_id]
    
    # 解析 content 判断 step_type
    parsed_step_type = step_type
    parsed_content = content
    
    try:
        # 尝试解析 JSON 内容
        if content.startswith("[") or content.startswith("{"):
            import ast
            data = ast.literal_eval(content)
            if isinstance(data, list) and len(data) > 0:
                first_item = data[0]
                if isinstance(first_item, dict):
                    item_type = first_item.get("type", "")
                    if item_type == "tool_use":
                        parsed_step_type = "tool_call"
                        parsed_content = {
                            "name": first_item.get("name", ""),
                            "input": first_item.get("input", {})
                        }
                    elif item_type == "tool_result":
                        parsed_step_type = "tool_result"
                        output = first_item.get("output", [])
                        if isinstance(output, list) and len(output) > 0:
                            parsed_content = output[0].get("text", str(output))
                        else:
                            parsed_content = str(output)
                    elif item_type == "text":
                        parsed_step_type = "ai_response"
                        parsed_content = first_item.get("text", "")
    except:
        pass
    
    step = {
        "type": "step",
        "timestamp": round(relative_timestamp, 3),
        "step_type": parsed_step_type,
        "agent_name": agent_name,
        "content": parsed_content
    }
    
    replay_file = REPLAY_LOG_DIR / f"{session_id}.jsonl"
    with open(replay_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(step, ensure_ascii=False) + "\n")


def end_replay_session(session_id: str):
    """结束回放会话
    
    Args:
        session_id: 会话ID
    """
    if session_id in _session_start_times:
        duration = time.time() - _session_start_times[session_id]
        
        # 写入结束标记
        end_meta = {
            "type": "session_end",
            "session_id": session_id,
            "end_time": datetime.now().isoformat(),
            "duration": round(duration, 3)
        }
        
        replay_file = REPLAY_LOG_DIR / f"{session_id}.jsonl"
        with open(replay_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(end_meta, ensure_ascii=False) + "\n")
        
        del _session_start_times[session_id]


def get_replay_sessions() -> List[Dict]:
    """获取所有回放会话列表
    
    Returns:
        会话列表
    """
    sessions = []
    for file in REPLAY_LOG_DIR.glob("*.jsonl"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                first_line = f.readline()
                if first_line:
                    meta = json.loads(first_line)
                    if meta.get("type") == "session_meta":
                        # 读取最后一行获取 duration
                        lines = f.readlines()
                        duration = 0
                        step_count = 0
                        for line in lines:
                            try:
                                data = json.loads(line)
                                if data.get("type") == "session_end":
                                    duration = data.get("duration", 0)
                                elif data.get("type") == "step":
                                    step_count += 1
                            except:
                                pass
                        
                        sessions.append({
                            "session_id": meta.get("session_id"),
                            "agent_name": meta.get("agent_name"),
                            "start_time": meta.get("start_time"),
                            "user_input": meta.get("user_input", "")[:100],
                            "duration": duration,
                            "step_count": step_count
                        })
        except Exception as e:
            pass
    
    # 按时间倒序排列
    sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
    return sessions


def get_replay_data(session_id: str) -> Optional[Dict]:
    """获取回放数据
    
    Args:
        session_id: 会话ID
        
    Returns:
        回放数据
    """
    replay_file = REPLAY_LOG_DIR / f"{session_id}.jsonl"
    if not replay_file.exists():
        return None
    
    steps = []
    meta = {}
    duration = 0
    
    with open(replay_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "session_meta":
                    meta = data
                elif data.get("type") == "session_end":
                    duration = data.get("duration", 0)
                elif data.get("type") == "step":
                    steps.append(data)
            except:
                pass
    
    # 如果没有结束标记，估算 duration
    if duration == 0 and steps:
        duration = steps[-1].get("timestamp", 0)
    
    return {
        "session_id": session_id,
        "name": meta.get("agent_name", "Unknown"),
        "start_time": meta.get("start_time", ""),
        "user_input": meta.get("user_input", ""),
        "duration": duration,
        "steps": steps
    }


# ============= AgentScope 钩子函数 =============

def pre_reasoning_hook(self, kwargs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """推理前钩子 - 不输出日志（简化模式下跳过）"""
    # 简化模式下不输出 pre_reasoning
    return None


def post_reasoning_hook(self, kwargs: Dict[str, Any], output: Any) -> Any:
    """推理后钩子 - 不输出日志（简化模式下跳过，由 pre_print 捕获）"""
    # 简化模式下不输出 post_reasoning，由 pre_print 统一捕获
    return None


def pre_acting_hook(self, kwargs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """行动前钩子 - 不输出日志（简化模式下跳过，由 pre_print 捕获）"""
    # 简化模式下不输出 pre_acting，由 pre_print 统一捕获
    return None


def post_acting_hook(self, kwargs: Dict[str, Any], output: Any) -> Any:
    """行动后钩子 - 不输出日志（简化模式下跳过，由 pre_print 捕获）"""
    # 简化模式下不输出 post_acting，由 pre_print 统一捕获
    return None


def pre_print_hook(self, kwargs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """打印前钩子 - 只捕获最终完整的打印内容（last=True）"""
    # 只记录最终完整的内容，跳过流式中间状态
    is_last = kwargs.get("last", True)
    if isinstance(is_last, str):
        is_last = is_last.lower() == "true"
    
    if not is_last:
        return None  # 跳过中间状态
    
    content = ""
    if "msg" in kwargs:
        msg = kwargs["msg"]
        if hasattr(msg, 'content'):
            content = str(msg.content)
        else:
            content = str(msg)
    
    if content:
        # 获取 session_id（如果有的话）
        session_id = getattr(self, '_replay_session_id', None)
        
        # 简化格式输出
        log_agent_event_simple(
            agent_name=getattr(self, 'name', 'Unknown'),
            content=content,
            session_id=session_id
        )
    
    return None


def post_reply_hook(self, kwargs: Dict[str, Any], output: Any) -> Any:
    """回复后钩子 - 不输出日志（简化模式下跳过，由 pre_print 捕获）"""
    # 简化模式下不输出 post_reply，由 pre_print 统一捕获
    return None


def register_hooks_to_agent(agent):
    """为智能体注册所有钩子函数
    
    Args:
        agent: AgentScope ReActAgent 实例
    """
    try:
        # 注册实例级钩子
        agent.register_instance_hook(
            hook_type="pre_reasoning",
            hook_name="execution_logger_pre_reasoning",
            hook=pre_reasoning_hook,
        )
        agent.register_instance_hook(
            hook_type="post_reasoning",
            hook_name="execution_logger_post_reasoning",
            hook=post_reasoning_hook,
        )
        agent.register_instance_hook(
            hook_type="pre_acting",
            hook_name="execution_logger_pre_acting",
            hook=pre_acting_hook,
        )
        agent.register_instance_hook(
            hook_type="post_acting",
            hook_name="execution_logger_post_acting",
            hook=post_acting_hook,
        )
        agent.register_instance_hook(
            hook_type="pre_print",
            hook_name="execution_logger_pre_print",
            hook=pre_print_hook,
        )
        agent.register_instance_hook(
            hook_type="post_reply",
            hook_name="execution_logger_post_reply",
            hook=post_reply_hook,
        )
        print(f"[AgentHooks] 已为 {getattr(agent, 'name', 'Agent')} 注册执行日志钩子")
    except Exception as e:
        print(f"[AgentHooks] 注册钩子失败: {e}")


def register_hooks_to_class(agent_class):
    """为智能体类注册所有钩子函数（类级别）
    
    Args:
        agent_class: AgentScope Agent 类
    """
    try:
        agent_class.register_class_hook(
            hook_type="pre_reasoning",
            hook_name="execution_logger_pre_reasoning",
            hook=pre_reasoning_hook,
        )
        agent_class.register_class_hook(
            hook_type="post_reasoning",
            hook_name="execution_logger_post_reasoning",
            hook=post_reasoning_hook,
        )
        agent_class.register_class_hook(
            hook_type="pre_acting",
            hook_name="execution_logger_pre_acting",
            hook=pre_acting_hook,
        )
        agent_class.register_class_hook(
            hook_type="post_acting",
            hook_name="execution_logger_post_acting",
            hook=post_acting_hook,
        )
        agent_class.register_class_hook(
            hook_type="pre_print",
            hook_name="execution_logger_pre_print",
            hook=pre_print_hook,
        )
        agent_class.register_class_hook(
            hook_type="post_reply",
            hook_name="execution_logger_post_reply",
            hook=post_reply_hook,
        )
        print(f"[AgentHooks] 已为 {agent_class.__name__} 类注册执行日志钩子")
    except Exception as e:
        print(f"[AgentHooks] 注册类钩子失败: {e}")
