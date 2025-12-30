import asyncio
import logging
import numpy as np
from stt import SpeechToText
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

        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.conversation_manager = ConversationManager()

    async def stop(self):
        logger.info("Stopping AI RTC System...")
        logger.info("AI RTC System stopped")
