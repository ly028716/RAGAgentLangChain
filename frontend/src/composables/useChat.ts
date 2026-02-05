import { ref } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import { fetchStream } from '@/utils/fetch-stream'
import type { ChatConfig } from '@/types'
import { ElMessage } from 'element-plus'

export function useChat() {
  const conversationStore = useConversationStore()
  const abortController = ref<AbortController | null>(null)

  function handleSseData(
    data: string,
    updateConversationId: (id: number) => void
  ) {
    if (!data) return
    if (data === '[DONE]') {
      return
    }

    if (data.startsWith('{') || data.startsWith('[')) {
      let parsed: any
      try {
        parsed = JSON.parse(data)
      } catch {
        conversationStore.appendStreamContent(data)
        return
      }

      if (parsed?.type === 'conversation' && parsed?.conversation_id) {
        updateConversationId(parsed.conversation_id)
      }

      if (parsed?.type === 'sources' && Array.isArray(parsed?.sources)) {
        conversationStore.setStreamSources(parsed.sources)
      }

      if (parsed?.conversation_id) {
        updateConversationId(parsed.conversation_id)
      }

      if (typeof parsed?.content === 'string' && parsed.content) {
        conversationStore.appendStreamContent(parsed.content)
      }

      if (parsed?.error) {
        throw new Error(parsed.error)
      }

      if (parsed?.type === 'done') {
        return
      }

      return
    }

    conversationStore.appendStreamContent(data)
  }

  async function sendMessage(
    content: string,
    conversationId: number | null,
    config?: ChatConfig
  ): Promise<{ conversationId: number | null; success: boolean }> {
    console.log('[useChat] 开始发送消息:', {
      conversationId,
      contentLength: content.length,
      hasConfig: !!config,
      knowledgeBaseIds: config?.knowledge_base_ids
    })

    // 添加用户消息
    conversationStore.addUserMessage(content)
    conversationStore.startStreaming()

    abortController.value = new AbortController()
    let newConversationId = conversationId

    try {
      let buffer = ''
      await fetchStream('/chat/stream', {
        method: 'POST',
        body: JSON.stringify({
          conversation_id: conversationId,
          content,
          config: config || {},
          knowledge_base_ids: config?.knowledge_base_ids
        }),
        signal: abortController.value.signal,
        timeout: 30000, // 30秒超时
        onMessage: (text) => {
          buffer += text

          const parts = buffer.split(/\r?\n\r?\n/)
          buffer = parts.pop() || ''

          const updateConversationId = (id: number) => {
            newConversationId = id
          }

          for (const part of parts) {
            const lines = part.split(/\r?\n/)
            const dataLines = lines
              .filter(line => line.startsWith('data:'))
              .map(line => line.slice(5).trimStart())

            if (dataLines.length === 0) continue

            const data = dataLines.join('\n').trim()
            if (!data) continue

            try {
              handleSseData(data, updateConversationId)
            } catch (e) {
              console.error('[useChat] 处理SSE数据失败:', e, '数据:', data)
              throw e
            }
          }
        }
      })

      console.log('[useChat] 消息发送成功, conversationId:', newConversationId)
      conversationStore.finalizeStreamMessage()
      return { conversationId: newConversationId, success: true }
    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('[useChat] 消息发送被取消')
        conversationStore.finalizeStreamMessage()
        return { conversationId: newConversationId, success: true }
      }

      console.error('[useChat] 发送消息失败:', {
        name: error?.name,
        message: error?.message,
        stack: error?.stack,
        conversationId: newConversationId
      })

      // 根据错误类型显示不同的提示
      let errorMessage = '发送消息失败'
      if (error?.message) {
        if (error.message.includes('超时')) {
          errorMessage = error.message
        } else if (error.message.includes('网络')) {
          errorMessage = '网络连接失败，请检查网络后重试'
        } else if (error.message.includes('认证')) {
          errorMessage = error.message
        } else {
          errorMessage = error.message
        }
      }

      ElMessage.error(errorMessage)
      conversationStore.finalizeStreamMessage()
      return { conversationId: newConversationId, success: false }
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
