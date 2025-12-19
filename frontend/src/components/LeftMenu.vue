<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

const emit = defineEmits<{
  (e: 'select', menu: string): void
  (e: 'menuLoaded', menus: MenuItem[]): void
  (e: 'logout'): void
}>()

function handleLogout() {
  emit('logout')
}

const props = defineProps<{
  activeMenu: string
}>()

export interface MenuItem {
  id: string
  name: string
  icon: string
  type: 'agent' | 'workflow' | 'chat'
  apiType?: string | null
  apiUrl?: string | null
  workflowName?: string | null
  description?: string
  model?: string | null
}

export interface MenuGroup {
  id: string
  name: string
  menus: MenuItem[]
}

const menuGroups = ref<MenuGroup[]>([
  {
    id: 'user-functions',
    name: '使用功能',
    menus: [
      { id: 'chat', name: '对话', icon: 'icon-message', type: 'chat' },
      { id: 'code-agent', name: '代码助手', icon: 'icon-code', type: 'agent' },
      { id: 'policy-qa', name: '制度问答', icon: 'icon-help', type: 'agent' },
    ]
  },
  {
    id: 'system-functions',
    name: '系统功能',
    menus: [
      { id: 'workflow', name: '流程编排', icon: 'icon-application', type: 'workflow' },
      { id: 'workflow-list', name: '流程查询', icon: 'icon-merge-request2', type: 'workflow' },
    ]
  }
])

// 扁平化的菜单列表，用于向父组件传递
const allMenuItems = computed(() => {
  return menuGroups.value.flatMap(group => group.menus)
})

async function loadMenuBindings() {
  try {
    const response = await fetch('http://localhost:8000/api/menu-bindings')
    if (response.ok) {
      const data = await response.json()
      // 支持新的分组格式
      if (data.menuGroups && data.menuGroups.length > 0) {
        menuGroups.value = data.menuGroups.map((group: any) => ({
          id: group.id,
          name: group.name,
          menus: group.menus.map((menu: any) => ({
            id: menu.id,
            name: menu.name,
            icon: menu.icon,
            type: menu.type,
            apiType: menu.apiType,
            apiUrl: menu.apiUrl,
            workflowName: menu.workflowName,
            description: menu.description,
            model: menu.model,
          }))
        }))
        emit('menuLoaded', allMenuItems.value)
        console.log('[LeftMenu] 加载菜单配置成功:', allMenuItems.value.length, '个菜单项')
      } else if (data.menus && data.menus.length > 0) {
        // 兼容旧格式
        menuGroups.value = [{
          id: 'default',
          name: '',
          menus: data.menus.map((menu: any) => ({
            id: menu.id,
            name: menu.name,
            icon: menu.icon,
            type: menu.type,
            apiType: menu.apiType,
            apiUrl: menu.apiUrl,
            workflowName: menu.workflowName,
            description: menu.description,
            model: menu.model,
          }))
        }]
        emit('menuLoaded', allMenuItems.value)
        console.log('[LeftMenu] 加载菜单配置成功(旧格式):', allMenuItems.value.length, '个菜单项')
      }
    }
  } catch (err) {
    console.error('[LeftMenu] 加载菜单配置失败:', err)
  }
}

onMounted(() => {
  loadMenuBindings()
})

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
      <template v-for="group in menuGroups" :key="group.id">
        <!-- 分组标题 -->
        <div 
          v-if="group.name && (!collapsed || isHovering)" 
          class="group-title mx-3 mt-3 mb-2 text-xs text-gray-500 font-medium uppercase tracking-wider"
        >
          {{ group.name }}
        </div>
        <div v-else-if="group.name" class="group-divider mx-3 my-2 border-t border-gray-700"></div>
        
        <!-- 分组菜单项 -->
        <div
          v-for="item in group.menus"
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
      </template>
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
        <svg 
          class="w-5 h-5 text-gray-400 hover:text-red-400 cursor-pointer transition-colors" 
          title="退出登录"
          @click="handleLogout"
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          stroke-width="2" 
          stroke-linecap="round" 
          stroke-linejoin="round"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.left-menu {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
}

.menu-list {
  scrollbar-width: thin;
  scrollbar-color: #4b5563 transparent;
  min-height: 0;
}

.menu-list::-webkit-scrollbar {
  width: 4px;
}

.menu-list::-webkit-scrollbar-track {
  background: transparent;
}

.menu-list::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 2px;
}

.menu-item {
  min-height: 44px;
}

.menu-header img {
  filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
}

.group-title {
  color: #9ca3af;
}
</style>
