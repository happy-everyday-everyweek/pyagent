import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

import ChatView from './views/ChatView.vue'
import TasksView from './views/TasksView.vue'
import ConfigView from './views/ConfigView.vue'
import DocumentEditor from './views/DocumentEditor.vue'
import VideoEditor from './views/VideoEditor.vue'

const routes = [
  { path: '/', component: ChatView },
  { path: '/tasks', component: TasksView },
  { path: '/config', component: ConfigView },
  { path: '/document/:id', component: DocumentEditor },
  { path: '/video/:id', component: VideoEditor }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const pinia = createPinia()

const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
