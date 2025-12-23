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
  // 分类器节点配置
  classifierModel: 'qwen3-max',
  classifierCategories: [] as { id: string; name: string; description: string }[],
  // 技能智能体配置
  skillAgentSkills: [] as string[],
  skillAgentModel: 'qwen3-max',
  skillAgentMaxIters: 30,
  skillAgentSystemPrompt: '',
  // 对话智能体配置
  simpleAgentName: 'SimpleAgent',
  simpleAgentSystemPrompt: '',
  simpleAgentModel: 'qwen3-max',
  // 工具节点配置
  toolType: '',
  toolName: '',
  toolParams: {} as Record<string, any>,
  // 邮件发送工具参数
  emailTo: '',
  emailSubject: '',
  emailBody: '',
  emailBodyType: 'text' as 'text' | 'html',
  // HTTP请求工具参数
  httpUrl: '',
  httpMethod: 'GET' as 'GET' | 'POST' | 'PUT' | 'DELETE',
  httpHeaders: '' as string,
  httpBody: '',
  // 文件写入工具参数
  filePath: '',
  fileContent: '',
  fileAppend: false,
})

// 可用技能列表（从后端加载）
const availableSkillList = ref<{ name: string; path: string; description: string }[]>([])

// 加载可用技能列表
async function loadAvailableSkills() {
  try {
    const response = await fetch('http://localhost:8000/api/skills')
    if (response.ok) {
      const data = await response.json()
      availableSkillList.value = data.skills || []
    }
  } catch (e) {
    console.error('加载技能列表失败:', e)
  }
}

