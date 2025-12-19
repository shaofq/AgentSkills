<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { computed } from 'vue'

const props = defineProps<{
  data: {
    label: string
    icon: string
    color: string
    classifierConfig?: {
      model: string
      categories: { id: string; name: string; description: string }[]
    }
  }
  selected?: boolean
}>()

const categories = computed(() => {
  return props.data.classifierConfig?.categories || []
})

// 计算每个分类的连接点位置（基于内容区域）
// 头部高度约 36px，每个分类项高度约 20px，内容区域 padding 8px
function getCategoryPosition(index: number): string {
  const headerHeight = 36  // 头部高度
  const contentPadding = 8 // 内容区域上边距
  const itemHeight = 20    // 每个分类项高度
  const itemOffset = 10    // 分类项中心偏移
  
  const top = headerHeight + contentPadding + (index * itemHeight) + itemOffset
  return `${top}px`
}

// 生成分类颜色
const categoryColors = ['#06b6d4', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#3b82f6', '#ec4899', '#84cc16']
function getCategoryColor(index: number): string {
  return categoryColors[index % categoryColors.length]
}
</script>

<template>
  <div 
    :class="[
      'w-[160px] rounded-lg overflow-hidden transition-all duration-200',
      selected ? 'ring-2 ring-cyan-400 ring-offset-2 shadow-xl' : 'shadow-lg hover:shadow-xl'
    ]"
    style="background: linear-gradient(135deg, #ffffff 0%, #ecfeff 100%); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
  >
    <!-- 头部 -->
    <div class="bg-gradient-to-r from-cyan-500 to-teal-500 px-2.5 py-2 flex items-center gap-2">
      <div class="w-5 h-5 bg-white/20 rounded flex items-center justify-center">
        <span class="text-sm">{{ data.icon || '🏷️' }}</span>
      </div>
      <span class="text-white font-semibold text-xs truncate">{{ data.label }}</span>
    </div>
    
    <!-- 内容 -->
    <div class="px-2.5 py-2 bg-white">
      <div v-if="categories.length > 0" class="text-[10px] text-gray-600 space-y-1">
        <div 
          v-for="(category, index) in categories" 
          :key="category.id"
          class="flex items-center gap-1.5"
        >
          <div 
            class="w-1.5 h-1.5 rounded-full flex-shrink-0"
            :style="{ backgroundColor: getCategoryColor(index) }"
          ></div>
          <span class="font-medium truncate">{{ category.name || `分类 ${index + 1}` }}</span>
        </div>
      </div>
      <div v-else class="text-[10px] text-gray-400 text-center py-1">
        点击配置分类
      </div>
    </div>
    
    <!-- 输入连接点 -->
    <Handle 
      type="target" 
      :position="Position.Left" 
      class="!w-3 !h-3 !bg-cyan-500 !border-2 !border-white" 
    />
    
    <!-- 每个分类的输出连接点 -->
    <Handle 
      v-for="(category, index) in categories"
      :key="category.id"
      :id="category.id"
      type="source" 
      :position="Position.Right" 
      :style="{ top: getCategoryPosition(index), backgroundColor: getCategoryColor(index) }"
      class="!w-3 !h-3 !border-2 !border-white"
    />
    
    <!-- 如果没有分类，显示默认输出点 -->
    <Handle 
      v-if="categories.length === 0"
      id="default"
      type="source" 
      :position="Position.Right" 
      class="!w-3 !h-3 !bg-gray-400 !border-2 !border-white" 
    />
  </div>
</template>

<style scoped>
/* 动态颜色需要内联样式 */
</style>
