<template>
  <div class="crew-compare-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <span class="title">🛂 船员护照比对系统</span>
      </div>
      <div class="toolbar-right">
        <button class="tool-btn" @click="showFieldConfig = true" title="比对字段配置">
          ⚙️ 字段配置
        </button>
        <button class="tool-btn" @click="loadHistory" title="操作历史">
          📋 历史记录
        </button>
      </div>
    </div>

    <!-- 步骤指示器 -->
    <div class="steps-indicator">
      <div 
        v-for="(step, index) in steps" 
        :key="index"
        :class="['step', { active: currentStep === index, completed: currentStep > index }]"
      >
        <div class="step-number">{{ currentStep > index ? '✓' : index + 1 }}</div>
        <div class="step-label">{{ step.label }}</div>
      </div>
    </div>

    <!-- 步骤内容 -->
    <div class="step-content">
      <!-- 步骤1: 上传 Excel -->
      <div v-if="currentStep === 0" class="upload-section">
        <div class="upload-card">
          <div class="upload-icon">📋</div>
          <h3>上传船员名单</h3>
          <p>支持 .xlsx 或 .xls 格式的 Excel 文件</p>
          
          <input 
            type="file" 
            ref="excelInput"
            accept=".xlsx,.xls"
            @change="handleExcelSelect"
            style="display: none"
          />
          
          <button class="upload-btn" @click="$refs.excelInput.click()" :disabled="isLoading">
            <span v-if="!isLoading">选择文件</span>
            <span v-else>上传中...</span>
          </button>
          
          <div v-if="excelFile" class="file-info">
            <span class="file-name">📄 {{ excelFile.name }}</span>
            <span class="file-size">{{ formatFileSize(excelFile.size) }}</span>
          </div>
        </div>

        <!-- Excel 预览 -->
        <div v-if="crewList.length > 0" class="preview-section">
          <div class="preview-header">
            <h4>船员名单预览 ({{ crewList.length }} 人)</h4>
            <button class="config-btn" @click="openColumnMapping" title="配置列映射">
              🔗 列映射配置
            </button>
          </div>
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>序号</th>
                  <th>姓名</th>
                  <th>国籍</th>
                  <th>出生日期</th>
                  <th>证件号码</th>
                  <th>职务</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="crew in crewList.slice(0, 10)" :key="crew.index">
                  <td>{{ crew.index }}</td>
                  <td>{{ crew.name }}</td>
                  <td>{{ crew.nationality }}</td>
                  <td>{{ crew.date_of_birth }}</td>
                  <td>{{ crew.passport_no }}</td>
                  <td>{{ crew.rank }}</td>
                </tr>
              </tbody>
            </table>
            <p v-if="crewList.length > 10" class="more-hint">
              还有 {{ crewList.length - 10 }} 条记录...
            </p>
          </div>
          
          <button class="next-btn" @click="currentStep = 1">
            下一步：上传护照
          </button>
        </div>
      </div>

      <!-- 步骤2: 上传护照图片 -->
      <div v-if="currentStep === 1" class="upload-section">
        <div class="upload-card passport-upload">
          <div class="upload-icon">🛂</div>
          <h3>上传护照图片</h3>
          <p>支持批量上传 JPG、PNG 格式图片</p>
          
          <input 
            type="file" 
            ref="passportInput"
            accept=".jpg,.jpeg,.png,.bmp,.webp"
            multiple
            @change="handlePassportSelect"
            style="display: none"
          />
          
          <button class="upload-btn" @click="$refs.passportInput.click()" :disabled="isLoading">
            选择图片
          </button>
        </div>

        <!-- 护照图片列表 -->
        <div v-if="passportFiles.length > 0" class="passport-list">
          <div class="list-header">
            <h4>已上传 {{ passportFiles.length }} 张护照</h4>
            <button 
              class="recognize-all-btn" 
              @click="recognizeAllPassports"
              :disabled="isRecognizing"
            >
              {{ isRecognizing ? `识别中 (${recognizedCount}/${passportFiles.length})...` : '开始识别全部' }}
            </button>
          </div>
          
          <div class="passport-grid">
            <div 
              v-for="(passport, index) in passportFiles" 
              :key="index"
              :class="['passport-card', { recognized: passport.recognized, selected: selectedPassport === index }]"
              @click="selectPassport(index)"
            >
              <img :src="passport.preview" class="passport-thumb" />
              <div class="passport-info">
                <span class="filename">{{ passport.file.name }}</span>
                <span v-if="passport.recognized" class="recognized-name">
                  {{ passport.result?.full_name || '识别完成' }}
                </span>
                <span v-else-if="passport.recognizing" class="recognizing">
                  识别中...
                </span>
              </div>
              <div v-if="passport.recognized" class="status-badge success">✓</div>
            </div>
          </div>
        </div>

        <!-- 选中的护照详情 -->
        <div v-if="selectedPassport !== null && passportFiles[selectedPassport]?.recognized" class="passport-detail">
          <div class="detail-header">
            <h4>护照识别结果</h4>
            <div class="detail-actions">
              <button 
                class="action-btn edit-btn" 
                @click="openPassportEdit(selectedPassport)"
                title="编辑识别结果"
              >
                ✏️ 编辑
              </button>
              <button 
                class="action-btn retry-btn" 
                @click="reRecognizePassport(selectedPassport)"
                :disabled="passportFiles[selectedPassport].recognizing"
                title="重新识别"
              >
                🔄 重识别
              </button>
            </div>
          </div>
          <div v-if="passportFiles[selectedPassport].result?.manually_edited" class="edit-badge">
            ✏️ 已手动编辑
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <label>姓名</label>
              <span>{{ passportFiles[selectedPassport].result?.full_name }}</span>
            </div>
            <div class="detail-item">
              <label>护照号</label>
              <span>{{ passportFiles[selectedPassport].result?.passport_no }}</span>
            </div>
            <div class="detail-item">
              <label>国籍</label>
              <span>{{ passportFiles[selectedPassport].result?.nationality }}</span>
            </div>
            <div class="detail-item">
              <label>出生日期</label>
              <span>{{ passportFiles[selectedPassport].result?.date_of_birth }}</span>
            </div>
            <div class="detail-item">
              <label>性别</label>
              <span>{{ passportFiles[selectedPassport].result?.sex }}</span>
            </div>
            <div class="detail-item">
              <label>有效期至</label>
              <span>{{ passportFiles[selectedPassport].result?.date_of_expiry }}</span>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <button class="back-btn" @click="currentStep = 0">上一步</button>
          <button 
            class="next-btn" 
            @click="startCompare"
            :disabled="recognizedCount === 0 || isComparing"
          >
            {{ isComparing ? '比对中...' : '开始比对' }}
          </button>
        </div>
      </div>

      <!-- 步骤3: 比对结果 -->
      <div v-if="currentStep === 2" class="results-section">
        <!-- 统计卡片 -->
        <div class="stats-cards">
          <div class="stat-card total">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">总人数</div>
          </div>
          <div class="stat-card matched">
            <div class="stat-value">{{ stats.matched }}</div>
            <div class="stat-label">完全一致</div>
          </div>
          <div class="stat-card mismatched">
            <div class="stat-value">{{ stats.mismatched }}</div>
            <div class="stat-label">有差异</div>
          </div>
          <div class="stat-card not-found">
            <div class="stat-value">{{ stats.not_found }}</div>
            <div class="stat-label">未找到护照</div>
          </div>
        </div>

        <!-- 筛选标签 -->
        <div class="filter-tabs">
          <button 
            :class="['filter-btn', { active: resultFilter === 'all' }]"
            @click="resultFilter = 'all'"
          >
            全部 ({{ stats.total }})
          </button>
          <button 
            :class="['filter-btn', { active: resultFilter === 'matched' }]"
            @click="resultFilter = 'matched'"
          >
            ✓ 一致 ({{ stats.matched }})
          </button>
          <button 
            :class="['filter-btn', { active: resultFilter === 'mismatched' }]"
            @click="resultFilter = 'mismatched'"
          >
            ⚠ 有差异 ({{ stats.mismatched }})
          </button>
          <button 
            :class="['filter-btn', { active: resultFilter === 'not_found' }]"
            @click="resultFilter = 'not_found'"
          >
            ✗ 未找到 ({{ stats.not_found }})
          </button>
        </div>

        <!-- 结果列表 -->
        <div class="results-list">
          <div 
            v-for="(result, index) in filteredResults" 
            :key="index"
            :class="['result-card', result.match_status]"
            @click="expandedResult = expandedResult === index ? null : index"
          >
            <div class="result-header">
              <div class="result-status">
                <span v-if="result.match_status === 'matched'" class="status-icon matched">✓</span>
                <span v-else-if="result.match_status === 'mismatched'" class="status-icon mismatched">⚠</span>
                <span v-else class="status-icon not-found">✗</span>
              </div>
              <div class="result-main">
                <div class="crew-name">{{ result.crew.name }}</div>
                <div class="crew-passport">{{ result.crew.passport_no }}</div>
              </div>
              <div class="result-summary">
                <span v-if="result.match_status === 'matched'">信息一致</span>
                <span v-else-if="result.match_status === 'mismatched'">
                  {{ result.differences.length }} 项差异
                </span>
                <span v-else>未找到对应护照</span>
              </div>
              <div class="expand-icon">{{ expandedResult === index ? '▼' : '▶' }}</div>
            </div>

            <!-- 展开详情 -->
            <div v-if="expandedResult === index" class="result-detail">
              <div class="compare-table">
                <div class="compare-header">
                  <div class="col-field">字段</div>
                  <div class="col-excel">Excel 数据</div>
                  <div class="col-passport">护照数据</div>
                  <div class="col-status">状态</div>
                </div>
                <div class="compare-row" v-for="field in compareFields" :key="field.excel_field">
                  <div class="col-field">{{ field.label }}</div>
                  <div class="col-excel">{{ result.crew[field.excel_field] || '-' }}</div>
                  <div class="col-passport">{{ result.passport?.[field.passport_field] || '-' }}</div>
                  <div :class="['col-status', getFieldStatus(result, field)]">
                    {{ getFieldStatusText(result, field) }}
                  </div>
                </div>
              </div>

              <!-- 差异详情 -->
              <div v-if="result.differences.length > 0" class="differences">
                <h5>差异详情：</h5>
                <div v-for="diff in result.differences" :key="diff.field" class="diff-item">
                  <span class="diff-field">{{ diff.field }}:</span>
                  <span class="diff-excel">{{ diff.excel_value }}</span>
                  <span class="diff-arrow">→</span>
                  <span class="diff-passport">{{ diff.passport_value }}</span>
                  <span :class="['diff-severity', diff.severity]">
                    {{ diff.severity === 'high' ? '严重' : diff.severity === 'medium' ? '中等' : '轻微' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="step-actions">
          <button class="back-btn" @click="currentStep = 1">返回修改</button>
          <button class="export-btn" @click="exportReport">
            📥 导出报告
          </button>
        </div>
      </div>
    </div>

    <!-- 字段配置弹窗 -->
    <div v-if="showFieldConfig" class="modal-overlay" @click.self="showFieldConfig = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>⚙️ 比对字段配置</h3>
          <button class="close-btn" @click="showFieldConfig = false">×</button>
        </div>
        <div class="modal-body">
          <p class="config-hint">选择需要进行比对的字段，未勾选的字段将不参与比对</p>
          <div class="field-list">
            <div v-for="(field, index) in compareFields" :key="index" class="field-item">
              <label class="field-checkbox">
                <input type="checkbox" v-model="field.enabled" />
                <span class="field-label">{{ field.label }}</span>
              </label>
              <div class="field-mapping">
                <span class="mapping-label">Excel:</span>
                <span class="mapping-value">{{ field.excel_field }}</span>
                <span class="mapping-arrow">→</span>
                <span class="mapping-label">护照:</span>
                <span class="mapping-value">{{ field.passport_field }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showFieldConfig = false">取消</button>
          <button class="save-btn" @click="saveCompareFields">保存配置</button>
        </div>
      </div>
    </div>

    <!-- 历史记录弹窗 -->
    <div v-if="showHistory" class="modal-overlay" @click.self="showHistory = false">
      <div class="modal-content history-modal">
        <div class="modal-header">
          <h3>📋 操作历史记录</h3>
          <button class="close-btn" @click="showHistory = false">×</button>
        </div>
        <div class="modal-body">
          <div v-if="historyList.length === 0" class="empty-history">
            暂无历史记录
          </div>
          <div v-else class="history-list">
            <div v-for="item in historyList" :key="item.id" class="history-item">
              <div class="history-time">{{ formatTime(item.timestamp) }}</div>
              <div class="history-action">
                <span class="action-badge" :class="item.action">
                  {{ getActionLabel(item.action) }}
                </span>
              </div>
              <div class="history-detail">{{ item.detail }}</div>
              <div class="history-session">会话: {{ item.session_id }}</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showHistory = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 列映射配置弹窗 -->
    <div v-if="showColumnMapping" class="modal-overlay" @click.self="showColumnMapping = false">
      <div class="modal-content column-mapping-modal">
        <div class="modal-header">
          <h3>🔗 Excel列映射配置</h3>
          <button class="close-btn" @click="showColumnMapping = false">×</button>
        </div>
        <div class="modal-body">
          <p class="config-hint">配置Excel列与系统字段的映射关系</p>
          <div class="mapping-list">
            <div v-for="(target, original) in columnMapping" :key="original" class="mapping-row">
              <div class="original-col" :title="original">
                {{ truncateText(original, 25) }}
              </div>
              <span class="mapping-arrow">→</span>
              <select v-model="columnMapping[original]" class="target-select">
                <option value="">不映射</option>
                <option value="name">姓名</option>
                <option value="passport_no">证件号码</option>
                <option value="nationality">国籍</option>
                <option value="date_of_birth">出生日期</option>
                <option value="sex">性别</option>
                <option value="place_of_birth">出生地点</option>
                <option value="rank">职务</option>
                <option value="embark_date">登船日期</option>
                <option value="embark_port">登船口岸</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showColumnMapping = false">取消</button>
          <button class="save-btn" @click="saveColumnMapping">应用映射</button>
        </div>
      </div>
    </div>

    <!-- 护照编辑弹窗 -->
    <div v-if="showPassportEdit" class="modal-overlay" @click.self="showPassportEdit = false">
      <div class="modal-content passport-edit-modal">
        <div class="modal-header">
          <h3>✏️ 编辑护照识别结果</h3>
          <button class="close-btn" @click="showPassportEdit = false">×</button>
        </div>
        <div class="modal-body">
          <div class="edit-form">
            <div class="form-row">
              <label>姓名</label>
              <input type="text" v-model="editingPassport.full_name" />
            </div>
            <div class="form-row">
              <label>护照号</label>
              <input type="text" v-model="editingPassport.passport_no" />
            </div>
            <div class="form-row">
              <label>国籍</label>
              <input type="text" v-model="editingPassport.nationality" />
            </div>
            <div class="form-row">
              <label>出生日期</label>
              <input type="text" v-model="editingPassport.date_of_birth" placeholder="YYYY-MM-DD" />
            </div>
            <div class="form-row">
              <label>性别</label>
              <select v-model="editingPassport.sex">
                <option value="M">男 (M)</option>
                <option value="F">女 (F)</option>
              </select>
            </div>
            <div class="form-row">
              <label>出生地点</label>
              <input type="text" v-model="editingPassport.place_of_birth" />
            </div>
            <div class="form-row">
              <label>有效期至</label>
              <input type="text" v-model="editingPassport.date_of_expiry" placeholder="YYYY-MM-DD" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showPassportEdit = false">取消</button>
          <button class="save-btn" @click="savePassportEdit">保存修改</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/crew-compare'

// 步骤定义
const steps = [
  { label: '上传名单' },
  { label: '上传护照' },
  { label: '比对结果' }
]
const currentStep = ref(0)

// 显示配置弹窗
const showFieldConfig = ref(false)
const showHistory = ref(false)
const showColumnMapping = ref(false)
const showPassportEdit = ref(false)

// 列映射配置
const columnMapping = ref({})
const originalColumns = ref([])

// 护照编辑
const editingPassport = ref({})
const editingPassportIndex = ref(null)

// 会话
const sessionId = ref('')

// Excel 相关
const excelFile = ref(null)
const crewList = ref([])

// 护照相关
const passportFiles = ref([])
const selectedPassport = ref(null)
const isRecognizing = ref(false)
const recognizedCount = computed(() => passportFiles.value.filter(p => p.recognized).length)

// 比对结果
const compareResults = ref([])
const stats = ref({ total: 0, matched: 0, mismatched: 0, not_found: 0 })
const resultFilter = ref('all')
const expandedResult = ref(null)
const isComparing = ref(false)

// 加载状态
const isLoading = ref(false)

// 比对字段定义（可配置）
const compareFields = ref([
  { excel_field: 'name', passport_field: 'full_name', label: '姓名', enabled: true },
  { excel_field: 'passport_no', passport_field: 'passport_no', label: '证件号码', enabled: true },
  { excel_field: 'nationality', passport_field: 'nationality', label: '国籍', enabled: true },
  { excel_field: 'date_of_birth', passport_field: 'date_of_birth', label: '出生日期', enabled: true },
  { excel_field: 'sex', passport_field: 'sex', label: '性别', enabled: true },
  { excel_field: 'place_of_birth', passport_field: 'place_of_birth', label: '出生地点', enabled: false },
])

// 历史记录
const historyList = ref([])

// 过滤后的结果
const filteredResults = computed(() => {
  if (resultFilter.value === 'all') return compareResults.value
  return compareResults.value.filter(r => r.match_status === resultFilter.value)
})

// 初始化会话
onMounted(async () => {
  await createSession()
})

// 创建会话
async function createSession() {
  try {
    const response = await axios.post(`${API_BASE}/session`)
    sessionId.value = response.data.session_id
    console.log('会话已创建:', sessionId.value)
    // 加载默认比对字段配置
    await loadCompareFields()
  } catch (error) {
    console.error('创建会话失败:', error)
    alert('初始化失败，请刷新页面重试')
  }
}

// 加载比对字段配置
async function loadCompareFields() {
  try {
    const response = await axios.get(`${API_BASE}/compare-fields/${sessionId.value}`)
    if (response.data.success) {
      compareFields.value = response.data.data
    }
  } catch (error) {
    console.error('加载比对字段配置失败:', error)
  }
}

// 保存比对字段配置
async function saveCompareFields() {
  try {
    await axios.put(`${API_BASE}/compare-fields/${sessionId.value}`, {
      fields: compareFields.value
    })
    showFieldConfig.value = false
  } catch (error) {
    console.error('保存比对字段配置失败:', error)
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 加载历史记录
async function loadHistory() {
  try {
    const response = await axios.get(`${API_BASE}/history?limit=50`)
    if (response.data.success) {
      historyList.value = response.data.data
    }
    showHistory.value = true
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 获取操作标签
function getActionLabel(action) {
  const labels = {
    'create_session': '创建会话',
    'upload_excel': '上传Excel',
    'upload_passports': '上传护照',
    'recognize_passport': '识别护照',
    're_recognize_passport': '重识别护照',
    'edit_passport': '编辑护照',
    'update_column_mapping': '更新列映射',
    'compare': '执行比对',
    'update_compare_fields': '更新配置',
    'export_report': '导出报告'
  }
  return labels[action] || action
}

// 截断文本
function truncateText(text, maxLen) {
  if (!text) return ''
  if (text.length <= maxLen) return text
  return text.substring(0, maxLen) + '...'
}

// ============= 列映射配置 =============

async function openColumnMapping() {
  try {
    const response = await axios.get(`${API_BASE}/column-mapping/${sessionId.value}`)
    if (response.data.success) {
      columnMapping.value = response.data.column_mapping || {}
      originalColumns.value = response.data.original_columns || []
    }
    showColumnMapping.value = true
  } catch (error) {
    console.error('加载列映射配置失败:', error)
    alert('加载失败: ' + (error.response?.data?.detail || error.message))
  }
}

async function saveColumnMapping() {
  try {
    const response = await axios.put(`${API_BASE}/column-mapping/${sessionId.value}`, {
      mapping: columnMapping.value
    })
    if (response.data.success && response.data.crew_list) {
      crewList.value = response.data.crew_list
    }
    showColumnMapping.value = false
    alert('列映射已更新')
  } catch (error) {
    console.error('保存列映射配置失败:', error)
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

// ============= 护照编辑 =============

function openPassportEdit(index) {
  const passport = passportFiles.value[index]
  if (!passport?.result) return
  
  editingPassportIndex.value = index
  editingPassport.value = { ...passport.result }
  showPassportEdit.value = true
}

async function savePassportEdit() {
  try {
    const passport = passportFiles.value[editingPassportIndex.value]
    const originalPassportNo = passport.result.passport_no
    
    const response = await axios.put(
      `${API_BASE}/passport/${sessionId.value}/${encodeURIComponent(originalPassportNo)}`,
      { updates: editingPassport.value }
    )
    
    if (response.data.success) {
      passport.result = response.data.passport
      showPassportEdit.value = false
    }
  } catch (error) {
    console.error('保存护照编辑失败:', error)
    alert('保存失败: ' + (error.response?.data?.detail || error.message))
  }
}

// ============= 单张重识别 =============

async function reRecognizePassport(index) {
  const passport = passportFiles.value[index]
  if (!passport) return
  
  passport.recognizing = true
  
  try {
    const response = await axios.post(
      `${API_BASE}/re-recognize/${sessionId.value}/${encodeURIComponent(passport.file.name)}`
    )
    
    if (response.data.success) {
      passport.result = response.data.result
      passport.recognized = true
    }
  } catch (error) {
    console.error('重新识别失败:', error)
    alert('重新识别失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    passport.recognizing = false
  }
}

// 处理 Excel 选择
async function handleExcelSelect(event) {
  const file = event.target.files[0]
  if (!file) return
  
  excelFile.value = file
  isLoading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post(
      `${API_BASE}/upload-excel/${sessionId.value}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    
    if (response.data.success) {
      crewList.value = response.data.data.crew_list
    }
  } catch (error) {
    console.error('上传 Excel 失败:', error)
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
    excelFile.value = null
  } finally {
    isLoading.value = false
  }
}

// 处理护照选择
async function handlePassportSelect(event) {
  const files = Array.from(event.target.files)
  if (files.length === 0) return
  
  // 创建预览
  for (const file of files) {
    const preview = URL.createObjectURL(file)
    passportFiles.value.push({
      file,
      preview,
      recognized: false,
      recognizing: false,
      result: null
    })
  }
  
  // 上传文件
  isLoading.value = true
  try {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    
    await axios.post(
      `${API_BASE}/upload-passports/${sessionId.value}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  } catch (error) {
    console.error('上传护照失败:', error)
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    isLoading.value = false
  }
}

// 识别所有护照
async function recognizeAllPassports() {
  isRecognizing.value = true
  
  for (let i = 0; i < passportFiles.value.length; i++) {
    const passport = passportFiles.value[i]
    if (passport.recognized) continue
    
    passport.recognizing = true
    
    try {
      const response = await axios.post(
        `${API_BASE}/recognize/${sessionId.value}/${passport.file.name}`
      )
      
      if (response.data.success) {
        passport.result = response.data.data
        passport.recognized = true
      }
    } catch (error) {
      console.error('识别失败:', passport.file.name, error)
    } finally {
      passport.recognizing = false
    }
  }
  
  isRecognizing.value = false
}

// 选择护照
function selectPassport(index) {
  selectedPassport.value = index
}

// 开始比对
async function startCompare() {
  isComparing.value = true
  
  try {
    const response = await axios.post(`${API_BASE}/compare/${sessionId.value}`)
    
    if (response.data.success) {
      compareResults.value = response.data.results
      stats.value = response.data.stats
      currentStep.value = 2
    }
  } catch (error) {
    console.error('比对失败:', error)
    alert('比对失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    isComparing.value = false
  }
}

// 获取字段状态
function getFieldStatus(result, field) {
  if (!result.passport) return 'no-data'
  
  const excelVal = String(result.crew[field.excel_field] || '').toUpperCase()
  const passportVal = String(result.passport[field.passport_field] || '').toUpperCase()
  
  if (!excelVal || !passportVal) return 'no-data'
  if (excelVal === passportVal) return 'match'
  return 'mismatch'
}

function getFieldStatusText(result, field) {
  const status = getFieldStatus(result, field)
  if (status === 'match') return '✓'
  if (status === 'mismatch') return '✗'
  return '-'
}

// 导出报告
async function exportReport() {
  try {
    const response = await axios.get(
      `${API_BASE}/export/${sessionId.value}`,
      { responseType: 'blob' }
    )
    
    // 创建下载链接
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `船员护照比对报告_${sessionId.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出失败:', error)
    alert('导出失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.crew-compare-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, #f8fafc);
  color: var(--text-primary, #1e293b);
  overflow: hidden;
}

/* 顶部工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: var(--bg-secondary, #fff);
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.toolbar-left .title {
  font-size: 18px;
  font-weight: 600;
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

.tool-btn {
  padding: 8px 16px;
  background: var(--bg-tertiary, #f1f5f9);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #e2e8f0;
}

/* 弹窗 */
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

.modal-content {
  background: var(--bg-secondary, #fff);
  border-radius: 12px;
  width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-content.history-modal {
  width: 600px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary, #64748b);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color, #e2e8f0);
}

.cancel-btn, .save-btn {
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background: var(--bg-tertiary, #f1f5f9);
  border: 1px solid var(--border-color, #e2e8f0);
}

.save-btn {
  background: #3b82f6;
  color: white;
  border: none;
}

/* 字段配置 */
.config-hint {
  margin-bottom: 16px;
  color: var(--text-secondary, #64748b);
  font-size: 13px;
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-tertiary, #f8fafc);
  border-radius: 8px;
}

.field-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.field-checkbox input {
  width: 18px;
  height: 18px;
}

.field-label {
  font-weight: 500;
}

.field-mapping {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #64748b);
}

.mapping-value {
  background: var(--bg-secondary, #fff);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
}

.mapping-arrow {
  color: var(--text-tertiary, #94a3b8);
}

/* 历史记录 */
.empty-history {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary, #64748b);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: grid;
  grid-template-columns: 100px 100px 1fr 80px;
  gap: 12px;
  padding: 12px;
  background: var(--bg-tertiary, #f8fafc);
  border-radius: 8px;
  align-items: center;
}

.history-time {
  font-size: 12px;
  color: var(--text-secondary, #64748b);
}

.action-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.action-badge.create_session { background: #dbeafe; color: #1d4ed8; }
.action-badge.upload_excel { background: #dcfce7; color: #16a34a; }
.action-badge.upload_passports { background: #fef3c7; color: #d97706; }
.action-badge.recognize_passport { background: #e0e7ff; color: #4338ca; }
.action-badge.compare { background: #f3e8ff; color: #7c3aed; }
.action-badge.update_compare_fields { background: #fce7f3; color: #be185d; }
.action-badge.export_report { background: #ccfbf1; color: #0d9488; }

.history-detail {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-session {
  font-size: 11px;
  color: var(--text-tertiary, #94a3b8);
  font-family: monospace;
}

/* 步骤指示器 */
.steps-indicator {
  display: flex;
  justify-content: center;
  gap: 60px;
  padding: 24px;
  background: var(--bg-secondary, #fff);
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
  transition: all 0.3s;
}

.step.active, .step.completed {
  opacity: 1;
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--border-color, #e2e8f0);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.step.active .step-number {
  background: #3b82f6;
  color: white;
}

.step.completed .step-number {
  background: #22c55e;
  color: white;
}

.step-label {
  font-size: 13px;
  font-weight: 500;
}

/* 步骤内容 */
.step-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

/* 上传区域 */
.upload-section {
  max-width: 1000px;
  margin: 0 auto;
}

.upload-card {
  background: var(--bg-secondary, #fff);
  border: 2px dashed var(--border-color, #e2e8f0);
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  transition: all 0.3s;
}

.upload-card:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-card h3 {
  font-size: 18px;
  margin-bottom: 8px;
}

.upload-card p {
  color: var(--text-secondary, #64748b);
  margin-bottom: 24px;
}

.upload-btn {
  padding: 12px 32px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover:not(:disabled) {
  background: #2563eb;
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-info {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 16px;
  color: var(--text-secondary, #64748b);
}

/* 预览区域 */
.preview-section {
  margin-top: 24px;
  background: var(--bg-secondary, #fff);
  border-radius: 12px;
  padding: 24px;
}

.preview-section h4 {
  margin-bottom: 16px;
  font-size: 16px;
}

.table-wrapper {
  overflow-x: auto;
  margin-bottom: 24px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.data-table th {
  background: var(--bg-tertiary, #f1f5f9);
  font-weight: 600;
}

.more-hint {
  text-align: center;
  color: var(--text-secondary, #64748b);
  font-size: 13px;
}

.next-btn {
  display: block;
  width: 80%;
  padding: 14px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.next-btn:hover:not(:disabled) {
  background: #2563eb;
}

.next-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 护照列表 */
.passport-list {
  margin-top: 24px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.recognize-all-btn {
  padding: 10px 20px;
  background: #22c55e;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.recognize-all-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.passport-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.passport-card {
  background: var(--bg-secondary, #fff);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
  position: relative;
}

.passport-card:hover {
  border-color: #3b82f6;
}

.passport-card.selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.passport-card.recognized {
  border-color: #22c55e;
}

.passport-thumb {
  width: 100%;
  height: 120px;
  object-fit: cover;
}

.passport-info {
  padding: 10px;
}

.passport-info .filename {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #64748b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.passport-info .recognized-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
  margin-top: 4px;
}

.passport-info .recognizing {
  display: block;
  font-size: 12px;
  color: #f59e0b;
  margin-top: 4px;
}

.status-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: white;
}

.status-badge.success {
  background: #22c55e;
}

/* 护照详情 */
.passport-detail {
  margin-top: 24px;
  background: var(--bg-secondary, #fff);
  border-radius: 12px;
  padding: 20px;
}

.passport-detail h4 {
  margin-bottom: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item label {
  font-size: 12px;
  color: var(--text-secondary, #64748b);
}

.detail-item span {
  font-weight: 500;
}

/* 步骤操作 */
.step-actions {
  display: flex;
  gap: 16px;
  margin-top: 24px;
}

.back-btn {
  padding: 12px 24px;
  background: var(--bg-secondary, #fff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

/* 结果区域 */
.results-section {
  max-width: 1200px;
  margin: 0 auto;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-secondary, #fff);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
}

.stat-card.total .stat-value { color: #3b82f6; }
.stat-card.matched .stat-value { color: #22c55e; }
.stat-card.mismatched .stat-value { color: #f59e0b; }
.stat-card.not-found .stat-value { color: #ef4444; }

/* 筛选标签 */
.filter-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-btn {
  padding: 8px 16px;
  background: var(--bg-secondary, #fff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.filter-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

/* 结果列表 */
.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-card {
  background: var(--bg-secondary, #fff);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  border-left: 4px solid transparent;
}

.result-card.matched { border-left-color: #22c55e; }
.result-card.mismatched { border-left-color: #f59e0b; }
.result-card.not_found { border-left-color: #ef4444; }

.result-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
}

.result-status {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.status-icon.matched { background: #dcfce7; color: #22c55e; }
.status-icon.mismatched { background: #fef3c7; color: #f59e0b; }
.status-icon.not-found { background: #fee2e2; color: #ef4444; }

.result-main {
  flex: 1;
}

.crew-name {
  font-weight: 600;
  font-size: 15px;
}

.crew-passport {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
}

.result-summary {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
}

.expand-icon {
  font-size: 12px;
  color: var(--text-tertiary, #94a3b8);
}

/* 展开详情 */
.result-detail {
  padding: 0 16px 16px;
  border-top: 1px solid var(--border-color, #e2e8f0);
}

.compare-table {
  margin-top: 16px;
}

.compare-header,
.compare-row {
  display: grid;
  grid-template-columns: 100px 1fr 1fr 60px;
  gap: 12px;
  padding: 10px 0;
}

.compare-header {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #64748b);
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.compare-row {
  font-size: 13px;
  border-bottom: 1px dashed var(--border-color, #e2e8f0);
}

.col-status.match { color: #22c55e; font-weight: 600; }
.col-status.mismatch { color: #ef4444; font-weight: 600; }
.col-status.no-data { color: var(--text-tertiary, #94a3b8); }

/* 差异详情 */
.differences {
  margin-top: 16px;
  padding: 12px;
  background: #fef3c7;
  border-radius: 8px;
}

.differences h5 {
  font-size: 13px;
  margin-bottom: 8px;
}

.diff-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 4px;
}

.diff-field {
  font-weight: 500;
}

.diff-excel {
  color: #dc2626;
  text-decoration: line-through;
}

.diff-arrow {
  color: var(--text-tertiary, #94a3b8);
}

.diff-passport {
  color: #22c55e;
  font-weight: 500;
}

.diff-severity {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}

.diff-severity.high { background: #fee2e2; color: #dc2626; }
.diff-severity.medium { background: #fef3c7; color: #d97706; }
.diff-severity.low { background: #dcfce7; color: #16a34a; }

/* 导出按钮 */
.export-btn {
  padding: 12px 24px;
  background: #22c55e;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  margin-left: auto;
}

.export-btn:hover {
  background: #16a34a;
}

/* 预览区头部 */
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-header h4 {
  margin: 0;
}

.config-btn {
  padding: 6px 12px;
  background: var(--bg-tertiary, #f1f5f9);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.config-btn:hover {
  background: #e2e8f0;
}

/* 护照详情头部 */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-header h4 {
  margin: 0;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  border: 1px solid var(--border-color, #e2e8f0);
}

.edit-btn {
  background: #fef3c7;
  color: #92400e;
}

.edit-btn:hover {
  background: #fde68a;
}

.retry-btn {
  background: #dbeafe;
  color: #1d4ed8;
}

.retry-btn:hover {
  background: #bfdbfe;
}

.retry-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.edit-badge {
  display: inline-block;
  padding: 4px 8px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 4px;
  font-size: 11px;
  margin-bottom: 12px;
}

/* 列映射弹窗 */
.column-mapping-modal {
  width: 600px;
}

.mapping-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.mapping-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg-tertiary, #f8fafc);
  border-radius: 6px;
}

.original-col {
  flex: 1;
  font-size: 13px;
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-secondary, #64748b);
}

.target-select {
  width: 140px;
  padding: 6px 10px;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 4px;
  font-size: 13px;
  background: white;
}

/* 护照编辑弹窗 */
.passport-edit-modal {
  width: 450px;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary, #64748b);
}

.form-row input,
.form-row select {
  padding: 10px 12px;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 6px;
  font-size: 14px;
}

.form-row input:focus,
.form-row select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
