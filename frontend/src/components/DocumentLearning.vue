<template>
  <div class="flex flex-col h-full bg-slate-50">
    <!-- 顶部标题栏 -->
    <div class="flex justify-between items-center px-6 py-4 bg-gradient-to-r from-primary to-primary-700 text-white shadow-md">
      <h1 class="text-xl font-semibold">智能文档学习与规则生成器</h1>
      <button 
        class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-white/20 hover:bg-white/30 border border-white/30 rounded-lg transition-colors"
        @click="goBack"
      >
        ← 返回
      </button>
    </div>

    <!-- 步骤指示器 -->
    <div class="flex items-center justify-center gap-4 py-6 bg-white border-b border-slate-200">
      <div class="flex items-center gap-2">
        <span 
          class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-semibold transition-colors"
          :class="currentStep >= 1 ? 'bg-primary text-white' : 'bg-slate-200 text-slate-500'"
        >1</span>
        <span class="text-sm font-medium" :class="currentStep >= 1 ? 'text-slate-900' : 'text-slate-400'">上传文档</span>
      </div>
      <div class="w-12 h-0.5" :class="currentStep > 1 ? 'bg-primary' : 'bg-slate-200'"></div>
      <div class="flex items-center gap-2">
        <span 
          class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-semibold transition-colors"
          :class="currentStep >= 2 ? 'bg-primary text-white' : 'bg-slate-200 text-slate-500'"
        >2</span>
        <span class="text-sm font-medium" :class="currentStep >= 2 ? 'text-slate-900' : 'text-slate-400'">智能标注</span>
      </div>
      <div class="w-12 h-0.5" :class="currentStep > 2 ? 'bg-primary' : 'bg-slate-200'"></div>
      <div class="flex items-center gap-2">
        <span 
          class="w-8 h-8 flex items-center justify-center rounded-full text-sm font-semibold transition-colors"
          :class="currentStep >= 3 ? 'bg-primary text-white' : 'bg-slate-200 text-slate-500'"
        >3</span>
        <span class="text-sm font-medium" :class="currentStep >= 3 ? 'text-slate-900' : 'text-slate-400'">规则生成</span>
      </div>
    </div>

    <!-- 步骤1: 上传文档 -->
    <div v-if="currentStep === 1" class="flex-1 flex items-start justify-center p-8 overflow-auto">
      <div class="w-full max-w-xl bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <h2 class="text-lg font-semibold text-slate-900 mb-6 text-center">上传新文档进行学习</h2>
        
        <div 
          class="border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all"
          :class="isDragover ? 'border-primary bg-primary/5' : 'border-slate-300 hover:border-primary/50 hover:bg-slate-50'"
          @dragover.prevent="isDragover = true"
          @dragleave="isDragover = false"
          @drop.prevent="handleDrop"
          @click="triggerUpload"
        >
          <div class="text-4xl mb-3">📄</div>
          <p class="text-slate-700 font-medium">点击或拖拽文件到此处</p>
          <p class="text-sm text-slate-400 mt-1">支持 PDF, Word, 图片等格式</p>
        </div>
        <input 
          ref="fileInput" 
          type="file" 
          accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.bmp" 
          class="hidden" 
          @change="handleFileSelect"
        />
        
        <div v-if="selectedFile" class="flex items-center gap-3 mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span class="text-2xl">📎</span>
          <span class="flex-1 text-sm font-medium text-slate-700 truncate">{{ selectedFile.name }}</span>
          <span class="text-xs text-slate-400">{{ formatSize(selectedFile.size) }}</span>
          <button 
            class="w-6 h-6 flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
            @click.stop="selectedFile = null"
          >×</button>
        </div>

        <div class="mt-6 space-y-3">
          <p class="text-sm font-medium text-slate-700">请选择文档类型：</p>
          <label 
            class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all"
            :class="docType === 'sds' ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-slate-300'"
          >
            <input type="radio" v-model="docType" value="sds" class="mt-1 accent-primary" />
            <div>
              <span class="text-sm font-medium text-slate-900">标准SDS/MSDS</span>
              <p class="text-xs text-slate-500 mt-0.5">系统将按标准流程解析</p>
            </div>
          </label>
          <label 
            class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all"
            :class="docType === 'other' ? 'border-primary bg-primary/5' : 'border-slate-200 hover:border-slate-300'"
          >
            <input type="radio" v-model="docType" value="other" class="mt-1 accent-primary" />
            <div>
              <span class="text-sm font-medium text-slate-900">其他文档</span>
              <p class="text-xs text-slate-500 mt-0.5">将启动智能学习与规则生成流程</p>
            </div>
          </label>
        </div>

        <button 
          class="w-full mt-6 py-3 px-4 bg-primary hover:bg-primary-600 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
          :disabled="!selectedFile || uploading"
          @click="uploadAndProcess"
        >
          <span v-if="uploading" class="animate-spin">⏳</span>
          {{ uploading ? '处理中...' : '开始处理' }}
        </button>
      </div>
    </div>

    <!-- 步骤2: 智能标注 -->
    <div v-if="currentStep === 2" class="flex-1 flex flex-col overflow-hidden">
      <!-- 标注头部 -->
      <div class="flex justify-between items-center px-6 py-3 bg-white border-b border-slate-200">
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium text-slate-700">{{ document?.filename }}</span>
          <span 
            class="px-2 py-0.5 text-xs font-medium rounded-full"
            :class="document?.status === 'processed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'"
          >{{ getStatusLabel(document?.status) }}</span>
        </div>
        <div class="flex gap-2">
          <button class="px-3 py-1.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors" @click="saveDraft">保存草稿</button>
          <button class="px-3 py-1.5 text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors" @click="currentStep = 1">放弃</button>
        </div>
      </div>

      <!-- 选择文本后的浮动菜单 -->
      <Teleport to="body">
        <div 
          v-if="showFieldMenu" 
          class="fixed bg-white rounded-lg shadow-lg border border-slate-200 py-2 min-w-[160px] z-50"
          :style="{ top: menuPosition.y + 'px', left: menuPosition.x + 'px' }"
          @mousedown.stop
        >
          <div class="px-3 py-1.5 text-xs text-slate-500 border-b border-slate-100">选择要标注的字段:</div>
          <div 
            v-for="field in annotationFields" 
            :key="field.name"
            class="px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 cursor-pointer transition-colors"
            @click.stop="assignToField(field.name)"
          >
            {{ field.label }}
          </div>
          <div class="px-3 py-2 text-sm text-slate-400 hover:bg-slate-50 cursor-pointer border-t border-slate-100 mt-1" @click.stop="cancelSelection">取消</div>
        </div>
      </Teleport>

      <!-- 主内容区 -->
      <div class="flex-1 flex gap-4 p-4 overflow-hidden">
        <!-- 左侧：文档原文 -->
        <div class="flex-1 flex flex-col bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div class="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
            <h3 class="text-sm font-semibold text-slate-800">文档原文</h3>
            <span class="text-xs text-slate-400">(选择文本后可标注)</span>
          </div>
          <div 
            class="flex-1 p-4 overflow-auto text-sm leading-relaxed whitespace-pre-wrap break-all cursor-text select-text"
            ref="docTextRef" 
            @mouseup="handleTextSelection"
          >
            <template v-for="(segment, index) in textSegments" :key="index">
              <span 
                v-if="segment.type === 'highlight'"
                class="bg-amber-100 border-b-2 border-dashed border-amber-400 cursor-pointer px-0.5 hover:bg-amber-200 transition-colors"
                :class="{ 'bg-green-100 border-green-400': segment.confirmed }"
                :data-entity="segment.entityType"
                @click="confirmHighlight(segment)"
              >{{ segment.text }}</span>
              <span v-else class="select-text">{{ segment.text }}</span>
            </template>
          </div>
        </div>

        <!-- 右侧：信息卡片 -->
        <div class="w-96 flex flex-col gap-4 overflow-auto">
          <!-- 标注关键信息 -->
          <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 class="text-sm font-semibold text-slate-800 mb-1">1. 标注关键信息</h3>
            <p class="text-xs text-slate-400 mb-3">从左侧文档中选择文本进行标注</p>
            
            <div class="space-y-2">
              <div 
                v-for="field in annotationFields" 
                :key="field.name"
                class="flex items-center gap-2"
              >
                <label class="w-20 text-xs text-slate-500 flex-shrink-0">{{ field.label }}:</label>
                <div class="flex-1 flex items-center gap-1">
                  <input 
                    v-model="annotations[field.name]"
                    :placeholder="selectingField === field.name ? '请在左侧选择...' : '点击标注'"
                    class="flex-1 px-2 py-1.5 text-sm border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    :class="selectingField === field.name ? 'border-primary bg-primary/5' : 'border-slate-200'"
                    @focus="startFieldSelection(field.name)"
                    @blur="endFieldSelection"
                  />
                  <button 
                    v-if="annotations[field.name]" 
                    class="w-6 h-6 flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                    @click="clearField(field.name)"
                  >×</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 做出判断 -->
          <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 class="text-sm font-semibold text-slate-800 mb-3">2. 做出判断</h3>
            <div class="flex gap-3">
              <label 
                class="flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer transition-all"
                :class="judgment === 'hazardous' ? 'border-red-400 bg-red-50 text-red-700' : 'border-slate-200 hover:border-slate-300'"
              >
                <input type="radio" v-model="judgment" value="hazardous" class="accent-red-500" />
                <span class="text-sm font-medium">是危险品</span>
              </label>
              <label 
                class="flex-1 flex items-center justify-center gap-2 p-3 rounded-lg border cursor-pointer transition-all"
                :class="judgment === 'non_hazardous' ? 'border-green-400 bg-green-50 text-green-700' : 'border-slate-200 hover:border-slate-300'"
              >
                <input type="radio" v-model="judgment" value="non_hazardous" class="accent-green-500" />
                <span class="text-sm font-medium">非危险品</span>
              </label>
            </div>
          </div>

          <!-- 选择判断依据 -->
          <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
            <h3 class="text-sm font-semibold text-slate-800 mb-1">3. 选择判断依据</h3>
            <p class="text-xs text-slate-400 mb-3">请勾选作为核心判断依据的字段</p>
            <div class="space-y-2">
              <label 
                v-for="field in annotationFields" 
                :key="field.name"
                class="flex items-center gap-2 p-2 rounded-lg transition-colors"
                :class="annotations[field.name] ? 'hover:bg-slate-50 cursor-pointer' : 'opacity-50 cursor-not-allowed'"
              >
                <input 
                  type="checkbox" 
                  v-model="basisFields"
                  :value="field.name"
                  :disabled="!annotations[field.name]"
                  class="accent-primary"
                />
                <span class="text-sm text-slate-700">{{ field.label }}: <span class="text-slate-500">{{ annotations[field.name] || '(未标注)' }}</span></span>
              </label>
            </div>
          </div>

          <button 
            class="w-full py-3 px-4 bg-primary hover:bg-primary-600 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            :disabled="!canGenerateRules"
            @click="generateRules"
          >
            完成标注并生成规则
          </button>
        </div>
      </div>
    </div>

    <!-- 步骤3: 规则生成与审核 -->
    <div v-if="currentStep === 3" class="flex-1 flex flex-col p-6 overflow-auto">
      <div class="max-w-4xl mx-auto w-full">
        <!-- 头部 -->
        <div class="text-center mb-6">
          <h2 class="text-xl font-semibold text-slate-900">规则生成与入库</h2>
          <p class="text-sm text-slate-500 mt-1">系统已根据您的标注和判断，生成了以下规则草稿。</p>
        </div>

        <!-- 来源信息 -->
        <div class="bg-slate-50 rounded-lg p-4 mb-6 flex gap-6">
          <p class="text-sm text-slate-600"><span class="font-medium text-slate-700">来源文档：</span>{{ document?.filename }}</p>
          <p class="text-sm text-slate-600">
            <span class="font-medium text-slate-700">您的判断：</span>
            <span :class="judgment === 'hazardous' ? 'text-red-600' : 'text-green-600'">
              {{ judgment === 'hazardous' ? '是危险品' : '非危险品' }}
            </span>
          </p>
        </div>

        <!-- 规则草稿列表 -->
        <div class="space-y-4 mb-6">
          <div v-for="(rule, index) in ruleDrafts" :key="index" class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div class="flex justify-between items-center px-4 py-3 bg-slate-50 border-b border-slate-100">
              <span class="text-sm font-semibold text-slate-700">规则草稿 {{ index + 1 }}</span>
              <button class="text-sm text-primary hover:text-primary-600 transition-colors" @click="editRule(rule)">编辑规则逻辑</button>
            </div>
            
            <div class="p-4">
              <p class="font-medium text-slate-900">{{ rule.name }}</p>
              <p class="text-sm text-slate-500 mt-1">{{ rule.description }}</p>
              
              <div class="mt-4 space-y-3">
                <div class="bg-blue-50 rounded-lg p-3">
                  <span class="text-xs font-semibold text-blue-600 uppercase">IF (如果)</span>
                  <ul class="mt-2 space-y-1">
                    <li v-for="(cond, ci) in rule.conditions" :key="ci" class="text-sm text-slate-700 flex items-start gap-2">
                      <span class="text-blue-400 mt-0.5">•</span>
                      {{ cond.description }}
                    </li>
                  </ul>
                </div>
                <div class="bg-green-50 rounded-lg p-3">
                  <span class="text-xs font-semibold text-green-600 uppercase">THEN (那么)</span>
                  <ul class="mt-2 space-y-1">
                    <li class="text-sm text-slate-700 flex items-start gap-2">
                      <span class="text-green-400 mt-0.5">•</span>
                      判定结果设置为 <span class="font-medium" :class="rule.result === 'hazardous' ? 'text-red-600' : 'text-green-600'">{{ rule.result === 'hazardous' ? '是危险品' : '非危险品' }}</span>
                    </li>
                    <li v-if="rule.suggested_class" class="text-sm text-slate-700 flex items-start gap-2">
                      <span class="text-green-400 mt-0.5">•</span>
                      危险类别建议为 <span class="font-medium text-amber-600">{{ rule.suggested_class }}</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            <div class="px-4 py-3 border-t border-slate-100">
              <button class="text-sm text-red-500 hover:text-red-600 transition-colors" @click="removeRule(index)">删除此条规则</button>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="flex items-center justify-center gap-4">
          <button 
            class="px-6 py-2.5 bg-primary hover:bg-primary-600 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center gap-2"
            :disabled="ruleDrafts.length === 0"
            @click="approveRules"
          >
            ✓ 批准并存入规则库
          </button>
          <button 
            class="px-6 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors flex items-center gap-2"
            @click="submitForReview"
          >
            📤 提交给管理员审核
          </button>
          <button 
            class="px-4 py-2.5 text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
            @click="currentStep = 2"
          >
            ← 返回修改标注
          </button>
        </div>
      </div>
    </div>

    <!-- 加载中遮罩 -->
    <div v-if="processing" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl p-8 flex flex-col items-center gap-4 shadow-xl">
        <div class="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p class="text-slate-700 font-medium">{{ processingMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const API_BASE = '/api/hazmat'

