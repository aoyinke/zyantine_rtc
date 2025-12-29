import io
import logging
import wave
import numpy as np
from typing import Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpeechToText:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "whisper-1"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "sk-wiHpoarpNTHaep0t54852a32A75a4d6986108b3f6eF7B7B9")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://openkey.cloud/v1")
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def convert_audio_format(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        target_format: str = "wav"
    ) -> bytes:
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(audio_data.dtype.itemsize)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        buffer.seek(0)
        return buffer.read()

    async def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: str = "zh"
    ) -> str:
        try:
            audio_bytes = self.convert_audio_format(audio_data, sample_rate)

            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=("audio.wav", audio_bytes, "audio/wav"),
                language=language
            )

            text = response.text
            logger.info(f"Transcription: {text}")
            return text

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

    async def transcribe_with_vad(
        self,
        audio_chunks: list[np.ndarray],
        sample_rate: int = 16000,
        language: str = "zh"
    ) -> str:
        if not audio_chunks:
            return ""

        combined_audio = np.concatenate(audio_chunks)
        
        min_samples = int(0.1 * sample_rate)
        if len(combined_audio) < min_samples:
            logger.warning(f"Audio too short: {len(combined_audio)} samples, minimum required: {min_samples}")
            return ""
        
        return await self.transcribe(combined_audio, sample_rate, language)


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
