import { createApp } from 'vue'
import { createPinia } from 'pinia'
import MateChat from '@matechat/core'
import '@devui-design/icons/icomoon/devui-icon.css'
import App from './App.vue'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(MateChat)
app.mount('#app')
