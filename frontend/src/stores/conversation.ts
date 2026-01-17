import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { conversationApi } from '@/api/conversation'
import type { Conversation, Message } from '@/types'

export const useConversationStore = defineStore('conversation', () => {
  // State
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<number | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const totalConversations = ref(0)

  // Getters
  const currentConversation = computed(() =>
    conversations.value.find(c => c.id === currentConversationId.value)
  )

  const sortedConversations = computed(() =>
    [...conversations.value].sort((a, b) => 
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  )

  // Actions
  async function fetchConversations(page = 1): Promise<void> {
    isLoading.value = true
    try {
      const response = await conversationApi.getList(page)
      if (page === 1) {
        conversations.value = response.items
      } else {
        conversations.value.push(...response.items)
      }
      totalConversations.value = response.total
    } catch (error) {
      console.error('获取对话列表失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function createConversation(title?: string): Promise<Conversation | null> {
    try {
      const conversation = await conversationApi.create(title)
      conversations.value.unshift(conversation)
      return conversation
    } catch (error) {
      console.error('创建对话失败:', error)
      return null
    }
  }

  async function deleteConversation(id: number): Promise<boolean> {
    try {
      await conversationApi.delete(id)
      conversations.value = conversations.value.filter(c => c.id !== id)
      if (currentConversationId.value === id) {
        currentConversationId.value = null
        messages.value = []
      }
      return true
    } catch (error) {
      console.error('删除对话失败:', error)
      return false
    }
  }

  async function updateConversationTitle(id: number, title: string): Promise<boolean> {
    try {
      const updated = await conversationApi.update(id, title)
      const index = conversations.value.findIndex(c => c.id === id)
      if (index !== -1) {
        conversations.value[index] = updated
      }
      return true
    } catch (error) {
      console.error('更新对话标题失败:', error)
      return false
    }
  }

  async function fetchMessages(conversationId: number): Promise<void> {
    isLoading.value = true
    try {
      const response = await conversationApi.getMessages(conversationId)
      // 按创建时间正序排列 (旧消息在前，新消息在后)
      messages.value = response.items.sort((a, b) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      )
    } catch (error) {
      console.error('获取消息列表失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  function setCurrentConversation(id: number | null) {
    currentConversationId.value = id
    if (!id) {
      messages.value = []
    }
  }

  function addUserMessage(content: string) {
    messages.value.push({
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString()
    })
  }

  function startStreaming() {
    isStreaming.value = true
    streamingContent.value = ''
  }

  function appendStreamContent(content: string) {
    streamingContent.value += content
  }

  function finalizeStreamMessage() {
    if (streamingContent.value) {
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: streamingContent.value,
        created_at: new Date().toISOString()
      })
    }
    streamingContent.value = ''
    isStreaming.value = false
  }

  function clearMessages() {
    messages.value = []
    streamingContent.value = ''
    isStreaming.value = false
  }

  return {
    conversations,
    currentConversationId,
    messages,
    isLoading,
    isStreaming,
    streamingContent,
    totalConversations,
    currentConversation,
    sortedConversations,
    fetchConversations,
    createConversation,
    deleteConversation,
    updateConversationTitle,
    fetchMessages,
    setCurrentConversation,
    addUserMessage,
    startStreaming,
    appendStreamContent,
    finalizeStreamMessage,
    clearMessages
  }
})
