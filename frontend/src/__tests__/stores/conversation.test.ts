/**
 * Conversation Store 测试
 * 测试范围：对话列表、消息管理、流式输出
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useConversationStore } from '@/stores/conversation'
import { conversationApi } from '@/api/conversation'

// Mock API 模块
vi.mock('@/api/conversation', () => ({
  conversationApi: {
    getList: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    update: vi.fn(),
    getMessages: vi.fn()
  }
}))

describe('Conversation Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useConversationStore()
      
      expect(store.conversations).toEqual([])
      expect(store.currentConversationId).toBeNull()
      expect(store.messages).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.isStreaming).toBe(false)
      expect(store.streamingContent).toBe('')
    })
  })

  describe('获取对话列表', () => {
    const mockConversations = {
      items: [
        { id: 1, title: '对话1', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T01:00:00Z' },
        { id: 2, title: '对话2', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T02:00:00Z' }
      ],
      total: 2,
      page: 1,
      page_size: 20
    }

    it('应该正确获取对话列表', async () => {
      vi.mocked(conversationApi.getList).mockResolvedValue(mockConversations)
      
      const store = useConversationStore()
      await store.fetchConversations()
      
      expect(store.conversations).toEqual(mockConversations.items)
      expect(store.totalConversations).toBe(2)
      expect(store.isLoading).toBe(false)
    })

    it('分页加载应追加数据', async () => {
      const page1 = { items: [{ id: 1, title: '对话1' }], total: 2, page: 1, page_size: 1 }
      const page2 = { items: [{ id: 2, title: '对话2' }], total: 2, page: 2, page_size: 1 }
      
      vi.mocked(conversationApi.getList)
        .mockResolvedValueOnce(page1 as any)
        .mockResolvedValueOnce(page2 as any)
      
      const store = useConversationStore()
      await store.fetchConversations(1)
      await store.fetchConversations(2)
      
      expect(store.conversations).toHaveLength(2)
    })

    it('获取失败时应保持空列表', async () => {
      vi.mocked(conversationApi.getList).mockRejectedValue(new Error('Network error'))
      
      const store = useConversationStore()
      await store.fetchConversations()
      
      expect(store.conversations).toEqual([])
      expect(store.isLoading).toBe(false)
    })
  })

  describe('创建对话', () => {
    it('应该正确创建对话并添加到列表', async () => {
      const newConversation = { 
        id: 3, 
        title: '新对话', 
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z'
      }
      vi.mocked(conversationApi.create).mockResolvedValue(newConversation)
      
      const store = useConversationStore()
      const result = await store.createConversation('新对话')
      
      expect(result).toEqual(newConversation)
      expect(store.conversations[0]).toEqual(newConversation)
    })

    it('创建失败应返回 null', async () => {
      vi.mocked(conversationApi.create).mockRejectedValue(new Error('Create failed'))
      
      const store = useConversationStore()
      const result = await store.createConversation()
      
      expect(result).toBeNull()
    })
  })

  describe('删除对话', () => {
    it('应该正确删除对话', async () => {
      vi.mocked(conversationApi.delete).mockResolvedValue({ message: 'Deleted' })
      
      const store = useConversationStore()
      store.conversations = [
        { id: 1, title: '对话1' },
        { id: 2, title: '对话2' }
      ] as any
      
      const result = await store.deleteConversation(1)
      
      expect(result).toBe(true)
      expect(store.conversations).toHaveLength(1)
      expect(store.conversations[0].id).toBe(2)
    })

    it('删除当前对话应清空消息', async () => {
      vi.mocked(conversationApi.delete).mockResolvedValue({ message: 'Deleted' })
      
      const store = useConversationStore()
      store.conversations = [{ id: 1, title: '对话1' }] as any
      store.currentConversationId = 1
      store.messages = [{ id: 1, content: 'test' }] as any
      
      await store.deleteConversation(1)
      
      expect(store.currentConversationId).toBeNull()
      expect(store.messages).toEqual([])
    })

    it('删除失败应返回 false', async () => {
      vi.mocked(conversationApi.delete).mockRejectedValue(new Error('Delete failed'))
      
      const store = useConversationStore()
      store.conversations = [{ id: 1, title: '对话1' }] as any
      
      const result = await store.deleteConversation(1)
      
      expect(result).toBe(false)
      expect(store.conversations).toHaveLength(1)
    })
  })

  describe('更新对话标题', () => {
    it('应该正确更新对话标题', async () => {
      const updatedConversation = { id: 1, title: '新标题', updated_at: '2026-01-01T01:00:00Z' }
      vi.mocked(conversationApi.update).mockResolvedValue(updatedConversation as any)
      
      const store = useConversationStore()
      store.conversations = [{ id: 1, title: '旧标题' }] as any
      
      const result = await store.updateConversationTitle(1, '新标题')
      
      expect(result).toBe(true)
      expect(store.conversations[0].title).toBe('新标题')
    })
  })

  describe('消息管理', () => {
    it('应该正确获取消息列表', async () => {
      const mockMessages = {
        items: [
          { id: 2, role: 'assistant', content: '回复', created_at: '2026-01-01T00:01:00Z' },
          { id: 1, role: 'user', content: '你好', created_at: '2026-01-01T00:00:00Z' }
        ],
        total: 2
      }
      vi.mocked(conversationApi.getMessages).mockResolvedValue(mockMessages as any)
      
      const store = useConversationStore()
      await store.fetchMessages(1)
      
      // 消息应该被反转为正序
      expect(store.messages[0].content).toBe('你好')
      expect(store.messages[1].content).toBe('回复')
    })

    it('应该正确添加用户消息', () => {
      const store = useConversationStore()
      
      store.addUserMessage('测试消息')
      
      expect(store.messages).toHaveLength(1)
      expect(store.messages[0].role).toBe('user')
      expect(store.messages[0].content).toBe('测试消息')
    })

    it('应该正确设置当前对话', () => {
      const store = useConversationStore()
      store.messages = [{ id: 1, content: 'test' }] as any
      
      store.setCurrentConversation(5)
      expect(store.currentConversationId).toBe(5)
      
      store.setCurrentConversation(null)
      expect(store.currentConversationId).toBeNull()
      expect(store.messages).toEqual([])
    })
  })

  describe('流式输出', () => {
    it('应该正确开始流式输出', () => {
      const store = useConversationStore()
      
      store.startStreaming()
      
      expect(store.isStreaming).toBe(true)
      expect(store.streamingContent).toBe('')
    })

    it('应该正确追加流式内容', () => {
      const store = useConversationStore()
      store.startStreaming()
      
      store.appendStreamContent('Hello')
      store.appendStreamContent(' World')
      
      expect(store.streamingContent).toBe('Hello World')
    })

    it('应该正确完成流式消息', () => {
      const store = useConversationStore()
      store.startStreaming()
      store.appendStreamContent('完整回复')
      
      store.finalizeStreamMessage()
      
      expect(store.isStreaming).toBe(false)
      expect(store.streamingContent).toBe('')
      expect(store.messages).toHaveLength(1)
      expect(store.messages[0].role).toBe('assistant')
      expect(store.messages[0].content).toBe('完整回复')
    })

    it('空内容不应添加消息', () => {
      const store = useConversationStore()
      store.startStreaming()
      
      store.finalizeStreamMessage()
      
      expect(store.messages).toHaveLength(0)
    })

    it('应该正确清空消息', () => {
      const store = useConversationStore()
      store.messages = [{ id: 1, content: 'test' }] as any
      store.streamingContent = 'streaming...'
      store.isStreaming = true
      
      store.clearMessages()
      
      expect(store.messages).toEqual([])
      expect(store.streamingContent).toBe('')
      expect(store.isStreaming).toBe(false)
    })
  })

  describe('计算属性', () => {
    it('currentConversation 应返回当前对话', () => {
      const store = useConversationStore()
      store.conversations = [
        { id: 1, title: '对话1' },
        { id: 2, title: '对话2' }
      ] as any
      store.currentConversationId = 2
      
      expect(store.currentConversation?.title).toBe('对话2')
    })

    it('sortedConversations 应按更新时间排序', () => {
      const store = useConversationStore()
      store.conversations = [
        { id: 1, title: '旧对话', updated_at: '2026-01-01T00:00:00Z' },
        { id: 2, title: '新对话', updated_at: '2026-01-02T00:00:00Z' }
      ] as any
      
      expect(store.sortedConversations[0].title).toBe('新对话')
    })
  })
})
