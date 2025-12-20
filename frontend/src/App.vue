<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Button } from 'vue-devui/button'
import 'vue-devui/button/style.css'
import FlowCanvas from './components/FlowCanvas.vue'
import Sidebar from './components/Sidebar.vue'
import NodeConfigPanel from './components/NodeConfigPanel.vue'
import Toolbar from './components/Toolbar.vue'
import LeftMenu from './components/LeftMenu.vue'
import PolicyQADialog from './components/PolicyQADialog.vue'
import WorkflowListDialog from './components/WorkflowListDialog.vue'
import LoginDialog from './components/LoginDialog.vue'
import CodeAssistantView from './components/CodeAssistantView.vue'

// 菜单配置类型
interface MenuConfig {
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

// 当前选中的菜单
const activeMenu = ref('chat')
const showConfigPanel = ref(false)
const showPolicyQA = ref(false)
// 默认菜单配置（当后端未返回时使用）
const defaultMenuConfigs: MenuConfig[] = [
  { id: 'chat', name: '对话', icon: 'icon-message', type: 'chat', apiType: 'chat', apiUrl: '/api/chat', workflowName: null, description: '通用对话助手，可以回答各种问题。', model: 'deepseek-ai/DeepSeek-R1' },
  { id: 'code-agent', name: '代码助手', icon: 'icon-code', type: 'agent', apiType: 'workflow', apiUrl: 'http://localhost:8000/api/workflow/run', workflowName: 'code_assistant', description: '专业的代码生成和调试助手。', model: 'qwen3-max' },
  { id: 'pptx-agent', name: 'PPT助手', icon: 'icon-file', type: 'agent', apiType: 'workflow', apiUrl: 'http://localhost:8000/api/workflow/run', workflowName: 'pptx_assistant', description: '演示文稿制作助手。', model: 'qwen3-max' },
  { id: 'data-agent', name: '数据分析', icon: 'icon-data-storage', type: 'agent', apiType: 'workflow', apiUrl: 'http://localhost:8000/api/workflow/run', workflowName: 'data_flow', description: '数据分析和可视化助手。', model: 'qwen3-max' },
  { id: 'policy-qa', name: '制度问答', icon: 'icon-help', type: 'agent', apiType: 'policy-qa', apiUrl: 'http://localhost:8000/api/policy-qa/sync', workflowName: null, description: '公司制度问答助手。', model: 'qwen3-max' },
  { id: 'ocr-agent', name: 'OCR识别', icon: 'icon-base-info', type: 'agent', apiType: 'ocr', apiUrl: 'http://localhost:8000/api/ocr/recognize', workflowName: null, description: 'OCR 文件识别助手。', model: 'qwen3-max' },
  { id: 'skill-creator', name: '技能创建', icon: 'icon-identity', type: 'agent', apiType: 'skill-creator', apiUrl: 'http://localhost:8000/api/skill-creator/chat', workflowName: null, description: '技能创建助手。', model: 'qwen3-max' },
  { id: 'workflow', name: '流程编排', icon: 'icon-application', type: 'workflow', apiType: null, apiUrl: null, workflowName: null, description: '可视化工作流编排工具', model: null },
  { id: 'workflow-list', name: '流程查询', icon: 'icon-merge-request2', type: 'workflow', apiType: null, apiUrl: null, workflowName: null, description: '查询和管理已加载的工作流', model: null },
]
const menuConfigs = ref<MenuConfig[]>(defaultMenuConfigs)

// 是否显示工作流模式
const isWorkflowMode = computed(() => activeMenu.value === 'workflow')
const isWorkflowListMode = computed(() => activeMenu.value === 'workflow-list')
const isCodeAssistantMode = computed(() => activeMenu.value === 'code-agent')

// 菜单加载完成回调
function handleMenuLoaded(menus: MenuConfig[]) {
  menuConfigs.value = menus
  console.log('[App] 菜单配置已加载:', menus.length, '个菜单项')
}

// 获取当前菜单配置（优先从加载的配置中查找，否则使用默认配置）
const currentMenuConfig = computed(() => {
  const config = menuConfigs.value.find(m => m.id === activeMenu.value)
  if (config) return config
  return defaultMenuConfigs.find(m => m.id === activeMenu.value)
})

// 当前智能体信息（从菜单配置中获取）
const currentAgent = computed(() => {
  const menu = currentMenuConfig.value
  if (menu) {
    return {
      name: menu.name,
      description: menu.description ? [menu.description] : ['欢迎使用'],
      model: menu.model || 'qwen3-max'
    }
  }
  // 默认值
  return {
    name: '智能对话',
    description: ['通用对话助手，可以回答各种问题。', '支持多轮对话和上下文理解。'],
    model: 'deepseek-ai/DeepSeek-R1'
  }
})

// 登录状态
const isLoggedIn = ref(false)
const currentUser = ref<{ username: string } | null>(null)

// 检查登录状态
function checkLoginStatus() {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      currentUser.value = user
      isLoggedIn.value = true
    } catch {
      isLoggedIn.value = false
    }
  }
}

