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
    <!-- 左侧装饰区域 -->
    <div class="login-side-info">
      <div class="side-info-content">
        <!-- 装饰图形 -->
        <div class="decorative-shapes">
          <div class="shape shape-1"></div>
          <div class="shape shape-2"></div>
          <div class="shape shape-3"></div>
          <div class="shape shape-4"></div>
          <div class="dots-pattern"></div>
        </div>
        
        <!-- Logo -->
        <div class="side-logo">
          <div class="logo-circle">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="logo-text">LowCode AI</span>
        </div>
        
        <!-- 宣传文案 -->
        <div class="side-text">
          <h2>智能体编排平台</h2>
          <p>通过可视化工作流，轻松构建和部署 AI 智能体应用</p>
        </div>
        
       
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
.login-side-info {
  flex: 1;
  background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.side-info-content {
  position: relative;
  z-index: 2;
  text-align: center;
  padding: 40px;
}

/* 装饰图形 */
.decorative-shapes {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}

.shape-1 {
  width: 400px;
  height: 400px;
  border: 60px solid rgba(255, 255, 255, 0.1);
  top: -150px;
  left: -100px;
}

.shape-2 {
  width: 300px;
  height: 300px;
  border: 50px solid rgba(255, 255, 255, 0.08);
  bottom: -100px;
  right: -80px;
}

.shape-3 {
  width: 150px;
  height: 150px;
  background: rgba(255, 255, 255, 0.1);
  top: 30%;
  right: 10%;
}

.shape-4 {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.15);
  bottom: 25%;
  left: 15%;
}

.dots-pattern {
  position: absolute;
  width: 200px;
  height: 200px;
  top: 20%;
  left: 10%;
  background-image: radial-gradient(rgba(255, 255, 255, 0.3) 2px, transparent 2px);
  background-size: 20px 20px;
}

/* Logo */
.side-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}

.logo-circle {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.logo-circle svg {
  width: 40px;
  height: 40px;
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: white;
  letter-spacing: 1px;
}

/* 宣传文案 */
.side-text {
  max-width: 320px;
  margin: 0 auto;
}

.side-text h2 {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin: 0 0 16px 0;
  line-height: 1.3;
}

.side-text p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: 1.6;
}

/* 底部装饰线 */
.bottom-decoration {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}

.bottom-decoration .line {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.bottom-decoration .line:first-child {
  background: white;
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
