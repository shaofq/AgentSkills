<template>
  <div class="vl-ocr-container">
    <!-- 顶部标签页 -->
    <div class="tab-header">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <i :class="tab.icon"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- 识别结果列表 -->
    <div v-if="activeTab === 'list'" class="tab-content">
      <div class="list-header">
        <h3>识别结果列表</h3>
        <div class="header-actions">
          <button class="clear-btn" @click="clearResults" title="清除所有缓存">
            <i class="pi pi-trash"></i>
            清除
          </button>
          <button class="refresh-btn" @click="fetchResults">
            <i class="pi pi-refresh"></i>
            刷新
          </button>
        </div>
      </div>
      
      <div class="result-list">
        <div 
          v-for="item in results" 
          :key="item.file_path"
          :class="['result-item', { 'verify-failed': item.verify_status === 'failed' }]"
          @click="viewResult(item)"
        >
          <div class="item-icon">
            <i :class="getFileIcon(item.file_path)"></i>
          </div>
          <div class="item-info">
            <div class="item-name">{{ getFileName(item.file_path) }}</div>
            <div class="item-path">{{ item.file_path }}</div>
            <div class="item-time">{{ formatTime(item.processed_at) }}</div>
          </div>
          <div class="item-actions">
            <button 
              v-if="item.status === 'completed' && !item.verify_status"
              class="verify-btn"
              @click.stop="verifyInvoice(item)"
              title="验证发票"
            >
              <i class="pi pi-shield"></i>
              <span>验证</span>
            </button>
            <div :class="['item-status', item.status]">
              {{ item.status === 'completed' ? '已完成' : '失败' }}
            </div>
            <div v-if="item.verify_status" :class="['verify-status', item.verify_status]">
              {{ item.verify_status === 'passed' ? '✓ 验证通过' : '✗ 验证失败' }}
            </div>
          </div>
        </div>
        
        <div v-if="results.length === 0" class="empty-list">
          <i class="pi pi-inbox"></i>
          <p>暂无识别结果</p>
        </div>
      </div>
    </div>

    <!-- 文件识别界面 -->
    <div v-if="activeTab === 'recognize'" class="tab-content recognize-view">
      <div class="recognize-panel">
        <!-- 左侧：PDF/图片预览 -->
        <div class="preview-panel">
          <div class="panel-header">
            <h4>文件预览</h4>
            <div class="file-input">
              <input 
                type="file" 
                ref="fileInput"
                accept=".pdf,.png,.jpg,.jpeg,.bmp,.tiff"
                @change="handleFileSelect"
                style="display: none"
              />
              <button class="upload-btn" @click="$refs.fileInput.click()">
                <i class="pi pi-upload"></i>
                选择文件
              </button>
              <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
            </div>
          </div>
          
          <div class="preview-container" ref="previewContainer">
            <template v-if="previewUrl">
              <!-- 图片包装层，用于定位标注 -->
              <div class="image-wrapper">
                <img 
                  v-if="isImage" 
                  :src="previewUrl" 
                  class="preview-image"
                  ref="previewImage"
                />
                <iframe 
                  v-else 
                  :src="previewUrl" 
                  class="preview-pdf"
                ></iframe>
                
                <!-- 定位标注层（与图片同尺寸） -->
                <div class="annotation-layer" v-if="currentResult && currentResult.blocks">
                  <div 
                    v-for="(block, index) in currentResult.blocks"
                    :key="index"
                    class="annotation-box"
                    :style="getBlockStyle(block)"
                    :class="{ 
                      active: selectedBlockId === block.id,
                      'has-error': isBlockError(block)
                    }"
                    @click="selectBlock(block)"
                    :title="getBlockError(block)?.message || ''"
                  >
                    <span class="block-id">{{ block.id }}</span>
                    <span v-if="isBlockError(block)" class="error-icon">!</span>
                  </div>
                </div>
              </div>
            </template>
            
            <div v-else class="preview-placeholder">
              <i class="pi pi-image"></i>
              <p>选择文件开始识别</p>
            </div>
          </div>
          
          <div class="preview-actions" v-if="selectedFile">
            <button 
              class="recognize-btn" 
              @click="recognizeFile"
              :disabled="isRecognizing"
            >
              <i :class="isRecognizing ? 'pi pi-spin pi-spinner' : 'pi pi-eye'"></i>
              {{ isRecognizing ? '识别中...' : '开始识别' }}
            </button>
          </div>
        </div>
        
        <!-- 右侧：识别结果 -->
        <div class="result-panel">
          <div class="panel-header">
            <h4>识别结果</h4>
            <button 
              v-if="currentResult" 
              class="copy-btn"
              @click="copyResult"
            >
              <i class="pi pi-copy"></i>
              复制
            </button>
          </div>
          
          <div class="result-content">
            <template v-if="currentResult">
              <!-- 文本块列表 -->
              <div class="blocks-section" v-if="currentResult.blocks && currentResult.blocks.length > 0">
                <h5>文本区域 ({{ currentResult.blocks.length }})</h5>
                <div class="blocks-list">
                  <div 
                    v-for="block in currentResult.blocks"
                    :key="block.id"
                    :class="['block-item', { active: selectedBlockId === block.id }]"
                    @click="selectBlock(block)"
                  >
                    <span class="block-id">{{ block.id }}</span>
                    <span class="block-type">{{ block.type || 'text' }}</span>
                    <p class="block-text">{{ block.text }}</p>
                  </div>
                </div>
              </div>
              
              <!-- 完整文本 -->
              <div class="full-text-section">
                <h5>完整文本</h5>
                <pre class="full-text">{{ currentResult.full_text }}</pre>
              </div>
            </template>
            
            <div v-else class="result-placeholder">
              <i class="pi pi-file-edit"></i>
              <p>识别结果将显示在这里</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 监控配置界面 -->
    <div v-if="activeTab === 'monitor'" class="tab-content">
      <div class="monitor-header">
        <h3>文件夹监控配置</h3>
        <div class="monitor-status">
          <span :class="['status-dot', monitorStatus.is_running ? 'running' : 'stopped']"></span>
          {{ monitorStatus.is_running ? '监控中' : '已停止' }}
        </div>
        <div class="monitor-actions">
          <button 
            v-if="!monitorStatus.is_running"
            class="start-btn"
            @click="startMonitor"
          >
            <i class="pi pi-play"></i>
            启动监控
          </button>
          <button 
            v-else
            class="stop-btn"
            @click="stopMonitor"
          >
            <i class="pi pi-stop"></i>
            停止监控
          </button>
        </div>
      </div>
      
      <!-- 添加目录 -->
      <div class="add-dir-section">
        <input 
          v-model="newDirPath"
          type="text"
          placeholder="输入要监控的文件夹路径"
          class="dir-input"
        />
        <input 
          v-model="newDirName"
          type="text"
          placeholder="目录名称（可选）"
          class="name-input"
        />
        <button class="add-btn" @click="addWatchDir">
          <i class="pi pi-plus"></i>
          添加
        </button>
      </div>
      
      <!-- 目录列表 -->
      <div class="dir-list">
        <div 
          v-for="dir in watchDirs" 
          :key="dir.path"
          class="dir-item"
        >
          <div class="dir-icon">
            <i class="pi pi-folder"></i>
          </div>
          <div class="dir-info">
            <div class="dir-name">{{ dir.name }}</div>
            <div class="dir-path">{{ dir.path }}</div>
          </div>
          <div :class="['dir-status', dir.status]">
            {{ dir.status === 'running' ? '监控中' : '已停止' }}
          </div>
          <button class="scan-btn" @click="scanDir(dir.path)" title="扫描现有文件">
            <i class="pi pi-search"></i>
          </button>
          <button class="remove-btn" @click="removeWatchDir(dir.path)">
            <i class="pi pi-times"></i>
          </button>
        </div>
        
        <div v-if="watchDirs.length === 0" class="empty-list">
          <i class="pi pi-folder-open"></i>
          <p>暂无监控目录</p>
        </div>
      </div>
      
      <!-- 扫描结果 -->
      <div v-if="scanResults.length > 0" class="scan-results">
        <h4>扫描到的文件 ({{ scanResults.length }})</h4>
        <div class="scan-list">
          <div 
            v-for="file in scanResults" 
            :key="file"
            class="scan-item"
          >
            <i :class="getFileIcon(file)"></i>
            <span>{{ file }}</span>
            <button class="process-btn" @click="processFile(file)">
              <i class="pi pi-eye"></i>
              识别
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

