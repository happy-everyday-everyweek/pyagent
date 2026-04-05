<template>
  <div class="video-editor">
    <div class="editor-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <div class="project-info">
          <input v-model="projectName" class="project-name-input" @blur="saveProjectName" placeholder="未命名项目" />
        </div>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="saveProject" :disabled="saving">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
          </svg>
          <span>{{ saving ? '保存中...' : '保存' }}</span>
        </button>
        <button class="action-btn primary" @click="exportProject">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          <span>导出</span>
        </button>
      </div>
    </div>
    
    <div class="editor-container">
      <div class="editor-main">
        <div class="preview-area">
          <div class="preview-wrapper">
            <video ref="previewVideo" class="preview-video" @timeupdate="onTimeUpdate"></video>
            <div class="preview-controls">
              <button class="play-btn" @click="togglePlay">
                <svg v-if="!isPlaying" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 3 19 12 5 21 5 3"/>
                </svg>
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="4" width="4" height="16"/>
                  <rect x="14" y="4" width="4" height="16"/>
                </svg>
              </button>
              <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
            </div>
          </div>
        </div>
        
        <div class="timeline-area">
          <div class="timeline-toolbar">
            <button class="toolbar-btn" @click="addVideoTrack" title="添加视频轨道">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
              </svg>
            </button>
            <button class="toolbar-btn" @click="addAudioTrack" title="添加音频轨道">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18V5l12-2v13"/>
                <circle cx="6" cy="18" r="3"/>
                <circle cx="18" cy="16" r="3"/>
              </svg>
            </button>
            <button class="toolbar-btn" @click="addTextTrack" title="添加字幕轨道">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="4 7 4 4 20 4 20 7"/>
                <line x1="9" y1="20" x2="15" y2="20"/>
                <line x1="12" y1="4" x2="12" y2="20"/>
              </svg>
            </button>
            <div class="toolbar-divider"></div>
            <button class="toolbar-btn" @click="splitClip" title="分割">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="2" x2="12" y2="22"/>
                <polyline points="8 6 12 2 16 6"/>
                <polyline points="8 18 12 22 16 18"/>
              </svg>
            </button>
            <button class="toolbar-btn" @click="deleteSelected" title="删除">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
            <div class="toolbar-divider"></div>
            <button class="toolbar-btn" @click="zoomIn" title="放大">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                <line x1="11" y1="8" x2="11" y2="14"/>
                <line x1="8" y1="11" x2="14" y2="11"/>
              </svg>
            </button>
            <button class="toolbar-btn" @click="zoomOut" title="缩小">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                <line x1="8" y1="11" x2="14" y2="11"/>
              </svg>
            </button>
          </div>
          
          <div class="timeline-scroll">
            <div class="timeline-ruler" :style="{ width: timelineWidth + 'px' }">
              <div v-for="tick in timelineTicks" :key="tick" class="ruler-tick" :style="{ left: (tick / duration * timelineWidth) + 'px' }">
                <span class="tick-label">{{ formatTime(tick) }}</span>
              </div>
            </div>
            <div class="timeline-tracks" :style="{ width: timelineWidth + 'px' }">
              <div v-for="track in tracks" :key="track.id" class="track" :class="track.type">
                <div class="track-header">
                  <span class="track-name">{{ track.name }}</span>
                  <button class="track-btn" @click="toggleTrackMute(track)">
                    <svg v-if="!track.muted" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    </svg>
                    <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                      <line x1="23" y1="9" x2="17" y2="15"/>
                      <line x1="17" y1="9" x2="23" y2="15"/>
                    </svg>
                  </button>
                </div>
                <div class="track-content">
                  <div v-for="element in track.elements" :key="element.id" 
                       class="element" 
                       :class="{ selected: selectedElement === element.id }"
                       :style="{ left: (element.start_time / duration * timelineWidth) + 'px', width: (element.duration / duration * timelineWidth) + 'px' }"
                       @click="selectElement(element.id)">
                    <span class="element-name">{{ element.name }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="playhead" :style="{ left: (currentTime / duration * timelineWidth) + 'px' }"></div>
          </div>
        </div>
      </div>
      
      <div class="assets-panel">
        <div class="panel-header">
          <span class="panel-title">素材库</span>
          <button class="add-btn" @click="importMedia">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>
        </div>
        <div class="assets-list">
          <div v-for="asset in assets" :key="asset.id" class="asset-item" @click="addToTimeline(asset)">
            <div class="asset-thumb">
              <svg v-if="asset.type === 'video'" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
              <svg v-else-if="asset.type === 'audio'" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M9 18V5l12-2v13"/>
              </svg>
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="18" height="18" rx="2"/>
              </svg>
            </div>
            <div class="asset-info">
              <span class="asset-name">{{ asset.name }}</span>
              <span class="asset-duration">{{ formatTime(asset.duration) }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="ai-panel">
        <div class="panel-header">
          <span class="panel-title">AI助手</span>
        </div>
        <div class="ai-actions">
          <button class="ai-btn" @click="aiAutoEdit">智能剪辑</button>
          <button class="ai-btn" @click="aiGenerateSubtitles">生成字幕</button>
          <button class="ai-btn" @click="aiRecommendEffects">推荐特效</button>
        </div>
        <div class="ai-chat">
          <div v-for="msg in aiMessages" :key="msg.id" :class="['ai-msg', msg.role]">
            {{ msg.content }}
          </div>
        </div>
        <div class="ai-input-row">
          <input v-model="aiInput" @keydown.enter="sendAiMessage" class="ai-input" placeholder="询问AI..." />
          <button class="ai-send" @click="sendAiMessage">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

interface TrackElement {
  id: string
  name: string
  start_time: number
  duration: number
}

interface Track {
  id: string
  type: 'video' | 'audio' | 'text'
  name: string
  elements: TrackElement[]
  muted: boolean
}

interface Asset {
  id: string
  name: string
  type: 'video' | 'audio' | 'image'
  duration: number
}

interface AiMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.id as string)
const projectName = ref('')
const saving = ref(false)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(60)
const zoom = ref(1)
const tracks = ref<Track[]>([])
const assets = ref<Asset[]>([])
const selectedElement = ref<string | null>(null)
const aiMessages = ref<AiMessage[]>([])
const aiInput = ref('')
const previewVideo = ref<HTMLVideoElement | null>(null)

const timelineWidth = computed(() => duration.value * 10 * zoom.value)
const timelineTicks = computed(() => {
  const ticks: number[] = []
  const step = 5
  for (let i = 0; i <= duration.value; i += step) {
    ticks.push(i)
  }
  return ticks
})

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const loadProject = async () => {
  try {
    const response = await axios.get(`/api/video/${projectId.value}`)
    const project = response.data
    projectName.value = project.name
    duration.value = project.duration || 60
    if (project.tracks) {
      tracks.value = project.tracks
    }
  } catch (error) {
    console.error('Load project error:', error)
  }
}

const saveProject = async () => {
  saving.value = true
  try {
    await axios.put(`/api/video/${projectId.value}`, {
      name: projectName.value,
      tracks: tracks.value
    })
  } catch (error) {
    console.error('Save project error:', error)
  } finally {
    saving.value = false
  }
}

const saveProjectName = async () => {
  try {
    await axios.put(`/api/video/${projectId.value}`, { name: projectName.value })
  } catch (error) {
    console.error('Save project name error:', error)
  }
}

const exportProject = async () => {
  try {
    const response = await axios.post(`/api/video/${projectId.value}/export`, {
      format: 'mp4',
      quality: 'high'
    })
    if (response.data.file_path) {
      window.open(response.data.file_path, '_blank')
    }
  } catch (error) {
    console.error('Export project error:', error)
  }
}

const togglePlay = () => {
  isPlaying.value = !isPlaying.value
  if (previewVideo.value) {
    if (isPlaying.value) {
      previewVideo.value.play()
    } else {
      previewVideo.value.pause()
    }
  }
}

const onTimeUpdate = () => {
  if (previewVideo.value) {
    currentTime.value = previewVideo.value.currentTime
  }
}

const addVideoTrack = () => {
  tracks.value.push({
    id: `track_${Date.now()}`,
    type: 'video',
    name: `视频轨道 ${tracks.value.filter(t => t.type === 'video').length + 1}`,
    elements: [],
    muted: false
  })
}

const addAudioTrack = () => {
  tracks.value.push({
    id: `track_${Date.now()}`,
    type: 'audio',
    name: `音频轨道 ${tracks.value.filter(t => t.type === 'audio').length + 1}`,
    elements: [],
    muted: false
  })
}

const addTextTrack = () => {
  tracks.value.push({
    id: `track_${Date.now()}`,
    type: 'text',
    name: `字幕轨道 ${tracks.value.filter(t => t.type === 'text').length + 1}`,
    elements: [],
    muted: false
  })
}

const toggleTrackMute = (track: Track) => {
  track.muted = !track.muted
}

const selectElement = (id: string) => {
  selectedElement.value = id
}

const splitClip = () => {
  if (!selectedElement.value) {
    console.warn('请先选择要分割的片段')
    return
  }

  for (const track of tracks.value) {
    const elementIndex = track.elements.findIndex(e => e.id === selectedElement.value)
    if (elementIndex === -1) continue

    const element = track.elements[elementIndex]
    const elementEnd = element.start_time + element.duration
    const splitTime = currentTime.value

    if (splitTime <= element.start_time || splitTime >= elementEnd) {
      console.warn('当前时间点不在选中片段范围内')
      return
    }

    const firstPartDuration = splitTime - element.start_time
    const secondPartDuration = elementEnd - splitTime

    const firstPart: TrackElement = {
      id: `element_${Date.now()}`,
      name: `${element.name} (1)`,
      start_time: element.start_time,
      duration: firstPartDuration
    }

    const secondPart: TrackElement = {
      id: `element_${Date.now() + 1}`,
      name: `${element.name} (2)`,
      start_time: splitTime,
      duration: secondPartDuration
    }

    track.elements.splice(elementIndex, 1, firstPart, secondPart)

    selectedElement.value = null

    console.log(`片段已分割: ${element.name} -> ${firstPart.name} + ${secondPart.name}`)
    return
  }

  console.warn('未找到选中的片段')
}

const deleteSelected = () => {
  if (!selectedElement.value) return
  for (const track of tracks.value) {
    const index = track.elements.findIndex(e => e.id === selectedElement.value)
    if (index !== -1) {
      track.elements.splice(index, 1)
      selectedElement.value = null
      break
    }
  }
}

const zoomIn = () => {
  zoom.value = Math.min(zoom.value * 1.2, 5)
}

const zoomOut = () => {
  zoom.value = Math.max(zoom.value / 1.2, 0.2)
}

const importMedia = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'video/*,audio/*,image/*'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      assets.value.push({
        id: `asset_${Date.now()}`,
        name: file.name,
        type: file.type.startsWith('video') ? 'video' : file.type.startsWith('audio') ? 'audio' : 'image',
        duration: 10
      })
    }
  }
  input.click()
}

