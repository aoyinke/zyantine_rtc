import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import base64
import struct
import uuid

from ai_rtc_system import AIRTCSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def create_session(self, websocket: WebSocket) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "websocket": websocket,
            "system": None,
            "recorded_audio_chunks": [],
            "created_at": datetime.now()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def update_session(self, session_id: str, **kwargs):
        session = self.get_session(session_id)
        if session:
            session.update(kwargs)

session_manager = SessionManager()

def pcm_to_wav(pcm_data: np.ndarray, sample_rate: int = 16000) -> bytes:
    """Convert PCM data to WAV format with proper header"""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data) * 2
    total_size = 36 + data_size
    
    wav_header = struct.pack('<4sI4s', b'RIFF', total_size, b'WAVE')
    fmt_chunk = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample)
    data_chunk_header = struct.pack('<4sI', b'data', data_size)
    
    wav_data = wav_header + fmt_chunk + data_chunk_header + pcm_data.tobytes()
    return wav_data


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = session_manager.create_session(websocket)
        self.active_connections[websocket] = session_id
        return session_id

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            session_id = self.active_connections[websocket]
            session_manager.remove_session(session_id)
            del self.active_connections[websocket]

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for websocket in self.active_connections:
            await websocket.send_json(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse(status_code=204)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "connect":
                await handle_connect(websocket, data, session_id)
            
            elif message_type == "disconnect":
                await handle_disconnect(websocket, session_id)
            
            elif message_type == "start_recording":
                await handle_start_recording(websocket, session_id)
            
            elif message_type == "stop_recording":
                await handle_stop_recording(websocket, session_id)
            
            elif message_type == "audio_data":
                await handle_audio_data(websocket, data, session_id)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_connect(websocket: WebSocket, data: dict, session_id: str):
    try:
        signaling_url = data.get("signaling_url", "ws://localhost:8765")
        client_id = data.get("client_id", "web_client")
        room_id = data.get("room_id", "web_room")
        
        # 从环境变量获取字节跳动ASR的配置
        stt_app_key = os.getenv("BYTEDANCE_APP_KEY", "5474947932")
        stt_access_key = os.getenv("BYTEDANCE_ACCESS_KEY", "q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c")
        
        system = AIRTCSystem(
            signaling_url=signaling_url,
            client_id=client_id,
            room_id=room_id,
            stt_app_key=stt_app_key,
            stt_access_key=stt_access_key
        )
        
        session_manager.update_session(session_id, system=system)
        
        await manager.send_message({
            "type": "status",
            "status": "connected",
            "message": "已连接到服务器"
        }, websocket)
        
        logger.info(f"Client connected: {client_id}, session_id: {session_id}")
    
    except Exception as e:
        logger.error(f"Connection error: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"连接失败: {str(e)}"
        }, websocket)


async def handle_disconnect(websocket: WebSocket, session_id: str):
    session = session_manager.get_session(session_id)
    if session and session.get("system"):
        try:
            await session["system"].stop()
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    await manager.send_message({
        "type": "status",
        "status": "disconnected",
        "message": "已断开连接"
    }, websocket)


async def handle_start_recording(websocket: WebSocket, session_id: str):
    session_manager.update_session(session_id, recorded_audio_chunks=[])
    
    await manager.send_message({
        "type": "status",
        "status": "recording",
        "message": "开始录音"
    }, websocket)


async def handle_stop_recording(websocket: WebSocket, session_id: str):
    session = session_manager.get_session(session_id)
    if session:
        audio_chunks_count = len(session.get("recorded_audio_chunks", []))
        logger.info(f"handle_stop_recording called, session_id: {session_id}, audio_chunks count: {audio_chunks_count}")
    
    await manager.send_message({
        "type": "status",
        "status": "stopped",
        "message": "停止录音"
    }, websocket)
    
    # 使用流式处理
    await process_speech_and_respond_stream(websocket, session_id)


async def handle_audio_data(websocket: WebSocket, data: dict, session_id: str):
    try:
        audio_base64 = data.get("audio_data", "")
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            session = session_manager.get_session(session_id)
            if session:
                session["recorded_audio_chunks"].append(audio_array)
                total_chunks = len(session["recorded_audio_chunks"])
                logger.info(f"Received audio chunk, session_id: {session_id}, size: {len(audio_array)}, total chunks: {total_chunks}")
    except Exception as e:
        logger.error(f"Audio data handling error: {e}")
        import traceback
        traceback.print_exc()


