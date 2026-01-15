# AI 语音助手系统

一个基于Python的纯语音交互AI助手系统，使用Web界面实现实时语音对话。

## 功能特性

- 纯语音交互界面，无需文本输入
- 实时音频采集和传输
- AI语音识别（STT）- 使用字节跳动语音识别
- AI语音合成（TTS）- 使用火山引擎豆包语音合成
- AI对话 - 使用自衍体 AI 系统
- 语音活动检测（VAD）
- 现代化的Web界面设计（Vue 3）
- 实时状态反馈和动态提示

## 系统要求

- Python 3.8+
- 麦克风和扬声器
- 自衍体 API 服务（本地运行或远程）
- 火山引擎API密钥（用于TTS）

## 安装步骤

### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd vue3-frontend
npm install
```

### 3. 配置文件

复制 `config.example.json` 为 `config.json` 并配置你的API密钥：

```bash
cp config.example.json config.json
```

编辑 `config.json` 文件，设置你的API密钥：

```json
{
  "zyantine": {
    "api_key": "",
    "base_url": "http://localhost:8001",
    "model": "zyantine-v1"
  },
  "stt": {
    "bytedance": {
      "app_key": "your_bytedance_app_key_here",
      "access_key": "your_bytedance_access_key_here",
      "ws_url": "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream"
    }
  },
  "tts": {
    "volcengine": {
      "appid": "your_volcengine_app_id_here",
      "access_token": "your_volcengine_access_token_here",
      "voice_type": "zh_female_vv_uranus_bigtts",
      "endpoint": "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
    }
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8765
  }
}
```

### 4. 启动自衍体 API 服务

在另一个终端中启动自衍体 API 服务：

```bash
cd /path/to/zyantine_memo/zyantine_genisis
python api_server.py
```

## 使用方法

### 1. 启动后端服务器

```bash
python -m uvicorn web_server:app --reload --host 0.0.0.0 --port 8765
```

### 2. 启动前端开发服务器

```bash
cd vue3-frontend
npm run dev
```

### 3. 访问Web界面

打开浏览器访问前端开发服务器地址（默认：`http://localhost:5173`）

### 使用说明

1. 点击录音按钮开始录音
2. 对着麦克风说话
3. 点击停止按钮结束录音
4. 系统会自动识别语音、生成AI回复并播放语音

## 项目结构

```
zyantine_rtc/
├── web_server.py           # FastAPI Web服务器
├── ai_rtc_system.py        # AI系统核心类
├── stt.py                  # 语音识别（STT）
├── tts.py                  # 语音合成（TTS）
├── ai_conversation.py      # AI对话管理
├── protocols.py            # WebSocket协议定义
├── requirements.txt        # Python依赖
├── config.example.json     # 配置文件示例
├── config.json             # 配置文件（实际使用）
├── tests/                  # 测试目录
│   ├── __init__.py         # 测试包初始化
│   ├── test_all.py         # 统一测试运行器
│   ├── test_stt.py         # 语音识别测试
│   ├── test_tts.py         # 语音合成测试
│   ├── test_tts_voices.py  # TTS声音测试
│   └── test_volcengine_tts.py # 火山引擎TTS测试
└── vue3-frontend/          # Vue 3前端项目
    ├── public/             # 静态资源
    │   ├── cubism-sdk/     # Live2D SDK
    │   └── live2d-models/  # Live2D模型
    ├── src/                # 源代码
    │   ├── assets/         # 资源文件
    │   ├── components/     # Vue组件
    │   │   ├── AnimatedAvatar/ # 动画头像组件
    │   │   ├── Avatar3D/   # 3D头像组件
    │   │   ├── ChatPanel/  # 聊天面板组件
    │   │   ├── ControlPanel/ # 控制面板组件
    │   │   └── Live2DAvatar/ # Live2D头像组件
    │   ├── composables/    # 组合式API
    │   ├── stores/         # 状态管理
    │   ├── App.vue         # 根组件
    │   └── main.js         # 入口文件
    ├── package.json        # 前端依赖
    ├── vite.config.js      # Vite配置
    └── tailwind.config.js  # Tailwind CSS配置
```

