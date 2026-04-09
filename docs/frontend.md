# PyAgent åç«¯ææ¡£ v0.8.0

æ¬ææ¡£è¯¦ç»è¯´æPyAgent v0.8.0åç«¯é¡¹ç®çè®¾è®¡åå®ç°ã?
## æ¦è¿°

**v0.3.2** çæ¬å¯¹åç«¯UIè¿è¡äºå¨é¢ä¼åï¼å¼å¥äºæè²æ¨¡å¼æ¯æãç°ä»£åUIç»ä»¶åæµççå¨ç»ææã?
## ææ¯æ 

- **æ¡æ¶**: Vue.js 3.4+
- **è·¯ç±**: Vue Router 4.2+
- **ç¶æç®¡ç?*: Pinia 2.1+
- **æå»ºå·¥å·**: Vite 5.0+
- **HTTPå®¢æ·ç«?*: Axios 1.6+
- **å·¥å·åº?*: VueUse 10.7+
- **è¯­è¨**: TypeScript 5.3+

## é¡¹ç®ç»æ

```
frontend/
âââ src/
â?  âââ views/           # é¡µé¢è§å¾
â?  â?  âââ ChatView.vue     # èå¤©è§å¾
â?  â?  âââ TasksView.vue    # ä»»å¡è§å¾
â?  â?  âââ ConfigView.vue   # éç½®è§å¾
â?  âââ components/      # å¬å±ç»ä»¶
â?  âââ stores/          # Piniaç¶æç®¡ç?â?  âââ router/          # è·¯ç±éç½®
â?  âââ api/             # APIæ¥å£
â?  âââ utils/           # å·¥å·å½æ°
â?  âââ assets/          # éæèµæº?â?  âââ App.vue          # æ ¹ç»ä»?â?  âââ main.ts          # å¥å£æä»¶
âââ index.html
âââ package.json
âââ tsconfig.json
âââ vite.config.ts
```

## æ ¸å¿ç¹æ?
### 1. æè²æ¨¡å¼æ¯æ

**å®ç°æ¹å¼**: CSSåé + localStorage

```vue
<!-- App.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const isDark = ref(false)

const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    isDark.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})
</script>
```

**CSSåéç³»ç»**:

```css
:root {
  /* äº®è²ä¸»é¢ */
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
  /* æè²ä¸»é¢ */
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
```

### 2. ååºå¼è®¾è®?
**æ­ç¹è®¾ç½®**:

```css
/* ç§»å¨ç«?*/
@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
  }
  
  .nav-item span {
    display: none;  /* éèæå­ï¼åªæ¾ç¤ºå¾æ  */
  }
  
  .main {
    padding: 16px;
  }
}
```

### 3. SVGå¾æ ç³»ç»

ä½¿ç¨SVGå¾æ æ¿ä»£å­ä½å¾æ ï¼æ¯æä¸»é¢è²ååï¼?
```vue
<template>
  <!-- å¤ªé³å¾æ ï¼äº®è²æ¨¡å¼ï¼ -->
  <svg v-if="isDark" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="5"/>
    <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
  </svg>
  
  <!-- æäº®å¾æ ï¼æè²æ¨¡å¼ï¼ -->
  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
  </svg>
</template>
```

### 4. å¨ç»ææ

**è¿æ¸¡å¨ç»**:

```css
/* ä¸»é¢åæ¢è¿æ¸¡ */
body {
  transition: background-color 0.3s, color 0.3s;
}

/* å¡çæ¬åææ */
.card {
  transition: all 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

/* æ¶æ¯æ·¡å¥å¨ç» */
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

.message {
  animation: fadeIn 0.3s ease;
}

/* æå­å¨ç» */
@keyframes typing {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.typing-indicator {
  animation: typing 1s infinite;
}
```

## é¡µé¢è§å¾

### 1. èå¤©è§å¾ (ChatView.vue)

**åè½**:
- å®æ¶èå¤©çé¢
- æ¶æ¯åå²å±ç¤º
- åéæ¶æ?- æå­æç¤ºå?- æè²æ¨¡å¼éé

**ç¹æ?*:
- æ¶æ¯æ°æ³¡æ ·å¼
- æ¶é´æ³æ¾ç¤?- èªå¨æ»å¨å°åºé?- ç©ºç¶ææç¤?
### 2. ä»»å¡è§å¾ (TasksView.vue)

**åè½**:
- Todoåè¡¨å±ç¤º
- é¶æ®µ/ä»»å¡/æ­¥éª¤ç®¡ç
- è¿åº¦æ¾ç¤º
- ç»è®¡ä¿¡æ¯

**ç¹æ?*:
- æ å½¢ç»æå±ç¤º
- ç¶ææ è¯?- è¿åº¦æ?- æä½æé®

### 3. éç½®è§å¾ (ConfigView.vue)

**åè½**:
- ç³»ç»éç½®
- ä¸»é¢åæ¢
- æ¨¡åéç½®
- MCPæå¡å¨ç®¡ç?
**ç¹æ?*:
- è¡¨åè¾å¥
- å¼å³æ§ä»?- ä¸æéæ©
- å®æ¶ä¿å­

## å¼åæå?
### å®è£ä¾èµ

```bash
cd frontend
npm install
```

### å¼åæ¨¡å¼?
```bash
npm run dev
```

### æå»ºçäº§çæ¬

```bash
npm run build
```

### é¢è§çäº§æå»º

```bash
npm run preview
```

## ç»ä»¶å¼å?
### ç»ä»¶æ¨¡æ¿

