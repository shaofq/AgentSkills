export interface CustomParam {
  key: string
  value: string
  type: 'string' | 'number' | 'boolean' | 'json'
}

export interface InputVariable {
  name: string
  description: string
  required: boolean
  defaultValue?: string
}

export interface AgentConfig {
  id: string
  name: string
  type: 'router' | 'code' | 'pptx' | 'data' | 'custom'
  description: string
  systemPrompt: string
  skills: string[]
  model: string
  maxIters: number
  temperature?: number
  enableThinking?: boolean
  stream?: boolean
  customParams?: CustomParam[]
  inputVariables?: InputVariable[]
}

export interface ConditionConfig {
  expression: string
}

export interface WorkflowNode {
  id: string
  type: 'agent' | 'input' | 'output' | 'condition' | 'parallel'
  position: { x: number; y: number }
  data: {
    label: string
    agentConfig?: AgentConfig
    conditionConfig?: ConditionConfig
    [key: string]: any
  }
}

export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  type?: string
  animated?: boolean
  label?: string
}

export interface Workflow {
  id: string
  name: string
  description: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  createdAt: string
  updatedAt: string
}

export interface ExecutionResult {
  nodeId: string
  status: 'pending' | 'running' | 'success' | 'error'
  output?: string
  error?: string
  startTime?: string
  endTime?: string
}

export interface WorkflowExecution {
  id: string
  workflowId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  input: string
  results: ExecutionResult[]
  startTime: string
  endTime?: string
}