// 图片引用
const previewImage = ref(null)

const API_BASE = 'http://localhost:8000/api/vl-ocr'

// 标签页
const tabs = [
  { key: 'list', label: '识别列表', icon: 'pi pi-list' },
  { key: 'recognize', label: '文件识别', icon: 'pi pi-eye' },
  { key: 'monitor', label: '监控配置', icon: 'pi pi-cog' },
]
const activeTab = ref('list')

// 识别结果列表
const results = ref([])

// 文件识别
const selectedFile = ref(null)
const previewUrl = ref('')
const isImage = ref(false)
const isRecognizing = ref(false)
const currentResult = ref(null)
const selectedBlockId = ref(null)

// 监控配置
const monitorStatus = ref({ is_running: false })
const watchDirs = ref([])
const newDirPath = ref('')
const newDirName = ref('')
const scanResults = ref([])

// 计算属性
const getFileName = (path) => {
  return path.split('/').pop()
}

const getFileIcon = (path) => {
  const ext = path.split('.').pop().toLowerCase()
  if (ext === 'pdf') return 'pi pi-file-pdf'
  if (['png', 'jpg', 'jpeg', 'bmp', 'tiff'].includes(ext)) return 'pi pi-image'
  return 'pi pi-file'
}

const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

// 获取文本块样式（定位标注）
const getBlockStyle = (block) => {
  if (!block.bbox || block.bbox.length !== 4) return {}
  const [x1, y1, x2, y2] = block.bbox
  
  // 获取图片元素
  const img = previewImage.value
  if (!img || !img.complete) return {}
  
  // 获取图片原始尺寸和显示尺寸
  const naturalWidth = img.naturalWidth
  const naturalHeight = img.naturalHeight
  const displayWidth = img.offsetWidth
  const displayHeight = img.offsetHeight
  
  // 计算缩放比例
  const scaleX = displayWidth / naturalWidth
  const scaleY = displayHeight / naturalHeight
  
  // 判断坐标类型并转换
  let finalX1, finalY1, finalX2, finalY2
  
  if (x1 <= 1 && y1 <= 1 && x2 <= 1 && y2 <= 1) {
    // 比例值：转换为像素
    finalX1 = x1 * displayWidth
    finalY1 = y1 * displayHeight
    finalX2 = x2 * displayWidth
    finalY2 = y2 * displayHeight
  } else {
    // 像素值：按缩放比例调整
    finalX1 = x1 * scaleX
    finalY1 = y1 * scaleY
    finalX2 = x2 * scaleX
    finalY2 = y2 * scaleY
  }
  
  console.log(`Block ${block.id}: bbox=[${x1},${y1},${x2},${y2}] -> [${finalX1.toFixed(1)},${finalY1.toFixed(1)},${finalX2.toFixed(1)},${finalY2.toFixed(1)}]`)
  console.log(`  图片: ${naturalWidth}x${naturalHeight} -> ${displayWidth}x${displayHeight}, 缩放: ${scaleX.toFixed(3)}x${scaleY.toFixed(3)}`)
  
  return {
    left: `${finalX1}px`,
    top: `${finalY1}px`,
    width: `${finalX2 - finalX1}px`,
    height: `${finalY2 - finalY1}px`,
  }
}

