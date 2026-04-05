<template>
  <div class="chat-view">
    <div class="chat-container">
      <div class="chat-header">
        <div class="chat-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8z"/>
            <path d="M17 17v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-8"/>
          </svg>
          <span>智能对话</span>
        </div>
        <div class="chat-actions">
          <button class="action-btn" @click="clearMessages" title="清空对话">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>
      
      <div class="messages" ref="messagesRef">
        <div v-if="messages.length === 0" class="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8z"/>
            <path d="M17 17v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-8"/>
          </svg>
          <p>开始一段新对话</p>
          <span>输入消息开始与AI助手交流</span>
        </div>
        
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message', msg.role]"
        >
          <div class="avatar">
            <svg v-if="msg.role === 'user'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
              <line x1="9" y1="9" x2="9.01" y2="9"/>
              <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
          </div>
          <div class="content">
            <div class="message-header">
              <span class="role-name">{{ msg.role === 'user' ? '你' : 'AI助手' }}</span>
              <span class="time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div class="text">{{ msg.content }}</div>
          </div>
        </div>
        
        <div v-if="loading" class="message assistant loading">
          <div class="avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
              <line x1="9" y1="9" x2="9.01" y2="9"/>
              <line x1="15" y1="9" x2="15.01" y2="9"/>
            </svg>
          </div>
          <div class="content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="input-area">
        <div class="quick-replies" v-if="!loading && messages.length > 0">
          <button 
            v-for="reply in quickReplies" 
            :key="reply.label" 
            class="quick-reply-btn"
            @click="sendQuickReply(reply.text)"
          >
            {{ reply.label }}
          </button>
        </div>
        <div class="input-wrapper">
          <div class="input-container">
            <textarea
              v-model="inputText"
              @keydown.enter.exact.prevent="sendMessage"
              @keydown.tab.prevent="handleTab"
              @keydown.up.prevent="navigateMenu(-1)"
              @keydown.down.prevent="navigateMenu(1)"
              placeholder="输入消息... (输入 / 查看命令)"
              rows="1"
              ref="textareaRef"
            />
            <SlashCommandMenu
              v-if="showSlashMenu"
              :filter="slashFilter"
              :selected-index="selectedMenuIndex"
              @select="executeCommand"
              @close="closeSlashMenu"
            />
          </div>
          <button @click="sendMessage" :disabled="loading || !inputText.trim()" class="send-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
        <div class="input-hint">
          <span v-if="isTyping" class="typing-status">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
            AI正在思考...
          </span>
          <span v-else>按 Enter 发送消息 | 输入 / 查看命令</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch, computed, defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  status?: 'sending' | 'sent' | 'error'
}

interface SlashCommand {
  id: string
  label: string
  icon: string
  action: () => void
}

const router = useRouter()
const messages = ref<Message[]>([])
const inputText = ref('')
const loading = ref(false)
const isTyping = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const showSlashMenu = ref(false)
const selectedMenuIndex = ref(0)
const mateModeEnabled = ref(false)

const slashFilter = computed(() => {
  const match = inputText.value.match(/^\/(\w*)/)
  return match ? match[1].toLowerCase() : ''
})

const slashCommands = computed<SlashCommand[]>(() => [
  {
    id: 'settings',
    label: '设置',
    icon: 'settings',
    action: openSettings
  },
  {
    id: 'newtopic',
    label: '新话题',
    icon: 'newtopic',
    action: startNewTopic
  },
  {
    id: 'mate',
    label: `Mate模式 ${mateModeEnabled.value ? '(已开启)' : '(已关闭)'}`,
    icon: 'mate',
    action: toggleMateMode
  }
])

const filteredCommands = computed(() => {
  if (!slashFilter.value) return slashCommands.value
  return slashCommands.value.filter(cmd => 
    cmd.id.startsWith(slashFilter.value) || 
    cmd.label.includes(slashFilter.value)
  )
})

const createDocument = async (type: 'word' | 'excel' | 'ppt') => {
  try {
    const response = await axios.post('/api/document/create', {
      document_type: type,
      name: `新建${type === 'word' ? '文档' : type === 'excel' ? '表格' : '演示文稿'}`
    })
    const documentId = response.data.document_id
    router.push(`/document/${documentId}`)
  } catch (error) {
    console.error('Create document error:', error)
  }
}

