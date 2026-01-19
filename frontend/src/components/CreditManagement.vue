<template>
  <div class="credit-management">
    <div class="credit-header">
      <h2>积分管理</h2>
      <p class="subtitle">管理用户积分，设置积分消耗规则</p>
    </div>

    <!-- 用户积分列表 -->
    <div class="credit-table-wrapper">
      <table class="credit-table">
        <thead>
          <tr>
            <th>用户ID</th>
            <th>用户名</th>
            <th>显示名称</th>
            <th>角色</th>
            <th>当前积分</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.display_name || '-' }}</td>
            <td>
              <span class="role-badge" :class="user.role">
                {{ getRoleLabel(user.role) }}
              </span>
            </td>
            <td>
              <span class="credits-value">💎 {{ user.credits ?? 0 }}</span>
            </td>
            <td>
              <div class="action-buttons">
                <button class="btn-adjust" @click="openAdjustDialog(user, 'add')">
                  + 充值
                </button>
                <button class="btn-set" @click="openAdjustDialog(user, 'set')">
                  设置
                </button>
                <button class="btn-logs" @click="openLogsDialog(user)">
                  记录
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 调整积分对话框 -->
    <div v-if="showAdjustDialog" class="dialog-overlay" @click.self="closeAdjustDialog">
      <div class="dialog">
        <div class="dialog-header">
          <h3>{{ adjustMode === 'add' ? '充值积分' : '设置积分' }}</h3>
          <button class="close-btn" @click="closeAdjustDialog">×</button>
        </div>
        <div class="dialog-body">
          <div class="form-item">
            <label>用户</label>
            <div class="user-info-display">
              {{ selectedUser?.display_name || selectedUser?.username }}
              <span class="current-credits">当前积分: {{ selectedUser?.credits ?? 0 }}</span>
            </div>
          </div>
          <div class="form-item">
            <label>{{ adjustMode === 'add' ? '充值数量' : '设置为' }}</label>
            <input 
              type="number" 
              v-model.number="adjustAmount" 
              :min="adjustMode === 'set' ? 0 : 1"
              :placeholder="adjustMode === 'add' ? '输入充值积分数量' : '输入积分数量'"
            />
          </div>
          <div class="form-item">
            <label>备注</label>
            <input 
              type="text" 
              v-model="adjustDescription" 
              placeholder="操作备注（可选）"
            />
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="closeAdjustDialog">取消</button>
          <button class="btn-confirm" @click="confirmAdjust" :disabled="adjusting">
            {{ adjusting ? '处理中...' : '确认' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 积分记录对话框 -->
    <div v-if="showLogsDialog" class="dialog-overlay" @click.self="closeLogsDialog">
      <div class="dialog logs-dialog">
        <div class="dialog-header">
          <h3>积分记录 - {{ selectedUser?.display_name || selectedUser?.username }}</h3>
          <button class="close-btn" @click="closeLogsDialog">×</button>
        </div>
        <div class="dialog-body">
          <table class="logs-table" v-if="creditLogs.length > 0">
            <thead>
              <tr>
                <th>时间</th>
                <th>变动</th>
                <th>余额</th>
                <th>类型</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in creditLogs" :key="log.id">
                <td>{{ formatTime(log.created_at) }}</td>
                <td :class="log.amount > 0 ? 'positive' : 'negative'">
                  {{ log.amount > 0 ? '+' : '' }}{{ log.amount }}
                </td>
                <td>{{ log.balance }}</td>
                <td>{{ getActionLabel(log.action) }}</td>
                <td>{{ log.description || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-else class="no-logs">暂无积分记录</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

interface UserCredit {
  id: number
  username: string
  display_name: string | null
  credits: number
  role: string
}

interface CreditLog {
  id: number
  user_id: number
  amount: number
  balance: number
  action: string
  description: string | null
  created_at: string
}

const users = ref<UserCredit[]>([])
const showAdjustDialog = ref(false)
const showLogsDialog = ref(false)
const selectedUser = ref<UserCredit | null>(null)
const adjustMode = ref<'add' | 'set'>('add')
const adjustAmount = ref(0)
const adjustDescription = ref('')
const adjusting = ref(false)
const creditLogs = ref<CreditLog[]>([])

function getRoleLabel(role: string): string {
  const labels: Record<string, string> = {
    'admin': '管理员',
    'operator': '操作员',
    'viewer': '查看者'
  }
  return labels[role] || role
}

function getActionLabel(action: string): string {
  const labels: Record<string, string> = {
    'admin_set': '管理员设置',
    'admin_adjust': '管理员调整',
    'recharge': '充值',
    'consume': '消费',
    'crew_compare_export': '导出船员比对报告'
  }
  return labels[action] || action
}

function formatTime(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadUsers() {
  try {
    const response = await fetch('/api/credits/users', {
      headers: {
        'Authorization': `Bearer ${userStore.token.value}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        users.value = data.data
      }
    }
  } catch (e) {
    console.error('加载用户积分失败:', e)
  }
}

function openAdjustDialog(user: UserCredit, mode: 'add' | 'set') {
  selectedUser.value = user
  adjustMode.value = mode
  adjustAmount.value = mode === 'set' ? (user.credits ?? 0) : 0
  adjustDescription.value = ''
  showAdjustDialog.value = true
}

function closeAdjustDialog() {
  showAdjustDialog.value = false
  selectedUser.value = null
}

async function confirmAdjust() {
  if (!selectedUser.value) return
  
  adjusting.value = true
  try {
    const endpoint = adjustMode.value === 'set' ? '/api/credits/set' : '/api/credits/adjust'
    const body = adjustMode.value === 'set' 
      ? {
          user_id: selectedUser.value.id,
          credits: adjustAmount.value,
          description: adjustDescription.value || undefined
        }
      : {
          user_id: selectedUser.value.id,
          amount: adjustAmount.value,
          action: 'recharge',
          description: adjustDescription.value || '管理员充值'
        }
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token.value}`
      },
      body: JSON.stringify(body)
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        await loadUsers()
        closeAdjustDialog()
      }
    }
  } catch (e) {
    console.error('调整积分失败:', e)
  } finally {
    adjusting.value = false
  }
}

async function openLogsDialog(user: UserCredit) {
  selectedUser.value = user
  creditLogs.value = []
  showLogsDialog.value = true
  
  try {
    const response = await fetch(`/api/credits/user/${user.id}/logs`, {
      headers: {
        'Authorization': `Bearer ${userStore.token.value}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        creditLogs.value = data.data
      }
    }
  } catch (e) {
    console.error('加载积分记录失败:', e)
  }
}

function closeLogsDialog() {
  showLogsDialog.value = false
  selectedUser.value = null
  creditLogs.value = []
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.credit-management {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.credit-header {
  margin-bottom: 24px;
}

.credit-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.credit-header .subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.credit-table-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.credit-table {
  width: 100%;
  border-collapse: collapse;
}

.credit-table th,
.credit-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.credit-table th {
  background: #fafafa;
  font-weight: 500;
  color: #666;
  font-size: 13px;
}

.credit-table tbody tr:hover {
  background: #fafafa;
}

.role-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background: #fff1f0;
  color: #cf1322;
}

.role-badge.operator {
  background: #e6f7ff;
  color: #0050b3;
}

.role-badge.viewer {
  background: #f6ffed;
  color: #389e0d;
}

.credits-value {
  font-weight: 600;
  color: #d97706;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-buttons button {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-adjust {
  background: #e6f7ff;
  color: #1890ff;
}

.btn-adjust:hover {
  background: #1890ff;
  color: white;
}

.btn-set {
  background: #fff7e6;
  color: #d97706;
}

.btn-set:hover {
  background: #d97706;
  color: white;
}

.btn-logs {
  background: #f0f0f0;
  color: #666;
}

.btn-logs:hover {
  background: #666;
  color: white;
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.logs-dialog {
  max-width: 700px;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  border-radius: 4px;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.dialog-body {
  padding: 20px;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.form-item input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-item input:focus {
  outline: none;
  border-color: #d97706;
  box-shadow: 0 0 0 2px rgba(217, 119, 6, 0.1);
}

.user-info-display {
  padding: 10px 12px;
  background: #f5f5f5;
  border-radius: 8px;
  font-size: 14px;
}

.current-credits {
  margin-left: 12px;
  color: #d97706;
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}

.btn-cancel,
.btn-confirm {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #f0f0f0;
  color: #666;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-confirm {
  background: #d97706;
  color: white;
}

.btn-confirm:hover:not(:disabled) {
  background: #b45309;
}

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 积分记录表格 */
.logs-table {
  width: 100%;
  border-collapse: collapse;
}

.logs-table th,
.logs-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.logs-table th {
  background: #fafafa;
  font-weight: 500;
  color: #666;
}

.logs-table .positive {
  color: #52c41a;
  font-weight: 500;
}

.logs-table .negative {
  color: #ff4d4f;
  font-weight: 500;
}

.no-logs {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>
