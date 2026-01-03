# -*- coding: utf-8 -*-
"""回放日志 API 路由"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from api.services.agent_hooks import (
    get_replay_sessions,
    get_replay_data,
    start_replay_session,
    end_replay_session
)

router = APIRouter(prefix="/api/replay", tags=["replay"])


class ReplaySessionResponse(BaseModel):
    """回放会话响应"""
    session_id: str
    agent_name: str
    start_time: str
    user_input: str
    duration: float
    step_count: int


class ReplayDataResponse(BaseModel):
    """回放数据响应"""
    session_id: str
    name: str
    start_time: str
    user_input: str
    duration: float
    steps: List[dict]


@router.get("/sessions", response_model=List[ReplaySessionResponse])
async def list_replay_sessions():
    """获取所有回放会话列表"""
    try:
        sessions = get_replay_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_replay(session_id: str):
    """获取指定会话的回放数据"""
    try:
        data = get_replay_data(session_id)
        if data is None:
            raise HTTPException(status_code=404, detail="会话不存在")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def delete_session_replay(session_id: str):
    """删除指定会话的回放数据"""
    from pathlib import Path
    try:
        replay_file = Path("./logs/agent_replay") / f"{session_id}.jsonl"
        if replay_file.exists():
            replay_file.unlink()
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="会话不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
