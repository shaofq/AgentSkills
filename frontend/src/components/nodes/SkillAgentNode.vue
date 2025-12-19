<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'

const props = defineProps<{
  data: {
    label: string
    icon: string
    color: string
    skillAgentConfig?: {
      skills: string[]
      model: string
      maxIters: number
      systemPrompt?: string
    }
  }
  selected?: boolean
}>()

const skills = computed(() => {
  return props.data.skillAgentConfig?.skills || []
})

const model = computed(() => {
  return props.data.skillAgentConfig?.model || 'qwen3-max'
})
</script>

<template>
  <div 
    :class="[
      'w-[160px] rounded-lg overflow-hidden transition-all duration-200',
      selected ? 'ring-2 ring-emerald-400 ring-offset-2 shadow-xl' : 'shadow-lg hover:shadow-xl'
    ]"
    style="background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
  >
    <!-- 头部 -->
    <div class="bg-gradient-to-r from-emerald-500 to-teal-500 px-2.5 py-2 flex items-center gap-2">
      <div class="w-5 h-5 bg-white/20 rounded flex items-center justify-center">
        <span class="text-sm">{{ data.icon || '🎯' }}</span>
      </div>
      <span class="text-white font-semibold text-xs truncate">{{ data.label }}</span>
    </div>
    
    <!-- 内容 -->
    <div class="px-2.5 py-2 bg-white">
      <div v-if="skills.length > 0" class="text-[10px] text-gray-600 space-y-1">
        <div class="flex items-center gap-1 text-gray-400 mb-1">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <span>技能列表</span>
        </div>
        <div 
          v-for="(skill, index) in skills.slice(0, 3)" 
          :key="index"
          class="flex items-center gap-1.5"
        >
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"></div>
          <span class="font-medium truncate">{{ skill }}</span>
        </div>
        <div v-if="skills.length > 3" class="text-gray-400 text-[9px]">
          +{{ skills.length - 3 }} 更多技能...
        </div>
      </div>
      <div v-else class="text-[10px] text-gray-400 text-center py-1">
        点击配置技能
      </div>
      
      <!-- 模型信息 -->
      <div class="mt-1.5 pt-1.5 border-t border-gray-100 text-[9px] text-gray-400 flex items-center gap-1">
        <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <span class="truncate">{{ model }}</span>
      </div>
    </div>
    
    <!-- 输入连接点 -->
    <Handle 
      type="target" 
      :position="Position.Left" 
      class="!w-3 !h-3 !bg-emerald-500 !border-2 !border-white" 
    />
    
    <!-- 输出连接点 -->
    <Handle 
      type="source" 
      :position="Position.Right" 
      class="!w-3 !h-3 !bg-emerald-500 !border-2 !border-white" 
    />
  </div>
</template>
