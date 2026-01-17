/**
 * Storage 工具函数测试
 * 测试范围：Token存储、用户信息存储、认证清除
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { storage } from '@/utils/storage'

describe('Storage 工具函数', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Token 操作', () => {
    it('应该正确存储和获取 access_token', () => {
      const token = 'test-access-token-123'
      
      storage.setToken(token)
      
      expect(storage.getToken()).toBe(token)
      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', token)
    })

    it('应该正确删除 access_token', () => {
      storage.setToken('test-token')
      storage.removeToken()
      
      expect(storage.getToken()).toBeNull()
      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
    })

    it('应该正确存储和获取 refresh_token', () => {
      const refreshToken = 'test-refresh-token-456'
      
      storage.setRefreshToken(refreshToken)
      
      expect(storage.getRefreshToken()).toBe(refreshToken)
      expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', refreshToken)
    })

    it('应该正确删除 refresh_token', () => {
      storage.setRefreshToken('test-refresh')
      storage.removeRefreshToken()
      
      expect(storage.getRefreshToken()).toBeNull()
    })

    it('未设置 token 时应返回 null', () => {
      expect(storage.getToken()).toBeNull()
      expect(storage.getRefreshToken()).toBeNull()
    })
  })

  describe('用户信息操作', () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      avatar: '/avatar.png',
      created_at: '2026-01-01T00:00:00Z',
      is_active: true
    }

    it('应该正确存储和获取用户信息', () => {
      storage.setUser(mockUser)
      
      const user = storage.getUser()
      
      expect(user).toEqual(mockUser)
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'user_info',
        JSON.stringify(mockUser)
      )
    })

    it('应该正确删除用户信息', () => {
      storage.setUser(mockUser)
      storage.removeUser()
      
      expect(storage.getUser()).toBeNull()
    })

    it('未设置用户信息时应返回 null', () => {
      expect(storage.getUser()).toBeNull()
    })

    it('JSON 解析失败时应返回 null 并清除无效数据', () => {
      // 模拟存储无效 JSON
      localStorage.setItem('user_info', 'invalid-json{')
      
      const user = storage.getUser()
      
      expect(user).toBeNull()
      expect(localStorage.removeItem).toHaveBeenCalledWith('user_info')
    })
  })

  describe('清除认证信息', () => {
    it('应该清除所有认证相关数据', () => {
      storage.setToken('access-token')
      storage.setRefreshToken('refresh-token')
      storage.setUser({ id: 1, username: 'test' })
      
      storage.clearAuth()
      
      expect(storage.getToken()).toBeNull()
      expect(storage.getRefreshToken()).toBeNull()
      expect(storage.getUser()).toBeNull()
    })
  })
})
