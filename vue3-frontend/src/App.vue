<template>
  <div class="app-container">
    <h1 class="app-title">AI 语音助手</h1>
    
    <div class="main-content">
      <!-- 左边：聊天对话历史、开始对话按钮和动态显示 -->
      <div class="left-section">
        <div class="chat-history-section">
          <ChatPanel />
        </div>
        <div class="control-section">
          <ControlPanel />
        </div>
      </div>
      
      <!-- 右边：人物模型 -->
      <div class="right-section">
        <Live2DAvatar />
      </div>
    </div>
  </div>
</template>

<script setup>
import ControlPanel from './components/ControlPanel/ControlPanel.vue';
import ChatPanel from './components/ChatPanel/ChatPanel.vue';
import Live2DAvatar from './components/Live2DAvatar/Live2DAvatar.vue';
</script>

<style>
.app-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
  overflow: hidden;
}

.app-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  text-align: center;
  padding: 1rem;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 1rem;
  background-color: #f5f5f5;
  border-right: 1px solid #e5e7eb;
}

.chat-history-section {
  flex: 1;
  overflow: hidden;
  margin-bottom: 1rem;
}

.control-section {
  flex: 0 0 auto;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.right-section {
  flex: 0 0 400px;
  min-width: 300px;
  max-width: 500px;
  background-color: white;
  position: relative;
  border-left: 1px solid #e5e7eb;
}

/* 响应式布局调整 */
@media (max-width: 1024px) {
  .right-section {
    flex: 0 0 350px;
    min-width: 250px;
    max-width: 400px;
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .left-section {
    flex: 2;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .right-section {
    flex: 1;
    min-height: 300px;
    border-left: none;
    border-top: 1px solid #e5e7eb;
  }
  
  .app-title {
    font-size: 1.25rem;
    padding: 0.75rem;
  }
  
  .left-section {
    padding: 0.75rem;
  }
}

@media (max-width: 480px) {
  .app-title {
    font-size: 1.125rem;
    padding: 0.5rem;
  }
  
  .left-section {
    padding: 0.5rem;
  }
  
  .right-section {
    min-height: 250px;
  }
}
</style>