// 选择文本块
const selectBlock = (block) => {
  selectedBlockId.value = block.id
}

// 文件选择
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  selectedFile.value = file
  currentResult.value = null
  selectedBlockId.value = null
  
  // 创建预览 URL
  previewUrl.value = URL.createObjectURL(file)
  isImage.value = !file.name.toLowerCase().endsWith('.pdf')
}

// 识别文件
const recognizeFile = async () => {
  if (!selectedFile.value || isRecognizing.value) return
  
  isRecognizing.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('dpi', '150')
    formData.append('return_positions', 'true')
    
    const response = await axios.post(`${API_BASE}/upload-and-recognize`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (response.data.success) {
      currentResult.value = response.data.data
      // 刷新结果列表
      fetchResults()
    }
  } catch (error) {
    console.error('识别失败:', error)
    alert('识别失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    isRecognizing.value = false
  }
}

// 复制结果
const copyResult = () => {
  if (!currentResult.value) return
  navigator.clipboard.writeText(currentResult.value.full_text)
  alert('已复制到剪贴板')
}

// 清除所有缓存结果
const clearResults = async () => {
  if (!confirm('确定要清除所有识别结果缓存吗？')) return
  
  try {
    const response = await axios.delete(`${API_BASE}/results`)
    if (response.data.success) {
      results.value = []
      currentResult.value = null
      alert(response.data.message)
    }
  } catch (error) {
    console.error('清除缓存失败:', error)
    alert('清除缓存失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 查看结果详情
const viewResult = (item) => {
  // 处理结果数据结构（可能是多页 PDF）
  let result = item.result
  if (result && result.pages && result.pages.length > 0) {
    // 多页 PDF：合并所有页面的 blocks
    const allBlocks = []
    result.pages.forEach((page, idx) => {
      if (page.blocks) {
        page.blocks.forEach(block => {
          allBlocks.push({
            ...block,
            id: `${idx + 1}-${block.id}`,
            page: idx + 1
          })
        })
      }
    })
    result = {
      ...result,
      blocks: allBlocks
    }
  }
  
  // 加载验证结果（如果有）
  if (item.verify_result) {
    result.verify_result = item.verify_result
  }
  
  currentResult.value = result
  activeTab.value = 'recognize'
  
  // 如果有文件路径，设置预览（PDF 会被转换为图片）
  if (item.file_path) {
    // 通过后端 API 获取文件预览（PDF 会转换为图片）
    previewUrl.value = `http://localhost:8000/api/vl-ocr/preview?path=${encodeURIComponent(item.file_path)}`
    // PDF 也会转换为图片，所以统一使用 img 标签显示
    isImage.value = true
  }
}

// 获取识别结果列表
const fetchResults = async () => {
  try {
    const response = await axios.get(`${API_BASE}/results`)
    if (response.data.success) {
      results.value = response.data.data
    }
  } catch (error) {
    console.error('获取结果列表失败:', error)
  }
}

// 验证发票
const verifyInvoice = async (item) => {
  try {
    const response = await axios.post(`${API_BASE}/verify/from-ocr?file_path=${encodeURIComponent(item.file_path)}`)
    if (response.data.success) {
      const verifyResult = response.data.data
      // 更新本地结果
      item.verify_status = verifyResult.passed ? 'passed' : 'failed'
      item.verify_result = verifyResult
      
      // 显示验证结果
      if (verifyResult.passed) {
        alert('✓ 发票验证通过')
      } else {
        const errors = verifyResult.errors.map(e => e.message).join('\n')
        alert(`✗ 发票验证失败:\n${errors}`)
      }
      
      // 刷新列表
      fetchResults()
    } else {
      alert('验证失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('验证发票失败:', error)
    alert('验证失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 获取验证结果中的错误字段
const verifyResult = ref(null)

// 判断 block 是否有错误
const isBlockError = (block) => {
  if (!currentResult.value?.verify_result) return false
  const errors = currentResult.value.verify_result.errors || []
  const fieldPositions = currentResult.value.verify_result.field_positions || {}
  
  // 检查是否是错误字段对应的 block
  for (const error of errors) {
    const blockId = fieldPositions[error.field]
    if (blockId && blockId === block.id) {
      return true
    }
  }
  return false
}

// 获取 block 的错误信息
const getBlockError = (block) => {
  if (!currentResult.value?.verify_result) return null
  const errors = currentResult.value.verify_result.errors || []
  const fieldPositions = currentResult.value.verify_result.field_positions || {}
  
  for (const error of errors) {
    const blockId = fieldPositions[error.field]
    if (blockId && blockId === block.id) {
      return error
    }
  }
  return null
}

// 获取监控状态
const fetchMonitorStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE}/monitor/status`)
    if (response.data.success) {
      monitorStatus.value = response.data.data
      watchDirs.value = response.data.data.watch_dirs || []
    }
  } catch (error) {
    console.error('获取监控状态失败:', error)
  }
}

// 启动监控
const startMonitor = async () => {
  try {
    const response = await axios.post(`${API_BASE}/monitor/start`)
    if (response.data.success) {
      fetchMonitorStatus()
    }
  } catch (error) {
    console.error('启动监控失败:', error)
    alert('启动监控失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 停止监控
const stopMonitor = async () => {
  try {
    const response = await axios.post(`${API_BASE}/monitor/stop`)
    if (response.data.success) {
      fetchMonitorStatus()
    }
  } catch (error) {
    console.error('停止监控失败:', error)
  }
}

// 添加监控目录
const addWatchDir = async () => {
  if (!newDirPath.value) return
  
  try {
    const response = await axios.post(`${API_BASE}/monitor/dirs`, {
      path: newDirPath.value,
      name: newDirName.value,
      auto_process: true
    })
    
    if (response.data.success) {
      newDirPath.value = ''
      newDirName.value = ''
      fetchMonitorStatus()
    } else {
      alert(response.data.error || '添加失败')
    }
  } catch (error) {
    console.error('添加目录失败:', error)
    alert('添加目录失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 移除监控目录
const removeWatchDir = async (path) => {
  if (!confirm('确定要移除此监控目录吗？')) return
  
  try {
    const response = await axios.delete(`${API_BASE}/monitor/dirs`, {
      params: { path }
    })
    
    if (response.data.success) {
      fetchMonitorStatus()
    }
  } catch (error) {
    console.error('移除目录失败:', error)
  }
}

// 扫描目录
const scanDir = async (path) => {
  try {
    const response = await axios.post(`${API_BASE}/monitor/scan`, { path })
    if (response.data.success) {
      scanResults.value = response.data.data.files
    }
  } catch (error) {
    console.error('扫描目录失败:', error)
  }
}

// 处理单个文件
const processFile = async (filePath) => {
  try {
    const response = await axios.post(`${API_BASE}/monitor/process`, {
      file_path: filePath
    })
    
    if (response.data.success) {
      currentResult.value = response.data.data
      activeTab.value = 'recognize'
      fetchResults()
    }
  } catch (error) {
    console.error('处理文件失败:', error)
    alert('处理失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 初始化
onMounted(() => {
  fetchResults()
  fetchMonitorStatus()
})
</script>

<style scoped>
.vl-ocr-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  color: var(--text-primary);
}

/* 标签页头部 */
.tab-header {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--bg-hover);
}

.tab-btn.active {
  background: var(--menu-item-active);
  color: white;
}

/* 标签页内容 */
.tab-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

/* 列表视图 */
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.list-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.refresh-btn,
.clear-btn {
  padding: 8px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.clear-btn:hover {
  background: #dc2626;
  color: white;
  border-color: #dc2626;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.result-item:hover {
  background: var(--bg-hover);
}

.item-icon {
  font-size: 24px;
  color: var(--text-tertiary);
}

.item-info {
  flex: 1;
}

.item-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.item-path {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 2px;
}

.item-time {
  font-size: 12px;
  color: var(--text-tertiary);
}

.item-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.item-status.completed {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.item-status.failed {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* 验证相关样式 */
.item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.verify-btn {
  padding: 6px 10px;
  background: #f59e0b;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.verify-btn:hover {
  background: #d97706;
}

.verify-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.verify-status.passed {
  background: rgba(34, 197, 94, 0.2);
  color: #16a34a;
}

.verify-status.failed {
  background: rgba(239, 68, 68, 0.2);
  color: #dc2626;
}

.result-item.verify-failed {
  border-left: 4px solid #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

/* 识别视图 */
.recognize-view {
  padding: 0 !important;
}

.recognize-panel {
  display: flex;
  height: 100%;
}

.preview-panel,
.result-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
}

.result-panel {
  border-right: none;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.panel-header h4 {
  font-size: 14px;
  font-weight: 600;
}

.file-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.upload-btn,
.copy-btn {
  padding: 6px 12px;
  background: var(--menu-item-active);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.file-name {
  font-size: 13px;
  color: var(--text-secondary);
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-container {
  flex: 1;
  overflow: auto;
  background: var(--bg-tertiary);
}

.image-wrapper {
  position: relative;
  display: inline-block;
}

.preview-image {
  display: block;
  max-width: 100%;
  height: auto;
}

.annotation-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.preview-pdf {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-placeholder,
.result-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.preview-placeholder i,
.result-placeholder i {
  font-size: 48px;
  margin-bottom: 16px;
}

/* 定位标注层 - 已移至 .image-wrapper 后 */

.annotation-box {
  position: absolute;
  border: 2px solid rgba(37, 99, 235, 0.6);
  background: rgba(37, 99, 235, 0.1);
  pointer-events: auto;
  cursor: pointer;
  transition: all 0.2s;
}

.annotation-box:hover,
.annotation-box.active {
  border-color: #2563eb;
  background: rgba(37, 99, 235, 0.2);
}

.annotation-box .block-id {
  position: absolute;
  top: -18px;
  left: -2px;
  background: #2563eb;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.annotation-box.has-error {
  border: 3px solid #ef4444;
  background: rgba(239, 68, 68, 0.2);
  animation: error-pulse 1.5s infinite;
}

.annotation-box.has-error .block-id {
  background: #ef4444;
}

.annotation-box .error-icon {
  position: absolute;
  top: -18px;
  right: -2px;
  background: #ef4444;
  color: white;
  font-size: 10px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 50%;
}

@keyframes error-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
}

.preview-actions {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.recognize-btn {
  width: 100%;
  padding: 10px;
  background: #2563eb;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}

.recognize-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 结果面板 */
.result-content {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.blocks-section,
.full-text-section {
  margin-bottom: 24px;
}

.blocks-section h5,
.full-text-section h5 {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.blocks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.block-item {
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
}

.block-item:hover,
.block-item.active {
  border-color: #2563eb;
}

.block-item .block-id {
  display: inline-block;
  background: #2563eb;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 8px;
}

.block-item .block-type {
  font-size: 11px;
  color: var(--text-tertiary);
}

.block-item .block-text {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}

.full-text {
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow: auto;
}

/* 监控配置 */
.monitor-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.monitor-header h3 {
  font-size: 18px;
  font-weight: 600;
}

.monitor-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg-secondary);
  border-radius: 20px;
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.running {
  background: #22c55e;
  box-shadow: 0 0 8px #22c55e;
}

.status-dot.stopped {
  background: #6b7280;
}

.monitor-actions {
  margin-left: auto;
}

.start-btn,
.stop-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.start-btn {
  background: #22c55e;
  color: white;
}

.stop-btn {
  background: #ef4444;
  color: white;
}

.add-dir-section {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.dir-input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 14px;
}

.name-input {
  width: 200px;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 14px;
}

.add-btn {
  padding: 10px 20px;
  background: #2563eb;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dir-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dir-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.dir-icon {
  font-size: 24px;
  color: #f59e0b;
}

.dir-info {
  flex: 1;
}

.dir-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.dir-path {
  font-size: 12px;
  color: var(--text-tertiary);
}

.dir-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
}

.dir-status.running {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.dir-status.stopped {
  background: rgba(107, 114, 128, 0.2);
  color: #6b7280;
}

.scan-btn,
.remove-btn {
  padding: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  color: var(--text-tertiary);
}

.scan-btn:hover {
  background: var(--bg-hover);
  color: #2563eb;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.scan-results {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.scan-results h4 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.scan-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow: auto;
}

.scan-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--bg-secondary);
  border-radius: 6px;
}

.scan-item i {
  color: var(--text-tertiary);
}

.scan-item span {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.process-btn {
  padding: 6px 12px;
  background: #2563eb;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

/* 空状态 */
.empty-list {
  text-align: center;
  padding: 48px;
  color: var(--text-tertiary);
}

.empty-list i {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>
