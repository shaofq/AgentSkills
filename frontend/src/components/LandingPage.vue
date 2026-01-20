<template>
  <div class="landing-page">
    <!-- 导航栏 -->
    <nav class="navbar">
      <div class="nav-content">
        <div class="logo">
          <!-- <RocketLaunchIcon class="logo-icon" />  -->
          <AcademicCapIcon class="logo-icon" />   
         
          <span class="logo-text">Neptune AI</span>
        </div>
        <div class="nav-links">
          <a @click.prevent="scrollTo('business')">业务功能</a>
          <a @click.prevent="scrollTo('ai-tools')">AI助手</a>
          <a @click.prevent="scrollTo('features')">技术特性</a>
        </div>
        <button class="cta-btn" @click="enterApp">登录</button>
      </div>
    </nav>

    <!-- Hero 区域 -->
    <section class="hero">
      <div class="hero-bg">
        <div class="gradient-orb orb-1"></div>
        <div class="gradient-orb orb-2"></div>
        <div class="gradient-orb orb-3"></div>
      </div>
      <div class="hero-content">
        <div class="hero-badge">
          <SparklesIcon class="inline-icon" />
          AI驱动的智能平台
        </div>
        <h1 class="hero-title">
          <span class="gradient-text">Neptune AI</span>
          <br />
          企业级智能化解决方案
        </h1>
        <p class="hero-subtitle">
          融合大语言模型、视觉识别、流程自动化等前沿AI技术，为企业提供一站式智能化业务解决方案
         
        </p>
        <div class="hero-actions">
          <button class="primary-btn" @click="enterApp">
            <span>立即体验</span>
            <ArrowRightIcon class="btn-icon" />
          </button>
          <button class="secondary-btn" @click="scrollToFeatures">
            <span>了解更多</span>
          </button>
        </div>
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-value">99.5%</span>
            <span class="stat-label">识别准确率</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">10x</span>
            <span class="stat-label">效率提升</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-value">24/7</span>
            <span class="stat-label">自动化运行</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 核心业务功能 -->
    <section id="business" class="section business-section">
      <div class="section-header">
        <div class="section-badge">
          <CheckCircleIcon class="inline-icon" />
          核心业务
        </div>
        <h2 class="section-title">专业业务功能</h2>
        <p class="section-subtitle">针对航运物流行业深度定制，解决实际业务痛点</p>
      </div>

      <div class="business-tabs">
        <div class="business-tabs-inner">
          <button
            v-for="item in businessFeatures"
            :key="item.key"
            class="business-tab"
            :class="{ active: activeBusiness === item.key }"
            @click="activeBusiness = item.key"
            type="button"
          >
            <component :is="item.icon" class="business-tab-icon" />
            <span class="business-tab-text">{{ item.tabLabel }}</span>
          </button>
        </div>
      </div>

      <div class="business-feature">
        <div class="business-feature-left">
          <div class="business-pill">{{ currentBusiness.badge }}</div>
          <h3 class="business-feature-title">{{ currentBusiness.title }}</h3>
          <p class="business-feature-desc">{{ currentBusiness.desc }}</p>

          <button class="business-cta" type="button" @click="enterApp">
            <span>{{ currentBusiness.cta }}</span>
            <ArrowRightIcon class="btn-icon" />
          </button>
        </div>

        <div class="business-feature-right">
          <div class="business-preview">
            <div class="business-preview-bg"></div>
            <div class="business-preview-card">
              <img v-if="currentBusiness.previewImage" :src="currentBusiness.previewImage" :alt="currentBusiness.title" class="business-preview-img" />
              <template v-else>
                <component :is="currentBusiness.previewIcon" class="business-preview-icon" />
                <div class="business-preview-text">{{ currentBusiness.previewText }}</div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特性 -->
    <section id="features" class="section features-section">
      <div class="section-header">
        <div class="section-badge">
          <BoltIcon class="inline-icon" />
          技术特性
        </div>
        <h2 class="section-title">为什么选择我们</h2>
        <p class="section-subtitle">先进技术架构，可靠稳定的企业级解决方案</p>
      </div>
      <div class="features-grid">
        <div class="feature-card">
          <CpuChipIcon class="feature-icon" />
          <h3>多模型智能路由</h3>
          <p>根据任务场景自动选择最佳AI模型，平衡速度与质量，实现最优效果。</p>
        </div>
        <div class="feature-card">
          <ShieldCheckIcon class="feature-icon" />
          <h3>数据安全保障</h3>
          <p>本地化部署，数据不出企业，严格的权限控制，保护商业机密。</p>
        </div>
        <div class="feature-card">
          <BoltIcon class="feature-icon" />
          <h3>高效处理引擎</h3>
          <p>优化的处理管线，秒级响应，支持高并发批量任务处理。</p>
        </div>
        <div class="feature-card">
          <CodeBracketIcon class="feature-icon" />
          <h3>灵活可配置</h3>
          <p>可视化工作流编排，灵活的规则配置，快速适应业务变化。</p>
        </div>
        <div class="feature-card">
          <ChartBarIcon class="feature-icon" />
          <h3>完整追溯记录</h3>
          <p>全程操作历史记录，支持审计追溯，满足合规要求。</p>
        </div>
        <div class="feature-card">
          <GlobeAltIcon class="feature-icon" />
          <h3>开放集成能力</h3>
          <p>标准API接口，支持与现有系统无缝集成，扩展企业能力边界。</p>
        </div>
      </div>
    </section>

    <!-- AI 工具 -->
    <section id="ai-tools" class="section ai-section">
      <div class="section-header">
        <div class="section-badge">
          <CpuChipIcon class="inline-icon" />
          AI 助手
        </div>
        <h2 class="section-title">智能AI工具集</h2>
        <p class="section-subtitle">覆盖日常办公场景的AI助手，提升工作效率</p>
      </div>
      <div class="ai-tools-grid">
        <div class="ai-tool-card">
          <CodeBracketIcon class="tool-icon" />
          <div class="tool-content">
            <h4>代码助手</h4>
            <p>专业的代码生成和调试助手，支持amis、React、Vue等多种框架</p>
          </div>
        </div>
        <div class="ai-tool-card">
          <DocumentTextIcon class="tool-icon" />
          <div class="tool-content">
            <h4>公司制度问答</h4>
            <p>解答员工手册、财务制度、电脑补贴等公司规章问题</p>
          </div>
        </div>
        <div class="ai-tool-card">
          <EyeIcon class="tool-icon" />
          <div class="tool-content">
            <h4>OCR识别</h4>
            <p>识别PDF和图片中的文字内容，支持多种文档格式</p>
          </div>
        </div>
        <div class="ai-tool-card">
          <PresentationChartBarIcon class="tool-icon" />
          <div class="tool-content">
            <h4>PPT生成</h4>
            <p>根据文本内容自动生成专业PPT，节省制作时间</p>
          </div>
        </div>
        <div class="ai-tool-card">
          <GlobeAltIcon class="tool-icon" />
          <div class="tool-content">
            <h4>海运订舱</h4>
            <p>智能订舱助手，支持创建订舱申请和查询订舱状态</p>
          </div>
        </div>
        <div class="ai-tool-card">
          <GlobeAltIcon class="tool-icon" />
          <div class="tool-content">
            <h4>Web自动化</h4>
            <p>自动化Web页面操作，实现网页任务自动执行</p>
          </div>
        </div>
        <div class="ai-tool-card">
          <CloudIcon class="tool-icon" />
          <div class="tool-content">
            <h4>云应用AI</h4>
            <p>沙箱环境中执行代码、文件操作和浏览器自动化</p>
          </div>
        </div>
        <div class="ai-tool-card">
          <CodeBracketIcon class="tool-icon" />
          <div class="tool-content">
            <h4>技能创建</h4>
            <p>创建新的Skill技能包，设计技能结构和编写文档</p>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ -->
    <!-- <section id="faq" class="section faq-section">
      <div class="section-header">
        <div class="section-badge">
          <QuestionMarkCircleIcon class="inline-icon" />
          FAQ
        </div>
        <h2 class="section-title">常见问题</h2>
        <p class="section-subtitle">快速了解平台的常见问题</p>
      </div>
      <div class="faq-list">
        <div 
          v-for="(item, index) in faqItems" 
          :key="index" 
          class="faq-item"
          :class="{ active: activeFaq === index }"
        >
          <div class="faq-question" @click="toggleFaq(index)">
            <span>{{ item.question }}</span>
            <ChevronUpIcon v-if="activeFaq === index" class="faq-toggle-icon" />
            <ChevronDownIcon v-else class="faq-toggle-icon" />
          </div>
          <div class="faq-answer" v-show="activeFaq === index">
            {{ item.answer }}
          </div>
        </div>
      </div>
    </section> -->

    <!-- CTA -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>准备好提升您的业务效率了吗？</h2>
        <p>立即开始使用 Neptune AI，体验智能化办公的魅力</p>
        <button class="primary-btn large" @click="enterApp">
          <span>免费开始使用</span>
          <ArrowRightIcon class="btn-icon" />
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-brand">
          <!-- <span class="logo-icon">🚀</span> -->
          <span class="logo-text">Neptune AI</span>
          <p>企业级智能化办公平台</p>
        </div>
        <div class="footer-links">
          <div class="link-group">
            <h4>产品</h4>
            <a href="#business">业务功能</a>
            <a href="#features">功能特性</a>
            <a href="#ai-tools">AI工具</a>
          </div>
          <div class="link-group">
            <h4>支持</h4>
            <a href="#faq">常见问题</a>
            <a href="#">技术文档</a>
            <a href="#">API接口</a>
          </div>
          <div class="link-group">
            <h4>联系</h4>
            <a href="#">技术支持</a>
            <a href="#">商务合作</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2024 Neptune AI. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import {
  RocketLaunchIcon,
  SparklesIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  UserGroupIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  CpuChipIcon,
  CloudIcon,
  ChartBarIcon,
  BoltIcon,
  CodeBracketIcon,
  EyeIcon,
  PresentationChartBarIcon,
  ChatBubbleLeftRightIcon,
  DocumentDuplicateIcon,
  PhotoIcon,
  GlobeAltIcon,
  QuestionMarkCircleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  AcademicCapIcon
} from '@heroicons/vue/24/outline'

