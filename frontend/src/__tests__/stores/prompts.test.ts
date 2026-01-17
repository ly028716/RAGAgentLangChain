import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePromptsStore } from '@/stores/prompts'
import { promptsApi } from '@/api/prompts'
import type { SystemPrompt } from '@/types'

// Mock API
vi.mock('@/api/prompts', () => ({
  promptsApi: {
    getList: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    setDefault: vi.fn()
  }
}))

describe('Prompts Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mockPrompt: SystemPrompt = {
    id: 1,
    user_id: 1,
    name: '测试提示词',
    content: '测试内容',
    category: 'general',
    is_default: false,
    is_system: false,
    created_at: '2026-01-11T00:00:00Z',
    updated_at: '2026-01-11T00:00:00Z'
  }

  const mockSystemPrompt: SystemPrompt = {
    id: 2,
    name: '系统提示词',
    content: '系统内容',
    category: 'general',
    is_default: true,
    is_system: true,
    created_at: '2026-01-11T00:00:00Z',
    updated_at: '2026-01-11T00:00:00Z'
  }

  describe('fetchPrompts', () => {
    it('should fetch prompts successfully', async () => {
      const mockResponse = {
        items: [mockPrompt, mockSystemPrompt],
        total: 2
      }
      vi.mocked(promptsApi.getList).mockResolvedValue(mockResponse)

      const store = usePromptsStore()
      await store.fetchPrompts()

      expect(promptsApi.getList).toHaveBeenCalledWith(0, 50, undefined)
      expect(store.prompts).toEqual(mockResponse.items)
      expect(store.total).toBe(2)
      expect(store.loading).toBe(false)
    })

    it('should handle fetch error', async () => {
      const error = new Error('Network error')
      vi.mocked(promptsApi.getList).mockRejectedValue(error)

      const store = usePromptsStore()
      await expect(store.fetchPrompts()).rejects.toThrow()
      expect(store.error).toBeTruthy()
    })
  })

  describe('createPrompt', () => {
    it('should create prompt successfully', async () => {
      vi.mocked(promptsApi.create).mockResolvedValue(mockPrompt)

      const store = usePromptsStore()
      const result = await store.createPrompt({
        name: '测试提示词',
        content: '测试内容',
        category: 'general'
      })

      expect(result).toEqual(mockPrompt)
      expect(store.prompts).toHaveLength(1)
      expect(store.prompts[0].id).toBe(mockPrompt.id)
      expect(store.total).toBe(1)
    })
  })

  describe('updatePrompt', () => {
    it('should update prompt successfully', async () => {
      const updatedPrompt = { ...mockPrompt, name: '更新后的名称' }
      vi.mocked(promptsApi.update).mockResolvedValue(updatedPrompt)

      const store = usePromptsStore()
      store.prompts = [mockPrompt]
      
      const result = await store.updatePrompt(1, { name: '更新后的名称' })

      expect(result.name).toBe('更新后的名称')
      expect(store.prompts[0].name).toBe('更新后的名称')
    })
  })

  describe('deletePrompt', () => {
    it('should delete prompt successfully', async () => {
      vi.mocked(promptsApi.delete).mockResolvedValue(undefined)

      const store = usePromptsStore()
      store.prompts = [mockPrompt]
      store.total = 1

      await store.deletePrompt(1)

      expect(store.prompts).toHaveLength(0)
      expect(store.total).toBe(0)
    })
  })

  describe('setDefaultPrompt', () => {
    it('should set default prompt successfully', async () => {
      vi.mocked(promptsApi.setDefault).mockResolvedValue({ success: true, message: '设置成功' })

      const store = usePromptsStore()
      store.prompts = [mockPrompt, mockSystemPrompt]

      await store.setDefaultPrompt(1)

      expect(store.prompts.find(p => p.id === 1)?.is_default).toBe(true)
      expect(store.prompts.find(p => p.id === 2)?.is_default).toBe(false)
    })
  })

  describe('computed properties', () => {
    it('should filter system prompts', () => {
      const store = usePromptsStore()
      store.prompts = [mockPrompt, mockSystemPrompt]

      expect(store.systemPrompts).toHaveLength(1)
      expect(store.systemPrompts[0].is_system).toBe(true)
    })

    it('should filter user prompts', () => {
      const store = usePromptsStore()
      store.prompts = [mockPrompt, mockSystemPrompt]

      expect(store.userPrompts).toHaveLength(1)
      expect(store.userPrompts[0].is_system).toBe(false)
    })

    it('should get default prompt', () => {
      const store = usePromptsStore()
      store.prompts = [mockPrompt, mockSystemPrompt]

      // mockSystemPrompt has is_default: true
      expect(store.defaultPrompt?.is_default).toBe(true)
    })
  })
})
