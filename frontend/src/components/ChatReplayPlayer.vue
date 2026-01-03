<template>
  <div class="chat-replay-player">
    <!-- 头部 -->
    <div class="player-header">
      <div class="header-left">
        <button class="btn-back" @click="$emit('close')" v-if="currentView === 'player'">
          ← 返回列表
        </button>
        <span class="title">{{ currentView === 'list' ? '对话回放' : currentSession?.name || '回放' }}</span>
      </div>
      <div class="header-right">
        <button class="btn-close" @click="$emit('close')">✕</button>
      </div>
    </div>

    <!-- 会话列表 -->
    <div v-if="currentView === 'list'" class="session-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="sessions.length === 0" class="empty">暂无回放记录</div>
      <div v-else class="session-items">
        <div 
          v-for="session in sessions" 
          :key="session.session_id"
          class="session-item"
          @click="loadSession(session.session_id)"
        >
          <div class="session-info">
            <span class="session-name">{{ session.agent_name }}</span>
            <span class="session-time">{{ formatDateTime(session.start_time) }}</span>
          </div>
          <div class="session-meta">
            <span class="session-input">{{ session.user_input || '(无输入)' }}</span>
            <span class="session-stats">
              {{ session.step_count }} 步 · {{ formatDuration(session.duration) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 回放播放器 -->
    <div v-else class="player-content">
      <!-- 对话区域 -->
      <div class="chat-area" ref="chatArea">
        <div 
          v-for="(step, index) in visibleSteps" 
          :key="index"
          :class="['chat-message', step.step_type]"
        >
          <div class="message-icon">{{ getStepIcon(step.step_type) }}</div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-type">{{ getStepLabel(step.step_type) }}</span>
              <span class="message-time">{{ formatTime(step.timestamp) }}</span>
            </div>
            <div class="message-body">
              <template v-if="step.step_type === 'tool_call'">
                <div class="tool-call">
                  <span class="tool-name">🔧 {{ step.content?.name || 'Unknown' }}</span>
                  <pre class="tool-input">{{ formatToolInput(step.content?.input) }}</pre>
                </div>
              </template>
              <template v-else-if="step.step_type === 'tool_result'">
                <pre class="tool-result">{{ truncateText(step.content, 500) }}</pre>
              </template>
              <template v-else>
                <div class="text-content" v-html="formatMarkdown(step.content)"></div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 播放控制 -->
      <div class="player-controls">
        <button class="ctrl-btn" @click="prevStep" :disabled="currentStepIndex <= 0">
          ⏮️
        </button>
        <button class="ctrl-btn play-btn" @click="togglePlay">
          {{ isPlaying ? '⏸️' : '▶️' }}
        </button>
        <button class="ctrl-btn" @click="nextStep" :disabled="currentStepIndex >= totalSteps - 1">
          ⏭️
        </button>
        
        <!-- 进度条 -->
        <div class="progress-bar">
          <input 
            type="range" 
            :min="0" 
            :max="totalSteps - 1" 
            :value="currentStepIndex"
            @input="onProgressChange"
            class="progress-slider"
          />
          <span class="progress-text">{{ currentStepIndex + 1 }} / {{ totalSteps }}</span>
        </div>

        <!-- 速度控制 -->
        <div class="speed-control">
          <span>Speed:</span>
          <button 
            v-for="speed in [0.5, 1, 2, 4]" 
            :key="speed"
            :class="['speed-btn', { active: playSpeed === speed }]"
            @click="playSpeed = speed"
          >
            {{ speed }}x
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, nextTick } from 'vue'

interface ReplayStep {
  timestamp: number
  step_type: string
  agent_name: string
  content: any
}

interface ReplaySession {
  session_id: string
  name: string
  start_time: string
  user_input: string
  duration: number
  steps: ReplayStep[]
}

interface SessionListItem {
  session_id: string
  agent_name: string
  start_time: string
  user_input: string
  duration: number
  step_count: number
}

const emit = defineEmits(['close'])

// 状态
const currentView = ref<'list' | 'player'>('list')
const sessions = ref<SessionListItem[]>([])
const currentSession = ref<ReplaySession | null>(null)
const currentStepIndex = ref(0)
const isPlaying = ref(false)
const playSpeed = ref(1)
const loading = ref(false)
const chatArea = ref<HTMLElement>()

let playTimer: number | null = null

// 计算属性
const totalSteps = computed(() => currentSession.value?.steps?.length || 0)

const visibleSteps = computed(() => {
  if (!currentSession.value?.steps) return []
  return currentSession.value.steps.slice(0, currentStepIndex.value + 1)
})

// API 调用
async function fetchSessions() {
  loading.value = true
  try {
    const response = await fetch('/api/replay/sessions')
    if (response.ok) {
      sessions.value = await response.json()
    }
  } catch (e) {
    console.error('获取会话列表失败:', e)
  } finally {
    loading.value = false
  }
}

async function loadSession(sessionId: string) {
  loading.value = true
  try {
    const response = await fetch(`/api/replay/session/${sessionId}`)
    if (response.ok) {
      currentSession.value = await response.json()
      currentStepIndex.value = 0
      currentView.value = 'player'
    }
  } catch (e) {
    console.error('加载会话失败:', e)
  } finally {
    loading.value = false
  }
}

// 格式化函数
function formatDateTime(isoString: string): string {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDuration(seconds: number): string {
  if (!seconds) return '0s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}m${secs}s`
}

function formatTime(timestamp: number): string {
  const secs = Math.floor(timestamp)
  return `${secs}s`
}

function getStepIcon(stepType: string): string {
  switch (stepType) {
    case 'user_input': return '👤'
    case 'tool_call': return '🔧'
    case 'tool_result': return '📋'
    case 'ai_response': return '🤖'
    default: return '📌'
  }
}

function getStepLabel(stepType: string): string {
  switch (stepType) {
    case 'user_input': return '用户输入'
    case 'tool_call': return '工具调用'
    case 'tool_result': return '执行结果'
    case 'ai_response': return 'AI 回复'
    default: return '步骤'
  }
}

function formatToolInput(input: any): string {
  if (!input) return ''
  if (typeof input === 'string') return input
  return JSON.stringify(input, null, 2)
}

function truncateText(text: any, maxLen: number): string {
  const str = typeof text === 'string' ? text : JSON.stringify(text)
  return str.length > maxLen ? str.slice(0, maxLen) + '...' : str
}

function formatMarkdown(content: any): string {
  if (!content) return ''
  const text = typeof content === 'string' ? content : JSON.stringify(content)
  // 简单的 markdown 转换
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
}

// 播放控制
function togglePlay() {
  if (isPlaying.value) {
    stopPlay()
  } else {
    startPlay()
  }
}

function startPlay() {
  if (currentStepIndex.value >= totalSteps.value - 1) {
    currentStepIndex.value = 0
  }
  isPlaying.value = true
  scheduleNextStep()
}

function stopPlay() {
  isPlaying.value = false
  if (playTimer) {
    clearTimeout(playTimer)
    playTimer = null
  }
}

function scheduleNextStep() {
  if (!isPlaying.value || !currentSession.value?.steps) return
  
  const currentStep = currentSession.value.steps[currentStepIndex.value]
  const nextStep = currentSession.value.steps[currentStepIndex.value + 1]
  
  if (!nextStep) {
    stopPlay()
    return
  }
  
  const delay = ((nextStep.timestamp - currentStep.timestamp) * 1000) / playSpeed.value
  
  playTimer = window.setTimeout(() => {
    currentStepIndex.value++
    scrollToBottom()
    scheduleNextStep()
  }, Math.max(delay, 200))
}

function prevStep() {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--
  }
}

function nextStep() {
  if (currentStepIndex.value < totalSteps.value - 1) {
    currentStepIndex.value++
    scrollToBottom()
  }
}

function onProgressChange(e: Event) {
  const target = e.target as HTMLInputElement
  currentStepIndex.value = parseInt(target.value)
}

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight
    }
  })
}