const businessFeatures = [
  {
    key: 'passport',
    tabLabel: '船员护照比对',
    icon: UserGroupIcon,
    badge: '船员护照比对',
    title: '船员护照比对',
    desc: '把名单核验，交给更聪明的方式。导入 Excel 名单与护照图片，系统自动 OCR 提取关键信息，并进行智能匹配与一致性校验。拼写差异、日期格式、缺失项、疑似错配，一目了然。差异结果清晰呈现，支持一键导出报告用于复核与留档。更少手工核对，更少遗漏，更快完成船员资料核验',
    points: ['Excel名单智能解析', '护照OCR自动识别', 'AI语义比对匹配', '差异报告一键导出'],
    cta: '开始使用',
    previewImage: '/ship.png'
  },
  {
    key: 'hazmat',
    tabLabel: '危险品智能识别',
    icon: ShieldCheckIcon,
    badge: '危险品识别',
    title: '危险品智能识别',
    desc: '危险品判定，不再靠经验堆叠。上传 SDS/MSDS，系统自动解析并抽取产品名称、CAS/UN、闪点、类别等核心信息，结合规则库与智能分析快速给出是否危险品的结论与依据。更重要的是，你的每一次确认与标注，都能沉淀为可复用规则草稿，支持审核与编辑，让识别越用越准、越用越可解释',
    points: ['多格式文件解析', '危险品智能判定', '规则库灵活配置', '批量审核确认'],
    cta: '开始使用',
    // previewIcon: ShieldCheckIcon,
    previewImage: '/aiDanger.png'
  },
  {
    key: 'docs',
    tabLabel: '单证智能审核',
    icon: DocumentTextIcon,
    badge: '单证处理',
    title: '单证智能审核',
    desc: '让单证处理变得轻松且可控。无论图片还是 PDF，系统自动识别版面与字段，提取单号、品名、数量、日期等关键信息，低置信度自动提示，便于快速复核。批量导入、统一汇总、结果直观呈现，减少重复录入与逐张核对。你把时间留给判断与决策，把繁琐交给自动化',
    points: ['视觉语言模型识别', '文件夹自动监控', '定位信息提取', '实时处理反馈'],
    cta: '开始使用',
    previewIcon: DocumentTextIcon,
    previewText: 'VL-OCR + 自动化处理'
  },
  {
    key: 'docsEmail',
    tabLabel: 'EMAIL自动派单',
    icon: DocumentTextIcon,
    badge: 'EMAIL自动派单',
    title: 'EMAIL自动派单',
    desc: '从邮件到任务，零延迟流转。系统自动接收指定邮箱的邮件与附件，识别主题与关键内容，按业务规则或智能分类完成分拣与派发。自动生成待办、记录处理状态、全程可追踪。减少转发与人工分配，避免遗漏与滞后。每一封邮件，都能更快到达正确的人与流程',
    points: ['视觉语言模型识别', '文件夹自动监控', '定位信息提取', '实时处理反馈'],
    cta: '开始使用',
    previewIcon: DocumentTextIcon,
    previewText: 'VL-OCR + 自动化处理'
  }
]

