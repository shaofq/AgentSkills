#!/usr/bin/env python3
# 测试工作流加载
import json
import os

predefined_workflows = {}

def load_predefined_workflows():
    """加载预定义工作流"""
    workflow_dir = "./workflows"
    if os.path.exists(workflow_dir):
        print(f"工作流目录存在: {workflow_dir}")
        files = os.listdir(workflow_dir)
        print(f"目录中的文件: {files}")
        
        for filename in files:
            if filename.endswith('.json'):
                filepath = os.path.join(workflow_dir, filename)
                print(f"\n处理文件: {filepath}")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                        workflow_name = filename.replace('.json', '')
                        predefined_workflows[workflow_name] = workflow
                        print(f"✓ 加载成功: {workflow_name}")
                        print(f"  - 节点数: {len(workflow.get('nodes', []))}")
                        print(f"  - 边数: {len(workflow.get('edges', []))}")
                except Exception as e:
                    print(f"✗ 加载失败 {filename}: {e}")
    else:
        print(f"工作流目录不存在: {workflow_dir}")

load_predefined_workflows()

print(f"\n最终结果:")
print(f"加载的工作流数量: {len(predefined_workflows)}")
print(f"工作流名称: {list(predefined_workflows.keys())}")
