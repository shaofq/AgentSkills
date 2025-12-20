<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'

// amis 渲染器引用
const amisPreviewRef = ref<HTMLElement | null>(null)
let amisInstance: any = null

// 动态加载 amis SDK
const amisLoaded = ref(false)
const amisLoadError = ref('')

async function loadAmisSDK() {
  if ((window as any).amisRequire || (window as any).amis) {
    amisLoaded.value = true
    return
  }
  
  try {
    // 使用 amis 3.x 版本的 SDK（更稳定）
    const cssLinks = [
      'https://unpkg.com/amis@6.13.0/lib/themes/cxd.css',
      'https://unpkg.com/amis@6.13.0/lib/helper.css',
      'https://unpkg.com/amis@6.13.0/sdk/iconfont.css'
    ]
    
    for (const href of cssLinks) {
      if (!document.querySelector(`link[href="${href}"]`)) {
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = href
        document.head.appendChild(link)
      }
    }
    
    // 加载 amis JS SDK
    await new Promise<void>((resolve, reject) => {
      const script = document.createElement('script')
      script.src = 'https://unpkg.com/amis@6.13.0/sdk/sdk.js'
      script.onload = () => {
        // 等待 amis 初始化
        setTimeout(() => resolve(), 100)
      }
      script.onerror = () => reject(new Error('加载 amis SDK 失败'))
      document.head.appendChild(script)
    })
    
    amisLoaded.value = true
  } catch (e: any) {
    amisLoadError.value = e.message
  }
}

// 渲染 amis 配置
function renderAmis(schema: any) {
  if (!amisLoaded.value || !amisPreviewRef.value) return
  
  const amisLib = (window as any).amisRequire ? (window as any).amisRequire('amis/embed') : (window as any).amis
  if (!amisLib) {
    console.error('amis SDK 未正确加载')
    return
  }
  
  // 清除之前的内容
  if (amisPreviewRef.value) {
    amisPreviewRef.value.innerHTML = ''
  }
  
  // 清除之前的实例
  if (amisInstance && amisInstance.unmount) {
    try {
      amisInstance.unmount()
    } catch (e) {
      // 忽略卸载错误
    }
    amisInstance = null
  }
  
  // 渲染新的配置
  try {
    // 尝试不同的 API
    if (typeof amisLib.embed === 'function') {
      amisInstance = amisLib.embed(
        amisPreviewRef.value,
        schema,
        {},
        { theme: 'cxd' }
      )
    } else if (typeof amisLib === 'function') {
      amisInstance = amisLib(
        amisPreviewRef.value,
        schema,
        {},
        { theme: 'cxd' }
      )
    } else {
      // 如果都不行，显示 JSON
      amisPreviewRef.value.innerHTML = `<pre style="padding: 16px; background: #f5f5f5; border-radius: 8px; overflow: auto;">${JSON.stringify(schema, null, 2)}</pre>`
    }
  } catch (e) {
    console.error('amis 渲染失败:', e)
    // 降级显示 JSON
    if (amisPreviewRef.value) {
      amisPreviewRef.value.innerHTML = `
        <div style="padding: 16px;">
          <div style="color: #f59e0b; margin-bottom: 8px;">⚠️ amis 渲染失败，显示原始配置：</div>
          <pre style="padding: 16px; background: #1f2937; color: #f3f4f6; border-radius: 8px; overflow: auto; font-size: 12px;">${JSON.stringify(schema, null, 2)}</pre>
        </div>
      `
    }
  }
}

// 消息类型
interface Message {
  id: string
  from: 'user' | 'assistant'
  content: string
  loading?: boolean
  amisCode?: any
}

// 状态
const messages = ref<Message[]>([])
const inputValue = ref('')
const isLoading = ref(false)
const activeTab = ref<'preview' | 'code'>('preview')
const currentAmisCode = ref<any>(null)
const messagesContainer = ref<HTMLElement | null>(null)

// 监听 amis 代码变化
watch(() => currentAmisCode.value, (newCode) => {
  if (newCode && activeTab.value === 'preview') {
    nextTick(() => renderAmis(newCode))
  }
})

