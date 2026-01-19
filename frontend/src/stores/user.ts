// 用户状态管理
import { ref, computed } from 'vue'

// 用户信息接口
export interface User {
  id: number
  username: string
  email: string | null
  display_name: string | null
  role: 'admin' | 'operator' | 'viewer'
  is_active: boolean
  credits: number
  created_at: string
  last_login: string | null
}

// 用户状态
const user = ref<User | null>(null)
const token = ref<string | null>(null)
const permissions = ref<string[]>([])
const isAuthenticated = computed(() => !!token.value && !!user.value)

// 初始化 - 从localStorage恢复
function init() {
  const savedToken = localStorage.getItem('token')
  const savedUser = localStorage.getItem('user')
  const savedPermissions = localStorage.getItem('permissions')
  
  if (savedToken && savedUser) {
    token.value = savedToken
    try {
      user.value = JSON.parse(savedUser)
      permissions.value = savedPermissions ? JSON.parse(savedPermissions) : []
    } catch (e) {
      console.error('解析用户信息失败:', e)
      logout()
    }
  }
}

// 登录
function setAuth(authData: { access_token: string; user: User; permissions: string[] }) {
  token.value = authData.access_token
  user.value = authData.user
  permissions.value = authData.permissions
  
  localStorage.setItem('token', authData.access_token)
  localStorage.setItem('user', JSON.stringify(authData.user))
  localStorage.setItem('permissions', JSON.stringify(authData.permissions))
}

// 登出
function logout() {
  token.value = null
  user.value = null
  permissions.value = []
  
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  localStorage.removeItem('permissions')
}

// 检查权限
function hasPermission(permission: string): boolean {
  if (!isAuthenticated.value) return false
  if (permissions.value.includes('*')) return true
  return permissions.value.includes(permission)
}

// 检查角色
function hasRole(role: string): boolean {
  return user.value?.role === role
}

// 是否管理员
const isAdmin = computed(() => user.value?.role === 'admin')

// 用户积分
const credits = computed(() => user.value?.credits ?? 0)

// 刷新积分
async function refreshCredits() {
  if (!token.value) return
  try {
    const response = await fetch('/api/credits/me', {
      headers: {
        'Authorization': `Bearer ${token.value}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      if (data.success && user.value) {
        user.value.credits = data.data.credits
        localStorage.setItem('user', JSON.stringify(user.value))
      }
    }
  } catch (e) {
    console.error('刷新积分失败:', e)
  }
}

// 导出
export function useUserStore() {
  return {
    user,
    token,
    permissions,
    isAuthenticated,
    isAdmin,
    credits,
    init,
    setAuth,
    logout,
    hasPermission,
    hasRole,
    refreshCredits
  }
}

// 初始化
init()
