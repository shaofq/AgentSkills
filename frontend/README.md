# 智能体编排系统前端

基于 Vue 3 + Vue Flow 的智能体可视化编排系统。

## 功能特性

- 🎨 **可视化编排**: 拖拽式节点编排，直观创建工作流
- 🤖 **多种智能体**: 支持路由、代码生成、PPT制作、数据分析等智能体
- 🔗 **流程控制**: 支持条件分支、并行执行等流程控制节点
- 💾 **工作流管理**: 导入/导出工作流配置
- ⚡ **实时执行**: 一键运行工作流，查看执行结果

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vue Flow** - 基于 Vue 3 的流程图库
- **Pinia** - Vue 状态管理
- **TailwindCSS** - 原子化 CSS 框架
- **TypeScript** - 类型安全
- **Vite** - 下一代前端构建工具

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API 接口
│   ├── components/       # Vue 组件
│   │   ├── nodes/        # 自定义节点组件
│   │   ├── FlowCanvas.vue    # 流程画布
│   │   ├── Sidebar.vue       # 侧边栏组件库
│   │   ├── NodeConfigPanel.vue # 节点配置面板
│   │   └── Toolbar.vue       # 顶部工具栏
│   ├── stores/           # Pinia 状态管理
│   ├── types/            # TypeScript 类型定义
│   ├── App.vue           # 根组件
│   ├── main.ts           # 入口文件
│   └── style.css         # 全局样式
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## 使用说明

### 创建工作流

1. 从左侧组件库拖拽节点到画布
2. 连接节点创建执行流程
3. 点击节点配置参数
4. 点击"运行"执行工作流

### 节点类型

- **用户输入**: 工作流的起点，接收用户输入
- **输出结果**: 工作流的终点，显示最终结果
- **智能体节点**: 执行具体任务的 AI 智能体
  - Router: 路由智能体，分析意图并分发任务
  - CodeMaster: 代码生成智能体
  - SlideCreator: PPT 制作智能体
  - DataAnalyst: 数据分析智能体
- **条件分支**: 根据条件选择不同的执行路径
- **并行执行**: 同时执行多个分支

### 工作流示例

**串行执行**:
```
用户输入 → CodeMaster → SlideCreator → 输出结果
```

**并行执行**:
```
用户输入 → 并行执行 → CodeMaster
                    → DataAnalyst → 输出结果
```

## 后端 API

前端通过 `/api` 代理连接后端服务。启动后端：

```bash
# 在项目根目录
python api_server.py
```

API 端点：
- `GET /api/agents` - 获取可用智能体列表
- `GET /api/skills` - 获取可用技能列表
- `GET/POST /api/workflows` - 工作流 CRUD
- `POST /api/workflows/:id/execute` - 执行工作流
- `GET /api/executions/:id` - 获取执行状态
