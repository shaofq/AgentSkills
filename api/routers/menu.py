# -*- coding: utf-8 -*-
"""
菜单和技能相关路由
"""
from fastapi import APIRouter, HTTPException

from api.models.request import MenuBindingUpdate
from api import config
from agents.base import get_available_skills

router = APIRouter(prefix="/api", tags=["菜单配置"])


@router.get("/menu-bindings")
async def get_menu_bindings():
    """获取菜单绑定配置"""
    return config.menu_bindings_config


@router.get("/skills")
async def get_skills():
    """获取所有可用的技能列表"""
    skills = get_available_skills()
    return {"skills": skills, "total": len(skills)}


@router.post("/menu-bindings")
async def update_menu_binding(request: MenuBindingUpdate):
    """更新菜单绑定的工作流"""
    all_menus = config.get_all_menus()
    
    for menu in all_menus:
        if menu.get("id") == request.menuId:
            menu["workflowName"] = request.workflowName
            if config.save_menu_bindings():
                print(f"[MenuBindings] 更新菜单 {request.menuId} 绑定工作流: {request.workflowName}")
                return {"success": True, "message": "更新成功"}
            else:
                raise HTTPException(status_code=500, detail="保存配置失败")
    
    raise HTTPException(status_code=404, detail=f"菜单 {request.menuId} 不存在")


@router.get("/workflowsquery")
async def get_workflows_query():
    """获取所有已加载的预定义工作流列表，包含绑定的菜单信息"""
    print(f"\n[API /api/workflowsquery] 被调用")
    workflows = []
    
    all_menus = config.get_all_menus()
    
    # 构建工作流名称到菜单的映射
    workflow_to_menus = {}
    for menu in all_menus:
        wf_name = menu.get("workflowName")
        if wf_name:
            if wf_name not in workflow_to_menus:
                workflow_to_menus[wf_name] = []
            workflow_to_menus[wf_name].append({
                "id": menu.get("id"),
                "name": menu.get("name"),
                "icon": menu.get("icon")
            })
    
    for workflow_name, workflow in config.predefined_workflows.items():
        bound_menus = workflow_to_menus.get(workflow_name, [])
        workflow_info = {
            "name": workflow_name,
            "title": workflow.get("name", workflow_name),
            "description": workflow.get("description", ""),
            "nodeCount": len(workflow.get("nodes", [])),
            "edgeCount": len(workflow.get("edges", [])),
            "boundMenus": bound_menus
        }
        workflows.append(workflow_info)
    
    print(f"[API] 返回 {len(workflows)} 个工作流")
    return {"workflows": workflows, "total": len(workflows)}


@router.get("/workflows/debug")
async def debug_workflows():
    """调试：查看 predefined_workflows 的原始内容"""
    return {
        "keys": list(config.predefined_workflows.keys()),
        "count": len(config.predefined_workflows),
        "raw": config.predefined_workflows
    }
