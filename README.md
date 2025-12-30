# AI 语音助手系统

一个基于Python的纯语音交互AI助手系统，使用Web界面实现实时语音对话。

## 功能特性

- 纯语音交互界面，无需文本输入
- 实时音频采集和传输
- AI语音识别（STT）- 使用OpenAI Whisper
- AI语音合成（TTS）- 使用火山引擎豆包语音合成
- AI对话 - 使用自衍体 AI 系统
- 语音活动检测（VAD）
- 现代化的Web界面设计
- 实时状态反馈和动态提示

## 系统要求

- Python 3.8+
- 麦克风和扬声器
- 自衍体 API 服务（本地运行或远程）
- 火山引擎API密钥（用于TTS）

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置你的API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的API密钥：

```
ZYANTINE_BASE_URL=http://localhost:8000
VOLCENGINE_APP_ID=your_volcengine_app_id_here
VOLCENGINE_ACCESS_TOKEN=your_volcengine_access_token_here
```

### 3. 启动自衍体 API 服务

在另一个终端中启动自衍体 API 服务：

```bash
cd /path/to/zyantine_memo/zyantine_genisis
python api_server.py
```

## 使用方法

### 启动Web服务器

```bash
python -m uvicorn web_server:app --reload --host 0.0.0.0 --port 8765
```

### 访问Web界面

打开浏览器访问：`http://localhost:8765`

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
├── .env.example           # 环境变量示例
├── templates/
│   └── index.html         # Web前端界面
├── test_tts_voices.py     # TTS声音测试工具
└── test_volcengine_tts.py # 火山引擎TTS测试工具
```

## 配置选项

在 `.env` 文件中可以配置以下选项：

### 自衍体 API 配置
- `ZYANTINE_API_KEY`: 自衍体 API密钥（可选，如果API服务需要认证）
- `ZYANTINE_BASE_URL`: 自衍体 API基础URL（默认：http://localhost:8000）
- `LLM_MODEL`: 对话模型（默认：zyantine-v1，可选：zyantine-enhanced）

### OpenAI配置（仅用于STT）
- `OPENAI_API_KEY`: OpenAI API密钥（用于Whisper语音识别）
- `OPENAI_BASE_URL`: OpenAI API基础URL（可选）
- `STT_MODEL`: 语音识别模型（默认：whisper-1）

### 火山引擎配置
- `VOLCENGINE_APP_ID`: 火山引擎应用ID（必需）
- `VOLCENGINE_ACCESS_TOKEN`: 火山引擎访问令牌（必需）
- `VOLCENGINE_VOICE_TYPE`: 语音类型（默认：zh_female_vv_uranus_bigtts）

### 服务器配置
- `SERVER_HOST`: 服务器主机（默认：0.0.0.0）
- `SERVER_PORT`: 服务器端口（默认：8765）

## 可用的TTS声音

火山引擎支持多种语音类型，常用的包括：

- `zh_female_vv_uranus_bigtts`: 女性声音（推荐）
- `zh_male_vv_apollo_bigtts`: 男性声音
- `zh_female_vv_mars_bigtts`: 女性声音
- `zh_male_vv_mercury_bigtts`: 男性声音

你可以在 `tts.py` 中修改 `voice_type` 参数来更换声音。

## 测试工具

### 测试TTS声音

```bash
python test_tts_voices.py
```

### 测试火山引擎TTS

```bash
python test_volcengine_tts.py
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
- **OpenAI Whisper**: 语音识别
- **火山引擎TTS**: 语音合成
- **自衍体 AI**: 对话生成

### 前端
- **HTML5/CSS3**: 现代化界面设计
- **JavaScript**: 交互逻辑
- **WebSocket API**: 实时通信
- **Web Audio API**: 音频处理

## 许可证

MIT License
