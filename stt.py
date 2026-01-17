import io
import logging
import wave
import numpy as np
from typing import Optional, List, Dict, Any, Tuple, AsyncGenerator
import os
import asyncio
import aiohttp
import json
import struct
import gzip
import uuid
from dotenv import load_dotenv
from audio_utils import convert_audio_format
from error_handler import async_error_handler, STTError, AudioError, NetworkError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_SAMPLE_RATE = 16000

class ProtocolVersion:
    V1 = 0b0001

class MessageType:
    CLIENT_FULL_REQUEST = 0b0001
    CLIENT_AUDIO_ONLY_REQUEST = 0b0010
    SERVER_FULL_RESPONSE = 0b1001
    SERVER_ERROR_RESPONSE = 0b1111

class MessageTypeSpecificFlags:
    NO_SEQUENCE = 0b0000
    POS_SEQUENCE = 0b0001
    NEG_SEQUENCE = 0b0010
    NEG_WITH_SEQUENCE = 0b0011

class SerializationType:
    NO_SERIALIZATION = 0b0000
    JSON = 0b0001

class CompressionType:
    GZIP = 0b0001


class Config:
    def __init__(self, app_key: str, access_key: str):
        self.auth = {
            "app_key": app_key,
            "access_key": access_key
        }

    @property
    def app_key(self) -> str:
        return self.auth["app_key"]

    @property
    def access_key(self) -> str:
        return self.auth["access_key"]


class CommonUtils:
    @staticmethod
    def gzip_compress(data: bytes) -> bytes:
        return gzip.compress(data)

    @staticmethod
    def gzip_decompress(data: bytes) -> bytes:
        return gzip.decompress(data)

    @staticmethod
    def judge_wav(data: bytes) -> bool:
        if len(data) < 44:
            return False
        return data[:4] == b'RIFF' and data[8:12] == b'WAVE'


class AsrRequestHeader:
    def __init__(self):
        self.message_type = MessageType.CLIENT_FULL_REQUEST
        self.message_type_specific_flags = MessageTypeSpecificFlags.POS_SEQUENCE
        self.serialization_type = SerializationType.JSON
        self.compression_type = CompressionType.GZIP
        self.reserved_data = bytes([0x00])

    def with_message_type(self, message_type: int) -> 'AsrRequestHeader':
        self.message_type = message_type
        return self

    def with_message_type_specific_flags(self, flags: int) -> 'AsrRequestHeader':
        self.message_type_specific_flags = flags
        return self

    def with_serialization_type(self, serialization_type: int) -> 'AsrRequestHeader':
        self.serialization_type = serialization_type
        return self

    def with_compression_type(self, compression_type: int) -> 'AsrRequestHeader':
        self.compression_type = compression_type
        return self

    def with_reserved_data(self, reserved_data: bytes) -> 'AsrRequestHeader':
        self.reserved_data = reserved_data
        return self

    def to_bytes(self) -> bytes:
        header = bytearray()
        header.append((ProtocolVersion.V1 << 4) | 1)
        header.append((self.message_type << 4) | self.message_type_specific_flags)
        header.append((self.serialization_type << 4) | self.compression_type)
        header.extend(self.reserved_data)
        return bytes(header)

    @staticmethod
    def default_header() -> 'AsrRequestHeader':
        return AsrRequestHeader()


