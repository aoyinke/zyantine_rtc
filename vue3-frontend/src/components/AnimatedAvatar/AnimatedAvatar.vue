<template>
  <div class="animated-avatar-container">
    <div class="avatar-wrapper" :class="{ speaking: isSpeaking }">
      <!-- 头像主体 -->
      <div class="avatar">
        <!-- 头部 -->
        <div class="head">
          <!-- 头发 -->
          <div class="hair"></div>
          <!-- 面部 -->
          <div class="face">
            <!-- 眼睛 -->
            <div class="eyes">
              <div class="eye left">
                <div class="pupil"></div>
              </div>
              <div class="eye right">
                <div class="pupil"></div>
              </div>
            </div>
            <!-- 嘴巴 -->
            <div class="mouth" :class="{ speaking: isSpeaking }"></div>
            <!-- 腮红 -->
            <div class="blush left"></div>
            <div class="blush right"></div>
          </div>
        </div>
        <!-- 身体 -->
        <div class="body">
          <div class="shirt"></div>
          <div class="arm left"></div>
          <div class="arm right"></div>
        </div>
      </div>
    </div>
    <!-- 状态文本 -->
    <div class="status-text">{{ statusText }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useChatStore } from '../../stores/chat'

const chatStore = useChatStore()

// 计算是否在说话
const isSpeaking = computed(() => {
  return ['recording', 'playing'].includes(chatStore.status)
})

// 计算状态文本
const statusText = computed(() => {
  switch (chatStore.status) {
    case 'recording':
      return '正在聆听...'
    case 'processing':
      return '正在识别...'
    case 'generating':
      return '正在思考...'
    case 'synthesizing':
      return '正在生成语音...'
    case 'playing':
      return '正在回应...'
    case 'connected':
      return '已就绪'
    case 'error':
      return '出现错误'
    default:
      return '你好！'
  }
})
</script>

<style scoped>
.animated-avatar-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.avatar-wrapper {
  position: relative;
  width: 150px;
  height: 200px;
  animation: float 3s ease-in-out infinite;
}

.avatar-wrapper.speaking {
  animation: float 3s ease-in-out infinite, pulse 0.5s ease-in-out infinite;
}

.avatar {
  position: relative;
  width: 100%;
  height: 100%;
}

/* 头部 */
.head {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 120px;
  border-radius: 50px 50px 45px 45px;
  background: linear-gradient(135deg, #ffddc1 0%, #ffccb0 100%);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* 头发 */
.hair {
  position: absolute;
  top: -20px;
  left: -10px;
  width: 120px;
  height: 80px;
  background: linear-gradient(135deg, #333 0%, #222 100%);
  border-radius: 50px 50px 0 0;
  z-index: 1;
}

.hair::before {
  content: '';
  position: absolute;
  top: 40px;
  left: 10px;
  width: 10px;
  height: 20px;
  background: #333;
  border-radius: 5px;
  transform: rotate(-30deg);
}

.hair::after {
  content: '';
  position: absolute;
  top: 40px;
  right: 10px;
  width: 10px;
  height: 20px;
  background: #333;
  border-radius: 5px;
  transform: rotate(30deg);
}

/* 面部 */
.face {
  position: relative;
  width: 100%;
  height: 100%;
  z-index: 2;
}

/* 眼睛 */
.eyes {
  position: absolute;
  top: 40px;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: space-around;
}

.eye {
  position: relative;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pupil {
  width: 10px;
  height: 10px;
  background: #333;
  border-radius: 50%;
  animation: blink 3s infinite;
}

/* 嘴巴 */
.mouth {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 10px;
  background: #ff6b6b;
  border-radius: 0 0 15px 15px;
  transition: all 0.3s ease;
}

.mouth.speaking {
  width: 25px;
  height: 15px;
  border-radius: 50%;
  animation: speak 0.5s ease-in-out infinite;
}

/* 腮红 */
.blush {
  position: absolute;
  top: 60px;
  width: 20px;
  height: 10px;
  background: rgba(255, 182, 193, 0.6);
  border-radius: 10px;
}

.blush.left {
  left: 10px;
}

.blush.right {
  right: 10px;
}

/* 身体 */
.body {
  position: absolute;
  top: 110px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 80px;
  background: #4a90e2;
  border-radius: 20px 20px 10px 10px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

/* 衬衫 */
.shirt {
  position: absolute;
  top: 10px;
  left: 10px;
  width: 60px;
  height: 40px;
  background: white;
  border-radius: 10px;
}

/* 手臂 */
.arm {
  position: absolute;
  top: 10px;
  width: 20px;
  height: 40px;
  background: linear-gradient(135deg, #ffddc1 0%, #ffccb0 100%);
  border-radius: 10px;
  animation: wave 4s ease-in-out infinite;
}

.arm.left {
  left: -10px;
  transform-origin: top right;
}

.arm.right {
  right: -10px;
  transform-origin: top left;
  animation-delay: 2s;
}

/* 状态文本 */
.status-text {
  position: absolute;
  bottom: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-top: 10px;
  text-align: center;
  padding: 5px 15px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

/* 动画 */
@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes blink {
  0%, 95%, 100% {
    transform: scaleY(1);
  }
  97.5% {
    transform: scaleY(0.1);
  }
}

@keyframes speak {
  0%, 100% {
    transform: translateX(-50%) scale(1);
  }
  50% {
    transform: translateX(-50%) scale(1.2);
  }
}

@keyframes wave {
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(15deg);
  }
  75% {
    transform: rotate(-15deg);
  }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .avatar-wrapper {
    width: 120px;
    height: 160px;
  }
  
  .head {
    width: 80px;
    height: 96px;
  }
  
  .hair {
    width: 100px;
    height: 64px;
  }
  
  .eyes {
    top: 32px;
  }
  
  .eye {
    width: 16px;
    height: 16px;
  }
  
  .pupil {
    width: 8px;
    height: 8px;
  }
  
  .mouth {
    bottom: 24px;
    width: 24px;
    height: 8px;
  }
  
  .mouth.speaking {
    width: 20px;
    height: 12px;
  }
  
  .blush {
    top: 48px;
    width: 16px;
    height: 8px;
  }
  
  .body {
    top: 88px;
    width: 64px;
    height: 64px;
  }
  
  .shirt {
    top: 8px;
    left: 8px;
    width: 48px;
    height: 32px;
  }
  
  .arm {
    width: 16px;
    height: 32px;
  }
  
  .status-text {
    font-size: 14px;
  }
}
</style>