<template>
  <div class="flex flex-col h-full bg-slate-50">
    <!-- 顶部标题栏 -->
    <div class="flex justify-between items-center px-6 py-4 bg-gradient-to-r from-primary to-primary-700 text-white shadow-md">
      <h1 class="text-xl font-semibold">危险品智能识别系统</h1>
      <div class="flex items-center gap-6">
        <span class="flex items-center gap-2">
          <span class="text-white/70 text-sm">总文件:</span>
          <span class="font-semibold">{{ statistics.total_files }}</span>
        </span>
        <span class="flex items-center gap-2 px-3 py-1 bg-red-500/20 rounded-full">
          <span class="text-white/80 text-sm">危险品:</span>
          <span class="font-semibold text-red-200">{{ statistics.hazardous }}</span>
        </span>
        <span class="flex items-center gap-2 px-3 py-1 bg-green-500/20 rounded-full">
          <span class="text-white/80 text-sm">非危险品:</span>
          <span class="font-semibold text-green-200">{{ statistics.non_hazardous }}</span>
        </span>
      </div>
    </div>

    <!-- 三栏布局 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左栏：文件列表 -->
      <div class="w-80 flex flex-col bg-white border-r border-slate-200">
        <div class="p-3 space-y-2 border-b border-slate-100">
          <button 
            class="w-full py-2.5 px-4 bg-primary hover:bg-primary-600 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            @click="triggerUpload"
          >
            📤 上传新文件
          </button>
          <button 
            class="w-full py-2 px-4 text-primary hover:bg-primary/5 border border-dashed border-primary/50 rounded-lg transition-colors flex items-center justify-center gap-2 text-sm"
            @click="openLearningMode"
          >
            🧠 智能学习
          </button>
          <input 
            ref="fileInput" 
            type="file" 
            accept=".pdf" 
            class="hidden" 
            @change="handleFileUpload"
          />
        </div>
        
        <div class="p-3 border-b border-slate-100">
          <input 
            v-model="searchKeyword" 
            placeholder="搜索文件名..." 
            class="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors"
            @input="debounceSearch"
          />
        </div>
        
        <div class="flex border-b border-slate-100">
          <button 
            class="flex-1 py-2 text-xs font-medium transition-colors"
            :class="statusFilter === '' ? 'text-primary border-b-2 border-primary bg-primary/5' : 'text-slate-500 hover:text-slate-700'"
            @click="setStatusFilter('')"
          >全部</button>
          <button 
            class="flex-1 py-2 text-xs font-medium transition-colors"
            :class="statusFilter === 'pending' ? 'text-primary border-b-2 border-primary bg-primary/5' : 'text-slate-500 hover:text-slate-700'"
            @click="setStatusFilter('pending')"
          >待处理</button>
          <button 
            class="flex-1 py-2 text-xs font-medium transition-colors"
            :class="statusFilter === 'completed' ? 'text-primary border-b-2 border-primary bg-primary/5' : 'text-slate-500 hover:text-slate-700'"
            @click="setStatusFilter('completed')"
          >已分析</button>
          <button 
            class="flex-1 py-2 text-xs font-medium transition-colors"
            :class="statusFilter === 'confirmed' ? 'text-primary border-b-2 border-primary bg-primary/5' : 'text-slate-500 hover:text-slate-700'"
            @click="setStatusFilter('confirmed')"
          >已确认</button>
        </div>
        
        <div class="flex-1 overflow-auto">
          <div 
            v-for="file in fileList" 
            :key="file.id"
            class="p-3 border-b border-slate-100 cursor-pointer transition-colors"
            :class="{ 
              'bg-primary/5 border-l-4 border-l-primary': selectedFile?.id === file.id,
              'hover:bg-slate-50': selectedFile?.id !== file.id
            }"
            @click="selectFile(file)"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">📄</span>
              <div class="flex gap-1">
                <span 
                  class="px-2 py-0.5 text-xs font-medium rounded-full"
                  :class="{
                    'bg-slate-100 text-slate-600': file.status === 'pending',
                    'bg-blue-100 text-blue-600': file.status === 'completed',
                    'bg-green-100 text-green-600': file.status === 'confirmed'
                  }"
                >{{ getStatusLabel(file.status) }}</span>
                <span 
                  v-if="file.result" 
                  class="px-2 py-0.5 text-xs font-medium rounded-full"
                  :class="file.result === 'hazardous' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'"
                >{{ getResultLabel(file.result) }}</span>
              </div>
            </div>
            <div class="text-sm font-medium text-slate-800 truncate" :title="file.filename">{{ file.filename }}</div>
            <div class="flex gap-2 mt-1 text-xs text-slate-400">
              <span>{{ formatFileSize(file.file_size) }}</span>
              <span>{{ formatDate(file.created_at) }}</span>
            </div>
          </div>
          
          <div v-if="fileList.length === 0" class="flex flex-col items-center justify-center py-12 text-slate-400">
            <span class="text-3xl mb-2">📂</span>
            <span class="text-sm">暂无文件，请上传SDS文件</span>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="totalPages > 1" class="flex items-center justify-center gap-3 p-3 border-t border-slate-100">
          <button 
            class="px-3 py-1 text-sm text-slate-600 hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="currentPage <= 1" 
            @click="changePage(currentPage - 1)"
          >上一页</button>
          <span class="text-sm text-slate-500">{{ currentPage }} / {{ totalPages }}</span>
          <button 
            class="px-3 py-1 text-sm text-slate-600 hover:bg-slate-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="currentPage >= totalPages" 
            @click="changePage(currentPage + 1)"
          >下一页</button>
        </div>
      </div>

      <!-- 中栏：文件预览和操作 -->
      <div class="flex-1 flex flex-col bg-white">
        <template v-if="selectedFile">
          <div class="flex justify-between items-center px-4 py-3 border-b border-slate-200">
            <h2 class="text-base font-semibold text-slate-800 truncate">{{ selectedFile.filename }}</h2>
            <div class="flex gap-2">
              <button 
                v-if="selectedFile.status === 'pending'" 
                class="px-4 py-2 bg-primary hover:bg-primary-600 disabled:bg-slate-300 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                :disabled="analyzing"
                @click="analyzeFile"
              >
                <span v-if="analyzing" class="animate-spin">⏳</span>
                {{ analyzing ? '分析中...' : '开始分析' }}
              </button>
              <button 
                class="px-3 py-2 text-red-500 hover:bg-red-50 text-sm rounded-lg transition-colors"
                @click="deleteCurrentFile"
              >
                🗑️ 删除
              </button>
            </div>
          </div>
          
          <!-- PDF预览区 -->
          <div class="flex-1 bg-slate-100 relative">
            <iframe 
              v-if="pdfUrl"
              :src="pdfUrl" 
              class="w-full h-full border-0"
            ></iframe>
            <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-slate-400">
              <span class="text-5xl mb-4">📋</span>
              <p class="text-sm">PDF预览区域</p>
              <p v-if="selectedFile.status === 'pending'" class="text-xs mt-1">请点击"开始分析"进行识别</p>
            </div>
          </div>
          
          <!-- 审核操作区 -->
          <div v-if="selectedFile.status === 'completed'" class="p-4 border-t border-slate-200 bg-slate-50">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">判断结果是否正确？</h3>
            <div class="flex gap-3">
              <button 
                class="flex-1 py-2.5 bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                @click="confirmResult(true)"
              >
                ✓ 正确，确认归档
              </button>
              <button 
                class="flex-1 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                @click="showModifyDialog = true"
              >
                ✏️ 错误，我要修正
              </button>
            </div>
          </div>
        </template>
        
        <div v-else class="flex-1 flex flex-col items-center justify-center text-slate-400">
          <span class="text-6xl mb-4">📄</span>
          <p class="text-sm">请从左侧选择一个文件查看详情</p>
        </div>
      </div>

      <!-- 右栏：规则与结果 -->
      <div class="w-80 flex flex-col bg-white border-l border-slate-200 overflow-auto">
        <template v-if="selectedFile && selectedFile.status !== 'pending'">
          <!-- 判断结果 -->
          <div class="p-4 border-b border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">判断结果</h3>
            <div 
              class="flex items-center gap-3 p-4 rounded-xl"
              :class="selectedFile.result === 'hazardous' ? 'bg-red-50' : 'bg-green-50'"
            >
              <span class="text-3xl">
                {{ selectedFile.result === 'hazardous' ? '⚠️' : '✅' }}
              </span>
              <div>
                <span 
                  class="font-semibold"
                  :class="selectedFile.result === 'hazardous' ? 'text-red-700' : 'text-green-700'"
                >{{ getResultLabel(selectedFile.result) }}</span>
                <span v-if="selectedFile.confidence" class="block text-xs text-slate-500 mt-0.5">
                  {{ (Number(selectedFile.confidence) * 100).toFixed(0) }}% 置信度
                </span>
              </div>
            </div>
          </div>
          
          <!-- 命中的规则 -->
          <div v-if="selectedFile.matched_rules?.length" class="p-4 border-b border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">命中的规则</h3>
            <div class="space-y-2">
              <div 
                v-for="(rule, idx) in selectedFile.matched_rules" 
                :key="idx"
                class="flex items-center gap-2 p-2 bg-slate-50 rounded-lg text-sm"
              >
                <span class="text-slate-400">{{ Number(idx) + 1 }}.</span>
                <span class="flex-1 text-slate-700">{{ rule.name }}</span>
                <span 
                  class="px-2 py-0.5 text-xs rounded-full"
                  :class="rule.rule_type === 'builtin' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'"
                >{{ rule.rule_type === 'builtin' ? '内置' : '自定义' }}</span>
              </div>
            </div>
          </div>
          
          <!-- 提取的关键信息 -->
          <div v-if="selectedFile.extracted_info" class="p-4 border-b border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">提取的关键信息</h3>
            <div class="space-y-2">
              <div class="flex items-start gap-2 text-sm" v-if="selectedFile.extracted_info.product_name">
                <span class="w-16 text-slate-400 flex-shrink-0">产品名称</span>
                <span class="flex-1 text-slate-700">{{ selectedFile.extracted_info.product_name }}</span>
                <button class="text-xs text-primary hover:underline" @click="editField('product_name')">修正</button>
              </div>
              <div class="flex items-start gap-2 text-sm" v-if="selectedFile.extracted_info.cas_number">
                <span class="w-16 text-slate-400 flex-shrink-0">CAS号</span>
                <span class="flex-1 text-slate-700 font-mono">{{ selectedFile.extracted_info.cas_number }}</span>
                <button class="text-xs text-primary hover:underline" @click="editField('cas_number')">修正</button>
              </div>
              <div class="flex items-start gap-2 text-sm" v-if="selectedFile.extracted_info.hazard_class?.length">
                <span class="w-16 text-slate-400 flex-shrink-0">危险类别</span>
                <span class="flex-1 text-slate-700">{{ selectedFile.extracted_info.hazard_class.join(', ') }}</span>
                <button class="text-xs text-primary hover:underline" @click="editField('hazard_class')">修正</button>
              </div>
              <div class="flex items-start gap-2 text-sm" v-if="selectedFile.extracted_info.signal_word">
                <span class="w-16 text-slate-400 flex-shrink-0">信号词</span>
                <span 
                  class="px-2 py-0.5 rounded font-medium"
                  :class="selectedFile.extracted_info.signal_word === 'Danger' ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-600'"
                >{{ selectedFile.extracted_info.signal_word }}</span>
                <button class="text-xs text-primary hover:underline" @click="editField('signal_word')">修正</button>
              </div>
              <div class="flex items-start gap-2 text-sm" v-if="selectedFile.extracted_info.un_number">
                <span class="w-16 text-slate-400 flex-shrink-0">UN编号</span>
                <span class="px-2 py-0.5 bg-amber-100 text-amber-700 rounded font-mono">{{ selectedFile.extracted_info.un_number }}</span>
                <button class="text-xs text-primary hover:underline" @click="editField('un_number')">修正</button>
              </div>
              <div class="flex items-start gap-2 text-sm" v-if="selectedFile.extracted_info.proper_shipping_name">
                <span class="w-16 text-slate-400 flex-shrink-0">运输名称</span>
                <span class="flex-1 text-slate-700">{{ selectedFile.extracted_info.proper_shipping_name }}</span>
                <button class="text-xs text-primary hover:underline" @click="editField('proper_shipping_name')">修正</button>
              </div>
              <div class="flex items-start gap-2 text-sm" v-if="selectedFile.extracted_info.pictograms?.length">
                <span class="w-16 text-slate-400 flex-shrink-0">象形图</span>
                <span class="flex gap-1">
                  <span v-for="p in selectedFile.extracted_info.pictograms" :key="p" class="text-lg">{{ p }}</span>
                </span>
              </div>
            </div>
          </div>
          
          <!-- 建议 -->
          <div v-if="suggestions?.length" class="p-4 border-b border-slate-100">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">建议</h3>
            <ul class="space-y-1 text-sm text-slate-600">
              <li v-for="(s, idx) in suggestions" :key="idx" class="flex items-start gap-2">
                <span class="text-primary">•</span>
                {{ s }}
              </li>
            </ul>
          </div>
        </template>
        
        <!-- 规则管理入口 -->
        <div class="mt-auto p-4 border-t border-slate-100">
          <button 
            class="w-full py-2 px-4 text-sm text-slate-600 hover:bg-slate-50 border border-slate-200 rounded-lg transition-colors flex items-center justify-center gap-2"
            @click="showRuleDialog = true"
          >
            ⚙️ 管理规则库
          </button>
        </div>
      </div>
    </div>

    <!-- 修正对话框 -->
    <div v-if="showModifyDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModifyDialog = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 class="text-lg font-semibold text-slate-800 mb-4">修正信息</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">修正字段</label>
            <select v-model="modifyField" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
              <option value="product_name">产品名称</option>
              <option value="cas_number">CAS号</option>
              <option value="hazard_class">危险性类别</option>
              <option value="signal_word">信号词</option>
              <option value="un_number">UN编号</option>
              <option value="proper_shipping_name">运输名称</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">修正值</label>
            <input v-model="modifyValue" placeholder="输入正确的值" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">最终判断</label>
            <select v-model="modifyResult" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
              <option value="hazardous">是危险品</option>
              <option value="non_hazardous">非危险品</option>
            </select>
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="createRuleFromModify" class="accent-primary" />
            <span class="text-sm text-slate-700">根据此次修正创建新规则</span>
          </label>
          <div v-if="createRuleFromModify">
            <label class="block text-sm font-medium text-slate-700 mb-1">规则名称</label>
            <input v-model="newRuleName" placeholder="输入规则名称" class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button class="flex-1 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors" @click="showModifyDialog = false">取消</button>
          <button class="flex-1 py-2 bg-primary hover:bg-primary-600 text-white font-medium rounded-lg transition-colors" @click="submitModify">确认修正</button>
        </div>
      </div>
    </div>

    <!-- 规则管理对话框 -->
    <div v-if="showRuleDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showRuleDialog = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
        <div class="px-6 py-4 border-b border-slate-200">
          <h3 class="text-lg font-semibold text-slate-800">规则管理</h3>
        </div>
        
        <div class="flex border-b border-slate-200">
          <button 
            class="px-4 py-2 text-sm font-medium transition-colors"
            :class="ruleTab === 'all' ? 'text-primary border-b-2 border-primary' : 'text-slate-500 hover:text-slate-700'"
            @click="ruleTab = 'all'"
          >全部规则</button>
          <button 
            class="px-4 py-2 text-sm font-medium transition-colors"
            :class="ruleTab === 'builtin' ? 'text-primary border-b-2 border-primary' : 'text-slate-500 hover:text-slate-700'"
            @click="ruleTab = 'builtin'"
          >内置规则</button>
          <button 
            class="px-4 py-2 text-sm font-medium transition-colors"
            :class="ruleTab === 'custom' ? 'text-primary border-b-2 border-primary' : 'text-slate-500 hover:text-slate-700'"
            @click="ruleTab = 'custom'"
          >自定义规则</button>
        </div>
        
        <div class="flex-1 overflow-auto p-4">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-slate-500 border-b border-slate-200">
                <th class="pb-2 font-medium">规则名称</th>
                <th class="pb-2 font-medium">条件</th>
                <th class="pb-2 font-medium">结果</th>
                <th class="pb-2 font-medium">类型</th>
                <th class="pb-2 font-medium">状态</th>
                <th class="pb-2 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rule in filteredRules" :key="rule.id" class="border-b border-slate-100 hover:bg-slate-50">
                <td class="py-2 text-slate-700">{{ rule.name }}</td>
                <td class="py-2 text-slate-500 text-xs font-mono">
                  {{ rule.condition_field }} {{ rule.condition_operator }} '{{ rule.condition_value }}'
                </td>
                <td class="py-2">
                  <span 
                    class="px-2 py-0.5 text-xs rounded-full"
                    :class="rule.result === 'hazardous' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'"
                  >{{ rule.result === 'hazardous' ? '危险品' : '非危险品' }}</span>
                </td>
                <td class="py-2">
                  <span 
                    class="px-2 py-0.5 text-xs rounded-full"
                    :class="rule.rule_type === 'builtin' ? 'bg-blue-100 text-blue-600' : 'bg-purple-100 text-purple-600'"
                  >{{ rule.rule_type === 'builtin' ? '内置' : '自定义' }}</span>
                </td>
                <td class="py-2">
                  <button 
                    class="relative w-10 h-5 rounded-full transition-colors"
                    :class="rule.is_active ? 'bg-primary' : 'bg-slate-300'"
                    @click="toggleRule(rule)"
                  >
                    <span 
                      class="absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform"
                      :class="rule.is_active ? 'left-5' : 'left-0.5'"
                    ></span>
                  </button>
                </td>
                <td class="py-2">
                  <button 
                    v-if="rule.rule_type === 'custom'" 
                    class="text-xs text-red-500 hover:text-red-600"
                    @click="deleteRule(rule.id)"
                  >删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div class="p-4 border-t border-slate-200 bg-slate-50">
          <h4 class="text-sm font-semibold text-slate-700 mb-3">添加新规则</h4>
          <div class="flex gap-2 flex-wrap">
            <input v-model="newRule.name" placeholder="规则名称" class="flex-1 min-w-[120px] px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            <select v-model="newRule.condition_field" class="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
              <option value="">选择字段</option>
              <option v-for="f in fieldDefinitions" :key="f.name" :value="f.name">
                {{ f.label }}
              </option>
            </select>
            <select v-model="newRule.condition_operator" class="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
              <option value="">选择操作</option>
              <option v-for="o in operatorDefinitions" :key="o.name" :value="o.name">
                {{ o.label }}
              </option>
            </select>
            <input v-model="newRule.condition_value" placeholder="匹配值" class="flex-1 min-w-[100px] px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary" />
            <select v-model="newRule.result" class="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary">
              <option value="hazardous">危险品</option>
              <option value="non_hazardous">非危险品</option>
            </select>
            <button class="px-4 py-2 bg-primary hover:bg-primary-600 text-white text-sm font-medium rounded-lg transition-colors" @click="addRule">添加</button>
          </div>
        </div>
        
        <div class="px-6 py-4 border-t border-slate-200 flex justify-end">
          <button class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors" @click="showRuleDialog = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const API_BASE = 'http://localhost:8000/api/hazmat'

