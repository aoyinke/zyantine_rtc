<template>
  <div class="live2d-container">
    <div ref="live2dContainer" class="live2d-container-inner">
      <canvas ref="canvas" class="live2d-canvas"></canvas>
    </div>
    <div v-if="isLoading" class="loading-indicator">
      <div class="loading-spinner"></div>
      <p>正在加载Live2D模型...</p>
    </div>
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="initLive2D" class="retry-button">重试</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Live2DCharacter',
  data() {
    return {
      isLoading: true,
      error: null,
      modelPath: '/live2d-models/hiyori_pro_zh/hiyori_pro_t11.model3.json',
      canvas: null,
      gl: null,
      cubismSDK: null,
      cubismFramework: null,
      model: null,
      renderer: null,
      animationFrameId: null,
      modelSettings: null,
      textures: [],
      textureCache: new Map(),
      userModel: null,
      motionManager: null,
      expressionManager: null,
      eyeBlink: null,
      breath: null,
      lastUpdateTime: 0,
      isVisible: true
    };
  },
  mounted() {
    console.log('=== Live2DCharacter 组件已挂载 ===');
    this.initLive2D();
    
    // 添加可见性监听
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        this.isVisible = entry.isIntersecting;
        if (!this.isVisible) {
          console.log('Live2D 组件不可见，暂停渲染');
          this.pauseAnimation();
        } else {
          console.log('Live2D 组件可见，恢复渲染');
          this.resumeAnimation();
        }
      });
    }, { threshold: 0.1 });
    
    if (this.$refs.live2dContainer) {
      this.observer.observe(this.$refs.live2dContainer);
    }
  },
  beforeUnmount() {
    if (this.observer) {
      this.observer.disconnect();
    }
    this.cleanup();
  },
  methods: {
    async initLive2D() {
      try {
        this.isLoading = true;
        this.error = null;
        
        console.log('=== 开始初始化Live2D ===');
        
        // 加载 Cubism SDK
        const loadSdkPromises = [];
        
        if (!window.Live2DCubismCore) {
          loadSdkPromises.push(this.loadScript('/cubism-sdk/live2dcubismcore.min.js'));
        }
        
        if (!window.Live2DCubismFramework) {
          loadSdkPromises.push(this.loadScript('/cubism-sdk/framework/live2dcubismframework.js'));
        }
        
        if (loadSdkPromises.length > 0) {
          console.log('并行加载 SDK 文件...');
          await Promise.all(loadSdkPromises);
          console.log('SDK 文件加载完成');
        }
        
        this.cubismSDK = window.Live2DCubismCore;
        this.cubismFramework = window.Live2DCubismFramework;
        
        // 检查 SDK 版本
        if (this.cubismSDK && typeof this.cubismSDK.getVersion === 'function') {
          console.log('Cubism SDK 版本:', this.cubismSDK.getVersion());
        } else {
          console.log('Cubism SDK 版本: 未知');
        }
        
        // 初始化 Cubism Framework
        console.log('初始化 Cubism Framework...');
        this.cubismFramework.initialize();
        console.log('Cubism Framework 初始化完成');
        
        // 获取 canvas 元素
        this.canvas = this.$refs.canvas;
        if (!this.canvas) {
          throw new Error('Canvas 元素未找到');
        }
        
        // 适配容器大小
        this.resizeCanvas();
        
        // 初始化 WebGL
        this.gl = this.canvas.getContext('webgl') || this.canvas.getContext('experimental-webgl');
        if (!this.gl) {
          throw new Error('浏览器不支持 WebGL');
        }
        console.log('WebGL 上下文创建成功:', this.gl);
        
        // 加载模型设置
        console.log('加载模型设置:', this.modelPath);
        const modelResponse = await fetch(this.modelPath);
        if (!modelResponse.ok) {
          throw new Error(`模型文件加载失败: ${modelResponse.status}`);
        }
        
        const modelSettingsJson = await modelResponse.json();
        const modelSettings = new this.cubismFramework.CubismModelSettingJson(modelSettingsJson);
        this.modelSettings = modelSettings;
        console.log('模型设置加载完成');
        
        // 并行加载 MOC3 和纹理
        console.log('并行加载模型资源...');
        
        const mocPath = `/live2d-models/hiyori_pro_zh/${modelSettings.getMocPath()}`;
        const mocPromise = fetch(mocPath)
          .then(response => {
            if (!response.ok) throw new Error(`MOC3 文件加载失败: ${response.status}`);
            return response.arrayBuffer();
          })
          .then(arrayBuffer => {
            console.log('MOC3 文件加载成功，大小:', arrayBuffer.byteLength, '字节');
            return arrayBuffer;
          });
        
        // 并行加载纹理
        const texturePromises = [];
        for (let i = 0; i < modelSettings.getTextureCount(); i++) {
          const texturePath = `/live2d-models/hiyori_pro_zh/${modelSettings.getTexturePath(i)}`;
          texturePromises.push(
            this.loadTexture(texturePath)
              .then(image => ({ index: i, image }))
              .catch(error => {
                console.error(`纹理 ${i} 加载失败:`, error);
                return null;
              })
          );
        }
        
        // 等待所有资源加载完成
        const [mocArrayBuffer, textureResults] = await Promise.all([mocPromise, Promise.all(texturePromises)]);
        console.log('模型资源加载完成');
        
        // 创建模型
        console.log('创建模型...');
        const moc = this.cubismSDK.Moc.fromArrayBuffer(mocArrayBuffer);
        this.model = moc.createModel();
        console.log('模型创建成功');
        
        // 初始化渲染器
        console.log('初始化渲染器...');
        this.renderer = this.cubismFramework.CubismRendererWebGL.create();
        this.renderer.initialize(this.gl, this.canvas.width, this.canvas.height);
        this.renderer.setModel(this.model);
        console.log('渲染器初始化成功');
        
        // 加载纹理
        console.log('设置纹理...');
        this.textures = [];
        
        textureResults.forEach(result => {
          if (result) {
            try {
              const texture = this.renderer.createTexture();
              this.renderer.setTexture(result.index, texture, result.image, false);
              this.textures.push(texture);
              console.log(`纹理 ${result.index} 设置成功`);
            } catch (error) {
              console.error(`纹理 ${result.index} 设置失败:`, error);
            }
          }
        });
        
        // 初始化管理器
        console.log('初始化管理器...');
        this.motionManager = new this.cubismFramework.CubismMotionManager();
        this.expressionManager = new this.cubismFramework.CubismExpressionMotionManager();
        this.eyeBlink = this.cubismFramework.CubismEyeBlink.create();
        this.breath = this.cubismFramework.CubismBreath.create();
        console.log('管理器初始化完成');
        
        // 设置模型参数
        console.log('设置模型参数...');
        this.model.saveParameters();
        
        // 加载默认动作
        console.log('加载默认动作...');
        const motionGroup = 'Idle';
        if (modelSettings.getMotionCount(motionGroup) > 0) {
          const motionIndex = 0;
          const motionPath = `/live2d-models/hiyori_pro_zh/${modelSettings.getMotionPath(motionGroup, motionIndex)}`;
          await this.loadMotion(motionGroup, motionPath);
        }
        
        // 开始动画循环
        this.lastUpdateTime = Date.now();
        this.startAnimationLoop();
        console.log('动画循环已启动');
        
        // 添加窗口大小变化监听
        window.addEventListener('resize', this.resizeCanvas);
        
        console.log('=== Live2D 初始化完成 ===');
        this.isLoading = false;
        
      } catch (err) {
        console.error('=== 初始化Live2D失败 ===', err);
        console.error('错误堆栈:', err.stack);
        this.error = `初始化失败: ${err.message}`;
        this.isLoading = false;
      }
    },
    resizeCanvas() {
      const container = this.$refs.live2dContainer;
      if (container) {
        const rect = container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        console.log('Canvas 大小调整为:', this.canvas.width, 'x', this.canvas.height);
        
        // 更新渲染器视口
        if (this.renderer) {
          this.renderer.setViewport(0, 0, this.canvas.width, this.canvas.height);
        }
      }
    },
    async loadTexture(url) {
      return new Promise((resolve, reject) => {
        const image = new Image();
        image.crossOrigin = 'anonymous';
        image.onload = () => {
          if (image.width === 0 || image.height === 0) {
            reject(new Error(`纹理加载失败: 图像尺寸无效 ${url}`));
            return;
          }
          resolve(image);
        };
        image.onerror = () => {
          reject(new Error(`纹理加载失败: ${url}`));
        };
        image.src = url;
      });
    },
    async loadMotion(group, path) {
      return new Promise((resolve, reject) => {
        fetch(path)
          .then(response => response.arrayBuffer())
          .then(arrayBuffer => {
            const motion = this.cubismFramework.CubismMotion.loadFromArray(arrayBuffer);
            this.motionManager.startMotionPriority(motion, group, 3, false);
            resolve();
          })
          .catch(error => {
            reject(error);
          });
      });
    },
    startAnimationLoop() {
      console.log('=== 开始动画循环 ===');
      
      const MAX_DELTA_TIME = 0.1; // 最大时间步长（100ms）
      const TARGET_FPS = 60; // 目标帧率
      const FRAME_INTERVAL = 1000 / TARGET_FPS; // 帧间隔
      
      let lastFrameTime = Date.now();
      let frameCount = 0;
      let lastFpsUpdateTime = Date.now();
      
      const update = () => {
        try {
          if (!this.isVisible) {
            this.animationFrameId = requestAnimationFrame(update);
            return;
          }
          
          const currentTime = Date.now();
          const deltaTime = Math.min((currentTime - this.lastUpdateTime) / 1000, MAX_DELTA_TIME);
          this.lastUpdateTime = currentTime;
          
          // 帧率控制
          const elapsedSinceLastFrame = currentTime - lastFrameTime;
          if (elapsedSinceLastFrame < FRAME_INTERVAL) {
            this.animationFrameId = requestAnimationFrame(update);
            return;
          }
          
          lastFrameTime = currentTime;
          frameCount++;
          
          // 每秒钟更新一次帧率
          if (currentTime - lastFpsUpdateTime >= 1000) {
            const fps = frameCount;
            console.log(`Live2D 帧率: ${fps} FPS`);
            frameCount = 0;
            lastFpsUpdateTime = currentTime;
          }
          
          if (this.model && this.renderer && this.gl) {
            // 检查WebGL上下文是否有效
            if (this.gl.isContextLost()) {
              console.warn('WebGL上下文丢失，尝试恢复...');
              this.animationFrameId = requestAnimationFrame(update);
              return;
            }
            
            // 更新模型
            this.model.update();
            
            // 更新运动
            if (this.motionManager) {
              this.motionManager.updateMotion(this.model, deltaTime);
            }
            
            // 更新表情
            if (this.expressionManager) {
              this.expressionManager.updateMotion(this.model, deltaTime);
            }
            
            // 更新眨眼
            if (this.eyeBlink) {
              this.eyeBlink.updateParameters(this.model, deltaTime);
            }
            
            // 更新呼吸
            if (this.breath) {
              this.breath.updateParameters(this.model, deltaTime);
            }
            
            // 渲染模型
            try {
              this.renderer.setViewport(0, 0, this.canvas.width, this.canvas.height);
              this.renderer.clearCanvas();
              this.renderer.drawModel();
            } catch (renderError) {
              console.error('渲染错误:', renderError);
            }
          }
        } catch (error) {
          console.error('动画循环错误:', error);
        }
        
        this.animationFrameId = requestAnimationFrame(update);
      };
      
      update();
    },
    loadScript(url) {
      return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.onload = () => {
          console.log('脚本加载成功:', url);
          resolve();
        };
        script.onerror = () => {
          console.error('脚本加载失败:', url);
          reject(new Error(`脚本加载失败: ${url}`));
        };
        document.head.appendChild(script);
      });
    },
    cleanup() {
      console.log('=== 清理Live2D资源 ===');
      
      // 移除窗口大小变化监听
      window.removeEventListener('resize', this.resizeCanvas);
      
      // 停止动画循环
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
        console.log('动画循环已停止');
      }
      
      // 释放模型资源
      if (this.model) {
        try {
          this.model.delete();
          console.log('模型资源已释放');
        } catch (error) {
          console.error('释放模型资源时出错:', error);
        }
      }
      
      // 释放渲染器资源
      if (this.renderer) {
        try {
          this.renderer.delete();
          console.log('渲染器资源已释放');
        } catch (error) {
          console.error('释放渲染器资源时出错:', error);
        }
      }
      
      // 释放管理器资源
      if (this.motionManager) {
        this.motionManager.delete();
      }
      
      if (this.expressionManager) {
        this.expressionManager.delete();
      }
      
      if (this.eyeBlink) {
        this.eyeBlink.delete();
      }
      
      if (this.breath) {
        this.breath.delete();
      }
      
      // 清空数组
      this.textures = [];
      
      console.log('=== Live2D资源清理完成 ===');
    },
    speak() {
      console.log('=== Live2D 角色说话 ===');
      
      // 这里可以添加说话动画的逻辑
      if (this.motionManager) {
        const motionGroup = 'Talk';
        if (this.modelSettings && this.modelSettings.getMotionCount(motionGroup) > 0) {
          const motionIndex = Math.floor(Math.random() * this.modelSettings.getMotionCount(motionGroup));
          const motionPath = `/live2d-models/hiyori_pro_zh/${this.modelSettings.getMotionPath(motionGroup, motionIndex)}`;
          this.loadMotion(motionGroup, motionPath);
        }
      }
    }
  }
};
</script>

<style scoped>
.live2d-container {
  position: relative;
  width: 100%;
  height: 350px;
  margin: 0 auto;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.live2d-container-inner {
  position: relative;
  width: 200px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.live2d-canvas {
  display: block;
  margin: 0 auto;
  width: 100%;
  height: 100%;
}

.loading-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #333;
  z-index: 10;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #e74c3c;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.retry-button {
  margin-top: 10px;
  padding: 8px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s;
}

.retry-button:hover {
  background: #2980b9;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .live2d-container {
    height: 250px;
  }
  
  .live2d-container-inner {
    width: 150px;
    height: 200px;
  }
}
</style>