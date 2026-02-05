import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChat } from '@/composables/useChat'
import { useConversationStore } from '@/stores/conversation'

// Mock fetchStream
vi.mock('@/utils/fetch-stream', () => ({
  fetchStream: vi.fn()
}))

import { fetchStream } from '@/utils/fetch-stream'

describe('useChat Composable', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('sendMessage', () => {
    it('应该正确发送消息并处理流式响应', async () => {
      // 模拟 fetchStream 行为
      vi.mocked(fetchStream).mockImplementation(async (url, options) => {
        // 模拟接收数据
        if (options?.onMessage) {
          options.onMessage('data: {"content":"Hello"}\n\n')
          options.onMessage('data: {"content":" World"}\n\n')
          options.onMessage('data: {"type":"done"}\n\n')
        }
        return Promise.resolve()
      })

      const { sendMessage } = useChat()
      const store = useConversationStore()
      
      const result = await sendMessage('测试消息', 1)
      
      expect(result.success).toBe(true)
      expect(fetchStream).toHaveBeenCalledWith('/chat/stream', expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('测试消息')
      }))
      
      // 验证用户消息被添加
      expect(store.messages.some(m => m.role === 'user' && m.content === '测试消息')).toBe(true)
    })

    it('应该处理新对话ID', async () => {
      vi.mocked(fetchStream).mockImplementation(async (url, options) => {
        if (options?.onMessage) {
          options.onMessage('data: {"conversation_id":123,"content":"Hi"}\n\n')
          options.onMessage('data: {"type":"done","conversation_id":123}\n\n')
        }
        return Promise.resolve()
      })

      const { sendMessage } = useChat()
      
      const result = await sendMessage('新对话', null)
      
      expect(result.conversationId).toBe(123)
    })

    it('错误应返回失败', async () => {
      vi.mocked(fetchStream).mockRejectedValue(new Error('Network error'))

      const { sendMessage } = useChat()
      
      const result = await sendMessage('测试', 1)
      
      expect(result.success).toBe(false)
    })

    it('应该处理流式错误响应', async () => {
      vi.mocked(fetchStream).mockImplementation(async (url, options) => {
        if (options?.onMessage) {
          options.onMessage('data: {"type":"error","error":"Server error"}\n\n')
        }
        return Promise.resolve()
      })

      const { sendMessage } = useChat()
      
      const result = await sendMessage('测试', 1)
      
      // 由于 useChat 内部 catch 了错误，success 为 false (因为 throw new Error(parsed.error))
      expect(result.success).toBe(false)
    })

    it('应该处理被拆分的 SSE 分片', async () => {
      vi.mocked(fetchStream).mockImplementation(async (url, options) => {
        if (options?.onMessage) {
          options.onMessage('da')
          options.onMessage('ta: {"type":"token","content":"Hel')
          options.onMessage('lo"}\n')
          options.onMessage('\n')
          options.onMessage('data: {"type":"done"}\n\n')
        }
        return Promise.resolve()
      })

      const { sendMessage } = useChat()
      const store = useConversationStore()

      const result = await sendMessage('测试', 1)

      expect(result.success).toBe(true)
      expect(store.messages.some(m => m.role === 'assistant' && m.content.includes('Hello'))).toBe(true)
    })
  })

  describe('stopStreaming', () => {
    it('应该能够取消正在进行的请求', async () => {
      let abortSignal: AbortSignal | undefined
      
      vi.mocked(fetchStream).mockImplementation(async (url, options) => {
        abortSignal = options?.signal || undefined
        return new Promise((_, reject) => {
          if (abortSignal) {
            abortSignal.addEventListener('abort', () => {
              const error = new Error('Aborted')
              error.name = 'AbortError'
              reject(error)
            })
          }
        })
      })

      const { sendMessage, stopStreaming } = useChat()
      
      // 开始发送（不等待完成）
      const sendPromise = sendMessage('测试', 1)
      
      // 立即停止
      stopStreaming()
      
      const result = await sendPromise
      
      // AbortError 应该被视为成功（用户主动取消）
      expect(result.success).toBe(true)
    })
  })

  describe('请求参数', () => {
    it('应该正确传递配置参数', async () => {
      vi.mocked(fetchStream).mockResolvedValue()

      const { sendMessage } = useChat()
      
      await sendMessage('测试', 1, { temperature: 0.8, max_tokens: 1000 })
      
      const callArgs = vi.mocked(fetchStream).mock.calls[0]
      // fetchStream 第二个参数是 options
      const body = callArgs[1]?.body ? JSON.parse(callArgs[1].body as string) : {}
      
      expect(body.config).toEqual({ temperature: 0.8, max_tokens: 1000 })
    })

    it('无配置时应传递空对象', async () => {
      vi.mocked(fetchStream).mockResolvedValue()

      const { sendMessage } = useChat()
      
      await sendMessage('测试', 1)
      
      const callArgs = vi.mocked(fetchStream).mock.calls[0]
      const options = callArgs[1]
      const body = options?.body ? JSON.parse(options.body as string) : {}
      
      expect(body.config).toEqual({})
    })
  })
})