// 状态
const fileList = ref<any[]>([])
const selectedFile = ref<any>(null)
const statistics = ref({
  total_files: 0,
  hazardous: 0,
  non_hazardous: 0,
  pending: 0,
  completed: 0,
  confirmed: 0
})
const rules = ref<any[]>([])
const suggestions = ref<string[]>([])

// 分页和筛选
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 20
const searchKeyword = ref('')
const statusFilter = ref('')

// 对话框
const showModifyDialog = ref(false)
const showRuleDialog = ref(false)
const analyzing = ref(false)

// 修正表单
const modifyField = ref('un_number')
const modifyValue = ref('')
const modifyResult = ref('hazardous')
const createRuleFromModify = ref(false)
const newRuleName = ref('')

// 规则管理
const ruleTab = ref('all')
const fieldDefinitions = ref<any[]>([])
const operatorDefinitions = ref<any[]>([])
const newRule = ref({
  name: '',
  condition_field: '',
  condition_operator: 'contains',
  condition_value: '',
  result: 'hazardous'
})

// 文件上传
const fileInput = ref<HTMLInputElement | null>(null)

// PDF预览URL
const pdfUrl = computed(() => {
  if (selectedFile.value?.id) {
    const tkn = userStore.token.value || localStorage.getItem('token')
    return `${API_BASE}/files/${selectedFile.value.id}/content?token=${tkn}`
  }
  return ''
})

