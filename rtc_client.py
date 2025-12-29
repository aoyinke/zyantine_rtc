import asyncio
import json
import logging
import pyaudio
import numpy as np
from websockets import connect
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioStreamer:
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        format: int = pyaudio.paInt16
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = format
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False

    def start_recording(self):
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        self.is_recording = True
        logger.info("Audio recording started")

    def stop_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.is_recording = False
            logger.info("Audio recording stopped")

    def read_audio_chunk(self) -> np.ndarray:
        if not self.stream or not self.is_recording:
            return np.array([], dtype=np.int16)

        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        audio_array = np.frombuffer(data, dtype=np.int16)
        return audio_array

    def play_audio(self, audio_data: np.ndarray):
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            output=True
        )
        stream.write(audio_data.tobytes())
        stream.stop_stream()
        stream.close()

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()


class RTCClient:
    def __init__(
        self,
        signaling_url: str,
        client_id: str,
        room_id: str = "default"
    ):
        self.signaling_url = signaling_url
        self.client_id = client_id
        self.room_id = room_id
        self.websocket = None
        self.audio_streamer = AudioStreamer()
        self.message_queue = asyncio.Queue()
        self.is_connected = False

    async def connect(self):
        try:
            self.websocket = await connect(self.signaling_url)
            self.is_connected = True
            logger.info(f"Connected to signaling server as {self.client_id}")

            await self.send_message({
                "type": "join",
                "client_id": self.client_id,
                "room_id": self.room_id
            })

            asyncio.create_task(self.receive_messages())
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def send_message(self, message: dict):
        if self.websocket:
            await self.websocket.send(json.dumps(message))

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.message_queue.put(data)
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self.is_connected = False

    async def send_audio_data(self, audio_data: np.ndarray):
        audio_base64 = audio_data.tobytes()
        await self.send_message({
            "type": "audio_data",
            "client_id": self.client_id,
            "audio_data": audio_base64.hex()
        })

    async def start_audio_stream(self):
        self.audio_streamer.start_recording()

        while self.is_connected:
            audio_chunk = self.audio_streamer.read_audio_chunk()
            if len(audio_chunk) > 0:
                await self.send_audio_data(audio_chunk)
            await asyncio.sleep(0.01)

    async def stop_audio_stream(self):
        self.audio_streamer.stop_recording()

    async def disconnect(self):
        if self.websocket:
            await self.send_message({
                "type": "leave",
                "client_id": self.client_id,
                "room_id": self.room_id
            })
            await self.websocket.close()
            self.is_connected = False
        self.audio_streamer.close()
        logger.info("Disconnected from server")


async def main():
    client = RTCClient(
        signaling_url="ws://localhost:8765",
        client_id="client_1",
        room_id="room_1"
    )

    if await client.connect():
        try:
            await client.start_audio_stream()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
