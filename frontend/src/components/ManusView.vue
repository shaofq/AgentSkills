<template>
  <div class="manus-view">
    <!-- 左侧：对话区域 -->
    <div class="chat-panel">
      <div class="chat-header">
        <div class="header-info">
          <span class="ai-icon">🤖</span>
          <span class="title">云应用 AI</span>
        </div>
        <div class="header-actions">
          <!-- 录制控制 -->
          <button 
            v-if="!isRecording" 
            class="btn-record"
            @click="startRecording"
            title="开始录制"
          >
            🔴 录制
          </button>
          <button 
            v-else 
            class="btn-record recording"
            @click="stopRecording"
            title="停止录制"
          >
            ⏹️ 停止
          </button>
          <button 
            class="btn-recordings"
            @click="openRecordingsPanel"
            title="查看录制"
          >
            📼 回放
          </button>
          <span class="date-tag">{{ currentDate }}</span>
        </div>
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

    <!-- 录制列表弹窗 -->
    <div v-if="showRecordingsPanel" class="recordings-modal">
      <div class="recordings-panel">
        <div class="panel-header">
          <h3>📼 录制回放</h3>
          <button class="btn-close" @click="showRecordingsPanel = false">✕</button>
        </div>
        <div class="recordings-list">
          <div v-if="recordings.length === 0" class="empty-tip">
            暂无录制，点击"录制"按钮开始
          </div>
          <div 
            v-for="rec in recordings" 
            :key="rec.id"
            class="recording-item"
          >
            <div class="recording-info">
              <span class="recording-name">{{ rec.name }}</span>
              <span class="recording-meta">
                {{ rec.steps_count }} 步骤 · {{ formatDuration(rec.duration) }}
              </span>
            </div>
            <div class="recording-actions">
              <button class="btn-play" @click="playRecording(rec.id)">▶️</button>
              <button class="btn-delete" @click="deleteRecording(rec.id)">🗑️</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 播放器弹窗 -->
    <div v-if="showPlayer && selectedRecording" class="player-modal">
      <RecordingPlayer 
        :recording="selectedRecording"
        @close="closePlayer"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import axios from 'axios'
import SandboxView from './SandboxView.vue'
import RecordingPlayer from './RecordingPlayer.vue'

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

// 录制相关接口
interface Recording {
  id: string
  name: string
  duration: number
  steps: any[]
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

// 录制状态
const isRecording = ref(false)
const recordingId = ref('')
const showRecordingsPanel = ref(false)
const recordings = ref<any[]>([])
const selectedRecording = ref<Recording | null>(null)
const showPlayer = ref(false)

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
function formatMessage(content: any): string {
  // 确保 content 是字符串
  let text = ''
  if (typeof content === 'string') {
    text = content
  } else if (Array.isArray(content)) {
    // 可能是 [{type: 'text', text: '...'}] 格式
    text = content.map(c => c.text || c.content || JSON.stringify(c)).join('\n')
  } else if (content && typeof content === 'object') {
    text = content.text || content.content || JSON.stringify(content)
  } else {
    text = String(content || '')
  }
  
  return text
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
      timeout: 300000  // 5分钟超时，智能体可能需要多轮工具调用
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
    
    // 根据操作类型切换标签页
    if (data.active_tab && sandboxView.value?.switchTab) {
      sandboxView.value.switchTab(data.active_tab)
    }
    
    taskStatus.value = 'completed'
    
  } catch (e: any) {
    console.error('执行出错:', e)
    let errorMsg = e.message || '未知错误'
    if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
      errorMsg = '请求超时，请稍后重试'
    }
    messages.value.push({
      role: 'assistant',
      content: `执行出错: ${errorMsg}`
    })
    taskStatus.value = ''
  } finally {
    isLoading.value = false
    currentTask.value = ''
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

// ==================== 录制功能 ====================

// 开始录制
async function startRecording() {
  try {
    const resp = await axios.post(`${API_BASE}/sandbox/recording/start`, {
      name: `录制_${new Date().toLocaleString()}`
    })
    if (resp.data.success) {
      isRecording.value = true
      recordingId.value = resp.data.recording_id
      console.log('录制已开始:', resp.data.recording_id)
    }
  } catch (e) {
    console.error('开始录制失败:', e)
  }
}

// 停止录制
async function stopRecording() {
  try {
    const resp = await axios.post(`${API_BASE}/sandbox/recording/stop`)
    if (resp.data.success) {
      isRecording.value = false
      recordingId.value = ''
      console.log('录制已保存:', resp.data.recording)
      // 刷新录制列表
      await loadRecordings()
    }
  } catch (e) {
    console.error('停止录制失败:', e)
  }
}

// 加载录制列表
async function loadRecordings() {
  try {
    const resp = await axios.get(`${API_BASE}/sandbox/recordings`)
    if (resp.data.success) {
      recordings.value = resp.data.recordings
    }
  } catch (e) {
    console.error('加载录制列表失败:', e)
  }
}

// 播放录制
async function playRecording(id: string) {
  try {
    const resp = await axios.get(`${API_BASE}/sandbox/recording/${id}`)
    if (resp.data.success) {
      selectedRecording.value = resp.data.recording
      showPlayer.value = true
      showRecordingsPanel.value = false
    }
  } catch (e) {
    console.error('加载录制失败:', e)
  }
}

// 删除录制
async function deleteRecording(id: string) {
  if (!confirm('确定要删除这个录制吗？')) return
  try {
    await axios.delete(`${API_BASE}/sandbox/recording/${id}`)
    await loadRecordings()
  } catch (e) {
    console.error('删除录制失败:', e)
  }
}

// 关闭播放器
function closePlayer() {
  showPlayer.value = false
  selectedRecording.value = null
}

// 格式化时长
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 打开录制列表面板
async function openRecordingsPanel() {
  await loadRecordings()
  showRecordingsPanel.value = true
}

// 初始化
onMounted(async () => {
  // 添加欢迎消息
  messages.value.push({
    role: 'assistant',
    content: '你好！我是 云应用 AI，可以帮你完成各种任务。我可以：\n\n- 📝 生成文档和报告\n- 💻 执行代码和脚本\n- 🌐 浏览网页并提取信息\n- 📁 创建和编辑文件\n\n你可以在右侧实时观看我的操作过程。有什么需要帮助的吗？'
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

/* 头部操作按钮 */
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-record {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: #f0f0f0;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-record:hover {
  background: #e0e0e0;
}

.btn-record.recording {
  background: #ff4d4f;
  color: white;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.btn-recordings {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: #f0f0f0;
  cursor: pointer;
  font-size: 13px;
}

.btn-recordings:hover {
  background: #e0e0e0;
}

/* 录制列表弹窗 */
.recordings-modal,
.player-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.recordings-panel {
  background: white;
  border-radius: 12px;
  width: 500px;
  max-height: 70vh;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-close:hover {
  background: #f0f0f0;
}

.recordings-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 12px;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 40px 20px;
}

.recording-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #f8f9fa;
  transition: all 0.2s;
}

.recording-item:hover {
  background: #e8f4ff;
}

.recording-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recording-name {
  font-weight: 500;
  color: #333;
}

.recording-meta {
  font-size: 12px;
  color: #999;
}

.recording-actions {
  display: flex;
  gap: 8px;
}

.btn-play,
.btn-delete {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
}

.btn-play:hover {
  background: #e0f0ff;
}

.btn-delete:hover {
  background: #ffe0e0;
}

/* 播放器弹窗 */
.player-modal > * {
  width: 90%;
  max-width: 1200px;
  height: 80vh;
}
</style>
