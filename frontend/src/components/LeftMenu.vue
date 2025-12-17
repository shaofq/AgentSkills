<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'select', menu: string): void
}>()

const props = defineProps<{
  activeMenu: string
}>()

interface MenuItem {
  id: string
  name: string
  icon: string
  type: 'agent' | 'workflow' | 'chat'
}

const menuItems: MenuItem[] = [
  { id: 'chat', name: '对话', icon: 'icon-message', type: 'chat' },
  { id: 'code-agent', name: '代码助手', icon: 'icon-code', type: 'agent' },
  { id: 'pptx-agent', name: 'PPT助手', icon: 'icon-file', type: 'agent' },
  { id: 'data-agent', name: '数据分析', icon: 'icon-data-storage', type: 'agent' },
  { id: 'policy-qa', name: '制度问答', icon: 'icon-help', type: 'agent' },
  { id: 'workflow', name: '流程编排', icon: 'icon-application', type: 'workflow' },
]

const collapsed = ref(true)
const isHovering = ref(false)

function toggleCollapse() {
  collapsed.value = !collapsed.value
}

function handleMouseEnter() {
  isHovering.value = true
}

function handleMouseLeave() {
  isHovering.value = false
}

function selectMenu(item: MenuItem) {
  emit('select', item.id)
}
</script>

<template>
  <div 
    class="left-menu h-full flex flex-col transition-all duration-300"
    :class="(collapsed && !isHovering) ? 'w-16' : 'w-56'"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <!-- Logo 区域 -->
    <div class="menu-header p-3 flex items-center justify-center border-b border-gray-700">
      <div class="flex items-center gap-2">
        <img src="https://matechat.gitcode.com/logo.svg" alt="logo" class="w-8 h-8" />
        <span v-if="!collapsed || isHovering" class="text-white font-semibold text-lg">智能体编排</span>
      </div>
    </div>

    <!-- 菜单列表 -->
    <div class="menu-list flex-1 py-2 overflow-y-auto">
      <div
        v-for="item in menuItems"
        :key="item.id"
        @click="selectMenu(item)"
        class="menu-item mx-2 mb-1 px-3 py-3 rounded-lg cursor-pointer transition-all flex items-center gap-3"
        :class="[
          activeMenu === item.id 
            ? 'bg-blue-600 text-white' 
            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
        ]"
      >
        <i :class="item.icon" class="text-lg"></i>
        <span v-if="!collapsed || isHovering" class="text-sm">{{ item.name }}</span>
      </div>
    </div>

    <!-- 底部操作区 -->
    <div class="menu-footer p-3 border-t border-gray-700">
      <div 
        @click="toggleCollapse"
        class="flex items-center justify-center p-2 rounded-lg cursor-pointer text-gray-400 hover:bg-gray-700 hover:text-white transition-all"
      >
        <i :class="collapsed ? 'icon-chevron-right' : 'icon-chevron-left'" class="text-lg"></i>
        <span v-if="!collapsed || isHovering" class="ml-2 text-sm">收起菜单</span>
      </div>
      
      <!-- 底部图标 -->
      <div class="flex items-center justify-around mt-3 pt-3 border-t border-gray-700">
        <i class="icon-language text-gray-400 hover:text-white cursor-pointer text-lg" title="语言"></i>
        <i class="icon-setting text-gray-400 hover:text-white cursor-pointer text-lg" title="设置"></i>
      </div>
    </div>
  </div>
</template>

<style scoped>
.left-menu {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
}

.menu-item {
  min-height: 44px;
}

.menu-header img {
  filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
}
</style>
