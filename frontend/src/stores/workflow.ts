import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WorkflowNode, WorkflowEdge, Workflow, AgentConfig } from '@/types'

export const useWorkflowStore = defineStore('workflow', () => {
  const nodes = ref<WorkflowNode[]>([])
  const edges = ref<WorkflowEdge[]>([])
  const currentWorkflow = ref<Workflow | null>(null)
  const selectedNodeId = ref<string | null>(null)

  const predefinedAgents: AgentConfig[] = [
    {
      id: 'router',
      name: 'Router',
      type: 'router',
      description: '路由智能体 - 分析用户意图并分发任务',
      systemPrompt: '你是一个智能路由助手，负责分析用户请求并将其分发到合适的专业智能体。',
      skills: [],
      model: 'qwen3-max',
      maxIters: 10,
    },
    {
      id: 'code_agent',
      name: 'CodeMaster',
      type: 'code',
      description: '代码生成智能体 - 生成 amis 配置和前端代码',
      systemPrompt: '你是一个专业的代码生成助手 CodeMaster。你的专长是生成 amis 低代码 JSON 配置、编写前端组件代码。',
      skills: ['amis-code-assistant'],
      model: 'qwen3-max',
      maxIters: 30,
    },
    {
      id: 'pptx_agent',
      name: 'SlideCreator',
      type: 'pptx',
      description: 'PPT制作智能体 - 创建和编辑演示文稿',
      systemPrompt: '你是一个专业的演示文稿制作助手 SlideCreator。你的专长是创建和编辑 PowerPoint 演示文稿。',
      skills: ['pptx'],
      model: 'qwen3-max',
      maxIters: 30,
    },
    {
      id: 'data_agent',
      name: 'DataAnalyst',
      type: 'data',
      description: '数据分析智能体 - 数据处理和可视化',
      systemPrompt: '你是一个专业的数据分析助手 DataAnalyst。你的专长是数据分析、SQL查询和图表可视化。',
      skills: ['data-analysis'],
      model: 'qwen3-max',
      maxIters: 30,
    },
    {
      id: 'policy_qa_agent',
      name: 'PolicyQA',
      type: 'policy',
      description: '制度问答智能体 - 解答公司规章制度问题',
      systemPrompt: '你是岸基科技公司的制度问答助手，专门负责解答员工关于公司规章制度的各类问题。',
      skills: ['company-policy-qa'],
      model: 'qwen3-max',
      maxIters: 10,
    },
    {
      id: 'ocr_agent',
      name: 'OCRReader',
      type: 'ocr',
      description: 'OCR文件识别智能体 - 识别PDF和图片中的文字',
      systemPrompt: '你是一个专业的OCR文件识别助手OCRReader。你的专长是识别PDF文件和图片中的文字内容。',
      skills: ['ocr-file-reader'],
      model: 'qwen3-max',
      maxIters: 10,
    },
    {
      id: 'skill_creator_agent',
      name: 'SkillCreator',
      type: 'skill-creator',
      description: '技能创建智能体 - 创建新的Skill技能包',
      systemPrompt: '你是一个专业的技能创建助手SkillCreator。你的专长是创建新的Skill技能包，设计技能结构和编写SKILL.md文档。',
      skills: ['skill-creator'],
      model: 'qwen3-max',
      maxIters: 30,
    },
  ]

  const selectedNode = computed(() => {
    if (!selectedNodeId.value) return null
    return nodes.value.find(n => n.id === selectedNodeId.value) || null
  })

  function addNode(node: WorkflowNode) {
    nodes.value.push(node)
  }

  function updateNode(id: string, data: Partial<WorkflowNode>) {
    const index = nodes.value.findIndex(n => n.id === id)
    if (index !== -1) {
      // 使用深拷贝确保响应式更新
      const updatedNode = JSON.parse(JSON.stringify({ ...nodes.value[index], ...data }))
      nodes.value.splice(index, 1, updatedNode)
    }
  }

  function removeNode(id: string) {
    nodes.value = nodes.value.filter(n => n.id !== id)
    edges.value = edges.value.filter(e => e.source !== id && e.target !== id)
    if (selectedNodeId.value === id) {
      selectedNodeId.value = null
    }
  }

  function addEdge(edge: WorkflowEdge) {
    const exists = edges.value.some(
      e => e.source === edge.source && e.target === edge.target
    )
    if (!exists) {
      edges.value.push(edge)
    }
  }

  function removeEdge(id: string) {
    edges.value = edges.value.filter(e => e.id !== id)
  }

  function selectNode(id: string | null) {
    selectedNodeId.value = id
  }

  function clearWorkflow() {
    nodes.value = []
    edges.value = []
    selectedNodeId.value = null
  }

  function loadWorkflow(workflow: Workflow) {
    currentWorkflow.value = workflow
    nodes.value = workflow.nodes
    edges.value = workflow.edges
    selectedNodeId.value = null
  }

  function exportWorkflow(): Workflow {
    return {
      id: currentWorkflow.value?.id || `workflow_${Date.now()}`,
      name: currentWorkflow.value?.name || '未命名工作流',
      description: currentWorkflow.value?.description || '',
      nodes: nodes.value,
      edges: edges.value,
      createdAt: currentWorkflow.value?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
  }

  return {
    nodes,
    edges,
    currentWorkflow,
    selectedNodeId,
    selectedNode,
    predefinedAgents,
    addNode,
    updateNode,
    removeNode,
    addEdge,
    removeEdge,
    selectNode,
    clearWorkflow,
    loadWorkflow,
    exportWorkflow,
  }
})
