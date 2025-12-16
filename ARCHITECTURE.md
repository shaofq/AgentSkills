# 多智能体架构设计

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      用户请求入口                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Router Agent (路由智能体)                  │
│  - 分析用户意图                                              │
│  - 选择合适的专业智能体                                       │
│  - 协调多智能体协作                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Code Agent  │   │ PPTX Agent  │   │ Data Agent  │
│ (代码生成)   │   │ (PPT制作)    │   │ (数据分析)   │
├─────────────┤   ├─────────────┤   ├─────────────┤
│ Skills:     │   │ Skills:     │   │ Skills:     │
│ - amis      │   │ - pptx      │   │ - sql       │
│ - react     │   │ - design    │   │ - pandas    │
│ - api       │   │             │   │ - chart     │
└─────────────┘   └─────────────┘   └─────────────┘
```

## 目录结构

```
lowcode-ai/
├── main.py                     # 主入口
├── config/                     # 配置文件
│   ├── __init__.py
│   ├── agents.yaml             # 智能体配置
│   ├── models.yaml             # 模型配置
│   └── settings.py             # 全局设置
│
├── agents/                     # 智能体定义
│   ├── __init__.py
│   ├── base.py                 # 基础智能体类
│   ├── router.py               # 路由智能体
│   ├── code_agent.py           # 代码生成智能体
│   ├── pptx_agent.py           # PPT制作智能体
│   └── data_agent.py           # 数据分析智能体
│
├── skills/                     # 技能库
│   ├── amis-code-assistant/    # amis代码辅助
│   │   ├── SKILL.md
│   │   ├── docs/
│   │   └── examples/
│   ├── pptx/                   # PPT制作
│   │   ├── SKILL.md
│   │   ├── docs/
│   │   └── scripts/
│   ├── react-code/             # React代码生成
│   │   ├── SKILL.md
│   │   └── docs/
│   └── data-analysis/          # 数据分析
│       ├── SKILL.md
│       └── docs/
│
├── orchestrator/               # 编排层
│   ├── __init__.py
│   ├── workflow.py             # 工作流定义
│   ├── dispatcher.py           # 任务分发器
│   └── context.py              # 上下文管理
│
├── memory/                     # 记忆管理
│   ├── __init__.py
│   ├── shared_memory.py        # 共享记忆
│   └── agent_memory.py         # 智能体私有记忆
│
├── tools/                      # 通用工具
│   ├── __init__.py
│   ├── file_tools.py           # 文件操作
│   └── api_tools.py            # API调用
│
└── tests/                      # 测试
    ├── test_agents.py
    └── test_skills.py
```

## 核心设计原则

### 1. 单一职责
每个智能体专注于一个领域，配备相关技能。

### 2. 松耦合
智能体之间通过消息传递通信，不直接依赖。

### 3. 可扩展
新增智能体只需：
- 在 `agents/` 添加智能体类
- 在 `skills/` 添加对应技能
- 在 `config/agents.yaml` 注册

### 4. 统一入口
Router Agent 作为统一入口，负责意图识别和任务分发。

## 智能体配置示例 (agents.yaml)

```yaml
agents:
  router:
    name: "Router"
    type: "router"
    model: "qwen3-max"
    description: "分析用户意图，分发任务到专业智能体"
    
  code_agent:
    name: "CodeMaster"
    type: "react"
    model: "qwen3-max"
    skills:
      - "amis-code-assistant"
      - "react-code"
    description: "专注于代码生成和开发任务"
    
  pptx_agent:
    name: "SlideCreator"
    type: "react"
    model: "qwen3-max"
    skills:
      - "pptx"
    description: "专注于PPT创建和编辑"
    
  data_agent:
    name: "DataAnalyst"
    type: "react"
    model: "qwen3-max"
    skills:
      - "data-analysis"
    description: "专注于数据分析和可视化"
```

## 工作流模式

### 模式1：单智能体处理
用户请求 → Router → 单个专业智能体 → 返回结果

### 模式2：串行协作
用户请求 → Router → Agent A → Agent B → 返回结果

### 模式3：并行协作
用户请求 → Router → [Agent A, Agent B] (并行) → 合并结果 → 返回
