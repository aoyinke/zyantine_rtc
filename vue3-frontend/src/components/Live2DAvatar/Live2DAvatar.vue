<template>
  <div class="live2d-container" @mouseenter="onMouseEnter" @mouseleave="onMouseLeave">
    <!-- 气泡容器 -->
    <div v-if="showBubble" class="bubble-container animate-bubble">
      <div class="bubble-content">{{ bubbleText }}</div>
      <div class="bubble-arrow"></div>
    </div>
    
    <canvas ref="liveCanvas" class="live2d-canvas"></canvas>
    
    <!-- 加载状态 -->
    <div v-if="is_loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">加载中...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, onMounted, onBeforeUnmount, watch, computed } from 'vue';
import * as PIXI from 'pixi.js';
// 只需要 Cubism 4
import { Live2DModel } from 'pixi-live2d-display/cubism4';
import { useChatStore } from '../../stores/chat';

// 将 PIXI 暴露到 window 对象，以便运行库能够一次使用全部方法
window.PIXI = PIXI;

// 为了存储pixi实例
const app = ref();
// 为了存储live2d实例
const model = ref();
// 便签绑定
const liveCanvas = shallowRef();
// 模型是否运动
const is_moving = ref(false);
// 模型是否加载中
const is_loading = ref(false);
// 气泡显示状态
const showBubble = ref(false);
// 气泡文本
const bubbleText = ref('');
// 气泡显示计时器
const bubbleTimer = ref(null);

// 动作管理
const actionQueue = ref([]);
const isActionPlaying = ref(false);
const currentAction = ref(null);

// 表情参数
const expressionParams = ref({
  happiness: 0,
  sadness: 0,
  surprise: 0,
  anger: 0
});

// 聊天存储
const chatStore = useChatStore();

// 模型路径
const modelPath = '/live2d-models/hiyori_pro_zh/hiyori_pro_t11.model3.json';

// 可用动作列表
const availableActions = {
  idle: ['Idle'],
  tap: ['Tap'],
  tapBody: ['Tap@Body'],
  flick: ['Flick'],
  flickDown: ['FlickDown'],
  flickUp: ['FlickUp']
};

// 动作优先级
const actionPriorities = {
  tap: 3,
  tapBody: 3,
  flick: 2,
  flickDown: 2,
  flickUp: 2,
  idle: 1
};

// 关键词到动作的映射
const keywordToAction = {
  你好: 'idle',
  嗨: 'idle',
  早上好: 'idle',
  晚上好: 'idle',
  谢谢: 'idle',
  谢谢: 'idle',
  真棒: 'idle',
  厉害: 'idle',
  为什么: 'idle',
  什么: 'idle',
  怎么: 'idle'
};

// 计算属性：获取当前AI消息
const currentAIMessage = computed(() => chatStore.currentAIMessage);

// 计算属性：获取聊天状态
const chatStatus = computed(() => chatStore.status);

// 加载模型的函数
const loadModel = async () => {
  // 如果已经有模型存在，先销毁
  if (model.value) {
    app.value.stage.removeChild(model.value);
    model.value.destroy();
    model.value = null;
  }
  
  is_loading.value = true;
  
  try {
    console.log('开始加载模型:', modelPath);
    // 加载新模型
    model.value = await Live2DModel.from(modelPath);
    console.log('模型加载成功:', model.value);
    
    // 直接引入模型
    app.value.stage.addChild(model.value);
    // 确保模型在舞台的最上层
    app.value.stage.setChildIndex(model.value, app.value.stage.children.length - 1);
    
    // 获取容器大小
    const container = liveCanvas.value.parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    console.log('容器大小:', { width, height });
    
    // 调整缩放比例，根据容器高度计算
    const scale = 0.2; // 增加缩放比例，使模型更大更醒目
    model.value.scale.set(scale);
    console.log('模型缩放比例:', scale);
    
    // 调整渲染位置，使其在容器中居中显示（减少向左偏移，调整Y坐标以垂直居中）
    model.value.position.set(width / 2 - 300, height * 0.3);
    console.log('模型位置:', { x: width / 2 - 300, y: height * 0.3 });
    
    // 确保模型可见
    model.value.visible = true;
    model.value.alpha = 1;
    
    model.value.autoInteract = true; // 启用自动交互
    console.log('自动交互已启用');
    
    // 初始化表情参数
    initExpressionParams();
    
  } catch (error) {
    console.error('加载模型失败:', error);
    console.error('错误详情:', error.message);
  } finally {
    is_loading.value = false;
  }
};

