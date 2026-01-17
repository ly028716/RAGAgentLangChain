import request from './index'
import type {
  KnowledgeBasePermission,
  PermissionCreate,
  PermissionUpdate,
  ShareKnowledgeBaseRequest,
  PaginatedList
} from '@/types'

export const kbPermissionsApi = {
  // 获取权限列表
  getPermissions(kbId: number): Promise<PaginatedList<KnowledgeBasePermission>> {
    return request.get(`/knowledge-bases/${kbId}/permissions`)
  },

  // 添加权限
  addPermission(kbId: number, data: PermissionCreate): Promise<KnowledgeBasePermission> {
    return request.post(`/knowledge-bases/${kbId}/permissions`, data)
  },

  // 更新权限
  updatePermission(kbId: number, permissionId: number, data: PermissionUpdate): Promise<KnowledgeBasePermission> {
    return request.put(`/knowledge-bases/${kbId}/permissions/${permissionId}`, data)
  },

  // 删除权限
  deletePermission(kbId: number, permissionId: number): Promise<void> {
    return request.delete(`/knowledge-bases/${kbId}/permissions/${permissionId}`)
  },

  // 通过用户名分享知识库
  share(kbId: number, data: ShareKnowledgeBaseRequest): Promise<KnowledgeBasePermission> {
    return request.post(`/knowledge-bases/${kbId}/share`, data)
  }
}
