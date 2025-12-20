# -*- coding: utf-8 -*-
"""
配置模块

负责加载和管理应用配置，包括：
- API 密钥
- 菜单绑定配置
- 预定义工作流
"""
import os
import json
from typing import Dict

# API 密钥
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-547e87e8934f4737b972199090958ff2")

# 预定义工作流存储
predefined_workflows: Dict[str, dict] = {}

# 菜单绑定配置
menu_bindings_config: dict = {}


def load_menu_bindings():
    """加载菜单绑定配置"""
    global menu_bindings_config
    config_path = "./config/menu_bindings.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                menu_bindings_config = json.load(f)
                if "menuGroups" in menu_bindings_config:
                    total = sum(len(g.get("menus", [])) for g in menu_bindings_config.get("menuGroups", []))
                    print(f"[MenuBindings] 加载菜单绑定配置(分组格式): {total} 个菜单项")
                elif "menus" in menu_bindings_config:
                    print(f"[MenuBindings] 加载菜单绑定配置: {len(menu_bindings_config.get('menus', []))} 个菜单项")
        except Exception as e:
            print(f"[MenuBindings] 加载菜单绑定配置失败: {e}")
    else:
        print(f"[MenuBindings] 配置文件不存在: {config_path}")


def load_predefined_workflows():
    """加载预定义工作流"""
    global predefined_workflows
    workflow_dir = "./workflows"
    if os.path.exists(workflow_dir):
        for filename in os.listdir(workflow_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(workflow_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                        workflow_name = filename.replace('.json', '')
                        predefined_workflows[workflow_name] = workflow
                        print(f"[Workflow] 加载预定义工作流: {workflow_name}")
                except Exception as e:
                    print(f"[Workflow] 加载工作流失败 {filename}: {e}")


def get_all_menus():
    """获取所有菜单项（支持分组格式）"""
    all_menus = []
    if "menuGroups" in menu_bindings_config:
        for group in menu_bindings_config.get("menuGroups", []):
            all_menus.extend(group.get("menus", []))
    else:
        all_menus = menu_bindings_config.get("menus", [])
    return all_menus


def save_menu_bindings():
    """保存菜单绑定配置"""
    config_path = "./config/menu_bindings.json"
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(menu_bindings_config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[MenuBindings] 保存配置失败: {e}")
        return False


def init_config():
    """初始化配置"""
    load_predefined_workflows()
    load_menu_bindings()
    print(f"[Startup] 工作流加载完成，共 {len(predefined_workflows)} 个: {list(predefined_workflows.keys())}")