// 点击外部关闭菜单
function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.field-select-menu')) {
    showFieldMenu.value = false
  }
}

onMounted(() => {
  window.document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.document.removeEventListener('click', handleClickOutside)
})

// 状态
const currentStep = ref(1)
const selectedFile = ref<File | null>(null)
const docType = ref('other')
const isDragover = ref(false)
const uploading = ref(false)
const processing = ref(false)
const processingMessage = ref('')

const document = ref<any>(null)
const rawText = ref('')
const aiHighlights = ref<any[]>([])
const annotations = ref<Record<string, string>>({})
const judgment = ref<'hazardous' | 'non_hazardous' | ''>('')
const basisFields = ref<string[]>([])
const selectingField = ref<string | null>(null)
const showFieldMenu = ref(false)
const menuPosition = ref({ x: 0, y: 0 })
const pendingSelection = ref('')
const ruleDrafts = ref<any[]>([])

const fileInput = ref<HTMLInputElement | null>(null)
const docTextRef = ref<HTMLDivElement | null>(null)

// 标注字段定义
const annotationFields = ref([
  { name: 'product_name', label: '产品名称' },
  { name: 'cas_number', label: 'CAS号' },
  { name: 'un_number', label: 'UN编号' },
  { name: 'flash_point', label: '闪点' },
  { name: 'boiling_point', label: '沸点' },
  { name: 'hazard_class', label: '危险类别' },
  { name: 'packing_group', label: '包装组' },
  { name: 'hazard_keyword', label: '危险性关键词' },
])