// 初始化
fetchSessions()

// 清理
onUnmounted(() => {
  stopPlay()
})
</script>

<style scoped>
.chat-replay-player {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-back {
  background: rgba(255,255,255,0.2);
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 12px;
  border-radius: 4px;
}

.btn-back:hover {
  background: rgba(255,255,255,0.3);
}

.title {
  font-weight: 600;
  color: #fff;
}

.btn-close {
  background: rgba(255,255,255,0.2);
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-close:hover {
  background: rgba(255,255,255,0.3);
  color: #fff;
}

/* 会话列表样式 */
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.loading, .empty {
  text-align: center;
  color: #6b7280;
  padding: 40px;
}

.session-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-item:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.session-name {
  font-weight: 500;
  color: #1f2937;
}

.session-time {
  color: #6b7280;
  font-size: 0.85em;
}

.session-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-input {
  color: #4b5563;
  font-size: 0.9em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 60%;
}

.session-stats {
  color: #667eea;
  font-size: 0.85em;
  font-weight: 500;
}

/* 播放器内容 */
.player-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  max-width: 90%;
}

.chat-message.tool_call .message-content {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
  border-color: #dbeafe;
}

.chat-message.tool_result .message-content {
  background: #f0fdf4;
  border-left: 3px solid #22c55e;
  border-color: #dcfce7;
}

.chat-message.ai_response .message-content {
  background: #faf5ff;
  border-color: #f3e8ff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-type {
  font-size: 0.85em;
  color: #6b7280;
}

.message-time {
  font-size: 0.8em;
  color: #9ca3af;
}

.message-body {
  color: #1f2937;
  font-size: 14px;
  line-height: 1.5;
}

.tool-call {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-name {
  font-weight: 500;
  color: #3b82f6;
}

.tool-input, .tool-result {
  background: #f3f4f6;
  padding: 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
  color: #059669;
}

.text-content {
  white-space: pre-wrap;
  word-break: break-word;
}

/* 播放控制 */
.player-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.ctrl-btn {
  background: #e5e7eb;
  border: none;
  color: #374151;
  font-size: 16px;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.ctrl-btn:hover:not(:disabled) {
  background: #d1d5db;
}

.ctrl-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.play-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.play-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.progress-bar {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-slider {
  flex: 1;
  height: 4px;
  appearance: none;
  -webkit-appearance: none;
  background: #e5e7eb;
  border-radius: 2px;
  cursor: pointer;
}

.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: #667eea;
  border-radius: 50%;
  cursor: pointer;
}

.progress-text {
  color: #6b7280;
  font-size: 0.85em;
  min-width: 60px;
  text-align: right;
}

.speed-control {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #6b7280;
  font-size: 0.85em;
}

.speed-btn {
  background: #e5e7eb;
  border: none;
  color: #6b7280;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.speed-btn:hover {
  background: #d1d5db;
}

.speed-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}
</style>
