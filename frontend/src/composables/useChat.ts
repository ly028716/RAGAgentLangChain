import { ref } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import { storage } from '@/utils/storage'
import type { ChatConfig } from '@/types'

export function useChat() {
  const conversationStore = useConversationStore()
  const abortController = ref<AbortController | null>(null)

  async function sendMessage(
    content: string,
    conversationId: number | null,
    config?: ChatConfig
  ): Promise<{ conversationId: number | null; success: boolean }> {
    // 添加用户消息
    conversationStore.addUserMessage(content)
    conversationStore.startStreaming()

    abortController.value = new AbortController()

    try {
      const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${storage.getToken()}`
        },
        body: JSON.stringify({
          conversation_id: conversationId,  // 可以为 null，后端会自动创建新对话
          content,
          config: config || {}
        }),
        signal: abortController.value.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let newConversationId = conversationId

      while (reader) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            
            if (data === '[DONE]') {
              conversationStore.finalizeStreamMessage()
              return { conversationId: newConversationId, success: true }
            }

            try {
              const parsed = JSON.parse(data)
              
              // 处理新对话ID（后端自动创建对话时返回）
              if (parsed.type === 'conversation' && parsed.conversation_id) {
                newConversationId = parsed.conversation_id
              }
              
              // 处理done事件中的conversation_id
              if (parsed.conversation_id && !newConversationId) {
                newConversationId = parsed.conversation_id
              }
              
              // 处理内容
              if (parsed.content) {
                conversationStore.appendStreamContent(parsed.content)
              }
              
              // 处理错误
              if (parsed.error) {
                throw new Error(parsed.error)
              }
            } catch (e) {
              // 忽略解析错误，可能是不完整的JSON
              if (data && !data.startsWith('{')) {
                conversationStore.appendStreamContent(data)
              }
            }
          }
        }
      }

      conversationStore.finalizeStreamMessage()
      return { conversationId: newConversationId, success: true }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        conversationStore.finalizeStreamMessage()
        return { conversationId, success: true }
      }
      
      console.error('发送消息失败:', error)
      conversationStore.finalizeStreamMessage()
      return { conversationId, success: false }
    } finally {
      abortController.value = null
    }
  }

  function stopStreaming() {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
  }

  return {
    sendMessage,
    stopStreaming
  }
}