// 计算属性
const canGenerateRules = computed(() => {
  return judgment.value && basisFields.value.length > 0
})

const textSegments = computed(() => {
  if (!rawText.value) return []
  
  const text = rawText.value
  const highlights = aiHighlights.value || []
  const segments: any[] = []
  
  // 按位置排序高亮
  const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start)
  
  let lastEnd = 0
  for (const h of sortedHighlights) {
    // 添加高亮前的普通文本
    if (h.start > lastEnd) {
      segments.push({
        type: 'text',
        text: text.substring(lastEnd, h.start)
      })
    }
    // 添加高亮文本
    segments.push({
      type: 'highlight',
      text: h.text,
      entityType: h.entity_type,
      confidence: h.confidence,
      suggestedValue: h.suggested_value,
      confirmed: false
    })
    lastEnd = h.end
  }
  // 添加最后的普通文本
  if (lastEnd < text.length) {
    segments.push({
      type: 'text',
      text: text.substring(lastEnd)
    })
  }
  
  return segments
})

// 方法
function getHeaders() {
  const token = userStore.token.value || localStorage.getItem('token')
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    'uploading': '上传中',
    'preprocessing': 'AI预处理中',
    'annotating': '待标注',
    'generating': '规则生成中',
    'pending_review': '待审核',
    'approved': '已批准',
    'rejected': '已拒绝',
    'completed': '已完成'
  }
  return labels[status] || status
}

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
  }
}