async def process_speech_and_respond(websocket: WebSocket, session_id: str):
    """处理语音并响应（非流式）"""
    session = session_manager.get_session(session_id)
    if not session:
        return
    
    system = session.get("system")
    recorded_audio_chunks = session.get("recorded_audio_chunks", [])
    
    if not system or len(recorded_audio_chunks) == 0:
        return
    
    try:
        await manager.send_message({
            "type": "status",
            "status": "processing",
            "message": "正在识别语音..."
        }, websocket)
        
        user_text = await system.stt.transcribe_with_vad(recorded_audio_chunks)
        
        session_manager.update_session(session_id, recorded_audio_chunks=[])
        
        if user_text.strip():
            await manager.send_message({
                "type": "user_text",
                "text": user_text
            }, websocket)
            
            await manager.send_message({
                "type": "status",
                "status": "generating",
                "message": "AI 正在思考..."
            }, websocket)
            
            ai_response = await system.conversation_manager.process_user_input(user_text)
            
            if ai_response.strip():
                await manager.send_message({
                    "type": "ai_text",
                    "text": ai_response
                }, websocket)
                
                await manager.send_message({
                    "type": "status",
                    "status": "synthesizing",
                    "message": "正在生成语音..."
                }, websocket)
                
                audio_response = await system.tts.synthesize(ai_response)
                
                if len(audio_response) > 0:
                    wav_data = pcm_to_wav(audio_response)
                    audio_base64 = base64.b64encode(wav_data).decode('utf-8')
                    await manager.send_message({
                        "type": "audio_response",
                        "audio_data": audio_base64,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                else:
                    await manager.send_message({
                        "type": "error",
                        "message": "语音合成失败"
                    }, websocket)
            else:
                await manager.send_message({
                    "type": "error",
                    "message": "AI 生成响应失败"
                }, websocket)
        else:
            await manager.send_message({
                "type": "error",
                "message": "语音识别失败，请重新录音"
            }, websocket)
    
    except Exception as e:
        logger.error(f"Speech processing error: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"语音处理失败: {str(e)}"
        }, websocket)
        session_manager.update_session(session_id, recorded_audio_chunks=[])


async def process_speech_and_respond_stream(websocket: WebSocket, session_id: str):
    """处理语音并响应（流式）"""
    session = session_manager.get_session(session_id)
    if not session:
        return
    
    system = session.get("system")
    recorded_audio_chunks = session.get("recorded_audio_chunks", [])
    
    if not system or len(recorded_audio_chunks) == 0:
        return
    
    try:
        await manager.send_message({
            "type": "status",
            "status": "processing",
            "message": "正在识别语音..."
        }, websocket)
        
        user_text = await system.stt.transcribe_with_vad(recorded_audio_chunks)
        
        session_manager.update_session(session_id, recorded_audio_chunks=[])
        
        if user_text.strip():
            await manager.send_message({
                "type": "user_text",
                "text": user_text
            }, websocket)
            
            await manager.send_message({
                "type": "status",
                "status": "generating",
                "message": "AI 正在思考..."
            }, websocket)
            
            # 使用流式方式获取 AI 响应
            full_ai_response = ""
            async for ai_chunk in system.conversation_manager.process_user_input_stream(user_text):
                full_ai_response += ai_chunk
                # 发送部分 AI 响应给前端
                await manager.send_message({
                    "type": "ai_text_chunk",
                    "text": ai_chunk,
                    "is_final": False
                }, websocket)
            
            # 发送完整的 AI 响应
            await manager.send_message({
                "type": "ai_text",
                "text": full_ai_response
            }, websocket)
            
            await manager.send_message({
                "type": "status",
                "status": "synthesizing",
                "message": "正在生成语音..."
            }, websocket)
            
            # 使用非流式方式合成完整语音
            logger.info(f"Starting TTS synthesis for text: {full_ai_response[:50]}...")
            try:
                # 使用非流式的 synthesize 方法合成完整的语音
                audio_array = await system.tts.synthesize(full_ai_response)
                logger.info(f"TTS synthesis completed, audio length: {len(audio_array)} samples")
                
                if len(audio_array) > 0:
                    # 转换为 WAV 格式
                    wav_data = pcm_to_wav(audio_array)
                    logger.info(f"Converted to WAV, size: {len(wav_data)} bytes")
                    
                    # 编码为 base64
                    audio_base64 = base64.b64encode(wav_data).decode('utf-8')
                    logger.info(f"Audio base64 length: {len(audio_base64)}")
                    
                    # 发送完整的音频响应给前端
                    await manager.send_message({
                        "type": "audio_response",
                        "audio_data": audio_base64,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    logger.info("Audio response sent successfully")
                else:
                    logger.error("No audio data synthesized")
                    await manager.send_message({
                        "type": "error",
                        "message": "语音合成失败: 没有生成音频数据"
                    }, websocket)
            except Exception as e:
                logger.error(f"Error during TTS synthesis: {e}")
                import traceback
                traceback.print_exc()
                await manager.send_message({
                    "type": "error",
                    "message": f"语音合成失败: {str(e)}"
                }, websocket)
        else:
            await manager.send_message({
                "type": "error",
                "message": "语音识别失败，请重新录音"
            }, websocket)
    
    except Exception as e:
        logger.error(f"Streaming speech processing error: {e}")
        import traceback
        traceback.print_exc()
        await manager.send_message({
            "type": "error",
            "message": f"语音处理失败: {str(e)}"
        }, websocket)
        session_manager.update_session(session_id, recorded_audio_chunks=[])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
