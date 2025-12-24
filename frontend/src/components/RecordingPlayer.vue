<template>
  <div class="recording-player">
    <!-- 头部控制 -->
    <div class="player-header">
      <div class="header-left">
        <span class="title">{{ recording?.name || '录制回放' }}</span>
        <span class="duration">{{ formatDuration(recording?.duration || 0) }}</span>
      </div>
      <div class="header-right">
        <button class="btn-close" @click="$emit('close')">✕</button>
      </div>
    </div>

    <!-- 播放区域 -->
    <div class="player-content">
      <!-- 截图显示 -->
      <div class="screenshot-area">
        <img 
          v-if="currentScreenshot" 
          :src="'data:image/png;base64,' + currentScreenshot" 
          alt="截图"
          class="screenshot-img"
        />
        <div v-else class="no-screenshot">
          <span>📷</span>
          <p>无截图</p>
        </div>
      </div>

      <!-- 操作日志 -->
      <div class="log-area">
        <div class="log-header">操作日志</div>
        <div class="log-list" ref="logList">
          <div 
            v-for="(step, index) in recording?.steps || []" 
            :key="index"
            :class="['log-item', step.step_type, { active: index === currentStepIndex }]"
            @click="jumpToStep(index)"
          >
            <span class="step-icon">
              {{ getStepIcon(step.step_type) }}
            </span>
            <span class="step-time">{{ formatTime(step.timestamp) }}</span>
            <span class="step-content">{{ truncateContent(step.content) }}</span>
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
      <select v-model="playSpeed" class="speed-select">
        <option :value="0.5">0.5x</option>
        <option :value="1">1x</option>
        <option :value="2">2x</option>
        <option :value="4">4x</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'

interface RecordingStep {
  timestamp: number
  step_type: string
  content: any
  screenshot?: string
}

interface Recording {
  id: string
  name: string
  duration: number
  steps: RecordingStep[]
}

const props = defineProps<{
  recording: Recording | null
}>()

const emit = defineEmits(['close'])

// 状态
const currentStepIndex = ref(0)
const isPlaying = ref(false)
const playSpeed = ref(1)
const logList = ref<HTMLElement>()

let playTimer: number | null = null

// 计算属性
const totalSteps = computed(() => props.recording?.steps?.length || 0)

const currentScreenshot = computed(() => {
  if (!props.recording?.steps) return null
  const step = props.recording.steps[currentStepIndex.value]
  return step?.screenshot || null
})

// 格式化时长
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 格式化时间戳
function formatTime(timestamp: number): string {
  const secs = Math.floor(timestamp)
  const ms = Math.floor((timestamp % 1) * 100)
  return `${secs}.${ms.toString().padStart(2, '0')}s`
}

// 获取步骤图标
function getStepIcon(stepType: string): string {
  switch (stepType) {
    case 'user_input': return '👤'
    case 'tool_call': return '🔧'
    case 'tool_result': return '📋'
    case 'ai_response': return '🤖'
    default: return '📌'
  }
}

// 截断内容
function truncateContent(content: any): string {
  const text = typeof content === 'string' ? content : JSON.stringify(content)
  return text.length > 50 ? text.slice(0, 50) + '...' : text
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
  if (!isPlaying.value || !props.recording?.steps) return
  
  const currentStep = props.recording.steps[currentStepIndex.value]
  const nextStep = props.recording.steps[currentStepIndex.value + 1]
  
  if (!nextStep) {
    stopPlay()
    return
  }
  
  const delay = ((nextStep.timestamp - currentStep.timestamp) * 1000) / playSpeed.value
  
  playTimer = window.setTimeout(() => {
    currentStepIndex.value++
    scrollToCurrentStep()
    scheduleNextStep()
  }, Math.max(delay, 100))
}

function prevStep() {
  if (currentStepIndex.value > 0) {
    currentStepIndex.value--
    scrollToCurrentStep()
  }
}

function nextStep() {
  if (currentStepIndex.value < totalSteps.value - 1) {
    currentStepIndex.value++
    scrollToCurrentStep()
  }
}

function jumpToStep(index: number) {
  currentStepIndex.value = index
  scrollToCurrentStep()
}

function onProgressChange(e: Event) {
  const target = e.target as HTMLInputElement
  currentStepIndex.value = parseInt(target.value)
  scrollToCurrentStep()
}

function scrollToCurrentStep() {
  if (logList.value) {
    const activeItem = logList.value.querySelector('.log-item.active')
    if (activeItem) {
      activeItem.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }
}

// 监听 recording 变化
watch(() => props.recording, () => {
  currentStepIndex.value = 0
  stopPlay()
})

// 清理
onUnmounted(() => {
  stopPlay()
})
</script>

<style scoped>
.recording-player {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #2d2d2d;
  border-bottom: 1px solid #3d3d3d;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-weight: 600;
  color: #e0e0e0;
}

.duration {
  color: #888;
  font-size: 0.9em;
}

.btn-close {
  background: none;
  border: none;
  color: #888;
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-close:hover {
  background: #3d3d3d;
  color: #fff;
}

.player-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.screenshot-area {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111;
  border-right: 1px solid #3d3d3d;
}

.screenshot-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.no-screenshot {
  text-align: center;
  color: #666;
}

.no-screenshot span {
  font-size: 48px;
}

.log-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 280px;
}

.log-header {
  padding: 8px 12px;
  background: #2d2d2d;
  color: #aaa;
  font-size: 0.9em;
  border-bottom: 1px solid #3d3d3d;
}

.log-list {
  flex: 1;
  overflow-y: auto;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #2d2d2d;
  cursor: pointer;
  transition: background 0.2s;
}

.log-item:hover {
  background: #2d2d2d;
}

.log-item.active {
  background: #3d5a80;
}

.step-icon {
  font-size: 14px;
}

.step-time {
  color: #888;
  font-size: 0.8em;
  min-width: 50px;
}

.step-content {
  flex: 1;
  color: #ccc;
  font-size: 0.85em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-item.user_input .step-content {
  color: #98c379;
}

.log-item.ai_response .step-content {
  color: #61afef;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #2d2d2d;
  border-top: 1px solid #3d3d3d;
}

.ctrl-btn {
  background: #3d3d3d;
  border: none;
  color: #e0e0e0;
  font-size: 18px;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.ctrl-btn:hover:not(:disabled) {
  background: #4d4d4d;
}

.ctrl-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.play-btn {
  background: #3d5a80;
}

.play-btn:hover {
  background: #4a6fa5;
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
  background: #3d3d3d;
  border-radius: 2px;
  cursor: pointer;
}

.progress-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: #3d5a80;
  border-radius: 50%;
  cursor: pointer;
}

.progress-text {
  color: #888;
  font-size: 0.85em;
  min-width: 60px;
  text-align: right;
}

.speed-select {
  background: #3d3d3d;
  border: none;
  color: #e0e0e0;
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
}
</style>
