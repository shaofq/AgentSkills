<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  data: {
    label: string
    icon: string
    color: string
  }
  selected?: boolean
}>()
</script>

<template>
  <div 
    :class="[
      'w-[140px] rounded-lg overflow-hidden transition-all duration-200',
      selected ? 'ring-2 ring-purple-400 ring-offset-2 shadow-xl' : 'shadow-lg hover:shadow-xl'
    ]"
    style="background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
  >
    <!-- 头部 -->
    <div class="bg-gradient-to-r from-purple-500 to-violet-500 px-2.5 py-2 flex items-center gap-2">
      <div class="w-5 h-5 bg-white/20 rounded flex items-center justify-center">
        <span class="text-sm">{{ data.icon || '⚡' }}</span>
      </div>
      <span class="text-white font-semibold text-xs truncate">{{ data.label }}</span>
    </div>
    
    <!-- 内容 -->
    <div class="px-2.5 py-2 bg-white">
      <div class="text-[10px] text-gray-600 space-y-1">
        <div class="flex items-center gap-1.5">
          <div class="w-1 h-1 rounded-full bg-purple-400 flex-shrink-0"></div>
          <span class="font-medium">并行执行</span>
        </div>
      </div>
    </div>
    
    <!-- 连接点 -->
    <Handle type="target" :position="Position.Left" class="!w-3 !h-3 !bg-purple-500 !border-2 !border-white" />
    <Handle 
      id="branch1" 
      type="source" 
      :position="Position.Right" 
      :style="{ top: '30%' }"
      class="!w-3 !h-3 !bg-purple-500 !border-2 !border-white" 
    />
    <Handle 
      id="branch2" 
      type="source" 
      :position="Position.Right" 
      :style="{ top: '50%' }"
      class="!w-3 !h-3 !bg-purple-500 !border-2 !border-white" 
    />
    <Handle 
      id="branch3" 
      type="source" 
      :position="Position.Right" 
      :style="{ top: '70%' }"
      class="!w-3 !h-3 !bg-purple-500 !border-2 !border-white" 
    />
  </div>
</template>
