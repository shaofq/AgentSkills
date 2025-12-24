<template>
  <div class="manus-view">
    <!-- 左侧：对话区域 -->
    <div class="chat-panel">
      <div class="chat-header">
        <div class="header-info">
          <span class="ai-icon">🤖</span>
          <span class="title">Manus AI</span>
        </div>
        <span class="date-tag">{{ currentDate }}</span>
      </div>

      <!-- 任务摘要 -->
      <div v-if="taskSummary" class="task-summary">
        <h4>摘要</h4>
        <p>{{ taskSummary }}</p>
      </div>

      <!-- 消息列表 -->
      <div class="message-list" ref="messageList">
        <div 
          v-for="(msg, index) in messages" 
          :key="index"
          :class="['message', msg.role]"
        >
          <div class="message-avatar">
            <span v-if="msg.role === 'assistant'">🤖</span>
            <span v-else>👤</span>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(msg.content)"></div>
            <div v-if="msg.files && msg.files.length > 0" class="message-files">
              <div 
                v-for="file in msg.files" 
                :key="file.name"
                class="file-card"
                @click="downloadFile(file)"
              >
                <span>📄</span>
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ file.size }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载中 -->
        <div v-if="isLoading" class="message assistant loading">
          <div class="message-avatar">
            <span>🤖</span>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成的文件 -->
      <div v-if="generatedFiles.length > 0" class="generated-files">
        <div class="files-header">
          <span>📁</span>
          <span>查看此任务中的所有文件</span>
        </div>
        <div class="files-grid">
          <div 
            v-for="file in generatedFiles" 
            :key="file.path"
            class="file-item"
            @click="previewFile(file)"
          >
            <span>📄</span>
            <span>{{ file.name }}</span>
          </div>
        </div>
      </div>

      <!-- 任务状态 -->
      <div v-if="taskStatus" class="task-status" :class="taskStatus">
        <span v-if="taskStatus === 'completed'">✅</span>
        <span v-else class="loading-spinner"></span>
        <span>{{ taskStatusText }}</span>
      </div>

      <!-- 推荐追问 -->
      <div v-if="suggestedQuestions.length > 0" class="suggested-questions">
        <h4>推荐追问</h4>
        <div 
          v-for="(q, idx) in suggestedQuestions" 
          :key="idx"
          class="question-item"
          @click="askQuestion(q)"
        >
          {{ q }}
        </div>
      </div>

      <!-- 输入框 -->
      <div class="input-area">
        <textarea
          v-model="userInput"
          rows="2"
          placeholder="发送消息给 Manus (Ctrl+Enter 发送)"
          @keyup.ctrl.enter="sendMessage"
          class="input-textarea"
        ></textarea>
        <div class="input-actions">
          <button class="btn-icon" title="附件">➕</button>
          <button 
            class="btn-send"
            @click="sendMessage"
            :disabled="!userInput.trim() || isLoading"
          >
            发送
          </button>
        </div>
      </div>
    </div>

    <!-- 右侧：Sandbox 可视化 -->
    <div class="sandbox-panel">
      <SandboxView 
        ref="sandboxView"
        :task="currentTask"
        :files="generatedFiles.map(f => f.path)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import axios from 'axios'
import SandboxView from './SandboxView.vue'

const API_BASE = ''

interface Message {
  role: 'user' | 'assistant'
  content: string
  files?: Array<{name: string, path: string, size: string}>
}

interface GeneratedFile {
  name: string
  path: string
  size: string
}

// 状态
const messages = ref<Message[]>([])
const userInput = ref('')
const isLoading = ref(false)
const taskSummary = ref('')
const taskStatus = ref<'running' | 'completed' | ''>('')
const currentTask = ref('')
const generatedFiles = ref<GeneratedFile[]>([])
const suggestedQuestions = ref<string[]>([])
const messageList = ref<HTMLElement>()
const sandboxView = ref()

