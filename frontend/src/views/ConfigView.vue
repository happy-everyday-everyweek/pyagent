<template>
  <div class="config-view">
    <div class="config-section">
      <div class="section-header">
        <div class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <circle cx="19" cy="5" r="2"/>
            <circle cx="5" cy="19" r="2"/>
            <path d="M10.5 9.5L7 6M14.5 14.5L18 18"/>
          </svg>
          <h3>协作模式配置</h3>
        </div>
        <button class="save-btn" @click="saveCollaborationConfig" :disabled="saving">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
          </svg>
          <span>{{ saving ? '保存中...' : '保存配置' }}</span>
        </button>
      </div>
      <div class="config-grid">
        <div class="config-item full-width">
          <div class="config-row">
            <div class="config-label">
              <span class="label-text">启用协作模式</span>
              <span class="label-desc">允许多个智能体协作完成任务</span>
            </div>
            <button 
              class="toggle-switch" 
              :class="{ active: collaborationConfig.enabled }" 
              @click="collaborationConfig.enabled = !collaborationConfig.enabled"
            >
              <span class="toggle-slider"></span>
            </button>
          </div>
        </div>
        <div class="config-item">
          <label>
            <span class="label-text">最大智能体数量</span>
            <span class="label-desc">协作时最多可同时运行的智能体数</span>
          </label>
          <div class="input-wrapper">
            <input 
              type="number" 
              v-model.number="collaborationConfig.maxAgents" 
              min="1" 
              max="10"
            />
            <span class="input-suffix">个</span>
          </div>
        </div>
        <div class="config-item">
          <label>
            <span class="label-text">任务超时时间</span>
            <span class="label-desc">单个任务的最大执行时间</span>
          </label>
          <div class="input-wrapper">
            <input 
              type="number" 
              v-model.number="collaborationConfig.timeout" 
              min="30" 
              max="3600"
            />
            <span class="input-suffix">秒</span>
          </div>
        </div>
        <div class="config-item">
          <label>
            <span class="label-text">重试次数</span>
            <span class="label-desc">任务失败后的自动重试次数</span>
          </label>
          <div class="input-wrapper">
            <input 
              type="number" 
              v-model.number="collaborationConfig.retryCount" 
              min="0" 
              max="5"
            />
            <span class="input-suffix">次</span>
          </div>
        </div>
        <div class="config-item full-width">
          <div class="config-row">
            <div class="config-label">
              <span class="label-text">自动故障切换</span>
              <span class="label-desc">当某个智能体失败时自动切换到备用智能体</span>
            </div>
            <button 
              class="toggle-switch" 
              :class="{ active: collaborationConfig.autoFailover }" 
              @click="collaborationConfig.autoFailover = !collaborationConfig.autoFailover"
            >
              <span class="toggle-slider"></span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="config-section">
      <div class="section-header">
        <div class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="4" y="4" width="16" height="16" rx="2"/>
            <rect x="9" y="9" width="6" height="6"/>
            <line x1="9" y1="1" x2="9" y2="4"/>
            <line x1="15" y1="1" x2="15" y2="4"/>
            <line x1="9" y1="20" x2="9" y2="23"/>
            <line x1="15" y1="20" x2="15" y2="23"/>
            <line x1="20" y1="9" x2="23" y2="9"/>
            <line x1="20" y1="14" x2="23" y2="14"/>
            <line x1="1" y1="9" x2="4" y2="9"/>
            <line x1="1" y1="14" x2="4" y2="14"/>
          </svg>
          <h3>模型配置</h3>
        </div>
      </div>
      <div class="config-grid">
        <div class="config-item" v-for="(config, tier) in modelConfig" :key="tier">
          <label>
            <span class="label-text">{{ getTierLabel(tier) }}</span>
            <span class="label-desc">{{ getTierDesc(tier) }}</span>
          </label>
          <div class="config-value">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="4" y="4" width="16" height="16" rx="2"/>
              <rect x="9" y="9" width="6" height="6"/>
            </svg>
            <span>{{ config.model || '未配置' }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="config-section">
      <div class="section-header">
        <div class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
          <h3>MCP服务器</h3>
        </div>
      </div>
      <div class="mcp-servers">
        <div v-if="Object.keys(mcpServers).length === 0" class="empty">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          <span>暂无MCP服务器配置</span>
        </div>
        <div
          v-for="(server, name) in mcpServers"
          :key="name"
          class="server-item"
        >
          <div class="server-info">
            <span class="server-name">{{ name }}</span>
            <span class="tool-count">{{ server.tool_count }} 个工具</span>
          </div>
          <span :class="['server-status', server.connected ? 'connected' : 'disconnected']">
            <svg v-if="server.connected" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
            <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            {{ server.connected ? '已连接' : '未连接' }}
          </span>
        </div>
      </div>
    </div>
    
    <div class="config-section">
      <div class="section-header">
        <div class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 2 7 12 12 22 7 12 2"/>
            <polyline points="2 17 12 22 22 17"/>
            <polyline points="2 12 12 17 22 12"/>
          </svg>
          <h3>技能列表</h3>
        </div>
      </div>
      <div class="skills-list">
        <div v-if="skills.length === 0" class="empty">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polygon points="12 2 2 7 12 12 22 7 12 2"/>
          </svg>
          <span>暂无技能</span>
        </div>
        <div
          v-for="skill in skills"
          :key="skill.id"
          class="skill-item"
        >
          <div class="skill-info">
            <span class="skill-name">{{ skill.name }}</span>
            <span class="skill-desc">{{ skill.description }}</span>
          </div>
          <span class="skill-status" v-if="skill.enabled">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            已启用
          </span>
        </div>
      </div>
    </div>

    <div class="config-section">
      <div class="section-header">
        <div class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <h3>系统更新</h3>
        </div>
      </div>
      <div class="update-content">
        <div class="update-item">
          <div class="update-label">
            <span class="label-text">当前版本</span>
            <span class="label-desc">系统当前运行的版本号</span>
          </div>
          <div class="version-display">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            <span v-if="currentVersion">{{ currentVersion }}</span>
            <span v-else class="loading-text">加载中...</span>
          </div>
        </div>

        <div class="update-item">
          <div class="update-label">
            <span class="label-text">上传更新包</span>
            <span class="label-desc">选择 .zip 格式的更新包进行系统更新</span>
          </div>
          <div class="upload-area">
            <input
              type="file"
              ref="fileInput"
              accept=".zip"
              @change="handleFileSelect"
              style="display: none"
            />
            <button class="upload-btn" @click="$refs.fileInput.click()" :disabled="uploading || updateStatus.updating">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>{{ uploading ? '上传中...' : '选择文件' }}</span>
            </button>
            <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
            <button
              v-if="selectedFile && !uploading"
              class="confirm-btn"
              @click="uploadUpdate"
              :disabled="updateStatus.updating"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              确认上传
            </button>
          </div>
          <div v-if="uploadProgress > 0" class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            <span class="progress-text">{{ uploadProgress }}%</span>
          </div>
        </div>

        <div class="update-item" v-if="updateStatus.updating || updateStatus.message">
          <div class="update-label">
            <span class="label-text">更新状态</span>
            <span class="label-desc">当前系统更新的执行状态</span>
          </div>
          <div class="status-display">
            <div v-if="updateStatus.updating" class="status-updating">
              <div class="spinner"></div>
              <span>正在更新中，请稍候...</span>
            </div>
            <div v-else-if="updateStatus.success" class="status-success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <span>{{ updateStatus.message }}</span>
            </div>
            <div v-else-if="updateStatus.error" class="status-error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <span>{{ updateStatus.message }}</span>
            </div>
          </div>
          <div v-if="updateStatus.progress > 0 && updateStatus.updating" class="progress-bar">
            <div class="progress-fill" :style="{ width: updateStatus.progress + '%' }"></div>
            <span class="progress-text">{{ updateStatus.progress }}%</span>
          </div>
        </div>

        <div class="update-item">
          <div class="update-label">
            <span class="label-text">回滚操作</span>
            <span class="label-desc">将系统回滚到上一个稳定版本</span>
          </div>
          <div class="rollback-area">
            <div v-if="backupInfo" class="backup-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
                <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
                <line x1="6" y1="6" x2="6.01" y2="6"/>
                <line x1="6" y1="18" x2="6.01" y2="18"/>
              </svg>
              <span>最新备份: {{ backupInfo.version || '未知版本' }} ({{ backupInfo.time || '未知时间' }})</span>
            </div>
            <div v-else class="backup-info loading">
              <span>加载备份信息...</span>
            </div>
            <button
              class="rollback-btn"
              @click="performRollback"
              :disabled="rollbacking || updateStatus.updating || !backupInfo"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="1 4 1 10 7 10"/>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
              </svg>
              <span>{{ rollbacking ? '回滚中...' : '执行回滚' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const modelConfig = ref<Record<string, any>>({})
const mcpServers = ref<Record<string, any>>({})
const skills = ref<any[]>([])
const saving = ref(false)

const collaborationConfig = ref({
  enabled: false,
  maxAgents: 3,
  timeout: 300,
  retryCount: 2,
  autoFailover: true
})

const currentVersion = ref<string>('')
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const rollbacking = ref(false)
const backupInfo = ref<{ version: string; time: string } | null>(null)

const updateStatus = ref<{
  updating: boolean;
  success: boolean;
  error: boolean;
  message: string;
  progress: number;
}>({
  updating: false,
  success: false,
  error: false,
  message: '',
  progress: 0
})

const tierLabels: Record<string, string> = {
  'base': '基础模型',
  'strong': '强能力模型',
  'performance': '高性能模型',
  'cost-effective': '性价比模型'
}

const tierDescs: Record<string, string> = {
  'base': '默认模型，所有未指定分级的调用使用此模型',
  'strong': '负责规划任务，如GLM-5、GPT-5',
  'performance': '负责日常任务，如Qwen3.5-35B',
  'cost-effective': '负责意图判断、记忆整理等简单任务'
}

const getTierLabel = (tier: string) => {
  return tierLabels[tier] || tier
}

const getTierDesc = (tier: string) => {
  return tierDescs[tier] || ''
}

const loadConfig = async () => {
  try {
    const configRes = await axios.get('/api/config')
    modelConfig.value = configRes.data.models || {}
  } catch (error) {
    console.error('Load config error:', error)
  }
  
  try {
    const mcpRes = await axios.get('/api/mcp/servers')
    mcpServers.value = mcpRes.data.servers || {}
  } catch (error) {
    console.error('Load MCP servers error:', error)
  }
  
  try {
    const skillsRes = await axios.get('/api/skills')
    skills.value = skillsRes.data.skills || []
  } catch (error) {
    console.error('Load skills error:', error)
  }
  
  try {
    const collabRes = await axios.get('/api/collaboration/config')
    if (collabRes.data) {
      collaborationConfig.value = {
        enabled: collabRes.data.enabled || false,
        maxAgents: collabRes.data.max_agents || 3,
        timeout: collabRes.data.timeout || 300,
        retryCount: collabRes.data.retry_count || 2,
        autoFailover: collabRes.data.auto_failover !== false
      }
    }
  } catch (error) {
    console.error('Load collaboration config error:', error)
  }

  await loadVersionInfo()
  await loadBackupInfo()
  await loadUpdateStatus()
}

const loadVersionInfo = async () => {
  try {
    const res = await axios.get('/api/hot-reload/version')
    currentVersion.value = res.data.version || '未知版本'
  } catch (error) {
    console.error('Load version error:', error)
    currentVersion.value = '获取失败'
  }
}

const loadBackupInfo = async () => {
  try {
    const res = await axios.get('/api/hot-reload/backup')
    if (res.data && res.data.exists) {
      backupInfo.value = {
        version: res.data.version || '未知',
        time: res.data.time || '未知'
      }
    } else {
      backupInfo.value = null
    }
  } catch (error) {
    console.error('Load backup info error:', error)
    backupInfo.value = null
  }
}

const loadUpdateStatus = async () => {
  try {
    const res = await axios.get('/api/hot-reload/status')
    updateStatus.value = {
      updating: res.data.updating || false,
      success: res.data.success || false,
      error: res.data.error || false,
      message: res.data.message || '',
      progress: res.data.progress || 0
    }
  } catch (error) {
    console.error('Load update status error:', error)
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const file = target.files[0]
    if (file.name.endsWith('.zip')) {
      selectedFile.value = file
      updateStatus.value = {
        updating: false,
        success: false,
        error: false,
        message: '',
        progress: 0
      }
    } else {
      alert('请选择 .zip 格式的文件')
      target.value = ''
    }
  }
}

const uploadUpdate = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  uploadProgress.value = 0
  updateStatus.value = {
    updating: true,
    success: false,
    error: false,
    message: '正在上传更新包...',
    progress: 0
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    await axios.post('/api/hot-reload/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        }
      }
    })

    updateStatus.value = {
      updating: true,
      success: false,
      error: false,
      message: '上传成功，正在应用更新...',
      progress: 50
    }

    pollUpdateStatus()
  } catch (error: any) {
    console.error('Upload error:', error)
    updateStatus.value = {
      updating: false,
      success: false,
      error: true,
      message: error.response?.data?.message || '上传失败',
      progress: 0
    }
  } finally {
    uploading.value = false
  }
}

