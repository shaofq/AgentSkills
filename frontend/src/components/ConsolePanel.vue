<template>
  <div 
    class="console-panel"
    :class="{ 'console-panel--expanded': isExpanded }"
  >
    <!-- 回放按钮 -->
    <div class="replay-button" @click="$emit('openReplay')" title="对话回放">
      <svg class="replay-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>回放</span>
    </div>
    
    <!-- 头部 -->
    <div class="console-header" @click="toggleExpand">
      <div class="console-title">
        <svg class="console-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>执行日志</span>
        <span v-if="logs.length > 0" class="log-count">{{ logs.length }}</span>
      </div>
      <div class="console-actions">
        <button 
          v-if="logs.length > 0" 
          @click.stop="clearLogs" 
          class="action-btn"
          title="清空日志"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
        <button class="action-btn expand-btn" :title="isExpanded ? '收起' : '展开'">
          <svg 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            class="w-4 h-4 transition-transform"
            :class="{ 'rotate-180': isExpanded }"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- 日志内容 -->
    <div v-show="isExpanded" class="console-content" ref="contentRef">
      <div v-if="logs.length === 0" class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span>暂无执行日志</span>
      </div>
      
      <div v-else class="log-list">
        <div 
          v-for="(log, index) in logs" 
          :key="index"
          class="log-item"
          :class="getLogClass(log.type)"
        >
          <span class="log-time">{{ log.timestamp }}</span>
          <span class="log-source" v-if="log.source">{{ log.source }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

interface LogEntry {
  timestamp: string
  type: string
  source?: string
  message: string
}

const props = defineProps<{
  logs: LogEntry[]
}>()

const emit = defineEmits<{
  (e: 'clear'): void
  (e: 'openReplay'): void
}>()

const isExpanded = ref(false)
const contentRef = ref<HTMLElement | null>(null)

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}

function clearLogs() {
  emit('clear')
}

function getLogClass(type: string): string {
  switch (type) {
    case 'error':
      return 'log-error'
    case 'warning':
      return 'log-warning'
    case 'success':
      return 'log-success'
    case 'info':
    default:
      return 'log-info'
  }
}

// 自动滚动到底部
watch(() => props.logs.length, async () => {
  if (isExpanded.value && contentRef.value) {
    await nextTick()
    contentRef.value.scrollTop = contentRef.value.scrollHeight
  }
})

// 有新日志时自动展开
watch(() => props.logs.length, (newLen, oldLen) => {
  // if (newLen > oldLen && newLen === 1) {
  //   isExpanded.value = true
  // }
})
</script>

<style scoped>
.console-panel {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 100;
  transition: all 0.3s ease;
  margin-left: 8px;
}

.replay-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 12px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.replay-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.replay-icon {
  width: 16px;
  height: 16px;
}

.console-header-wrapper {
  width: 350px;
  background: #1e1e2e;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.console-panel--expanded .console-header-wrapper {
  width: 850px;
}

.console-header {
  width: 350px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: linear-gradient(135deg, #2d2d3a 0%, #1e1e2e 100%);
  border-radius: 12px;
  cursor: pointer;
  user-select: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.console-panel--expanded .console-header {
  width: 850px;
  border-radius: 12px 12px 0 0;
}

.console-panel--expanded .console-content {
  border-radius: 0 0 12px 12px;
}

.console-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cdd6f4;
  font-size: 13px;
  font-weight: 500;
}

.console-icon {
  width: 18px;
  height: 18px;
  color: #89b4fa;
}

.log-count {
  background: #89b4fa;
  color: #1e1e2e;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}

.console-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  padding: 4px;
  border: none;
  background: transparent;
  color: #6c7086;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #cdd6f4;
}

.expand-btn svg {
  transition: transform 0.3s ease;
}

.console-content {
  max-height: 300px;
  overflow-y: auto;
  padding: 12px;
  background: #11111b;
}

.console-content::-webkit-scrollbar {
  width: 6px;
}

.console-content::-webkit-scrollbar-track {
  background: transparent;
}

.console-content::-webkit-scrollbar-thumb {
  background: #45475a;
  border-radius: 3px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #6c7086;
  font-size: 12px;
  gap: 8px;
}

.empty-icon {
  width: 32px;
  height: 32px;
  opacity: 0.5;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  background: rgba(255, 255, 255, 0.02);
}

.log-time {
  color: #6c7086;
  font-size: 11px;
  flex-shrink: 0;
}

.log-source {
  color: #89b4fa;
  font-size: 11px;
  padding: 1px 6px;
  background: rgba(137, 180, 250, 0.1);
  border-radius: 4px;
  flex-shrink: 0;
}

.log-message {
  color: #cdd6f4;
  word-break: break-word;
}

.log-info .log-message {
  color: #cdd6f4;
}

.log-success .log-message {
  color: #a6e3a1;
}

.log-warning .log-message {
  color: #f9e2af;
}

.log-error .log-message {
  color: #f38ba8;
}

.log-error {
  background: rgba(243, 139, 168, 0.1);
}

.log-success {
  background: rgba(166, 227, 161, 0.1);
}

.log-warning {
  background: rgba(249, 226, 175, 0.1);
}
</style>