const activeBusiness = ref(businessFeatures[0].key)
const currentBusiness = computed(() => businessFeatures.find(i => i.key === activeBusiness.value) || businessFeatures[0])

const activeFaq = ref(null)

const faqItems = [
  {
    question: '这个平台支持哪些AI模型？',
    answer: '平台支持多种AI模型，包括Qwen系列（qwen3-max、qwen-vl-max-latest、qwen-plus）等，可根据不同任务场景智能选择最适合的模型。'
  },
  {
    question: '数据安全如何保障？',
    answer: '平台支持本地化部署，所有数据在企业内部处理，不会外传。同时提供完整的权限管理和操作审计功能。'
  },
  {
    question: '船员护照比对的准确率如何？',
    answer: '基于先进的视觉语言模型，护照OCR识别准确率达99.5%以上，结合AI语义比对，可智能处理姓名拼写差异、日期格式不同等情况。'
  },
  {
    question: '危险品识别支持哪些文件格式？',
    answer: '支持PDF、Excel、Word、图片等多种格式，系统会自动解析文件内容，提取货物信息进行危险品判定。'
  },
  {
    question: '如何配置自动化工作流？',
    answer: '平台提供可视化流程编排工具，通过拖拽方式设计工作流，支持条件分支、循环、并行等复杂逻辑，无需编程即可实现自动化。'
  },
  {
    question: '是否支持与现有系统集成？',
    answer: '平台提供标准RESTful API接口，支持与ERP、OA、TMS等企业系统集成，也支持通过邮件触发等方式与外部系统交互。'
  }
]

