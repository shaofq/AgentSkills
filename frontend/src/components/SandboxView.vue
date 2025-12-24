<template>
  <div class="sandbox-view">
    <!-- 头部 -->
    <div class="sandbox-header">
      <div class="header-left">
        <span class="computer-icon">🖥️</span>
        <span class="title">AI 的电脑</span>
        <span :class="['status-tag', isConnected ? 'connected' : 'disconnected']">
          {{ isConnected ? '已连接' : '未连接' }}
        </span>
      </div>
      <div class="header-right">
        <div class="tab-group">
          <button 
            :class="['tab-btn', activeView === 'vnc' ? 'active' : '']" 
            @click="activeView = 'vnc'"
          >
            🖥️ 屏幕
          </button>
          <button 
            :class="['tab-btn', activeView === 'editor' ? 'active' : '']" 
            @click="activeView = 'editor'"
          >
            ✏️ 编辑器
          </button>
          <button 
            :class="['tab-btn', activeView === 'terminal' ? 'active' : '']" 
            @click="activeView = 'terminal'"
          >
            💻 终端
          </button>
          <button 
            :class="['tab-btn', activeView === 'files' ? 'active' : '']" 
            @click="activeView = 'files'"
          >
            📁 文件
          </button>
        </div>
        <button class="btn-small" @click="openInNewTab">↗ 新窗口</button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="sandbox-content">
      <!-- VNC 视图 -->
      <div v-if="activeView === 'vnc'" class="vnc-container">
        <iframe 
          v-if="isConnected && sandboxUrls.vnc"
          :src="sandboxUrls.vnc"
          class="vnc-iframe"
          frameborder="0"
          allow="clipboard-read; clipboard-write"
        />
        <div v-else class="placeholder">
          <span class="placeholder-icon">🖥️</span>
          <p>Sandbox 未连接</p>
          <button class="btn-primary" @click="checkConnection">连接</button>
        </div>
      </div>

      <!-- 编辑器视图 (VSCode) -->
      <div v-else-if="activeView === 'editor'" class="editor-container">
        <iframe 
          v-if="isConnected && sandboxUrls.vscode"
          :src="sandboxUrls.vscode"
          class="vscode-iframe"
          frameborder="0"
        />
        <div v-else class="placeholder">
          <span class="placeholder-icon">✏️</span>
          <p>编辑器未连接</p>
          <button class="btn-primary" @click="checkConnection">连接</button>
        </div>
      </div>

      <!-- 终端视图 -->
      <div v-else-if="activeView === 'terminal'" class="terminal-container">
        <div class="terminal-output" ref="terminalOutput">
          <div 
            v-for="(log, index) in terminalLogs" 
            :key="index"
            :class="['log-line', log.type]"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-content">{{ log.content }}</span>
          </div>
        </div>
        <div class="terminal-input">
          <span class="prompt">$</span>
          <input 
            v-model="commandInput"
            type="text"
            placeholder="输入命令..."
            @keyup.enter="executeCommand"
            :disabled="!isConnected"
            class="cmd-input"
          />
          <button 
            class="btn-primary" 
            @click="executeCommand"
            :disabled="!isConnected || !commandInput"
          >
            执行
          </button>
        </div>
      </div>

      <!-- 文件视图 -->
      <div v-else-if="activeView === 'files'" class="files-container">
        <div class="files-toolbar">
          <input 
            v-model="currentPath" 
            type="text"
            placeholder="/home/user"
            @keyup.enter="loadFiles"
            class="path-input"
          />
          <button class="btn-small" @click="loadFiles">🔄 刷新</button>
        </div>
        <div class="files-list">
          <div 
            v-for="file in fileList" 
            :key="file.name"
            class="file-item"
            @click="handleFileClick(file)"
          >
            <span>{{ file.isDirectory ? '📁' : '📄' }}</span>
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ file.size }}</span>
          </div>
          <div v-if="fileList.length === 0" class="empty-files">
            <p>暂无文件</p>
          </div>
        </div>
        <!-- 文件预览 -->
        <div v-if="previewContent" class="file-preview">
          <div class="preview-header">
            <span>{{ previewFileName }}</span>
            <button class="btn-small" @click="previewContent = ''">关闭</button>
          </div>
          <pre class="preview-content">{{ previewContent }}</pre>
        </div>
      </div>
    </div>

    <!-- 任务状态栏 -->
    <div class="sandbox-status">
      <div class="status-item">
        <span>⏱️</span>
        <span>{{ currentTask || '空闲' }}</span>
      </div>
      <div class="status-item" v-if="generatedFiles.length > 0">
        <span>📄</span>
        <span>{{ generatedFiles.length }} 个文件</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'

