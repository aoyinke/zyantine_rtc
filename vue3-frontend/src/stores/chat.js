import { defineStore } from 'pinia'

// 延迟导入useAudio以避免循环依赖
let useAudio = null
async function getUseAudio() {
  if (!useAudio) {
    const { useAudio: _useAudio } = await import('../composables/useAudio')
    useAudio = _useAudio
  }
  return useAudio
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    // 聊天消息列表
    messages: [],
    // 当前AI流式回复
    currentAIMessage: '',
    // 连接状态
    isConnected: false,
    // 当前状态
    status: 'idle', // idle, connected, recording, processing, generating, synthesizing, playing, error
    // 错误消息
    errorMessage: '',
    // 音频队列
    audioQueue: [],
    // 音频处理状态
    audioProcessing: {
      isProcessing: false,
      lastActivityTime: Date.now(),
      timeoutId: null,
    },
  }),
  
  getters: {
    // 获取最新的AI消息
    latestAIMessage: (state) => {
      return state.messages.findLast(msg => msg.sender === 'ai')
    },
    
    // 获取最新的用户消息
    latestUserMessage: (state) => {
      return state.messages.findLast(msg => msg.sender === 'user')
    },
    
    // 获取消息数量
    messageCount: (state) => {
      return state.messages.length
    },
  },
  
  actions: {
    // 添加消息
    addMessage(sender, text) {
      const message = {
        sender,
        text,
        timestamp: new Date().toLocaleTimeString('zh-CN'),
      }
      this.messages.push(message)
    },
    
    // 更新当前AI流式回复
    updateCurrentAIMessage(text) {
      this.currentAIMessage = text
    },
    
    // 完成AI回复
    completeAIMessage() {
      if (this.currentAIMessage) {
        this.addMessage('ai', this.currentAIMessage)
        this.currentAIMessage = ''
      }
    },
    
    // 设置状态
    setStatus(status) {
      this.status = status
    },
    
    // 设置错误
    setError(message) {
      this.status = 'error'
      this.errorMessage = message
    },
    
    // 清除错误
    clearError() {
      this.status = 'idle'
      this.errorMessage = ''
    },
    
    // 设置连接状态
    setConnected(connected) {
      this.isConnected = connected
      if (connected) {
        this.status = 'connected'
      } else {
        this.status = 'idle'
      }
    },
    
    // 清空聊天记录
    clearMessages() {
      this.messages = []
      this.currentAIMessage = ''
      // 清空音频队列
      this.audioQueue = []
      // 清除音频处理超时
      this.clearAudioProcessingTimeout()
      // 重置音频处理状态
      this.audioProcessing = {
        isProcessing: false,
        lastActivityTime: Date.now(),
        timeoutId: null,
      }
    },
    
    // 处理WebSocket消息
    handleWebSocketMessage(message) {
      try {
        // 更新音频处理活动时间
        this.audioProcessing.lastActivityTime = Date.now()
        
        switch (message.type) {
          case 'status':
            this.setStatus(message.status)
            break
          
          case 'user_text':
            this.addMessage('user', message.text)
            break
          
          case 'ai_text':
            // 只需要调用completeAIMessage()，因为currentAIMessage已经包含了完整的回复
            this.completeAIMessage()
            break
          
          case 'ai_text_chunk':
            this.updateCurrentAIMessage(this.currentAIMessage + message.text)
            break
          
          case 'audio_response':
            // 处理非流式音频响应
            console.log('Received audio response:', message.audio_data ? message.audio_data.length : 0)
            this.processAudioResponse(message.audio_data)
            break
          
          case 'audio_chunk':
            // 处理流式音频响应
            console.log('Received audio chunk:', message.audio_data ? message.audio_data.length : 0)
            this.audioQueue.push(message.audio_data)
            // 清除之前的超时
            this.clearAudioProcessingTimeout()
            // 设置新的超时
            this.setAudioProcessingTimeout()
            break
          
          case 'audio_complete':
            // 处理音频流完成
            console.log('Audio stream complete, playing...', message.chunk_count ? `received ${message.chunk_count} chunks` : '')
            // 清除超时
            this.clearAudioProcessingTimeout()
            this.processAudioQueue()
            break
          
          case 'error':
            this.setError(message.message)
            break
        }
      } catch (error) {
        console.error('Error handling WebSocket message:', error)
        this.setError('处理消息失败')
      }
    },
    
    // 设置音频处理超时
    setAudioProcessingTimeout() {
      // 清除之前的超时
      this.clearAudioProcessingTimeout()
      
      // 设置新的超时（15秒）
      this.audioProcessing.timeoutId = setTimeout(() => {
        const elapsed = Date.now() - this.audioProcessing.lastActivityTime
        if (elapsed > 15000 && this.audioQueue.length > 0) {
          console.warn('Audio processing timeout, forcing processAudioQueue')
          this.processAudioQueue()
        }
      }, 15000)
    },
    
    // 清除音频处理超时
    clearAudioProcessingTimeout() {
      if (this.audioProcessing.timeoutId) {
        clearTimeout(this.audioProcessing.timeoutId)
        this.audioProcessing.timeoutId = null
      }
    },
    
    // 处理音频响应
    async processAudioResponse(audioData) {
      try {
        console.log('Processing audio response...')
        this.setStatus('playing')
        
        // 延迟导入useAudio以避免循环依赖
        const useAudioFn = await getUseAudio()
        const { queueAudio } = useAudioFn()
        
        // 解码base64音频数据
        const audioBuffer = await this.decodeAudioData(audioData)
        
        // 添加到音频队列并播放
        queueAudio(audioBuffer)
        
        this.setStatus('idle')
        console.log('Audio response processed successfully')
      } catch (error) {
        console.error('Error processing audio response:', error)
        this.setError('处理音频响应失败')
      }
    },
    
    // 处理音频队列
    async processAudioQueue() {
      console.log('Starting processAudioQueue, current queue length:', this.audioQueue.length)
      console.log('Current audioProcessing state:', this.audioProcessing)
      
      try {
        // 检查是否正在处理
        if (this.audioProcessing.isProcessing) {
          console.warn('Audio queue processing already in progress, skipping')
          return
        }
        
        const totalChunks = this.audioQueue.length
        console.log('Processing audio queue with', totalChunks, 'chunks')
        this.setStatus('playing')
        this.audioProcessing.isProcessing = true
        this.audioProcessing.lastActivityTime = Date.now()
        console.log('Set audioProcessing.isProcessing to true')
        
        if (totalChunks === 0) {
          console.warn('Audio queue is empty, nothing to process')
          this.setStatus('idle')
          this.audioProcessing.isProcessing = false
          console.log('Set audioProcessing.isProcessing to false (empty queue)')
          return
        }
        
        // 延迟导入useAudio以避免循环依赖
        console.log('Importing useAudio...')
        const useAudioFn = await getUseAudio()
        const { queueAudio } = useAudioFn()
        console.log('useAudio imported successfully')
        
        // 解码所有音频数据并提取PCM数据
        console.log('Decoding all audio chunks...')
        const pcmDataArray = []
        let wavHeader = null
        let sampleRate = 16000 // 默认采样率
        
        for (let i = 0; i < totalChunks; i++) {
          try {
            const audioData = this.audioQueue[i]
            console.log(`Processing audio chunk ${i+1}/${totalChunks}:`, audioData ? audioData.length : 0)
            
            // 解码base64音频数据
            console.log('Decoding base64 audio data...')
            const audioBuffer = await this.decodeAudioData(audioData)
            console.log('Decoded audio buffer length:', audioBuffer.byteLength)
            
            if (audioBuffer.byteLength < 44) {
              console.error(`Audio chunk ${i+1} is too small (less than 44 bytes), skipping`)
              continue
            }
            
            // 读取WAV头部信息
            const headerView = new DataView(audioBuffer, 0, 44)
            const riffHeader = String.fromCharCode.apply(null, new Uint8Array(audioBuffer, 0, 4))
            const waveHeader = String.fromCharCode.apply(null, new Uint8Array(audioBuffer, 8, 4))
            
            if (riffHeader !== 'RIFF' || waveHeader !== 'WAVE') {
              console.error(`Audio chunk ${i+1} is not a valid WAV file, skipping`)
              continue
            }
            
            // 保存第一个音频块的WAV头部
            if (!wavHeader) {
              wavHeader = new Uint8Array(audioBuffer, 0, 44)
              console.log('Saved WAV header from first chunk')
              
              // 读取采样率
              sampleRate = headerView.getUint32(24, true)
              console.log('Sample rate:', sampleRate)
            }
            
            // 提取PCM数据（跳过44字节的WAV头部）
            const pcmData = new Uint8Array(audioBuffer, 44)
            pcmDataArray.push(pcmData)
            console.log(`Extracted PCM data from chunk ${i+1}, length:`, pcmData.length)
            
            this.audioProcessing.lastActivityTime = Date.now()
            console.log('Updated lastActivityTime:', this.audioProcessing.lastActivityTime)
          } catch (chunkError) {
            console.error(`Error processing audio chunk ${i+1}:`, chunkError)
            // 继续处理下一个音频块
            console.log('Continuing with next audio chunk...')
            continue
          }
        }
        
        // 检查是否有有效的音频数据
        if (!wavHeader || pcmDataArray.length === 0) {
          console.error('No valid audio data to play')
          this.audioQueue = []
          this.setStatus('idle')
          this.audioProcessing.isProcessing = false
          console.log('Set audioProcessing.isProcessing to false (no valid data)')
          return
        }
        
        // 计算总PCM数据长度
        let totalPcmLength = 0
        for (const pcmData of pcmDataArray) {
          totalPcmLength += pcmData.length
        }
        console.log('Total PCM data length:', totalPcmLength)
        
        // 创建新的合并音频缓冲区
        const totalLength = 44 + totalPcmLength // 44字节WAV头部 + PCM数据
        const mergedBuffer = new ArrayBuffer(totalLength)
        const mergedView = new Uint8Array(mergedBuffer)
        
        // 复制WAV头部
        mergedView.set(wavHeader, 0)
        console.log('Copied WAV header to merged buffer')
        
        // 更新WAV头部中的数据长度
        const dataView = new DataView(mergedBuffer)
        dataView.setUint32(4, 36 + totalPcmLength, true) // RIFF块大小
        dataView.setUint32(40, totalPcmLength, true) // 数据块大小
        console.log('Updated WAV header with new data lengths')
        console.log('RIFF chunk size:', dataView.getUint32(4, true))
        console.log('Data chunk size:', dataView.getUint32(40, true))
        
        // 复制所有PCM数据
        let offset = 44
        for (const pcmData of pcmDataArray) {
          mergedView.set(pcmData, offset)
          offset += pcmData.length
          console.log('Copied PCM data, current offset:', offset)
        }
        console.log('All PCM data copied, final offset:', offset)
        
        // 播放合并后的音频
        console.log('Playing merged audio, total length:', mergedBuffer.byteLength)
        queueAudio(mergedBuffer)
        console.log('Merged audio queued successfully')
        
        // 清空音频队列
        this.audioQueue = []
        console.log('Cleared audio queue')
        
        this.setStatus('idle')
        this.audioProcessing.isProcessing = false
        console.log('Set audioProcessing.isProcessing to false (completed)')
        console.log(`Audio queue processed successfully, merged ${pcmDataArray.length}/${totalChunks} chunks`)
      } catch (error) {
        console.error('Error processing audio queue:', error)
        this.setError('处理音频队列失败')
        this.audioQueue = []
        this.audioProcessing.isProcessing = false
        console.log('Set audioProcessing.isProcessing to false (error)')
      } finally {
        // 确保状态被重置
        if (this.audioProcessing.isProcessing) {
          this.audioProcessing.isProcessing = false
          console.log('Set audioProcessing.isProcessing to false (finally)')
        }
        console.log('processAudioQueue completed, final audioProcessing state:', this.audioProcessing)
      }
    },
    
    // 解码base64音频数据
    decodeAudioData(base64Data) {
      return new Promise((resolve, reject) => {
        try {
          console.log('Decoding base64 audio data, length:', base64Data ? base64Data.length : 0)
          
          if (!base64Data || typeof base64Data !== 'string') {
            throw new Error('Invalid base64 data')
          }
          
          // 解码base64数据
          const binaryString = atob(base64Data)
          console.log('Base64 decoded successfully, binary string length:', binaryString.length)
          
          const len = binaryString.length
          const bytes = new Uint8Array(len)
          
          for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i)
          }
          
          // 创建ArrayBuffer
          const arrayBuffer = bytes.buffer
          console.log('Created ArrayBuffer, length:', arrayBuffer.byteLength)
          resolve(arrayBuffer)
        } catch (error) {
          console.error('Error decoding audio data:', error)
          reject(error)
        }
      })
    },
  },
})