function toggleFaq(index) {
  activeFaq.value = activeFaq.value === index ? null : index
}

function enterApp() {
  // 跳转到主应用
  window.location.hash = '#app'
}

function scrollToFeatures() {
  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
}

function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<style scoped>
/* 基础变量 - 严格参照 raphael.app 配色（深棕/橙金暖色调） */
.landing-page {
  --primary: #d97706;
  --primary-light: #f59e0b;
  --primary-dark: #b45309;
  --secondary: #22c55e;
  --accent: #fbbf24;
  --bg-dark: #1a1510;
  --bg-darker: #0d0b08;
  --bg-card: rgba(30, 25, 20, 0.8);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-muted: rgba(255, 255, 255, 0.5);
  --border: rgba(255, 255, 255, 0.08);
  --gradient-1: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
  --gradient-2: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-darker);
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
}

/* 导航栏 */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 16px 0;
  background: rgba(13, 11, 8, 0.9);
  backdrop-filter: blur(20px);
  /* border-bottom: 1px solid var(--border); */
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 700;
  white-space: nowrap;
  min-width: 0;
  flex-shrink: 1;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: var(--primary);
  flex-shrink: 0;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 40px;
}

.nav-links a {
  color: var(--text-muted);
  text-decoration: none;
  font-size: 15px;
  font-weight: 400;
  transition: color 0.2s;
  white-space: nowrap;
  cursor: pointer;
}

