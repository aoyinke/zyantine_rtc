<template>
  <div class="chat-panel h-full flex flex-col">
    <div class="chat-header text-xl font-bold text-indigo-600 mb-4 pb-2 border-b border-indigo-100 flex items-center gap-2">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
      </svg>
      对话记录
    </div>
    <div class="chat-history flex-1 overflow-y-auto p-4 flex flex-col gap-4" ref="chatHistoryRef">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="empty-state flex flex-col items-center justify-center h-full text-gray-400">
        <div class="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center mb-4">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-indigo-400">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
          </svg>
        </div>
        <div class="text-lg font-medium">还没有对话记录</div>
        <div class="text-sm mt-2">点击下方按钮开始与 AI 交流吧！</div>
      </div>
      
      <!-- 聊天消息 -->
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message-wrapper', message.sender === 'user' ? 'user-message' : 'ai-message']"
      >
        <div class="message-content" :class="message.sender === 'user' ? 'user-content' : 'ai-content'">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-time">{{ message.timestamp }}</div>
        </div>
      </div>
      
      <!-- 流式AI回复 -->
      <div v-if="currentAIMessage" class="message-wrapper ai-message">
        <div class="message-content ai-content">
          <div class="message-text">{{ currentAIMessage }}</div>
          <div class="message-time">{{ new Date().toLocaleTimeString('zh-CN') }}</div>
        </div>
      </div>
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

// 自动滚动到最新消息
function scrollToBottom() {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
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
</script>

<style scoped>
.chat-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  flex-shrink: 0;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
}

/* 滚动条样式 */
.chat-history::-webkit-scrollbar {
  width: 6px;
}

.chat-history::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 10px;
}

.chat-history::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

.chat-history::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 消息样式 */
.message-wrapper {
  display: flex;
  margin-bottom: 12px;
}

.user-message {
  justify-content: flex-end;
}

.ai-message {
  justify-content: flex-start;
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
}

.user-content {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-content {
  background: white;
  color: #374151;
  border-bottom-left-radius: 4px;
  border: 1px solid #e5e7eb;
}

.message-text {
  font-size: 14px;
  line-height: 1.4;
  margin-bottom: 4px;
}

.message-time {
  font-size: 11px;
  opacity: 0.7;
  text-align: right;
}

.user-content .message-time {
  color: rgba(255, 255, 255, 0.8);
}

.ai-content .message-time {
  color: #9ca3af;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
    padding: 10px 14px;
  }
  
  .message-text {
    font-size: 13px;
  }
  
  .message-time {
    font-size: 10px;
  }
}
</style>