function handleDrop(event: DragEvent) {
  isDragover.value = false
  if (event.dataTransfer?.files.length) {
    selectedFile.value = event.dataTransfer.files[0]
  }
}

async function uploadAndProcess() {
  if (!selectedFile.value) return
  
  uploading.value = true
  processing.value = true
  processingMessage.value = '正在上传文档...'
  
  try {
    // 上传文件
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    const uploadRes = await fetch(`${API_BASE}/learning/upload?doc_type=${docType.value}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token.value || localStorage.getItem('token')}`
      },
      body: formData
    })
    const uploadData = await uploadRes.json()
    
    if (!uploadData.success) {
      throw new Error(uploadData.detail || '上传失败')
    }
    
    const docId = uploadData.data.id
    
    // AI预处理
    processingMessage.value = 'AI正在阅读和预分析文档，请稍候...'
    
    const preprocessRes = await fetch(`${API_BASE}/learning/${docId}/preprocess`, {
      method: 'POST',
      headers: getHeaders()
    })
    const preprocessData = await preprocessRes.json()
    
    if (!preprocessData.success) {
      throw new Error(preprocessData.detail || '预处理失败')
    }
    
    // 更新状态
    document.value = { id: docId, filename: selectedFile.value.name, status: preprocessData.data.status }
    rawText.value = preprocessData.data.raw_text
    aiHighlights.value = preprocessData.data.ai_highlights
    
    // 进入标注步骤
    currentStep.value = 2
    
  } catch (error: any) {
    alert('处理失败: ' + error.message)
  } finally {
    uploading.value = false
    processing.value = false
  }
}

