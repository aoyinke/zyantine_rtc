import wave
import struct
import numpy as np

# 设置音频参数
sample_rate = 16000  # 采样率
duration = 2  # 持续时间（秒）
frequency = 440  # 频率（Hz）
volume = 0.5  # 音量

# 创建WAV文件
with wave.open('test.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # 单声道
    wav_file.setsampwidth(2)  # 16位
    wav_file.setframerate(sample_rate)
    
    # 生成音频数据
    num_samples = sample_rate * duration
    samples = [int(volume * 32767 * np.sin(2 * np.pi * frequency * i / sample_rate)) for i in range(num_samples)]
    
    # 写入数据
    for sample in samples:
        wav_file.writeframes(struct.pack('<h', sample))

print("Test audio file 'test.wav' created successfully.")