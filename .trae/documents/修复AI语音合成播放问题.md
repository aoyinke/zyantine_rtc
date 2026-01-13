## 问题分析

AI回复后没有播放语音的原因是后端在发送完所有音频块后没有发送`audio_complete`消息，导致前端的音频队列永远不会被处理。

## 解决方案

修改后端的`process_speech_and_respond_stream`函数，在所有音频块发送完成后，添加发送`audio_complete`消息的代码。

## 具体修改

1. **文件**: `web_server.py`
2. **位置**: `process_speech_and_respond_stream`函数的音频流处理部分
3. **修改内容**: 在所有音频块发送完成后，添加发送`audio_complete`消息的代码

## 预期效果

修改后，当AI生成语音响应时，后端会发送所有音频块，然后发送`audio_complete`消息，前端收到该消息后会处理音频队列并播放语音，实现完整的语音交互流程。