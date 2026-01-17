import { describe, it, expect, vi, beforeEach } from 'vitest'
import { kbPermissionsApi } from '@/api/kb-permissions'
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

describe('Knowledge Base Permissions API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getPermissions', () => {
    it('should call GET /knowledge-bases/:id/permissions', async () => {
      const mockResponse = { items: [], total: 0 }
      vi.mocked(request.get).mockResolvedValue(mockResponse)

      await kbPermissionsApi.getPermissions(1)

      expect(request.get).toHaveBeenCalledWith('/knowledge-bases/1/permissions')
    })
  })

  describe('addPermission', () => {
    it('should call POST /knowledge-bases/:id/permissions', async () => {
      const permissionData = { user_id: 2, permission_type: 'viewer' as const }
      const mockResponse = { id: 1, ...permissionData }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await kbPermissionsApi.addPermission(1, permissionData)

      expect(request.post).toHaveBeenCalledWith('/knowledge-bases/1/permissions', permissionData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updatePermission', () => {
    it('should call PUT /knowledge-bases/:kbId/permissions/:permId', async () => {
      const updateData = { permission_type: 'editor' as const }
      const mockResponse = { id: 1, permission_type: 'editor' }
      vi.mocked(request.put).mockResolvedValue(mockResponse)

      const result = await kbPermissionsApi.updatePermission(1, 2, updateData)

      expect(request.put).toHaveBeenCalledWith('/knowledge-bases/1/permissions/2', updateData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deletePermission', () => {
    it('should call DELETE /knowledge-bases/:kbId/permissions/:permId', async () => {
      vi.mocked(request.delete).mockResolvedValue(undefined)

      await kbPermissionsApi.deletePermission(1, 2)

      expect(request.delete).toHaveBeenCalledWith('/knowledge-bases/1/permissions/2')
    })
  })

  describe('share', () => {
    it('should call POST /knowledge-bases/:id/share', async () => {
      const shareData = { username: 'testuser', permission_type: 'viewer' as const }
      const mockResponse = { id: 1, username: 'testuser', permission_type: 'viewer' }
      vi.mocked(request.post).mockResolvedValue(mockResponse)

      const result = await kbPermissionsApi.share(1, shareData)

      expect(request.post).toHaveBeenCalledWith('/knowledge-bases/1/share', shareData)
      expect(result).toEqual(mockResponse)
    })
  })
})