// 过滤后的规则
const filteredRules = computed(() => {
  if (ruleTab.value === 'all') return rules.value
  return rules.value.filter(r => r.rule_type === ruleTab.value)
})

// 获取请求头
function getHeaders() {
  const tkn = userStore.token.value || localStorage.getItem('token')
  return {
    'Authorization': `Bearer ${tkn}`,
    'Content-Type': 'application/json'
  }
}

// 获取状态标签
function getStatusLabel(status: string) {
  const labels: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已分析',
    'confirmed': '已确认',
    'error': '处理错误'
  }
  return labels[status] || status
}

// 获取结果标签
function getResultLabel(result: string) {
  const labels: Record<string, string> = {
    'hazardous': '是危险品',
    'non_hazardous': '非危险品',
    'uncertain': '待确认'
  }
  return labels[result] || result
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 格式化日期
function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 今天内显示时间
  if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  // 一周内显示星期
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return days[date.getDay()]
  }
  // 其他显示日期
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 加载文件列表
async function loadFiles() {
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: pageSize.toString()
    })
    if (statusFilter.value) params.append('status', statusFilter.value)
    if (searchKeyword.value) params.append('keyword', searchKeyword.value)
    
    const res = await fetch(`${API_BASE}/files?${params}`, {
      headers: getHeaders()
    })
    const data = await res.json()
    if (data.success) {
      fileList.value = data.data.items
      totalPages.value = data.data.total_pages
    }
  } catch (e) {
    console.error('加载文件列表失败:', e)
  }
}

