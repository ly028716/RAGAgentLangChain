import { describe, it, expect, vi, beforeEach } from 'vitest'
import { promptsApi } from '@/api/prompts'
import request from '@/api/index'

// Mock request
vi.mock('@/api/index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Prompts API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getList', () => {
    it('should call GET /prompts with correct params', async () => {
      const mockResponse = { items: [], total: 0 }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      await promptsApi.getList(0, 20, 'general')

      expect(request.get).toHaveBeenCalledWith('/prompts', {
        params: { skip: 0, limit: 20, category: 'general' }
      })
    })
  })

  describe('getById', () => {
    it('should call GET /prompts/:id', async () => {
      const mockPrompt = { id: 1, name: 'Test' }
      vi.mocked(request.get).mockResolvedValue(mockPrompt)

      const result = await promptsApi.getById(1)

      expect(request.get).toHaveBeenCalledWith('/prompts/1')
      expect(result).toEqual(mockPrompt)
    })
  })

  describe('create', () => {
    it('should call POST /prompts with data', async () => {
      const createData = { name: 'New Prompt', content: 'Content', category: 'general' }
      const mockResponse = { id: 1, ...createData }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await promptsApi.create(createData)

      expect(request.post).toHaveBeenCalledWith('/prompts', createData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('update', () => {
    it('should call PUT /prompts/:id with data', async () => {
      const updateData = { name: 'Updated Name' }
      const mockResponse = { id: 1, name: 'Updated Name' }
      vi.mocked(request.put).mockResolvedValue(mockResponse)

      const result = await promptsApi.update(1, updateData)

      expect(request.put).toHaveBeenCalledWith('/prompts/1', updateData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('delete', () => {
    it('should call DELETE /prompts/:id', async () => {
      vi.mocked(request.delete).mockResolvedValue(undefined)

      await promptsApi.delete(1)

      expect(request.delete).toHaveBeenCalledWith('/prompts/1')
    })
  })

  describe('setDefault', () => {
    it('should call PUT /prompts/:id/default', async () => {
      const mockResponse = { success: true, message: '设置成功' }
      vi.mocked(request.put).mockResolvedValue(mockResponse)

      const result = await promptsApi.setDefault(1)

      expect(request.put).toHaveBeenCalledWith('/prompts/1/default')
      expect(result).toEqual(mockResponse)
    })
  })
})
