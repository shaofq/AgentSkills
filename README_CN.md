# 🤖 LowCode AI - 智能体可视化编排平台

<p align="center">
  <strong>基于 AgentScope 的多智能体可视化编排系统</strong>
</p>

<p align="center">
  <a href="#-特性">特性</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-项目结构">项目结构</a> •
  <a href="#-使用指南">使用指南</a> •
  <a href="#-智能体列表">智能体列表</a> •
  <a href="./README.md">English</a>
</p>

---

## 📖 项目简介

LowCode AI 是一个**智能体可视化编排平台**，让用户通过拖拽的方式构建复杂的 AI 工作流。基于阿里巴巴开源的 [AgentScope](https://github.com/modelscope/agentscope) 框架，支持多种大语言模型，提供丰富的预置智能体和技能。

### 核心能力

- 🎨 **可视化编排** - 拖拽式工作流设计，所见即所得
- 🔗 **多智能体协作** - 支持串行、并行、条件分支等编排模式
- 🛠️ **技能扩展** - 可插拔的技能系统，轻松扩展智能体能力
- 📚 **Claude SKILL 支持** - 基于 Markdown 的技能定义，智能体可装备多种技能（amis代码生成、PPT制作、OCR识别等）
- 📡 **实时执行** - 流式输出，实时查看执行过程
- 💾 **工作流导入导出** - JSON 格式存储，便于分享和复用

---

## ✨ 特性

| 特性 | 描述 |
|------|------|
| 🎯 **代码助手** | 生成 amis 低代码配置、React/Vue 组件代码 |
| 📊 **PPT 助手** | 自动生成专业的 PowerPoint 演示文稿 |
| 📈 **数据分析** | SQL 查询、数据可视化、报表生成 |
| 📋 **制度问答** | 基于 RAG 的企业知识库问答 |
| 📄 **OCR 识别** | PDF 和图片文字识别提取 |
| 🔀 **智能路由** | 自动分析用户意图，分发到合适的智能体 |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Conda (推荐)

### 1. 克隆项目

```bash
git clone <repository-url>
cd lowcode-ai
```

### 2. 安装后端依赖

```bash
# 创建并激活虚拟环境
conda create -n aicodeskill python=3.10
conda activate aicodeskill

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 设置 API Key（支持通义千问、OpenAI 等）
export DASHSCOPE_API_KEY="your-api-key"
```

### 4. 启动后端服务

```bash
python api_server.py
# 服务运行在 http://localhost:8000
```

### 5. 启动前端界面

```bash
cd frontend
npm install
npm run dev
# 界面运行在 http://localhost:5173
```

---

## 📁 项目结构

```
lowcode-ai/
├── agents/                 # 智能体定义
│   ├── base.py            # 基础智能体类
│   ├── code_agent.py      # 代码生成智能体
│   ├── pptx_agent.py      # PPT 制作智能体
│   ├── ocr_agent.py       # OCR 识别智能体
│   └── policy_qa_agent.py # 制度问答智能体
├── skill/                  # 技能库
│   ├── amis-code-assistant/   # amis 代码助手技能
│   ├── pptx/                  # PPT 制作技能
│   ├── company-policy-qa/     # 制度问答技能
│   └── ocr-file-reader/       # OCR 识别技能
├── workflows/              # 预定义工作流
├── config/                 # 配置文件
│   └── menu_bindings.json # 菜单绑定配置
├── frontend/               # Vue 3 前端项目
│   └── src/
│       ├── components/    # 组件
│       ├── stores/        # Pinia 状态管理
│       └── types/         # TypeScript 类型
├── api_server.py          # FastAPI 后端服务
├── main.py                # 单智能体入口
└── multi_agent_main.py    # 多智能体入口
```

---

## 📖 使用指南

### 可视化编排界面

1. 访问 `http://localhost:5173`
2. 点击左侧菜单「流程编排」进入编排界面
3. 从左侧组件库拖拽节点到画布
4. 连接节点创建工作流
5. 点击「保存」导出工作流配置

### 命令行运行

#### 多智能体模式

```bash
# 默认测试模式
python multi_agent_main.py

# 交互模式
python multi_agent_main.py -i

# 串行协作示例
python multi_agent_main.py -seq

# 并行协作示例
python multi_agent_main.py -par
```

#### 运行导出的工作流

```bash
# 单次执行
python run_workflow.py workflow.json "你的输入内容"

# 交互模式
python run_workflow.py workflow.json -i
```

---

## 🤖 智能体列表

| 智能体 | 类型 | 描述 | 技能 |
|--------|------|------|------|
| **CodeMaster** | 代码生成 | 生成 amis JSON 配置和前端代码 | amis-code-assistant |
| **SlideCreator** | PPT 制作 | 创建专业的演示文稿 | pptx |
| **DataAnalyst** | 数据分析 | 数据处理和可视化 | data-analysis |
| **PolicyQA** | 制度问答 | 企业知识库问答 | company-policy-qa |
| **OCRReader** | OCR 识别 | PDF 和图片文字识别 | ocr-file-reader |
| **Router** | 智能路由 | 分析意图并分发任务 | - |

---

## 🔧 扩展开发

### 添加新技能

1. 在 `skill/` 目录下创建技能文件夹
2. 编写 `SKILL.md` 描述技能用法
3. 在 `frontend/src/components/NodeConfigPanel.vue` 的 `availableSkills` 中注册

### 添加新智能体

1. 在 `agents/` 目录下创建智能体类
2. 继承 `BaseAgent` 并实现业务逻辑
3. 在 `api_server.py` 中注册 API 接口
4. 在 `config/menu_bindings.json` 中添加菜单配置

---

## 🔌 OCR 能力

OCR 功能需要额外启动 OCR 服务：

```bash
# 启动 OCR 服务（端口 8009）
cd /path/to/dots.ocr-adapter_mps
python main.py
```

OCR API 接口：
- `POST http://localhost:8009/api/ocr/filepath` - 识别文件内容

---

## 📝 技能生成工具

使用 Skill_Seekers 从 PDF 文档生成技能：

```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -r requirements.txt

# 从 PDF 生成技能
skill-seekers pdf --pdf docs/document.pdf --name my-skill
```
帮我创建一个具有订舱技能的技能包，该技能包括：
1、可以收集客户提交的订舱数据，调用订舱api接口把数据写入业务系统，api接口说明哪些是必填项、字段的字数、字段的类型要求等控制，如果提交的数据不符合规范要让客户进行调整
2、可以为客户提供查询订舱状态的功能，客户可以通过提单号查询订舱状态
---

## 📄 License

MIT License

---

<p align="center">
  Made with ❤️ by LowCode AI Team
</p>
