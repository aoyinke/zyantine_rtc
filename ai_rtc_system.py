import asyncio
import logging
import numpy as np
import os
import json
from stt import SpeechToText
from tts import TextToSpeech
from ai_conversation import ConversationManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            return {}
    
    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

config_manager = ConfigManager()


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
            asr_app_key = stt_app_key or config_manager.get("stt.bytedance.app_key") or "5474947932"
            asr_access_key = stt_access_key or config_manager.get("stt.bytedance.access_key") or "q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c"
            
            self.stt = SpeechToText(
                api_key=asr_access_key,
                base_url=asr_app_key,
                model=stt_model
            )
            logger.info("SpeechToText initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SpeechToText: {e}")
            raise

        try:
            tts_appid = config_manager.get("tts.volcengine.appid") or "5474947932"
            tts_access_token = config_manager.get("tts.volcengine.access_token") or "q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c"
            tts_voice_type = config_manager.get("tts.volcengine.voice_type") or "zh_female_vv_uranus_bigtts"
            tts_endpoint = config_manager.get("tts.volcengine.endpoint") or "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
            
            self.tts = TextToSpeech(
                appid=tts_appid,
                access_token=tts_access_token,
                voice_type=tts_voice_type,
                endpoint=tts_endpoint
            )
            logger.info("TextToSpeech initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TextToSpeech: {e}")
            raise

        try:
            zyantine_api_key = config_manager.get("zyantine.api_key") or ""
            zyantine_base_url = config_manager.get("zyantine.base_url") or "http://localhost:8001"
            zyantine_model = config_manager.get("zyantine.model") or "zyantine-v1"
            
            self.conversation_manager = ConversationManager()
            # 更新AIConversation的配置
            self.conversation_manager.conversation.api_key = zyantine_api_key
            self.conversation_manager.conversation.base_url = zyantine_base_url
            self.conversation_manager.conversation.model = zyantine_model
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
