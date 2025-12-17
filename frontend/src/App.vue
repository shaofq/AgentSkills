<script setup lang="ts">
import { ref, computed } from 'vue'
import { Button } from 'vue-devui/button'
import 'vue-devui/button/style.css'
import FlowCanvas from './components/FlowCanvas.vue'
import Sidebar from './components/Sidebar.vue'
import NodeConfigPanel from './components/NodeConfigPanel.vue'
import Toolbar from './components/Toolbar.vue'
import LeftMenu from './components/LeftMenu.vue'
import PolicyQADialog from './components/PolicyQADialog.vue'

// 当前选中的菜单
const activeMenu = ref('chat')
const showConfigPanel = ref(false)
const showPolicyQA = ref(false)

// 是否显示工作流模式
const isWorkflowMode = computed(() => activeMenu.value === 'workflow')

// 当前智能体信息
const currentAgent = computed(() => {
  const agents: Record<string, { name: string; description: string[]; model: string }> = {
    'chat': { 
      name: '智能对话', 
      description: ['通用对话助手，可以回答各种问题。', '支持多轮对话和上下文理解。'], 
      model: 'deepseek-ai/DeepSeek-R1' 
    },
    'code-agent': { 
      name: '代码助手', 
      description: ['专业的代码生成和调试助手。', '支持 amis、React、Vue 等多种框架。'], 
      model: 'qwen3-max' 
    },
    'pptx-agent': { 
      name: 'PPT助手', 
      description: ['演示文稿制作助手。', '快速创建专业的 PowerPoint 演示文稿。'], 
      model: 'qwen3-max' 
    },
    'data-agent': { 
      name: '数据分析', 
      description: ['数据分析和可视化助手。', '支持 SQL 查询、图表生成、报表分析。'], 
      model: 'qwen3-max' 
    },
    'policy-qa': { 
      name: '制度问答', 
      description: ['公司制度问答助手。', '解答员工手册、财务制度、电脑补贴等问题。'], 
      model: 'qwen3-max' 
    },
  }
  return agents[activeMenu.value] || agents['chat']
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
    // 根据当前菜单选择不同的 API
    let apiUrl = '/api/chat'
    let requestBody: Record<string, string> = { message: evt }
    
    if (activeMenu.value === 'policy-qa') {
      // 制度问答使用专门的 API
      apiUrl = 'http://localhost:8000/api/policy-qa/sync'
      requestBody = { question: evt }
    }
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
    
    if (response.ok) {
      const data = await response.json()
      let content = ''
      
      if (activeMenu.value === 'policy-qa') {
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
      } else {
        content = data.response || '处理完成'
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
  <div class="h-screen w-screen flex">
    <!-- 左侧菜单 -->
    <LeftMenu :activeMenu="activeMenu" @select="handleMenuSelect" />
    
    <!-- 右侧主内容区 -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- 对话模式 -->
      <template v-if="!isWorkflowMode">
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
              <McBubble
                v-else
                :content="formatContent(msg.content)"
                :avatarConfig="{ imgSrc: 'https://matechat.gitcode.com/logo.svg' }"
                :loading="msg.loading"
                class="model-bubble"
              />
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
</style>