// 计算属性
const currentDate = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`
})

const taskStatusText = computed(() => {
  if (taskStatus.value === 'completed') return '任务已完成'
  if (taskStatus.value === 'running') return '正在执行...'
  return ''
})

// 格式化消息（支持 Markdown）
function formatMessage(content: string): string {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
}

// 发送消息
async function sendMessage() {
  if (!userInput.value.trim() || isLoading.value) return
  
  const content = userInput.value.trim()
  userInput.value = ''
  
  // 添加用户消息
  messages.value.push({ role: 'user', content })
  scrollToBottom()
  
  isLoading.value = true
  taskStatus.value = 'running'
  currentTask.value = content.slice(0, 50) + (content.length > 50 ? '...' : '')
  
  try {
    // 调用 Agent API（这里可以根据实际 API 调整）
    const resp = await axios.post(`${API_BASE}/sandbox/agents/sandbox/execute`, {
      message: content,
      use_sandbox: true
    }, {
      timeout: 120000
    })
    
    const data = resp.data
    
    // 添加 AI 回复
    messages.value.push({
      role: 'assistant',
      content: data.response || data.content || '任务已完成',
      files: data.files || []
    })
    
    // 更新生成的文件
    if (data.files) {
      generatedFiles.value = data.files.map((f: any) => ({
        name: f.name || f.split('/').pop(),
        path: f.path || f,
        size: f.size || '-'
      }))
    }
    
    // 更新摘要
    if (data.summary) {
      taskSummary.value = data.summary
    }
    
    // 更新推荐问题
    if (data.suggested_questions) {
      suggestedQuestions.value = data.suggested_questions
    }
    
    taskStatus.value = 'completed'
    
  } catch (e: any) {
    messages.value.push({
      role: 'assistant',
      content: `执行出错: ${e.message || '未知错误'}`
    })
    taskStatus.value = ''
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messageList.value) {
      messageList.value.scrollTop = messageList.value.scrollHeight
    }
  })
}

// 追问
function askQuestion(question: string) {
  userInput.value = question
  sendMessage()
}

// 预览文件
async function previewFile(file: GeneratedFile) {
  try {
    await axios.post(`${API_BASE}/sandbox/file/read`, {
      file_path: file.path
    })
    // 在 Sandbox 视图中显示
    if (sandboxView.value) {
      sandboxView.value.addLog('info', `预览文件: ${file.name}`)
    }
  } catch (e) {
    console.error('读取文件失败', e)
  }
}

// 下载文件
function downloadFile(file: {name: string, path: string}) {
  console.log(`下载: ${file.name}`)
}

// 初始化
onMounted(() => {
  // 添加欢迎消息
  messages.value.push({
    role: 'assistant',
    content: '你好！我是 Manus AI，可以帮你完成各种任务。我可以：\n\n- 📝 生成文档和报告\n- 💻 执行代码和脚本\n- 🌐 浏览网页并提取信息\n- 📁 创建和编辑文件\n\n你可以在右侧实时观看我的操作过程。有什么需要帮助的吗？'
  })
  
  suggestedQuestions.value = [
    '帮我写一份项目技术方案文档',
    '用 Python 分析这个数据文件',
    '帮我抓取网页内容并整理成报告'
  ]
})
</script>

<style scoped>
.manus-view {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

/* 左侧对话面板 */
.chat-panel {
  width: 45%;
  min-width: 400px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-right: 1px solid #e0e0e0;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 24px;
}

.title {
  font-size: 18px;
  font-weight: 600;
}

.date-tag {
  padding: 4px 10px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.input-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  resize: none;
  font-family: inherit;
  font-size: 14px;
}

.input-textarea:focus {
  outline: none;
  border-color: #409eff;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border: none;
  background: #f0f0f0;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
}

.btn-icon:hover {
  background: #e0e0e0;
}

.btn-send {
  padding: 8px 20px;
  border: none;
  background: #409eff;
  color: #fff;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
}

.btn-send:hover {
  background: #66b1ff;
}

.btn-send:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #ccc;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 任务摘要 */
.task-summary {
  padding: 16px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.task-summary h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
}

.task-summary p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e8f4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: #f0f0f0;
}

.message-content {
  max-width: 80%;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  background: #f5f5f5;
  line-height: 1.6;
}

.message.user .message-text {
  background: #409eff;
  color: #fff;
}

.message.assistant .message-text {
  background: #f8f9fa;
}

/* 文件卡片 */
.message-files {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.file-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-card:hover {
  border-color: #409eff;
  background: #f8f9ff;
}

.file-info {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
}

.file-size {
  font-size: 11px;
  color: #999;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #ccc;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 生成的文件 */
.generated-files {
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  background: #fafafa;
}

.files-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
}

.files-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.files-grid .file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.files-grid .file-item:hover {
  border-color: #409eff;
}

/* 任务状态 */
.task-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #f0f9eb;
  color: #67c23a;
  font-size: 14px;
}

.task-status .success {
  color: #67c23a;
}

/* 推荐追问 */
.suggested-questions {
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
}

.suggested-questions h4 {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: #999;
}

.question-item {
  padding: 10px 14px;
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.question-item:hover {
  background: #e8f4ff;
  color: #409eff;
}

/* 输入区域 */
.input-area {
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
  background: #fff;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

/* 右侧 Sandbox 面板 */
.sandbox-panel {
  flex: 1;
  min-width: 500px;
}
</style>