function confirmHighlight(segment: any) {
  // 点击高亮区域确认标注
  const fieldName = segment.entityType
  if (fieldName && annotationFields.value.some(f => f.name === fieldName)) {
    annotations.value[fieldName] = segment.suggestedValue || segment.text
    segment.confirmed = true
  }
}

function startFieldSelection(fieldName: string) {
  selectingField.value = fieldName
}

function endFieldSelection() {
  setTimeout(() => {
    selectingField.value = null
  }, 200)
}

function handleTextSelection(event: MouseEvent) {
  const selection = window.getSelection()
  const selectedText = selection?.toString().trim()
  
  if (!selectedText) {
    showFieldMenu.value = false
    return
  }
  
  // 如果已有选中字段，直接赋值
  if (selectingField.value) {
    annotations.value[selectingField.value] = selectedText
    selection?.removeAllRanges()
    selectingField.value = null
    return
  }
  
  // 否则显示字段选择菜单
  pendingSelection.value = selectedText
  menuPosition.value = {
    x: event.clientX - 100,
    y: event.clientY + 10
  }
  showFieldMenu.value = true
}

function assignToField(fieldName: string) {
  if (pendingSelection.value) {
    annotations.value[fieldName] = pendingSelection.value
  }
  showFieldMenu.value = false
  pendingSelection.value = ''
  window.getSelection()?.removeAllRanges()
}

