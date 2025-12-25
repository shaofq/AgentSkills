<script setup lang="ts">
import { ref, onMounted } from 'vue'

const emit = defineEmits<{
  (e: 'login-success', user: { username: string }): void
}>()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

async function handleLogin() {
  if (!username.value.trim()) {
    error.value = '请输入用户名'
    return
  }
  if (!password.value.trim()) {
    error.value = '请输入密码'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    // 模拟登录验证（实际项目中应调用后端 API）
    await new Promise(resolve => setTimeout(resolve, 800))
    
    // 简单验证：用户名和密码都不为空即可登录
    // 实际项目中应该调用后端验证
    if (username.value && password.value) {
      // 保存登录状态到 localStorage
      const user = { username: username.value, loginTime: Date.now() }
      localStorage.setItem('user', JSON.stringify(user))
      emit('login-success', user)
    } else {
      error.value = '用户名或密码错误'
    }
  } catch (e) {
    error.value = '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    handleLogin()
  }
}

onMounted(() => {
  // 自动聚焦用户名输入框
  const input = document.querySelector('.login-input') as HTMLInputElement
  if (input) input.focus()
})
</script>

<template>
  <div class="login-page">
    <!-- 左侧装饰区域 (login9 风格) -->
    <div class="login-side-info">
      <!-- 背景装饰图形 -->
      <div class="bg-shapes">
        <div class="shape-circle shape-1"></div>
        <div class="shape-circle shape-2"></div>
        <div class="shape-circle shape-3"></div>
        <div class="shape-dots"></div>
      </div>
      
      <!-- 内容区域 -->
      <div class="side-info-content">
        <!-- 大标题 -->
        <h1 class="main-title">
          智能体编排与运行平台
          <span class="highlight">LowCode AI</span> 
          platform.
        </h1>
        
        <!-- 描述文字 -->
        <p class="main-desc">
          Access to the most powerful tool in the entire AI agent design and automation industry.
        </p>
        
        <!-- 底部装饰点 -->
        <div class="nav-dots">
          <span class="dot active"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
      
      <!-- 3D 装饰图片 (login9 风格 SVG) -->
      <div class="decoration-image">
        <svg class="login9-svg" viewBox="0 0 500 500" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- 背景圆形 -->
          <circle cx="250" cy="250" r="200" fill="rgba(255,255,255,0.1)"/>
          <circle cx="250" cy="250" r="150" fill="rgba(255,255,255,0.08)"/>
          
          <!-- 主要图形 - 3D 盒子 -->
          <g transform="translate(150, 120)">
            <!-- 顶面 -->
            <path d="M100 0 L200 50 L100 100 L0 50 Z" fill="rgba(255,255,255,0.3)"/>
            <!-- 左侧面 -->
            <path d="M0 50 L100 100 L100 200 L0 150 Z" fill="rgba(255,255,255,0.2)"/>
            <!-- 右侧面 -->
            <path d="M100 100 L200 50 L200 150 L100 200 Z" fill="rgba(255,255,255,0.15)"/>
          </g>
          
          <!-- 浮动小元素 -->
          <circle cx="120" cy="150" r="20" fill="rgba(251,191,36,0.8)"/>
          <circle cx="380" cy="200" r="15" fill="rgba(255,255,255,0.5)"/>
          <circle cx="350" cy="380" r="25" fill="rgba(255,255,255,0.3)"/>
          
          <!-- 装饰线条 -->
          <path d="M80 300 Q150 280 200 320" stroke="rgba(255,255,255,0.3)" stroke-width="2" fill="none"/>
          <path d="M300 100 Q350 150 320 200" stroke="rgba(255,255,255,0.2)" stroke-width="2" fill="none"/>
          
          <!-- 小方块 -->
          <rect x="400" cy="300" width="30" height="30" rx="5" fill="rgba(255,255,255,0.2)" transform="rotate(15 415 315)"/>
          <rect x="100" y="380" width="20" height="20" rx="3" fill="rgba(251,191,36,0.6)" transform="rotate(-10 110 390)"/>
        </svg>
      </div>
    </div>
    
    <!-- 右侧登录表单区域 -->
    <div class="login-form-area">
      <div class="form-container">
        <!-- 标题 -->
        <div class="form-header">
          <h1>登录账户</h1>
          <p>欢迎回来，请输入您的账户信息</p>
        </div>
        
        <!-- 登录表单 -->
        <div class="login-form">
          <div class="form-group">
            <label class="form-label">用户名</label>
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <input 
                v-model="username"
                type="text"
                class="login-input"
                placeholder="请输入用户名"
                @keydown="handleKeydown"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">密码</label>
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 11V7C7 5.67392 7.52678 4.40215 8.46447 3.46447C9.40215 2.52678 10.6739 2 12 2C13.3261 2 14.5979 2.52678 15.5355 3.46447C16.4732 4.40215 17 5.67392 17 7V11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <input 
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="login-input"
                placeholder="请输入密码"
                @keydown="handleKeydown"
              />
              <button 
                type="button"
                class="toggle-password"
                @click="showPassword = !showPassword"
              >
                <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 12C1 12 5 4 12 4C19 4 23 12 23 12C23 12 19 20 12 20C5 20 1 12 1 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17.94 17.94C16.2306 19.243 14.1491 19.9649 12 20C5 20 1 12 1 12C2.24389 9.68192 3.96914 7.65663 6.06 6.06M9.9 4.24C10.5883 4.0789 11.2931 3.99836 12 4C19 4 23 12 23 12C22.393 13.1356 21.6691 14.2048 20.84 15.19M14.12 14.12C13.8454 14.4148 13.5141 14.6512 13.1462 14.8151C12.7782 14.9791 12.3809 15.0673 11.9781 15.0744C11.5753 15.0815 11.1752 15.0074 10.8016 14.8565C10.4281 14.7056 10.0887 14.4811 9.80385 14.1962C9.51897 13.9113 9.29439 13.5719 9.14351 13.1984C8.99262 12.8248 8.91853 12.4247 8.92563 12.0219C8.93274 11.6191 9.02091 11.2218 9.18488 10.8538C9.34884 10.4859 9.58525 10.1546 9.88 9.88" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <line x1="1" y1="1" x2="23" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
          
          <!-- 错误提示 -->
          <div v-if="error" class="error-message">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <circle cx="12" cy="16" r="1" fill="currentColor"/>
            </svg>
            {{ error }}
          </div>
          
          <!-- 登录按钮 -->
          <button 
            class="login-button"
            :class="{ loading }"
            :disabled="loading"
            @click="handleLogin"
          >
            <span v-if="loading" class="loading-spinner"></span>
            <span v-else>登 录</span>
          </button>
          
          <!-- 底部提示 -->
          <p class="login-hint">
            首次使用？输入任意用户名和密码即可登录
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 分屏式登录页面 - 参考 iofrm login19 风格 */
.login-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  z-index: 9999;
}