const addToTimeline = (asset: Asset) => {
  const trackType = asset.type === 'audio' ? 'audio' : 'video'
  let track = tracks.value.find(t => t.type === trackType)
  if (!track) {
    track = {
      id: `track_${Date.now()}`,
      type: trackType,
      name: `${trackType === 'audio' ? '音频' : '视频'}轨道 1`,
      elements: [],
      muted: false
    }
    tracks.value.push(track)
  }
  const lastElement = track.elements[track.elements.length - 1]
  const startTime = lastElement ? lastElement.start_time + lastElement.duration : 0
  track.elements.push({
    id: `element_${Date.now()}`,
    name: asset.name,
    start_time: startTime,
    duration: asset.duration
  })
}

const aiAutoEdit = async () => {
  aiMessages.value.push({ id: Date.now().toString(), role: 'user', content: '请帮我智能剪辑' })
  try {
    const response = await axios.post(`/api/video/${projectId.value}/ai-edit`, { action: 'auto_edit' })
    aiMessages.value.push({ id: (Date.now() + 1).toString(), role: 'assistant', content: response.data.result })
  } catch (error) {
    console.error('AI auto edit error:', error)
  }
}

const aiGenerateSubtitles = async () => {
  aiMessages.value.push({ id: Date.now().toString(), role: 'user', content: '请生成字幕' })
  try {
    const response = await axios.post(`/api/video/${projectId.value}/ai-edit`, { action: 'generate_subtitles' })
    aiMessages.value.push({ id: (Date.now() + 1).toString(), role: 'assistant', content: response.data.result })
  } catch (error) {
    console.error('AI generate subtitles error:', error)
  }
}