const API_BASE = ''

// 状态
const isConnected = ref(false)
const activeView = ref<'vnc' | 'editor' | 'terminal' | 'files'>('vnc')
const sandboxUrls = ref({
  vnc: '',
  vscode: '',
  docs: '',
  base: ''
})

// 终端
const terminalLogs = ref<Array<{time: string, type: string, content: string}>>([])
const commandInput = ref('')
const terminalOutput = ref<HTMLElement>()

// 文件
const currentPath = ref('/home/user')
const fileList = ref<Array<{name: string, isDirectory: boolean, size: string}>>([])
const previewContent = ref('')
const previewFileName = ref('')

// 任务
const currentTask = ref('')
const generatedFiles = ref<string[]>([])

// Props
const props = defineProps<{
  task?: string
  files?: string[]
}>()

// Watch props
watch(() => props.task, (val) => {
  if (val) currentTask.value = val
})

watch(() => props.files, (val) => {
  if (val) generatedFiles.value = val
})

// 检查连接
async function checkConnection() {
  try {
    const resp = await axios.get(`${API_BASE}/sandbox/status`)
    if (resp.data.available) {
      isConnected.value = true
      sandboxUrls.value = {
        vnc: resp.data.vnc_url,
        vscode: resp.data.vscode_url,
        docs: resp.data.docs_url,
        base: resp.data.base_url
      }
      console.log('Sandbox 已连接')
    } else {
      isConnected.value = false
      console.warn('Sandbox 服务未启动')
    }
  } catch (e) {
    isConnected.value = false
    console.error('无法连接到 Sandbox')
  }
}

// 执行命令
async function executeCommand() {
  if (!commandInput.value.trim()) return
  
  const cmd = commandInput.value
  commandInput.value = ''
  
  addLog('input', `$ ${cmd}`)
  
  try {
    const resp = await axios.post(`${API_BASE}/sandbox/shell/exec`, {
      command: cmd
    })
    addLog('output', resp.data.output || '(无输出)')
  } catch (e: any) {
    addLog('error', e.message || '执行失败')
  }
}

// 添加日志
function addLog(type: string, content: string) {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  terminalLogs.value.push({ time, type, content })
  
  nextTick(() => {
    if (terminalOutput.value) {
      terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight
    }
  })
}

// 加载文件列表
async function loadFiles() {
  try {
    const resp = await axios.post(`${API_BASE}/sandbox/file/list`, {
      directory: currentPath.value
    })
    fileList.value = (resp.data.files || []).map((f: string) => ({
      name: f,
      isDirectory: !f.includes('.'),
      size: '-'
    }))
  } catch (e) {
    console.error('加载文件列表失败', e)
  }
}

// 处理文件点击
function handleFileClick(file: {name: string, isDirectory: boolean}) {
  if (file.isDirectory) {
    currentPath.value = `${currentPath.value}/${file.name}`.replace('//', '/')
    loadFiles()
  } else {
    previewFile(`${currentPath.value}/${file.name}`)
  }
}

// 预览文件
async function previewFile(filePath: string) {
  try {
    const resp = await axios.post(`${API_BASE}/sandbox/file/read`, {
      file_path: filePath
    })
    previewContent.value = resp.data.content || ''
    previewFileName.value = filePath.split('/').pop() || filePath
  } catch (e) {
    console.error('读取文件失败', e)
  }
}

