import asyncio
import logging
from typing import List, Dict, Optional
from openai import OpenAI
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
        model: str = "gpt-4.1-nano-2025-04-14",
        system_prompt: str = "你是一个友好的AI助手，可以进行自然的对话。"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "sk-wiHpoarpNTHaep0t54852a32A75a4d6986108b3f6eF7B7B9")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://openkey.cloud/v1")
        self.model = model
        self.system_prompt = system_prompt

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

    async def get_response(self, user_message: str) -> str:
        try:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=500
            )

            assistant_message = response.choices[0].message.content
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
