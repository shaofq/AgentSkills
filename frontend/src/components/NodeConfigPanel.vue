<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useWorkflowStore } from '@/stores/workflow'

const emit = defineEmits<{
  (e: 'close'): void
}>()

const store = useWorkflowStore()

const localConfig = ref({
  name: '',
  systemPrompt: '',
  skills: [] as string[],
  model: 'qwen3-max',
  maxIters: 30,
  temperature: 0.7,
  enableThinking: false,
  stream: true,
  customParams: [] as { key: string; value: string; type: string }[],
  inputVariables: [] as { name: string; description: string; required: boolean }[],
  // 条件节点配置
  conditionExpression: '',
  // 并行节点配置
  parallelDescription: '',
})

const activeTab = ref<'basic' | 'advanced' | 'variables'>('basic')

const selectedNode = computed(() => store.selectedNode)

watch(selectedNode, (node) => {
  if (node?.data?.agentConfig) {
    const config = node.data.agentConfig
    localConfig.value = {
      name: config.name || node.data.label,
      systemPrompt: config.systemPrompt || '',
      skills: config.skills || [],
      model: config.model || 'qwen3-max',
      maxIters: config.maxIters || 30,
      temperature: config.temperature ?? 0.7,
      enableThinking: config.enableThinking ?? false,
      stream: config.stream ?? true,
      customParams: config.customParams || [],
      inputVariables: config.inputVariables || [],
      conditionExpression: '',
      parallelDescription: '',
    }
  } else if (node?.data?.conditionConfig) {
    // 条件节点配置
    const config = node.data.conditionConfig
    localConfig.value = {
      name: node.data.label,
      systemPrompt: '',
      skills: [],
      model: 'qwen3-max',
      maxIters: 30,
      temperature: 0.7,
      enableThinking: false,
      stream: true,
      customParams: [],
      inputVariables: [],
      conditionExpression: config.expression || '',
      parallelDescription: '',
    }
  } else if (node) {
    localConfig.value = {
      name: node.data.label,
      systemPrompt: '',
      skills: [],
      model: 'qwen3-max',
      maxIters: 30,
      temperature: 0.7,
      enableThinking: false,
      stream: true,
      customParams: [],
      inputVariables: [],
      conditionExpression: '',
      parallelDescription: '',
    }
  }
  activeTab.value = 'basic'
}, { immediate: true })

function handleSave() {
  if (selectedNode.value) {
    const nodeType = selectedNode.value.type
    
    if (nodeType === 'agent') {
      // 智能体节点
      store.updateNode(selectedNode.value.id, {
        data: {
          ...selectedNode.value.data,
          label: localConfig.value.name,
          agentConfig: {
            ...selectedNode.value.data.agentConfig,
            name: localConfig.value.name,
            systemPrompt: localConfig.value.systemPrompt,
            skills: localConfig.value.skills,
            model: localConfig.value.model,
            maxIters: localConfig.value.maxIters,
            temperature: localConfig.value.temperature,
            enableThinking: localConfig.value.enableThinking,
            stream: localConfig.value.stream,
            customParams: localConfig.value.customParams,
            inputVariables: localConfig.value.inputVariables,
          },
        },
      })
    } else if (nodeType === 'condition') {
      // 条件节点
      store.updateNode(selectedNode.value.id, {
        data: {
          ...selectedNode.value.data,
          label: localConfig.value.name,
          conditionConfig: {
            expression: localConfig.value.conditionExpression,
          },
        },
      })
    } else {
      // 其他节点（input, output, parallel）
      store.updateNode(selectedNode.value.id, {
        data: {
          ...selectedNode.value.data,
          label: localConfig.value.name,
        },
      })
    }
  }
  emit('close')
}

function addCustomParam() {
  localConfig.value.customParams.push({ key: '', value: '', type: 'string' as const })
}

function removeCustomParam(index: number) {
  localConfig.value.customParams.splice(index, 1)
}

function addInputVariable() {
  localConfig.value.inputVariables.push({ name: '', description: '', required: true })
}

function removeInputVariable(index: number) {
  localConfig.value.inputVariables.splice(index, 1)
}

function handleDelete() {
  if (selectedNode.value && confirm('确定要删除此节点吗？')) {
    store.removeNode(selectedNode.value.id)
    emit('close')
  }
}

