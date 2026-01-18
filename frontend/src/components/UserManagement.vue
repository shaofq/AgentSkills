<template>
  <div class="user-management">
    <div class="page-header">
      <h2>用户管理</h2>
      <button class="btn-primary" @click="showAddModal = true">
        <span class="icon">+</span> 添加用户
      </button>
    </div>
    
    <!-- 用户列表 -->
    <div class="user-table-container">
      <table class="user-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>显示名称</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>最后登录</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.display_name || '-' }}</td>
            <td>{{ user.email || '-' }}</td>
            <td>
              <span class="role-badge" :class="user.role">
                {{ getRoleLabel(user.role) }}
              </span>
            </td>
            <td>
              <span class="status-badge" :class="user.is_active ? 'active' : 'inactive'">
                {{ user.is_active ? '正常' : '已禁用' }}
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>{{ user.last_login ? formatDate(user.last_login) : '-' }}</td>
            <td class="actions">
              <button class="btn-icon" @click="editUser(user)" title="编辑">✏️</button>
              <button 
                class="btn-icon" 
                @click="toggleUserStatus(user)" 
                :title="user.is_active ? '禁用' : '启用'"
              >
                {{ user.is_active ? '🔒' : '🔓' }}
              </button>
              <button 
                class="btn-icon danger" 
                @click="deleteUser(user)" 
                title="删除"
                :disabled="user.role === 'admin'"
              >🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="users.length === 0" class="empty-state">
        暂无用户数据
      </div>
    </div>
    
    <!-- 添加/编辑用户弹窗 -->
    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ showEditModal ? '编辑用户' : '添加用户' }}</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        
        <form @submit.prevent="handleSubmit" class="modal-body">
          <div class="form-group">
            <label>用户名 *</label>
            <input 
              v-model="formData.username" 
              type="text" 
              placeholder="请输入用户名"
              :disabled="showEditModal"
              required
            />
          </div>
          
          <div class="form-group">
            <label>{{ showEditModal ? '新密码（留空不修改）' : '密码 *' }}</label>
            <input 
              v-model="formData.password" 
              type="password" 
              placeholder="请输入密码"
              :required="!showEditModal"
            />
          </div>
          
          <div class="form-group">
            <label>显示名称</label>
            <input 
              v-model="formData.display_name" 
              type="text" 
              placeholder="请输入显示名称"
            />
          </div>
          
          <div class="form-group">
            <label>邮箱</label>
            <input 
              v-model="formData.email" 
              type="email" 
              placeholder="请输入邮箱"
            />
          </div>
          
          <div class="form-group">
            <label>角色 *</label>
            <select v-model="formData.role" required>
              <option value="admin">管理员</option>
              <option value="operator">操作员</option>
              <option value="viewer">查看者</option>
            </select>
          </div>
          
          <div v-if="formError" class="error-message">
            {{ formError }}
          </div>
          
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="closeModal">取消</button>
            <button type="submit" class="btn-primary" :disabled="submitting">
              {{ submitting ? '提交中...' : '确定' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/user'

interface User {
  id: number
  username: string
  email: string | null
  display_name: string | null
  role: string
  is_active: boolean
  created_at: string
  last_login: string | null
}

const userStore = useUserStore()
const users = ref<User[]>([])
const showAddModal = ref(false)
const showEditModal = ref(false)
const editingUser = ref<User | null>(null)
const submitting = ref(false)
const formError = ref('')

const formData = reactive({
  username: '',
  password: '',
  display_name: '',
  email: '',
  role: 'operator'
})

// 获取请求头
function getAuthHeaders() {
  return {
    Authorization: `Bearer ${userStore.token.value}`
  }
}

// 加载用户列表
async function loadUsers() {
  try {
    const response = await axios.get('/api/auth/users', {
      headers: getAuthHeaders()
    })
    if (response.data.success) {
      users.value = response.data.data
    }
  } catch (error: any) {
    console.error('加载用户列表失败:', error)
    alert('加载用户列表失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 获取角色标签
function getRoleLabel(role: string) {
  const labels: Record<string, string> = {
    admin: '管理员',
    operator: '操作员',
    viewer: '查看者'
  }
  return labels[role] || role
}

// 格式化日期
function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 编辑用户
function editUser(user: User) {
  editingUser.value = user
  formData.username = user.username
  formData.password = ''
  formData.display_name = user.display_name || ''
  formData.email = user.email || ''
  formData.role = user.role
  showEditModal.value = true
}

// 切换用户状态
async function toggleUserStatus(user: User) {
  const action = user.is_active ? '禁用' : '启用'
  if (!confirm(`确定要${action}用户 "${user.username}" 吗？`)) return
  
  try {
    await axios.put(`/api/auth/users/${user.id}`, {
      is_active: !user.is_active
    }, {
      headers: getAuthHeaders()
    })
    await loadUsers()
  } catch (error: any) {
    alert(`${action}失败: ` + (error.response?.data?.detail || error.message))
  }
}

// 删除用户
async function deleteUser(user: User) {
  if (user.role === 'admin') {
    alert('不能删除管理员用户')
    return
  }
  
  if (!confirm(`确定要删除用户 "${user.username}" 吗？此操作不可恢复！`)) return
  
  try {
    await axios.delete(`/api/auth/users/${user.id}`, {
      headers: getAuthHeaders()
    })
    await loadUsers()
  } catch (error: any) {
    alert('删除失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 关闭弹窗
function closeModal() {
  showAddModal.value = false
  showEditModal.value = false
  editingUser.value = null
  formError.value = ''
  Object.assign(formData, {
    username: '',
    password: '',
    display_name: '',
    email: '',
    role: 'operator'
  })
}

// 提交表单
async function handleSubmit() {
  formError.value = ''
  submitting.value = true
  
  try {
    if (showEditModal.value && editingUser.value) {
      // 编辑用户
      const updateData: any = {
        display_name: formData.display_name || null,
        email: formData.email || null,
        role: formData.role
      }
      if (formData.password) {
        updateData.password = formData.password
      }
      
      await axios.put(`/api/auth/users/${editingUser.value.id}`, updateData, {
        headers: getAuthHeaders()
      })
    } else {
      // 添加用户
      await axios.post('/api/auth/register', {
        username: formData.username,
        password: formData.password,
        display_name: formData.display_name || formData.username,
        email: formData.email || null,
        role: formData.role
      }, {
        headers: getAuthHeaders()
      })
    }
    
    closeModal()
    await loadUsers()
  } catch (error: any) {
    formError.value = error.response?.data?.detail || '操作失败'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f0f0f0;
  color: #666;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.user-table-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
}

.user-table th,
.user-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.user-table th {
  background: #fafafa;
  font-weight: 600;
  color: #666;
  font-size: 13px;
}

.user-table td {
  font-size: 14px;
  color: #333;
}

.user-table tr:hover {
  background: #fafafa;
}

.role-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background: #fff1f0;
  color: #ff4d4f;
}

.role-badge.operator {
  background: #e6f7ff;
  color: #1890ff;
}

.role-badge.viewer {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.status-badge.active {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.inactive {
  background: #fff2f0;
  color: #ff4d4f;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-icon:hover:not(:disabled) {
  background: #e8e8e8;
}

.btn-icon.danger:hover:not(:disabled) {
  background: #fff1f0;
}

.btn-icon:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.empty-state {
  padding: 60px;
  text-align: center;
  color: #999;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input:disabled {
  background: #f5f5f5;
}

.error-message {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
