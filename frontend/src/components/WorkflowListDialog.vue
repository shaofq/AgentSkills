<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface BoundMenu {
  id: string
  name: string
  icon: string
}

interface Workflow {
  name: string
  title: string
  description: string
  nodeCount: number
  edgeCount: number
  boundMenus: BoundMenu[]
}

const workflows = ref<Workflow[]>([])
const loading = ref(false)
const error = ref('')

async function loadWorkflows() {
  loading.value = true
  error.value = ''
  
  try {
    console.log('[WorkflowList] 开始加载工作流列表...')
    const response = await fetch('http://localhost:8000/api/workflowsquery')
    console.log('[WorkflowList] 响应状态:', response.status)
    
    if (response.ok) {
      const data = await response.json()
      console.log('[WorkflowList] 接收到的数据:', data)
      workflows.value = data.workflows || []
      console.log('[WorkflowList] 工作流数量:', workflows.value.length)
    } else {
      error.value = `加载流程列表失败 (状态码: ${response.status})`
    }
  } catch (err) {
    console.error('[WorkflowList] 加载失败:', err)
    error.value = '网络请求失败: ' + (err as Error).message
  } finally {
    loading.value = false
  }
}

function refreshList() {
  loadWorkflows()
}

onMounted(() => {
  loadWorkflows()
})
</script>

<template>
  <div class="workflow-list-container p-6">
    <div class="header flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold text-gray-800">已加载的工作流</h2>
      <button 
        @click="refreshList"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        :disabled="loading"
      >
        <i class="icon-refresh" :class="{ 'animate-spin': loading }"></i>
        刷新
      </button>
    </div>

    <div v-if="error" class="error-message mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
      {{ error }}
    </div>

    <div v-if="loading && workflows.length === 0" class="loading text-center py-12 text-gray-500">
      <i class="icon-loading animate-spin text-3xl mb-2"></i>
      <p>加载中...</p>
    </div>

    <div v-else-if="workflows.length === 0" class="empty text-center py-12 text-gray-500">
      <i class="icon-inbox text-5xl mb-4 opacity-50"></i>
      <p class="text-lg">暂无已加载的工作流</p>
      <p class="text-sm mt-2">请在 workflows 目录下添加工作流配置文件</p>
    </div>

    <div v-else class="workflow-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="workflow in workflows" 
        :key="workflow.name"
        class="workflow-card bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-5 border border-gray-200"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2">
            <i class="icon-application text-2xl text-blue-600"></i>
            <h3 class="text-lg font-semibold text-gray-800">{{ workflow.title }}</h3>
          </div>
          <span class="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">已加载</span>
        </div>

        <p class="text-sm text-gray-600 mb-4 line-clamp-2">
          {{ workflow.description || '暂无描述' }}
        </p>

        <div class="workflow-meta flex items-center gap-4 text-xs text-gray-500 mb-4">
          <div class="flex items-center gap-1">
            <i class="icon-node"></i>
            <span>{{ workflow.nodeCount }} 个节点</span>
          </div>
          <div class="flex items-center gap-1">
            <i class="icon-link"></i>
            <span>{{ workflow.edgeCount }} 条连线</span>
          </div>
        </div>

        <div class="workflow-name text-xs text-gray-400 font-mono bg-gray-50 px-2 py-1 rounded">
          {{ workflow.name }}
        </div>

        <!-- 绑定的功能菜单 -->
        <div v-if="workflow.boundMenus && workflow.boundMenus.length > 0" class="bound-menus mt-3 pt-3 border-t border-gray-100">
          <div class="text-xs text-gray-500 mb-2">绑定功能:</div>
          <div class="flex flex-wrap gap-2">
            <span 
              v-for="menu in workflow.boundMenus" 
              :key="menu.id"
              class="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
            >
              <i :class="menu.icon" class="text-sm"></i>
              {{ menu.name }}
            </span>
          </div>
        </div>
        <div v-else class="bound-menus mt-3 pt-3 border-t border-gray-100">
          <div class="text-xs text-gray-400 italic">未绑定功能菜单</div>
        </div>
      </div>
    </div>

    <!-- <div v-if="workflows.length > 0" class="summary mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <p class="text-sm text-blue-800">
        <i class="icon-info-circle mr-2"></i>
        共加载 <strong>{{ workflows.length }}</strong> 个工作流
      </p>
    </div> -->
  </div>
</template>

<style scoped>
.workflow-list-container {
  height: 100%;
  overflow-y: auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.workflow-card {
  transition: all 0.3s ease;
}

.workflow-card:hover {
  transform: translateY(-2px);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
