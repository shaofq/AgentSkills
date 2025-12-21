"""
Token 消耗统计 API
记录和统计大模型调用的 Token 消耗
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import json
import os

router = APIRouter(prefix="/api/token-stats", tags=["token-stats"])

# Token 日志文件路径
TOKEN_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "token_logs.json")

# 确保数据目录存在
os.makedirs(os.path.dirname(TOKEN_LOG_FILE), exist_ok=True)


class TokenLogEntry(BaseModel):
    """Token 日志条目"""
    timestamp: str
    agent_id: str
    agent_name: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TokenLogRequest(BaseModel):
    """记录 Token 消耗请求"""
    agent_id: str
    agent_name: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TokenStats(BaseModel):
    """Token 统计数据"""
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    call_count: int
    by_agent: dict
    by_model: dict
    by_date: dict


def load_token_logs() -> List[dict]:
    """加载 Token 日志"""
    if not os.path.exists(TOKEN_LOG_FILE):
        return []
    try:
        with open(TOKEN_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_token_logs(logs: List[dict]):
    """保存 Token 日志"""
    with open(TOKEN_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


@router.post("/log")
async def log_token_usage(request: TokenLogRequest):
    """记录 Token 消耗"""
    logs = load_token_logs()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "agent_id": request.agent_id,
        "agent_name": request.agent_name,
        "model": request.model,
        "prompt_tokens": request.prompt_tokens,
        "completion_tokens": request.completion_tokens,
        "total_tokens": request.total_tokens,
        "user_id": request.user_id,
        "session_id": request.session_id,
    }
    
    logs.append(entry)
    save_token_logs(logs)
    
    return {"success": True, "message": "Token usage logged"}


@router.get("/stats")
async def get_token_stats(days: int = 30):
    """获取 Token 统计数据"""
    logs = load_token_logs()
    
    # 过滤指定天数内的日志
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered_logs = []
    for log in logs:
        try:
            log_date = datetime.fromisoformat(log["timestamp"])
            if log_date >= cutoff_date:
                filtered_logs.append(log)
        except (ValueError, KeyError):
            continue
    
    # 统计数据
    total_tokens = 0
    prompt_tokens = 0
    completion_tokens = 0
    by_agent = {}
    by_model = {}
    by_date = {}
    
    for log in filtered_logs:
        total_tokens += log.get("total_tokens", 0)
        prompt_tokens += log.get("prompt_tokens", 0)
        completion_tokens += log.get("completion_tokens", 0)
        
        # 按智能体统计
        agent_id = log.get("agent_id", "unknown")
        agent_name = log.get("agent_name", "未知")
        if agent_id not in by_agent:
            by_agent[agent_id] = {
                "name": agent_name,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "call_count": 0
            }
        by_agent[agent_id]["total_tokens"] += log.get("total_tokens", 0)
        by_agent[agent_id]["prompt_tokens"] += log.get("prompt_tokens", 0)
        by_agent[agent_id]["completion_tokens"] += log.get("completion_tokens", 0)
        by_agent[agent_id]["call_count"] += 1
        
        # 按模型统计
        model = log.get("model", "unknown")
        if model not in by_model:
            by_model[model] = {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "call_count": 0
            }
        by_model[model]["total_tokens"] += log.get("total_tokens", 0)
        by_model[model]["prompt_tokens"] += log.get("prompt_tokens", 0)
        by_model[model]["completion_tokens"] += log.get("completion_tokens", 0)
        by_model[model]["call_count"] += 1
        
        # 按日期统计
        try:
            date_str = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d")
            if date_str not in by_date:
                by_date[date_str] = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "call_count": 0
                }
            by_date[date_str]["total_tokens"] += log.get("total_tokens", 0)
            by_date[date_str]["prompt_tokens"] += log.get("prompt_tokens", 0)
            by_date[date_str]["completion_tokens"] += log.get("completion_tokens", 0)
            by_date[date_str]["call_count"] += 1
        except (ValueError, KeyError):
            continue
    
    return {
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "call_count": len(filtered_logs),
        "by_agent": by_agent,
        "by_model": by_model,
        "by_date": dict(sorted(by_date.items()))
    }


@router.get("/logs")
async def get_token_logs(limit: int = 100, offset: int = 0):
    """获取 Token 日志列表"""
    logs = load_token_logs()
    
    # 按时间倒序排列
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # 分页
    total = len(logs)
    paginated_logs = logs[offset:offset + limit]
    
    return {
        "total": total,
        "logs": paginated_logs,
        "limit": limit,
        "offset": offset
    }


@router.delete("/clear")
async def clear_token_logs():
    """清空 Token 日志"""
    save_token_logs([])
    return {"success": True, "message": "Token logs cleared"}