// 组件挂载时加载技能列表
import { onMounted } from 'vue'
onMounted(() => {
  loadAvailableSkills()
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
      classifierModel: 'qwen3-max',
      classifierCategories: [],
      skillAgentSkills: [],
      skillAgentModel: 'qwen3-max',
      skillAgentMaxIters: 30,
      skillAgentSystemPrompt: '',
      simpleAgentName: 'SimpleAgent',
      simpleAgentSystemPrompt: '',
      simpleAgentModel: 'qwen3-max',
    }
  } else if (node?.data?.skillAgentConfig) {
    // 技能智能体配置
    const config = node.data.skillAgentConfig
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
      classifierModel: 'qwen3-max',
      classifierCategories: [],
      skillAgentSkills: config.skills || [],
      skillAgentModel: config.model || 'qwen3-max',
      skillAgentMaxIters: config.maxIters || 30,
      skillAgentSystemPrompt: config.systemPrompt || '',
      simpleAgentName: 'SimpleAgent',
      simpleAgentSystemPrompt: '',
      simpleAgentModel: 'qwen3-max',
    }
  } else if (node?.data?.simpleAgentConfig) {
    // 对话智能体配置
    const config = node.data.simpleAgentConfig
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
      classifierModel: 'qwen3-max',
      classifierCategories: [],
      skillAgentSkills: [],
      skillAgentModel: 'qwen3-max',
      skillAgentMaxIters: 30,
      skillAgentSystemPrompt: '',
      simpleAgentName: config.name || 'SimpleAgent',
      simpleAgentSystemPrompt: config.systemPrompt || '',
      simpleAgentModel: config.model || 'qwen3-max',
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
      classifierModel: 'qwen3-max',
      classifierCategories: [],
      skillAgentSkills: [],
      skillAgentModel: 'qwen3-max',
      skillAgentMaxIters: 30,
      skillAgentSystemPrompt: '',
      simpleAgentName: 'SimpleAgent',
      simpleAgentSystemPrompt: '',
      simpleAgentModel: 'qwen3-max',
    }
  } else if (node?.data?.classifierConfig) {
    // 分类器节点配置
    const config = node.data.classifierConfig
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
      classifierModel: config.model || 'qwen3-max',
      classifierCategories: config.categories || [],
      skillAgentSkills: [],
      skillAgentModel: 'qwen3-max',
      skillAgentMaxIters: 30,
      skillAgentSystemPrompt: '',
      simpleAgentName: 'SimpleAgent',
      simpleAgentSystemPrompt: '',
      simpleAgentModel: 'qwen3-max',
    }
  } else if (node?.data?.toolConfig) {
    // 工具节点配置
    const config = node.data.toolConfig
    const params = config.params || {}
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
      classifierModel: 'qwen3-max',
      classifierCategories: [],
      skillAgentSkills: [],
      skillAgentModel: 'qwen3-max',
      skillAgentMaxIters: 30,
      skillAgentSystemPrompt: '',
      simpleAgentName: 'SimpleAgent',
      simpleAgentSystemPrompt: '',
      simpleAgentModel: 'qwen3-max',
      toolType: config.toolType || '',
      toolName: config.toolName || '',
      toolParams: params,
      emailTo: params.to || '',
      emailSubject: params.subject || '',
      emailBody: params.body || '',
      emailBodyType: params.bodyType || 'text',
      httpUrl: params.url || '',
      httpMethod: params.method || 'GET',
      httpHeaders: params.headers || '',
      httpBody: params.body || '',
      filePath: params.path || '',
      fileContent: params.content || '',
      fileAppend: params.append || false,
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
      classifierModel: 'qwen3-max',
      classifierCategories: [],
      skillAgentSkills: [],
      skillAgentModel: 'qwen3-max',
      skillAgentMaxIters: 30,
      skillAgentSystemPrompt: '',
      simpleAgentName: 'SimpleAgent',
      simpleAgentSystemPrompt: '',
      simpleAgentModel: 'qwen3-max',
      toolType: '',
      toolName: '',
      toolParams: {},
      emailTo: '',
      emailSubject: '',
      emailBody: '',
      emailBodyType: 'text',
      httpUrl: '',
      httpMethod: 'GET',
      httpHeaders: '',
      httpBody: '',
      filePath: '',
      fileContent: '',
      fileAppend: false,
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
    } else if (nodeType === 'classifier') {
      // 分类器节点
      store.updateNode(selectedNode.value.id, {
        data: {
          ...selectedNode.value.data,
          label: localConfig.value.name,
          classifierConfig: {
            model: localConfig.value.classifierModel,
            categories: localConfig.value.classifierCategories,
          },
        },
      })
    } else if (nodeType === 'skill-agent') {
      // 技能智能体节点
      store.updateNode(selectedNode.value.id, {
        data: {
          ...selectedNode.value.data,
          label: localConfig.value.name,
          skillAgentConfig: {
            skills: localConfig.value.skillAgentSkills,
            model: localConfig.value.skillAgentModel,
            maxIters: localConfig.value.skillAgentMaxIters,
            systemPrompt: localConfig.value.skillAgentSystemPrompt,
          },
        },
      })
    } else if (nodeType === 'simple-agent') {
      // 对话智能体节点
      store.updateNode(selectedNode.value.id, {
        data: {
          ...selectedNode.value.data,
          label: localConfig.value.name,
          simpleAgentConfig: {
            name: localConfig.value.simpleAgentName,
            systemPrompt: localConfig.value.simpleAgentSystemPrompt,
            model: localConfig.value.simpleAgentModel,
          },
        },
      })
    } else if (nodeType === 'tool') {
      // 工具节点
      let params: Record<string, any> = {}
      if (localConfig.value.toolType === 'email-send') {
        params = {
          to: localConfig.value.emailTo,
          subject: localConfig.value.emailSubject,
          body: localConfig.value.emailBody,
          bodyType: localConfig.value.emailBodyType,
        }
      } else if (localConfig.value.toolType === 'http-request') {
        params = {
          url: localConfig.value.httpUrl,
          method: localConfig.value.httpMethod,
          headers: localConfig.value.httpHeaders,
          body: localConfig.value.httpBody,
        }
      } else if (localConfig.value.toolType === 'file-write') {
        params = {
          path: localConfig.value.filePath,
          content: localConfig.value.fileContent,
          append: localConfig.value.fileAppend,
        }
      }
      store.updateNode(selectedNode.value.id, {
        data: {
          ...selectedNode.value.data,
          label: localConfig.value.name,
          toolConfig: {
            toolType: localConfig.value.toolType,
            toolName: localConfig.value.toolName,
            params,
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

function addClassifierCategory() {
  const id = `cat_${Date.now()}`
  localConfig.value.classifierCategories.push({ id, name: '', description: '' })
}

function removeClassifierCategory(index: number) {
  localConfig.value.classifierCategories.splice(index, 1)
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

      <!-- 分类器节点配置 -->
      <template v-if="selectedNode.type === 'classifier'">
        <!-- 模型选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">分类模型</label>
          <select 
            v-model="localConfig.classifierModel"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          >
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <!-- 分类列表 -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">分类 <span class="text-red-500">*</span></label>
            <button 
              @click="addClassifierCategory"
              class="text-xs text-cyan-600 hover:text-cyan-700 font-medium"
            >+ 添加分类</button>
          </div>
          
          <div class="space-y-3">
            <div 
              v-for="(category, index) in localConfig.classifierCategories" 
              :key="category.id"
              class="p-3 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-gray-500">分类 {{ index + 1 }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-gray-400">{{ index + 1 }}</span>
                  <button 
                    @click="removeClassifierCategory(index)"
                    class="p-1 text-red-500 hover:bg-red-100 rounded"
                    title="删除分类"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <input 
                v-model="category.name"
                type="text"
                placeholder="分类名称"
                class="w-full px-3 py-2 mb-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none"
              />
              <textarea 
                v-model="category.description"
                rows="2"
                placeholder="分类描述（用于 LLM 判断分类条件）"
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none resize-none"
              ></textarea>
            </div>
            
            <div v-if="localConfig.classifierCategories.length === 0" class="text-center py-6 text-gray-400 text-sm border-2 border-dashed border-gray-200 rounded-lg">
              <p>暂无分类</p>
              <p class="text-xs mt-1">点击上方"添加分类"按钮创建</p>
            </div>
          </div>
        </div>

        <!-- 使用说明 -->
        <div class="p-3 bg-cyan-50 border border-cyan-200 rounded-lg">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-cyan-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="text-xs text-cyan-700">
              <p class="font-medium mb-1">问题分类器：</p>
              <ul class="space-y-1 list-disc list-inside">
                <li>使用 LLM 智能分析用户输入并分类</li>
                <li>每个分类对应一个输出连接点</li>
                <li>根据分类结果路由到不同的下游节点</li>
                <li>分类描述越详细，分类越准确</li>
              </ul>
            </div>
          </div>
        </div>
      </template>
      
      <!-- 技能智能体配置 -->
      <template v-if="selectedNode.type === 'skill-agent'">
        <!-- 技能选择 -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">选择技能 <span class="text-red-500">*</span></label>
            <button 
              @click="loadAvailableSkills"
              class="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
            >刷新列表</button>
          </div>
          
          <div class="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-2">
            <div v-if="availableSkillList.length === 0" class="text-center py-4 text-gray-400 text-sm">
              <p>暂无可用技能</p>
              <p class="text-xs mt-1">请在 skill 目录下创建技能</p>
            </div>
            <label 
              v-for="skill in availableSkillList" 
              :key="skill.name"
              class="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
              :class="{ 'bg-emerald-50 border border-emerald-200': localConfig.skillAgentSkills[0] === skill.name }"
            >
              <input 
                type="radio" 
                name="skillAgent"
                :value="skill.name"
                :checked="localConfig.skillAgentSkills[0] === skill.name"
                @change="localConfig.skillAgentSkills = [skill.name]"
                class="mt-0.5 border-gray-300 text-emerald-500 focus:ring-emerald-500"
              />
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium text-gray-700">{{ skill.name }}</div>
                <div class="text-xs text-gray-500 truncate">{{ skill.description || '无描述' }}</div>
              </div>
            </label>
          </div>
          
          <div v-if="localConfig.skillAgentSkills.length > 0" class="mt-2 text-xs text-gray-500">
            已选择: {{ localConfig.skillAgentSkills[0] }}
          </div>
        </div>

        <!-- 模型选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">模型</label>
          <select 
            v-model="localConfig.skillAgentModel"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
          >
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <!-- 最大迭代次数 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">最大迭代次数</label>
          <input 
            v-model.number="localConfig.skillAgentMaxIters"
            type="number"
            min="1"
            max="100"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
          />
        </div>

        <!-- 自定义系统提示词 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            系统提示词 <span class="text-gray-400 text-xs">(可选)</span>
          </label>
          <textarea 
            v-model="localConfig.skillAgentSystemPrompt"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all resize-none"
            placeholder="留空则根据选择的技能自动生成..."
          ></textarea>
        </div>

        <!-- 使用说明 -->
        <div class="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="text-xs text-emerald-700">
              <p class="font-medium mb-1">技能智能体：</p>
              <ul class="space-y-1 list-disc list-inside">
                <li>选择一个或多个技能来增强智能体能力</li>
                <li>技能会自动加载到智能体的工具集中</li>
                <li>执行时会根据技能动态创建智能体</li>
                <li>可自定义系统提示词或使用自动生成</li>
              </ul>
            </div>
          </div>
        </div>
      </template>

      <!-- 工具节点配置 -->
      <template v-if="selectedNode.type === 'tool'">
        <!-- 工具类型 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">工具类型</label>
          <select 
            v-model="localConfig.toolType"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
          >
            <option value="">选择工具类型...</option>
            <option value="email-send">邮件发送</option>
            <option value="http-request">HTTP请求</option>
            <option value="file-write">文件写入</option>
          </select>
        </div>

        <!-- 邮件发送配置 -->
        <template v-if="localConfig.toolType === 'email-send'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">收件人 <span class="text-red-500">*</span></label>
            <input 
              v-model="localConfig.emailTo"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
              placeholder="多个收件人用逗号分隔，支持变量 {{email}}"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮件主题 <span class="text-red-500">*</span></label>
            <input 
              v-model="localConfig.emailSubject"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
              placeholder="支持变量 {{subject}}"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮件内容 <span class="text-red-500">*</span></label>
            <textarea 
              v-model="localConfig.emailBody"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all resize-none"
              placeholder="支持变量 {{content}}，可引用上游节点输出"
            ></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">内容类型</label>
            <select 
              v-model="localConfig.emailBodyType"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
            >
              <option value="text">纯文本</option>
              <option value="html">HTML</option>
            </select>
          </div>
        </template>

        <!-- HTTP请求配置 -->
        <template v-if="localConfig.toolType === 'http-request'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">请求URL <span class="text-red-500">*</span></label>
            <input 
              v-model="localConfig.httpUrl"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
              placeholder="https://api.example.com/endpoint"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">请求方法</label>
            <select 
              v-model="localConfig.httpMethod"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">请求头 (JSON)</label>
            <textarea 
              v-model="localConfig.httpHeaders"
              rows="2"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all resize-none font-mono text-sm"
              placeholder='{"Content-Type": "application/json"}'
            ></textarea>
          </div>
          <div v-if="localConfig.httpMethod !== 'GET'">
            <label class="block text-sm font-medium text-gray-700 mb-1">请求体</label>
            <textarea 
              v-model="localConfig.httpBody"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all resize-none font-mono text-sm"
              placeholder="支持变量 {{data}}"
            ></textarea>
          </div>
        </template>

        <!-- 文件写入配置 -->
        <template v-if="localConfig.toolType === 'file-write'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">文件路径 <span class="text-red-500">*</span></label>
            <input 
              v-model="localConfig.filePath"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
              placeholder="/path/to/file.txt"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">文件内容 <span class="text-red-500">*</span></label>
            <textarea 
              v-model="localConfig.fileContent"
              rows="4"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all resize-none"
              placeholder="支持变量 {{content}}"
            ></textarea>
          </div>
          <label class="flex items-center gap-2 p-2 hover:bg-gray-50 rounded-md cursor-pointer">
            <input 
              type="checkbox"
              v-model="localConfig.fileAppend"
              class="w-4 h-4 text-amber-600 border-gray-300 rounded focus:ring-amber-500"
            />
            <span class="text-sm text-gray-700">追加模式（不覆盖原有内容）</span>
          </label>
        </template>

        <!-- 使用说明 -->
        <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="text-xs text-amber-700">
              <p class="font-medium mb-1">工具节点：</p>
              <ul class="space-y-1 list-disc list-inside">
                <li>执行具体的操作任务（发邮件、调接口等）</li>
                <li>支持使用 { { 变量名 } } 引用上游节点输出</li>
                <li>执行结果会传递给下游节点</li>
              </ul>
            </div>
          </div>
        </div>
      </template>

      <!-- 对话智能体配置 -->
      <template v-if="selectedNode.type === 'simple-agent'">
        <!-- 模型选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">模型</label>
          <select 
            v-model="localConfig.simpleAgentModel"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
          >
            <option v-for="model in availableModels" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <!-- 系统提示词 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            系统提示词 <span class="text-red-500">*</span>
          </label>
          <textarea 
            v-model="localConfig.simpleAgentSystemPrompt"
            rows="6"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all resize-none"
            placeholder="定义智能体的行为和能力，例如：你是一个内容分析助手，直接从输入中提取用户需要的信息..."
          ></textarea>
        </div>

        <!-- 使用说明 -->
        <div class="p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div class="text-xs text-purple-700">
              <p class="font-medium mb-1">对话智能体：</p>
              <ul class="space-y-1 list-disc list-inside">
                <li>纯对话模型，不调用任何工具</li>
                <li>适合内容分析、总结、问答等场景</li>
                <li>直接根据系统提示词和输入生成回复</li>
                <li>执行速度快，适合简单任务</li>
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
