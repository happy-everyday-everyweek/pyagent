<template>
  <div class="document-editor">
    <div class="editor-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </button>
        <div class="doc-info">
          <input 
            v-model="documentName" 
            class="doc-name-input"
            @blur="saveDocumentName"
            placeholder="未命名文档"
          />
          <span class="doc-type-badge" :class="documentType">{{ docTypeLabel }}</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="action-btn" @click="saveDocument" :disabled="saving">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
            <polyline points="17 21 17 13 7 13 7 21"/>
            <polyline points="7 3 7 8 15 8"/>
          </svg>
          <span>{{ saving ? '保存中...' : '保存' }}</span>
        </button>
        <button class="action-btn primary" @click="exportDocument">
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
        <div class="editor-toolbar">
          <button class="toolbar-btn" @click="formatText('bold')" title="粗体">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/>
              <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/>
            </svg>
          </button>
          <button class="toolbar-btn" @click="formatText('italic')" title="斜体">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="19" y1="4" x2="10" y2="4"/>
              <line x1="14" y1="20" x2="5" y2="20"/>
              <line x1="15" y1="4" x2="9" y2="20"/>
            </svg>
          </button>
          <button class="toolbar-btn" @click="formatText('underline')" title="下划线">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M6 3v7a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"/>
              <line x1="4" y1="21" x2="20" y2="21"/>
            </svg>
          </button>
          <div class="toolbar-divider"></div>
          <button class="toolbar-btn" @click="formatText('align-left')" title="左对齐">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="17" y1="10" x2="3" y2="10"/>
              <line x1="21" y1="6" x2="3" y2="6"/>
              <line x1="21" y1="14" x2="3" y2="14"/>
              <line x1="17" y1="18" x2="3" y2="18"/>
            </svg>
          </button>
          <button class="toolbar-btn" @click="formatText('align-center')" title="居中">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="10" x2="6" y2="10"/>
              <line x1="21" y1="6" x2="3" y2="6"/>
              <line x1="21" y1="14" x2="3" y2="14"/>
              <line x1="18" y1="18" x2="6" y2="18"/>
            </svg>
          </button>
          <button class="toolbar-btn" @click="formatText('align-right')" title="右对齐">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="21" y1="10" x2="7" y2="10"/>
              <line x1="21" y1="6" x2="3" y2="6"/>
              <line x1="21" y1="14" x2="3" y2="14"/>
              <line x1="21" y1="18" x2="7" y2="18"/>
            </svg>
          </button>
          <div class="toolbar-divider"></div>
          <button class="toolbar-btn" @click="insertImage" title="插入图片">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
          </button>
          <button class="toolbar-btn" @click="insertTable" title="插入表格">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="3" y1="15" x2="21" y2="15"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
              <line x1="15" y1="3" x2="15" y2="21"/>
            </svg>
          </button>
        </div>
        
        <div class="editor-content" ref="editorRef">
          <div 
            class="editor-area" 
            contenteditable="true"
            @input="onContentChange"
            @paste="onPaste"
            ref="contentArea"
          ></div>
        </div>
      </div>
      
      <div class="ai-assistant-panel" :class="{ collapsed: aiPanelCollapsed }">
        <div class="ai-panel-header">
          <span class="ai-panel-title">AI助手</span>
          <button class="collapse-btn" @click="aiPanelCollapsed = !aiPanelCollapsed">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline :points="aiPanelCollapsed ? '9 18 15 12 9 6' : '15 18 9 12 15 6'"/>
            </svg>
          </button>
        </div>
        <div class="ai-panel-content" v-if="!aiPanelCollapsed">
          <div class="ai-quick-actions">
            <button class="ai-action-btn" @click="aiAssist('rewrite')">改写</button>
            <button class="ai-action-btn" @click="aiAssist('expand')">扩写</button>
            <button class="ai-action-btn" @click="aiAssist('summarize')">缩写</button>
            <button class="ai-action-btn" @click="aiAssist('translate')">翻译</button>
            <button class="ai-action-btn" @click="aiAssist('proofread')">校对</button>
          </div>
          <div class="ai-chat-area" ref="aiChatRef">
            <div v-for="msg in aiMessages" :key="msg.id" :class="['ai-message', msg.role]">
              <div class="ai-message-content">{{ msg.content }}</div>
            </div>
          </div>
          <div class="ai-input-area">
            <input 
              v-model="aiInput" 
              @keydown.enter="sendAiMessage"
              placeholder="询问AI..."
              class="ai-input"
            />
            <button class="ai-send-btn" @click="sendAiMessage">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

interface AiMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const route = useRoute()
const router = useRouter()

const documentId = computed(() => route.params.id as string)
const documentName = ref('')
const documentType = ref<'word' | 'excel' | 'ppt'>('word')
const saving = ref(false)
const aiPanelCollapsed = ref(false)
const aiInput = ref('')
const aiMessages = ref<AiMessage[]>([])
const editorRef = ref<HTMLElement | null>(null)
const contentArea = ref<HTMLElement | null>(null)
const aiChatRef = ref<HTMLElement | null>(null)

const docTypeLabel = computed(() => {
  const labels: Record<string, string> = {
    word: 'Word文档',
    excel: 'Excel表格',
    ppt: 'PPT演示'
  }
  return labels[documentType.value] || '文档'
})