const SlashCommandMenu = defineComponent({
  name: 'SlashCommandMenu',
  props: {
    filter: { type: String, default: '' },
    selectedIndex: { type: Number, default: 0 }
  },
  emits: ['select', 'close'],
  setup(props, { emit }) {
    const commands = computed(() => {
      const allCommands = [
        { id: 'settings', label: '设置', icon: 'settings' },
        { id: 'newtopic', label: '新话题', icon: 'newtopic' },
        { id: 'mate', label: `Mate模式 ${mateModeEnabled.value ? '(已开启)' : '(已关闭)'}`, icon: 'mate' }
      ]
      if (!props.filter) return allCommands
      return allCommands.filter(cmd => 
        cmd.id.startsWith(props.filter) || 
        cmd.label.includes(props.filter)
      )
    })

    const getIconSvg = (icon: string) => {
      const icons: Record<string, string> = {
        settings: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>`,
        newtopic: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>`,
        mate: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <circle cx="19" cy="5" r="2"/>
          <circle cx="5" cy="19" r="2"/>
          <path d="M10.5 9.5L7 6M14.5 14.5L18 18"/>
        </svg>`
      }
      return icons[icon] || ''
    }

    const docIcons = {
      ppt: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="18" height="18" rx="2" fill="#FF6B35"/>
        <text x="12" y="15" text-anchor="middle" fill="white" font-size="8" font-weight="bold">PPT</text>
      </svg>`,
      word: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="18" height="18" rx="2" fill="#2B579A"/>
        <text x="12" y="15" text-anchor="middle" fill="white" font-size="8" font-weight="bold">W</text>
      </svg>`,
      excel: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="3" width="18" height="18" rx="2" fill="#217346"/>
        <text x="12" y="15" text-anchor="middle" fill="white" font-size="8" font-weight="bold">X</text>
      </svg>`
    }

    return () => {
      const children: any[] = []
      
      children.push(h('div', { class: 'doc-icons-row' }, [
        h('div', {
          class: 'doc-icon-btn ppt',
          onClick: (e: Event) => {
            e.stopPropagation()
            createDocument('ppt')
            emit('close')
          }
        }, [
          h('span', { class: 'doc-icon', innerHTML: docIcons.ppt }),
          h('span', { class: 'doc-icon-label' }, 'PPT')
        ]),
        h('div', {
          class: 'doc-icon-btn word',
          onClick: (e: Event) => {
            e.stopPropagation()
            createDocument('word')
            emit('close')
          }
        }, [
          h('span', { class: 'doc-icon', innerHTML: docIcons.word }),
          h('span', { class: 'doc-icon-label' }, 'Word')
        ]),
        h('div', {
          class: 'doc-icon-btn excel',
          onClick: (e: Event) => {
            e.stopPropagation()
            createDocument('excel')
            emit('close')
          }
        }, [
          h('span', { class: 'doc-icon', innerHTML: docIcons.excel }),
          h('span', { class: 'doc-icon-label' }, 'Excel')
        ])
      ]))

      if (commands.value.length === 0) {
        children.push(h('div', { class: 'slash-menu-empty' }, '没有匹配的命令'))
      } else {
        children.push(h('div', { class: 'slash-menu-commands' },
          commands.value.map((cmd, index) => 
            h('div', {
              class: ['slash-menu-item', { selected: index === props.selectedIndex }],
              onClick: () => emit('select', cmd.id),
              key: cmd.id
            }, [
              h('span', { 
                class: 'slash-menu-icon',
                innerHTML: getIconSvg(cmd.icon)
              }),
              h('span', { class: 'slash-menu-label' }, cmd.label),
              h('span', { class: 'slash-menu-hint' }, `/${cmd.id}`)
            ])
          )
        ))
      }

      return h('div', { class: 'slash-menu' }, children)
    }
  }
})

const quickReplies = [
  { label: '继续', text: '请继续' },
  { label: '详细说明', text: '请详细说明' },
  { label: '总结', text: '请总结一下' },
  { label: '代码示例', text: '请给出代码示例' }
]

watch(inputText, (newValue) => {
  if (newValue.startsWith('/')) {
    showSlashMenu.value = true
    selectedMenuIndex.value = 0
  } else {
    showSlashMenu.value = false
  }
})

const handleTab = () => {
  if (showSlashMenu.value && filteredCommands.value.length > 0) {
    const selectedCommand = filteredCommands.value[selectedMenuIndex.value]
    if (selectedCommand) {
      inputText.value = `/${selectedCommand.id} `
      showSlashMenu.value = false
    }
  }
}

const navigateMenu = (direction: number) => {
  if (!showSlashMenu.value) return
  const maxIndex = filteredCommands.value.length - 1
  selectedMenuIndex.value = Math.max(0, Math.min(maxIndex, selectedMenuIndex.value + direction))
}

const executeCommand = (commandId: string) => {
  const command = slashCommands.value.find(cmd => cmd.id === commandId)
  if (command) {
    command.action()
  }
  inputText.value = ''
  showSlashMenu.value = false
}

const closeSlashMenu = () => {
  showSlashMenu.value = false
}

const openSettings = () => {
  router.push('/config')
}

const startNewTopic = () => {
  messages.value = []
  if (textareaRef.value) {
    textareaRef.value.focus()
  }
}

const toggleMateMode = async () => {
  try {
    mateModeEnabled.value = !mateModeEnabled.value
    await axios.post('/api/mate/mode', {
      enabled: mateModeEnabled.value
    })
  } catch (error) {
    console.error('Toggle mate mode error:', error)
    mateModeEnabled.value = !mateModeEnabled.value
  }
}

const loadMateModeStatus = async () => {
  try {
    const response = await axios.get('/api/mate/status')
    mateModeEnabled.value = response.data.enabled || false
  } catch (error) {
    console.error('Load mate mode status error:', error)
  }
}

const sendMessage = async () => {
  if (showSlashMenu.value) {
    if (filteredCommands.value.length > 0) {
      executeCommand(filteredCommands.value[selectedMenuIndex.value].id)
    }
    return
  }
  
  if (!inputText.value.trim() || loading.value) return
  
  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputText.value,
    timestamp: Date.now(),
    status: 'sending'
  }
  
  messages.value.push(userMessage)
  const text = inputText.value
  inputText.value = ''
  
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
  
  loading.value = true
  isTyping.value = true
  
  try {
    const response = await axios.post('/api/chat', {
      message: text,
      chat_id: 'web',
      platform: 'web'
    })
    
    const index = messages.value.findIndex(m => m.id === userMessage.id)
    if (index !== -1) {
      messages.value[index].status = 'sent'
    }
    
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.data.response,
      timestamp: Date.now()
    }
    
    messages.value.push(assistantMessage)
  } catch (error) {
    console.error('Send message error:', error)
    const index = messages.value.findIndex(m => m.id === userMessage.id)
    if (index !== -1) {
      messages.value[index].status = 'error'
    }
    const errorMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后重试。',
      timestamp: Date.now()
    }
    messages.value.push(errorMessage)
  } finally {
    loading.value = false
    isTyping.value = false
  }
  
  await nextTick()
  scrollToBottom()
}