// 加载统计信息
async function loadStatistics() {
  try {
    const res = await fetch(`${API_BASE}/statistics`, {
      headers: getHeaders()
    })
    const data = await res.json()
    if (data.success) {
      statistics.value = data.data
    }
  } catch (e) {
    console.error('加载统计信息失败:', e)
  }
}

// 加载规则列表
async function loadRules() {
  try {
    const res = await fetch(`${API_BASE}/rules?include_inactive=true`, {
      headers: getHeaders()
    })
    const data = await res.json()
    if (data.success) {
      rules.value = data.data
    }
  } catch (e) {
    console.error('加载规则失败:', e)
  }
}

// 加载字段定义
async function loadFieldDefinitions() {
  try {
    const res = await fetch(`${API_BASE}/field-definitions`)
    const data = await res.json()
    if (data.success) {
      fieldDefinitions.value = data.data.fields
      operatorDefinitions.value = data.data.operators
    }
  } catch (e) {
    console.error('加载字段定义失败:', e)
  }
}

// 选择文件
async function selectFile(file: any) {
  selectedFile.value = file
  suggestions.value = []
  
  // 如果已分析，重新获取详情
  if (file.status !== 'pending') {
    try {
      const res = await fetch(`${API_BASE}/files/${file.id}`, {
        headers: getHeaders()
      })
      const data = await res.json()
      if (data.success) {
        selectedFile.value = data.data
      }
    } catch (e) {
      console.error('获取文件详情失败:', e)
    }
  }
}

