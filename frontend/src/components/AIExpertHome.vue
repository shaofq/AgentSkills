<script setup lang="ts">
// Vue 组件

interface AgentCard {
  id: string
  name: string
  description: string
  icon: string
  iconBg: string
  iconType?: string
  usageCount: number
  avgTime: string
}

const props = defineProps<{
  agents: AgentCard[]
}>()

const emit = defineEmits<{
  (e: 'select', agentId: string): void
}>()

function handleCardClick(agentId: string) {
  emit('select', agentId)
}

function formatUsageCount(count: number): string {
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万'
  }
  return count.toString()
}
</script>

<template>
  <div class="ai-expert-home">
    <!-- 头部标题区域 -->
    <div class="header-section">
      <div class="logo-title">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="url(#gradient1)"/>
            <path d="M2 17L12 22L22 17" stroke="url(#gradient2)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="url(#gradient3)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <defs>
              <linearGradient id="gradient1" x1="2" y1="7" x2="22" y2="7" gradientUnits="userSpaceOnUse">
                <stop stop-color="#6366f1"/>
                <stop offset="1" stop-color="#8b5cf6"/>
              </linearGradient>
              <linearGradient id="gradient2" x1="2" y1="19.5" x2="22" y2="19.5" gradientUnits="userSpaceOnUse">
                <stop stop-color="#06b6d4"/>
                <stop offset="1" stop-color="#3b82f6"/>
              </linearGradient>
              <linearGradient id="gradient3" x1="2" y1="14.5" x2="22" y2="14.5" gradientUnits="userSpaceOnUse">
                <stop stop-color="#8b5cf6"/>
                <stop offset="1" stop-color="#06b6d4"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span class="title-text">AI 专家</span>
      </div>
      <p class="main-subtitle">根据你的需求，可以请诸各行业 AI 专家为你解决问题</p>
      <p class="sub-description">AgChat 可以辅助客户提升业务体验、查询知识和相关作业信息、编写文档等。</p>
    </div>

    <!-- 卡片网格区域 -->
    <div class="cards-grid">
      <div 
        v-for="agent in agents" 
        :key="agent.id"
        class="agent-card"
        @click="handleCardClick(agent.id)"
      >
        <div class="card-header">
          <div class="card-icon" :style="{ background: agent.iconBg }">
            <!-- 代码助手 -->
            <svg v-if="agent.id === 'code-agent'" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="16,18 22,12 16,6"/>
              <polyline points="8,6 2,12 8,18"/>
            </svg>
            <!-- 制度问答 -->
            <svg v-else-if="agent.id === 'policy-qa'" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <!-- OCR识别 -->
            <svg v-else-if="agent.id === 'ocr-agent'" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10,9 9,9 8,9"/>
            </svg>
            <!-- PPT生成 -->
            <svg v-else-if="agent.id === 'pptx-agent'" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            <!-- 订舱智能体 -->
            <svg v-else-if="agent.id === 'booking-agent'" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8h1a4 4 0 0 1 0 8h-1"/>
              <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
              <line x1="6" y1="1" x2="6" y2="4"/>
              <line x1="10" y1="1" x2="10" y2="4"/>
              <line x1="14" y1="1" x2="14" y2="4"/>
            </svg>
            <!-- 技能创建 -->
            <svg v-else-if="agent.id === 'skill-creator'" class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            <!-- 默认图标 -->
            <svg v-else class="icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <h3 class="card-title">{{ agent.name }}</h3>
        </div>
        <p class="card-description">{{ agent.description }}</p>
        <div class="card-footer">
          <span class="stat-item">
            <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            {{ formatUsageCount(agent.usageCount) }}
          </span>
          <span class="stat-item">
            <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12,6 12,12 16,14"/>
            </svg>
            {{ agent.avgTime }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-expert-home {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 48px 24px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

/* 头部区域 */
.header-section {
  text-align: center;
  margin-bottom: 48px;
}

.logo-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
}

.logo-icon {
  width: 48px;
  height: 48px;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
}

.title-text {
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.main-subtitle {
  font-size: 20px;
  color: #1e293b;
  margin-bottom: 12px;
  font-weight: 500;
}

.sub-description {
  font-size: 15px;
  color: #64748b;
  max-width: 600px;
  margin: 0 auto;
}

/* 卡片网格 */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  max-width: 900px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .cards-grid {
    grid-template-columns: 1fr;
  }
}

/* 卡片样式 */
.agent-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.agent-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
  border-color: #c7d2fe;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.card-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-emoji {
  font-size: 22px;
}

.icon-svg {
  width: 24px;
  height: 24px;
  stroke: white;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.card-description {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 44px;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #94a3b8;
}

.stat-icon {
  width: 14px;
  height: 14px;
}
</style>
