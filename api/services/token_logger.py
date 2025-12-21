# -*- coding: utf-8 -*-
"""
Token 消耗记录服务

在大模型调用后记录 Token 消耗。
"""
import json
import os
from datetime import datetime
from typing import Optional

# Token 日志文件路径
TOKEN_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "token_logs.json")

# 确保数据目录存在
os.makedirs(os.path.dirname(TOKEN_LOG_FILE), exist_ok=True)


def load_token_logs() -> list:
    """加载 Token 日志"""
    if not os.path.exists(TOKEN_LOG_FILE):
        return []
    try:
        with open(TOKEN_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_token_logs(logs: list):
    """保存 Token 日志"""
    with open(TOKEN_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def log_token_usage(
    agent_id: str,
    agent_name: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """
    记录 Token 消耗
    
    Args:
        agent_id: 智能体 ID
        agent_name: 智能体名称
        model: 模型名称
        prompt_tokens: 输入 Token 数
        completion_tokens: 输出 Token 数
        total_tokens: 总 Token 数
        user_id: 用户 ID（可选）
        session_id: 会话 ID（可选）
    """
    logs = load_token_logs()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": agent_id,
        "agent_name": agent_name,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "user_id": user_id,
        "session_id": session_id,
    }
    
    logs.append(entry)
    save_token_logs(logs)
    
    print(f"[TokenLogger] 记录 Token 消耗: {agent_name} ({model}) - 输入: {prompt_tokens}, 输出: {completion_tokens}, 总计: {total_tokens}")


def estimate_tokens(text: str) -> int:
    """
    估算文本的 Token 数量
    
    简单估算：中文约 1.5 字符/token，英文约 4 字符/token
    这是一个粗略估算，实际 Token 数可能有所不同
    """
    if not text:
        return 0
    
    # 统计中文字符和其他字符
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    
    # 中文约 1.5 字符/token，其他约 4 字符/token
    estimated = int(chinese_chars / 1.5 + other_chars / 4)
    return max(1, estimated)


def log_agent_call(
    agent_id: str,
    agent_name: str,
    model: str,
    input_text: str,
    output_text: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
):
    """
    记录智能体调用（自动估算 Token）
    
    Args:
        agent_id: 智能体 ID
        agent_name: 智能体名称
        model: 模型名称
        input_text: 输入文本
        output_text: 输出文本
        user_id: 用户 ID（可选）
        session_id: 会话 ID（可选）
    """
    prompt_tokens = estimate_tokens(input_text)
    completion_tokens = estimate_tokens(output_text)
    total_tokens = prompt_tokens + completion_tokens
    
    log_token_usage(
        agent_id=agent_id,
        agent_name=agent_name,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        user_id=user_id,
        session_id=session_id,
    )
