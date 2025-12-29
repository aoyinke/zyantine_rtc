import asyncio
import logging
import numpy as np
from rtc_client import RTCClient, AudioStreamer
from stt import SpeechToText, VADProcessor
from tts import TextToSpeech
from ai_conversation import ConversationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIRTCSystem:
    def __init__(
        self,
        signaling_url: str = "ws://localhost:8765",
        client_id: str = "ai_client",
        room_id: str = "default"
    ):
        self.client_id = client_id
        self.room_id = room_id

        self.rtc_client = RTCClient(signaling_url, client_id, room_id)
        self.audio_streamer = AudioStreamer()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.conversation_manager = ConversationManager()

        self.vad_processor = VADProcessor()
        self.is_running = False

    async def start(self):
        logger.info("Starting AI RTC System...")

        if not await self.rtc_client.connect():
            logger.error("Failed to connect to signaling server")
            return

        self.is_running = True
        self.audio_streamer.start_recording()

        tasks = [
            self.process_audio_stream(),
            self.handle_incoming_messages()
        ]

        await asyncio.gather(*tasks)

    async def process_audio_stream(self):
        logger.info("Starting audio stream processing...")

        while self.is_running:
            try:
                audio_chunk = self.audio_streamer.read_audio_chunk()

                if len(audio_chunk) > 0:
                    has_speech, speech_chunks = self.vad_processor.process_chunk(audio_chunk)

                    if has_speech and speech_chunks:
                        await self.handle_speech(speech_chunks)

                await asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Error processing audio stream: {e}")

    async def handle_speech(self, speech_chunks: list[np.ndarray]):
        logger.info("Processing speech...")

        user_text = await self.stt.transcribe_with_vad(speech_chunks)

        if user_text.strip():
            logger.info(f"User said: {user_text}")

            ai_response = await self.conversation_manager.process_user_input(user_text)

            if ai_response.strip():
                logger.info(f"AI response: {ai_response}")

                audio_response = await self.tts.synthesize(ai_response)

                if len(audio_response) > 0:
                    self.audio_streamer.play_audio(audio_response)

    async def handle_incoming_messages(self):
        logger.info("Starting message handler...")

        while self.is_running:
            try:
                message = await self.rtc_client.message_queue.get()

                message_type = message.get("type")

                if message_type == "audio_data":
                    await self.handle_remote_audio(message)

                elif message_type == "text_message":
                    await self.handle_text_message(message)

            except Exception as e:
                logger.error(f"Error handling message: {e}")

    async def handle_remote_audio(self, message: dict):
        audio_hex = message.get("audio_data", "")
        if audio_hex:
            try:
                audio_bytes = bytes.fromhex(audio_hex)
                audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

                has_speech, speech_chunks = self.vad_processor.process_chunk(audio_array)

                if has_speech and speech_chunks:
                    await self.handle_speech(speech_chunks)

            except Exception as e:
                logger.error(f"Error processing remote audio: {e}")

    async def handle_text_message(self, message: dict):
        text = message.get("text", "")
        if text.strip():
            logger.info(f"Received text message: {text}")

            ai_response = await self.conversation_manager.process_user_input(text)

            if ai_response.strip():
                audio_response = await self.tts.synthesize(ai_response)

                if len(audio_response) > 0:
                    self.audio_streamer.play_audio(audio_response)

    async def stop(self):
        logger.info("Stopping AI RTC System...")
        self.is_running = False
        self.audio_streamer.stop_recording()
        await self.rtc_client.disconnect()
        logger.info("AI RTC System stopped")


async def main():
    system = AIRTCSystem(
        signaling_url="ws://localhost:8765",
        client_id="ai_client_1",
        room_id="room_1"
    )

    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(main())
