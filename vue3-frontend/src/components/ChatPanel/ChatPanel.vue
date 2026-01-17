<template>
  <div 
    class="chat-panel h-full flex flex-col" 
    role="region" 
    aria-label="电话对话聊天面板" 
    tabindex="0" 
    @keydown.arrow-down="scrollToBottom" 
    @keydown.arrow-up="scrollToTop"
  >
    <div class="chat-header text-xl font-bold text-indigo-600 mb-4 pb-2 border-b border-indigo-100 flex items-center gap-2">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
      </svg>
      和小叶的聊天
    </div>
    <div 
      class="chat-history flex-1 overflow-y-auto p-4 flex flex-col gap-4" 
      ref="chatHistoryRef"
      role="log"
      aria-live="polite"
      aria-atomic="false"
      tabindex="0"
    >
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="empty-state flex flex-col items-center justify-center h-full" role="status" aria-live="polite">
        <div class="empty-state-background"></div>
        <div class="microphone-icon animate-float animate-pulse-slow">
          <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="11" r="8"></circle>
            <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
            <line x1="9" y1="9" x2="9.01" y2="9"></line>
            <line x1="15" y1="9" x2="15.01" y2="9"></line>
          </svg>
        </div>
        <div class="empty-state-title">嗨～我是小叶同学</div>
        <div class="empty-state-subtitle">点击下方按钮，和我聊聊天吧！</div>
        <div class="empty-state-tips animate-fade-in">
          <span>✨ 你可以和我分享你的生活，或者问我任何问题哦</span>
        </div>
      </div>
      
      <!-- 聊天消息 -->
        <TransitionGroup name="bubble" tag="div" class="messages-container" aria-label="聊天消息">
          <!-- 消息项 -->
          <template v-for="(message, index) in messages" :key="index">
            <!-- 时间分隔线 -->
            <div
              v-if="shouldShowTimeSeparator(index)"
              class="time-separator"
              :aria-label="`时间分隔：${formatTimeSeparator(message.timestamp)}`"
              role="separator"
              aria-orientation="horizontal"
            >
              <span class="time-separator-text">{{ formatTimeSeparator(message.timestamp) }}</span>
            </div>
            
            <!-- 消息分组 -->
            <div
              :class="[
                'message-wrapper',
                message.sender === 'user' ? 'user-message' : 'ai-message',
                { 'group-first': isGroupFirst(index), 'group-middle': isGroupMiddle(index), 'group-last': isGroupLast(index) }
              ]"
              role="group"
              :aria-label="message.sender === 'user' ? '用户消息组' : 'AI消息组'"
            >
              <!-- 只有分组第一个消息显示头像 -->
              <div 
                v-if="isGroupFirst(index) && message.sender === 'ai'" 
                class="message-avatar ai-avatar"
                role="img"
                aria-label="AI助手头像"
                tabindex="0"
                @keydown.enter="focusChatHistory"
              >
                <div class="avatar-circle">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                    <path d="M12 12v2"></path>
                    <path d="M12 16v1"></path>
                  </svg>
                </div>
              </div>
              
              <!-- 消息内容 -->
              <div 
                class="message-content" 
                :class="message.sender === 'user' ? 'user-content' : 'ai-content'"
                role="dialog"
                :aria-label="message.sender === 'user' ? '用户消息' : 'AI回复'"
                tabindex="0"
                @keydown.enter="focusChatHistory"
              >
                <div class="message-text" tabindex="0">{{ message.text }}</div>
                <div class="message-time" tabindex="0">{{ message.timestamp }}</div>
              </div>
              
              <!-- 只有分组第一个消息显示头像 -->
              <div 
                v-if="isGroupFirst(index) && message.sender === 'user'" 
                class="message-avatar user-avatar"
                role="img"
                aria-label="用户头像"
                tabindex="0"
                @keydown.enter="focusChatHistory"
              >
                <div class="avatar-circle">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                </div>
              </div>
            </div>
          </template>
        
        <!-- AI正在思考状态 -->
        <div 
          v-if="isTyping && !currentAIMessage" 
          class="message-wrapper ai-message"
          role="status"
          aria-live="polite"
          aria-label="AI正在思考"
        >
          <div class="message-avatar ai-avatar" role="img" aria-label="AI助手头像">
            <div class="avatar-circle">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
                <path d="M12 12v2"></path>
                <path d="M12 16v1"></path>
              </svg>
            </div>
          </div>
          <div class="message-content ai-content">
            <div class="message-text ai-is-thinking">
              <span class="thinking-text">正在思考...</span>
              <span class="thinking-icon" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2a10 10 0 0 0-9.95 9h11.64L9.74 7.05A1 1 0 0 1 10.7 6h2.61A10 10 0 0 0 12 2z"></path>
                  <path d="M12 22a10 10 0 0 0 9.95-9h-11.64L14.26 16.95A1 1 0 0 1 13.3 18h-2.61A10 10 0 0 0 12 22z"></path>
                </svg>
              </span>
            </div>
            <div class="message-time">{{ new Date().toLocaleTimeString('zh-CN') }}</div>
          </div>
        </div>
        
        <!-- 流式AI回复 -->
        <div 
          v-if="currentAIMessage" 
          class="message-wrapper ai-message"
          role="group"
          aria-label="AI流式回复"
        >
          <div class="message-avatar ai-avatar" role="img" aria-label="AI助手头像">
            <div class="avatar-circle">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
                <path d="M12 12v2"></path>
                <path d="M12 16v1"></path>
              </svg>
            </div>
          </div>
          <div class="message-content ai-content">
            <div class="message-text typing-effect">
              {{ currentAIMessage }}
              <span 
                v-if="isTyping" 
                class="typing-indicator"
                role="status"
                aria-label="正在输入"
              >
                <span aria-hidden="true"></span>
              </span>
            </div>
            <div class="message-time">{{ new Date().toLocaleTimeString('zh-CN') }}</div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useChatStore } from '../../stores/chat'

