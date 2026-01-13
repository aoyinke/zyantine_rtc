import asyncio
import logging
import numpy as np
import os
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
        room_id: str = "default",
        stt_app_key: str = None,
        stt_access_key: str = None,
        stt_model: str = "bigmodel"
    ):
        self.client_id = client_id
        self.room_id = room_id
        self.is_running = True

        # 获取字节跳动ASR的配置
        try:
            self.stt = SpeechToText(
                api_key=stt_access_key or os.getenv("BYTEDANCE_ACCESS_KEY") or "q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c",
                base_url=stt_app_key or os.getenv("BYTEDANCE_APP_KEY") or "5474947932",
                model=stt_model
            )
            logger.info("SpeechToText initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SpeechToText: {e}")
            raise

        try:
            self.tts = TextToSpeech()
            logger.info("TextToSpeech initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TextToSpeech: {e}")
            raise

        try:
            self.conversation_manager = ConversationManager()
            logger.info("ConversationManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ConversationManager: {e}")
            raise

    async def stop(self):
        logger.info("Stopping AI RTC System...")
        self.is_running = False
        
        # 清理资源
        try:
            # 这里可以添加更多清理逻辑
            pass
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("AI RTC System stopped")

    def get_status(self):
        """获取系统状态"""
        return {
            "is_running": self.is_running,
            "client_id": self.client_id,
            "room_id": self.room_id
        }

    def reset_conversation(self):
        """重置对话历史"""
        if self.conversation_manager:
            self.conversation_manager.reset()
            logger.info("Conversation history reset")

    def set_voice(self, voice_type: str):
        """设置TTS语音类型"""
        if self.tts:
            self.tts.set_voice(voice_type)
            logger.info(f"Voice set to: {voice_type}")