.nav-links a:hover {
  color: var(--text-primary);
}

.cta-btn {
  padding: 10px 20px;
  background: #d97706;
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  flex-shrink: 0;
  white-space: nowrap;
}

.cta-btn:hover {
  transform: translateY(-2px);
  /* background: #16a34a; */
  box-shadow: 0 10px 40px rgba(34, 197, 94, 0.4);
}

/* Hero */
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120px 24px 80px;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.5;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: #92400e;
  top: -200px;
  right: -200px;
  animation-delay: 0s;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: #78350f;
  bottom: -150px;
  left: -150px;
  animation-delay: -7s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: #451a03;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 900px;
  text-align: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 14px;
  background: rgba(217, 119, 6, 0.15);
  border-radius: 100px;
  font-size: 13px;
  color: var(--primary-light);
  margin-bottom: 16px;
  white-space: nowrap;
}

.hero-title {
  font-size: 64px;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 24px;
  letter-spacing: -0.02em;
}

.gradient-text {
  background: var(--gradient-1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 40px;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 60px;
}

.primary-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 32px;
  background: var(--gradient-1);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.primary-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px rgba(217, 119, 6, 0.5);
}

.primary-btn.large {
  padding: 20px 40px;
  font-size: 18px;
}

.btn-icon {
  width: 20px;
  height: 20px;
  transition: transform 0.3s;
}

.primary-btn:hover .btn-icon {
  transform: translateX(4px);
}

.secondary-btn {
  padding: 16px 32px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.secondary-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--text-secondary);
}

.hero-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 36px;
  font-weight: 700;
  background: var(--gradient-2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 14px;
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--border);
}

/* Sections */
.section {
  padding: 100px 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 60px;
}

.section-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  background: rgba(217, 119, 6, 0.15);
  border-radius: 100px;
  font-size: 13px;
  color: var(--primary-light);
  margin-bottom: 16px;
  white-space: nowrap;
}

.section-title {
  font-size: 42px;
  font-weight: 700;
  margin-bottom: 16px;
  letter-spacing: -0.02em;
}

.section-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  max-width: 600px;
  margin: 0 auto;
}

/* Business Section */
.business-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.business-tabs {
  display: flex;
  justify-content: center;
  margin: 28px 0 40px;
}

.business-tabs-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  width: auto;
  background: rgba(255, 255, 255, 0.03);
  /* border: 1px solid var(--border); */
  /* backdrop-filter: blur(10px); */
  /* box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25); */
  /* overflow-x: auto; */
  /* position: relative; */
}


.business-tabs-inner::-webkit-scrollbar {
  display: none;
}

.business-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.25s ease;
}

.business-tab:hover {
  color: var(--text-secondary);
  transform: translateY(-1px);
}

