import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import base64
import struct

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

active_connections: list[WebSocket] = []
system: Optional[AIRTCSystem] = None
recorded_audio_chunks = []

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
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


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
    global system, recorded_audio_chunks
    
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "connect":
                await handle_connect(websocket, data)
            
            elif message_type == "disconnect":
                await handle_disconnect(websocket)
            
            elif message_type == "start_recording":
                await handle_start_recording(websocket)
            
            elif message_type == "stop_recording":
                await handle_stop_recording(websocket)
            
            elif message_type == "audio_data":
                await handle_audio_data(websocket, data)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_connect(websocket: WebSocket, data: dict):
    global system
    
    try:
        signaling_url = data.get("signaling_url", "ws://localhost:8765")
        client_id = data.get("client_id", "web_client")
        room_id = data.get("room_id", "web_room")
        
        system = AIRTCSystem(
            signaling_url=signaling_url,
            client_id=client_id,
            room_id=room_id
        )
        
        await manager.send_message({
            "type": "status",
            "status": "connected",
            "message": "已连接到服务器"
        }, websocket)
        
        logger.info(f"Client connected: {client_id}")
    
    except Exception as e:
        logger.error(f"Connection error: {e}")
        await manager.send_message({
            "type": "error",
            "message": f"连接失败: {str(e)}"
        }, websocket)


async def handle_disconnect(websocket: WebSocket):
    global system
    
    if system:
        try:
            await system.stop()
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    await manager.send_message({
        "type": "status",
        "status": "disconnected",
        "message": "已断开连接"
    }, websocket)


async def handle_start_recording(websocket: WebSocket):
    global recorded_audio_chunks
    
    recorded_audio_chunks = []
    
    await manager.send_message({
        "type": "status",
        "status": "recording",
        "message": "开始录音"
    }, websocket)


async def handle_stop_recording(websocket: WebSocket):
    global recorded_audio_chunks
    
    logger.info(f"handle_stop_recording called, audio_chunks count: {len(recorded_audio_chunks)}")
    
    await manager.send_message({
        "type": "status",
        "status": "stopped",
        "message": "停止录音"
    }, websocket)
    
    await process_speech_and_respond(websocket)


async def handle_audio_data(websocket: WebSocket, data: dict):
    global recorded_audio_chunks
    
    try:
        audio_base64 = data.get("audio_data", "")
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            recorded_audio_chunks.append(audio_array)
            logger.info(f"Received audio chunk, size: {len(audio_array)}, total chunks: {len(recorded_audio_chunks)}")
    except Exception as e:
        logger.error(f"Audio data handling error: {e}")
        import traceback
        traceback.print_exc()


async def process_speech_and_respond(websocket: WebSocket):
    global recorded_audio_chunks
    
    if not system or len(recorded_audio_chunks) == 0:
        return
    
    try:
        await manager.send_message({
            "type": "status",
            "status": "processing",
            "message": "正在识别语音..."
        }, websocket)
        
        user_text = await system.stt.transcribe_with_vad(recorded_audio_chunks)
        
        recorded_audio_chunks = []
        
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
        recorded_audio_chunks = []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
