# AI 语音助手 Vue3 前端

现代化的AI语音助手前端界面，使用Vue3 + Vite + Three.js构建，包含3D卡通人物、实时对话功能和流式输出。

## 功能特性

- 🎭 动态3D卡通人物
- 🎤 实时语音对话
- 💬 流式AI回复
- 🎵 实时音频处理
- 📱 响应式设计
- 🌟 现代化UI界面

## 技术栈

- **前端框架**: Vue 3
- **构建工具**: Vite
- **3D渲染**: Three.js
- **样式处理**: Tailwind CSS
- **状态管理**: Pinia
- **WebSocket**: 实时通信
- **音频处理**: Web Audio API

## 项目结构

```
vue3-frontend/
├── public/             # 静态资源
├── src/
│   ├── assets/         # 图片、音频等资源
│   ├── components/     # Vue组件
│   │   ├── Avatar3D/   # 3D卡通人物组件
│   │   ├── ChatPanel/  # 聊天面板组件
│   │   ├── ControlPanel/ # 控制面板组件
│   │   └── StatusBar/  # 状态栏组件
│   ├── composables/    # 组合式API
│   │   ├── useWebSocket.js # WebSocket通信
│   │   ├── useAudio.js # 音频处理
│   │   └── useAvatar.js # 3D头像控制
│   ├── stores/         # Pinia状态管理
│   │   ├── chat.js     # 聊天状态
│   │   └── audio.js    # 音频状态
│   ├── utils/          # 工具函数
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── index.html          # HTML模板
├── vite.config.js      # Vite配置
├── package.json        # 项目依赖
└── README.md           # 项目说明
```

## 安装与运行

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置相关参数：

```bash
cp .env.example .env
```

### 3. 开发模式运行

```bash
npm run dev
```

### 4. 构建生产版本

```bash
npm run build
```

## 核心功能实现

### 1. 3D卡通人物

使用Three.js实现动态3D卡通人物，支持：
- 面部表情动画
- 语音同步动画
- 互动响应

### 2. 实时对话系统

基于WebSocket的实时对话系统：
- 实时音频采集和传输
- 语音活动检测
- 流式AI响应

### 3. 流式输出

实现AI回复的流式输出：
- 文字逐字显示
- 语音逐段合成
- 实时状态反馈

### 4. 音频处理

使用Web Audio API处理音频：
- 音频采集和编码
- 音频播放和缓冲
- 音频质量优化

## 界面设计

### 布局结构

```
+----------------------------------------+
|                                        |
|            3D卡通人物区域              |
|                                        |
+----------------------------------------+
|                                        |
|            聊天记录区域                |
|                                        |
|                                        |
|                                        |
+----------------------------------------+
|                                        |
|        开始对话按钮 + 状态显示          |
|                                        |
+----------------------------------------+
```

### 交互流程

1. **初始化**：加载3D卡通人物，建立WebSocket连接
2. **开始对话**：点击开始对话按钮，请求麦克风权限
3. **语音采集**：实时采集音频并传输到服务器
4. **AI处理**：服务器进行语音识别、AI对话生成和语音合成
5. **流式输出**：前端接收流式AI回复，逐字显示并播放语音
6. **对话结束**：AI回复完成后，等待用户下一次输入

## 配置选项

### 环境变量

```env
# 后端WebSocket地址
VITE_WS_URL=ws://localhost:8765/ws

# 3D模型配置
VITE_AVATAR_MODEL=default
VITE_AVATAR_ANIMATIONS=true

# 音频配置
VITE_AUDIO_SAMPLE_RATE=16000
VITE_AUDIO_BUFFER_SIZE=4096

# 界面配置
VITE_THEME=light
VITE_ANIMATIONS=true
```

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 开发指南

### 添加新功能

1. 在 `src/components/` 目录创建新组件
2. 在 `src/composables/` 目录添加相关逻辑
3. 在 `src/stores/` 目录管理状态
4. 在 `src/utils/` 目录添加工具函数

### 自定义3D人物

1. 在 `public/models/` 目录添加3D模型
2. 修改 `src/components/Avatar3D/` 组件中的模型加载逻辑
3. 配置模型动画和交互行为

### 扩展对话功能

1. 在 `src/composables/useWebSocket.js` 中添加新的消息类型处理
2. 在 `src/stores/chat.js` 中添加相应的状态管理
3. 在 `src/components/ChatPanel/` 中添加UI展示

## 性能优化

- **3D渲染优化**: 使用LOD（多级细节）和实例化渲染
- **音频处理优化**: 使用Web Workers处理音频数据
- **网络优化**: 压缩音频数据，使用WebSocket二进制消息
- **UI优化**: 使用虚拟滚动处理长聊天记录

## 安全注意事项

- 确保HTTPS环境下使用麦克风权限
- 验证WebSocket连接的安全性
- 处理用户输入数据的验证
- 保护用户隐私和数据安全

## 部署说明

### 本地部署

1. 构建生产版本：`npm run build`
2. 启动本地服务器：`npm run preview`

### 生产部署

1. 构建生产版本：`npm run build`
2. 将 `dist/` 目录部署到Web服务器
3. 配置服务器支持WebSocket
4. 确保HTTPS环境

## 故障排除

### 麦克风权限问题

- 确保在HTTPS环境下访问
- 检查浏览器麦克风权限设置
- 刷新页面重试

### 3D人物加载失败

- 检查网络连接
- 确认Three.js依赖正确安装
- 查看浏览器控制台错误信息

### WebSocket连接失败

- 确认后端服务正在运行
- 检查WebSocket地址配置
- 查看网络连接状态

### 音频播放问题

- 检查扬声器设置
- 确认浏览器支持Web Audio API
- 查看音频数据格式是否正确

## 许可证

MIT License
