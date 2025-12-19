<script setup lang="ts">
import { useWorkflowStore } from '@/stores/workflow'

const store = useWorkflowStore()

const nodeTypes = [
  {
    category: '输入/输出',
    items: [
      { type: 'input', label: '用户输入', icon: '📥', color: 'bg-green-500' },
      { type: 'output', label: '输出结果', icon: '📤', color: 'bg-orange-500' },
    ]
  },
  {
    category: '智能体',
    items: store.predefinedAgents.map(agent => ({
      type: 'agent',
      label: agent.name,
      icon: getAgentIcon(agent.type),
      color: getAgentColor(agent.type),
      agentConfig: agent,
    }))
  },
  {
    category: '流程控制',
    items: [
      { type: 'classifier', label: '问题分类器', icon: '🏷️', color: 'bg-cyan-500' },
      { type: 'condition', label: '条件分支', icon: '🔀', color: 'bg-yellow-500' },
      { type: 'parallel', label: '并行执行', icon: '⚡', color: 'bg-purple-500' },
    ]
  }
]

function getAgentIcon(type: string): string {
  const icons: Record<string, string> = {
    router: '🔄',
    code: '💻',
    pptx: '📊',
    data: '📈',
    custom: '🤖',
  }
  return icons[type] || '🤖'
}

function getAgentColor(type: string): string {
  const colors: Record<string, string> = {
    router: 'bg-blue-500',
    code: 'bg-indigo-500',
    pptx: 'bg-pink-500',
    data: 'bg-teal-500',
    custom: 'bg-gray-500',
  }
  return colors[type] || 'bg-gray-500'
}

function onDragStart(event: DragEvent, item: any) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/json', JSON.stringify(item))
    event.dataTransfer.effectAllowed = 'move'
  }
}
</script>

<template>
  <div class="w-64 bg-white border-r border-gray-200 flex flex-col">
    <!-- 标题 -->
    <div class="p-4 border-b border-gray-200">
      <h2 class="text-sm font-semibold text-gray-600 uppercase tracking-wider">组件库</h2>
    </div>
    
    <!-- 组件列表 -->
    <div class="flex-1 overflow-y-auto p-3 space-y-4">
      <div v-for="category in nodeTypes" :key="category.category">
        <h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 px-1">
          {{ category.category }}
        </h3>
        <div class="space-y-1">
          <div
            v-for="item in category.items"
            :key="item.label"
            draggable="true"
            @dragstart="onDragStart($event, item)"
            class="flex items-center gap-3 p-2.5 rounded-lg cursor-grab hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all group"
          >
            <div 
              :class="[item.color, 'w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-sm group-hover:shadow transition-shadow']"
            >
              <span class="text-sm">{{ item.icon }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-gray-700 truncate">{{ item.label }}</div>
              <div v-if="item.agentConfig" class="text-xs text-gray-400 truncate">
                {{ item.agentConfig.description }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 底部提示 -->
    <div class="p-3 border-t border-gray-200 bg-gray-50">
      <p class="text-xs text-gray-500 text-center">
        拖拽组件到画布中创建工作流
      </p>
    </div>
  </div>
</template>