const chatStore = useChatStore()
const chatHistoryRef = ref(null)

// 计算属性：获取聊天消息
const messages = computed(() => chatStore.messages)

// 计算属性：获取当前AI流式回复
const currentAIMessage = computed(() => chatStore.currentAIMessage)

// 计算属性：是否正在输入
const isTyping = computed(() => chatStore.isStreaming)

// 自动滚动到最新消息
function scrollToBottom() {
  nextTick(() => {
    if (chatHistoryRef.value) {
      // 平滑滚动
      chatHistoryRef.value.scrollTo({
        top: chatHistoryRef.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

// 监听消息变化，自动滚动
watch(() => messages.value.length, () => {
  scrollToBottom()
})

// 监听当前AI消息变化，自动滚动
watch(() => currentAIMessage.value, () => {
  scrollToBottom()
})

// 滚动到顶部
function scrollToTop() {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTo({
        top: 0,
        behavior: 'smooth'
      })
    }
  })
}

// 聚焦到聊天历史区域
function focusChatHistory() {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.focus()
    }
  })
}

// 时间分隔线逻辑：超过5分钟显示时间分隔
function shouldShowTimeSeparator(index) {
  if (index === 0) return true
  
  const currentMsg = messages.value[index]
  const prevMsg = messages.value[index - 1]
  
  // 解析时间字符串
  const currentTime = new Date(`2000-01-01 ${currentMsg.timestamp}`)
  const prevTime = new Date(`2000-01-01 ${prevMsg.timestamp}`)
  
  // 如果时间差超过5分钟，显示分隔线
  return Math.abs(currentTime - prevTime) > 5 * 60 * 1000
}