const aiRecommendEffects = async () => {
  aiMessages.value.push({ id: Date.now().toString(), role: 'user', content: '请推荐特效' })
  try {
    const response = await axios.post(`/api/video/${projectId.value}/ai-edit`, { action: 'recommend_effects' })
    aiMessages.value.push({ id: (Date.now() + 1).toString(), role: 'assistant', content: response.data.result })
  } catch (error) {
    console.error('AI recommend effects error:', error)
  }
}

const sendAiMessage = async () => {
  if (!aiInput.value.trim()) return
  const msg = aiInput.value
  aiMessages.value.push({ id: Date.now().toString(), role: 'user', content: msg })
  aiInput.value = ''
  try {
    const response = await axios.post('/api/chat', { message: msg, context: 'video_editor', project_id: projectId.value })
    aiMessages.value.push({ id: (Date.now() + 1).toString(), role: 'assistant', content: response.data.response })
  } catch (error) {
    console.error('AI chat error:', error)
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  loadProject()
})
</script>

<style scoped>
.video-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
  color: #fff;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #2a2a2a;
  border-bottom: 1px solid #3a3a3a;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #aaa;
  cursor: pointer;
}

.back-btn:hover {
  background: #3a3a3a;
  color: #fff;
}

.project-name-input {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: transparent;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  min-width: 150px;
}

