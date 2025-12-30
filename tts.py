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
        target_sample_rate: int = 16000,
        endpoint: str = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
    ):
        self.appid = appid or os.getenv("VOLCENGINE_APPID", "5474947932")
        self.access_token = access_token or os.getenv("VOLCENGINE_ACCESS_TOKEN", "q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c")
        self.voice_type = voice_type
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

                async def send_chars():
                    for char in text:
                        synthesis_request = base_request.copy()
                        synthesis_request["event"] = EventType.TaskRequest
                        synthesis_request["req_params"]["text"] = char
                        await task_request(
                            websocket, json.dumps(synthesis_request).encode(), session_id
                        )
                        await asyncio.sleep(0.005)

                    await finish_session(websocket, session_id)

                send_task = asyncio.create_task(send_chars())

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

                async def send_chars():
                    for char in text:
                        synthesis_request = base_request.copy()
                        synthesis_request["event"] = EventType.TaskRequest
                        synthesis_request["req_params"]["text"] = char
                        await task_request(
                            websocket, json.dumps(synthesis_request).encode(), session_id
                        )
                        await asyncio.sleep(0.005)

                    await finish_session(websocket, session_id)

                send_task = asyncio.create_task(send_chars())

                while True:
                    msg = await receive_message(websocket)

                    if msg.type == MsgType.FullServerResponse:
                        if msg.event == EventType.SessionFinished:
                            break
                    elif msg.type == MsgType.AudioOnlyServer:
                        audio_array = self.convert_mp3_to_pcm(msg.payload)
                        if len(audio_array) > 0:
                            yield audio_array
                    else:
                        raise RuntimeError(f"TTS conversion failed: {msg}")

                await send_task

                await finish_connection(websocket)
                await wait_for_event(
                    websocket, MsgType.FullServerResponse, EventType.ConnectionFinished
                )

        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            yield np.array([], dtype=np.int16)

    def set_voice(self, voice_type: str):
        self.voice_type = voice_type
        logger.info(f"Voice changed to {voice_type}")

    def set_voice_type(self, voice_type: str):
        self.voice_type = voice_type
        logger.info(f"Voice type changed to {voice_type}")