// 格式化时间分隔显示
function formatTimeSeparator(timestamp) {
  const date = new Date(`2000-01-01 ${timestamp}`)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 消息分组逻辑：同一发送者连续发送的消息为一组
function isGroupFirst(index) {
  if (index === 0) return true
  return messages.value[index].sender !== messages.value[index - 1].sender
}

function isGroupMiddle(index) {
  if (index === 0 || index === messages.value.length - 1) return false
  return messages.value[index].sender === messages.value[index - 1].sender && 
         messages.value[index].sender === messages.value[index + 1].sender
}

function isGroupLast(index) {
  if (index === messages.value.length - 1) return true
  return messages.value[index].sender !== messages.value[index + 1].sender
}
</script>

<style scoped>
.chat-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  transition: all 0.3s ease;
}

.chat-header {
  flex-shrink: 0;
  color: var(--primary);
  border-bottom-color: var(--secondary);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.chat-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  transform: translateX(-100%);
  animation: headerGradient 3s ease-in-out infinite;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
  position: relative;
}

/* 滚动条样式 */
.chat-history::-webkit-scrollbar {
  width: 8px;
}

.chat-history::-webkit-scrollbar-track {
  background: var(--bg);
  border-radius: 10px;
}

.chat-history::-webkit-scrollbar-thumb {
  background: var(--secondary);
  border-radius: 10px;
  transition: all 0.3s ease;
}

.chat-history::-webkit-scrollbar-thumb:hover {
  background: var(--primary);
  transform: scale(1.1);
}

.chat-history::-webkit-scrollbar-thumb:active {
  background: var(--primary);
  transform: scale(0.9);
}

/* 消息容器 */
.messages-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 时间分隔线 */
.time-separator {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 16px 0;
  position: relative;
  animation: fadeIn 0.3s ease-out;
}

.time-separator::before,
.time-separator::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(to right, transparent, var(--secondary-light), transparent);
  margin: 0 12px;
}

.time-separator-text {
  background: var(--bg);
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  z-index: 1;
  animation: pulse 1s ease-out;
}

/* 消息样式 */
.message-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  animation: slideIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  margin-bottom: 4px;
}

.user-message {
  flex-direction: row-reverse;
}

.ai-message {
  flex-direction: row;
}

/* 消息分组样式 */
.message-wrapper.group-first .message-content {
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
}

.message-wrapper.group-middle .message-content {
  border-radius: 16px;
  margin-top: 2px;
  margin-bottom: 2px;
}

.message-wrapper.group-last .message-content {
  border-bottom-left-radius: 24px;
  border-bottom-right-radius: 24px;
}

/* 用户消息分组 */
.user-message.group-first .message-content {
  border-bottom-right-radius: 6px;
  border-bottom-left-radius: 24px;
}

.user-message.group-middle .message-content {
  border-bottom-right-radius: 16px;
  border-bottom-left-radius: 16px;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.user-message.group-last .message-content {
  border-bottom-right-radius: 6px;
  border-bottom-left-radius: 24px;
}

/* AI消息分组 */
.ai-message.group-first .message-content {
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 24px;
}

.ai-message.group-middle .message-content {
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.ai-message.group-last .message-content {
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 24px;
}

/* 头像样式 */
.message-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  animation: avatarSlideIn 0.3s ease-out;
}

/* 头像滑动动画 */
@keyframes avatarSlideIn {
  from {
    opacity: 0;
    transform: scale(0.8) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.avatar-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

/* 头像呼吸光效 */
.avatar-circle::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transform: rotate(45deg);
  animation: shine 3s ease-in-out infinite;
}

/* 头像脉冲效果 */
.avatar-circle::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  transform: scale(0);
  opacity: 0;
  transition: all 0.3s ease;
}

.avatar-circle:hover::after {
  transform: scale(1.2);
  opacity: 1;
}

.ai-avatar .avatar-circle {
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
  animation: aiAvatarPulse 2s ease-in-out infinite;
}

/* AI头像脉冲动画 */
@keyframes aiAvatarPulse {
  0%, 100% {
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    transform: scale(1.05);
  }
}

.user-avatar .avatar-circle {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.avatar-circle:hover {
  transform: scale(1.15) translateY(-2px) rotate(5deg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.avatar-circle:active {
  transform: scale(1.1) translateY(-1px) rotate(2deg);
}

.avatar-circle svg {
  position: relative;
  z-index: 1;
  width: 24px;
  height: 24px;
  transition: all 0.3s ease;
}

.avatar-circle:hover svg {
  transform: scale(1.2);
  animation: avatarSvgSpin 0.6s ease-out;
}

/* 头像图标旋转动画 */
@keyframes avatarSvgSpin {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.3) rotate(10deg);
  }
  100% {
    transform: scale(1.2);
  }
}

/* 消息内容 */
.message-content {
  max-width: 75%;
  padding: 16px 20px;
  border-radius: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  position: relative;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  overflow: hidden;
  animation: messageAppear 0.3s ease-out;
  border: 1px solid transparent;
  transform-origin: bottom right;
}

.message-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.6s ease;
}

/* 增强的消息悬停效果 */
.message-content:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.message-content:hover::before {
  left: 100%;
}

/* 用户消息悬停效果增强 */
.user-content:hover {
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.25);
}

