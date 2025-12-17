import axios from 'axios'
import type { Workflow, WorkflowExecution, AgentConfig } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export const workflowApi = {
  async getWorkflows(): Promise<Workflow[]> {
    const { data } = await api.get('/workflows')
    return data
  },

  async getWorkflow(id: string): Promise<Workflow> {
    const { data } = await api.get(`/workflows/${id}`)
    return data
  },

  async saveWorkflow(workflow: Workflow): Promise<Workflow> {
    const { data } = await api.post('/workflows', workflow)
    return data
  },

  async updateWorkflow(id: string, workflow: Workflow): Promise<Workflow> {
    const { data } = await api.put(`/workflows/${id}`, workflow)
    return data
  },

  async deleteWorkflow(id: string): Promise<void> {
    await api.delete(`/workflows/${id}`)
  },

  async executeWorkflow(id: string, input: string): Promise<WorkflowExecution> {
    const { data } = await api.post(`/workflows/${id}/execute`, { input })
    return data
  },

  async getExecution(id: string): Promise<WorkflowExecution> {
    const { data } = await api.get(`/executions/${id}`)
    return data
  },
}

export const agentApi = {
  async getAgents(): Promise<AgentConfig[]> {
    const { data } = await api.get('/agents')
    return data
  },

  async getSkills(): Promise<string[]> {
    const { data } = await api.get('/skills')
    return data
  },
}

export default api
