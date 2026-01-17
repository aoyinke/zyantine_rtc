import { ref, computed } from 'vue'
import { useAudioStore } from '../stores/audio'

// 音频处理组合式API
export function useAudio() {
  const audioStore = useAudioStore()
  const isRecording = computed(() => audioStore.isRecording)
  const isPlaying = computed(() => audioStore.isPlaying)
  
  // 延迟导入useWebSocket以避免Pinia初始化问题
  let sendAudioData = null
  let sendMessage = null
  let stopConversationCallback = null
  
  async function getWebSocketFunctions() {
    if (!sendAudioData || !sendMessage) {
      const { useWebSocket } = await import('./useWebSocket')
      const { sendAudioData: _sendAudioData, sendMessage: _sendMessage } = useWebSocket()
      sendAudioData = _sendAudioData
      sendMessage = _sendMessage
    }
    return { sendAudioData, sendMessage }
  }
  
  // 语音活动检测（VAD）配置
  const vadConfig = {
    sampleRate: 16000,
    chunkSize: 1024,
    silenceThreshold: 0.005,  // 进一步降低静音阈值，提高检测灵敏度
    minSpeechDuration: 0.1,  // 进一步降低最小语音时长
    maxSilenceDuration: 0.6,  // 进一步降低最大静音时长，更快检测停止说话
  }
  
  // VAD状态
  const vadState = {
    isSpeaking: false,
    speechChunks: [],
    silenceCounter: 0,
    silenceStartTime: null,
  }
  
  // 处理VAD（语音活动检测）
  function processVAD(audioChunk) {
    // 计算音频能量
    const energy = Math.sqrt(audioChunk.reduce((sum, sample) => sum + (sample * sample), 0) / audioChunk.length)
    const energyNormalized = energy / 32768.0
    
    console.log('VAD: Energy:', energyNormalized.toFixed(6), 'Threshold:', vadConfig.silenceThreshold)
    
    const isSpeech = energyNormalized > vadConfig.silenceThreshold
    
    if (isSpeech) {
      // 检测到语音
      console.log('VAD: Detected speech - isSpeaking:', vadState.isSpeaking)
      vadState.isSpeaking = true
      vadState.silenceCounter = 0
      vadState.silenceStartTime = null
      vadState.speechChunks.push(audioChunk)
      console.log('VAD: Speech chunks count:', vadState.speechChunks.length)
    } else {
      console.log('VAD: Detected silence - isSpeaking:', vadState.isSpeaking)
      if (vadState.isSpeaking) {
        // 检测到静音，且之前在说话
        vadState.silenceCounter++
        console.log('VAD: Silence counter:', vadState.silenceCounter)
        
        if (!vadState.silenceStartTime) {
          vadState.silenceStartTime = Date.now()
          console.log('VAD: Started silence timer at:', vadState.silenceStartTime)
        }
        
        // 计算静音时长
        const silenceDuration = (Date.now() - vadState.silenceStartTime) / 1000
        console.log('VAD: Silence duration:', silenceDuration.toFixed(3), 'Max:', vadConfig.maxSilenceDuration)
        
        // 如果静音时长超过阈值，认为用户停止说话
        if (silenceDuration > vadConfig.maxSilenceDuration) {
          // 检查是否有足够的语音数据
          const totalSpeechDuration = (vadState.speechChunks.length * vadConfig.chunkSize) / vadConfig.sampleRate
          console.log('VAD: Total speech duration:', totalSpeechDuration.toFixed(3), 'Min:', vadConfig.minSpeechDuration)
          console.log('VAD: Speech chunks total:', vadState.speechChunks.length, 'Chunk size:', vadConfig.chunkSize)
          
          if (totalSpeechDuration > vadConfig.minSpeechDuration) {
            // 用户停止说话，且有足够的语音数据
            console.log('VAD: User stopped speaking - triggering processing')
            // 将异步操作移到事件循环中执行，避免阻塞音频处理线程
            setTimeout(() => {
              handleUserStoppedSpeaking()
            }, 0)
          } else {
            // 语音时长太短，重置VAD状态
            console.log('VAD: Speech too short, resetting')
            resetVAD()
          }
        }
      }
    }
  }
  
  // 重置VAD状态
  function resetVAD() {
    vadState.isSpeaking = false
    vadState.speechChunks = []
    vadState.silenceCounter = 0
    vadState.silenceStartTime = null
  }
  
  // 处理用户停止说话
  async function handleUserStoppedSpeaking() {
    try {
      console.log('=== Handling user stopped speaking ===')
      
      // 发送停止录音消息（但不实际停止录音设备）
      console.log('Sending stop recording message...')
      if (sendMessage) {
        sendMessage({ type: 'stop_recording' })
        console.log('Stop recording message sent')
      } else {
        console.error('sendMessage is not initialized')
      }
      
      // 重置VAD状态，准备下一轮监听
      console.log('Resetting VAD state...')
      resetVAD()
      console.log('VAD state reset')
      console.log('=== User stopped speaking handling complete ===')
    } catch (error) {
      console.error('Error handling user stopped speaking:', error)
    }
  }
  
  // 开始录音
  async function startRecording(callback) {
    try {
      // 保存停止对话回调
      stopConversationCallback = callback
      
      // 提前初始化WebSocket函数
      await getWebSocketFunctions()
      
      // 重置VAD状态
      resetVAD()
      
      // 请求麦克风权限
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioStore.setMediaStream(mediaStream)
      
      // 创建音频上下文
      let audioContext = audioStore.audioContext
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
          sampleRate: audioStore.config.sampleRate
        })
        audioStore.setAudioContext(audioContext)
      } else if (audioContext.state === 'suspended') {
        await audioContext.resume()
      }
      
      // 创建媒体流源
      const source = audioContext.createMediaStreamSource(mediaStream)
      
      // 创建脚本处理器
      const scriptProcessor = audioContext.createScriptProcessor(
        audioStore.config.bufferSize,
        audioStore.config.channels,
        audioStore.config.channels
      )
      audioStore.setScriptProcessor(scriptProcessor)
      
      // 音频处理回调
      scriptProcessor.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0)
        const pcmData = new Int16Array(inputData.length)
        
        // 转换为PCM数据
        for (let i = 0; i < inputData.length; i++) {
          pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF
        }
        
        // 添加到音频数据
        audioStore.addAudioChunk(pcmData)
        
        // 发送音频数据到服务器
        const uint8Array = new Uint8Array(pcmData.buffer)
        const binary = String.fromCharCode(...uint8Array)
        const base64Data = btoa(binary)
        if (sendAudioData) {
          sendAudioData(base64Data)
        }
        
        // 处理VAD（语音活动检测）
        processVAD(pcmData)
      }
      
      // 连接音频处理链
      source.connect(scriptProcessor)
      scriptProcessor.connect(audioContext.destination)
      
      // 更新状态
      audioStore.setRecording(true)
      
    } catch (error) {
      console.error('Error starting recording:', error)
      throw new Error('无法访问麦克风')
    }
  }
  
  // 停止录音
  async function stopRecording() {
    try {
      // 停止媒体流
      if (audioStore.mediaStream) {
        audioStore.mediaStream.getTracks().forEach(track => track.stop())
        audioStore.setMediaStream(null)
      }
      
      // 断开脚本处理器
      if (audioStore.scriptProcessor) {
        audioStore.scriptProcessor.disconnect()
        audioStore.setScriptProcessor(null)
      }
      
      // 挂起音频上下文，而不是关闭它
      if (audioStore.audioContext && audioStore.audioContext.state === 'running') {
        await audioStore.audioContext.suspend()
        console.log('Audio context suspended')
      }
      
      // 清空音频数据
      audioStore.clearAudioChunks()
      
      // 更新状态
      audioStore.setRecording(false)
      
    } catch (error) {
      console.error('Error stopping recording:', error)
      throw new Error('无法停止录音')
    }
  }
  
  // 播放音频
  async function playAudio(arrayBuffer) {
    try {
      // 创建或恢复音频上下文
      let audioContext = audioStore.audioContext
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)()
        audioStore.setAudioContext(audioContext)
        console.log('Created new audio context')
      } else {
        // 恢复音频上下文
        if (audioContext.state === 'suspended') {
          await audioContext.resume()
          console.log('Resumed audio context')
        } else if (audioContext.state === 'closed') {
          // 如果音频上下文已关闭，创建新的
          audioContext = new (window.AudioContext || window.webkitAudioContext)()
          audioStore.setAudioContext(audioContext)
          console.log('Created new audio context (previous was closed)')
        }
      }
      
      // 解码音频数据
      console.log('Decoding audio data, buffer length:', arrayBuffer.byteLength)
      const buffer = await audioContext.decodeAudioData(arrayBuffer)
      console.log('Audio data decoded successfully, duration:', buffer.duration.toFixed(2), 'seconds')
      
      // 创建音频源
      const source = audioContext.createBufferSource()
      source.buffer = buffer
      
      // 创建音量控制
      const gainNode = audioContext.createGain()
      gainNode.gain.value = audioStore.volume
      
      // 添加平滑过渡效果，避免播放开始和结束时的突兀感
      const currentTime = audioContext.currentTime
      const fadeDuration = 0.05 // 50ms的淡入淡出时间
      
      // 淡入效果
      gainNode.gain.setValueAtTime(0, currentTime)
      gainNode.gain.linearRampToValueAtTime(audioStore.volume, currentTime + fadeDuration)
      
      // 淡出效果
      gainNode.gain.setValueAtTime(audioStore.volume, currentTime + buffer.duration - fadeDuration)
      gainNode.gain.linearRampToValueAtTime(0, currentTime + buffer.duration)
      
      // 连接音频处理链
      source.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      // 播放完成回调
      source.onended = () => {
        console.log('Audio playback ended')
        // 短暂延迟后再播放下一个音频，避免播放间隙的突兀感
        setTimeout(() => {
          if (audioStore.audioQueue.length > 0) {
            // 播放队列中的下一个音频
            const nextAudio = audioStore.getAudioFromQueue()
            console.log('Playing next audio from queue, remaining:', audioStore.audioQueue.length)
            playAudio(nextAudio)
          } else {
            // 播放完成
            audioStore.setPlaying(false)
            audioStore.setCurrentSource(null)
            console.log('All audio playback completed')
            console.log('=== Ready for next user input ===')
            // 播放完成后，重置VAD状态，准备监听用户下一次说话
            resetVAD()
            // 更新聊天状态为connected，准备接受用户下一次输入
            import('../stores/chat').then(({ useChatStore }) => {
              const chatStore = useChatStore()
              chatStore.setStatus('connected')
            })
          }
        }, 10) // 10ms的延迟
      }
      
      // 更新状态
      audioStore.setPlaying(true)
      audioStore.setCurrentSource(source)
      
      // 开始播放
      console.log('Starting audio playback')
      source.start(0)
      
    } catch (error) {
      console.error('Error playing audio:', error)
      audioStore.setPlaying(false)
      audioStore.setCurrentSource(null)
      
      // 尝试播放队列中的下一个音频
      if (audioStore.audioQueue.length > 0) {
        const nextAudio = audioStore.getAudioFromQueue()
        console.log('Playing next audio after error')
        playAudio(nextAudio)
      }
    }
  }
  
  // 添加音频到播放队列
  function queueAudio(arrayBuffer) {
    console.log('Adding audio to queue, current queue length:', audioStore.audioQueue.length)
    audioStore.addAudioToQueue(arrayBuffer)
    console.log('Audio added to queue, new queue length:', audioStore.audioQueue.length)
    
    // 如果当前没有播放，开始播放
    if (!audioStore.isPlaying && audioStore.audioQueue.length > 0) {
      console.log('No audio currently playing, starting playback')
      const audioData = audioStore.getAudioFromQueue()
      console.log('Retrieved audio from queue, remaining queue length:', audioStore.audioQueue.length)
      playAudio(audioData)
    } else {
      console.log('Audio is already playing or queue is empty, will play after current audio')
    }
  }
  
  // 停止播放
  function stopPlaying() {
    if (audioStore.currentSource) {
      try {
        audioStore.currentSource.stop()
      } catch (e) {
        // 忽略已经停止的错误
      }
      audioStore.setCurrentSource(null)
    }
    
    audioStore.clearAudioQueue()
    audioStore.setPlaying(false)
  }
  
  // 设置音量
  function setVolume(volume) {
    audioStore.setVolume(volume)
  }
  
  // 更新音频配置
  function updateConfig(config) {
    audioStore.updateConfig(config)
  }
  
  // 停止所有音频
  function stopAllAudio() {
    stopRecording()
    stopPlaying()
    audioStore.stopAllAudio()
  }
  
  return {
    startRecording,
    stopRecording,
    playAudio,
    queueAudio,
    stopPlaying,
    setVolume,
    updateConfig,
    stopAllAudio,
    isRecording,
    isPlaying,
  }
}