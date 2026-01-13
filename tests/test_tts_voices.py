import asyncio
from tts import TextToSpeech

async def test_voices():
    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    test_text = "你好，这是一个语音测试。"
    
    print("测试不同的 TTS 声音：")
    print("=" * 50)
    
    for voice in voices:
        print(f"\n正在测试声音: {voice}")
        tts = TextToSpeech(voice=voice)
        audio = await tts.synthesize(test_text)
        
        if len(audio) > 0:
            print(f"  ✓ 成功生成音频")
            print(f"  - 音频长度: {len(audio)} 采样点")
            print(f"  - 音频时长: {len(audio)/16000:.2f} 秒")
            print(f"  - 音量范围: [{audio.min()}, {audio.max()}]")
        else:
            print(f"  ✗ 生成失败")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n声音说明：")
    print("- alloy: 中性声音，平衡")
    print("- echo: 男性声音，深沉")
    print("- fable: 英式口音，温暖")
    print("- onyx: 男性声音，深沉稳重")
    print("- nova: 女性声音，清晰明亮（推荐）")
    print("- shimmer: 女性声音，柔和")
    print("\n你可以在 ai_rtc_system.py 中修改 TextToSpeech 的初始化参数来更换声音：")
    print("  self.tts = TextToSpeech(voice='nova')")

if __name__ == "__main__":
    asyncio.run(test_voices())
