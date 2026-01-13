<template>
  <div class="app-container h-screen w-screen flex flex-col bg-gradient-to-br from-indigo-50 via-purple-50 to-white">
    <!-- 装饰元素 -->
    <div class="decorative-elements">
      <div class="decor-circle decor-circle-1"></div>
      <div class="decor-circle decor-circle-2"></div>
      <div class="decor-circle decor-circle-3"></div>
    </div>

    <!-- 头像区域 -->
    <div class="avatar-section flex items-center justify-center p-2 bg-white/90 backdrop-blur-md rounded-b-3xl shadow-xl border-b border-indigo-100">
      <Live2DCharacter ref="live2dCharacter" />
    </div>

    <!-- 聊天面板区域 -->
    <div class="chat-section flex-1 bg-white/90 backdrop-blur-md p-6 overflow-hidden border-x border-indigo-100">
      <ChatPanel />
    </div>

    <!-- 控制面板区域 -->
    <div class="control-section bg-white/90 backdrop-blur-md p-6 shadow-lg border-t border-indigo-100">
      <ControlPanel />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Live2DCharacter from './components/Live2DCharacter/Live2DCharacter.vue'
import ChatPanel from './components/ChatPanel/ChatPanel.vue'
import ControlPanel from './components/ControlPanel/ControlPanel.vue'

const live2dCharacter = ref(null)

// 触发Live2D人物说话动画的方法
defineExpose({
  triggerSpeak: () => {
    if (live2dCharacter.value) {
      live2dCharacter.value.speak()
    }
  }
})
</script>

<style scoped>
.app-container {
  max-width: 800px;
  margin: 0 auto;
  box-shadow: 0 0 50px rgba(79, 70, 229, 0.15);
  max-height: 100vh;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* 装饰元素 */
.decorative-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.decor-circle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 58, 237, 0.1) 0%, rgba(124, 58, 237, 0) 70%);
  animation: float 6s ease-in-out infinite;
}

.decor-circle-1 {
  width: 200px;
  height: 200px;
  top: -50px;
  right: -50px;
  animation-delay: 0s;
}

.decor-circle-2 {
  width: 150px;
  height: 150px;
  bottom: -30px;
  left: -30px;
  animation-delay: 2s;
}

.decor-circle-3 {
  width: 100px;
  height: 100px;
  top: 50%;
  left: -20px;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) scale(1);
    opacity: 0.5;
  }
  50% {
    transform: translateY(-20px) scale(1.1);
    opacity: 0.8;
  }
}

.avatar-section {
  height: 30vh;
  min-height: 250px;
  max-height: 350px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 20px;
}

.chat-section {
  flex: 1;
  min-height: 200px;
  max-height: 40vh;
}

.control-section {
  flex-shrink: 0;
  min-height: 130px;
  max-height: 20vh;
}

@media (max-width: 768px) {
  .avatar-section {
    height: 25vh;
    min-height: 200px;
  }
  
  .chat-section {
    min-height: 150px;
  }
  
  .control-section {
    min-height: 120px;
  }
}

/* 针对小屏幕高度的额外调整 */
@media (max-height: 600px) {
  .avatar-section {
    height: 20vh;
    min-height: 150px;
  }
  
  .chat-section {
    min-height: 120px;
  }
  
  .control-section {
    min-height: 100px;
  }
}
</style>