# -*- coding: utf-8 -*-
"""
智能体编排系统 API 服务

重构后的主入口文件，负责：
1. FastAPI 应用初始化
2. 路由注册
3. 配置加载
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import config
from api.services.agent_manager import AgentManager
from api.routers import execution


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    config.init_config()
    AgentManager.set_api_key(config.API_KEY)
    execution.set_predefined_workflows(config.predefined_workflows)
    
    print("\n" + "="*50)
    print("API 服务启动完成")
    print(f"工作流数量: {len(config.predefined_workflows)}")
    print(f"工作流列表: {list(config.predefined_workflows.keys())}")
    print("="*50 + "\n")
    
    yield
    
    # 关闭时执行（如有需要）
    print("API 服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(title="智能体编排系统 API", version="2.0.0", lifespan=lifespan)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
from api.routers import agents, workflows, menu, policy_qa, ocr, skill_creator, code_assistant, booking, token_stats, upload, email_trigger, sandbox

app.include_router(agents.router)
app.include_router(workflows.router)
app.include_router(execution.router)
app.include_router(menu.router)
app.include_router(policy_qa.router)
app.include_router(ocr.router)
app.include_router(skill_creator.router)
app.include_router(code_assistant.router)
app.include_router(booking.router)
app.include_router(token_stats.router)
app.include_router(upload.router)
app.include_router(email_trigger.router)
app.include_router(sandbox.router)


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