// 初始化表情参数
const initExpressionParams = () => {
  if (model.value && model.value.internalModel) {
    const params = model.value.internalModel.parameters;
    console.log('可用参数:', params);
  }
};

// 调整模型大小和位置
const resizeModel = () => {
  if (!model.value || !liveCanvas.value) return;
  
  // 获取容器大小
  const container = liveCanvas.value.parentElement;
  const width = container.clientWidth;
  const height = container.clientHeight;
  
  // 调整模型位置，使其在容器中居中显示（减少向左偏移，调整Y坐标以垂直居中）
  model.value.position.set(width / 2 - 300, height * 0.3);
  
  // 调整缩放比例
  const scale = 0.15; // 增加缩放比例，使模型更大更醒目
  model.value.scale.set(scale);
  
  console.log('模型已调整大小和位置:', { width, height, scale });
};

// 显示气泡
const showBubbleMessage = (text) => {
  if (!text || text.trim() === '') return;
  
  // 清除之前的计时器
  if (bubbleTimer.value) {
    clearTimeout(bubbleTimer.value);
  }
  
  bubbleText.value = text;
  showBubble.value = true;
  
  // 3秒后隐藏气泡
  bubbleTimer.value = setTimeout(() => {
    showBubble.value = false;
  }, 3000);
};

// 动作管理器 - 添加动作到队列
const addActionToQueue = (actionType, priority = 1) => {
  if (!model.value) return;
  
  // 检查动作是否存在
  if (!availableActions[actionType]) {
    console.warn(`动作类型 ${actionType} 不存在`);
    return;
  }
  
  // 创建动作对象
  const action = {
    type: actionType,
    priority: priority,
    timestamp: Date.now()
  };
  
  // 添加到队列
  actionQueue.value.push(action);
  
  // 排序队列（按优先级和时间戳）
  actionQueue.value.sort((a, b) => {
    if (a.priority !== b.priority) {
      return b.priority - a.priority;
    }
    return a.timestamp - b.timestamp;
  });
  
  // 如果没有动作在播放，开始执行队列
  if (!isActionPlaying.value) {
    processActionQueue();
  }
};

// 处理动作队列
const processActionQueue = async () => {
  if (actionQueue.value.length === 0 || isActionPlaying.value) return;
  
  // 获取下一个动作
  const nextAction = actionQueue.value.shift();
  currentAction.value = nextAction;
  isActionPlaying.value = true;
  
  try {
    // 执行动作
    await playAction(nextAction.type);
  } catch (error) {
    console.error('执行动作失败:', error);
  } finally {
    isActionPlaying.value = false;
    currentAction.value = null;
    
    // 继续处理队列
    if (actionQueue.value.length > 0) {
      processActionQueue();
    }
  }
};

// 播放动作
const playAction = async (actionType) => {
  if (!model.value) return;
  
  try {
    const actions = availableActions[actionType];
    if (actions && actions.length > 0) {
      // 随机选择一个动作
      const randomAction = actions[Math.floor(Math.random() * actions.length)];
      console.log('播放动作:', randomAction);
      
      // 播放动作
      await model.value.motion(randomAction);
    }
  } catch (error) {
    console.warn('动作执行失败:', error);
    // 尝试使用默认动作
    try {
      await model.value.motion('Idle');
    } catch (e) {
      console.warn('默认动作也执行失败:', e);
    }
  }
};

// 设置表情
const setExpression = (expression, intensity = 1) => {
  if (!model.value || !model.value.internalModel) return;
  
  // 重置所有表情参数
  Object.keys(expressionParams.value).forEach(key => {
    expressionParams.value[key] = 0;
  });
  
  // 设置目标表情
  if (expressionParams.value.hasOwnProperty(expression)) {
    expressionParams.value[expression] = intensity;
  }
  
  // 应用表情参数
  applyExpression();
};

// 应用表情
const applyExpression = () => {
  if (!model.value || !model.value.internalModel) return;
  
  const params = model.value.internalModel.parameters;
  
  // 根据表情参数调整模型参数
  // 这里需要根据具体模型的参数名称进行调整
  if (params) {
    // 示例：调整眉毛和嘴巴参数
    // 实际参数名称需要根据模型配置进行修改
    if (params['ParamBrowUplift']) {
      params['ParamBrowUplift'] = expressionParams.value.happiness * 0.5 - expressionParams.value.sadness * 0.3;
    }
    
    if (params['ParamMouthSmile']) {
      params['ParamMouthSmile'] = expressionParams.value.happiness * 0.5 - expressionParams.value.sadness * 0.3 - expressionParams.value.anger * 0.2;
    }
    
    if (params['ParamEyeOpen']) {
      params['ParamEyeOpen'] = 1.0 - expressionParams.value.sadness * 0.2;
    }
  }
};