const pollUpdateStatus = async () => {
  const poll = async () => {
    try {
      const res = await axios.get('/api/hot-reload/status')
      updateStatus.value = {
        updating: res.data.updating || false,
        success: res.data.success || false,
        error: res.data.error || false,
        message: res.data.message || '',
        progress: res.data.progress || 0
      }

      if (updateStatus.value.updating) {
        setTimeout(poll, 1000)
      } else {
        await loadVersionInfo()
        await loadBackupInfo()
        selectedFile.value = null
        uploadProgress.value = 0
      }
    } catch (error) {
      console.error('Poll status error:', error)
      setTimeout(poll, 2000)
    }
  }

  poll()
}

const performRollback = async () => {
  if (!confirm('确定要回滚到上一个版本吗？')) return

  rollbacking.value = true
  updateStatus.value = {
    updating: true,
    success: false,
    error: false,
    message: '正在回滚...',
    progress: 0
  }

  try {
    await axios.post('/api/hot-reload/rollback')
    pollUpdateStatus()
  } catch (error: any) {
    console.error('Rollback error:', error)
    updateStatus.value = {
      updating: false,
      success: false,
      error: true,
      message: error.response?.data?.message || '回滚失败',
      progress: 0
    }
  } finally {
    rollbacking.value = false
  }
}

