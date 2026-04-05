<template>
  <div class="slash-panel">
    <div class="slash-panel-section recent-section">
      <div class="section-title">最近</div>
      <div class="office-apps">
        <div
          v-for="app in officeApps"
          :key="app.id"
          class="office-app-item"
          @click="selectApp(app)"
        >
          <component :is="app.icon" class="app-icon colored" />
          <span class="app-name">{{ app.name }}</span>
        </div>
      </div>
      <div class="recent-files">
        <div
          v-for="file in recentFiles"
          :key="file.id"
          class="recent-file-item"
          @click="selectFile(file)"
        >
          <FileIcon class="file-icon" />
          <div class="file-info">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-device">{{ file.deviceName }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="slash-panel-section apps-section">
      <div class="section-title">应用</div>
      <div class="apps-grid">
        <div
          v-for="app in otherApps"
          :key="app.id"
          class="app-item"
          @click="selectApp(app)"
        >
          <component :is="app.icon" class="app-icon mono" />
          <span class="app-name">{{ app.name }}</span>
        </div>
      </div>
    </div>

    <div class="slash-panel-section quick-actions-section">
      <div class="section-title">快捷操作</div>
      <div class="quick-actions-grid">
        <div
          v-for="action in quickActions"
          :key="action.id"
          class="quick-action-item"
          @click="selectConfig(action)"
        >
          <component :is="action.icon" class="action-icon" />
          <span class="action-name">{{ action.name }}</span>
        </div>
      </div>
    </div>

    <div class="slash-panel-section config-section">
      <div class="section-title">配置</div>
      <div class="config-list">
        <div
          v-for="config in configItems"
          :key="config.id"
          class="config-item"
          @click="selectConfig(config)"
        >
          <component :is="config.icon" class="config-icon" />
          <span class="config-name">{{ config.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface OfficeApp {
  id: string
  name: string
  icon: any
  type: string
}

interface RecentFile {
  id: string
  name: string
  deviceName: string
  deviceId: string
  path: string
  type: string
}

interface AppConfig {
  id: string
  name: string
  icon: any
  action: string
}

interface ConfigItem {
  id: string
  name: string
  icon: any
  action: string
}

const emit = defineEmits<{
  (e: 'select-app', app: OfficeApp): void
  (e: 'select-file', file: RecentFile): void
  (e: 'select-config', config: ConfigItem): void
}>()

const officeApps = ref<OfficeApp[]>([
  { id: 'word', name: 'Word', icon: 'WordIcon', type: 'word' },
  { id: 'ppt', name: 'PPT', icon: 'PptIcon', type: 'ppt' },
  { id: 'excel', name: 'Excel', icon: 'ExcelIcon', type: 'excel' },
])

const recentFiles = ref<RecentFile[]>([])

const otherApps = ref<AppConfig[]>([
  { id: 'calendar', name: '日历', icon: 'CalendarIcon', action: 'open-calendar' },
  { id: 'tasks', name: '任务', icon: 'TasksIcon', action: 'open-tasks' },
  { id: 'email', name: '邮件', icon: 'EmailIcon', action: 'open-email' },
  { id: 'notes', name: '笔记', icon: 'NotesIcon', action: 'open-notes' },
  { id: 'browser', name: '浏览器', icon: 'BrowserIcon', action: 'open-browser' },
  { id: 'files', name: '文件', icon: 'FilesIcon', action: 'open-files' },
])

const quickActions = ref<ConfigItem[]>([
  { id: 'event', name: '创建日程', icon: 'EventIcon', action: 'create-event' },
  { id: 'todo', name: '创建待办', icon: 'TodoIcon', action: 'create-todo' },
  { id: 'open', name: '打开文件', icon: 'OpenIcon', action: 'open-file' },
  { id: 'launch', name: '启动应用', icon: 'LaunchIcon', action: 'launch-app' },
])

const configItems = ref<ConfigItem[]>([
  { id: 'settings', name: '设置', icon: 'SettingsIcon', action: 'open-settings' },
  { id: 'mate', name: 'Mate模式', icon: 'MateIcon', action: 'toggle-mate' },
  { id: 'new-topic', name: '新话题', icon: 'NewTopicIcon', action: 'new-topic' },
])

const selectApp = (app: OfficeApp | AppConfig) => {
  emit('select-app', app)
}

const selectFile = (file: RecentFile) => {
  emit('select-file', file)
}

const selectConfig = (config: ConfigItem) => {
  emit('select-config', config)
}

const loadRecentFiles = async () => {
  try {
    const response = await fetch('/api/storage/recent?limit=3')
    if (response.ok) {
      const data = await response.json()
      recentFiles.value = data.files || []
    }
  } catch (error) {
    console.error('Failed to load recent files:', error)
  }
}

onMounted(() => {
  loadRecentFiles()
})
</script>

<style scoped>
.slash-panel {
  background: var(--bg-color, #ffffff);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 16px;
  max-width: 400px;
  max-height: 500px;
  overflow-y: auto;
}

.slash-panel-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #666);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.office-apps {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.office-app-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.office-app-item:hover {
  background-color: var(--hover-bg, #f5f5f5);
}

.app-icon.colored {
  width: 32px;
  height: 32px;
  margin-bottom: 4px;
}

.app-icon.mono {
  width: 24px;
  height: 24px;
  margin-bottom: 4px;
  color: var(--text-primary, #333);
}

.app-name {
  font-size: 12px;
  color: var(--text-primary, #333);
}

.recent-files {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recent-file-item {
  display: flex;
  align-items: center;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.recent-file-item:hover {
  background-color: var(--hover-bg, #f5f5f5);
}

.file-icon {
  width: 20px;
  height: 20px;
  margin-right: 8px;
  color: var(--text-secondary, #666);
}

.file-info {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 13px;
  color: var(--text-primary, #333);
}

.file-device {
  font-size: 11px;
  color: var(--text-secondary, #999);
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.app-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.app-item:hover {
  background-color: var(--hover-bg, #f5f5f5);
}

.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.quick-action-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.quick-action-item:hover {
  background-color: var(--hover-bg, #f5f5f5);
}

.action-icon {
  width: 18px;
  height: 18px;
  margin-right: 8px;
  color: var(--text-secondary, #666);
}

.action-name {
  font-size: 13px;
  color: var(--text-primary, #333);
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.config-item:hover {
  background-color: var(--hover-bg, #f5f5f5);
}

.config-icon {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  color: var(--text-secondary, #666);
}

.config-name {
  font-size: 13px;
  color: var(--text-primary, #333);
}
</style>
