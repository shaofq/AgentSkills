<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

interface AgentStats {
  name: string
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  call_count: number
}

interface ModelStats {
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  call_count: number
}

interface DateStats {
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  call_count: number
}

interface TokenStats {
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  call_count: number
  by_agent: Record<string, AgentStats>
  by_model: Record<string, ModelStats>
  by_date: Record<string, DateStats>
}

const loading = ref(false)
const stats = ref<TokenStats | null>(null)
const activeTab = ref<'overview' | 'agent' | 'model' | 'date'>('overview')
const selectedDays = ref(30)

async function loadStats() {
  loading.value = true
  try {
    const response = await fetch(`http://localhost:8000/api/token-stats/stats?days=${selectedDays.value}`)
    if (response.ok) {
      stats.value = await response.json()
    }
  } catch (err) {
    console.error('加载统计数据失败:', err)
  } finally {
    loading.value = false
  }
}

watch(() => props.visible, (val) => {
  if (val) {
    loadStats()
  }
})

watch(selectedDays, () => {
  loadStats()
})

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const agentList = computed(() => {
  if (!stats.value) return []
  return Object.entries(stats.value.by_agent).map(([id, data]) => ({
    id,
    ...data
  })).sort((a, b) => b.total_tokens - a.total_tokens)
})

const modelList = computed(() => {
  if (!stats.value) return []
  return Object.entries(stats.value.by_model).map(([name, data]) => ({
    name,
    ...data
  })).sort((a, b) => b.total_tokens - a.total_tokens)
})

const dateList = computed(() => {
  if (!stats.value) return []
  return Object.entries(stats.value.by_date).map(([date, data]) => ({
    date,
    ...data
  })).sort((a, b) => b.date.localeCompare(a.date))
})

function handleClose() {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
      <div class="dialog-container">
        <!-- 头部 -->
        <div class="dialog-header">
          <h2 class="dialog-title">
            <svg class="title-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20V10"/>
              <path d="M18 20V4"/>
              <path d="M6 20v-4"/>
            </svg>
            Token 消耗统计
          </h2>
          <button class="close-btn" @click="handleClose">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- 时间筛选 -->
        <div class="time-filter">
          <span class="filter-label">统计周期：</span>
          <div class="filter-options">
            <button 
              v-for="days in [7, 30, 90]" 
              :key="days"
              :class="['filter-btn', { active: selectedDays === days }]"
              @click="selectedDays = days"
            >
              {{ days }}天
            </button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <span>加载中...</span>
        </div>

        <!-- 统计内容 -->
        <div v-else-if="stats" class="stats-content">
          <!-- 概览卡片 -->
          <div class="overview-cards">
            <div class="stat-card">
              <div class="stat-icon total">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ formatNumber(stats.total_tokens) }}</span>
                <span class="stat-label">总 Token</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon prompt">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ formatNumber(stats.prompt_tokens) }}</span>
                <span class="stat-label">输入 Token</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon completion">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14,2 14,8 20,8"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ formatNumber(stats.completion_tokens) }}</span>
                <span class="stat-label">输出 Token</span>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon calls">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
                </svg>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ stats.call_count }}</span>
                <span class="stat-label">调用次数</span>
              </div>
            </div>
          </div>

          <!-- Tab 切换 -->
          <div class="tabs">
            <button 
              :class="['tab-btn', { active: activeTab === 'agent' }]"
              @click="activeTab = 'agent'"
            >
              按智能体
            </button>
            <button 
              :class="['tab-btn', { active: activeTab === 'model' }]"
              @click="activeTab = 'model'"
            >
              按模型
            </button>
            <button 
              :class="['tab-btn', { active: activeTab === 'date' }]"
              @click="activeTab = 'date'"
            >
              按日期
            </button>
          </div>

          <!-- 详细列表 -->
          <div class="detail-list">
            <!-- 按智能体 -->
            <template v-if="activeTab === 'agent'">
              <div v-if="agentList.length === 0" class="empty-state">暂无数据</div>
              <div v-else class="list-items">
                <div v-for="item in agentList" :key="item.id" class="list-item">
                  <div class="item-header">
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-count">{{ item.call_count }} 次调用</span>
                  </div>
                  <div class="item-stats">
                    <span class="item-stat">
                      <span class="stat-dot total"></span>
                      总计: {{ formatNumber(item.total_tokens) }}
                    </span>
                    <span class="item-stat">
                      <span class="stat-dot prompt"></span>
                      输入: {{ formatNumber(item.prompt_tokens) }}
                    </span>
                    <span class="item-stat">
                      <span class="stat-dot completion"></span>
                      输出: {{ formatNumber(item.completion_tokens) }}
                    </span>
                  </div>
                  <div class="item-bar">
                    <div 
                      class="bar-fill" 
                      :style="{ width: stats ? (item.total_tokens / stats.total_tokens * 100) + '%' : '0%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </template>

            <!-- 按模型 -->
            <template v-if="activeTab === 'model'">
              <div v-if="modelList.length === 0" class="empty-state">暂无数据</div>
              <div v-else class="list-items">
                <div v-for="item in modelList" :key="item.name" class="list-item">
                  <div class="item-header">
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-count">{{ item.call_count }} 次调用</span>
                  </div>
                  <div class="item-stats">
                    <span class="item-stat">
                      <span class="stat-dot total"></span>
                      总计: {{ formatNumber(item.total_tokens) }}
                    </span>
                    <span class="item-stat">
                      <span class="stat-dot prompt"></span>
                      输入: {{ formatNumber(item.prompt_tokens) }}
                    </span>
                    <span class="item-stat">
                      <span class="stat-dot completion"></span>
                      输出: {{ formatNumber(item.completion_tokens) }}
                    </span>
                  </div>
                  <div class="item-bar">
                    <div 
                      class="bar-fill model" 
                      :style="{ width: stats ? (item.total_tokens / stats.total_tokens * 100) + '%' : '0%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </template>

            <!-- 按日期 -->
            <template v-if="activeTab === 'date'">
              <div v-if="dateList.length === 0" class="empty-state">暂无数据</div>
              <div v-else class="list-items">
                <div v-for="item in dateList" :key="item.date" class="list-item">
                  <div class="item-header">
                    <span class="item-name">{{ item.date }}</span>
                    <span class="item-count">{{ item.call_count }} 次调用</span>
                  </div>
                  <div class="item-stats">
                    <span class="item-stat">
                      <span class="stat-dot total"></span>
                      总计: {{ formatNumber(item.total_tokens) }}
                    </span>
                    <span class="item-stat">
                      <span class="stat-dot prompt"></span>
                      输入: {{ formatNumber(item.prompt_tokens) }}
                    </span>
                    <span class="item-stat">
                      <span class="stat-dot completion"></span>
                      输出: {{ formatNumber(item.completion_tokens) }}
                    </span>
                  </div>
                  <div class="item-bar">
                    <div 
                      class="bar-fill date" 
                      :style="{ width: stats ? (item.total_tokens / stats.total_tokens * 100) + '%' : '0%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 无数据 -->
        <div v-else class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>暂无统计数据</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
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
  backdrop-filter: blur(4px);
}

