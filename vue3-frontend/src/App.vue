<template>
  <Transition name="fade">
    <div class="app-container" :class="{ dark: isDarkMode }">
      <!-- 顶部标题栏 -->
      <header class="app-header">
        <div class="header-content container">
          <div class="app-logo animate-fade-in">
            <div class="logo-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="11" r="8"></circle>
                <path d="M8 14s1.5 2 4 2 4-2 4-2"></path>
                <line x1="9" y1="9" x2="9.01" y2="9"></line>
                <line x1="15" y1="9" x2="15.01" y2="9"></line>
                <path d="M12 2v2"></path>
                <path d="M12 20v2"></path>
                <path d="M4.93 4.93l1.41 1.41"></path>
                <path d="M17.66 17.66l1.41 1.41"></path>
                <path d="M2 12h2"></path>
                <path d="M20 12h2"></path>
                <path d="M4.93 19.07l1.41-1.41"></path>
                <path d="M17.66 6.34l1.41-1.41"></path>
              </svg>
            </div>
            <h1 class="app-title">小叶同学</h1>
          </div>
          <div class="header-actions">
            <button class="theme-toggle" @click="toggleDarkMode" aria-label="切换主题">
              <svg v-if="!isDarkMode" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
              </svg>
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
              </svg>
            </button>
            <button class="info-button" @click="showInfo = !showInfo" aria-label="显示信息">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="16" x2="12" y2="12"></line>
                <line x1="12" y1="8" x2="12.01" y2="8"></line>
              </svg>
            </button>
          </div>
        </div>
      </header>
      
      <!-- 信息提示 -->
      <div v-if="showInfo" class="info-bar animate-slide-down">
        <div class="info-content container">
          <p>👋 你好！我是小叶同学，很高兴认识你！有什么想聊的吗？</p>
          <button class="close-info" @click="showInfo = false">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      
      <main class="main-content container">
        <div class="content-grid">
          <!-- 左边：聊天对话历史、开始对话按钮和动态显示 -->
          <div class="left-section">
            <!-- 聊天历史卡片 -->
            <div class="chat-card card animate-slide-in">
              <ChatPanel />
            </div>
            
            <!-- 控制面板卡片 -->
            <div class="control-card card animate-slide-in" style="animation-delay: 0.1s">
              <ControlPanel />
            </div>
          </div>
          
          <!-- 右边：人物模型 -->
          <div class="right-section">
            <div class="avatar-card card animate-slide-in" style="animation-delay: 0.2s">
              <Live2DAvatar />
            </div>
          </div>
        </div>
      </main>
      
      <!-- 背景装饰 -->
      <div class="background-decorations">
        <div class="decor-circle decor-1"></div>
        <div class="decor-circle decor-2"></div>
        <div class="decor-circle decor-3"></div>
        <!-- 小叶同学专属装饰 -->
        <div class="decor-heart decor-4"></div>
        <div class="decor-star decor-5"></div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import ControlPanel from './components/ControlPanel/ControlPanel.vue';
import ChatPanel from './components/ChatPanel/ChatPanel.vue';
import Live2DAvatar from './components/Live2DAvatar/Live2DAvatar.vue';

// 深色模式状态
const isDarkMode = ref(false);
// 显示信息状态
const showInfo = ref(false);

// 切换深色模式
function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem('darkMode', isDarkMode.value);
  updateDocumentClass();
}

// 更新文档类
function updateDocumentClass() {
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

// 初始化深色模式
onMounted(() => {
  const savedDarkMode = localStorage.getItem('darkMode');
  if (savedDarkMode !== null) {
    isDarkMode.value = savedDarkMode === 'true';
  } else {
    // 默认根据系统偏好
    isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  updateDocumentClass();
  
  // 显示欢迎信息
  setTimeout(() => {
    showInfo.value = true;
  }, 1000);
});

// 监听系统偏好变化
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
const handleMediaQueryChange = (e) => {
  if (localStorage.getItem('darkMode') === null) {
    isDarkMode.value = e.matches;
    updateDocumentClass();
  }
};

onMounted(() => {
  mediaQuery.addEventListener('change', handleMediaQueryChange);
});

onUnmounted(() => {
  mediaQuery.removeEventListener('change', handleMediaQueryChange);
});
</script>

<style>
/* 全局样式 */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

.app-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-gradient);
  color: var(--text-primary);
  overflow: hidden;
  transition: all var(--transition-normal);
  position: relative;
}

/* 顶部标题栏 */
.app-header {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  box-shadow: var(--shadow-md);
  z-index: 100;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.app-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: headerShine 3s ease-in-out infinite;
}

@keyframes headerShine {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-4);
  width: 100%;
  position: relative;
  z-index: 1;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  transition: all 0.3s ease;
}

.app-logo:hover {
  transform: translateX(8px);
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.logo-icon:hover {
  transform: scale(1.1);
  background: rgba(255, 255, 255, 0.3);
}

.app-logo svg {
  color: white;
  width: 28px;
  height: 28px;
  transition: all 0.3s ease;
}

.app-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  margin: 0;
  color: white;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.header-actions {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}

.theme-toggle {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: var(--radius-full);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-normal);
  color: white;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.info-button {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: var(--radius-full);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-normal);
  color: white;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.info-button:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

/* 信息提示栏 */
.info-bar {
  background: linear-gradient(135deg, var(--secondary), var(--primary));
  color: white;
  box-shadow: var(--shadow-md);
  z-index: 90;
  transition: all var(--transition-normal);
  position: relative;
}

.info-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  width: 100%;
}