const sendQuickReply = (text: string) => {
  inputText.value = text
  sendMessage()
}

const clearMessages = () => {
  messages.value = []
}

const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const autoResize = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 120) + 'px'
  }
}

watch(inputText, () => {
  nextTick(autoResize)
})

onMounted(() => {
  if (textareaRef.value) {
    textareaRef.value.focus()
  }
  loadMateModeStatus()
})
</script>

<style scoped>
.chat-view {
  height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: background-color 0.3s, box-shadow 0.3s;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: border-color 0.3s;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: var(--bg-color);
  color: var(--primary-color);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
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

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--primary-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .avatar {
  background: var(--success-color);
}

.content {
  max-width: 70%;
  min-width: 100px;
}

.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 0 4px;
}

.message.user .message-header {
  flex-direction: row-reverse;
}

.role-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.time {
  font-size: 11px;
  color: var(--text-muted);
}

.text {
  padding: 12px 16px;
  border-radius: 12px;
  background: var(--bg-color);
  line-height: 1.6;
  font-size: 14px;
  color: var(--text-color);
  transition: background-color 0.3s;
}

.message.user .text {
  background: var(--primary-color);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.assistant .text {
  border-bottom-left-radius: 4px;
}

.loading .content {
  display: flex;
  align-items: center;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  transition: border-color 0.3s;
}

.quick-replies {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.quick-reply-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-reply-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(24, 144, 255, 0.05);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-container {
  flex: 1;
  position: relative;
  background: var(--bg-color);
  border-radius: 12px;
  transition: background-color 0.3s;
}

textarea {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-color);
  font-family: inherit;
  max-height: 120px;
}

textarea::placeholder {
  color: var(--text-muted);
}

textarea:focus {
  outline: none;
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: var(--primary-color);
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: scale(1.05);
}

.send-btn:disabled {
  background: var(--border-color);
  cursor: not-allowed;
}

.input-hint {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}

.typing-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--primary-color);
}

.typing-status svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.slash-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--shadow-hover);
  margin-bottom: 4px;
  max-height: 280px;
  overflow-y: auto;
  z-index: 10;
}

.doc-icons-row {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-color);
}

.doc-icon-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.doc-icon-btn:hover {
  background: var(--card-bg);
  transform: translateY(-2px);
}

.doc-icon-btn.ppt:hover {
  box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
}

.doc-icon-btn.word:hover {
  box-shadow: 0 4px 12px rgba(43, 87, 154, 0.3);
}

.doc-icon-btn.excel:hover {
  box-shadow: 0 4px 12px rgba(33, 115, 70, 0.3);
}

.doc-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.doc-icon-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
}

.slash-menu-commands {
  max-height: 180px;
  overflow-y: auto;
}

.slash-menu-empty {
  padding: 12px 16px;
  color: var(--text-muted);
  font-size: 13px;
  text-align: center;
}

.slash-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.slash-menu-item:hover,
.slash-menu-item.selected {
  background: var(--bg-color);
}

.slash-menu-item.selected {
  background: rgba(24, 144, 255, 0.1);
}

.slash-menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.slash-menu-item:hover .slash-menu-icon,
.slash-menu-item.selected .slash-menu-icon {
  color: var(--primary-color);
}

.slash-menu-label {
  flex: 1;
  font-size: 14px;
  color: var(--text-color);
}

.slash-menu-hint {
  font-size: 12px;
  color: var(--text-muted);
  font-family: monospace;
}

@media (max-width: 768px) {
  .chat-view {
    height: calc(100vh - 140px);
  }
  
  .content {
    max-width: 85%;
  }
  
  .messages {
    padding: 12px;
  }
  
  .input-area {
    padding: 12px;
  }
}
</style>