// 情感识别
const analyzeEmotion = (text) => {
  if (!text) return 'neutral';
  
  const lowerText = text.toLowerCase();
  
  // 正面情感关键词
  const positiveKeywords = ['好', '开心', '高兴', '谢谢', '真棒', '厉害', '喜欢', '爱', '棒', '优秀'];
  
  // 负面情感关键词
  const negativeKeywords = ['不', '不好', '难过', '伤心', '生气', '讨厌', '恨', '坏', '差', '糟糕'];
  
  // 疑问关键词
  const questionKeywords = ['?', '？', '为什么', '什么', '怎么', '怎样', '哪里', '何时', '谁'];
  
  // 惊讶关键词
  const surpriseKeywords = ['！', '!', '哇', '哦', '啊', '天哪', '真的吗', '不敢相信'];
  
  // 检测情感
  for (const keyword of positiveKeywords) {
    if (lowerText.includes(keyword)) {
      return 'happy';
    }
  }
  
  for (const keyword of negativeKeywords) {
    if (lowerText.includes(keyword)) {
      return 'sad';
    }
  }
  
  for (const keyword of surpriseKeywords) {
    if (lowerText.includes(keyword)) {
      return 'surprised';
    }
  }
  
  for (const keyword of questionKeywords) {
    if (lowerText.includes(keyword)) {
      return 'questioning';
    }
  }
  
  return 'neutral';
};

// 根据文本触发动作
const triggerActionFromText = (text) => {
  if (!text) return;
  
  // 分析情感
  const emotion = analyzeEmotion(text);
  console.log('识别到情感:', emotion);
  
  // 根据情感设置表情
  switch (emotion) {
    case 'happy':
      setExpression('happiness', 0.8);
      addActionToQueue('idle', 2);
      break;
    case 'sad':
      setExpression('sadness', 0.8);
      addActionToQueue('idle', 2);
      break;
    case 'surprised':
      setExpression('surprise', 0.8);
      addActionToQueue('flick', 3);
      break;
    case 'questioning':
      addActionToQueue('idle', 2);
      break;
    default:
      setExpression('happiness', 0.3);
      addActionToQueue('idle', 1);
  }
  
  // 检测关键词
  const lowerText = text.toLowerCase();
  for (const [keyword, action] of Object.entries(keywordToAction)) {
    if (lowerText.includes(keyword)) {
      addActionToQueue(action, 2);
      break;
    }
  }
};

// 鼠标进入事件
const onMouseEnter = () => {
  // 触发眨眼和轻微歪头动作
  if (model.value) {
    addActionToQueue('idle', 2);
    // 显示欢迎气泡
    showBubbleMessage('你好呀！有什么可以帮你的吗？');
    // 设置开心表情
    setExpression('happiness', 0.5);
  }
};

// 鼠标离开事件
const onMouseLeave = () => {
  // 重置表情
  setExpression('happiness', 0.1);
};

// 鼠标移动事件
const onMouseMove = (event) => {
  if (!model.value) return;
  
  // 获取鼠标位置
  const rect = liveCanvas.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  
  // 获取容器中心
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  
  // 计算鼠标与中心的距离
  const dx = (x - centerX) / centerX;
  const dy = (y - centerY) / centerY;
  
  // 限制移动范围
  const maxRotation = 0.1;
  const rotationX = Math.max(-maxRotation, Math.min(maxRotation, -dy * 0.5));
  const rotationY = Math.max(-maxRotation, Math.min(maxRotation, dx * 0.5));
  
  // 应用旋转
  if (model.value.internalModel) {
    const params = model.value.internalModel.parameters;
    if (params) {
      if (params['ParamAngleX']) {
        params['ParamAngleX'] = rotationX;
      }
      if (params['ParamAngleY']) {
        params['ParamAngleY'] = rotationY;
      }
    }
  }
};

// 鼠标点击事件
const onMouseClick = (event) => {
  if (!model.value) return;
  
  // 获取点击位置
  const rect = liveCanvas.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  
  // 获取容器中心
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  
  // 计算点击位置与中心的距离
  const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
  
  // 根据点击位置触发不同动作
  if (distance < 100) {
    // 点击头部
    addActionToQueue('tap', 3);
    showBubbleMessage('哎呀，你戳到我了！');
    setExpression('surprise', 0.8);
  } else if (distance < 200) {
    // 点击身体
    addActionToQueue('tapBody', 3);
    showBubbleMessage('哈哈，好痒！');
    setExpression('happiness', 0.8);
  } else {
    // 点击其他位置
    addActionToQueue('tap', 2);
    showBubbleMessage('你好！');
    setExpression('happiness', 0.5);
  }
};