```vue
<template>
  <div class="component-name" :class="{ 'dark': isDark }">
    <!-- ç»ä»¶åå®¹ -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  title?: string
  data?: any
}

const props = withDefaults(defineProps<Props>(), {
  title: 'é»è®¤æ é¢'
})

const emit = defineEmits<{
  (e: 'update', value: any): void
}>()

// ç»ä»¶é»è¾
</script>

<style scoped>
.component-name {
  background: var(--card-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}
</style>
```

### ä½¿ç¨CSSåé

```vue
<style scoped>
.my-component {
  /* èæ¯è?*/
  background-color: var(--card-bg);
  
  /* æå­é¢è² */
  color: var(--text-color);
  
  /* è¾¹æ¡ */
  border: 1px solid var(--border-color);
  
  /* é´å½± */
  box-shadow: var(--shadow);
  
  /* ä¸»é¢è?*/
  border-left: 4px solid var(--primary-color);
}

.my-component:hover {
  box-shadow: var(--shadow-hover);
}
</style>
```

## APIéæ

### åºç¡éç½®

```typescript
// api/index.ts
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default api
```

### èå¤©API

```typescript
// api/chat.ts
import api from './index'

export const sendMessage = async (message: string, chatId: string = 'default') => {
  const response = await api.post('/chat', {
    message,
    chat_id: chatId
  })
  return response.data
}

export const getChatHistory = async (chatId: string) => {
  const response = await api.get(`/chat/${chatId}/history`)
  return response.data
}
```

### Todo API

```typescript
// api/todo.ts
import api from './index'

export const getPhases = async () => {
  const response = await api.get('/todo/phases')
  return response.data
}

export const createPhase = async (data: any) => {
  const response = await api.post('/todo/phases', data)
  return response.data
}

export const completeStep = async (stepId: string) => {
  const response = await api.post(`/todo/steps/${stepId}/complete`)
  return response.data
}
```

## ç¶æç®¡ç?
### Pinia Storeç¤ºä¾

```typescript
// stores/chat.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref<any[]>([])
  const isLoading = ref(false)
  const currentChatId = ref('default')
  
  // Getters
  const messageCount = computed(() => messages.value.length)
  
  // Actions
  const addMessage = (message: any) => {
    messages.value.push(message)
  }
  
  const clearMessages = () => {
    messages.value = []
  }
  
  return {
    messages,
    isLoading,
    currentChatId,
    messageCount,
    addMessage,
    clearMessages
  }
})
```

## æä½³å®è·?
### 1. ä½¿ç¨CSSåé

å§ç»ä½¿ç¨CSSåéèä¸æ¯ç¡¬ç¼ç é¢è²ï¼ç¡®ä¿æè²æ¨¡å¼æ­£å¸¸å·¥ä½ã?
```css
/* æ¨è */
.my-class {
  color: var(--text-color);
  background: var(--card-bg);
}

/* ä¸æ¨è?*/
.my-class {
  color: #333;
  background: #fff;
}
```

### 2. æ·»å è¿æ¸¡å¨ç»

ä¸ºä¸»é¢åæ¢åäº¤äºæ·»å è¿æ¸¡å¨ç»ï¼æåç¨æ·ä½éªã?
```css
.my-element {
  transition: all 0.3s ease;
}
```

### 3. ååºå¼è®¾è®?
ä½¿ç¨åªä½æ¥è¯¢ééä¸åå±å¹å°ºå¯¸ã?
```css
@media (max-width: 768px) {
  /* ç§»å¨ç«¯æ ·å¼?*/
}
```

### 4. ç»ä»¶åå¼å?
å°UIæåä¸ºå¯å¤ç¨çç»ä»¶ï¼æé«ä»£ç å¯ç»´æ¤æ§ã?
### 5. TypeScriptç±»å

ä¸ºææpropsãemitsåæ°æ®å®ä¹ç±»åï¼æé«ä»£ç è´¨éã?
## æéæé¤

### 1. æè²æ¨¡å¼ä¸çæ?
æ£æ¥æ¯å¦æ­£ç¡®è®¾ç½®äº`data-theme`å±æ§ï¼

```javascript
document.documentElement.setAttribute('data-theme', 'dark')
```

### 2. CSSåéæªå®ä¹?
ç¡®ä¿å¨`:root`ä¸­å®ä¹äºææCSSåéã?
### 3. å¾æ ä¸æ¾ç¤?
æ£æ¥SVGç`viewBox`åå°ºå¯¸è®¾ç½®æ¯å¦æ­£ç¡®ã?
## æ´æ°æ¥å¿

### v0.3.2 (2025-03-27)

- **æ°å¢**: æè²æ¨¡å¼æ¯æ
- **æ°å¢**: ä¸»é¢åæ¢åè½
- **ä¼å**: èå¤©è§å¾éæ°è®¾è®¡
- **ä¼å**: ä»»å¡è§å¾å¸å±æ¹è¿
- **ä¼å**: éç½®è§å¾æ·»å ä¸»é¢åæ¢
- **æ¹è¿**: ä½¿ç¨CSSåéå®ç°ä¸»é¢è?- **æ¹è¿**: ä½¿ç¨SVGå¾æ æ¿ä»£æå­å¾æ 
- **æ¹è¿**: æ·»å ç©ºç¶ææç¤?- **æ¹è¿**: æ·»å æå­å¨ç»ææ
- **æ¹è¿**: æ·»å æ¶æ¯æ·¡å¥æ·¡åºå¨ç»
- **æ¹è¿**: ä¼åååºå¼è®¾è®?