// 登录成功处理
function handleLoginSuccess(user: { username: string }) {
  currentUser.value = user
  isLoggedIn.value = true
}

// 退出登录
function handleLogout() {
  localStorage.removeItem('user')
  currentUser.value = null
  isLoggedIn.value = false
}

// 组件挂载时检查登录状态
onMounted(() => {
  checkLoginStatus()
})

// 对话相关状态
const startPage = ref(true)
const inputValue = ref('')
const messages = ref<{ from: 'user' | 'model'; content: string; loading?: boolean }[]>([])

// 菜单选择处理
function handleMenuSelect(menuId: string) {
  activeMenu.value = menuId
  // 切换菜单时重置对话状态
  if (menuId !== 'workflow') {
    startPage.value = true
    messages.value = []
  }
}

const introPrompt = {
  direction: 'horizontal' as const,
  list: [
    {
      value: 'createWorkflow',
      label: '创建一个工作流',
      iconConfig: { name: 'icon-info-o', color: '#5e7ce0' },
      desc: '开始创建智能体工作流',
    },
    {
      value: 'helpMe',
      label: '你可以帮我做什么？',
      iconConfig: { name: 'icon-star', color: 'rgb(255, 215, 0)' },
      desc: '了解系统功能',
    },
    {
      value: 'generateCode',
      label: '帮我生成代码',
      iconConfig: { name: 'icon-priority', color: '#3ac295' },
      desc: '使用代码智能体生成代码',
    },
  ],
}

const simplePrompt = [
  { value: 'createWorkflow', iconConfig: { name: 'icon-info-o', color: '#5e7ce0' }, label: '创建工作流' },
  { value: 'runWorkflow', iconConfig: { name: 'icon-star', color: 'rgb(255, 215, 0)' }, label: '运行工作流' },
]

const inputFootIcons = [
  { icon: 'icon-at', text: '智能体' },
  { icon: 'icon-standard', text: '工作流' },
  { icon: 'icon-add', text: '附件' },
]

// 格式化内容（后端已处理格式化，这里只做简单处理）
function formatContent(content: string): string {
  if (!content) return ''
  return content
}

// 新建对话
function newConversation() {
  startPage.value = true
  messages.value = []
}