function cancelSelection() {
  showFieldMenu.value = false
  pendingSelection.value = ''
  window.getSelection()?.removeAllRanges()
}

function clearField(fieldName: string) {
  annotations.value[fieldName] = ''
  // 从判断依据中移除
  const idx = basisFields.value.indexOf(fieldName)
  if (idx > -1) {
    basisFields.value.splice(idx, 1)
  }
}

async function saveDraft() {
  if (!document.value?.id) return
  
  try {
    const annotationList = Object.entries(annotations.value)
      .filter(([_, value]) => value)
      .map(([field, value]) => ({
        field,
        value,
        text_span: value,
        start: 0,
        end: 0,
        is_basis: basisFields.value.includes(field)
      }))
    
    await fetch(`${API_BASE}/learning/${document.value.id}/annotations`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        file_id: document.value.id,
        annotations: annotationList,
        judgment: judgment.value || 'hazardous',
        basis_fields: basisFields.value
      })
    })
    
    alert('草稿已保存')
  } catch (error) {
    console.error('保存草稿失败:', error)
  }
}

async function generateRules() {
  if (!document.value?.id) return
  
  processing.value = true
  processingMessage.value = '正在生成规则...'
  
  try {
    // 先保存标注
    await saveDraft()
    
    // 生成规则
    const res = await fetch(
      `${API_BASE}/learning/${document.value.id}/generate-rules?${basisFields.value.map(f => `basis_fields=${f}`).join('&')}`,
      {
        method: 'POST',
        headers: getHeaders()
      }
    )
    const data = await res.json()
    
    if (data.success) {
      ruleDrafts.value = data.data.rule_drafts
      currentStep.value = 3
    } else {
      throw new Error(data.detail || '规则生成失败')
    }
  } catch (error: any) {
    alert('规则生成失败: ' + error.message)
  } finally {
    processing.value = false
  }
}

function editRule(rule: any) {
  // TODO: 打开规则编辑对话框
  alert('规则编辑功能开发中...')
}

function removeRule(index: number) {
  ruleDrafts.value.splice(index, 1)
}

async function approveRules() {
  processing.value = true
  processingMessage.value = '正在批准规则...'
  
  try {
    for (const rule of ruleDrafts.value) {
      if (rule.id) {
        await fetch(`${API_BASE}/rule-drafts/${rule.id}/review?action=approve`, {
          method: 'POST',
          headers: getHeaders()
        })
      }
    }
    
    alert('规则已批准并存入规则库！')
    goBack()
  } catch (error: any) {
    alert('批准失败: ' + error.message)
  } finally {
    processing.value = false
  }
}

async function submitForReview() {
  alert('规则已提交给管理员审核，请等待审核结果。')
  goBack()
}

function goBack() {
  // 返回危险品识别主页面
  const event = new CustomEvent('closeLearningMode')
  window.dispatchEvent(event)
}

// 加载字段定义
onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/annotation-fields`)
    const data = await res.json()
    if (data.success) {
      annotationFields.value = data.data
    }
  } catch (error) {
    console.error('加载字段定义失败:', error)
  }
})
</script>

<style>
/* 全局样式确保文本可选择 */
.select-text,
.select-text * {
  user-select: text !important;
  -webkit-user-select: text !important;
  -moz-user-select: text !important;
}

/* 文本选中高亮 */
::selection {
  background: rgba(59, 130, 246, 0.3);
}
</style>