.project-name-input:focus {
  outline: none;
  background: #3a3a3a;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid #3a3a3a;
  border-radius: 6px;
  background: transparent;
  color: #aaa;
  font-size: 13px;
  cursor: pointer;
}

.action-btn:hover {
  background: #3a3a3a;
  color: #fff;
}

.action-btn.primary {
  background: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

.action-btn.primary:hover {
  background: #40a9ff;
}

.editor-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-area {
  height: 240px;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-video {
  max-width: 100%;
  max-height: 100%;
}

.preview-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.7);
}

.play-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #1890ff;
  color: #fff;
  cursor: pointer;
}

.time-display {
  font-size: 12px;
  color: #aaa;
  font-family: monospace;
}

.timeline-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #2a2a2a;
  overflow: hidden;
}

.timeline-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: #252525;
  border-bottom: 1px solid #3a3a3a;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #aaa;
  cursor: pointer;
}

.toolbar-btn:hover {
  background: #3a3a3a;
  color: #fff;
}

.toolbar-divider {
  width: 1px;
  height: 16px;
  background: #3a3a3a;
  margin: 0 4px;
}

.timeline-scroll {
  flex: 1;
  overflow-x: auto;
  overflow-y: auto;
  position: relative;
}

.timeline-ruler {
  height: 24px;
  background: #252525;
  position: relative;
}

.ruler-tick {
  position: absolute;
  top: 0;
  height: 100%;
  border-left: 1px solid #3a3a3a;
  padding-left: 4px;
}

.tick-label {
  font-size: 10px;
  color: #666;
}

.timeline-tracks {
  position: relative;
}

.track {
  height: 48px;
  display: flex;
  border-bottom: 1px solid #3a3a3a;
}

.track.video {
  background: #1e3a5f;
}

.track.audio {
  background: #1e5f3a;
}

.track.text {
  background: #5f3a1e;
}

.track-header {
  width: 120px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px;
  background: rgba(0, 0, 0, 0.3);
  flex-shrink: 0;
}

.track-name {
  font-size: 11px;
  color: #aaa;
}

.track-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #aaa;
  cursor: pointer;
}

.track-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.track-content {
  flex: 1;
  position: relative;
}

.element {
  position: absolute;
  top: 4px;
  bottom: 4px;
  background: rgba(24, 144, 255, 0.8);
  border-radius: 4px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  cursor: pointer;
}

.element:hover {
  background: rgba(24, 144, 255, 1);
}

.element.selected {
  outline: 2px solid #fff;
}

.element-name {
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ff4d4f;
  z-index: 10;
  pointer-events: none;
}

.assets-panel {
  width: 200px;
  background: #2a2a2a;
  border-left: 1px solid #3a3a3a;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid #3a3a3a;
}

.panel-title {
  font-size: 13px;
  font-weight: 500;
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #aaa;
  cursor: pointer;
}

.add-btn:hover {
  background: #3a3a3a;
  color: #fff;
}

.assets-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.asset-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
}

.asset-item:hover {
  background: #3a3a3a;
}

.asset-thumb {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3a3a3a;
  border-radius: 4px;
  color: #666;
}

.asset-info {
  flex: 1;
  min-width: 0;
}

.asset-name {
  display: block;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asset-duration {
  display: block;
  font-size: 10px;
  color: #666;
}

.ai-panel {
  width: 240px;
  background: #2a2a2a;
  border-left: 1px solid #3a3a3a;
  display: flex;
  flex-direction: column;
}

.ai-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
}

.ai-btn {
  padding: 8px 12px;
  border: 1px solid #3a3a3a;
  border-radius: 6px;
  background: transparent;
  color: #aaa;
  font-size: 12px;
  cursor: pointer;
  text-align: left;
}

.ai-btn:hover {
  background: #3a3a3a;
  color: #fff;
  border-color: #1890ff;
}

.ai-chat {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.ai-msg {
  margin-bottom: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.ai-msg.user {
  background: #1890ff;
  color: #fff;
  margin-left: 24px;
}

.ai-msg.assistant {
  background: #3a3a3a;
  color: #fff;
  margin-right: 24px;
}

.ai-input-row {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #3a3a3a;
}

.ai-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #3a3a3a;
  border-radius: 6px;
  background: #1a1a1a;
  color: #fff;
  font-size: 12px;
}

.ai-input:focus {
  outline: none;
  border-color: #1890ff;
}

.ai-send {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background: #1890ff;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
}

.ai-send:hover {
  background: #40a9ff;
}
</style>
