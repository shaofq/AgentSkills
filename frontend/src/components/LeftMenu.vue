<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useTheme } from '../composables/useTheme'

const { currentTheme, toggleTheme } = useTheme()

const emit = defineEmits<{
  (e: 'select', menu: string): void
  (e: 'menuLoaded', menus: MenuItem[]): void
  (e: 'logout'): void
  (e: 'openSettings'): void
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

function handleOpenSettings() {
  emit('openSettings')
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
    <div class="menu-header p-3 flex items-center justify-center">
      <div class="flex items-center gap-2">
        <img src="https://matechat.gitcode.com/logo.svg" alt="logo" class="w-8 h-8" />
        <span v-if="!collapsed || isHovering" class="menu-title font-semibold text-lg">智能体编排</span>
      </div>
    </div>

    <!-- 菜单列表 -->
    <div class="menu-list flex-1 py-2 overflow-y-auto">
      <template v-for="group in menuGroups" :key="group.id">
        <!-- 分组标题 -->
        <div 
          v-if="group.name && (!collapsed || isHovering)" 
          class="group-title mx-3 mt-3 mb-2 text-xs font-medium uppercase tracking-wider"
        >
          {{ group.name }}
        </div>
        <div v-else-if="group.name" class="group-divider mx-3 my-2"></div>
        
        <!-- 分组菜单项 -->
        <div
          v-for="item in group.menus"
          :key="item.id"
          @click="selectMenu(item)"
          class="menu-item mx-2 mb-1 px-3 py-3 rounded-lg cursor-pointer transition-all flex items-center gap-3"
          :class="[
            activeMenu === item.id 
              ? 'active' 
              : 'inactive'
          ]"
        >
          <i :class="item.icon" class="text-lg"></i>
          <span v-if="!collapsed || isHovering" class="text-sm">{{ item.name }}</span>
        </div>
      </template>
    </div>

    <!-- 底部操作区 -->
    <div class="menu-footer p-3">
      <div 
        @click="toggleCollapse"
        class="collapse-btn flex items-center justify-center p-2 rounded-lg cursor-pointer transition-all"
      >
        <i :class="collapsed ? 'icon-chevron-right' : 'icon-chevron-left'" class="text-lg"></i>
        <span v-if="!collapsed || isHovering" class="ml-2 text-sm">收起菜单</span>
      </div>
      
      <!-- 底部图标 -->
      <div class="bottom-icons flex items-center justify-around mt-3 pt-3">
        <!-- 主题切换按钮 -->
        <svg 
          class="w-5 h-5 icon-btn cursor-pointer transition-colors"
          :title="currentTheme === 'dark' ? '切换到浅色主题' : '切换到深色主题'"
          @click="toggleTheme"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <!-- 太阳图标（深色主题时显示） -->
          <template v-if="currentTheme === 'dark'">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </template>
          <!-- 月亮图标（浅色主题时显示） -->
          <template v-else>
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </template>
        </svg>
        <i class="icon-setting icon-btn cursor-pointer text-lg" title="设置" @click="handleOpenSettings"></i>
        <svg 
          class="w-5 h-5 icon-btn logout-btn cursor-pointer transition-colors" 
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
  background: var(--menu-bg);
  transition: background 0.3s ease;
  border-right: 1px solid var(--menu-border);
}

.menu-header {
  border-bottom: 1px solid var(--menu-border);
}

.menu-title {
  color: var(--menu-text);
}

.menu-list {
  scrollbar-width: thin;
  scrollbar-color: var(--menu-text-muted) transparent;
  min-height: 0;
}

.menu-list::-webkit-scrollbar {
  width: 4px;
}

.menu-list::-webkit-scrollbar-track {
  background: transparent;
}

.menu-list::-webkit-scrollbar-thumb {
  background: var(--menu-text-muted);
  border-radius: 2px;
}

.menu-item {
  min-height: 44px;
  color: var(--menu-text);
}

.menu-item.active {
  background: var(--menu-item-active);
  color: #ffffff;
}

.menu-item.inactive {
  color: var(--menu-text);
}

.menu-item.inactive:hover {
  background: var(--menu-item-hover);
}

.menu-header img {
  filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
}

.group-title {
  color: var(--menu-text-muted);
}

.group-divider {
  border-top: 1px solid var(--menu-border);
}

.menu-footer {
  border-top: 1px solid var(--menu-border);
}

.collapse-btn {
  color: var(--menu-text-muted);
}

.collapse-btn:hover {
  background: var(--menu-item-hover);
  color: var(--menu-text);
}

.bottom-icons {
  border-top: 1px solid var(--menu-border);
}

.icon-btn {
  color: var(--menu-text-muted);
}

.icon-btn:hover {
  color: var(--menu-text);
}

.logout-btn:hover {
  color: #ef4444;
}
</style>
