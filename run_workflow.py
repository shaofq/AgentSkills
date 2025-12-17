# -*- coding: utf-8 -*-
"""
工作流执行器

从导出的 JSON 配置文件运行智能体工作流。

用法:
    python run_workflow.py workflow.json "你的输入内容"
    python run_workflow.py workflow.json -i  # 交互模式
"""
import asyncio
import json
import os
import sys
from typing import Dict, List, Any

from agentscope.message import Msg
from agents.base import BaseAgent

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-547e87e8934f4737b972199090958ff2")


def load_workflow(filepath: str) -> dict:
    """加载工作流配置文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_execution_order(nodes: List[dict], edges: List[dict]) -> List[str]:
    """根据边计算节点执行顺序（拓扑排序）"""
    in_degree = {n["id"]: 0 for n in nodes}
    adj = {n["id"]: [] for n in nodes}
    
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source and target and source in adj and target in in_degree:
            adj[source].append(target)
            in_degree[target] += 1
    
    queue = [n for n in in_degree if in_degree[n] == 0]
    order = []
    
    while queue:
        node = queue.pop(0)
        order.append(node)
        for neighbor in adj.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return order


def create_agents(nodes: List[dict]) -> Dict[str, Any]:
    """根据节点配置创建智能体实例"""
    agents = {}
    
    for node in nodes:
        if node.get("type") != "agent":
            continue
        
        data = node.get("data", {})
        config = data.get("agentConfig", {})
        
        if not config:
            continue
        
        skills = config.get("skills", [])
        skill_paths = [f"./skill/{s}" for s in skills if s]
        
        # 获取高级参数
        temperature = config.get("temperature", 0.7)
        enable_thinking = config.get("enableThinking", False)
        stream = config.get("stream", True)
        custom_params = config.get("customParams", [])
        input_variables = config.get("inputVariables", [])
        
        try:
            agent = BaseAgent(
                name=config.get("name", node["id"]),
                sys_prompt=config.get("systemPrompt", ""),
                skills=skill_paths,
                api_key=API_KEY,
                model_name=config.get("model", "qwen3-max"),
                max_iters=config.get("maxIters", 30),
            )
            
            # 存储额外配置供执行时使用
            agent_info = {
                "agent": agent,
                "config": config,
                "temperature": temperature,
                "enable_thinking": enable_thinking,
                "stream": stream,
                "custom_params": {p["key"]: parse_param_value(p) for p in custom_params if p.get("key")},
                "input_variables": input_variables,
            }
            agents[node["id"]] = agent_info
            
            print(f"  ✓ 创建智能体: {config.get('name', node['id'])}")
            if custom_params:
                print(f"    自定义参数: {len(custom_params)} 个")
            if input_variables:
                print(f"    输入变量: {[v.get('name') for v in input_variables]}")
        except Exception as e:
            print(f"  ✗ 创建智能体失败 {node['id']}: {e}")
    
    return agents


def parse_param_value(param: dict) -> Any:
    """解析自定义参数值"""
    value = param.get("value", "")
    param_type = param.get("type", "string")
    
    if param_type == "number":
        try:
            return float(value) if "." in value else int(value)
        except:
            return 0
    elif param_type == "boolean":
        return value.lower() in ("true", "1", "yes")
    elif param_type == "json":
        try:
            return json.loads(value)
        except:
            return {}
    return value


def substitute_variables(text: str, variables: dict) -> str:
    """替换文本中的变量占位符 {{变量名}}"""
    import re
    pattern = r'\{\{(\w+)\}\}'
    
    def replacer(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))
    
    return re.sub(pattern, replacer, text)


def build_adjacency_graph(nodes: List[dict], edges: List[dict]) -> dict:
    """构建节点邻接图"""
    graph = {n["id"]: [] for n in nodes}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        source_handle = edge.get("sourceHandle")
        if source and target and source in graph:
            graph[source].append({
                "target": target,
                "handle": source_handle  # 用于条件分支
            })
    return graph


async def execute_node(node: dict, agents: dict, current_input: str, context: dict) -> str:
    """执行单个节点"""
    node_type = node.get("type")
    node_id = node.get("id")
    node_label = node.get("data", {}).get("label", node_id)
    
    if node_type == "input":
        print(f"\n[{node_label}] 接收输入")
        return current_input
        
    elif node_type == "output":
        print(f"\n[{node_label}] 输出结果")
        return current_input
        
    elif node_type == "agent" and node_id in agents:
        agent_info = agents[node_id]
        agent = agent_info["agent"]
        custom_params = agent_info.get("custom_params", {})
        
        print(f"\n[{node_label}] 处理中...")
        if custom_params:
            print(f"  参数: {custom_params}")
        
        try:
            processed_input = current_input
            if custom_params:
                param_context = "\n".join([f"- {k}: {v}" for k, v in custom_params.items()])
                processed_input = f"参数配置:\n{param_context}\n\n用户请求:\n{current_input}"
            
            response = await agent(Msg("user", processed_input, "user"))
            output = response.content if hasattr(response, "content") else str(response)
            print(f"  ✓ 完成")
            return output
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            return current_input
            
    elif node_type == "condition":
        # 条件节点：评估条件并返回结果
        condition_config = node.get("data", {}).get("conditionConfig", {})
        condition_expr = condition_config.get("expression", "")
        
        print(f"\n[{node_label}] 条件分支")
        print(f"  条件表达式: {condition_expr or '默认 True'}")
        
        # 简单的条件评估：检查输入中是否包含关键词
        if condition_expr:
            result = condition_expr.lower() in current_input.lower()
        else:
            result = True  # 默认走 True 分支
        
        context["condition_result"] = result
        print(f"  结果: {'True' if result else 'False'}")
        return current_input
        
    elif node_type == "parallel":
        # 并行节点：标记为并行执行点
        print(f"\n[{node_label}] 并行执行点")
        context["parallel_mode"] = True
        return current_input
    
    return current_input


async def execute_workflow(workflow: dict, user_input: str) -> str:
    """执行工作流（支持条件分支和并行执行）"""
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])
    
    print(f"\n{'='*60}")
    print(f"工作流: {workflow.get('name', '未命名')}")
    print(f"{'='*60}")
    
    # 创建智能体
    print("\n[1/3] 初始化智能体...")
    agents = create_agents(nodes)
    
    if not agents:
        print("警告: 没有找到可执行的智能体节点")
    
    # 构建邻接图
    print("\n[2/3] 构建执行图...")
    graph = build_adjacency_graph(nodes, edges)
    
    # 找到起始节点（input 节点）
    start_nodes = [n for n in nodes if n.get("type") == "input"]
    if not start_nodes:
        print("错误: 未找到输入节点")
        return user_input
    
    # 执行工作流
    print("\n[3/3] 开始执行...")
    print(f"  输入: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
    print("-" * 60)
    
    # 使用 BFS 遍历执行
    context = {}  # 执行上下文
    node_outputs = {}  # 存储每个节点的输出
    visited = set()
    
    async def execute_from_node(node_id: str, input_data: str):
        """从指定节点开始执行"""
        if node_id in visited:
            return node_outputs.get(node_id, input_data)
        
        visited.add(node_id)
        node = next((n for n in nodes if n["id"] == node_id), None)
        if not node:
            return input_data
        
        # 执行当前节点
        output = await execute_node(node, agents, input_data, context)
        node_outputs[node_id] = output
        
        # 获取下游节点
        next_nodes = graph.get(node_id, [])
        
        if not next_nodes:
            return output
        
        # 处理条件分支
        if node.get("type") == "condition":
            condition_result = context.get("condition_result", True)
            target_handle = "true" if condition_result else "false"
            
            # 找到对应分支的目标节点
            for next_node in next_nodes:
                if next_node["handle"] == target_handle:
                    return await execute_from_node(next_node["target"], output)
            
            # 如果没有找到对应分支，执行第一个
            if next_nodes:
                return await execute_from_node(next_nodes[0]["target"], output)
        
        # 处理并行执行
        elif node.get("type") == "parallel" or context.get("parallel_mode"):
            print(f"  并行执行 {len(next_nodes)} 个分支")
            
            # 并行执行所有分支
            tasks = [execute_from_node(n["target"], output) for n in next_nodes]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并结果
            valid_results = [r for r in results if isinstance(r, str)]
            if valid_results:
                merged_output = "\n\n--- 并行执行结果合并 ---\n\n".join(valid_results)
                return merged_output
            return output
        
        # 串行执行
        else:
            current_output = output
            for next_node in next_nodes:
                current_output = await execute_from_node(next_node["target"], current_output)
            return current_output
    
    # 从起始节点开始执行
    final_output = user_input
    for start_node in start_nodes:
        final_output = await execute_from_node(start_node["id"], user_input)
    
    print("\n" + "=" * 60)
    print("执行完成")
    print("=" * 60)
    
    return final_output


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n示例:")
        print("  python run_workflow.py my_workflow.json \"请帮我生成一个用户管理页面\"")
        print("  python run_workflow.py my_workflow.json -i")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    
    if not os.path.exists(workflow_file):
        print(f"错误: 文件不存在 - {workflow_file}")
        sys.exit(1)
    
    # 加载工作流
    print(f"加载工作流配置: {workflow_file}")
    workflow = load_workflow(workflow_file)
    
    # 交互模式
    if len(sys.argv) > 2 and sys.argv[2] == "-i":
        print("\n进入交互模式 (输入 'quit' 退出)")
        while True:
            try:
                user_input = input("\n请输入: ").strip()
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("再见!")
                    break
                if not user_input:
                    continue
                result = await execute_workflow(workflow, user_input)
                print(f"\n最终输出:\n{result}")
            except KeyboardInterrupt:
                print("\n再见!")
                break
    else:
        # 单次执行模式
        user_input = sys.argv[2] if len(sys.argv) > 2 else "请开始执行"
        result = await execute_workflow(workflow, user_input)
        print(f"\n最终输出:\n{result}")


if __name__ == "__main__":
    asyncio.run(main())
