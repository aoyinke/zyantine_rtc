import io
import logging
import numpy as np
import asyncio
import json
import uuid
import subprocess
import tempfile
import os
from typing import Optional
import websockets.asyncio.client
from protocols import (
    EventType,
    MsgType,
    finish_connection,
    finish_session,
    receive_message,
    start_connection,
    start_session,
    task_request,
    wait_for_event,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(
        self,
        appid: Optional[str] = None,
        access_token: Optional[str] = None,
        voice_type: str = "zh_female_vv_uranus_bigtts",
        emotion: str = "neutral",
        target_sample_rate: int = 16000,
        endpoint: str = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
    ):
        self.appid = appid or os.getenv("VOLCENGINE_APPID", "5474947932")
        self.access_token = access_token or os.getenv("VOLCENGINE_ACCESS_TOKEN", "q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c")
        self.voice_type = voice_type
        self.emotion = emotion
        self.target_sample_rate = target_sample_rate
        self.endpoint = endpoint

        if not self.appid or not self.access_token:
            raise ValueError("VOLCENGINE_APPID and VOLCENGINE_ACCESS_TOKEN are required")

    def get_resource_id(self, voice: str) -> str:
        return "seed-tts-2.0"

    def convert_mp3_to_pcm(self, mp3_data: bytes) -> np.ndarray:
        try:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
                mp3_file.write(mp3_data)
                mp3_file.flush()
                mp3_path = mp3_file.name

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                wav_path = wav_file.name

            try:
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', mp3_path,
                    '-ar', str(self.target_sample_rate),
                    '-ac', '1',
                    '-f', 'wav',
                    wav_path
                ], check=True, capture_output=True)

                with open(wav_path, 'rb') as f:
                    wav_data = f.read()

                if len(wav_data) < 44:
                    raise ValueError("Invalid WAV file: too small")

                header = wav_data[:44]
                if not header.startswith(b'RIFF') or b'WAVE' not in header:
                    raise ValueError("Invalid WAV file: missing RIFF/WAVE header")

                audio_data = wav_data[44:]
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                return audio_array

            finally:
                os.unlink(mp3_path)
                os.unlink(wav_path)

        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return np.array([], dtype=np.int16)

    async def synthesize(self, text: str) -> np.ndarray:
        try:
            headers = {
                "X-Api-App-Key": self.appid,
                "X-Api-Access-Key": self.access_token,
                "X-Api-Resource-Id": self.get_resource_id(self.voice_type),
                "X-Api-Connect-Id": str(uuid.uuid4()),
            }

            logger.info(f"Connecting to {self.endpoint}")
            async with websockets.asyncio.client.connect(
                self.endpoint, additional_headers=headers, max_size=10 * 1024 * 1024
            ) as websocket:
                logger.info(f"Connected to WebSocket server")

                await start_connection(websocket)
                await wait_for_event(
                    websocket, MsgType.FullServerResponse, EventType.ConnectionStarted
                )

                base_request = {
                    "user": {
                        "uid": str(uuid.uuid4()),
                    },
                    "namespace": "BidirectionalTTS",
                    "req_params": {
                        "speaker": self.voice_type,
                        "emotion": self.emotion,
                        "audio_params": {
                            "format": "mp3",
                            "sample_rate": 24000,
                            "enable_timestamp": True,
                        },
                        "additions": json.dumps(
                            {
                                "disable_markdown_filter": False,
                            }
                        ),
                    },
                }

                start_session_request = base_request.copy()
                start_session_request["event"] = EventType.StartSession
                session_id = str(uuid.uuid4())
                await start_session(
                    websocket, json.dumps(start_session_request).encode(), session_id
                )
                await wait_for_event(
                    websocket, MsgType.FullServerResponse, EventType.SessionStarted
                )

                async def send_text():
                    synthesis_request = base_request.copy()
                    synthesis_request["event"] = EventType.TaskRequest
                    synthesis_request["req_params"]["text"] = text
                    await task_request(
                        websocket, json.dumps(synthesis_request).encode(), session_id
                    )

                    await finish_session(websocket, session_id)

                send_task = asyncio.create_task(send_text())

                audio_data = bytearray()
                while True:
                    msg = await receive_message(websocket)

                    if msg.type == MsgType.FullServerResponse:
                        if msg.event == EventType.SessionFinished:
                            break
                    elif msg.type == MsgType.AudioOnlyServer:
                        audio_data.extend(msg.payload)
                    else:
                        raise RuntimeError(f"TTS conversion failed: {msg}")

                await send_task

                if not audio_data:
                    raise RuntimeError("No audio data received")

                logger.info(f"Received audio data: {len(audio_data)} bytes")

                audio_array = self.convert_mp3_to_pcm(bytes(audio_data))

                logger.info(f"Synthesized audio for text: {text[:50]}..., length: {len(audio_array)} samples")

                await finish_connection(websocket)
                await wait_for_event(
                    websocket, MsgType.FullServerResponse, EventType.ConnectionFinished
                )
                logger.info("Connection closed")

                return audio_array

        except Exception as e:
            logger.error(f"TTS error: {e}")
            import traceback
            traceback.print_exc()
            return np.array([], dtype=np.int16)

    async def synthesize_stream(self, text: str):
        """流式语音合成"""
        if not text or not text.strip():
            logger.warning("Empty text for TTS synthesis")
            return

        try:
            headers = {
                "X-Api-App-Key": self.appid,
                "X-Api-Access-Key": self.access_token,
                "X-Api-Resource-Id": self.get_resource_id(self.voice_type),
                "X-Api-Connect-Id": str(uuid.uuid4()),
            }

            async with websockets.asyncio.client.connect(
                self.endpoint, additional_headers=headers, max_size=10 * 1024 * 1024
            ) as websocket:
                logger.info(f"Connected to TTS server for streaming synthesis")

                await start_connection(websocket)
                await wait_for_event(
                    websocket, MsgType.FullServerResponse, EventType.ConnectionStarted
                )

                base_request = {
                    "user": {
                        "uid": str(uuid.uuid4()),
                    },
                    "namespace": "BidirectionalTTS",
                    "req_params": {
                        "speaker": self.voice_type,
                        "emotion": self.emotion,
                        "audio_params": {
                            "format": "mp3",
                            "sample_rate": 24000,
                            "enable_timestamp": True,
                        },
                        "additions": json.dumps(
                            {
                                "disable_markdown_filter": False,
                            }
                        ),
                    },
                }

                start_session_request = base_request.copy()
                start_session_request["event"] = EventType.StartSession
                session_id = str(uuid.uuid4())
                await start_session(
                    websocket, json.dumps(start_session_request).encode(), session_id
                )
                await wait_for_event(
                    websocket, MsgType.FullServerResponse, EventType.SessionStarted
                )

                async def send_text():
                    """发送完整文本"""
                    synthesis_request = base_request.copy()
                    synthesis_request["event"] = EventType.TaskRequest
                    synthesis_request["req_params"]["text"] = text
                    await task_request(
                        websocket, json.dumps(synthesis_request).encode(), session_id
                    )
                    # 不要立即结束会话，等待音频数据接收完成

                send_task = asyncio.create_task(send_text())
                logger.info(f"Started streaming TTS for text: {text[:50]}...")

                received_audio_chunks = 0
                task_finished = False
                last_audio_time = asyncio.get_event_loop().time()
                max_wait_time = 10.0  # 最大等待时间（秒）

                while True:
                    try:
                        # 添加超时机制，避免无限等待
                        msg = await asyncio.wait_for(
                            receive_message(websocket),
                            timeout=max_wait_time
                        )

                        if msg.type == MsgType.FullServerResponse:
                            if msg.event == EventType.SessionFinished:
                                logger.info(f"TTS session finished, received {received_audio_chunks} audio chunks")
                                break
                            elif msg.event == EventType.TaskFinished:
                                # 任务完成，等待所有音频数据接收完成
                                logger.info("TTS task finished, waiting for audio data...")
                                task_finished = True
                                # 任务完成后，设置较短的超时时间
                                max_wait_time = 5.0
                    
                    except asyncio.TimeoutError:
                        logger.warning(f"TTS receive message timeout after {max_wait_time} seconds")
                        # 超时后，检查是否已经收到任务完成事件和音频数据
                        if task_finished or received_audio_chunks > 0:
                            logger.info(f"Timeout but got {received_audio_chunks} audio chunks, finishing TTS")
                            break
                        else:
                            logger.error("TTS timeout with no audio data received")
                            raise
                    
                    except Exception as e:
                        logger.error(f"Error receiving TTS message: {e}")
                        # 非致命错误，继续处理
                        continue

                    if msg and msg.type == MsgType.AudioOnlyServer:
                        try:
                            audio_array = self.convert_mp3_to_pcm(msg.payload)
                            if len(audio_array) > 0:
                                received_audio_chunks += 1
                                logger.debug(f"Received audio chunk {received_audio_chunks}, size: {len(audio_array)}")
                                yield audio_array
                                last_audio_time = asyncio.get_event_loop().time()
                            else:
                                logger.warning(f"Empty audio chunk received")
                        except Exception as e:
                            logger.error(f"Error converting audio chunk: {e}")
                            import traceback
                            traceback.print_exc()
                    elif msg and msg.type != MsgType.FullServerResponse:
                        logger.error(f"Unexpected message type: {msg.type}")
                        break

                await send_task
                
                # 手动结束会话
                logger.info("Finishing TTS session...")
                try:
                    await finish_session(websocket, session_id)
                except Exception as e:
                    logger.error(f"Error finishing TTS session: {e}")
                
                logger.info(f"Streaming TTS completed successfully, received {received_audio_chunks} audio chunks")

                try:
                    await finish_connection(websocket)
                    await asyncio.wait_for(
                        wait_for_event(
                            websocket, MsgType.FullServerResponse, EventType.ConnectionFinished
                        ),
                        timeout=5.0
                    )
                except Exception as e:
                    logger.error(f"Error closing TTS connection: {e}")

        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            import traceback
            traceback.print_exc()
            # 不要在异常块中yield，这会导致生成器无法正确关闭
            return

    def set_voice(self, voice_type: str):
        self.voice_type = voice_type
        logger.info(f"Voice changed to {voice_type}")

    def set_voice_type(self, voice_type: str):
        self.voice_type = voice_type
        logger.info(f"Voice type changed to {voice_type}")

    def set_emotion(self, emotion: str):
        self.emotion = emotion
        logger.info(f"Emotion changed to {emotion}")

    def get_emotion(self) -> str:
        return self.emotion
