<template>
  <div class="tasks-view">
    <div class="tasks-header">
      <div class="header-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
        <h2>任务管理</h2>
      </div>
      <div class="header-actions">
        <button class="create-btn" @click="showCreateDialog = true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          <span>新建任务</span>
        </button>
        <button class="refresh-btn" @click="refreshTasks">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
          <span>刷新</span>
        </button>
      </div>
    </div>
    
    <div class="filter-bar">
      <div class="filter-tabs">
        <button 
          v-for="tab in filterTabs" 
          :key="tab.value" 
          :class="['filter-tab', { active: currentFilter === tab.value }]"
          @click="currentFilter = tab.value"
        >
          {{ tab.label }}
          <span class="count">{{ getFilterCount(tab.value) }}</span>
        </button>
      </div>
    </div>
    
    <div class="tasks-content">
      <div v-if="filteredTasks.length === 0" class="empty-state">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
        <p>暂无{{ currentFilter === 'all' ? '' : getFilterLabel(currentFilter) }}任务</p>
        <span>执行任务后，任务列表将显示在这里</span>
      </div>
      
      <div v-else class="tasks-list">
        <div v-for="task in filteredTasks" :key="task.id" class="task-card" @click="viewTask(task)" :style="getTaskProgressStyle(task)">
          <div class="task-header">
            <span :class="['status-badge', getStatusClass(task)]">
              {{ task.display_status || getDisplayStatus(task) }}
            </span>
          </div>
          <div class="task-prompt" v-if="task.prompt">{{ task.prompt }}</div>
          
          <div class="task-waiting-message" v-if="task.waiting_message">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="16" x2="12" y2="12"/>
              <line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            <span>{{ task.waiting_message }}</span>
          </div>
          
          <div class="task-body">
            <div class="task-meta">
              <div class="meta-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 6v6l4 2"/>
                </svg>
                <span>{{ formatTime(task.created_at) }}</span>
              </div>
              <div class="meta-item" v-if="task.duration">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
                <span>{{ task.duration }}ms</span>
              </div>
            </div>
            <div class="task-result" v-if="task.result">
              <span class="label">结果:</span>
              <div class="result-content">{{ task.result }}</div>
            </div>
            <div class="task-error" v-if="task.error">
              <span class="label">错误:</span>
              <div class="error-content">{{ task.error }}</div>
            </div>
          </div>
          
          <div class="task-user-actions" v-if="task.state === 'waiting'">
            <template v-if="task.waiting_type === 'confirm'">
              <button class="user-action-btn confirm" @click.stop="confirmTask(task)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                确认
              </button>
              <button class="user-action-btn cancel" @click.stop="cancelTaskConfirm(task)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
                取消
              </button>
            </template>
            <template v-else-if="task.waiting_type === 'assist'">
              <button class="user-action-btn provided" @click.stop="assistProvided(task)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                已提供
              </button>
              <button class="user-action-btn skip" @click.stop="skipAssist(task)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5 4 15 12 5 20 5 4"/>
                  <line x1="19" y1="5" x2="19" y2="19"/>
                </svg>
                跳过
              </button>
            </template>
          </div>
          
          <div class="task-actions">
            <button class="action-btn view" @click.stop="viewTask(task)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              查看
            </button>
            <button class="action-btn cancel" @click.stop="cancelTask(task)" v-if="task.status === 'running'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              取消
            </button>
            <button class="action-btn retry" @click.stop="retryTask(task)" v-if="task.status === 'failed'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6M1 20v-6h6"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
              </svg>
              重试
            </button>
            <button class="action-btn resume" @click.stop="resumeTask(task)" v-if="task.state === 'paused'">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              继续
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="tasks-stats">
      <div class="stat-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        <span class="stat-label">运行中</span>
        <span class="stat-value running">{{ runningCount }}</span>
      </div>
      <div class="stat-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <span class="stat-label">已完成</span>
        <span class="stat-value completed">{{ completedCount }}</span>
      </div>
      <div class="stat-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <span class="stat-label">失败</span>
        <span class="stat-value error">{{ failedCount }}</span>
      </div>
      <div class="stat-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="10" y1="15" x2="10" y2="9"/>
          <line x1="14" y1="15" x2="14" y2="9"/>
        </svg>
        <span class="stat-label">暂停</span>
        <span class="stat-value paused">{{ pausedCount }}</span>
      </div>
      <div class="stat-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        <span class="stat-label">等待</span>
        <span class="stat-value waiting">{{ waitingCount }}</span>
      </div>
    </div>
    
    <div class="create-dialog" v-if="showCreateDialog" @click.self="showCreateDialog = false">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>新建任务</h3>
          <button class="close-btn" @click="showCreateDialog = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-item">
            <label>任务描述</label>
            <textarea v-model="newTaskPrompt" placeholder="请输入任务描述..." rows="4"></textarea>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="showCreateDialog = false">取消</button>
          <button class="btn-submit" @click="createTask" :disabled="!newTaskPrompt.trim()">创建</button>
        </div>
      </div>
    </div>
    
    <div class="task-detail-dialog" v-if="selectedTask" @click.self="selectedTask = null">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>任务详情</h3>
          <button class="close-btn" @click="selectedTask = null">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="detail-item">
            <span class="detail-label">任务ID</span>
            <span class="detail-value">{{ selectedTask.id }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">状态</span>
            <span :class="['status-badge', getStatusClass(selectedTask)]">{{ selectedTask.display_status || getDisplayStatus(selectedTask) }}</span>
          </div>
          <div class="detail-item" v-if="selectedTask.state">
            <span class="detail-label">任务状态</span>
            <span class="detail-value">{{ getStateLabel(selectedTask.state) }}</span>
          </div>
          <div class="detail-item" v-if="selectedTask.progress && selectedTask.progress > 0">
            <span class="detail-label">进度</span>
            <div class="detail-progress-bar" :style="{ background: `linear-gradient(to right, rgba(24, 144, 255, 0.2) ${selectedTask.progress}%, var(--bg-color) ${selectedTask.progress}%)` }">
              <span class="progress-value">{{ selectedTask.progress }}%</span>
            </div>
          </div>
          <div class="detail-item" v-if="selectedTask.prompt">
            <span class="detail-label">任务描述</span>
            <div class="detail-content">{{ selectedTask.prompt }}</div>
          </div>
          <div class="detail-item" v-if="selectedTask.waiting_message">
            <span class="detail-label">等待信息</span>
            <div class="detail-content warning">{{ selectedTask.waiting_message }}</div>
          </div>
          <div class="detail-item" v-if="selectedTask.result">
            <span class="detail-label">执行结果</span>
            <div class="detail-content result">{{ selectedTask.result }}</div>
          </div>
          <div class="detail-item" v-if="selectedTask.error">
            <span class="detail-label">错误信息</span>
            <div class="detail-content error">{{ selectedTask.error }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

interface Task {
  id: string
  status: 'running' | 'completed' | 'failed' | 'pending'
  state?: 'active' | 'paused' | 'error' | 'waiting'
  progress?: number
  display_status?: string
  waiting_type?: 'confirm' | 'assist'
  waiting_message?: string
  prompt?: string
  result?: string
  error?: string
  created_at?: number
  duration?: number
}

const tasks = ref<Task[]>([])
const currentFilter = ref('all')
const showCreateDialog = ref(false)
const newTaskPrompt = ref('')
const selectedTask = ref<Task | null>(null)
let refreshInterval: number | null = null

const filterTabs = [
  { label: '全部', value: 'all' },
  { label: '活跃', value: 'active' },
  { label: '暂停', value: 'paused' },
  { label: '异常', value: 'error' },
  { label: '等待', value: 'waiting' }
]

const filteredTasks = computed(() => {
  if (currentFilter.value === 'all') {
    return tasks.value
  }
  return tasks.value.filter(t => t.state === currentFilter.value)
})

const runningCount = computed(() => tasks.value.filter(t => t.status === 'running').length)
const completedCount = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const failedCount = computed(() => tasks.value.filter(t => t.status === 'failed').length)
const pausedCount = computed(() => tasks.value.filter(t => t.state === 'paused').length)
const waitingCount = computed(() => tasks.value.filter(t => t.state === 'waiting').length)

const getFilterCount = (filter: string) => {
  if (filter === 'all') return tasks.value.length
  return tasks.value.filter(t => t.state === filter).length
}

const getFilterLabel = (filter: string) => {
  const tab = filterTabs.find(t => t.value === filter)
  return tab ? tab.label : ''
}

const getStateLabel = (state: string) => {
  const labels: Record<string, string> = {
    active: '活跃',
    paused: '已暂停',
    error: '异常',
    waiting: '等待中'
  }
  return labels[state] || state
}

const getStatusClass = (task: Task) => {
  if (task.state === 'waiting') {
    return task.waiting_type === 'confirm' ? 'waiting-confirm' : 'waiting-assist'
  }
  if (task.state === 'paused') return 'paused'
  if (task.state === 'error') return 'error'
  if (task.status === 'completed') return 'completed'
  if (task.status === 'failed') return 'failed'
  if (task.status === 'running') return 'running'
  return 'pending'
}

const getTaskProgressStyle = (task: Task) => {
  if (task.progress && task.progress > 0) {
    const opacity = Math.min(0.15, task.progress / 100 * 0.15)
    return {
      background: `linear-gradient(to right, rgba(24, 144, 255, ${opacity}) ${task.progress}%, var(--bg-color) ${task.progress}%)`
    }
  }
  return {}
}

const getDisplayStatus = (task: Task): string => {
  if (task.display_status) return task.display_status
  
  if (task.status === 'completed') return '执行|完成'
  if (task.status === 'failed') return '执行|失败'
  
  if (task.state === 'waiting') {
    if (task.waiting_type === 'confirm') return '执行|须您确认'
    if (task.waiting_type === 'assist') return '执行|须您协助'
    return '执行|等待中'
  }
  
  if (task.state === 'paused') return '执行|已暂停'
  if (task.state === 'error') return '执行|异常'
  
  if (task.status === 'running') {
    if (task.progress && task.progress > 0) {
      return `执行|${task.progress}%`
    }
    return '执行|规划中'
  }
  
  return '等待中'
}

const formatTime = (timestamp?: number) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const refreshTasks = async () => {
  try {
    const response = await axios.get('/api/tasks')
    const taskList: Task[] = []
    
    if (response.data.tasks && Array.isArray(response.data.tasks)) {
      for (const taskData of response.data.tasks) {
        taskList.push({
          id: taskData.id,
          status: taskData.status || 'running',
          state: taskData.state,
          progress: taskData.progress,
          display_status: taskData.display_status,
          waiting_type: taskData.waiting_type,
          waiting_message: taskData.waiting_message,
          prompt: taskData.prompt,
          result: taskData.result,
          error: taskData.error,
          created_at: taskData.created_at,
          duration: taskData.duration
        })
      }
    } else {
      const runningTasks = response.data.running?.map((t: any) => ({
        id: typeof t === 'string' ? t : t.id,
        status: 'running' as const,
        state: typeof t === 'object' ? t.state : 'active',
        progress: typeof t === 'object' ? t.progress : 0,
        display_status: typeof t === 'object' ? t.display_status : undefined,
        waiting_type: typeof t === 'object' ? t.waiting_type : undefined,
        waiting_message: typeof t === 'object' ? t.waiting_message : undefined
      })) || []
      
      const completedTasks = response.data.completed?.map((task: any) => ({
        id: task.id,
        status: 'completed' as const,
        state: 'active' as const,
        result: task.result,
        duration: task.duration
      })) || []
      
      const failedTasks = response.data.failed?.map((task: any) => ({
        id: task.id,
        status: 'failed' as const,
        state: 'error' as const,
        error: task.error
      })) || []
      
      taskList.push(...runningTasks, ...completedTasks, ...failedTasks)
    }
    
    tasks.value = taskList
  } catch (error) {
    console.error('Refresh tasks error:', error)
  }
}

const createTask = async () => {
  if (!newTaskPrompt.value.trim()) return
  try {
    await axios.post('/api/tasks', {
      prompt: newTaskPrompt.value
    })
    showCreateDialog.value = false
    newTaskPrompt.value = ''
    await refreshTasks()
  } catch (error) {
    console.error('Create task error:', error)
  }
}

const viewTask = (task: Task) => {
  selectedTask.value = task
}

const cancelTask = async (task: Task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/cancel`)
    await refreshTasks()
  } catch (error) {
    console.error('Cancel task error:', error)
  }
}

const retryTask = async (task: Task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/retry`)
    await refreshTasks()
  } catch (error) {
    console.error('Retry task error:', error)
  }
}