// 监听标签切换
watch(() => activeTab.value, (tab) => {
  if (tab === 'preview' && currentAmisCode.value) {
    nextTick(() => renderAmis(currentAmisCode.value))
  }
})

onMounted(() => {
  loadAmisSDK()
})

onUnmounted(() => {
  if (amisInstance) {
    amisInstance.unmount()
  }
})

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 发送消息
async function sendMessage() {
  if (!inputValue.value.trim() || isLoading.value) return
  
  const userMessage = inputValue.value.trim()
  inputValue.value = ''
  
  // 添加用户消息
  messages.value.push({
    id: `msg_${Date.now()}`,
    from: 'user',
    content: userMessage
  })
  
  // 添加助手消息（加载状态）
  const assistantMsgId = `msg_${Date.now()}_assistant`
  messages.value.push({
    id: assistantMsgId,
    from: 'assistant',
    content: '',
    loading: true
  })
  
  scrollToBottom()
  isLoading.value = true
  
  try {
    // 使用 SSE 流式请求
    const response = await fetch('http://localhost:8000/api/code-assistant/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage })
    })
    
    if (!response.ok) {
      throw new Error('请求失败')
    }
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    
    if (!reader) {
      throw new Error('无法读取响应')
    }
    
    let fullContent = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.type === 'start' || data.type === 'thinking') {
              // 更新状态消息
              const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
              if (msgIndex !== -1) {
                messages.value[msgIndex].content = data.message
              }
            } else if (data.type === 'amis_code') {
              // 收到 amis 代码
              currentAmisCode.value = data.code
              const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
              if (msgIndex !== -1) {
                messages.value[msgIndex].amisCode = data.code
              }
            } else if (data.type === 'content') {
              // 收到完整内容
              fullContent = data.content
              const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
              if (msgIndex !== -1) {
                messages.value[msgIndex].content = fullContent
                messages.value[msgIndex].loading = false
              }
            } else if (data.type === 'error') {
              const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
              if (msgIndex !== -1) {
                messages.value[msgIndex].content = `错误: ${data.message}`
                messages.value[msgIndex].loading = false
              }
            }
            
            scrollToBottom()
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
    
  } catch (error: any) {
    const msgIndex = messages.value.findIndex(m => m.id === assistantMsgId)
    if (msgIndex !== -1) {
      messages.value[msgIndex].content = `请求失败: ${error.message}`
      messages.value[msgIndex].loading = false
    }
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 处理回车键
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 清空对话
function clearMessages() {
  messages.value = []
  currentAmisCode.value = null
}

// 复制代码
function copyCode() {
  if (currentAmisCode.value) {
    navigator.clipboard.writeText(JSON.stringify(currentAmisCode.value, null, 2))
  }
}
</script>

<template>
  <div class="h-full flex bg-gray-50">
    <!-- 左侧对话区域 -->
    <div class="w-1/2 flex flex-col border-r border-gray-200 bg-white">
      <!-- 头部 -->
      <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </div>
          <span class="font-semibold text-gray-800">代码助手</span>
        </div>
        <button 
          @click="clearMessages"
          class="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          title="清空对话"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
      
      <!-- 消息列表 -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="text-center py-12">
          <div class="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center">
            <svg class="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-gray-800 mb-2">amis 代码生成助手</h3>
          <p class="text-gray-500 text-sm mb-6">描述你想要的页面，我会帮你生成 amis 配置</p>
          <div class="flex flex-wrap justify-center gap-2">
            <button 
              @click="inputValue = '生成一个用户管理表格，包含姓名、邮箱、状态字段'"
              class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-600 transition-colors"
            >
              用户管理表格
            </button>
            <button 
              @click="inputValue = '生成一个登录表单，包含用户名、密码和记住我选项'"
              class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-600 transition-colors"
            >
              登录表单
            </button>
            <button 
              @click="inputValue = '生成一个数据统计仪表盘，包含4个统计卡片'"
              class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-600 transition-colors"
            >
              统计仪表盘
            </button>
          </div>
        </div>
        
        <!-- 消息列表 -->
        <template v-for="msg in messages" :key="msg.id">
          <!-- 用户消息 -->
          <div v-if="msg.from === 'user'" class="flex justify-end">
            <div class="max-w-[80%] bg-blue-500 text-white px-4 py-2.5 rounded-2xl rounded-br-md">
              {{ msg.content }}
            </div>
          </div>
          
          <!-- 助手消息 -->
          <div v-else class="flex gap-3">
            <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex-shrink-0 flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <!-- 加载状态 -->
              <div v-if="msg.loading" class="flex items-center gap-2 text-gray-500">
                <div class="flex gap-1">
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                </div>
                <span class="text-sm">{{ msg.content || '思考中...' }}</span>
              </div>
              
              <!-- 消息内容 -->
              <div v-else class="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-md">
                <div class="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">{{ msg.content }}</div>
                
                <!-- amis 代码提示 -->
                <div v-if="msg.amisCode" class="mt-3 pt-3 border-t border-gray-200">
                  <div class="flex items-center gap-2 text-xs text-green-600">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>已生成 amis 配置，查看右侧预览</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
      
      <!-- 输入区域 -->
      <div class="p-4 border-t border-gray-200">
        <div class="flex gap-2">
          <textarea
            v-model="inputValue"
            @keydown="handleKeydown"
            placeholder="描述你想要的页面..."
            class="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            rows="2"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="!inputValue.trim() || isLoading"
            class="px-4 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-xl transition-colors flex items-center justify-center"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 右侧预览区域 -->
    <div class="w-1/2 flex flex-col bg-white">
      <!-- 标签栏 -->
      <div class="px-4 py-2 border-b border-gray-200 flex items-center justify-between">
        <div class="flex gap-1">
          <button
            @click="activeTab = 'preview'"
            :class="[
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              activeTab === 'preview' ? 'bg-blue-100 text-blue-600' : 'text-gray-500 hover:bg-gray-100'
            ]"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              预览
            </span>
          </button>
          <button
            @click="activeTab = 'code'"
            :class="[
              'px-3 py-1.5 text-sm rounded-lg transition-colors',
              activeTab === 'code' ? 'bg-blue-100 text-blue-600' : 'text-gray-500 hover:bg-gray-100'
            ]"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              代码
            </span>
          </button>
        </div>
        
        <button
          v-if="currentAmisCode"
          @click="copyCode"
          class="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          title="复制代码"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
      
      <!-- 预览/代码内容 -->
      <div class="flex-1 overflow-auto">
        <!-- 空状态 -->
        <div v-if="!currentAmisCode" class="h-full flex items-center justify-center">
          <div class="text-center text-gray-400">
            <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p>生成代码后将在此处预览</p>
          </div>
        </div>
        
        <!-- 预览模式 -->
        <div v-else-if="activeTab === 'preview'" class="p-4 h-full">
          <div class="border border-gray-200 rounded-lg bg-white min-h-[400px] h-full overflow-auto">
            <!-- amis 加载状态 -->
            <div v-if="!amisLoaded && !amisLoadError" class="flex items-center justify-center h-64">
              <div class="text-center text-gray-500">
                <div class="flex gap-1 justify-center mb-2">
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
                  <span class="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
                </div>
                <p class="text-sm">正在加载 amis SDK...</p>
              </div>
            </div>
            
            <!-- amis 加载失败 -->
            <div v-else-if="amisLoadError" class="flex items-center justify-center h-64">
              <div class="text-center text-red-500">
                <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p class="text-sm">{{ amisLoadError }}</p>
                <button @click="loadAmisSDK" class="mt-2 px-3 py-1 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600">
                  重试
                </button>
              </div>
            </div>
            
            <!-- amis 渲染容器 -->
            <div v-else ref="amisPreviewRef" class="amis-preview-container p-4"></div>
          </div>
        </div>
        
        <!-- 代码模式 -->
        <div v-else class="p-4">
          <pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-auto text-sm font-mono">{{ JSON.stringify(currentAmisCode, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prose pre {
  background: #1f2937;
  color: #f3f4f6;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
}

.prose code {
  background: #e5e7eb;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.animate-bounce {
  animation: bounce 0.6s infinite;
}
</style>
