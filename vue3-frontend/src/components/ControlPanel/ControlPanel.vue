<template>
  <div class="control-panel px-6 py-4">
    <!-- 视觉分隔线 -->
    <div class="w-full h-px bg-gradient-to-r from-transparent via-secondary to-transparent mb-4"></div>
    
    <!-- 语音状态条 -->
    <div class="voice-bar flex flex-col items-center gap-4">
      <!-- 状态显示 -->
      <div class="status-display flex flex-col items-center gap-2">
        <!-- 聆听状态：语音波形动画 -->
        <div v-if="status === 'recording'" class="wave-container flex gap-2 items-center">
          <div class="wave"></div>
          <div class="wave" style="animation-delay: 0.1s"></div>
          <div class="wave" style="animation-delay: 0.2s"></div>
          <div class="wave" style="animation-delay: 0.3s"></div>
          <div class="wave" style="animation-delay: 0.4s"></div>
        </div>
        <!-- 思考状态：加载点 -->
        <div v-else-if="isThinking" class="loading-dots flex gap-2 items-center">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <!-- 初始/结束状态：麦克风图标 -->
        <div v-else class="mic-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
        </div>
        
        <!-- 状态文本 -->
        <div class="status-text font-medium text-center">{{ statusText }}</div>
        <div v-if="showHint" class="hint-text text-xs mt-1 animate-fade-in">
          {{ hintText }}
        </div>
      </div>
      
      <!-- 控制按钮 -->
      <button 
        :class="['start-btn', { 'active': isConversationActive }]"
        @click="toggleConversation"
        :disabled="isProcessing"
        class="group"
      >
        <div v-if="!isConversationActive" class="button-content">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon transition-transform duration-300 group-hover:scale-110">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          <span class="text">和我聊聊</span>
        </div>
        <div v-else class="button-content">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon transition-transform duration-300 group-hover:scale-110">
            <rect x="6" y="4" width="4" height="16"></rect>
            <rect x="14" y="4" width="4" height="16"></rect>
          </svg>
          <span class="text">停止聊天</span>
        </div>
      </button>
    </div>
    
    <!-- 视觉分隔线 -->
    <div class="w-full h-px bg-gradient-to-r from-transparent via-secondary to-transparent mt-4"></div>
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

// 计算属性：状态文本
const statusText = computed(() => {
  switch (status.value) {
    case 'connected':
      return '小叶已准备就绪～'
    case 'recording':
      return '我在听呢，请说...'
    case 'processing':
      return '让我想想...'
    case 'generating':
      return '正在思考中...'
    case 'synthesizing':
      return '准备回答你...'
    case 'playing':
      return '我在说话哦...'
    case 'error':
      return chatStore.errorMessage || '哎呀，出错了...'
    default:
      return '你好！点击按钮和我聊天吧'
  }
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
  background: var(--bg);
  transition: all 0.3s ease;
}

.voice-bar {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.status-display {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

/* 波形动画容器 */
.wave-container {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 12px;
  background: var(--bg);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--secondary);
  transition: all 0.3s ease;
}

/* 波形动画 */
.wave {
  width: 6px;
  height: 24px;
  background: var(--primary);
  border-radius: 3px;
  animation: wave 0.8s ease-in-out infinite alternate;
}

@keyframes wave {
  0% { transform: scaleY(0.3); }
  100% { transform: scaleY(1); }
}

/* 加载点动画 */
.loading-dots {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 12px;
  background: var(--bg);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--secondary);
  transition: all 0.3s ease;
}

.loading-dots span {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  margin: 0 2px;
  animation: bounce 1s infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

/* 麦克风图标 */
.mic-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--bg);
  border-radius: 50%;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  border: 2px solid var(--secondary);
  color: var(--primary);
  transition: all 0.3s ease;
}

/* 状态文本 */
.status-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
  text-align: center;
  transition: all 0.3s ease;
}

.hint-text {
  font-size: 12px;
  color: var(--text-light);
  text-align: center;
  max-width: 250px;
  transition: all 0.3s ease;
}

/* 开始按钮 */
.start-btn {
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: white;
  padding: 14px 28px;
  border-radius: 25px;
  border: none;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 180px;
  position: relative;
  overflow: hidden;
}

.start-btn::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transform: rotate(45deg);
  animation: shine 3s ease-in-out infinite;
}

.button-content {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}

.icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.text {
  white-space: nowrap;
}

.start-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.start-btn:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.start-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.start-btn.active {
  background: linear-gradient(135deg, #ef4444, #f87171);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.2);
}

.start-btn.active:hover:not(:disabled) {
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
}

/* 新增动画效果 */
@keyframes shine {
  0% {
    transform: translateX(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) rotate(45deg);
  }
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

/* 响应式调整 */
@media (max-width: 768px) {
  .control-panel {
    padding: 12px 0;
  }
  
  .voice-bar {
    gap: 12px;
  }
  
  .wave-container,
  .loading-dots {
    padding: 8px;
  }
  
  .wave {
    width: 4px;
    height: 20px;
  }
  
  .loading-dots span {
    width: 6px;
    height: 6px;
  }
  
  .mic-icon {
    width: 40px;
    height: 40px;
  }
  
  .mic-icon svg {
    width: 20px;
    height: 20px;
  }
  
  .status-text {
    font-size: 12px;
  }
  
  .hint-text {
    font-size: 10px;
  }
  
  .start-btn {
    padding: 10px 20px;
    font-size: 13px;
    min-width: 140px;
  }
  
  .start-btn svg {
    width: 18px;
    height: 18px;
  }
}
</style>