const loadDocument = async () => {
  try {
    const response = await axios.get(`/api/document/${documentId.value}`)
    const doc = response.data
    documentName.value = doc.name
    documentType.value = doc.document_type
    if (contentArea.value && doc.content) {
      contentArea.value.innerHTML = doc.content
    }
  } catch (error) {
    console.error('Load document error:', error)
  }
}

const saveDocument = async () => {
  saving.value = true
  try {
    await axios.put(`/api/document/${documentId.value}`, {
      name: documentName.value,
      content: contentArea.value?.innerHTML || ''
    })
  } catch (error) {
    console.error('Save document error:', error)
  } finally {
    saving.value = false
  }
}

const saveDocumentName = async () => {
  try {
    await axios.put(`/api/document/${documentId.value}`, {
      name: documentName.value
    })
  } catch (error) {
    console.error('Save document name error:', error)
  }
}

const exportDocument = async () => {
  try {
    const response = await axios.post(`/api/document/${documentId.value}/export`, {
      format: documentType.value === 'word' ? 'docx' : documentType.value === 'excel' ? 'xlsx' : 'pptx'
    })
    if (response.data.file_path) {
      window.open(response.data.file_path, '_blank')
    }
  } catch (error) {
    console.error('Export document error:', error)
  }
}

const formatText = (command: string) => {
  document.execCommand(command, false)
}

const insertImage = () => {
  const url = prompt('输入图片URL:')
  if (url) {
    document.execCommand('insertImage', false, url)
  }
}

const insertTable = () => {
  const rows = prompt('行数:', '3')
  const cols = prompt('列数:', '3')
  if (rows && cols) {
    let table = '<table style="border-collapse: collapse; width: 100%;">'
    for (let i = 0; i < parseInt(rows); i++) {
      table += '<tr>'
      for (let j = 0; j < parseInt(cols); j++) {
        table += '<td style="border: 1px solid #ddd; padding: 8px;">&nbsp;</td>'
      }
      table += '</tr>'
    }
    table += '</table>'
    document.execCommand('insertHTML', false, table)
  }
}

const onContentChange = () => {
}

const onPaste = (e: ClipboardEvent) => {
  e.preventDefault()
  const text = e.clipboardData?.getData('text/plain')
  if (text) {
    document.execCommand('insertText', false, text)
  }
}

const aiAssist = async (action: string) => {
  const selection = window.getSelection()?.toString()
  if (!selection) {
    aiMessages.value.push({
      id: Date.now().toString(),
      role: 'assistant',
      content: '请先选择要处理的文本'
    })
    return
  }
  
  aiMessages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: `${action}: ${selection.substring(0, 50)}...`
  })
  
  try {
    const response = await axios.post(`/api/document/${documentId.value}/ai-assist`, {
      action,
      text: selection
    })
    aiMessages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.data.result
    })
  } catch (error) {
    console.error('AI assist error:', error)
  }
}

const sendAiMessage = async () => {
  if (!aiInput.value.trim()) return
  
  const userMessage = aiInput.value
  aiMessages.value.push({
    id: Date.now().toString(),
    role: 'user',
    content: userMessage
  })
  aiInput.value = ''
  
  try {
    const response = await axios.post('/api/chat', {
      message: userMessage,
      context: 'document_editor',
      document_id: documentId.value
    })
    aiMessages.value.push({
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.data.response
    })
  } catch (error) {
    console.error('AI chat error:', error)
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  loadDocument()
})
</script>

<style scoped>
.document-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-color);
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
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
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--bg-color);
  color: var(--primary-color);
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.doc-name-input {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  background: transparent;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  min-width: 200px;
}

.doc-name-input:focus {
  outline: none;
  background: var(--bg-color);
}

.doc-type-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.doc-type-badge.word {
  background: rgba(43, 87, 154, 0.1);
  color: #2B579A;
}

.doc-type-badge.excel {
  background: rgba(33, 115, 70, 0.1);
  color: #217346;
}

.doc-type-badge.ppt {
  background: rgba(255, 107, 53, 0.1);
  color: #FF6B35;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--bg-color);
  color: var(--text-color);
}

.action-btn.primary {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.action-btn.primary:hover {
  background: var(--primary-hover);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
}

.toolbar-btn {
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
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: var(--bg-color);
  color: var(--primary-color);
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
  margin: 0 8px;
}

.editor-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: var(--card-bg);
}

.editor-area {
  min-height: 100%;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  outline: none;
  font-size: 14px;
  line-height: 1.8;
  color: #333;
}

.ai-assistant-panel {
  width: 320px;
  background: var(--card-bg);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.ai-assistant-panel.collapsed {
  width: 48px;
}

.ai-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.ai-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
}

.collapse-btn:hover {
  background: var(--bg-color);
}

.ai-panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
}

.ai-action-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.ai-action-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.ai-chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.ai-message {
  margin-bottom: 12px;
}

.ai-message.user .ai-message-content {
  background: var(--primary-color);
  color: #fff;
  margin-left: 24px;
}

.ai-message.assistant .ai-message-content {
  background: var(--bg-color);
  color: var(--text-color);
  margin-right: 24px;
}

.ai-message-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.ai-input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--border-color);
}

.ai-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-color);
  color: var(--text-color);
  font-size: 13px;
}

.ai-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.ai-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: var(--primary-color);
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.ai-send-btn:hover {
  background: var(--primary-hover);
}
</style>
