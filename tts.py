import io
import logging
import numpy as np
from typing import Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextToSpeech:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "tts-1",
        voice: str = "nova",
        target_sample_rate: int = 16000
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "sk-wiHpoarpNTHaep0t54852a32A75a4d6986108b3f6eF7B7B9")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://openkey.cloud/v1")
        self.model = model
        self.voice = voice
        self.target_sample_rate = target_sample_rate

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def synthesize(self, text: str) -> np.ndarray:
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="wav"
            )

            audio_bytes = response.content
            
            if len(audio_bytes) < 44:
                logger.error(f"Invalid WAV file: too small ({len(audio_bytes)} bytes)")
                return np.array([], dtype=np.int16)
            
            header = audio_bytes[:44]
            if not header.startswith(b'RIFF') or b'WAVE' not in header:
                logger.error("Invalid WAV file: missing RIFF/WAVE header")
                return np.array([], dtype=np.int16)
            
            channels = int.from_bytes(header[22:24], byteorder='little')
            sample_rate = int.from_bytes(header[24:28], byteorder='little')
            bits_per_sample = int.from_bytes(header[34:36], byteorder='little')
            
            logger.info(f"WAV format: {channels} channels, {sample_rate}Hz, {bits_per_sample} bits")
            
            audio_data = audio_bytes[44:]
            
            if bits_per_sample == 16:
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
            elif bits_per_sample == 24:
                audio_array = np.frombuffer(audio_data, dtype=np.uint8)
                audio_array = audio_array.reshape(-1, 3)
                audio_array = (audio_array[:, 0].astype(np.int32) | 
                              (audio_array[:, 1].astype(np.int32) << 8) | 
                              (audio_array[:, 2].astype(np.int32) << 16))
                audio_array = ((audio_array >> 8) - 32768).astype(np.int16)
            elif bits_per_sample == 32:
                audio_array = np.frombuffer(audio_data, dtype=np.int32)
                audio_array = (audio_array >> 16).astype(np.int16)
            else:
                logger.error(f"Unsupported bits per sample: {bits_per_sample}")
                return np.array([], dtype=np.int16)
            
            if channels == 2:
                audio_array = audio_array.reshape(-1, 2)
                audio_array = audio_array.mean(axis=1).astype(np.int16)
            
            if sample_rate != self.target_sample_rate:
                ratio = self.target_sample_rate / sample_rate
                new_length = int(len(audio_array) * ratio)
                audio_array = np.interp(
                    np.linspace(0, len(audio_array) - 1, new_length),
                    np.arange(len(audio_array)),
                    audio_array
                ).astype(np.int16)
                logger.info(f"Resampled from {sample_rate}Hz to {self.target_sample_rate}Hz")
            
            logger.info(f"Synthesized audio for text: {text[:50]}..., length: {len(audio_array)} samples")
            return audio_array

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return np.array([], dtype=np.int16)

    async def synthesize_stream(self, text: str):
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text
            )

            audio_bytes = response.content
            buffer = io.BytesIO(audio_bytes)

            while True:
                chunk = buffer.read(4096)
                if not chunk:
                    break
                yield np.frombuffer(chunk, dtype=np.int16)

        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            yield np.array([], dtype=np.int16)

    def set_voice(self, voice: str):
        available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice in available_voices:
            self.voice = voice
            logger.info(f"Voice changed to {voice}")
        else:
            logger.warning(f"Voice {voice} not available. Using {self.voice}")

    def set_model(self, model: str):
        available_models = ["tts-1", "tts-1-hd"]
        if model in available_models:
            self.model = model
            logger.info(f"Model changed to {model}")
        else:
            logger.warning(f"Model {model} not available. Using {self.model}")