.dialog-container {
  background: #ffffff;
  border-radius: 16px;
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.title-icon {
  width: 24px;
  height: 24px;
  color: #6366f1;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e2e8f0;
}

.close-btn svg {
  width: 18px;
  height: 18px;
  color: #64748b;
}

.time-filter {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.filter-label {
  font-size: 14px;
  color: #64748b;
}

.filter-options {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 6px 14px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  border-radius: 6px;
  font-size: 13px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  border-color: #c7d2fe;
  color: #6366f1;
}

.filter-btn.active {
  background: #6366f1;
  border-color: #6366f1;
  color: #ffffff;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  gap: 16px;
  color: #64748b;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.stats-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

@media (min-width: 640px) {
  .overview-cards {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 20px;
  height: 20px;
}

.stat-icon.total {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  color: #6366f1;
}

.stat-icon.prompt {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #10b981;
}

.stat-icon.completion {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #f59e0b;
}

.stat-icon.calls {
  background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
  color: #ec4899;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 12px;
}

.tab-btn {
  padding: 8px 16px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.tab-btn.active {
  background: #6366f1;
  color: #ffffff;
}

.detail-list {
  min-height: 200px;
}

.list-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.list-item {
  background: #f8fafc;
  border-radius: 10px;
  padding: 14px 16px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.item-count {
  font-size: 12px;
  color: #94a3b8;
}

.item-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.item-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.stat-dot.total {
  background: #6366f1;
}

.stat-dot.prompt {
  background: #10b981;
}

.stat-dot.completion {
  background: #f59e0b;
}

.item-bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.bar-fill.model {
  background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
}

.bar-fill.date {
  background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  gap: 12px;
  color: #94a3b8;
  font-size: 14px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: #cbd5e1;
}
</style>