class RequestBuilder:
    @staticmethod
    def new_auth_headers(config: Config) -> Dict[str, str]:
        reqid = str(uuid.uuid4())
        return {
            "X-Api-Resource-Id": "volc.bigasr.sauc.duration",
            "X-Api-Request-Id": reqid,
            "X-Api-Access-Key": config.access_key,
            "X-Api-App-Key": config.app_key
        }

    @staticmethod
    def new_full_client_request(seq: int) -> bytes:
        header = AsrRequestHeader.default_header() \
            .with_message_type_specific_flags(MessageTypeSpecificFlags.POS_SEQUENCE)
        
        payload = {
            "user": {
                "uid": "demo_uid"
            },
            "audio": {
                "format": "wav",
                "codec": "raw",
                "rate": 16000,
                "bits": 16,
                "channel": 1
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "enable_ddc": True,
                "show_utterances": True,
                "enable_nonstream": False
            }
        }
        
        payload_bytes = json.dumps(payload).encode('utf-8')
        compressed_payload = CommonUtils.gzip_compress(payload_bytes)
        payload_size = len(compressed_payload)
        
        request = bytearray()
        request.extend(header.to_bytes())
        request.extend(struct.pack('>i', seq))
        request.extend(struct.pack('>I', payload_size))
        request.extend(compressed_payload)
        
        return bytes(request)

    @staticmethod
    def new_audio_only_request(seq: int, segment: bytes, is_last: bool = False) -> bytes:
        header = AsrRequestHeader.default_header()
        if is_last:
            header.with_message_type_specific_flags(MessageTypeSpecificFlags.NEG_WITH_SEQUENCE)
            seq = -seq
        else:
            header.with_message_type_specific_flags(MessageTypeSpecificFlags.POS_SEQUENCE)
        header.with_message_type(MessageType.CLIENT_AUDIO_ONLY_REQUEST)
        
        request = bytearray()
        request.extend(header.to_bytes())
        request.extend(struct.pack('>i', seq))
        
        compressed_segment = CommonUtils.gzip_compress(segment)
        request.extend(struct.pack('>I', len(compressed_segment)))
        request.extend(compressed_segment)
        
        return bytes(request)


class AsrResponse:
    def __init__(self):
        self.code = 0
        self.event = 0
        self.is_last_package = False
        self.payload_sequence = 0
        self.payload_size = 0
        self.payload_msg = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "event": self.event,
            "is_last_package": self.is_last_package,
            "payload_sequence": self.payload_sequence,
            "payload_size": self.payload_size,
            "payload_msg": self.payload_msg
        }


