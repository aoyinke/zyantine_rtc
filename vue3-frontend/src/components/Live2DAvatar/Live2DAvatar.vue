<template>
  <div class="live2d-container">
    <canvas ref="liveCanvas" class="live2d-canvas"></canvas>
  </div>
</template>

<script setup>
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import * as PIXI from 'pixi.js';
// 只需要 Cubism 4
import { Live2DModel } from 'pixi-live2d-display/cubism4';

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

// 模型路径
const modelPath = '/live2d-models/hiyori_pro_zh/hiyori_pro_t11.model3.json';

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
    const scale = 0.1; // 使用固定缩放比例，确保模型可见
    model.value.scale.set(scale);
    console.log('模型缩放比例:', scale);
    
    // 调整渲染位置，使其在容器中居中显示
    model.value.position.set(width / 2, height / 2);
    console.log('模型位置:', { x: width / 2, y: height / 2 });
    
    // 确保模型可见
    model.value.visible = true;
    model.value.alpha = 1;
    
    model.value.autoInteract = true; // 启用自动交互
    console.log('自动交互已启用');
    
  } catch (error) {
    console.error('加载模型失败:', error);
    console.error('错误详情:', error.message);
  } finally {
    is_loading.value = false;
  }
};

// 调整模型大小和位置
const resizeModel = () => {
  if (!model.value || !liveCanvas.value) return;
  
  // 获取容器大小
  const container = liveCanvas.value.parentElement;
  const width = container.clientWidth;
  const height = container.clientHeight;
  
  // 调整模型位置，使其在容器中居中显示
  model.value.position.set(width / 2, height / 2);
  
  // 调整缩放比例
  const scale = 0.1; // 使用固定缩放比例，确保模型可见
  model.value.scale.set(scale);
  
  console.log('模型已调整大小和位置:', { width, height, scale });
};

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
  
  // 添加点击事件监听
  if (model.value) {
    model.value.on('pointerdown', (event) => {
      console.log('模型被点击', event.data.global);
      // 触发点击动作
      if (model.value) {
        console.log('触发点击动作');
        model.value.motion('Tap');
      }
    });
  }
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', resizeModel);
});

// 组件卸载前销毁资源
onBeforeUnmount(() => {
  // 移除窗口大小变化监听
  window.removeEventListener('resize', resizeModel);
  
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
}

.live2d-canvas {
  width: 100%;
  height: 100%;
  pointer-events: auto;
  display: block;
}
</style>