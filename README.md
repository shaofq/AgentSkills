# 🤖 LowCode AI - Visual Agent Orchestration Platform

<p align="center">
  <strong>Multi-Agent Visual Orchestration System based on AgentScope</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-project-structure">Project Structure</a> •
  <a href="#-usage-guide">Usage Guide</a> •
  <a href="#-agent-list">Agent List</a> •
  <a href="./README_CN.md">中文文档</a>
</p>


---

## 📖 Introduction

LowCode AI is a **visual agent orchestration platform** that enables users to build complex AI workflows through drag-and-drop. Built on Alibaba's open-source [AgentScope](https://github.com/modelscope/agentscope) framework, it supports multiple large language models and provides rich pre-built agents and skills.

### Core Capabilities

- 🎨 **Visual Orchestration** - Drag-and-drop workflow design, WYSIWYG
- 🔗 **Multi-Agent Collaboration** - Supports serial, parallel, and conditional branching patterns
- 🛠️ **Skill Extension** - Pluggable skill system for easy agent capability expansion
- 📚 **Claude SKILL Support** - Markdown-based skill definitions, agents can equip multiple skills (amis code generation, PPT creation, OCR recognition, etc.)
- � **Real-time Execution** - Streaming output, real-time execution monitoring
- 💾 **Workflow Import/Export** - JSON format storage for easy sharing and reuse

<p align="center">
  <img src="./docs/visualflow.png" alt="Visual Flow Editor" width="800" />
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 **Code Assistant** | Generate amis low-code configurations, React/Vue component code |
| 📊 **PPT Assistant** | Automatically generate professional PowerPoint presentations |
| 📈 **Data Analysis** | SQL queries, data visualization, report generation |
| 📋 **Policy Q&A** | RAG-based enterprise knowledge base Q&A |
| 📄 **OCR Recognition** | PDF and image text recognition and extraction |
| 🔀 **Smart Router** | Automatically analyze user intent and dispatch to appropriate agents |

---

## 🚀 Quick Start

### Requirements

- Python 3.10+
- Node.js 18+
- Conda (recommended)

### 1. Clone the Project

```bash
git clone <repository-url>
cd lowcode-ai
```

### 2. Install Backend Dependencies

```bash
# Create and activate virtual environment
conda create -n aicodeskill python=3.10
conda activate aicodeskill

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Set API Key (supports Qwen, OpenAI, etc.)
export DASHSCOPE_API_KEY="your-api-key"
```

### 4. Start Backend Service

```bash
python api.main
# Service runs at http://localhost:8000
```

### 5. Start Frontend Interface

```bash
cd frontend
npm install
npm run dev
# Interface runs at http://localhost:5173
```

---

## 📁 Project Structure

```
lowcode-ai/
├── agents/                 # Agent definitions
│   ├── base.py            # Base agent class
│   ├── code_agent.py      # Code generation agent
│   ├── pptx_agent.py      # PPT creation agent
│   ├── ocr_agent.py       # OCR recognition agent
│   └── policy_qa_agent.py # Policy Q&A agent
├── skill/                  # Skill library
│   ├── amis-code-assistant/   # amis code assistant skill
│   ├── pptx/                  # PPT creation skill
│   ├── company-policy-qa/     # Policy Q&A skill
│   └── ocr-file-reader/       # OCR recognition skill
├── workflows/              # Predefined workflows
├── config/                 # Configuration files
│   └── menu_bindings.json # Menu binding configuration
├── frontend/               # Vue 3 frontend project
│   └── src/
│       ├── components/    # Components
│       ├── stores/        # Pinia state management
│       └── types/         # TypeScript types
├── api_server.py          # FastAPI backend service
├── main.py                # Single agent entry
└── multi_agent_main.py    # Multi-agent entry
```

---

## 📖 Usage Guide

### Visual Orchestration Interface

1. Visit `http://localhost:5173`
2. Click "Workflow Editor" in the left menu to enter the orchestration interface
3. Drag nodes from the left component library to the canvas
4. Connect nodes to create workflows
5. Click "Save" to export workflow configuration


## 🤖 Agent List

| Agent | Type | Description | Skill |
|-------|------|-------------|-------|
| **CodeMaster** | Code Generation | Generate amis JSON configs and frontend code | amis-code-assistant |
| **SlideCreator** | PPT Creation | Create professional presentations | pptx |
| **DataAnalyst** | Data Analysis | Data processing and visualization | data-analysis |
| **PolicyQA** | Policy Q&A | Enterprise knowledge base Q&A | company-policy-qa |
| **OCRReader** | OCR Recognition | PDF and image text recognition | ocr-file-reader |
| **Router** | Smart Router | Analyze intent and dispatch tasks | - |

---

## 🔧 Extension Development

### Adding New Skills

1. Create a skill folder under `skill/` directory
2. Write `SKILL.md` to describe skill usage
3. Register in `availableSkills` in `frontend/src/components/NodeConfigPanel.vue`

### Adding New Agents

1. Create an agent class under `agents/` directory
2. Inherit from `BaseAgent` and implement business logic
3. Register API endpoints in `api_server.py`
4. Add menu configuration in `config/menu_bindings.json`

---

## 🔌 OCR Capability

OCR functionality requires starting the OCR service separately:

```bash
# Start OCR service (port 8009)
cd /path/to/dots.ocr-adapter_mps
python main.py
```

OCR API endpoint:
- `POST http://localhost:8009/api/ocr/filepath` - Recognize file content

---
## sandbox

```bash
docker run --security-opt seccomp=unconfined --rm -it -p 988:8080 ghcr.io/agent-infra/sandbox:latest
```

## 📝 Skill Generation Tool

Use Skill_Seekers to generate skills from PDF documents:

```bash
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers
pip install -r requirements.txt

# Generate skill from PDF
skill-seekers pdf --pdf docs/document.pdf --name my-skill
```

---

## 📄 License

MIT License

---

<p align="center">
  Made with ❤️ by LowCode AI Team
</p>