class ResponseParser:
    @staticmethod
    def parse_response(msg: bytes) -> AsrResponse:
        response = AsrResponse()
        
        header_size = msg[0] & 0x0f
        message_type = msg[1] >> 4
        message_type_specific_flags = msg[1] & 0x0f
        serialization_method = msg[2] >> 4
        message_compression = msg[2] & 0x0f
        
        payload = msg[header_size*4:]
        
        if message_type_specific_flags & 0x01:
            response.payload_sequence = struct.unpack('>i', payload[:4])[0]
            payload = payload[4:]
        if message_type_specific_flags & 0x02:
            response.is_last_package = True
        if message_type_specific_flags & 0x04:
            response.event = struct.unpack('>i', payload[:4])[0]
            payload = payload[4:]
            
        if message_type == MessageType.SERVER_FULL_RESPONSE:
            response.payload_size = struct.unpack('>I', payload[:4])[0]
            payload = payload[4:]
        elif message_type == MessageType.SERVER_ERROR_RESPONSE:
            response.code = struct.unpack('>i', payload[:4])[0]
            response.payload_size = struct.unpack('>I', payload[4:8])[0]
            payload = payload[8:]
            
        if not payload:
            return response
            
        if message_compression == CompressionType.GZIP:
            try:
                payload = CommonUtils.gzip_decompress(payload)
            except Exception as e:
                logger.error(f"Failed to decompress payload: {e}")
                return response
                
        try:
            if serialization_method == SerializationType.JSON:
                response.payload_msg = json.loads(payload.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to parse payload: {e}")
            
        return response


class AsrWsClient:
    def __init__(self, url: str, config: Config, segment_duration: int = 200):
        self.seq = 1
        self.url = url
        self.config = config
        self.segment_duration = segment_duration
        self.conn = None
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        if self.conn and not self.conn.closed:
            await self.conn.close()
        if self.session and not self.session.closed:
            await self.session.close()
        
    def get_segment_size(self, content: bytes) -> int:
        try:
            with io.BytesIO(content) as buffer:
                with wave.open(buffer, 'rb') as wav_file:
                    channel_num = wav_file.getnchannels()
                    samp_width = wav_file.getsampwidth()
                    frame_rate = wav_file.getframerate()
                    
                    size_per_sec = channel_num * samp_width * frame_rate
                    segment_size = size_per_sec * self.segment_duration // 1000
                    return segment_size
        except Exception as e:
            logger.error(f"Failed to calculate segment size: {e}")
            raise
            
    async def create_connection(self) -> None:
        headers = RequestBuilder.new_auth_headers(self.config)
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                self.conn = await self.session.ws_connect(
                    self.url,
                    headers=headers,
                    timeout=10.0  # 设置10秒超时
                )
                logger.info(f"Connected to {self.url}")
                return
            except Exception as e:
                error_msg = f"Failed to connect to WebSocket (attempt {attempt + 1}/{max_retries}): {e}"
                logger.error(error_msg)
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # 指数退避
                else:
                    # 最后一次尝试失败，抛出更友好的错误信息
                    if "DNS" in str(e) or "timeout" in str(e).lower():
                        raise NetworkError(
                            "Network connection failed: Unable to resolve DNS or connect to the server. Please check your network connection and try again.",
                            {"url": self.url, "error": str(e)}
                        )
                    raise
            
    async def send_full_client_request(self) -> None:
        request = RequestBuilder.new_full_client_request(self.seq)
        self.seq += 1
        try:
            await self.conn.send_bytes(request)
            logger.info(f"Sent full client request with seq: {self.seq-1}")
            
            msg = await self.conn.receive()
            if msg.type == aiohttp.WSMsgType.BINARY:
                response = ResponseParser.parse_response(msg.data)
                logger.info(f"Received response: {response.to_dict()}")
            else:
                logger.error(f"Unexpected message type: {msg.type}")
        except Exception as e:
            logger.error(f"Failed to send full client request: {e}")
            raise
            
    async def send_messages(self, segment_size: int, content: bytes) -> AsyncGenerator[None, None]:
        audio_segments = []
        for i in range(0, len(content), segment_size):
            end = i + segment_size
            if end > len(content):
                end = len(content)
            audio_segments.append(content[i:end])
        
        total_segments = len(audio_segments)
        
        for i, segment in enumerate(audio_segments):
            is_last = (i == total_segments - 1)
            request = RequestBuilder.new_audio_only_request(
                self.seq, 
                segment,
                is_last=is_last
            )
            await self.conn.send_bytes(request)
            logger.info(f"Sent audio segment with seq: {self.seq} (last: {is_last})")
            
            if not is_last:
                self.seq += 1
                
            await asyncio.sleep(self.segment_duration / 1000)
            yield
            
    async def recv_messages(self) -> AsyncGenerator[AsrResponse, None]:
        try:
            async for msg in self.conn:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    response = ResponseParser.parse_response(msg.data)
                    yield response
                    
                    if response.is_last_package or response.code != 0:
                        break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg.data}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logger.info("WebSocket connection closed")
                    break
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            raise
            
    async def start_audio_stream(self, segment_size: int, content: bytes) -> AsyncGenerator[AsrResponse, None]:
        async def sender():
            async for _ in self.send_messages(segment_size, content):
                pass
                
        sender_task = asyncio.create_task(sender())
        
        try:
            async for response in self.recv_messages():
                yield response
        finally:
            sender_task.cancel()
            try:
                await sender_task
            except asyncio.CancelledError:
                pass
                
    @async_error_handler
    async def execute(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            raise ValueError("Audio data is empty")
            
        try:
            segment_size = self.get_segment_size(audio_bytes)
            
            await self.create_connection()
            await self.send_full_client_request()
            
            full_transcript = ""
            async for response in self.start_audio_stream(segment_size, audio_bytes):
                if response.payload_msg and "result" in response.payload_msg:
                    text = response.payload_msg["result"].get("text", "")
                    if text:
                        full_transcript = text
            
            return full_transcript
            
        except Exception as e:
            logger.error(f"ASR execution error: {e}")
            raise


class SpeechToText:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "bigmodel"
    ):
        # 这里api_key实际上是access_key，base_url是app_key
        self.access_key = api_key or os.getenv("BYTEDANCE_ACCESS_KEY")
        self.app_key = base_url or os.getenv("BYTEDANCE_APP_KEY")
        self.model = model

        if not self.access_key or not self.app_key:
            raise ValueError("Both app_key and access_key are required for ByteDance ASR")

        self.ws_url = os.getenv("BYTEDANCE_WS_URL", "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_nostream")
        self.config = Config(self.app_key, self.access_key)

    def convert_audio_format(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        target_format: str = "wav"
    ) -> bytes:
        return convert_audio_format(audio_data, sample_rate, target_format)

    @async_error_handler
    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: str = "zh"
    ) -> str:
        try:
            audio_bytes = self.convert_audio_format(audio_data, sample_rate)

            async with AsrWsClient(self.ws_url, self.config) as client:
                text = await client.execute(audio_bytes)
                
            logger.info(f"Transcription: {text}")
            return text

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    @async_error_handler
    async def transcribe_with_vad(
        self,
        audio_chunks: list[np.ndarray],
        sample_rate: int = 16000,
        language: str = "zh"
    ) -> str:
        try:
            if not audio_chunks:
                logger.warning("No audio chunks provided for transcription")
                return ""

            # 创建VAD处理器
            vad_processor = VADProcessor(sample_rate=sample_rate)
            speech_segments = []
            
            logger.info(f"Processing {len(audio_chunks)} audio chunks with VAD")
            
            # 处理每个音频块，提取语音段
            for chunk in audio_chunks:
                is_speech_end, complete_speech = vad_processor.process_chunk(chunk)
                if complete_speech:
                    speech_segments.extend(complete_speech)
            
            # 处理可能剩余的语音段
            if vad_processor.speech_chunks:
                speech_segments.extend(vad_processor.speech_chunks)
                vad_processor.reset()
            
            if not speech_segments:
                logger.info("No speech detected in audio chunks")
                return ""
            
            # 合并语音段
            combined_audio = np.concatenate(speech_segments)
            
            min_samples = int(0.1 * sample_rate)
            if len(combined_audio) < min_samples:
                logger.warning(f"Audio too short after VAD: {len(combined_audio)} samples, minimum required: {min_samples}")
                return ""
            
            logger.info(f"Transcribing speech: {len(combined_audio)} samples, sample rate: {sample_rate}Hz")
            result = await self.transcribe(combined_audio, sample_rate, language)
            logger.info(f"Transcription result: {result[:50]}..." if result else "No transcription result")
            return result
        except Exception as e:
            logger.error(f"Error in transcribe_with_vad: {e}")
            return ""


class VADProcessor:
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        silence_threshold: float = 0.02,
        min_speech_duration: float = 0.3
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold
        self.min_speech_duration = min_speech_duration
        self.speech_chunks = []
        self.is_speaking = False
        self.silence_counter = 0

    def process_chunk(self, audio_chunk: np.ndarray) -> tuple[bool, Optional[list[np.ndarray]]]:
        energy = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
        energy_normalized = energy / 32768.0

        is_speech = energy_normalized > self.silence_threshold

        if is_speech:
            self.speech_chunks.append(audio_chunk)
            self.silence_counter = 0
            self.is_speaking = True
        elif self.is_speaking:
            self.silence_counter += 1
            silence_duration = (self.silence_counter * self.chunk_size) / self.sample_rate

            if silence_duration >= self.min_speech_duration:
                if self.speech_chunks:
                    complete_speech = self.speech_chunks[:]
                    self.speech_chunks = []
                    self.is_speaking = False
                    self.silence_counter = 0
                    return True, complete_speech

        return False, None

    def reset(self):
        self.speech_chunks = []
        self.is_speaking = False
        self.silence_counter = 0
