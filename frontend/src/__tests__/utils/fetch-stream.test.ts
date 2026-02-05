/**
 * fetch-stream 工具函数测试
 * 测试范围：流式请求、Token 注入、自动刷新 Token、错误处理
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { fetchStream } from '@/utils/fetch-stream'
import { storage } from '@/utils/storage'
import { useAuthStore } from '@/stores/auth'
import { setActivePinia, createPinia } from 'pinia'

// Mock storage
vi.mock('@/utils/storage', () => ({
  storage: {
    getToken: vi.fn(() => 'test-token'),
    setToken: vi.fn(),
    removeToken: vi.fn(),
    getRefreshToken: vi.fn(() => 'refresh-token'),
    setRefreshToken: vi.fn(),
    removeRefreshToken: vi.fn(),
    getUser: vi.fn(),
    setUser: vi.fn(),
    removeUser: vi.fn(),
    clearAuth: vi.fn()
  }
}))

// Mock router
vi.mock('@/router', () => ({
  default: {
    push: vi.fn()
  }
}))

describe('fetchStream', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    
    // Mock fetch
    mockFetch = vi.fn()
    global.fetch = mockFetch as any
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('应该正确发起请求并处理流式响应', async () => {
    const mockStream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('Hello'))
        controller.enqueue(new TextEncoder().encode(' World'))
        controller.close()
      }
    })

    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      body: mockStream,
      headers: new Headers()
    })

    const onMessage = vi.fn()
    const onDone = vi.fn()

    await fetchStream('/test', { onMessage, onDone })

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/test'),
      expect.objectContaining({
        headers: expect.any(Headers)
      })
    )
    
    // 验证 Authorization header
    const callArgs = mockFetch.mock.calls[0]
    const headers = callArgs[1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer test-token')

    expect(onMessage).toHaveBeenCalledWith('Hello')
    expect(onMessage).toHaveBeenCalledWith(' World')
    expect(onDone).toHaveBeenCalled()
  })

  it('应该处理 401 错误并尝试刷新 Token', async () => {
    // 第一次请求返回 401
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: () => Promise.resolve('Unauthorized'),
      headers: new Headers()
    })

    // 第二次请求（重试）返回成功
    const mockStream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('Success'))
        controller.close()
      }
    })
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      body: mockStream,
      headers: new Headers()
    })

    // Mock auth store action
    const authStore = useAuthStore()
    // 模拟刷新成功
    authStore.refreshTokenAction = vi.fn().mockResolvedValue(true)
    
    // 模拟获取新 Token
    vi.mocked(storage.getToken).mockReturnValue('new-token')

    const onMessage = vi.fn()

    await fetchStream('/test', { onMessage })

    expect(authStore.refreshTokenAction).toHaveBeenCalled()
    expect(mockFetch).toHaveBeenCalledTimes(2)
    
    // 验证第二次请求使用了新 Token
    const secondCallArgs = mockFetch.mock.calls[1]
    const headers = secondCallArgs[1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer new-token')
    
    expect(onMessage).toHaveBeenCalledWith('Success')
  })

  it('刷新 Token 失败时应跳转登录', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: () => Promise.resolve('Unauthorized'),
      headers: new Headers()
    })

    const authStore = useAuthStore()
    authStore.refreshTokenAction = vi.fn().mockResolvedValue(false)
    
    // Mock router
    const router = await import('@/router')
    
    // 我们无法直接 spy authStore.clearAuth，因为它是一个 action
    // 但是我们可以 spy storage.clearAuth，因为它被 authStore.clearAuth 调用
    await expect(fetchStream('/test')).rejects.toThrow('认证失效，请重新登录')
    
    expect(storage.clearAuth).toHaveBeenCalled()
    expect(router.default.push).toHaveBeenCalledWith('/login')
  })

  it('应该处理非 401 错误', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve('Server Error'),
      headers: new Headers()
    })

    await expect(fetchStream('/test')).rejects.toThrow('HTTP error! status: 500')
  })

  it('应该处理 AbortError', async () => {
    const error = new Error('Aborted')
    error.name = 'AbortError'
    mockFetch.mockRejectedValue(error)

    const onDone = vi.fn()
    const onError = vi.fn()

    await fetchStream('/test', { onDone, onError })

    expect(onDone).toHaveBeenCalled()
    expect(onError).not.toHaveBeenCalled()
  })
})
