import asyncio
import logging
import wave
from tts import TextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_volcengine_tts():
    test_text = "你好，这是豆包语音合成测试。"
    
    print("测试豆包语音合成：")
    print("=" * 50)
    
    tts = TextToSpeech(
        voice_type="zh_female_vv_uranus_bigtts"
    )
    
    print(f"\n正在合成语音: {test_text}")
    audio = await tts.synthesize(test_text)
    
    if len(audio) > 0:
        print(f"✓ 成功生成音频")
        print(f"  - 音频长度: {len(audio)} 采样点")
        print(f"  - 音频时长: {len(audio)/16000:.2f} 秒")
        print(f"  - 音量范围: [{audio.min()}, {audio.max()}]")
        
        output_file = "test_output.wav"
        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio.tobytes())
        
        print(f"\n音频已保存到: {output_file}")
        print("你可以使用以下命令播放音频:")
        print(f"  afplay {output_file}")
        print(f"  或: open {output_file}")
    else:
        print(f"✗ 生成失败")
    
    print("\n" + "=" * 50)
    print("测试完成！")


if __name__ == "__main__":
    asyncio.run(test_volcengine_tts())
