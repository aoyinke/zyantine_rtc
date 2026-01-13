<template>
  <div class="control-panel flex flex-col items-center gap-6 px-6 py-4">
    <!-- 视觉分隔线 -->
    <div class="w-full max-w-xs h-px bg-gradient-to-r from-transparent via-indigo-200 to-transparent mb-2"></div>
    
    <!-- 控制按钮 -->
    <button 
      :class="['btn-primary', { 'animate-pulse': isRecording, 'bg-gradient-to-r from-red-500 to-rose-500': isConversationActive }]"
      @click="toggleConversation"
      :disabled="isProcessing"
      class="relative group"
    >
      <span class="absolute inset-0 bg-white/10 rounded-full blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
      <svg v-if="!isConversationActive" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2 transition-transform duration-300 group-hover:scale-110">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2 transition-transform duration-300 group-hover:scale-110">
        <rect x="6" y="4" width="4" height="16"></rect>
        <rect x="14" y="4" width="4" height="16"></rect>
      </svg>
      <span v-if="!isConversationActive" class="transition-transform duration-300 group-hover:scale-105">开始对话</span>
      <span v-else class="transition-transform duration-300 group-hover:scale-105">停止对话</span>
    </button>
    
    <!-- 状态信息 -->
    <div class="status-info text-center w-full max-w-xs">
      <div class="status-icon text-2xl mb-2 transition-all duration-300 animate-bounce-subtle">{{ statusIcon }}</div>
      <div class="status-text text-sm font-medium text-gray-700 transition-all duration-300">{{ statusText }}</div>
      <div v-if="showHint" class="hint-text text-xs text-gray-500 mt-2 transition-all duration-300 animate-fade-in">
        {{ hintText }}
      </div>
    </div>
    
    <!-- 视觉分隔线 -->
    <div class="w-full max-w-xs h-px bg-gradient-to-r from-transparent via-indigo-200 to-transparent mt-2"></div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useAudioStore } from '../../stores/audio'
import { useWebSocket } from '../../composables/useWebSocket'
import { useAudio } from '../../composables/useAudio'

const chatStore = useChatStore()
const audioStore = useAudioStore()
const { connect, disconnect, sendMessage } = useWebSocket()
const { startRecording, stopRecording, isRecording } = useAudio()

const isConversationActive = ref(false)
const showHint = ref(false)
const hintText = ref('')

// 计算属性：获取当前状态
const status = computed(() => chatStore.status)

// 计算属性：状态图标
const statusIcon = computed(() => {
  switch (status.value) {
    case 'connected':
      return '🔗'
    case 'recording':
      return '🎤'
    case 'processing':
      return '🤔'
    case 'generating':
      return '💭'
    case 'synthesizing':
      return '🎵'
    case 'playing':
      return '🔊'
    case 'error':
      return '⚠️'
    default:
      return '👋'
  }
})

// 计算属性：状态文本
const statusText = computed(() => {
  switch (status.value) {
    case 'connected':
      return '已连接到服务器'
    case 'recording':
      return '正在聆听，请开始说话...'
    case 'processing':
      return '正在识别语音...'
    case 'generating':
      return 'AI 正在思考...'
    case 'synthesizing':
      return '正在生成语音...'
    case 'playing':
      return '正在播放...'
    case 'error':
      return chatStore.errorMessage || '发生错误'
    default:
      return '你好！点击按钮开始对话'
  }
})

// 计算属性：是否为活跃状态
const isActive = computed(() => {
  return ['recording', 'processing', 'generating', 'synthesizing', 'playing'].includes(status.value)
})

// 计算属性：是否为思考状态
const isThinking = computed(() => {
  return ['processing', 'generating', 'synthesizing'].includes(status.value)
})

// 计算属性：是否正在处理
const isProcessing = computed(() => {
  return ['processing', 'generating', 'synthesizing', 'playing'].includes(status.value)
})

// 切换对话状态
async function toggleConversation() {
  if (!isConversationActive.value) {
    // 开始对话
    await startConversation()
  } else {
    // 停止对话
    await stopConversation()
  }
}

// 开始对话
async function startConversation() {
  try {
    // 连接WebSocket
    if (!chatStore.isConnected) {
      await connect()
    }
    
    // 定义停止对话回调函数
    function onUserStoppedSpeaking() {
      console.log('User stopped speaking, updating UI...')
      isConversationActive.value = false
      showHint.value = false
    }
    
    // 开始录音（传递回调函数）
    await startRecording(onUserStoppedSpeaking)
    
    // 更新状态
    isConversationActive.value = true
    showHint.value = true
    hintText.value = '说话结束后会自动停止录音'
    
    // 通知服务器开始录音
    sendMessage({ type: 'start_recording' })
  } catch (error) {
    console.error('Start conversation error:', error)
    chatStore.setError('无法开始对话，请检查麦克风权限')
  }
}

// 停止对话
async function stopConversation() {
  try {
    // 停止录音
    await stopRecording()
    
    // 更新状态
    isConversationActive.value = false
    showHint.value = false
    
    // 通知服务器停止录音
    sendMessage({ type: 'stop_recording' })
  } catch (error) {
    console.error('Stop conversation error:', error)
    chatStore.setError('无法停止对话')
  }
}
</script>

<style scoped>
.control-panel {
  width: 100%;
  padding: 16px 0;
}

.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  max-width: 200px;
  padding: 16px 28px;
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  color: white;
  border: none;
  border-radius: 28px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
  position: relative;
  overflow: hidden;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.6);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

/* 录音状态动画 */
.animate-pulse {
  animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
  }
  50% {
    box-shadow: 0 10px 24px rgba(79, 70, 229, 0.8);
  }
}

/* 微妙的弹跳动画 */
@keyframes bounce-subtle {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

.animate-bounce-subtle {
  animation: bounce-subtle 3s ease-in-out infinite;
}

/* 淡入动画 */
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out forwards;
}

/* 控制按钮的渐变背景（停止对话状态） */
.btn-primary.bg-gradient-to-r {
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
}

.btn-primary.bg-gradient-to-r:hover:not(:disabled) {
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.6);
}

.status-info {
  width: 100%;
}

.status-icon {
  color: #6366f1;
}

.status-text {
  color: #374151;
}

.hint-text {
  max-width: 250px;
  margin: 0 auto;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .control-panel {
    gap: 4;
    padding: 12px 0;
  }
  
  .btn-primary {
    padding: 12px 20px;
    font-size: 13px;
  }
  
  .status-icon {
    font-size: 1.5rem;
  }
  
  .status-text {
    font-size: 12px;
  }
  
  .hint-text {
    font-size: 11px;
  }
}
</style>