// 新窗口打开
function openInNewTab() {
  let url = ''
  switch (activeView.value) {
    case 'vnc':
      url = sandboxUrls.value.vnc
      break
    case 'editor':
      url = sandboxUrls.value.vscode
      break
    default:
      url = sandboxUrls.value.docs
  }
  if (url) {
    window.open(url, '_blank')
  }
}

// 初始化
onMounted(() => {
  checkConnection()
})

// 切换标签页
function switchTab(tab: 'vnc' | 'editor' | 'terminal' | 'files') {
  activeView.value = tab
}

// 暴露方法给父组件
defineExpose({
  addLog,
  checkConnection,
  loadFiles,
  switchTab
})
</script>

<style scoped>
.sandbox-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
}

.sandbox-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.computer-icon {
  font-size: 20px;
}

.title {
  color: #fff;
  font-weight: 500;
}

.status-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-tag.connected {
  background: #67c23a;
  color: #fff;
}

.status-tag.disconnected {
  background: #f56c6c;
  color: #fff;
}

.header-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.tab-group {
  display: flex;
  gap: 2px;
}

.tab-btn {
  padding: 6px 12px;
  border: none;
  background: #3c3c3c;
  color: #ccc;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.tab-btn:first-child {
  border-radius: 4px 0 0 4px;
}

.tab-btn:last-child {
  border-radius: 0 4px 4px 0;
}

.tab-btn:hover {
  background: #4c4c4c;
}

.tab-btn.active {
  background: #007acc;
  color: #fff;
}

.btn-small {
  padding: 6px 12px;
  border: none;
  background: #3c3c3c;
  color: #ccc;
  cursor: pointer;
  border-radius: 4px;
  font-size: 12px;
}

.btn-small:hover {
  background: #4c4c4c;
}

.btn-primary {
  padding: 8px 16px;
  border: none;
  background: #007acc;
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
}

.btn-primary:hover {
  background: #0587d4;
}

.btn-primary:disabled {
  background: #555;
  cursor: not-allowed;
}

.placeholder-icon {
  font-size: 48px;
}

.cmd-input, .path-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #3c3c3c;
  background: #1e1e1e;
  color: #fff;
  border-radius: 4px;
  font-family: monospace;
}

.cmd-input:focus, .path-input:focus {
  outline: none;
  border-color: #007acc;
}

.sandbox-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.vnc-container,
.editor-container {
  width: 100%;
  height: 100%;
}

.vnc-iframe,
.vscode-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
  gap: 16px;
}

.terminal-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.terminal-output {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.log-line {
  margin-bottom: 4px;
  line-height: 1.5;
}

.log-time {
  color: #666;
  margin-right: 8px;
}

.log-line.input .log-content {
  color: #4fc3f7;
}

.log-line.output .log-content {
  color: #fff;
  white-space: pre-wrap;
}

.log-line.error .log-content {
  color: #f44336;
}

.terminal-input {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #252526;
  border-top: 1px solid #3c3c3c;
  gap: 8px;
}

.prompt {
  color: #4caf50;
  font-family: monospace;
}

.files-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.files-toolbar {
  display: flex;
  padding: 8px 12px;
  gap: 8px;
  background: #252526;
  border-bottom: 1px solid #3c3c3c;
}

.files-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  gap: 8px;
  cursor: pointer;
  border-radius: 4px;
  color: #fff;
}

.file-item:hover {
  background: #2d2d2d;
}

.file-name {
  flex: 1;
}

.file-size {
  color: #888;
  font-size: 12px;
}

.empty-files {
  text-align: center;
  color: #888;
  padding: 40px;
}

.file-preview {
  border-top: 1px solid #3c3c3c;
  max-height: 40%;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #252526;
  color: #fff;
}

.preview-content {
  padding: 12px;
  margin: 0;
  overflow: auto;
  max-height: 200px;
  font-size: 12px;
  color: #d4d4d4;
  background: #1e1e1e;
}

.sandbox-status {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #007acc;
  color: #fff;
  font-size: 12px;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