## 配置选项

在 `config.json` 文件中可以配置以下选项：

### 自衍体 API 配置
- `zyantine.api_key`: 自衍体 API密钥（可选，如果API服务需要认证）
- `zyantine.base_url`: 自衍体 API基础URL（默认：http://localhost:8001）
- `zyantine.model`: 对话模型（默认：zyantine-v1）

### 字节跳动语音识别配置
- `stt.bytedance.app_key`: 字节跳动应用ID（必需）
- `stt.bytedance.access_key`: 字节跳动访问令牌（必需）
- `stt.bytedance.ws_url`: WebSocket URL（默认：wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream）

### 火山引擎语音合成配置
- `tts.volcengine.appid`: 火山引擎应用ID（必需）
- `tts.volcengine.access_token`: 火山引擎访问令牌（必需）
- `tts.volcengine.voice_type`: 语音类型（默认：zh_female_vv_uranus_bigtts）
- `tts.volcengine.endpoint`: WebSocket端点（默认：wss://openspeech.bytedance.com/api/v3/tts/bidirection）

### 服务器配置
- `server.host`: 服务器主机（默认：0.0.0.0）
- `server.port`: 服务器端口（默认：8765）

## 可用的TTS声音

火山引擎支持多种语音类型，常用的包括：

- `zh_female_vv_uranus_bigtts`: 女性声音（推荐）
- `zh_male_vv_apollo_bigtts`: 男性声音
- `zh_female_vv_mars_bigtts`: 女性声音
- `zh_male_vv_mercury_bigtts`: 男性声音

你可以在 `tts.py` 中修改 `voice_type` 参数来更换声音。

## 测试工具

### 测试目录结构

所有测试文件都已整理到 `tests/` 目录中：

```
tests/
├── __init__.py           # 测试包初始化
├── test_stt.py           # 语音识别测试
├── test_tts.py           # 语音合成测试
├── test_tts_voices.py    # TTS声音测试
├── test_volcengine_tts.py # 火山引擎TTS测试
└── test_all.py           # 统一测试运行器
```

### 运行测试

#### 运行所有测试

```bash
python -m tests.test_all
```

#### 运行特定测试

```bash
# 测试语音识别
python -m tests.test_stt

# 测试语音合成
python -m tests.test_tts

# 测试TTS声音
python -m tests.test_tts_voices

# 测试火山引擎TTS
python -m tests.test_volcengine_tts
```

## 自定义AI角色

在 `ai_conversation.py` 中修改 `system_prompt`：

```python
AIConversation(
    system_prompt="你是一个专业的技术顾问，可以帮助用户解决编程问题。"
)
```

## 故障排除

### 麦克风权限问题

确保浏览器有麦克风访问权限：
- Chrome: 设置 > 隐私和安全 > 网站设置 > 麦克风
- Safari: Safari > 偏好设置 > 网站 > 麦克风
- Firefox: 选项 > 隐私与安全 > 权限 > 麦克风

### 音频播放失败

如果音频无法播放，请检查：
1. 浏览器控制台是否有错误信息
2. 音频数据是否正确编码
3. WAV文件头是否正确添加

### API连接失败

确保自衍体 API 服务正在运行：
1. 检查 API 服务是否已启动
2. 检查 `.env` 文件中的 `ZYANTINE_BASE_URL` 是否正确
3. 查看浏览器控制台或服务器日志获取详细错误信息

## 技术架构

### 后端
- **FastAPI**: Web框架
- **WebSocket**: 实时通信
- **字节跳动语音识别**: 语音识别
- **火山引擎TTS**: 语音合成
- **自衍体 AI**: 对话生成

### 前端
- **Vue 3**: 前端框架
- **Vite**: 构建工具
- **Tailwind CSS**: CSS框架
- **WebSocket API**: 实时通信
- **Web Audio API**: 音频处理
- **Live2D**: 交互式3D头像
- **Pinia**: 状态管理
- **Composition API**: Vue 3组合式API

## 许可证

MIT License