const availableSkills = [
  'amis-code-assistant',
  'pptx',
  'data-analysis',
  'company-policy-qa',
  'ocr-file-reader',
  'skill-creator',
  // 'react-code',
  // 'sql-query',
]

const availableModels = [
  'qwen3-max',
  'qwen-plus',
  'qwen-turbo',
  'gpt-4',
  'gpt-3.5-turbo',
]
</script>

<template>
  <div class="w-80 bg-white border-l border-gray-200 flex flex-col shadow-lg">
    <!-- 头部 -->
    <div class="p-4 border-b border-gray-200 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-gray-800">节点配置</h2>
      <button 
        @click="emit('close')"
        class="p-1 hover:bg-gray-100 rounded-md transition-colors"
      >
        <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <!-- 内容 -->
    <div v-if="selectedNode" class="flex-1 overflow-y-auto p-4 space-y-4">
      <!-- 节点类型 -->
      <div class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
        <div :class="[selectedNode.data.color, 'w-10 h-10 rounded-lg flex items-center justify-center text-white']">
          <span class="text-lg">{{ selectedNode.data.icon }}</span>
        </div>
        <div>
          <div class="text-sm font-medium text-gray-700">{{ selectedNode.type }}</div>
          <div class="text-xs text-gray-500">ID: {{ selectedNode.id }}</div>
        </div>
      </div>
      
      <!-- 名称 -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">名称</label>
        <input 
          v-model="localConfig.name"
          type="text"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          placeholder="节点名称"
        />
      </div>

      <!-- 条件节点配置 -->
      <template v-if="selectedNode.type === 'condition'">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">条件表达式</label>
          <input 
            v-model="localConfig.conditionExpression"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            placeholder="输入关键词，如：code、ppt、数据"
          />
          <p class="mt-1 text-xs text-gray-500">
            当输入内容包含此关键词时，走 True 分支；否则走 False 分支
          </p>
        </div>
        
        <div class="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="text-xs text-blue-700">
              <p class="font-medium mb-1">使用说明：</p>
              <ul class="space-y-1 list-disc list-inside">
                <li>条件表达式支持简单的关键词匹配</li>
                <li>例如：输入 "code"，当用户请求包含 "code" 时走 True 分支</li>
                <li>True 分支连接绿色连接点，False 分支连接红色连接点</li>
              </ul>
            </div>
          </div>
        </div>
      </template>

      <!-- 并行节点配置 -->
      <template v-if="selectedNode.type === 'parallel'">
        <div class="p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="text-xs text-purple-700">
              <p class="font-medium mb-1">并行执行节点：</p>
              <ul class="space-y-1 list-disc list-inside">
                <li>所有下游分支将同时并行执行</li>
                <li>适用于需要同时处理多个任务的场景</li>
                <li>执行结果会自动合并后输出</li>
              </ul>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 智能体特有配置 -->
      <template v-if="selectedNode.type === 'agent'">
        <!-- 标签页切换 -->
        <div class="flex border-b border-gray-200 -mx-4 px-4">
          <button 
            @click="activeTab = 'basic'"
            :class="['px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors', activeTab === 'basic' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
          >基础配置</button>
          <button 
            @click="activeTab = 'advanced'"
            :class="['px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors', activeTab === 'advanced' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
          >高级参数</button>
          <button 
            @click="activeTab = 'variables'"
            :class="['px-3 py-2 text-sm font-medium border-b-2 -mb-px transition-colors', activeTab === 'variables' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
          >输入变量</button>
        </div>

        <!-- 基础配置 -->
        <template v-if="activeTab === 'basic'">
          <!-- 系统提示词 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">系统提示词</label>
            <textarea 
              v-model="localConfig.systemPrompt"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-none"
              placeholder="定义智能体的行为和能力..."
            ></textarea>
          </div>
          
          <!-- 模型选择 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">模型</label>
            <select 
              v-model="localConfig.model"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            >
              <option v-for="model in availableModels" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
          </div>
          
          <!-- 技能选择 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">技能</label>
            <div class="space-y-2 max-h-32 overflow-y-auto">
              <label 
                v-for="skill in availableSkills" 
                :key="skill"
                class="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-md cursor-pointer"
              >
                <input 
                  type="checkbox"
                  :value="skill"
                  v-model="localConfig.skills"
                  class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span class="text-sm text-gray-700">{{ skill }}</span>
              </label>
            </div>
          </div>
        </template>

        <!-- 高级参数 -->
        <template v-if="activeTab === 'advanced'">
          <!-- 温度 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              温度 (Temperature): {{ localConfig.temperature.toFixed(2) }}
            </label>
            <input 
              v-model.number="localConfig.temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <p class="text-xs text-gray-500 mt-1">控制输出的随机性，0=确定性，2=高随机性</p>
          </div>

          <!-- 最大迭代次数 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              最大迭代次数: {{ localConfig.maxIters }}
            </label>
            <input 
              v-model.number="localConfig.maxIters"
              type="range"
              min="1"
              max="50"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <!-- 开关选项 -->
          <div class="space-y-3">
            <label class="flex items-center justify-between p-2 hover:bg-gray-50 rounded-md cursor-pointer">
              <div>
                <span class="text-sm font-medium text-gray-700">启用思考模式</span>
                <p class="text-xs text-gray-500">让模型展示推理过程</p>
              </div>
              <input 
                type="checkbox"
                v-model="localConfig.enableThinking"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
            <label class="flex items-center justify-between p-2 hover:bg-gray-50 rounded-md cursor-pointer">
              <div>
                <span class="text-sm font-medium text-gray-700">流式输出</span>
                <p class="text-xs text-gray-500">实时显示生成内容</p>
              </div>
              <input 
                type="checkbox"
                v-model="localConfig.stream"
                class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </label>
          </div>

          <!-- 自定义参数 -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-gray-700">自定义参数</label>
              <button 
                @click="addCustomParam"
                class="text-xs text-blue-600 hover:text-blue-700"
              >+ 添加参数</button>
            </div>
            <div class="space-y-2">
              <div 
                v-for="(param, index) in localConfig.customParams" 
                :key="index"
                class="flex gap-2 items-center"
              >
                <input 
                  v-model="param.key"
                  type="text"
                  placeholder="参数名"
                  class="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 outline-none"
                />
                <input 
                  v-model="param.value"
                  type="text"
                  placeholder="值"
                  class="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 outline-none"
                />
                <select 
                  v-model="param.type"
                  class="px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 outline-none"
                >
                  <option value="string">字符串</option>
                  <option value="number">数字</option>
                  <option value="boolean">布尔</option>
                  <option value="json">JSON</option>
                </select>
                <button 
                  @click="removeCustomParam(index)"
                  class="p-1 text-red-500 hover:bg-red-50 rounded"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </template>

        <!-- 输入变量 -->
        <template v-if="activeTab === 'variables'">
          <div class="mb-2">
            <p class="text-xs text-gray-500">定义此节点需要的输入变量，可在系统提示词中使用 {{变量名}} 引用</p>
          </div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">输入变量列表</label>
            <button 
              @click="addInputVariable"
              class="text-xs text-blue-600 hover:text-blue-700"
            >+ 添加变量</button>
          </div>
          <div class="space-y-3">
            <div 
              v-for="(variable, index) in localConfig.inputVariables" 
              :key="index"
              class="p-3 bg-gray-50 rounded-lg space-y-2"
            >
              <div class="flex items-center justify-between">
                <input 
                  v-model="variable.name"
                  type="text"
                  placeholder="变量名"
                  class="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 outline-none bg-white"
                />
                <button 
                  @click="removeInputVariable(index)"
                  class="ml-2 p-1 text-red-500 hover:bg-red-100 rounded"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <input 
                v-model="variable.description"
                type="text"
                placeholder="变量描述"
                class="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 outline-none bg-white"
              />
              <label class="flex items-center gap-2 text-sm text-gray-600">
                <input 
                  type="checkbox"
                  v-model="variable.required"
                  class="w-3 h-3 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                必填
              </label>
            </div>
            <div v-if="localConfig.inputVariables.length === 0" class="text-center py-4 text-gray-400 text-sm">
              暂无输入变量
            </div>
          </div>
        </template>
      </template>
    </div>
    
    <!-- 无选中节点 -->
    <div v-else class="flex-1 flex items-center justify-center p-4">
      <div class="text-center text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
        </svg>
        <p class="text-sm">点击节点进行配置</p>
      </div>
    </div>
    
    <!-- 底部按钮 -->
    <div v-if="selectedNode" class="p-4 border-t border-gray-200 space-y-2">
      <button 
        @click="handleSave"
        class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
      >
        保存配置
      </button>
      <button 
        @click="handleDelete"
        class="w-full px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors font-medium"
      >
        删除节点
      </button>
    </div>
  </div>
</template>
