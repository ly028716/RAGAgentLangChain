import { describe, it, expect, vi, beforeEach } from 'vitest'
import { userApi } from '@/api/user'
import request from '@/api/index'

// Mock the request module
vi.mock('@/api/index', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('User Deletion API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('requestDeletion', () => {
    it('should send deletion request with password and reason', async () => {
      const mockResponse = {
        success: true,
        message: '账号注销请求已提交',
        requested_at: '2026-01-12T10:00:00',
        scheduled_at: '2026-01-19T10:00:00',
        cooldown_days: 7
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await userApi.requestDeletion({
        password: 'testpassword123',
        reason: '测试注销'
      })

      expect(request.post).toHaveBeenCalledWith('/user/deletion/request', {
        password: 'testpassword123',
        reason: '测试注销'
      })
      expect(result).toEqual(mockResponse)
    })

    it('should send deletion request without reason', async () => {
      const mockResponse = {
        success: true,
        message: '账号注销请求已提交',
        cooldown_days: 7
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      await userApi.requestDeletion({ password: 'testpassword123' })

      expect(request.post).toHaveBeenCalledWith('/user/deletion/request', {
        password: 'testpassword123'
      })
    })
  })

  describe('cancelDeletion', () => {
    it('should send cancel deletion request', async () => {
      const mockResponse = {
        success: true,
        message: '注销请求已取消'
      }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await userApi.cancelDeletion()

      expect(request.post).toHaveBeenCalledWith('/user/deletion/cancel')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getDeletionStatus', () => {
    it('should get deletion status when no request exists', async () => {
      const mockResponse = {
        has_deletion_request: false,
        message: '您的账号状态正常'
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await userApi.getDeletionStatus()

      expect(request.get).toHaveBeenCalledWith('/user/deletion/status')
      expect(result.has_deletion_request).toBe(false)
    })

    it('should get deletion status when request exists', async () => {
      const mockResponse = {
        has_deletion_request: true,
        requested_at: '2026-01-12T10:00:00',
        scheduled_at: '2026-01-19T10:00:00',
        reason: '测试注销',
        remaining_days: 5,
        remaining_hours: 12,
        can_cancel: true,
        message: '您的账号将于 5 天 12 小时后被删除'
      }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      const result = await userApi.getDeletionStatus()

      expect(result.has_deletion_request).toBe(true)
      expect(result.remaining_days).toBe(5)
      expect(result.can_cancel).toBe(true)
    })
  })
})