const saveCollaborationConfig = async () => {
  saving.value = true
  try {
    await axios.post('/api/collaboration/config', {
      enabled: collaborationConfig.value.enabled,
      max_agents: collaborationConfig.value.maxAgents,
      timeout: collaborationConfig.value.timeout,
      retry_count: collaborationConfig.value.retryCount,
      auto_failover: collaborationConfig.value.autoFailover
    })
  } catch (error) {
    console.error('Save collaboration config error:', error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.config-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-section {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  transition: border-color 0.3s;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-color);
}

.section-title h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.save-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--primary-color);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.save-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 20px;
}

.config-item {
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
  transition: background-color 0.3s;
}

.config-item.full-width {
  grid-column: 1 / -1;
}

.config-item label {
  display: block;
  margin-bottom: 12px;
}

.label-text {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 4px;
}

.label-desc {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
}

.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.config-label {
  flex: 1;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-wrapper input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--card-bg);
  color: var(--text-color);
  font-size: 14px;
  transition: border-color 0.3s, background-color 0.3s;
}

.input-wrapper input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.input-suffix {
  font-size: 13px;
  color: var(--text-muted);
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  border: none;
  border-radius: 12px;
  background: var(--border-color);
  cursor: pointer;
  transition: background-color 0.3s;
  padding: 0;
  flex-shrink: 0;
}