// 触发上传
function triggerUpload() {
  fileInput.value?.click()
}

// 打开智能学习模式
function openLearningMode() {
  // 通过事件通知父组件切换到学习模式
  const event = new CustomEvent('openLearningMode')
  window.dispatchEvent(event)
}

// 处理文件上传
async function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token.value}`
      },
      body: formData
    })
    const data = await res.json()
    if (data.success) {
      await loadFiles()
      await loadStatistics()
      selectFile(data.data)
    } else {
      alert(data.detail || '上传失败')
    }
  } catch (e) {
    console.error('上传失败:', e)
    alert('上传失败')
  }
  
  // 清空input
  input.value = ''
}

// 分析文件
async function analyzeFile() {
  if (!selectedFile.value) return
  
  analyzing.value = true
  try {
    const res = await fetch(`${API_BASE}/analyze/${selectedFile.value.id}?use_llm=true`, {
      method: 'POST',
      headers: getHeaders()
    })
    const data = await res.json()
    if (data.success) {
      suggestions.value = data.data.suggestions || []
      await loadFiles()
      await loadStatistics()
      // 刷新选中的文件
      await selectFile({ id: selectedFile.value.id })
    } else {
      alert(data.detail || '分析失败')
    }
  } catch (e) {
    console.error('分析失败:', e)
    alert('分析失败')
  } finally {
    analyzing.value = false
  }
}

// 确认结果
async function confirmResult(correct: boolean) {
  if (!selectedFile.value) return
  
  const result = correct ? selectedFile.value.result : 
    (selectedFile.value.result === 'hazardous' ? 'non_hazardous' : 'hazardous')
  
  try {
    const res = await fetch(`${API_BASE}/confirm`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        file_id: selectedFile.value.id,
        result: result
      })
    })
    const data = await res.json()
    if (data.success) {
      await loadFiles()
      await loadStatistics()
      await selectFile({ id: selectedFile.value.id })
    }
  } catch (e) {
    console.error('确认失败:', e)
  }
}

// 提交修正
async function submitModify() {
  if (!selectedFile.value) return
  
  try {
    const res = await fetch(`${API_BASE}/confirm`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        file_id: selectedFile.value.id,
        result: modifyResult.value,
        corrections: [{
          field_name: modifyField.value,
          new_value: modifyValue.value
        }],
        create_rule: createRuleFromModify.value,
        rule_name: newRuleName.value
      })
    })
    const data = await res.json()
    if (data.success) {
      showModifyDialog.value = false
      modifyValue.value = ''
      createRuleFromModify.value = false
      newRuleName.value = ''
      
      await loadFiles()
      await loadStatistics()
      await loadRules()
      await selectFile({ id: selectedFile.value.id })
    }
  } catch (e) {
    console.error('修正失败:', e)
  }
}

// 编辑字段
function editField(field: string) {
  modifyField.value = field
  modifyValue.value = selectedFile.value?.extracted_info?.[field] || ''
  modifyResult.value = selectedFile.value?.result || 'hazardous'
  showModifyDialog.value = true
}

// 删除当前文件
async function deleteCurrentFile() {
  if (!selectedFile.value) return
  if (!confirm('确定要删除此文件吗？')) return
  
  try {
    const res = await fetch(`${API_BASE}/files/${selectedFile.value.id}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
    const data = await res.json()
    if (data.success) {
      selectedFile.value = null
      await loadFiles()
      await loadStatistics()
    }
  } catch (e) {
    console.error('删除失败:', e)
  }
}

