<template>
  <div class="email-trigger-config h-full overflow-auto">
    <div class="max-w-4xl mx-auto p-6">
    <!-- 头部 -->
    <div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-100">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
        </div>
        <div>
          <h2 class="text-xl font-bold text-gray-800">邮件触发配置</h2>
          <p class="text-sm text-gray-400">配置邮箱监听，自动触发工作流执行</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full" :class="serviceStatus.is_running ? 'bg-green-50' : 'bg-gray-50'">
          <span class="w-2 h-2 rounded-full" :class="serviceStatus.is_running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"></span>
          <span class="text-sm font-medium" :class="serviceStatus.is_running ? 'text-green-700' : 'text-gray-500'">
            {{ serviceStatus.is_running ? '运行中' : '已停止' }}
          </span>
        </div>
        <button
          v-if="!serviceStatus.is_running"
          @click="startService"
          class="px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-lg hover:from-indigo-600 hover:to-purple-700 transition-all shadow-md shadow-indigo-200 text-sm font-medium"
          :disabled="loading"
        >
          {{ loading ? '启动中...' : '启动服务' }}
        </button>
        <button
          v-else
          @click="stopService"
          class="px-4 py-2 bg-white border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium"
          :disabled="loading"
        >
          {{ loading ? '停止中...' : '停止服务' }}
        </button>
      </div>
    </div>

    <!-- 全局开关 -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-medium text-gray-800">启用邮件触发</h3>
          <p class="text-sm text-gray-500">开启后，系统将自动监听配置的邮箱</p>
        </div>
        <label class="relative inline-flex items-center cursor-pointer">
          <input type="checkbox" v-model="config.enabled" class="sr-only peer" @change="saveConfig">
          <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
        </label>
      </div>
      <div class="mt-4 flex items-center gap-4">
        <label class="text-sm text-gray-600">轮询间隔:</label>
        <input 
          type="number" 
          v-model.number="config.poll_interval_seconds" 
          min="10" 
          max="300"
          class="w-20 px-3 py-1 border border-gray-300 rounded-lg text-sm"
          @change="saveConfig"
        >
        <span class="text-sm text-gray-500">秒</span>
      </div>
    </div>

    <!-- 邮箱账户列表 -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-medium text-gray-800">邮箱账户</h3>
        <button 
          @click="addAccount"
          class="px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors text-sm"
        >
          + 添加邮箱
        </button>
      </div>

      <div v-if="config.email_accounts.length === 0" class="text-center py-8 text-gray-400">
        <span class="text-4xl">📭</span>
        <p class="mt-2">暂无邮箱账户，点击上方按钮添加</p>
      </div>

      <div v-else class="space-y-4">
        <div 
          v-for="(account, index) in config.email_accounts" 
          :key="account.id"
          class="border border-gray-200 rounded-lg p-4"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="text-xl">📬</span>
              <div>
                <input 
                  v-model="account.name" 
                  class="font-medium text-gray-800 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-indigo-500 outline-none"
                  placeholder="账户名称"
                >
                <p class="text-sm text-gray-500">{{ account.email || '未配置邮箱' }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="account.enabled" class="sr-only peer">
                <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
              <button 
                @click="testConnection(account)"
                class="px-3 py-1 text-sm text-indigo-600 hover:bg-indigo-50 rounded"
                :disabled="testing === account.id"
              >
                {{ testing === account.id ? '测试中...' : '测试连接' }}
              </button>
              <button 
                @click="removeAccount(index)"
                class="px-2 py-1 text-red-500 hover:bg-red-50 rounded"
              >
                删除
              </button>
            </div>
          </div>

          <!-- 邮箱配置 -->
          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="col-span-2">
              <label class="block text-xs font-medium text-gray-500 mb-1">邮箱地址</label>
              <input 
                v-model="account.email" 
                type="email"
                class="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200 outline-none transition-all"
                placeholder="example@company.com"
              >
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">端口</label>
              <div class="flex items-center gap-2">
                <input 
                  v-model.number="account.imap_port" 
                  type="number"
                  class="w-20 px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200 outline-none transition-all"
                  placeholder="993"
                >
                <label class="flex items-center gap-1.5 text-sm text-gray-600 cursor-pointer">
                  <input type="checkbox" v-model="account.use_ssl" class="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500">
                  <span>SSL</span>
                </label>
              </div>
            </div>
            <div class="col-span-2">
              <label class="block text-xs font-medium text-gray-500 mb-1">IMAP 服务器</label>
              <input 
                v-model="account.imap_server" 
                class="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200 outline-none transition-all"
                placeholder="imap.company.com"
              >
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-500 mb-1">用户名</label>
              <input 
                v-model="account.username" 
                class="w-full px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200 outline-none transition-all"
                placeholder="用户名"
              >
            </div>
            <div class="col-span-3">
              <label class="block text-xs font-medium text-gray-500 mb-1">密码环境变量</label>
              <div class="flex items-center gap-2">
                <input 
                  v-model="account.password_env" 
                  class="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm font-mono bg-gray-50 focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200 outline-none transition-all"
                  placeholder="EMAIL_PASSWORD"
                >
                <span class="text-xs text-gray-400">密码通过环境变量配置</span>
              </div>
            </div>
          </div>

          <!-- 工作流绑定 -->
          <div class="border-t border-gray-100 pt-3 mt-3">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-xs font-medium text-gray-500 uppercase tracking-wide">工作流绑定</h4>
              <button 
                @click="addWorkflowBinding(account)"
                class="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
              >
                + 添加
              </button>
            </div>
            
            <div v-if="!account.workflow_bindings || account.workflow_bindings.length === 0" class="text-xs text-gray-400 py-2 italic">
              暂无工作流绑定，点击上方添加
            </div>

            <div v-else class="space-y-1.5">
              <div 
                v-for="(binding, bIndex) in account.workflow_bindings" 
                :key="bIndex"
                class="flex items-center gap-2 bg-gradient-to-r from-gray-50 to-white rounded-lg px-3 py-2 border border-gray-100"
              >
                <span class="text-indigo-500 text-sm">📋</span>
                <select 
                  v-model="binding.workflow_name"
                  class="flex-1 px-2 py-1 border border-gray-200 rounded text-sm bg-white focus:border-indigo-400 focus:ring-1 focus:ring-indigo-200 outline-none"
                >
                  <option value="">选择工作流...</option>
                  <option v-for="wf in availableWorkflows" :key="wf" :value="wf">{{ wf }}</option>
                </select>
                <label class="flex items-center gap-1 text-xs text-gray-500 cursor-pointer whitespace-nowrap">
                  <input 
                    type="checkbox" 
                    v-model="binding.default" 
                    class="w-3.5 h-3.5 rounded border-gray-300 text-indigo-600"
                  >
                  默认
                </label>
                <button 
                  @click="removeWorkflowBinding(account, bIndex)"
                  class="text-gray-400 hover:text-red-500 transition-colors p-0.5"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 允许的发送者白名单 -->
    <div class="bg-white rounded-xl border border-gray-200 p-4 mb-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-medium text-gray-800">允许的发送者</h3>
          <p class="text-sm text-gray-500">只有这些地址发送的邮件才能触发工作流（支持通配符 *）</p>
        </div>
        <button 
          @click="addAllowedSender"
          class="px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors text-sm"
        >
          + 添加
        </button>
      </div>

      <div v-if="config.allowed_senders_whitelist.length === 0" class="text-sm text-gray-400 py-2">
        未配置白名单，将接受所有发送者
      </div>

      <div v-else class="flex flex-wrap gap-2">
        <div 
          v-for="(sender, index) in config.allowed_senders_whitelist" 
          :key="index"
          class="flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1"
        >
          <span class="text-sm">{{ sender }}</span>
          <button 
            @click="removeAllowedSender(index)"
            class="text-gray-400 hover:text-red-500"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <!-- 保存按钮 -->
    <div class="flex justify-end gap-3">
      <button 
        @click="loadConfig"
        class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
      >
        重置
      </button>
      <button 
        @click="saveConfig"
        class="px-6 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors"
        :disabled="saving"
      >
        {{ saving ? '保存中...' : '保存配置' }}
      </button>
    </div>
    </div>

    <!-- 测试结果弹窗 -->
    <div v-if="testResult" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click="testResult = null">
      <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4" @click.stop>
        <div class="flex items-center gap-3 mb-4">
          <span class="text-2xl">{{ testResult.success ? '✅' : '❌' }}</span>
          <h3 class="text-lg font-medium">{{ testResult.success ? '连接成功' : '连接失败' }}</h3>
        </div>
        <p class="text-gray-600 mb-4">{{ testResult.message }}</p>
        <div v-if="testResult.details" class="bg-gray-50 rounded-lg p-3 text-sm">
          <p>文件夹数量: {{ testResult.details.folder_count }}</p>
          <p>未读邮件: {{ testResult.details.unread_count }}</p>
        </div>
        <button 
          @click="testResult = null"
          class="mt-4 w-full py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600"
        >
          确定
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface WorkflowBinding {
  workflow_name: string
  conditions: {
    allowed_senders?: string[]
    subject_contains?: string[]
  }
  default: boolean
}

interface EmailAccount {
  id: string
  name: string
  email: string
  imap_server: string
  imap_port: number
  use_ssl: boolean
  username: string
  password_env: string
  enabled: boolean
  workflow_bindings: WorkflowBinding[]
}

interface EmailConfig {
  enabled: boolean
  poll_interval_seconds: number
  email_accounts: EmailAccount[]
  allowed_senders_whitelist: string[]
}

const config = ref<EmailConfig>({
  enabled: false,
  poll_interval_seconds: 30,
  email_accounts: [],
  allowed_senders_whitelist: []
})

const serviceStatus = ref({ is_running: false, listeners: [] })
const availableWorkflows = ref<string[]>([])
const loading = ref(false)
const saving = ref(false)
const testing = ref<string | null>(null)
const testResult = ref<any>(null)

const API_BASE = 'http://localhost:8000'

onMounted(async () => {
  await loadConfig()
  await loadStatus()
  await loadWorkflows()
})

async function loadConfig() {
  try {
    const res = await fetch(`${API_BASE}/email/config`)
    const data = await res.json()
    console.log('[EmailTriggerConfig] 加载配置:', data)
    if (data.success && data.config) {
      // 确保配置对象包含所有必要字段
      config.value = {
        enabled: data.config.enabled ?? false,
        poll_interval_seconds: data.config.poll_interval_seconds ?? 30,
        email_accounts: data.config.email_accounts ?? [],
        allowed_senders_whitelist: data.config.allowed_senders_whitelist ?? []
      }
      console.log('[EmailTriggerConfig] 配置已加载, 邮箱账户数:', config.value.email_accounts.length)
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const res = await fetch(`${API_BASE}/email/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.value)
    })
    const data = await res.json()
    if (data.success) {
      console.log('配置已保存')
    }
  } catch (e) {
    console.error('保存配置失败:', e)
  } finally {
    saving.value = false
  }
}

async function loadStatus() {
  try {
    const res = await fetch(`${API_BASE}/email/status`)
    const data = await res.json()
    if (data.success) {
      serviceStatus.value = data
    }
  } catch (e) {
    console.error('获取状态失败:', e)
  }
}

async function loadWorkflows() {
  try {
    const res = await fetch(`${API_BASE}/api/workflowsquery`)
    const data = await res.json()
    if (data.workflows) {
      availableWorkflows.value = data.workflows.map((w: any) => w.name)
    }
  } catch (e) {
    console.error('获取工作流列表失败:', e)
  }
}

async function startService() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/email/start`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      await loadStatus()
    }
  } catch (e) {
    console.error('启动服务失败:', e)
  } finally {
    loading.value = false
  }
}

async function stopService() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/email/stop`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      await loadStatus()
    }
  } catch (e) {
    console.error('停止服务失败:', e)
  } finally {
    loading.value = false
  }
}

async function testConnection(account: EmailAccount) {
  testing.value = account.id
  try {
    // 需要用户输入密码进行测试
    const password = prompt('请输入邮箱密码进行测试连接:')
    if (!password) {
      testing.value = null
      return
    }

    const res = await fetch(`${API_BASE}/email/test-connection`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        imap_server: account.imap_server,
        imap_port: account.imap_port,
        use_ssl: account.use_ssl,
        username: account.username,
        password: password
      })
    })
    testResult.value = await res.json()
  } catch (e) {
    testResult.value = { success: false, message: '测试请求失败' }
  } finally {
    testing.value = null
  }
}

function addAccount() {
  const id = 'account_' + Date.now()
  const newAccount: EmailAccount = {
    id,
    name: '新邮箱账户',
    email: '',
    imap_server: '',
    imap_port: 993,
    use_ssl: true,
    username: '',
    password_env: 'EMAIL_PASSWORD_' + config.value.email_accounts.length,
    enabled: true,
    workflow_bindings: []
  }
  // 使用新数组触发响应式更新
  config.value.email_accounts = [...config.value.email_accounts, newAccount]
  console.log('[EmailTriggerConfig] 添加邮箱账户, 当前数量:', config.value.email_accounts.length)
}

function removeAccount(index: number) {
  if (confirm('确定删除此邮箱账户?')) {
    config.value.email_accounts.splice(index, 1)
  }
}

function addWorkflowBinding(account: EmailAccount) {
  if (!account.workflow_bindings) {
    account.workflow_bindings = []
  }
  account.workflow_bindings.push({
    workflow_name: '',
    conditions: { allowed_senders: ['*'], subject_contains: [] },
    default: account.workflow_bindings.length === 0
  })
}

function removeWorkflowBinding(account: EmailAccount, index: number) {
  account.workflow_bindings.splice(index, 1)
}

function addAllowedSender() {
  const sender = prompt('请输入允许的发送者邮箱（支持通配符 *，如 *@company.com）:')
  if (sender) {
    config.value.allowed_senders_whitelist.push(sender)
  }
}

function removeAllowedSender(index: number) {
  config.value.allowed_senders_whitelist.splice(index, 1)
}
</script>

<style scoped>
.email-trigger-config {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

/* 自定义滚动条 */
.email-trigger-config::-webkit-scrollbar {
  width: 6px;
}

.email-trigger-config::-webkit-scrollbar-track {
  background: transparent;
}

.email-trigger-config::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.email-trigger-config::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