// 监听AI消息变化
watch(currentAIMessage, (newMessage) => {
  if (newMessage) {
    showBubbleMessage(newMessage);
    // 触发说话动作
    if (model.value) {
      addActionToQueue('idle', 2);
      // 分析消息内容，触发相应动作
      triggerActionFromText(newMessage);
    }
  }
});

// 监听聊天状态变化
watch(chatStatus, (newStatus) => {
  switch (newStatus) {
    case 'processing':
    case 'generating':
      // 触发思考动作
      if (model.value) {
        addActionToQueue('idle', 2);
        setExpression('happiness', 0.2);
      }
      break;
    case 'playing':
      // 触发说话动作
      if (model.value) {
        addActionToQueue('idle', 2);
        setExpression('happiness', 0.5);
      }
      break;
  }
});

// 页面dom构建完成就执行
onMounted(async () => {
  // 获取容器元素的大小
  const container = liveCanvas.value.parentElement;
  const width = container.clientWidth;
  const height = container.clientHeight;
  
  console.log('初始化PIXI应用，容器大小:', { width, height });
  
  app.value = new PIXI.Application({
    view: liveCanvas.value, //ref组件绑定，liveCanvas为下文自定义的
    width: width,
    height: height,
    autoStart: true, //是否开启自动播放
    resizeTo: container, // 调整大小以适应容器
    interaction: {
      autoPreventDefault: true,
      pointerFrequency: 0.01
    }, // 确保启用交互系统
    backgroundAlpha: 0, //背景透明
    resolution: window.devicePixelRatio || 1, // 使用设备像素比提高清晰度
    antialias: true, // 开启抗锯齿
    transparent: true // 确保画布透明
  });
  
  console.log('PIXI应用创建成功:', app.value);
  
  // 初始加载模型
  await loadModel();
  
  // 添加事件监听
  if (model.value) {
    // 点击事件
    model.value.on('pointerdown', onMouseClick);
    
    // 鼠标移动事件
    liveCanvas.value.addEventListener('mousemove', onMouseMove);
  }
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', resizeModel);
});

// 组件卸载前销毁资源
onBeforeUnmount(() => {
  // 移除窗口大小变化监听
  window.removeEventListener('resize', resizeModel);
  
  // 移除鼠标移动事件监听
  if (liveCanvas.value) {
    liveCanvas.value.removeEventListener('mousemove', onMouseMove);
  }
  
  // 清除计时器
  if (bubbleTimer.value) {
    clearTimeout(bubbleTimer.value);
  }
  
  if (model.value) {
    model.value.destroy();
    model.value = null;
  }
  if (app.value) {
    app.value.destroy();
    app.value = null;
  }
  console.log('Live2D组件已销毁');
});
</script>

<style scoped>
.live2d-container {
  position: relative;
  width: 100%;
  height: 100%;
  z-index: 10;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: var(--bg);
  transition: all 0.3s ease;
}

.live2d-canvas {
  width: 100%;
  height: 100%;
  pointer-events: auto;
  display: block;
}

/* 气泡容器 */
.bubble-container {
  position: absolute;
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  max-width: 80%;
  z-index: 20;
  animation: bubble-appear 0.3s ease-out forwards;
}

.bubble-content {
  background: linear-gradient(135deg, #fff3f3 0%, #fef3c7 100%);
  color: var(--text-primary);
  padding: 12px 16px;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.15);
  border: 1px solid var(--primary-light);
  font-size: 14px;
  line-height: 1.4;
  word-wrap: break-word;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.bubble-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 107, 107, 0.1), transparent);
  animation: shine 3s ease-in-out infinite;
}

.bubble-arrow {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 8px solid #fef3c7;
}

/* 新增动画效果 */
@keyframes shine {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

/* 加载覆盖层 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 30;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--secondary);
  border-top: 3px solid var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

.loading-text {
  color: var(--text-main);
  font-size: 14px;
  transition: all 0.3s ease;
}

/* 动画效果 */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes bubble-appear {
  from {
    opacity: 0;
    transform: translateX(-50%) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) scale(1);
  }
}

.animate-bubble {
  animation: bubble-appear 0.3s ease-out forwards;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .bubble-content {
    font-size: 12px;
    padding: 10px 14px;
  }
  
  .bubble-container {
    top: 10%;
    max-width: 90%;
  }
}
</style>