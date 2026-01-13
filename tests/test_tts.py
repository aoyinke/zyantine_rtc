import asyncio
import logging
import numpy as np
from tts import TextToSpeech

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_synthesize_stream():
    """测试流式语音合成功能"""
    try:
        # 创建TTS实例
        tts = TextToSpeech(
            appid="5474947932",
            access_token="q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c"
        )
        
        test_text = "你好，这是一个测试消息。"
        logger.info(f"Testing TTS with text: {test_text}")
        
        # 测试流式合成
        audio_chunks = []
        async for audio_chunk in tts.synthesize_stream(test_text):
            logger.info(f"Received audio chunk: {len(audio_chunk)} samples")
            if len(audio_chunk) > 0:
                audio_chunks.append(audio_chunk)
        
        if not audio_chunks:
            logger.error("No audio chunks received from TTS service")
            return False
        
        # 合并所有音频块
        full_audio = np.concatenate(audio_chunks)
        logger.info(f"Total audio length: {len(full_audio)} samples")
        
        # 验证音频数据
        if len(full_audio) > 0:
            logger.info("TTS streaming test PASSED")
            logger.info(f"Audio range: {np.min(full_audio)} to {np.max(full_audio)}")
            logger.info(f"Audio dtype: {full_audio.dtype}")
            return True
        else:
            logger.error("No valid audio data received")
            return False
            
    except Exception as e:
        logger.error(f"TTS test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_convert_mp3_to_pcm():
    """测试MP3到PCM的转换功能"""
    try:
        tts = TextToSpeech(
            appid="5474947932",
            access_token="q-ZhU5ZhND2Xva_cGEgZYSuN5NpCMQ6c"
        )
        
        # 创建一个简单的测试MP3文件（使用ffmpeg生成）
        import subprocess
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
            mp3_path = temp_mp3.name
        
        try:
            # 使用ffmpeg生成一个简单的MP3文件
            subprocess.run([
                'ffmpeg', '-y',
                '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
                '-ar', '24000',
                '-ac', '1',
                '-b:a', '64k',
                mp3_path
            ], check=True, capture_output=True)
            
            # 读取MP3文件
            with open(mp3_path, 'rb') as f:
                mp3_data = f.read()
            
            logger.info(f"Testing convert_mp3_to_pcm with {len(mp3_data)} bytes MP3 data")
            
            # 转换为PCM
            pcm_data = tts.convert_mp3_to_pcm(mp3_data)
            logger.info(f"Conversion result: {len(pcm_data)} samples")
            
            if len(pcm_data) > 0:
                logger.info("MP3 to PCM conversion test PASSED")
                logger.info(f"PCM data range: {np.min(pcm_data)} to {np.max(pcm_data)}")
                return True
            else:
                logger.error("MP3 to PCM conversion returned empty array")
                return False
                
        finally:
            # 清理临时文件
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)
                
    except Exception as e:
        logger.error(f"MP3 to PCM test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """运行所有测试"""
    logger.info("Starting TTS tests...")
    
    # 先测试MP3到PCM的转换
    logger.info("\n=== Testing MP3 to PCM conversion ===")
    convert_ok = await test_convert_mp3_to_pcm()
    
    # 再测试流式合成
    logger.info("\n=== Testing TTS streaming ===")
    streaming_ok = await test_synthesize_stream()
    
    if convert_ok and streaming_ok:
        logger.info("\nAll TTS tests PASSED!")
        return 0
    else:
        logger.error("\nSome TTS tests FAILED!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)