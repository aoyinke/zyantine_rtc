import { defineStore } from 'pinia'

export const useAudioStore = defineStore('audio', {
  state: () => ({
    // 音频上下文
    audioContext: null,
    // 媒体流
    mediaStream: null,
    // 脚本处理器
    scriptProcessor: null,
    // 音频数据
    audioChunks: [],
    // 录音状态
    isRecording: false,
    // 播放状态
    isPlaying: false,
    // 音频队列
    audioQueue: [],
    // 当前音频源
    currentSource: null,
    // 音量
    volume: 1.0,
    // 音频配置
    config: {
      sampleRate: 16000,
      bufferSize: 4096,
      channels: 1,
    },
  }),
  
  getters: {
    // 获取音频数据大小
    audioDataSize: (state) => {
      return state.audioChunks.reduce((total, chunk) => total + chunk.length, 0)
    },
    
    // 获取音频队列大小
    audioQueueSize: (state) => {
      return state.audioQueue.length
    },
    
    // 是否有音频数据
    hasAudioData: (state) => {
      return state.audioChunks.length > 0
    },
    
    // 是否有音频队列
    hasAudioQueue: (state) => {
      return state.audioQueue.length > 0
    },
  },
  
  actions: {
    // 设置音频上下文
    setAudioContext(context) {
      this.audioContext = context
    },
    
    // 设置媒体流
    setMediaStream(stream) {
      this.mediaStream = stream
    },
    
    // 设置脚本处理器
    setScriptProcessor(processor) {
      this.scriptProcessor = processor
    },
    
    // 添加音频数据
    addAudioChunk(chunk) {
      this.audioChunks.push(chunk)
    },
    
    // 清空音频数据
    clearAudioChunks() {
      this.audioChunks = []
    },
    
    // 设置录音状态
    setRecording(isRecording) {
      this.isRecording = isRecording
    },
    
    // 设置播放状态
    setPlaying(isPlaying) {
      this.isPlaying = isPlaying
    },
    
    // 添加音频到队列
    addAudioToQueue(arrayBuffer) {
      this.audioQueue.push(arrayBuffer)
    },
    
    // 从队列获取音频
    getAudioFromQueue() {
      return this.audioQueue.shift()
    },
    
    // 清空音频队列
    clearAudioQueue() {
      this.audioQueue = []
    },
    
    // 设置当前音频源
    setCurrentSource(source) {
      this.currentSource = source
    },
    
    // 设置音量
    setVolume(volume) {
      this.volume = Math.max(0, Math.min(1, volume))
    },
    
    // 更新音频配置
    updateConfig(config) {
      this.config = { ...this.config, ...config }
    },
    
    // 停止所有音频
    stopAllAudio() {
      // 停止当前音频源
      if (this.currentSource) {
        try {
          this.currentSource.stop()
        } catch (e) {
          // 忽略已经停止的错误
        }
        this.currentSource = null
      }
      
      // 停止媒体流
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop())
        this.mediaStream = null
      }
      
      // 断开脚本处理器
      if (this.scriptProcessor) {
        this.scriptProcessor.disconnect()
        this.scriptProcessor = null
      }
      
      // 关闭音频上下文
      if (this.audioContext) {
        this.audioContext.close()
        this.audioContext = null
      }
      
      // 重置状态
      this.isRecording = false
      this.isPlaying = false
      this.clearAudioChunks()
      this.clearAudioQueue()
    },
  },
})