<script setup lang="ts">
import { ref, computed } from 'vue'
import { useWorkflowStore } from '@/stores/workflow'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useWorkflowStore()
const userInput = ref('')
const isRunning = ref(false)
const executionLogs = ref<Array<{
  nodeId: string
  nodeLabel: string
  type: 'info' | 'success' | 'error' | 'warning'
  message: string
  timestamp: string
}>>([])
const finalOutput = ref('')

const hasWorkflow = computed(() => {
  return store.nodes.length > 0
})

async function handleTest() {
  if (!userInput.value.trim()) {
    alert('请输入测试内容')
    return
  }

  isRunning.value = true
  executionLogs.value = []
  finalOutput.value = ''

  try {
    const workflow = store.exportWorkflow()
    
    addLog('system', '系统', 'info', '开始执行工作流测试...')
    addLog('system', '系统', 'info', `输入内容: ${userInput.value}`)

    const response = await fetch('http://localhost:8000/api/workflow/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        workflow,
        input: userInput.value,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(line => line.trim())

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))
            handleStreamData(data)
          }
        }
      }
    }

    addLog('system', '系统', 'success', '工作流执行完成')
  } catch (error) {
    console.error('执行失败:', error)
    addLog('system', '系统', 'error', `执行失败: ${error}`)
  } finally {
    isRunning.value = false
  }
}

function handleStreamData(data: any) {
  if (data.type === 'node_start') {
    addLog(data.nodeId, data.nodeLabel, 'info', `开始执行节点`)
  } else if (data.type === 'node_complete') {
    addLog(data.nodeId, data.nodeLabel, 'success', `节点执行完成`)
  } else if (data.type === 'node_error') {
    addLog(data.nodeId, data.nodeLabel, 'error', `节点执行失败: ${data.error}`)
  } else if (data.type === 'condition_result') {
    addLog(data.nodeId, data.nodeLabel, 'warning', `条件判断结果: ${data.result ? 'True' : 'False'}`)
  } else if (data.type === 'parallel_start') {
    addLog(data.nodeId, data.nodeLabel, 'info', `并行执行 ${data.branchCount} 个分支`)
  } else if (data.type === 'output') {
    finalOutput.value = data.content
    addLog('system', '系统', 'success', '获取到输出结果')
  } else if (data.type === 'log') {
    addLog(data.nodeId || 'system', data.nodeLabel || '系统', 'info', data.message)
  }
}

function addLog(nodeId: string, nodeLabel: string, type: 'info' | 'success' | 'error' | 'warning', message: string) {
  executionLogs.value.push({
    nodeId,
    nodeLabel,
    type,
    message,
    timestamp: new Date().toLocaleTimeString(),
  })
}

function handleClear() {
  userInput.value = ''
  executionLogs.value = []
  finalOutput.value = ''
}

function getLogIcon(type: string) {
  switch (type) {
    case 'success':
      return '✓'
    case 'error':
      return '✗'
    case 'warning':
      return '⚠'
    default:
      return '•'
  }
}

function getLogColor(type: string) {
  switch (type) {
    case 'success':
      return 'text-green-600 bg-green-50'
    case 'error':
      return 'text-red-600 bg-red-50'
    case 'warning':
      return 'text-yellow-600 bg-yellow-50'
    default:
      return 'text-blue-600 bg-blue-50'
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
      <!-- 头部 -->
      <div class="p-4 border-b border-gray-200 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-gradient-to-br from-green-500 to-teal-600 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
          </div>
          <h2 class="text-lg font-semibold text-gray-800">工作流测试</h2>
        </div>
        <button 
          @click="emit('close')"
          class="p-1 hover:bg-gray-100 rounded-md transition-colors"
        >
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- 内容区域 -->
      <div class="flex-1 overflow-hidden flex flex-col p-4 gap-4">
        <!-- 输入区域 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">测试输入</label>
          <textarea 
            v-model="userInput"
            :disabled="isRunning"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
            rows="3"
            placeholder="输入测试内容，例如：请帮我生成一个用户管理页面"
          ></textarea>
        </div>

        <!-- 执行日志 -->
        <div class="flex-1 overflow-hidden flex flex-col">
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">执行日志</label>
            <button 
              v-if="executionLogs.length > 0"
              @click="handleClear"
              class="text-xs text-gray-500 hover:text-gray-700"
            >清空</button>
          </div>
          <div class="flex-1 overflow-y-auto bg-gray-50 rounded-lg border border-gray-200 p-3 space-y-2">
            <div 
              v-if="executionLogs.length === 0"
              class="h-full flex items-center justify-center text-gray-400 text-sm"
            >
              暂无执行日志
            </div>
            <div 
              v-for="(log, index) in executionLogs"
              :key="index"
              :class="['flex items-start gap-2 p-2 rounded text-xs', getLogColor(log.type)]"
            >
              <span class="font-bold">{{ getLogIcon(log.type) }}</span>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span class="font-medium">{{ log.nodeLabel }}</span>
                  <span class="text-gray-500">{{ log.timestamp }}</span>
                </div>
                <div class="mt-0.5">{{ log.message }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 输出结果 -->
        <div v-if="finalOutput">
          <label class="block text-sm font-medium text-gray-700 mb-2">输出结果</label>
          <div class="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-gray-700 max-h-32 overflow-y-auto">
            {{ finalOutput }}
          </div>
        </div>
      </div>

      <!-- 底部按钮 -->
      <div class="p-4 border-t border-gray-200 flex items-center justify-between">
        <div class="text-xs text-gray-500">
          <span v-if="!hasWorkflow" class="text-red-500">⚠ 当前工作流为空</span>
          <span v-else>✓ 工作流包含 {{ store.nodes.length }} 个节点</span>
        </div>
        <div class="flex gap-2">
          <button 
            @click="emit('close')"
            class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          >
            关闭
          </button>
          <button 
            @click="handleTest"
            :disabled="isRunning || !hasWorkflow"
            class="px-4 py-2 text-sm text-white bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 rounded-lg transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="!isRunning" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ isRunning ? '测试中...' : '开始测试' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
