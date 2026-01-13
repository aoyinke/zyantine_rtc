import { ref } from 'vue'
import { useChatStore } from '../stores/chat'

let ws = null
let reconnectTimeout = null

const isConnecting = ref(false)

// WebSocket通信组合式API
export function useWebSocket() {
  const chatStore = useChatStore()
  
  // 连接WebSocket
  async function connect() {
    if (isConnecting.value || chatStore.isConnected) {
      return
    }
    
    isConnecting.value = true
    
    try {
      // 连接到后端WebSocket服务
      const wsUrl = 'ws://localhost:8765/ws'
      
      return new Promise((resolve, reject) => {
        ws = new WebSocket(wsUrl)
        
        ws.onopen = () => {
          console.log('WebSocket connected')
          chatStore.setConnected(true)
          
          // 发送连接消息
          ws.send(JSON.stringify({
            type: 'connect',
            client_id: 'web_client',
            room_id: 'web_room'
          }))
          
          resolve()
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            chatStore.handleWebSocketMessage(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
        
        ws.onclose = () => {
          console.log('WebSocket disconnected')
          chatStore.setConnected(false)
          
          // 尝试重连
          if (reconnectTimeout) {
            clearTimeout(reconnectTimeout)
          }
          
          reconnectTimeout = setTimeout(() => {
            if (!chatStore.isConnected) {
              connect()
            }
          }, 3000)
        }
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          chatStore.setError('WebSocket连接错误')
          reject(error)
        }
      })
    } catch (error) {
      console.error('Error connecting WebSocket:', error)
      chatStore.setError('无法连接到服务器')
      throw error
    } finally {
      isConnecting.value = false
    }
  }
  
  // 断开WebSocket
  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
    
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }
    
    chatStore.setConnected(false)
  }
  
  // 发送消息
  function sendMessage(message) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket not connected')
      chatStore.setError('WebSocket未连接')
    }
  }
  
  // 发送音频数据
  function sendAudioData(audioData) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'audio_data',
        audio_data: audioData
      }))
    }
  }
  
  return {
    connect,
    disconnect,
    sendMessage,
    sendAudioData,
    isConnecting,
  }
}