<template>
  <div class="app" :class="{ 'dark': isDark }">
    <header class="header">
      <div class="logo">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="14" stroke="currentColor" stroke-width="2"/>
          <circle cx="16" cy="16" r="6" fill="currentColor"/>
          <path d="M16 6 L18 12L24 12L19 16L21 22L16 18L11 22L13 16L8 12L14 12L16 6Z" fill="currentColor" opacity="0.3"/>
        </svg>
        <span class="logo-text">
          <span class="logo-name">PyAgent</span>
          <span class="logo-version">v0.9.9</span>
        </span>
      </div>
      <nav class="nav">
        <router-link to="/" class="nav-item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8z"/>
            <path d="M17 17v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-8"/>
          </svg>
          <span>聊天</span>
        </router-link>
        <router-link to="/tasks" class="nav-item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
          <span>任务</span>
        </router-link>
        <router-link to="/config" class="nav-item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
          <span>配置</span>
        </router-link>
      </nav>
      <div class="header-actions">
        <div class="collaboration-toggle">
          <label class="toggle-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <circle cx="19" cy="5" r="2"/>
              <circle cx="5" cy="19" r="2"/>
              <path d="M10.5 9.5L7 6M14.5 14.5L18 18"/>
            </svg>
            <span>协作</span>
          </label>
          <button 
            class="toggle-switch" 
            :class="{ active: collaborationEnabled }" 
            @click="collaborationEnabled = !collaborationEnabled; toggleCollaboration()"
            :disabled="collaborationLoading"
          >
            <span class="toggle-slider"></span>
          </button>
        </div>
        <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换到亮色模式' : '切换到暗色模式'">
          <svg v-if="isDark" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>
      </div>
    </header>
    <main class="main">
      <router-view />
    </main>
    <footer class="footer">
      <span>PyAgent v0.9.9</span>
      <span class="divider">|</span>
      <span>AI原生智能体框架</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const isDark = ref(false)
const collaborationEnabled = ref(false)
const collaborationLoading = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

const toggleCollaboration = async () => {
  if (collaborationLoading.value) return
  collaborationLoading.value = true
  try {
    await axios.post('/api/collaboration/mode', {
      enabled: collaborationEnabled.value
    })
  } catch (error) {
    console.error('Toggle collaboration error:', error)
    collaborationEnabled.value = !collaborationEnabled.value
  } finally {
    collaborationLoading.value = false
  }
}

const loadCollaborationStatus = async () => {
  try {
    const response = await axios.get('/api/collaboration/status')
    collaborationEnabled.value = response.data.enabled || false
  } catch (error) {
    console.error('Load collaboration status error:', error)
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  }
  loadCollaborationStatus()
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary-color: #1890ff;
  --primary-hover: #40a9ff;
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #ff4d4f;
  --bg-color: #f5f7fa;
  --card-bg: #ffffff;
  --text-color: #333333;
  --text-secondary: #666666;
  --text-muted: #999999;
  --border-color: #e8e8e8;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-hover: 0 4px 16px rgba(0, 0, 0, 0.12);
}

[data-theme="dark"] {
  --primary-color: #177ddc;
  --primary-hover: #3c9ae8;
  --success-color: #49aa19;
  --warning-color: #d89614;
  --error-color: #d32029;
  --bg-color: #141414;
  --card-bg: #1f1f1f;
  --text-color: #ffffffd9;
  --text-secondary: #ffffffa6;
  --text-muted: #ffffff73;
  --border-color: #303030;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
  --shadow-hover: 0 4px 16px rgba(0, 0, 0, 0.6);
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-color);
  transition: background-color 0.3s, color 0.3s;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: var(--card-bg);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--primary-color);
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-name {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.2;
}

.logo-version {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 400;
}

.nav {
  display: flex;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  color: var(--text-secondary);
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s ease;
  font-size: 14px;
}

.nav-item:hover {
  background: var(--bg-color);
  color: var(--primary-color);
}

.nav-item.router-link-active {
  color: var(--primary-color);
  background: rgba(24, 144, 255, 0.1);
}

[data-theme="dark"] .nav-item.router-link-active {
  background: rgba(23, 125, 220, 0.2);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.theme-toggle:hover {
  background: var(--bg-color);
  color: var(--primary-color);
}

.collaboration-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg-color);
  border-radius: 8px;
  transition: background-color 0.3s;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}

.toggle-switch {
  position: relative;
  width: 36px;
  height: 20px;
  border: none;
  border-radius: 10px;
  background: var(--border-color);
  cursor: pointer;
  transition: background-color 0.3s;
  padding: 0;
}

.toggle-switch.active {
  background: var(--primary-color);
}

.toggle-switch:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toggle-slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-slider {
  transform: translateX(16px);
}

.main {
  flex: 1;
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.footer {
  background: var(--card-bg);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
  border-top: 1px solid var(--border-color);
  transition: background-color 0.3s, border-color 0.3s;
}

.footer .divider {
  opacity: 0.5;
}

@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
  }
  
  .nav {
    gap: 4px;
  }
  
  .nav-item {
    padding: 8px 12px;
  }
  
  .nav-item span {
    display: none;
  }
  
  .main {
    padding: 16px;
  }
  
  .logo-version {
    display: none;
  }
}
</style>
