<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  data: {
    label: string
    icon: string
    color: string
    toolConfig?: {
      toolType?: string
      toolName?: string
      params?: Record<string, any>
    }
  }
  selected?: boolean
}>()

const toolTypeLabels: Record<string, string> = {
  'email-send': '邮件发送',
  'http-request': 'HTTP请求',
  'file-write': '文件写入',
  'database': '数据库操作',
}
</script>

<template>
  <div 
    :class="[
      'w-[140px] rounded-lg overflow-hidden transition-all duration-200',
      selected ? 'ring-2 ring-amber-400 ring-offset-2 shadow-xl' : 'shadow-lg hover:shadow-xl'
    ]"
    style="background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
  >
    <!-- 头部 -->
    <div class="bg-gradient-to-r from-amber-500 to-orange-500 px-2.5 py-2 flex items-center gap-2">
      <div class="w-5 h-5 bg-white/20 rounded flex items-center justify-center">
        <span class="text-sm">{{ data.icon || '🔧' }}</span>
      </div>
      <span class="text-white font-semibold text-xs truncate">{{ data.label }}</span>
    </div>
    
    <!-- 内容 -->
    <div class="px-2.5 py-2 bg-white">
      <div v-if="data.toolConfig?.toolType" class="text-[10px] text-gray-600 space-y-1">
        <div class="flex items-center gap-1 truncate">
          <div class="w-1 h-1 rounded-full bg-amber-400 flex-shrink-0"></div>
          <span class="truncate font-medium">{{ toolTypeLabels[data.toolConfig.toolType] || data.toolConfig.toolType }}</span>
        </div>
        <div v-if="data.toolConfig.toolName" class="flex items-center gap-1">
          <div class="w-1 h-1 rounded-full bg-orange-400 flex-shrink-0"></div>
          <span class="font-medium truncate">{{ data.toolConfig.toolName }}</span>
        </div>
      </div>
      <div v-else class="text-[10px] text-gray-500 font-medium">
        点击配置工具
      </div>
    </div>
    
    <!-- 连接点 -->
    <Handle type="target" :position="Position.Left" class="!w-3 !h-3 !bg-amber-500 !border-2 !border-white" />
    <Handle type="source" :position="Position.Right" class="!w-3 !h-3 !bg-amber-500 !border-2 !border-white" />
  </div>
</template>