// 提交消息
async function onSubmit(evt: string) {
  if (!evt || !evt.trim()) return
  
  inputValue.value = ''
  startPage.value = false
  
  // 处理特殊命令
  if (evt === '创建一个工作流' || evt === '创建工作流') {
    activeMenu.value = 'workflow'
    return
  }
  
  // 用户发送消息
  messages.value.push({ from: 'user', content: evt })
  
  // 添加加载状态的模型消息
  messages.value.push({ from: 'model', content: '', loading: true })
  
  try {
    // 根据当前菜单配置选择 API
    const menuConfig = currentMenuConfig.value
    let apiUrl = '/api/chat'
    let requestBody: Record<string, any> = { message: evt }
    
    if (menuConfig) {
      const apiType = menuConfig.apiType
      if (apiType === 'workflow' && menuConfig.workflowName) {
        // 使用工作流 API
        apiUrl = menuConfig.apiUrl || 'http://localhost:8000/api/workflow/run'
        requestBody = { workflow_name: menuConfig.workflowName, input: evt }
      } else if (apiType === 'policy-qa') {
        // 制度问答 API
        apiUrl = menuConfig.apiUrl || 'http://localhost:8000/api/policy-qa/sync'
        requestBody = { question: evt }
      } else if (apiType === 'ocr') {
        // OCR 识别 API
        apiUrl = menuConfig.apiUrl || 'http://localhost:8000/api/ocr/recognize'
        requestBody = { file_path: evt, dpi: 144, prompt_mode: 'prompt_layout_all_en' }
      } else if (apiType === 'skill-creator') {
        // 技能创建 API
        apiUrl = menuConfig.apiUrl || 'http://localhost:8000/api/skill-creator/chat'
        requestBody = { question: evt }
      } else if (apiType === 'chat') {
        // 通用对话 API
        apiUrl = menuConfig.apiUrl || '/api/chat'
        requestBody = { message: evt }
      }
    }
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
    
    if (response.ok) {
      const data = await response.json()
      let content = ''
      
      const apiType = menuConfig?.apiType
      if (apiType === 'policy-qa') {
        // 制度问答 API 返回 answer 字段
        let answer = data.answer || '抱歉，未能找到相关制度信息。'
        // 如果 answer 是 JSON 字符串，尝试解析并提取 text 字段
        try {
          if (typeof answer === 'string' && answer.startsWith('[')) {
            const parsed = JSON.parse(answer)
            if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].text) {
              answer = parsed[0].text
            }
          }
        } catch {
          // 解析失败，使用原始内容
        }
        content = answer
      } else if (apiType === 'ocr') {
        // OCR 识别 API 返回 text 字段
        content = data.text || data.answer || 'OCR 识别完成'
      } else if (apiType === 'skill-creator') {
        // 技能创建 API 返回 answer 字段
        content = data.answer || '技能创建完成'
      } else if (apiType === 'workflow') {
        // 工作流 API 返回可能是 JSON 数组
        let response = data
        try {
          // 如果是数组，提取第一个元素的 text 字段
          if (Array.isArray(response) && response.length > 0 && response[0].text) {
            content = response[0].text
          } else if (typeof response === 'string' && response.startsWith('[')) {
            // 如果是 JSON 字符串，尝试解析
            const parsed = JSON.parse(response)
            if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].text) {
              content = parsed[0].text
            } else {
              content = response
            }
          } else if (response.response) {
            content = response.response
          } else {
            content = JSON.stringify(response)
          }
        } catch {
          content = typeof response === 'string' ? response : JSON.stringify(response)
        }
        content = content || '处理完成'
      } else {
        content = data.response || data.answer || '处理完成'
      }
      
      messages.value[messages.value.length - 1] = {
        from: 'model',
        content,
        loading: false,
      }
    } else {
      messages.value[messages.value.length - 1] = {
        from: 'model',
        content: `收到您的消息: "${evt}"\n\n目前系统正在开发中，请切换到工作流模式进行智能体编排。`,
        loading: false,
      }
    }
  } catch {
    messages.value[messages.value.length - 1] = {
      from: 'model',
      content: `收到您的消息: "${evt}"\n\n提示：您可以点击右上角切换到"工作流模式"进行智能体编排。`,
      loading: false,
    }
  }
}

</script>

<template>
  <!-- 登录对话框 -->
  <LoginDialog v-if="!isLoggedIn" @login-success="handleLoginSuccess" />
  
  <div v-else class="h-screen w-screen flex">
    <!-- 左侧菜单 -->
    <LeftMenu :activeMenu="activeMenu" @select="handleMenuSelect" @menuLoaded="handleMenuLoaded" @logout="handleLogout" />
    
    <!-- 右侧主内容区 -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- 流程查询模式 -->
      <WorkflowListDialog v-if="isWorkflowListMode" />
      
      <!-- 代码助手模式 -->
      <CodeAssistantView v-else-if="isCodeAssistantMode" class="flex-1" />
      
      <!-- 对话模式 -->
      <template v-else-if="!isWorkflowMode">
        <!-- 开始页面 -->
        <McLayoutContent 
          v-if="startPage" 
          style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px"
        >
          <McIntroduction
            logoImg="https://matechat.gitcode.com/logo2x.svg"
            :title="currentAgent.name"
            :subTitle="'Hi，欢迎使用' + currentAgent.name"
            :description="currentAgent.description"
          />
          <McPrompt
            :list="introPrompt.list"
            :direction="introPrompt.direction"
            class="intro-prompt"
            @itemClick="onSubmit($event.label)"
          />
        </McLayoutContent>

        <!-- 对话内容 -->
        <McLayoutContent class="content-container" v-else>
          <div class="messages-wrapper">
            <template v-for="(msg, idx) in messages" :key="idx">
              <McBubble
                v-if="msg.from === 'user'"
                :content="msg.content"
                align="right"
                :avatarConfig="{ imgSrc: 'https://matechat.gitcode.com/png/demo/userAvatar.svg' }"
              />
              <div v-else class="model-message">
                <div class="model-avatar">
                  <img src="https://matechat.gitcode.com/logo.svg" alt="AI" />
                </div>
                <div class="model-content">
                  <McMarkdownCard v-if="!msg.loading" :content="formatContent(msg.content)" />
                  <div v-else class="loading-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </McLayoutContent>

        <!-- 快捷操作 -->
        <div class="shortcut-container">
          <div class="shortcut-wrapper">
            <McPrompt
              v-if="!startPage"
              :list="simplePrompt"
              direction="horizontal"
              style="flex: 1"
              @itemClick="onSubmit($event.label)"
            />
            <Button
              icon="add"
              shape="circle"
              title="新建对话"
              size="md"
              @click="newConversation"
            />
          </div>
        </div>

        <!-- 输入区域 -->
        <McLayoutSender class="sender-container">
          <div class="sender-wrapper">
            <McInput
              :value="inputValue"
              :maxLength="2000"
              @change="(e: string) => (inputValue = e)"
              @submit="onSubmit"
            >
            <template #extra>
              <div class="input-foot-wrapper">
                <div class="input-foot-left">
                  <span v-for="(item, index) in inputFootIcons" :key="index" class="cursor-pointer hover:text-blue-500">
                    <i :class="item.icon"></i>
                    {{ item.text }}
                  </span>
                  <span class="input-foot-dividing-line"></span>
                  <span class="input-foot-maxlength">{{ inputValue.length }}/2000</span>
                </div>
                <div class="input-foot-right">
                  <Button icon="op-clearup" shape="round" :disabled="!inputValue" @click="inputValue = ''">
                    <span class="demo-button-content">清空</span>
                  </Button>
                </div>
              </div>
            </template>
            </McInput>
          </div>
        </McLayoutSender>
      </template>

      <!-- 工作流编排模式 -->
      <template v-else>
        <div class="flex-1 flex flex-col overflow-hidden bg-gray-100">
          <!-- 工具栏 -->
          <Toolbar />
          
          <!-- 主内容区 -->
          <div class="flex-1 flex overflow-hidden">
            <!-- 左侧智能体面板 -->
            <Sidebar />
            
            <!-- 中间画布 -->
            <div class="flex-1 relative">
              <FlowCanvas @node-click="showConfigPanel = true" />
            </div>
            
            <!-- 右侧配置面板 -->
            <NodeConfigPanel 
              v-if="showConfigPanel" 
              @close="showConfigPanel = false" 
            />
          </div>
        </div>
      </template>
    </div>

    <!-- 制度问答浮动按钮 -->
    <button
      @click="showPolicyQA = true"
      class="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center z-40 group"
      title="制度问答"
    >
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span class="absolute right-16 bg-gray-800 text-white text-sm px-3 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
        制度问答
      </span>
    </button>

    <!-- 制度问答对话框 -->
    <PolicyQADialog :visible="showPolicyQA" @close="showPolicyQA = false" />
  </div>
