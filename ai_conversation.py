import asyncio
import logging
from typing import List, Dict, Optional
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIConversation:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "zyantine-v1",
        system_prompt: str = "你是一个友好的AI助手，可以进行自然的对话。"
    ):
        self.api_key = api_key or os.getenv("ZYANTINE_API_KEY", "")
        self.base_url = base_url or os.getenv("ZYANTINE_BASE_URL", "http://localhost:8001")
        self.model = model
        self.system_prompt = system_prompt

        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

    async def get_response(self, user_message: str) -> str:
        try:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            url = f"{self.base_url}/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": self.model,
                "messages": self.conversation_history,
                "temperature": 0.7,
                "max_tokens": 500
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return "抱歉，我遇到了一些问题，请稍后再试。"

                    data = await response.json()
                    assistant_message = data["choices"][0]["message"]["content"]

            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            logger.info(f"AI Response: {assistant_message[:100]}...")
            return assistant_message

        except Exception as e:
            logger.error(f"Conversation error: {e}")
            return "抱歉，我遇到了一些问题，请稍后再试。"

    def clear_history(self):
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
        logger.info("Conversation history cleared")

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt
        self.conversation_history[0] = {"role": "system", "content": prompt}
        logger.info("System prompt updated")

    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history.copy()


class ConversationManager:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversation = AIConversation()

    async def process_user_input(self, user_text: str) -> str:
        response = await self.conversation.get_response(user_text)

        history = self.conversation.get_history()
        if len(history) > self.max_history * 2 + 1:
            system_msg = history[0]
            recent_messages = history[-(self.max_history * 2):]
            self.conversation.conversation_history = [system_msg] + recent_messages

        return response

    def reset(self):
        self.conversation.clear_history()