.toggle-switch.active {
  background: var(--primary-color);
}

.toggle-slider {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-switch.active .toggle-slider {
  transform: translateX(20px);
}

.config-value {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--card-bg);
  border-radius: 6px;
  font-size: 14px;
  color: var(--text-color);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  color: var(--text-muted);
  text-align: center;
}

.empty svg {
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty span {
  font-size: 13px;
}

.mcp-servers {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
}

.server-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-color);
  border-radius: 8px;
  transition: background-color 0.3s;
}

.server-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.server-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-color);
}

.tool-count {
  font-size: 12px;
  color: var(--text-muted);
}

.server-status {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.server-status.connected {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.server-status.disconnected {
  background: rgba(255, 77, 79, 0.1);
  color: var(--error-color);
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
}

.skill-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-color);
  border-radius: 8px;
  transition: background-color 0.3s;
}

.skill-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-name {
  font-weight: 500;
  font-size: 14px;
  color: var(--text-color);
}

.skill-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.skill-status {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
  font-size: 12px;
}

.update-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
}

.update-item {
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
  transition: background-color 0.3s;
}

.update-label {
  margin-bottom: 12px;
}

.version-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--card-bg);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.loading-text {
  color: var(--text-muted);
  font-weight: normal;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--primary-color);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.upload-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-name {
  padding: 6px 12px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-color);
}

.confirm-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--success-color);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.confirm-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.confirm-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.progress-bar {
  position: relative;
  height: 24px;
  background: var(--card-bg);
  border-radius: 12px;
  overflow: hidden;
  margin-top: 12px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
  border-radius: 12px;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-color);
}

.status-display {
  padding: 12px 16px;
  border-radius: 8px;
}

.status-updating {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--primary-color);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--primary-color);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.status-success {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(82, 196, 26, 0.1);
  border-radius: 6px;
  color: var(--success-color);
  font-size: 14px;
}

.status-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(255, 77, 79, 0.1);
  border-radius: 6px;
  color: var(--error-color);
  font-size: 14px;
}

.rollback-area {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.backup-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--card-bg);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-color);
}

.backup-info.loading {
  color: var(--text-muted);
}

.rollback-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--warning-color, #faad14);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.rollback-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.rollback-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .save-btn {
    width: 100%;
    justify-content: center;
  }

  .upload-area {
    flex-direction: column;
    align-items: stretch;
  }

  .upload-btn,
  .confirm-btn {
    justify-content: center;
  }

  .rollback-area {
    flex-direction: column;
    align-items: stretch;
  }

  .rollback-btn {
    justify-content: center;
  }
}
</style>