// 切换规则状态
async function toggleRule(rule: any) {
  try {
    const res = await fetch(`${API_BASE}/rules/${rule.id}/toggle?is_active=${!rule.is_active}`, {
      method: 'PUT',
      headers: getHeaders()
    })
    if (res.ok) {
      await loadRules()
    }
  } catch (e) {
    console.error('切换规则状态失败:', e)
  }
}

// 删除规则
async function deleteRule(ruleId: number) {
  if (!confirm('确定要删除此规则吗？')) return
  
  try {
    const res = await fetch(`${API_BASE}/rules/${ruleId}`, {
      method: 'DELETE',
      headers: getHeaders()
    })
    if (res.ok) {
      await loadRules()
    }
  } catch (e) {
    console.error('删除规则失败:', e)
  }
}

// 添加规则
async function addRule() {
  if (!newRule.value.name || !newRule.value.condition_field) {
    alert('请填写规则名称和条件字段')
    return
  }
  
  try {
    const res = await fetch(`${API_BASE}/rules`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(newRule.value)
    })
    const data = await res.json()
    if (data.success) {
      newRule.value = {
        name: '',
        condition_field: '',
        condition_operator: 'contains',
        condition_value: '',
        result: 'hazardous'
      }
      await loadRules()
    }
  } catch (e) {
    console.error('添加规则失败:', e)
  }
}

// 设置状态筛选
function setStatusFilter(status: string) {
  statusFilter.value = status
  currentPage.value = 1
  loadFiles()
}

// 切换页面
function changePage(page: number) {
  currentPage.value = page
  loadFiles()
}

// 防抖搜索
let searchTimer: number | null = null
function debounceSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadFiles()
  }, 300) as unknown as number
}

// 初始化
onMounted(() => {
  // 确保userStore初始化
  userStore.init()
  
  // 检查是否已登录
  if (userStore.isAuthenticated.value) {
    loadFiles()
    loadStatistics()
    loadRules()
  }
  loadFieldDefinitions()
})
</script>

<style>
/* 保留必要的全局样式 */
</style>
