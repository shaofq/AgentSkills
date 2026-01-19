<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>
    
    <div class="login-card">
      <!-- Logo & 标题 -->
      <div class="login-header">
        <div class="logo-wrapper">
          <AcademicCapIcon class="logo-icon" />
        </div>
        <h1 class="title">Neptune AI</h1>
        <p class="subtitle">企业级智能化解决方案</p>
      </div>
      
      <!-- 登录表单 -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-field">
          <label for="username">用户名</label>
          <div class="input-wrapper">
            <UserIcon class="input-icon" />
            <input
              id="username"
              v-model="form.username"
              type="text"
              placeholder="请输入用户名"
              :disabled="loading"
              autocomplete="username"
              required
            />
          </div>
        </div>
        
        <div class="form-field">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <LockClosedIcon class="input-icon" />
            <input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :disabled="loading"
              autocomplete="current-password"
              required
            />
          </div>
        </div>
        
        <div v-if="error" class="error-alert">
          <ExclamationCircleIcon class="error-icon" />
          <span>{{ error }}</span>
        </div>
        
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>登录</span>
          <ArrowRightIcon v-if="!loading" class="btn-arrow" />
        </button>
      </form>
      
      <!-- 底部提示 -->
      <div class="login-footer">
        <p>默认账号：admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import axios from 'axios'
import { useUserStore } from '../stores/user'
import { 
  AcademicCapIcon, 
  UserIcon, 
  LockClosedIcon, 
  ExclamationCircleIcon,
  ArrowRightIcon 
} from '@heroicons/vue/24/outline'

const emit = defineEmits(['login-success'])

const userStore = useUserStore()

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!form.username || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.post('/api/auth/login', {
      username: form.username,
      password: form.password
    })
    
    if (response.data.success) {
      userStore.setAuth(response.data.data)
      emit('login-success')
    } else {
      error.value = response.data.message || '登录失败'
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* shadcn 风格暗色主题 */
.login-container {
  --primary: #d97706;
  --primary-light: #f59e0b;
  --bg-dark: #0a0908;
  --bg-card: rgba(20, 17, 14, 0.95);
  --border: rgba(255, 255, 255, 0.08);
  --text-primary: #f5f5f4;
  --text-secondary: rgba(245, 245, 244, 0.7);
  --text-muted: rgba(245, 245, 244, 0.5);
  
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-dark);
  padding: 24px;
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(217, 119, 6, 0.3) 0%, transparent 70%);
  top: -200px;
  right: -100px;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(34, 197, 94, 0.2) 0%, transparent 70%);
  bottom: -150px;
  left: -100px;
}

/* 登录卡片 */
.login-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  backdrop-filter: blur(20px);
  box-shadow: 
    0 25px 80px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.03) inset;
}

/* 头部 */
.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-wrapper {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(217, 119, 6, 0.3);
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: white;
}

.title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--text-muted);
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-field label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  color: var(--primary);
  pointer-events: none;
  transition: color 0.2s;
  z-index: 1;
}

.input-wrapper input {
  width: 100%;
  padding: 12px 14px 12px 44px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  transition: all 0.2s;
}

.input-wrapper input::placeholder {
  color: var(--text-muted);
}

.input-wrapper input:focus {
  outline: none;
  border-color: var(--primary);
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

.input-wrapper input:focus + .input-icon,
.input-wrapper:focus-within .input-icon {
  color: var(--primary-light);
}

.input-wrapper input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 覆盖浏览器 autofill 样式 */
.input-wrapper input:-webkit-autofill,
.input-wrapper input:-webkit-autofill:hover,
.input-wrapper input:-webkit-autofill:focus {
  -webkit-text-fill-color: var(--text-primary);
  -webkit-box-shadow: 0 0 0 1000px rgba(20, 17, 14, 0.95) inset;
  transition: background-color 5000s ease-in-out 0s;
  border-color: var(--border);
  font-weight: 400 !important;
}

/* 错误提示 */
.error-alert {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 10px;
  color: #f87171;
  font-size: 14px;
}

.error-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

/* 提交按钮 */
.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 20px;
  background: var(--primary);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 8px 24px rgba(217, 119, 6, 0.25);
}

.submit-btn:hover:not(:disabled) {
  background: var(--primary-light);
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(217, 119, 6, 0.35);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-arrow {
  width: 18px;
  height: 18px;
}

.spinner {
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

/* 底部 */
.login-footer {
  margin-top: 24px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.login-footer p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }
  
  .title {
    font-size: 22px;
  }
}
</style>
