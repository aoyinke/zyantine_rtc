import asyncio
import numpy as np
import os
from stt import SpeechToText

async def main():
    # 创建测试音频数据（440Hz正弦波）
    sample_rate = 16000
    duration = 2  # 2秒
    frequency = 440  # 440Hz
    volume = 0.5
    
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * volume * 32767).astype(np.int16)
    
    try:
        # 使用新的SpeechToText类
        stt = SpeechToText(
            api_key="q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c",  # access_key
            base_url="5474947932"  # app_key
        )
        
        # 测试转录功能
        result = await stt.transcribe(audio_data, sample_rate=sample_rate)
        print(f"Transcription result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())