import asyncio
import json
from typing import List, Dict, Optional, AsyncGenerator
import aiohttp
import os
from dotenv import load_dotenv
from error_handler import async_error_handler, AIError
from logger import get_logger

load_dotenv()

logger = get_logger(__name__)


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
        
        # 增强系统提示词，添加情绪分析要求
        enhanced_system_prompt = f"{system_prompt}\n\n" \
            "请在回复时，在内容末尾添加情绪标签，格式为：[EMOTION:情绪类型]\n" \
            "情绪类型可选值：neutral（中性）、happy（开心）、sad（悲伤）、angry（愤怒）、excited（兴奋）、calm（平静）、surprised（惊讶）、disgusted（厌恶）\n" \
            "请根据对话内容和上下文选择合适的情绪类型。"

        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": enhanced_system_prompt}
        ]
        self.current_emotion = "neutral"

    def extract_emotion(self, text: str) -> str:
        """从文本中提取情绪标签"""
        import re
        match = re.search(r'\[EMOTION:(\w+)\]', text)
        if match:
            emotion = match.group(1).lower()
            # 验证情绪类型是否有效
            valid_emotions = ["neutral", "happy", "sad", "angry", "excited", "calm", "surprised", "disgusted"]
            if emotion in valid_emotions:
                return emotion
        return "neutral"

    def remove_emotion_tag(self, text: str) -> str:
        """从文本中移除情绪标签"""
        import re
        # 定义有效的情绪类型
        valid_emotions = "neutral|happy|sad|angry|excited|calm|surprised|disgusted"
        # 移除格式化的情绪标签 [EMOTION:xxx]
        text = re.sub(r'\s*\[EMOTION:(?:' + valid_emotions + r')\]\s*$', '', text)
        # 移除直接附加的纯文本情绪词
        text = re.sub(r'\s*(?:' + valid_emotions + r')\s*$', '', text)
        return text.strip()

    @async_error_handler
    async def get_response(self, user_message: str, stream: bool = False) -> tuple[str, str]:
        if stream:
            # 使用流式响应
            full_response = ""
            async for chunk in self.get_response_stream(user_message):
                full_response += chunk
            # 提取情绪
            emotion = self.extract_emotion(full_response)
            # 移除情绪标签
            clean_response = self.remove_emotion_tag(full_response)
            self.current_emotion = emotion
            return clean_response, emotion
        
        # 非流式响应
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
                        return "抱歉，我遇到了一些问题，请稍后再试。", "neutral"

                    data = await response.json()
                    assistant_message = data["choices"][0]["message"]["content"]

            # 提取情绪
            emotion = self.extract_emotion(assistant_message)
            # 移除情绪标签
            clean_response = self.remove_emotion_tag(assistant_message)
            
            # 更新对话历史，使用清理后的响应
            self.conversation_history.append({
                "role": "assistant",
                "content": clean_response
            })

            self.current_emotion = emotion
            logger.info(f"AI Response: {clean_response[:100]}..., Emotion: {emotion}")
            return clean_response, emotion

        except Exception as e:
            logger.error(f"Conversation error: {e}")
            return "抱歉，我遇到了一些问题，请稍后再试。", "neutral"

    @async_error_handler
    async def get_response_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """获取流式响应"""
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
                "max_tokens": 500,
                "stream": True
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        yield "抱歉，我遇到了一些问题，请稍后再试。"
                        return

                    full_response = ""
                    async for chunk in response.content:
                        if chunk:
                            try:
                                chunk_str = chunk.decode('utf-8')
                                for line in chunk_str.splitlines():
                                    line = line.strip()
                                    if line.startswith('data: '):
                                        data = line[6:]
                                        if data == '[DONE]':
                                            break
                                        try:
                                            response_chunk = json.loads(data)
                                            delta = response_chunk['choices'][0]['delta']
                                            if 'content' in delta:
                                                content_chunk = delta['content']
                                                full_response += content_chunk
                                                # 过滤掉包含情绪标签的内容块
                                                # 检查是否包含情绪标签的开始或结束部分
                                                if 'EMOTION:' not in content_chunk and not content_chunk.strip().startswith(']') and not content_chunk.strip().endswith('['):
                                                    yield content_chunk
                                        except json.JSONDecodeError:
                                            continue
                            except UnicodeDecodeError:
                                continue

            # 提取情绪
            emotion = self.extract_emotion(full_response)
            # 移除情绪标签
            clean_response = self.remove_emotion_tag(full_response)
            
            # 更新对话历史，使用清理后的响应
            self.conversation_history.append({
                "role": "assistant",
                "content": clean_response
            })

            self.current_emotion = emotion
            logger.info(f"AI Response (streaming): {clean_response[:100]}..., Emotion: {emotion}")

        except Exception as e:
            logger.error(f"Streaming conversation error: {e}")
            yield "抱歉，我遇到了一些问题，请稍后再试。"

    def clear_history(self):
        # 重新创建增强系统提示词
        enhanced_system_prompt = f"{self.system_prompt}\n\n" \
            "请在回复时，在内容末尾添加情绪标签，格式为：[EMOTION:情绪类型]\n" \
            "情绪类型可选值：neutral（中性）、happy（开心）、sad（悲伤）、angry（愤怒）、excited（兴奋）、calm（平静）、surprised（惊讶）、disgusted（厌恶）\n" \
            "请根据对话内容和上下文选择合适的情绪类型。"
        
        self.conversation_history = [
            {"role": "system", "content": enhanced_system_prompt}
        ]
        self.current_emotion = "neutral"
        logger.info("Conversation history cleared")

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt
        # 创建增强系统提示词
        enhanced_system_prompt = f"{prompt}\n\n" \
            "请在回复时，在内容末尾添加情绪标签，格式为：[EMOTION:情绪类型]\n" \
            "情绪类型可选值：neutral（中性）、happy（开心）、sad（悲伤）、angry（愤怒）、excited（兴奋）、calm（平静）、surprised（惊讶）、disgusted（厌恶）\n" \
            "请根据对话内容和上下文选择合适的情绪类型。"
        self.conversation_history[0] = {"role": "system", "content": enhanced_system_prompt}
        logger.info("System prompt updated")

    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history.copy()


class ConversationManager:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversation = AIConversation()

    @async_error_handler
    async def process_user_input(self, user_text: str, stream: bool = False) -> tuple[str, str]:
        response, emotion = await self.conversation.get_response(user_text, stream=stream)

        history = self.conversation.get_history()
        if len(history) > self.max_history * 2 + 1:
            system_msg = history[0]
            recent_messages = history[-(self.max_history * 2):]
            self.conversation.conversation_history = [system_msg] + recent_messages

        return response, emotion

    @async_error_handler
    async def process_user_input_stream(self, user_text: str) -> AsyncGenerator[str, None]:
        """处理用户输入并返回流式响应"""
        async for chunk in self.conversation.get_response_stream(user_text):
            yield chunk

        history = self.conversation.get_history()
        if len(history) > self.max_history * 2 + 1:
            system_msg = history[0]
            recent_messages = history[-(self.max_history * 2):]
            self.conversation.conversation_history = [system_msg] + recent_messages

    def reset(self):
        self.conversation.clear_history()
        
    def get_current_emotion(self) -> str:
        """获取当前情绪"""
        return self.conversation.current_emotion
