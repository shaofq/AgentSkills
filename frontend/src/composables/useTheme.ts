import { ref, watch } from 'vue'

export type ThemeType = 'dark' | 'light'

const THEME_KEY = 'app-theme'

// 全局主题状态
const currentTheme = ref<ThemeType>((localStorage.getItem(THEME_KEY) as ThemeType) || 'dark')

// 应用主题到 document
function applyTheme(theme: ThemeType) {
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem(THEME_KEY, theme)
}

// 初始化时应用主题
applyTheme(currentTheme.value)

// 监听主题变化
watch(currentTheme, (newTheme) => {
  applyTheme(newTheme)
})

export function useTheme() {
  const toggleTheme = () => {
    currentTheme.value = currentTheme.value === 'dark' ? 'light' : 'dark'
  }

  const setTheme = (theme: ThemeType) => {
    currentTheme.value = theme
  }

  const isDark = () => currentTheme.value === 'dark'

  return {
    currentTheme,
    toggleTheme,
    setTheme,
    isDark,
  }
}