.info-content p {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.close-info {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: var(--radius-full);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-normal);
  color: white;
}

.close-info:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

/* 主内容区域 */
.main-content {
  flex: 1;
  overflow: hidden;
  padding: var(--space-6);
  position: relative;
  z-index: 1;
}

.content-grid {
  display: grid;
  grid-template-columns: 70% 30%;
  gap: var(--space-6);
  height: 100%;
  overflow: hidden;
}

/* 左侧区域 */
.left-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  overflow: hidden;
}

.chat-card {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.control-card {
  flex: 0 0 auto;
}

/* 右侧区域 */
.right-section {
  overflow: hidden;
}

.avatar-card {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 卡片样式 */
.card {
  background: var(--bg-light);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-md);
  transition: all var(--transition-normal);
  overflow: hidden;
  position: relative;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.card:hover::before {
  transform: scaleX(1);
}

/* 背景装饰 */
.background-decorations {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.decor-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(99, 102, 241, 0.1);
  backdrop-filter: blur(20px);
  animation: float 6s ease-in-out infinite;
  transition: all 0.3s ease;
}

.decor-1 {
  width: 300px;
  height: 300px;
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.decor-2 {
  width: 200px;
  height: 200px;
  bottom: -50px;
  left: -50px;
  animation-delay: 2s;
}

.decor-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  left: -75px;
  animation-delay: 4s;
}

/* 小叶同学专属装饰 */
.decor-heart {
  position: absolute;
  width: 60px;
  height: 60px;
  background: rgba(255, 107, 107, 0.2);
  backdrop-filter: blur(20px);
  animation: float 6s ease-in-out infinite;
  transition: all 0.3s ease;
  transform: rotate(45deg);
}

.decor-heart::before,
.decor-heart::after {
  content: '';
  position: absolute;
  width: 60px;
  height: 60px;
  background: rgba(255, 107, 107, 0.2);
  border-radius: 50%;
}

.decor-heart::before {
  top: -30px;
  left: 0;
}

.decor-heart::after {
  top: 0;
  left: -30px;
}

.decor-star {
  position: absolute;
  width: 40px;
  height: 40px;
  background: rgba(78, 205, 196, 0.2);
  backdrop-filter: blur(20px);
  animation: float 8s ease-in-out infinite;
  transition: all 0.3s ease;
  clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%);
}

.decor-4 {
  top: 20%;
  right: 10%;
  animation-delay: 2s;
}

.decor-5 {
  bottom: 30%;
  right: 5%;
  animation-delay: 5s;
}

/* 动画效果 */
@keyframes float {
  0%, 100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-20px) scale(1.05);
  }
}

/* 心形装饰动画 */
@keyframes pulse-heart {
  0%, 100% {
    transform: rotate(45deg) scale(1);
  }
  50% {
    transform: rotate(45deg) scale(1.1);
  }
}

.decor-heart {
  animation: float 6s ease-in-out infinite, pulse-heart 2s ease-in-out infinite;
}

/* 星星装饰动画 */
@keyframes twinkle {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

.decor-star {
  animation: float 8s ease-in-out infinite, twinkle 3s ease-in-out infinite;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slideIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

.animate-slide-down {
  animation: slideDown 0.4s ease-out forwards;
}

.animate-fade-in {
  animation: fadeIn 0.6s ease-out forwards;
}

/* 页面入场动画 */
.fade-enter-from {
  opacity: 0;
}

.fade-enter-active {
  transition: opacity var(--transition-slow);
}

.fade-enter-to {
  opacity: 1;
}

/* 响应式调整 */

/* 桌面端 */
@media (min-width: 1024px) {
  .content-grid {
    grid-template-columns: 70% 30%;
  }
}

/* 平板端 */
@media (max-width: 1023px) and (min-width: 768px) {
  .content-grid {
    grid-template-columns: 60% 40%;
  }
  
  .main-content {
    padding: var(--space-4);
  }
  
  .content-grid {
    gap: var(--space-4);
  }
  
  .header-content {
    padding: var(--space-4);
  }
  
  .app-title {
    font-size: var(--text-xl);
  }
  
  .logo-icon {
    width: 40px;
    height: 40px;
  }
  
  .app-logo svg {
    width: 24px;
    height: 24px;
  }
  
  .theme-toggle,
  .info-button {
    width: 40px;
    height: 40px;
  }
}

/* 移动端 */
@media (max-width: 767px) {
  .content-grid {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
  }
  
  .main-content {
    padding: var(--space-3);
  }
  
  .content-grid {
    gap: var(--space-3);
  }
  
  .header-content {
    padding: var(--space-4) var(--space-3);
  }
  
  .app-title {
    font-size: var(--text-lg);
  }
  
  .theme-toggle,
  .info-button {
    width: 36px;
    height: 36px;
  }
  
  .logo-icon {
    width: 36px;
    height: 36px;
  }
  
  .app-logo svg {
    width: 20px;
    height: 20px;
  }
  
  .header-actions {
    gap: var(--space-2);
  }
  
  .right-section {
    max-height: 250px;
  }
  
  .info-content p {
    font-size: var(--text-xs);
  }
  
  .decor-circle {
    display: none;
  }
}

/* 小屏幕移动端 */
@media (max-width: 480px) {
  .main-content {
    padding: var(--space-2);
  }
  
  .content-grid {
    gap: var(--space-2);
  }
  
  .right-section {
    max-height: 200px;
  }
  
  .app-title {
    font-size: var(--text-base);
  }
}
</style>