/* AI消息悬停效果增强 */
.ai-content:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 消息发送成功的涟漪效果 */
.user-message .message-content::after {
  content: '';
  position: absolute;
  bottom: 8px;
  right: 12px;
  width: 16px;
  height: 16px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'%3E%3C/polyline%3E%3C/svg%3E") no-repeat center center;
  background-size: 14px;
  opacity: 0.7;
  animation: sendSuccess 0.5s ease-out;
}

/* 发送成功动画 */
@keyframes sendSuccess {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.7;
  }
}

/* 增强版消息出现动画 */
@keyframes messageAppear {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }
}

/* 用户消息样式 - 电话风格的气泡 */
.user-content {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
  border-bottom-right-radius: 6px;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  border-bottom-left-radius: 24px;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.2);
  margin-right: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* AI消息样式 - 电话风格的气泡 */
.ai-content {
  background: linear-gradient(135deg, #ffffff, #f3f4f6);
  color: var(--text-primary);
  border-bottom-left-radius: 6px;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  border-bottom-right-radius: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  margin-left: 8px;
  border: 1px solid rgba(209, 213, 219, 0.5);
}

/* 消息状态指示器 */
.user-message .message-content::after {
  content: '';
  position: absolute;
  bottom: 8px;
  right: 12px;
  width: 16px;
  height: 16px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='20 6 9 17 4 12'%3E%3C/polyline%3E%3C/svg%3E") no-repeat center center;
  background-size: 14px;
  opacity: 0.7;
}

/* 消息出现动画 */
@keyframes messageAppear {
  from {
    opacity: 0;
    transform: translateY(15px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 6px;
  word-wrap: break-word;
  position: relative;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  text-align: right;
  color: inherit;
  font-weight: 500;
}

/* AI正在思考状态 - 电话风格的"正在输入"提示 */
.ai-is-typing {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #ffffff, #f3f4f6);
  border-radius: 24px;
  border-bottom-left-radius: 6px;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  border-bottom-right-radius: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  margin-left: 8px;
  animation: fadeInUp 0.3s ease-out;
}

/* 打字机效果 */
.typing-effect {
  position: relative;
}

/* 增强版打字指示器 */
.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  animation: pulse 1.5s ease-in-out infinite;
}

/* 打字指示器的点 */
.typing-indicator::before,
.typing-indicator::after,
.typing-indicator span {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: typingDots 1.4s infinite ease-in-out both;
}

.typing-indicator span {
  margin: 0 2px;
}

.typing-indicator::before {
  animation-delay: -0.32s;
}

.typing-indicator span {
  animation-delay: 0s;
}

.typing-indicator::after {
  animation-delay: 0.32s;
}

/* 思考状态文本 */
.thinking-text {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
  margin-right: 8px;
}

/* 思考状态的大脑图标 */
.thinking-icon {
  width: 18px;
  height: 18px;
  color: var(--primary);
  animation: brainPulse 2s ease-in-out infinite;
  margin-right: 8px;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.6s ease-out;
}

.empty-state-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 24 24' fill='none' stroke='%236366f1' stroke-width='0.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 60px 60px;
  opacity: 0.05;
  z-index: -1;
  animation: backgroundMove 20s linear infinite;
}

.microphone-icon {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, var(--bg), var(--secondary));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
  color: var(--primary);
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
  border: 3px solid var(--secondary);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.microphone-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(99, 102, 241, 0.1), transparent);
  transform: rotate(45deg);
  animation: shine 3s ease-in-out infinite;
}

