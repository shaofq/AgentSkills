# -*- coding: utf-8 -*-
"""
图算法工具

提供工作流图相关的算法，如拓扑排序。
"""
from typing import List, Dict


def get_execution_order(nodes: List[dict], edges: List[dict]) -> List[str]:
    """
    根据边计算节点执行顺序（拓扑排序）。
    
    Args:
        nodes: 节点列表，每个节点包含 id
        edges: 边列表，每条边包含 source 和 target
    
    Returns:
        按执行顺序排列的节点 ID 列表
    """
    # 构建入度表和邻接表
    in_degree = {n["id"]: 0 for n in nodes}
    adj = {n["id"]: [] for n in nodes}
    
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source and target and source in adj and target in in_degree:
            adj[source].append(target)
            in_degree[target] += 1
    
    # Kahn 算法进行拓扑排序
    queue = [n for n in in_degree if in_degree[n] == 0]
    order = []
    
    while queue:
        node = queue.pop(0)
        order.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return order


def build_adjacency_graph(nodes: List[dict], edges: List[dict]) -> Dict[str, List[dict]]:
    """
    构建邻接图。
    
    Args:
        nodes: 节点列表
        edges: 边列表
    
    Returns:
        邻接图，key 为节点 ID，value 为下游节点信息列表
    """
    graph = {n["id"]: [] for n in nodes}
    
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        source_handle = edge.get("sourceHandle")
        
        if source and target and source in graph:
            graph[source].append({
                "target": target,
                "handle": source_handle
            })
    
    return graph