.business-tab.active {
  background: rgba(217, 119, 6, 0.15);
  border: 1px solid rgba(217, 119, 6, 0.35);
  color: var(--text-primary);
  box-shadow: 0 8px 24px rgba(217, 119, 6, 0.15);
}

.business-tab-icon {
  width: 16px;
  height: 16px;
  color: var(--primary-light);
}

.business-tab.active .business-tab-icon {
  color: var(--primary-light);
}

.business-feature {
  display: grid;
  grid-template-columns: 1fr 1.1fr;
  gap: 60px;
  align-items: center;
  margin-top: 20px;
}

.business-feature-left {
  text-align: left;
}

.business-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(217, 119, 6, 0.14);
  border: 1px solid rgba(217, 119, 6, 0.22);
  color: var(--primary-light);
  font-size: 12px;
  margin-bottom: 14px;
  white-space: nowrap;
}

.business-feature-title {
  font-size: 36px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 0 0 20px;
  line-height: 1.2;
}

.business-feature-desc {
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.8;
  max-width: 480px;
  margin: 0 0 28px;
}

.business-feature-points {
  list-style: none;
  padding: 0;
  margin: 0 0 26px;
}

.business-feature-points li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}

.business-feature-points .list-icon {
  width: 16px;
  height: 16px;
  margin-right: 0;
  color: var(--primary-light);
}

.business-feature-points li:last-child {
  border-bottom: none;
}

.business-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  border: 0;
  border-radius: 10px;
  background: var(--primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 12px 32px rgba(217, 119, 6, 0.3);
  transition: all 0.25s ease;
}

.business-cta:hover {
  transform: translateY(-2px);
  background: var(--primary-light);
  box-shadow: 0 16px 40px rgba(217, 119, 6, 0.4);
}

.business-cta .btn-icon {
  width: 16px;
  height: 16px;
}

.business-feature-right {
  display: flex;
  justify-content: flex-end;
}

.business-preview {
  position: relative;
  width: 100%;
  max-width: 520px;
  aspect-ratio: 4 / 3;
  border-radius: 12px;
  overflow: hidden;
}

.business-preview-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 600px 400px at 20% 30%, rgba(217, 119, 6, 0.18) 0%, transparent 70%),
    radial-gradient(ellipse 500px 350px at 80% 70%, rgba(34, 197, 94, 0.12) 0%, transparent 70%);
}

.business-preview-card {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 16px;
  text-align: center;
  padding: 0px;
}

.business-preview-icon {
  width: 64px;
  height: 64px;
  color: var(--primary-light);
  filter: drop-shadow(0 8px 24px rgba(217, 119, 6, 0.3));
}

.business-preview-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.business-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 20px;
  transition: all 0.4s ease;
}

.business-preview-card:hover .business-preview-img {
  transform: scale(1.02);
}

.business-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 32px;
  transition: all 0.3s;
}

.business-card:hover {
  transform: translateY(-8px);
  border-color: var(--primary);
  box-shadow: 0 20px 40px rgba(217, 119, 6, 0.2);
}

.business-card.featured {
  background: linear-gradient(135deg, rgba(120, 53, 15, 0.2) 0%, rgba(69, 26, 3, 0.1) 100%);
}

.card-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 20px;
  color: var(--primary);
}

.business-card h3 {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 12px;
}

.business-card p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 20px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0 0 20px 0;
}

.feature-list li {
  padding: 8px 0;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
}

.feature-list li:last-child {
  border-bottom: none;
}

.card-footer {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tech-tag {
  padding: 4px 10px;
  background: rgba(34, 197, 94, 0.2);
  border-radius: 6px;
  font-size: 11px;
  color: #4ade80;
  font-weight: 500;
}

/* Features Section */
.features-section {
  /* background: linear-gradient(180deg, transparent 0%, rgba(120, 53, 15, 0.08) 50%, transparent 100%); */
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.feature-card {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  padding: 24px 16px;
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-3px);
}

.feature-icon {
  width: 32px;
  height: 32px;
  padding: 10px;
  margin-bottom: 20px;
  color: var(--primary);
  background: rgba(217, 119, 6, 0.12);
  border-radius: 50%;
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
}

.feature-card p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* AI Tools Section */
.ai-tools-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.ai-tool-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 20px 12px;
  transition: all 0.3s;
  box-shadow: none;
}