.microphone-icon:hover {
  transform: scale(1.05);
  box-shadow: 0 12px 40px rgba(99, 102, 241, 0.3);
}

.empty-state-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 12px;
  transition: all 0.3s ease;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.empty-state-subtitle {
  font-size: 14px;
  color: var(--text-light);
  margin-bottom: 24px;
  transition: all 0.3s ease;
}

.empty-state-tips {
  font-size: 13px;
  color: var(--primary);
  background: rgba(99, 102, 241, 0.1);
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid var(--secondary);
  transition: all 0.3s ease;
}

.empty-state-tips:hover {
  background: rgba(99, 102, 241, 0.2);
  transform: translateY(-2px);
}

/* 动画效果 */
@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-15px);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

@keyframes pulse-slow {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

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

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes typingDots {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 大脑脉冲动画 */
@keyframes brainPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
}

/* 消息出现动画 */
@keyframes messageAppear {
  from {
    opacity: 0;
    transform: translateY(15px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes headerGradient {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes backgroundMove {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 100px 100px;
  }
}

@keyframes shine {
  0% {
    transform: translateX(-100%) rotate(45deg);
  }
  100% {
    transform: translateX(100%) rotate(45deg);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-float {
  animation: float 4s ease-in-out infinite;
}

.animate-pulse-slow {
  animation: pulse-slow 3s ease-in-out infinite;
}

.animate-fade-in {
  animation: fade-in 0.6s ease-out forwards;
}

/* 消息气泡动画 */
.bubble-enter-from {
  opacity: 0;
  transform: translateY(30px) scale(0.85);
}

.bubble-enter-active {
  transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.bubble-move {
  transition: transform 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.bubble-leave-from {
  opacity: 1;
  transform: scale(1);
}

.bubble-leave-active {
  transition: all 0.3s ease;
}

.bubble-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .message-content {
    max-width: 80%;
    padding: 12px 16px;
  }
  
  .message-text {
    font-size: 13px;
  }
  
  .message-time {
    font-size: 10px;
  }
  
  .message-avatar {
    width: 32px;
    height: 32px;
  }
  
  .avatar-circle {
    width: 32px;
    height: 32px;
  }
  
  .avatar-circle svg {
    width: 16px;
    height: 16px;
  }
  
  .empty-state {
    padding: 60px 16px;
  }
  
  .microphone-icon {
    width: 90px;
    height: 90px;
    margin-bottom: 24px;
  }
  
  .microphone-icon svg {
    width: 40px;
    height: 40px;
  }
  
  .empty-state-title {
    font-size: 18px;
  }
  
  .empty-state-subtitle {
    font-size: 13px;
  }
  
  .empty-state-tips {
    font-size: 12px;
    padding: 6px 12px;
  }
}

@media (max-width: 480px) {
  .message-content {
    max-width: 85%;
    padding: 10px 14px;
  }
  
  .message-text {
    font-size: 12px;
  }
  
  .message-avatar {
    width: 28px;
    height: 28px;
  }
  
  .avatar-circle {
    width: 28px;
    height: 28px;
  }
}
</style>