</template>

<style>
.content-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: auto;
  padding: 16px 0;
}

.messages-wrapper {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-sizing: border-box;
}

/* 用户消息靠右对齐 */
.messages-wrapper :deep(.mc-bubble[align="right"]) {
  justify-content: flex-end;
}

/* AI 消息靠左对齐 */
.messages-wrapper .model-bubble {
  justify-content: flex-start;
}

/* 消息气泡宽度控制 */
.messages-wrapper :deep(.mc-bubble-content-container) {
  max-width: 85%;
}

.shortcut-container {
  padding: 8px 0;
}

.shortcut-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sender-container {
  padding: 16px 0;
}

.sender-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.input-foot-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  height: 100%;
  margin-right: 8px;
}

.input-foot-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-foot-left span {
  font-size: 14px;
  line-height: 18px;
  color: #252b3a;
}

.input-foot-dividing-line {
  width: 1px;
  height: 14px;
  background-color: #d7d8da;
}

.input-foot-maxlength {
  font-size: 14px;
  color: #71757f;
}

.input-foot-right {
  display: flex;
  gap: 8px;
}

.demo-button-content {
  font-size: 14px;
}

.intro-prompt {
  max-width: 800px;
}

/* 确保消息内容换行正确显示 */
.model-bubble :deep(.mc-bubble-content),
.model-bubble :deep(.mc-bubble-content.filled) {
  white-space: pre-wrap !important;
  word-break: break-word !important;
  line-height: 1.8 !important;
}

/* 全局样式备用 */
.mc-bubble-content,
.mc-bubble-content.filled {
  white-space: pre-wrap !important;
  word-break: break-word !important;
  line-height: 1.8 !important;
}

/* 模型消息样式 */
.model-message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.model-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.model-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.model-content {
  flex: 1;
  max-width: calc(100% - 48px);
  background: #f5f7fa;
  border-radius: 12px;
  padding: 16px;
  overflow: hidden;
}

.model-content :deep(.mc-markdown-card) {
  background: transparent !important;
  padding: 0 !important;
}

.model-content :deep(pre) {
  background: #1e1e1e !important;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.model-content :deep(code) {
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
}

.model-content :deep(p) {
  margin-bottom: 12px;
  line-height: 1.7;
}

.model-content :deep(h1),
.model-content :deep(h2),
.model-content :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
}

/* 加载动画 */
.loading-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.loading-indicator .dot {
  width: 8px;
  height: 8px;
  background: #999;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-indicator .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-indicator .dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>