.ai-tool-card:hover {
  transform: translateY(-3px);
}

.tool-icon {
  width: 24px;
  height: 24px;
  padding: 8px;
  flex-shrink: 0;
  color: var(--secondary);
  background: rgba(34, 197, 94, 0.12);
  border-radius: 50%;
}

.tool-content h4 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
}

.tool-content p {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}

/* FAQ Section */
.faq-list {
  max-width: 800px;
  margin: 0 auto;
}

.faq-item {
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 12px;
  overflow: hidden;
  transition: all 0.3s;
}

.faq-item.active {
  border-color: var(--primary);
  background: rgba(217, 119, 6, 0.1);
}

.faq-question {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.faq-question:hover {
  background: rgba(255, 255, 255, 0.02);
}

.faq-toggle-icon {
  width: 24px;
  height: 24px;
  color: var(--primary);
}

.faq-answer {
  padding: 0 24px 20px;
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 14px;
}

/* CTA Section */
.cta-section {
  padding: 100px 24px;
  background: linear-gradient(135deg, rgba(120, 53, 15, 0.15) 0%, rgba(69, 26, 3, 0.1) 100%);
  text-align: center;
}

 .cta-content {
   display: flex;
   flex-direction: column;
   align-items: center;
 }

.cta-content h2 {
  font-size: 36px;
  font-weight: 700;
  margin-bottom: 16px;
}

.cta-content p {
  font-size: 18px;
  color: var(--text-secondary);
  margin-bottom: 32px;
}

 .cta-content .primary-btn {
   display: inline-flex;
   justify-content: center;
   margin: 0 auto;
 }

/* Footer */
.footer {
  background: var(--bg-dark);
  border-top: 1px solid var(--border);
  padding: 60px 24px 24px;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  padding-bottom: 40px;
  border-bottom: 1px solid var(--border);
}

.footer-brand {
  max-width: 300px;
}

.footer-brand .logo-icon {
  width: 24px;
  height: 24px;
}

.footer-brand .logo-text {
  font-size: 18px;
  font-weight: 700;
}

.footer-brand p {
  margin-top: 12px;
  font-size: 14px;
  color: var(--text-muted);
}

.footer-links {
  display: flex;
  gap: 80px;
}

.link-group h4 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
}

.link-group a {
  display: block;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  margin-bottom: 10px;
  transition: color 0.2s;
}

.link-group a:hover {
  color: var(--text-primary);
}

.inline-icon {
  width: 16px;
  height: 16px;
  margin-right: 6px;
  vertical-align: middle;
}

.footer-bottom {
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 24px;
  text-align: center;
}

.footer-bottom p {
  font-size: 13px;
  color: var(--text-muted);
}

.list-icon {
  width: 14px;
  height: 14px;
  margin-right: 8px;
  vertical-align: middle;
  color: var(--secondary);
}

/* Responsive */
@media (max-width: 1024px) {
  .business-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .ai-tools-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .business-feature {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .business-feature-left {
    text-align: center;
  }

  .business-feature-desc {
    margin-left: auto;
    margin-right: auto;
  }

  .business-feature-right {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
  }
  
  .hero-title {
    font-size: 40px;
  }
  
  .hero-stats {
    flex-direction: column;
    gap: 24px;
  }
  
  .stat-divider {
    display: none;
  }
  
  .business-grid,
  .features-grid,
  .ai-tools-grid {
    grid-template-columns: 1fr;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 40px;
  }
  
  .footer-links {
    flex-wrap: wrap;
    gap: 40px;
  }
}
</style>