/* 左侧装饰区域 */
/* ==================== 左侧区域 (login9 风格) ==================== */
.login-side-info {
  flex: 1;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px;
  overflow: hidden;
}

/* 背景装饰图形 */
.bg-shapes {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.shape-circle {
  position: absolute;
  border-radius: 50%;
}

.shape-circle.shape-1 {
  width: 500px;
  height: 500px;
  border: 80px solid rgba(255, 255, 255, 0.08);
  top: -200px;
  right: -150px;
}

.shape-circle.shape-2 {
  width: 300px;
  height: 300px;
  border: 50px solid rgba(255, 255, 255, 0.06);
  bottom: -100px;
  left: -100px;
}

.shape-circle.shape-3 {
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.05);
  top: 50%;
  left: 20%;
}

.shape-dots {
  position: absolute;
  width: 150px;
  height: 150px;
  bottom: 20%;
  right: 15%;
  background-image: radial-gradient(rgba(255, 255, 255, 0.4) 2px, transparent 2px);
  background-size: 15px 15px;
}

/* 内容区域 */
.side-info-content {
  position: relative;
  z-index: 2;
  max-width: 500px;
}

/* 大标题 */
.main-title {
  font-size: 42px;
  font-weight: 700;
  color: white;
  line-height: 1.3;
  margin: 0 0 24px 0;
}

.main-title .highlight {
  color: #fbbf24;
}

/* 描述文字 */
.main-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.7;
  margin: 0 0 40px 0;
}

/* 底部导航点 */
.nav-dots {
  display: flex;
  gap: 10px;
}

.nav-dots .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.3s;
}

.nav-dots .dot.active {
  background: white;
  width: 30px;
  border-radius: 6px;
}

/* 装饰 SVG 图片 */
.decoration-image {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 400px;
  height: 400px;
  opacity: 0.9;
}

.login9-svg {
  width: 100%;
  height: 100%;
  animation: float-svg 4s ease-in-out infinite;
}

@keyframes float-svg {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-15px) rotate(2deg);
  }
}

/* 右侧登录表单区域 */
.login-form-area {
  flex: 1;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.form-container {
  width: 100%;
  max-width: 400px;
}

/* 表单标题 */
.form-header {
  margin-bottom: 40px;
}

.form-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 12px 0;
}

.form-header p {
  font-size: 16px;
  color: #6b7280;
  margin: 0;
}

/* 表单样式 */
.login-form {
  position: relative;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  width: 20px;
  height: 20px;
  color: #9ca3af;
  pointer-events: none;
}

.login-input {
  width: 100%;
  padding: 16px 48px;
  font-size: 15px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  outline: none;
  transition: all 0.3s ease;
  background: #f9fafb;
  color: #1a1a2e;
}

.login-input:focus {
  border-color: #1e3a5f;
  background: white;
  box-shadow: 0 0 0 4px rgba(30, 58, 95, 0.15);
}

.login-input::placeholder {
  color: #9ca3af;
}

.toggle-password {
  position: absolute;
  right: 16px;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: none;
  color: #9ca3af;
  cursor: pointer;
  transition: color 0.2s;
}

.toggle-password:hover {
  color: #1e3a5f;
}

.toggle-password svg {
  width: 20px;
  height: 20px;
}

/* 错误提示 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #dc2626;
  font-size: 14px;
  margin-bottom: 24px;
}

.error-message svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* 登录按钮 */
.login-button {
  width: 100%;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 20px -5px rgba(30, 58, 95, 0.4);
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px -5px rgba(30, 58, 95, 0.5);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-hint {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
  margin: 24px 0 0 0;
}

/* 响应式设计 */
@media (max-width: 900px) {
  .login-page {
    flex-direction: column;
  }
  
  .login-side-info {
    flex: none;
    height: 200px;
  }
  
  .side-text h2 {
    font-size: 24px;
  }
  
  .side-text p {
    font-size: 14px;
  }
  
  .bottom-decoration {
    display: none;
  }
}

@media (max-width: 480px) {
  .login-form-area {
    padding: 24px;
  }
  
  .form-header h1 {
    font-size: 24px;
  }
}
</style>
