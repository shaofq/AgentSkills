# -*- coding: utf-8 -*-
"""
多智能体系统主入口

这是一个多智能体架构示例，展示如何：
1. 创建多个专业智能体
2. 使用路由智能体分发任务
3. 协调智能体协作
"""
import asyncio
import os

from agentscope.model import DashScopeChatModel
from agentscope.message import Msg

from agents.base import BaseAgent
from agents.router import RouterAgent


# API Key 配置
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "sk-547e87e8934f4737b972199090958ff2")


async def main():
    """多智能体系统主入口"""
    
    print("=" * 60)
    print("多智能体系统启动")
    print("=" * 60)
    
    # 1. 创建专业智能体
    print("\n[系统] 初始化专业智能体...")
    
    # 代码生成智能体
    code_agent = BaseAgent(
        name="CodeMaster",
        sys_prompt="""你是一个专业的代码生成助手 CodeMaster。
你的专长是生成 amis 低代码 JSON 配置、编写前端组件代码。
使用装备的技能来查阅文档和示例，生成符合规范的代码。""",
        skills=["./skill/amis-code-assistant"],
        api_key=API_KEY,
        max_iters=30,
    )
    print("  ✓ CodeMaster (代码生成) 已就绪")
    
    # PPT制作智能体
    pptx_agent = BaseAgent(
        name="SlideCreator",
        sys_prompt="""你是一个专业的演示文稿制作助手 SlideCreator。
你的专长是创建和编辑 PowerPoint 演示文稿。
使用装备的技能来完成 PPT 相关任务。""",
        skills=["./skill/pptx"],
        api_key=API_KEY,
        max_iters=30,
    )
    print("  ✓ SlideCreator (PPT制作) 已就绪")
    
    # 2. 创建路由智能体
    print("\n[系统] 初始化路由智能体...")
    
    agents = {
        "code_agent": code_agent,
        "pptx_agent": pptx_agent,
    }
    
    router = RouterAgent(
        agents=agents,
        api_key=API_KEY,
    )
    print("  ✓ Router (路由) 已就绪")
    
    print("\n" + "=" * 60)
    print("系统就绪，开始处理请求")
    print("=" * 60)
    
    # 3. 测试请求
    test_requests = [
        "请帮我生成一个用户管理页面的amis配置，需要包含用户列表和新增功能。",
        # "请帮我创建一个产品介绍的PPT。",
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{'='*60}")
        print(f"请求 {i}: {request}")
        print("=" * 60)
        
        response = await router(Msg("user", request, "user"))
        
        print(f"\n[完成] 请求 {i} 处理完毕")


async def sequential_demo():
    """串行协作示例：先生成代码，再制作PPT展示"""
    
    print("=" * 60)
    print("串行协作示例")
    print("=" * 60)
    
    # 初始化智能体
    code_agent = BaseAgent(
        name="CodeMaster",
        sys_prompt="""你是一个专业的代码生成助手。使用装备的技能生成 amis 配置代码。
完成后，请总结你生成的代码的主要功能和特点，以便下一个智能体使用。""",
        skills=["./skill/amis-code-assistant"],
        api_key=API_KEY,
        max_iters=30,
    )
    
    pptx_agent = BaseAgent(
        name="SlideCreator",
        sys_prompt="""你是一个专业的PPT制作助手。
你会收到前一个智能体的输出，请基于这些内容创建演示文稿。""",
        skills=["./skill/pptx"],
        api_key=API_KEY,
        max_iters=30,
    )
    
    router = RouterAgent(
        agents={"code_agent": code_agent, "pptx_agent": pptx_agent},
        api_key=API_KEY,
    )
    
    print("\n[示例] 串行协作：先生成用户管理代码，再制作功能介绍PPT")
    print("-" * 60)
    
    # 串行协作：code_agent -> pptx_agent
    await router.sequential(
        Msg("user", "设计一个用户管理系统的amis配置，包含用户列表、新增、编辑、删除功能", "user"),
        ["code_agent", "pptx_agent"]
    )
    
    print("\n[完成] 串行协作示例结束")


async def parallel_demo():
    """并行协作示例：同时让多个智能体处理"""
    
    print("=" * 60)
    print("并行协作示例")
    print("=" * 60)
    
    # 初始化智能体
    code_agent = BaseAgent(
        name="CodeMaster",
        sys_prompt="""你是一个专业的代码生成助手。使用装备的技能生成 amis 配置代码。""",
        skills=["./skill/amis-code-assistant"],
        api_key=API_KEY,
        max_iters=30,
    )
    
    pptx_agent = BaseAgent(
        name="SlideCreator",
        sys_prompt="""你是一个专业的PPT制作助手。使用装备的技能创建演示文稿。""",
        skills=["./skill/pptx"],
        api_key=API_KEY,
        max_iters=30,
    )
    
    router = RouterAgent(
        agents={"code_agent": code_agent, "pptx_agent": pptx_agent},
        api_key=API_KEY,
    )
    
    print("\n[示例] 并行协作：同时生成代码和PPT")
    print("-" * 60)
    
    # 并行协作：同时执行
    results = await router.parallel(
        Msg("user", "创建一个产品介绍", "user"),
        ["code_agent", "pptx_agent"]
    )
    
    print(f"\n[完成] 并行协作示例结束，收到 {len(results)} 个响应")


async def interactive_mode():
    """交互模式 - 持续接收用户输入"""
    
    print("=" * 60)
    print("多智能体系统 - 交互模式")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'seq' 测试串行协作")
    print("输入 'par' 测试并行协作")
    print("=" * 60)
    
    # 初始化智能体
    code_agent = BaseAgent(
        name="CodeMaster",
        sys_prompt="""你是一个专业的代码生成助手。使用装备的技能生成 amis 配置代码。""",
        skills=["./skill/amis-code-assistant"],
        api_key=API_KEY,
        max_iters=30,
    )
    
    pptx_agent = BaseAgent(
        name="SlideCreator",
        sys_prompt="""你是一个专业的PPT制作助手。使用装备的技能创建演示文稿。""",
        skills=["./skill/pptx"],
        api_key=API_KEY,
        max_iters=30,
    )
    
    router = RouterAgent(
        agents={"code_agent": code_agent, "pptx_agent": pptx_agent},
        api_key=API_KEY,
    )
    
    print("\n系统就绪，请输入您的请求：\n")
    
    while True:
        try:
            user_input = input("\n[用户] > ").strip()
            
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n再见！")
                break
            
            if not user_input:
                continue
            
            # 特殊命令处理
            if user_input.lower() == "seq":
                await router.sequential(
                    Msg("user", "设计一个用户管理系统的amis配置", "user"),
                    ["code_agent", "pptx_agent"]
                )
                continue
            
            if user_input.lower() == "par":
                await router.parallel(
                    Msg("user", "创建一个产品介绍", "user"),
                    ["code_agent", "pptx_agent"]
                )
                continue
            
            await router(Msg("user", user_input, "user"))
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "-i":
            # 交互模式
            asyncio.run(interactive_mode())
        elif mode == "-seq":
            # 串行协作示例
            asyncio.run(sequential_demo())
        elif mode == "-par":
            # 并行协作示例
            asyncio.run(parallel_demo())
        else:
            print(f"未知参数: {mode}")
            print("用法:")
            print("  python multi_agent_main.py       # 默认测试模式")
            print("  python multi_agent_main.py -i    # 交互模式")
            print("  python multi_agent_main.py -seq  # 串行协作示例")
            print("  python multi_agent_main.py -par  # 并行协作示例")
    else:
        # 测试模式
        asyncio.run(main())
