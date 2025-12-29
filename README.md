# AI RTC System

一个基于Python的实时通信（RTC）系统，可以与AI进行语音对话。

## 功能特性

- 实时音频采集和传输
- WebRTC信令服务器（WebSocket）
- AI语音识别（STT）- 使用OpenAI Whisper
- AI语音合成（TTS）- 使用OpenAI TTS
- AI对话 - 使用OpenAI GPT模型
- 语音活动检测（VAD）
- 支持多房间通信

## 系统要求

- Python 3.8+
- 麦克风和扬声器
- OpenAI API密钥

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置你的OpenAI API密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的API密钥：

```
OPENAI_API_KEY=your_actual_api_key_here
```

## 使用方法

### 方式一：使用启动脚本

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
start.bat
```

### 方式二：手动启动

**1. 启动信令服务器：**
```bash
python signaling_server.py
```

**2. 在新的终端窗口启动AI RTC客户端：**
```bash
python ai_rtc_system.py
```

## 项目结构

```
zyantine_rtc/
├── signaling_server.py      # WebRTC信令服务器
├── rtc_client.py            # RTC客户端基础类
├── stt.py                   # 语音识别（STT）
├── tts.py                   # 语音合成（TTS）
├── ai_conversation.py       # AI对话管理
├── ai_rtc_system.py         # AI RTC系统主程序
├── requirements.txt         # Python依赖
├── .env.example            # 环境变量示例
├── start.sh                # Linux/Mac启动脚本
└── start.bat               # Windows启动脚本
```

## 配置选项

在 `.env` 文件中可以配置以下选项：

- `OPENAI_API_KEY`: OpenAI API密钥（必需）
- `OPENAI_BASE_URL`: OpenAI API基础URL（可选）
- `STT_MODEL`: 语音识别模型（默认：whisper-1）
- `TTS_MODEL`: 语音合成模型（默认：tts-1）
- `TTS_VOICE`: 语音合成声音（默认：alloy）
- `LLM_MODEL`: 对话模型（默认：gpt-4o）
- `SERVER_HOST`: 服务器主机（默认：0.0.0.0）
- `SERVER_PORT`: 服务器端口（默认：8765）

## 可用的TTS声音

- alloy
- echo
- fable
- onyx
- nova
- shimmer

## 使用示例

### 作为独立客户端使用

```python
from ai_rtc_system import AIRTCSystem
import asyncio

async def main():
    system = AIRTCSystem(
        signaling_url="ws://localhost:8765",
        client_id="my_client",
        room_id="room_1"
    )
    
    await system.start()

asyncio.run(main())
```

### 自定义AI角色

在 `ai_conversation.py` 中修改 `system_prompt`：

```python
AIConversation(
    system_prompt="你是一个专业的技术顾问，可以帮助用户解决编程问题。"
)
```

## 故障排除

### 麦克风权限问题

确保应用程序有麦克风访问权限：
- Mac: 系统偏好设置 > 安全性与隐私 > 麦克风
- Linux: 检查音频设备权限
- Windows: 隐私设置 > 麦克风

### PyAudio安装失败

**Mac:**
```bash
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-pyaudio
```

**Windows:**
下载并安装 PyAudio 的wheel文件。

### API密钥错误

确保 `.env` 文件中的 `OPENAI_API_KEY` 已正确设置。

## 停止系统

按 `Ctrl+C` 停止运行中的服务。

## 许可证

MIT License
