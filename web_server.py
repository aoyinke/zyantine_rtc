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
import uuid

from ai_rtc_system import AIRTCSystem
from config import config_manager
from audio_utils import pcm_to_wav
from error_handler import async_error_handler, format_error_response

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




class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket) -> str:
        """
        接受WebSocket连接并创建会话
        
        Args:
            websocket: WebSocket连接对象
            
        Returns:
            str: 创建的会话ID
        """
        try:
            # 接受WebSocket连接
            await websocket.accept()
            logger.info(f"WebSocket connection accepted")
            
            # 创建会话
            session_id = session_manager.create_session(websocket)
            self.active_connections[websocket] = session_id
            logger.info(f"Created new session: {session_id}")
            
            return session_id
        except Exception as e:
            logger.error(f"Failed to connect WebSocket: {e}")
            raise

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            session_id = self.active_connections[websocket]
            session_manager.remove_session(session_id)
            del self.active_connections[websocket]

    async def send_message(self, message: dict, websocket: WebSocket) -> bool:
        """
        发送消息到指定WebSocket连接
        
        Args:
            message: 要发送的消息
            websocket: WebSocket连接对象
            
        Returns:
            bool: 发送结果，True表示发送成功，False表示发送失败
        """
        # 先检查连接是否在活跃列表中
        if websocket not in self.active_connections:
            logger.debug(f"WebSocket not in active connections, cannot send message")
            return False
        
        try:
            # 发送消息
            await websocket.send_json(message)
            logger.debug(f"Message sent successfully: {message.get('type')}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            logger.error(f"Message type: {message.get('type')}")
            logger.error(f"WebSocket in active_connections: {websocket in self.active_connections}")
            
            # 从活跃连接中移除无效连接
            if websocket in self.active_connections:
                logger.info(f"Removing inactive WebSocket from active connections")
                self.disconnect(websocket)
            return False

    async def broadcast(self, message: dict):
        """
        向所有活跃连接广播消息
        
        Args:
            message: 要广播的消息
        """
        # 创建活跃连接的副本，避免并发修改问题
        active_websockets = list(self.active_connections.keys())
        for websocket in active_websockets:
            # 使用send_message方法，它包含了连接状态检查和异常处理
            await self.send_message(message, websocket)


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


@async_error_handler
async def handle_connect(websocket: WebSocket, data: dict, session_id: str):
    try:
        signaling_url = data.get("signaling_url", "ws://localhost:8765")
        client_id = data.get("client_id", "web_client")
        room_id = data.get("room_id", "web_room")
        
        # 从配置文件获取字节跳动ASR的配置
        stt_app_key = config_manager.get("stt.bytedance.app_key") or "5474947932"
        stt_access_key = config_manager.get("stt.bytedance.access_key") or "q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c"
        
        system = AIRTCSystem(
            signaling_url=signaling_url,
            client_id=client_id,
            room_id=room_id,
            stt_app_key=stt_app_key,
            stt_access_key=stt_access_key
        )
        
        session_manager.update_session(session_id, system=system)
        
        # 检查连接是否仍然活跃
        if websocket in manager.active_connections:
            await manager.send_message({
                "type": "status",
                "status": "connected",
                "message": "已连接到服务器"
            }, websocket)
            
            logger.info(f"Client connected: {client_id}, session_id: {session_id}")
    
    except Exception as e:
        logger.error(f"Connection error: {e}")
        # 检查连接是否仍然活跃
        if websocket in manager.active_connections:
            await manager.send_message({
                "type": "error",
                "message": f"连接失败: {str(e)}"
            }, websocket)


@async_error_handler
async def handle_disconnect(websocket: WebSocket, session_id: str):
    session = session_manager.get_session(session_id)
    if session and session.get("system"):
        try:
            await session["system"].stop()
        except Exception as e:
            logger.error(f"Error stopping system: {e}")
    
    # 检查连接是否仍然活跃
    if websocket in manager.active_connections:
        await manager.send_message({
            "type": "status",
            "status": "disconnected",
            "message": "已断开连接"
        }, websocket)
    
    # 断开连接
    manager.disconnect(websocket)


async def handle_start_recording(websocket: WebSocket, session_id: str):
    session_manager.update_session(session_id, recorded_audio_chunks=[])
    
    # 检查连接是否仍然活跃
    if websocket in manager.active_connections:
        await manager.send_message({
            "type": "status",
            "status": "recording",
            "message": "开始录音"
        }, websocket)


@async_error_handler
async def handle_stop_recording(websocket: WebSocket, session_id: str):
    session = session_manager.get_session(session_id)
    if session:
        audio_chunks_count = len(session.get("recorded_audio_chunks", []))
        logger.info(f"handle_stop_recording called, session_id: {session_id}, audio_chunks count: {audio_chunks_count}")
    
    # 检查连接是否仍然活跃
    if websocket in manager.active_connections:
        await manager.send_message({
            "type": "status",
            "status": "stopped",
            "message": "停止录音"
        }, websocket)
        
        # 使用流式处理
        await process_speech_and_respond_stream(websocket, session_id)


@async_error_handler
async def handle_audio_data(websocket: WebSocket, data: dict, session_id: str):
    try:
        # 检查连接是否仍然活跃
        if websocket not in manager.active_connections:
            logger.debug(f"WebSocket not in active connections, ignoring audio data for session: {session_id}")
            return
        
        audio_base64 = data.get("audio_data", "")
        if audio_base64:
            audio_bytes = base64.b64decode(audio_base64)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            
            session = session_manager.get_session(session_id)
            if session:
                # 压缩音频数据以减少内存使用
                # 注意：这里我们仍然存储原始音频数据，因为STT需要原始数据
                # 在未来的优化中，我们可以考虑在传输过程中使用压缩
                session["recorded_audio_chunks"].append(audio_array)
                total_chunks = len(session["recorded_audio_chunks"])
                total_size = sum(len(chunk) for chunk in session["recorded_audio_chunks"])
                logger.info(f"Received audio chunk, session_id: {session_id}, size: {len(audio_array)}, total chunks: {total_chunks}, total size: {total_size} samples")
    except Exception as e:
        logger.error(f"Audio data handling error: {e}")
        import traceback
        traceback.print_exc()
        # 从活跃连接中移除无效连接
        if websocket in manager.active_connections:
            manager.disconnect(websocket)


@async_error_handler
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
                
                ai_response, emotion = await system.conversation_manager.process_user_input(user_text)
                
                # 详细日志：记录情绪传递情况
                logger.info(f"AI response generated - Emotion: {emotion}")
                
                if ai_response.strip():
                    await manager.send_message({
                        "type": "ai_text",
                        "text": ai_response,
                        "emotion": emotion
                    }, websocket)
                    
                    await manager.send_message({
                        "type": "status",
                        "status": "synthesizing",
                        "message": "正在生成语音..."
                    }, websocket)
                    
                    # 详细日志：记录 TTS 调用时的情绪传递
                    logger.info(f"Calling TTS synthesis with emotion: {emotion}")
                    audio_response = await system.tts.synthesize(ai_response, emotion=emotion)
                    
                    if len(audio_response) > 0:
                        wav_data = pcm_to_wav(audio_response)
                        audio_base64 = base64.b64encode(wav_data).decode('utf-8')
                        await manager.send_message({
                            "type": "audio_response",
                            "audio_data": audio_base64,
                            "emotion": emotion,
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


@async_error_handler
async def process_speech_and_respond_stream(websocket: WebSocket, session_id: str):
    """处理语音并响应（流式）"""
    # 检查连接是否仍然活跃
    if websocket not in manager.active_connections:
        logger.debug(f"WebSocket not in active connections, cannot process speech for session: {session_id}")
        return
    
    session = session_manager.get_session(session_id)
    if not session:
        return
    
    system = session.get("system")
    recorded_audio_chunks = session.get("recorded_audio_chunks", [])
    
    if not system or len(recorded_audio_chunks) == 0:
        return
    
    try:
        # 发送消息前检查连接状态
        if websocket not in manager.active_connections:
            logger.debug(f"WebSocket connection closed during processing, exiting")
            return
        
        await manager.send_message({
            "type": "status",
            "status": "processing",
            "message": "正在识别语音..."
        }, websocket)
        
        user_text = await system.stt.transcribe_with_vad(recorded_audio_chunks)
        
        session_manager.update_session(session_id, recorded_audio_chunks=[])
        
        if user_text.strip():
            # 发送消息前检查连接状态
            if websocket not in manager.active_connections:
                logger.debug(f"WebSocket connection closed, cannot send user text")
                return
            
            await manager.send_message({
                "type": "user_text",
                "text": user_text
            }, websocket)
            
            # 发送消息前检查连接状态
            if websocket not in manager.active_connections:
                logger.debug(f"WebSocket connection closed, cannot send generating status")
                return
            
            await manager.send_message({
                "type": "status",
                "status": "generating",
                "message": "AI 正在思考..."
            }, websocket)
            
            # 使用流式方式获取 AI 响应
            full_ai_response = ""
            async for ai_chunk in system.conversation_manager.process_user_input_stream(user_text):
                full_ai_response += ai_chunk
                
                # 发送消息前检查连接状态
                if websocket not in manager.active_connections:
                    logger.debug(f"WebSocket connection closed, exiting streaming loop")
                    return
                
                # 发送部分 AI 响应给前端
                await manager.send_message({
                    "type": "ai_text_chunk",
                    "text": ai_chunk,
                    "is_final": False
                }, websocket)
            
            # 获取情绪信息
            emotion = system.conversation_manager.get_current_emotion()
            
            # 移除情绪标签
            clean_ai_response = system.conversation_manager.conversation.remove_emotion_tag(full_ai_response)
            
            # 发送消息前检查连接状态
            if websocket not in manager.active_connections:
                logger.debug(f"WebSocket connection closed, cannot send final AI response")
                return
            
            # 发送完整的 AI 响应
            await manager.send_message({
                "type": "ai_text",
                "text": clean_ai_response,
                "emotion": emotion
            }, websocket)
            
            # 发送消息前检查连接状态
            if websocket not in manager.active_connections:
                logger.debug(f"WebSocket connection closed, cannot send synthesizing status")
                return
            
            await manager.send_message({
                "type": "status",
                "status": "synthesizing",
                "message": "正在生成语音..."
            }, websocket)
            
            # 使用非流式方式合成完整语音
            logger.info(f"=== Starting TTS synthesis ===")
            logger.info(f"Text: {clean_ai_response[:100]}..., emotion: {emotion}")
            try:
                # 确保系统和TTS服务可用
                if not system or not system.tts:
                    logger.error("TTS service is not available")
                    await manager.send_message({
                        "type": "error",
                        "message": "语音合成服务不可用"
                    }, websocket)
                    return
                
                # 使用非流式的 synthesize 方法合成完整的语音
                audio_array = await system.tts.synthesize(clean_ai_response, emotion=emotion)
                logger.info(f"TTS synthesis completed, audio length: {len(audio_array)} samples")
                
                if len(audio_array) > 0:
                    # 转换为 WAV 格式
                    wav_data = pcm_to_wav(audio_array)
                    logger.info(f"Converted to WAV, size: {len(wav_data)} bytes")
                    
                    # 编码为 base64
                    audio_base64 = base64.b64encode(wav_data).decode('utf-8')
                    logger.info(f"Audio base64 length: {len(audio_base64)}")
                    
                    # 发送消息前检查连接状态
                    if websocket not in manager.active_connections:
                        logger.error(f"WebSocket connection closed, cannot send audio response")
                        return
                    
                    # 发送完整的音频响应给前端
                    message_sent = await manager.send_message({
                        "type": "audio_response",
                        "audio_data": audio_base64,
                        "emotion": emotion,
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                    
                    if message_sent:
                        logger.info("Audio response sent successfully")
                    else:
                        logger.error("Failed to send audio response")
                else:
                    logger.error("No audio data synthesized, audio array is empty")
                    
                    # 发送消息前检查连接状态
                    if websocket in manager.active_connections:
                        await manager.send_message({
                            "type": "error",
                            "message": "语音合成失败: 没有生成音频数据"
                        }, websocket)
                    else:
                        logger.error("Cannot send TTS error message, WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error during TTS synthesis: {e}")
                import traceback
                traceback.print_exc()
                
                # 发送消息前检查连接状态
                if websocket in manager.active_connections:
                    await manager.send_message({
                        "type": "error",
                        "message": f"语音合成失败: {str(e)}"
                    }, websocket)
                else:
                    logger.error("Cannot send TTS error message, WebSocket connection closed")
            finally:
                logger.info("=== TTS synthesis process completed ===")
        else:
            # 发送消息前检查连接状态
            if websocket not in manager.active_connections:
                logger.debug(f"WebSocket connection closed, cannot send recognition error message")
                return
            
            await manager.send_message({
                "type": "error",
                "message": "语音识别失败，请重新录音"
            }, websocket)
    
    except Exception as e:
        logger.error(f"Streaming speech processing error: {e}")
        import traceback
        traceback.print_exc()
        
        # 发送消息前检查连接状态
        if websocket in manager.active_connections:
            await manager.send_message({
                "type": "error",
                "message": f"语音处理失败: {str(e)}"
            }, websocket)
        
        session_manager.update_session(session_id, recorded_audio_chunks=[])


if __name__ == "__main__":
    import uvicorn
    host = config_manager.get("server.host") or "0.0.0.0"
    port = config_manager.get("server.port") or 8765
    uvicorn.run(app, host=host, port=port)