const resumeTask = async (task: Task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/resume`)
    await refreshTasks()
  } catch (error) {
    console.error('Resume task error:', error)
  }
}

const confirmTask = async (task: Task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/confirm`)
    await refreshTasks()
  } catch (error) {
    console.error('Confirm task error:', error)
  }
}

const cancelTaskConfirm = async (task: Task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/cancel-confirm`)
    await refreshTasks()
  } catch (error) {
    console.error('Cancel task confirm error:', error)
  }
}

const assistProvided = async (task: Task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/assist-provided`)
    await refreshTasks()
  } catch (error) {
    console.error('Assist provided error:', error)
  }
}

const skipAssist = async (task: Task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/skip-assist`)
    await refreshTasks()
  } catch (error) {
    console.error('Skip assist error:', error)
  }
}

onMounted(() => {
  refreshTasks()
  refreshInterval = window.setInterval(refreshTasks, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
.tasks-view {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  transition: border-color 0.3s;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-color);
}

.header-title h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.create-btn, .refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.create-btn {
  background: var(--success-color);
  color: #fff;
}

.create-btn:hover {
  opacity: 0.9;
}

.refresh-btn {
  background: var(--primary-color);
  color: #fff;
}

.refresh-btn:hover {
  background: var(--primary-hover);
}

.filter-bar {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-color);
  transition: border-color 0.3s;
}

.filter-tabs {
  display: flex;
  gap: 8px;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tab:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.filter-tab.active {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.filter-tab .count {
  padding: 2px 6px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.1);
  font-size: 11px;
}

.filter-tab.active .count {
  background: rgba(255, 255, 255, 0.2);
}

.tasks-content {
  padding: 20px;
  min-height: 300px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--text-muted);
  text-align: center;
}

.empty-state svg {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.empty-state span {
  font-size: 13px;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 1px solid var(--border-color);
}

.task-card:hover {
  box-shadow: var(--shadow);
}

.task-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 12px;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.running {
  background: rgba(24, 144, 255, 0.1);
  color: var(--primary-color);
}

.status-badge.completed {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.status-badge.failed {
  background: rgba(255, 77, 79, 0.1);
  color: var(--error-color);
}

.status-badge.pending {
  background: rgba(250, 173, 20, 0.1);
  color: var(--warning-color);
}

.status-badge.paused {
  background: rgba(114, 46, 209, 0.1);
  color: #722ed1;
}

.status-badge.error {
  background: rgba(255, 77, 79, 0.1);
  color: var(--error-color);
}

.status-badge.waiting-confirm {
  background: rgba(250, 173, 20, 0.15);
  color: #d48806;
}

.status-badge.waiting-assist {
  background: rgba(24, 144, 255, 0.15);
  color: #096dd9;
}

.task-prompt {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--card-bg);
  border-radius: 6px;
  line-height: 1.5;
}

.task-waiting-message {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(250, 173, 20, 0.1);
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
  color: var(--warning-color);
}

.task-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.task-result, .task-error {
  margin-top: 8px;
}

.task-result .label, .task-error .label {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 4px;
  display: block;
}

.result-content, .error-content {
  padding: 10px;
  background: var(--card-bg);
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-color);
  max-height: 100px;
  overflow-y: auto;
}

.error-content {
  color: var(--error-color);
}

.task-user-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  background: rgba(250, 173, 20, 0.05);
  border-radius: 6px;
  border: 1px dashed var(--warning-color);
}

.user-action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-action-btn.confirm {
  background: var(--success-color);
  color: #fff;
}

.user-action-btn.confirm:hover {
  opacity: 0.9;
}

.user-action-btn.cancel {
  background: var(--error-color);
  color: #fff;
}

.user-action-btn.cancel:hover {
  opacity: 0.9;
}

.user-action-btn.provided {
  background: var(--primary-color);
  color: #fff;
}

.user-action-btn.provided:hover {
  opacity: 0.9;
}

.user-action-btn.skip {
  background: var(--text-muted);
  color: #fff;
}

.user-action-btn.skip:hover {
  opacity: 0.9;
}

.task-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.action-btn.cancel:hover {
  border-color: var(--error-color);
  color: var(--error-color);
}

.action-btn.retry:hover {
  border-color: var(--warning-color);
  color: var(--warning-color);
}

.action-btn.resume:hover {
  border-color: var(--success-color);
  color: var(--success-color);
}

.tasks-stats {
  display: flex;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  gap: 24px;
  transition: border-color 0.3s;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-muted);
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
}

.stat-value.running {
  color: var(--primary-color);
}

.stat-value.completed {
  color: var(--success-color);
}

.stat-value.error {
  color: var(--error-color);
}

.stat-value.paused {
  color: #722ed1;
}

.stat-value.waiting {
  color: var(--warning-color);
}

.create-dialog, .task-detail-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-content {
  background: var(--card-bg);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.dialog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--bg-color);
  color: var(--text-color);
}

.dialog-body {
  padding: 20px;
  overflow-y: auto;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.form-item textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  color: var(--text-color);
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.3s, background-color 0.3s;
}

.form-item textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-item textarea::placeholder {
  color: var(--text-muted);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-cancel, .btn-submit {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
}

.btn-cancel:hover {
  border-color: var(--text-color);
  color: var(--text-color);
}

.btn-submit {
  border: none;
  background: var(--primary-color);
  color: #fff;
}

.btn-submit:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.detail-item {
  margin-bottom: 16px;
}

.detail-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
}

.detail-value {
  font-size: 14px;
  color: var(--text-color);
}

.detail-progress-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  border-radius: 6px;
  transition: background 0.3s ease;
}

.progress-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.detail-content {
  padding: 12px;
  background: var(--bg-color);
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-color);
  white-space: pre-wrap;
  word-break: break-word;
}

.detail-content.result {
  border-left: 3px solid var(--success-color);
}

.detail-content.error {
  border-left: 3px solid var(--error-color);
  color: var(--error-color);
}

.detail-content.warning {
  border-left: 3px solid var(--warning-color);
  color: var(--warning-color);
}

@media (max-width: 768px) {
  .header-actions {
    flex-direction: column;
  }
  
  .filter-tabs {
    flex-wrap: wrap;
  }
  
  .tasks-stats {
    flex-wrap: wrap;
  }
}
</style>
