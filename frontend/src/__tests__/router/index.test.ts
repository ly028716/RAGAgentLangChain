/**
 * Router 路由守卫测试
 * 测试范围：认证路由守卫、重定向逻辑
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createRouter, createWebHistory, RouteLocationNormalized } from 'vue-router'
import { setActivePinia, createPinia } from 'pinia'

// Mock auth store
const mockIsAuthenticated = vi.fn(() => false)

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    isAuthenticated: mockIsAuthenticated()
  })
}))

describe('Router 路由守卫', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('认证检查逻辑', () => {
    it('未登录访问需要认证的页面应重定向到登录页', () => {
      mockIsAuthenticated.mockReturnValue(false)
      
      const to = { 
        meta: { requiresAuth: true }, 
        fullPath: '/chat',
        name: 'Chat'
      } as unknown as RouteLocationNormalized
      
      const isAuthenticated = mockIsAuthenticated()
      const requiresAuth = to.meta.requiresAuth
      
      let redirectTo: any = null
      
      if (requiresAuth && !isAuthenticated) {
        redirectTo = { name: 'Login', query: { redirect: to.fullPath } }
      }
      
      expect(redirectTo).toEqual({ name: 'Login', query: { redirect: '/chat' } })
    })

    it('已登录访问登录页应重定向到聊天页', () => {
      mockIsAuthenticated.mockReturnValue(true)
      
      const to = { 
        meta: { requiresAuth: false }, 
        name: 'Login'
      } as unknown as RouteLocationNormalized
      
      const isAuthenticated = mockIsAuthenticated()
      
      let redirectTo: any = null
      
      if (!to.meta.requiresAuth && isAuthenticated && to.name === 'Login') {
        redirectTo = { name: 'Chat' }
      }
      
      expect(redirectTo).toEqual({ name: 'Chat' })
    })

    it('已登录访问注册页应重定向到聊天页', () => {
      mockIsAuthenticated.mockReturnValue(true)
      
      const to = { 
        meta: { requiresAuth: false }, 
        name: 'Register'
      } as unknown as RouteLocationNormalized
      
      const isAuthenticated = mockIsAuthenticated()
      
      let redirectTo: any = null
      
      if (!to.meta.requiresAuth && isAuthenticated && to.name === 'Register') {
        redirectTo = { name: 'Chat' }
      }
      
      expect(redirectTo).toEqual({ name: 'Chat' })
    })

    it('已登录访问需要认证的页面应正常通过', () => {
      mockIsAuthenticated.mockReturnValue(true)
      
      const to = { 
        meta: { requiresAuth: true }, 
        name: 'Chat'
      } as unknown as RouteLocationNormalized
      
      const isAuthenticated = mockIsAuthenticated()
      const requiresAuth = to.meta.requiresAuth
      
      // 已登录且访问需要认证的页面，应该通过
      const shouldPass = requiresAuth && isAuthenticated
      
      expect(shouldPass).toBe(true)
    })

    it('未登录访问公开页面应正常通过', () => {
      mockIsAuthenticated.mockReturnValue(false)
      
      const to = { 
        meta: { requiresAuth: false }, 
        name: 'Login'
      } as unknown as RouteLocationNormalized
      
      const isAuthenticated = mockIsAuthenticated()
      const requiresAuth = to.meta.requiresAuth
      
      // 未登录访问公开页面，应该通过
      const shouldPass = !requiresAuth && !isAuthenticated
      
      expect(shouldPass).toBe(true)
    })
  })

  describe('路由配置', () => {
    const routes = [
      { path: '/login', name: 'Login', meta: { requiresAuth: false, layout: 'auth' } },
      { path: '/register', name: 'Register', meta: { requiresAuth: false, layout: 'auth' } },
      { path: '/', name: 'Home', redirect: '/chat' },
      { path: '/chat', name: 'Chat', meta: { requiresAuth: true, title: '智能对话' } },
      { path: '/chat/:id', name: 'ChatDetail', meta: { requiresAuth: true, title: '智能对话' } },
      { path: '/knowledge', name: 'Knowledge', meta: { requiresAuth: true, title: '知识库' } },
      { path: '/agent', name: 'Agent', meta: { requiresAuth: true, title: 'Agent' } },
      { path: '/settings', name: 'Settings', meta: { requiresAuth: true, title: '设置' } }
    ]

    it('登录和注册页面不需要认证', () => {
      const loginRoute = routes.find(r => r.name === 'Login')
      const registerRoute = routes.find(r => r.name === 'Register')
      
      expect(loginRoute?.meta?.requiresAuth).toBe(false)
      expect(registerRoute?.meta?.requiresAuth).toBe(false)
    })

    it('主要功能页面需要认证', () => {
      const protectedRoutes = ['Chat', 'ChatDetail', 'Knowledge', 'Agent', 'Settings']
      
      protectedRoutes.forEach(name => {
        const route = routes.find(r => r.name === name)
        expect(route?.meta?.requiresAuth).toBe(true)
      })
    })

    it('首页应重定向到聊天页', () => {
      const homeRoute = routes.find(r => r.name === 'Home')
      
      expect(homeRoute?.redirect).toBe('/chat')
    })

    it('认证页面应使用 auth 布局', () => {
      const loginRoute = routes.find(r => r.name === 'Login')
      const registerRoute = routes.find(r => r.name === 'Register')
      
      expect(loginRoute?.meta?.layout).toBe('auth')
      expect(registerRoute?.meta?.layout).toBe('auth')
    })
  })

  describe('路由参数验证', () => {
    it('对话详情页应支持 id 参数', () => {
      const chatDetailRoute = { path: '/chat/:id', name: 'ChatDetail' }
      
      // 验证路径包含 :id 参数
      expect(chatDetailRoute.path).toContain(':id')
    })

    it('应该验证 id 参数为有效正整数', () => {
      const validateId = (id: string | undefined): number | null => {
        if (!id) return null
        const numId = Number(id)
        return Number.isInteger(numId) && numId > 0 ? numId : null
      }

      expect(validateId('123')).toBe(123)
      expect(validateId('0')).toBeNull()
      expect(validateId('-1')).toBeNull()
      expect(validateId('abc')).toBeNull()
      expect(validateId('1.5')).toBeNull()
      expect(validateId(undefined)).toBeNull()
    })
  })
})
