<template>
  <el-dialog
    v-model="visible"
    title="分享知识库"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form 
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item label="用户名" prop="username">
        <el-input 
          v-model="form.username" 
          placeholder="请输入要分享给的用户名"
        />
      </el-form-item>
      
      <el-form-item label="权限" prop="permission_type">
        <el-radio-group v-model="form.permission_type">
          <el-radio value="viewer">查看者</el-radio>
          <el-radio value="editor">编辑者</el-radio>
        </el-radio-group>
        <div class="permission-desc">
          <p v-if="form.permission_type === 'viewer'">查看者只能查询知识库内容</p>
          <p v-else>编辑者可以上传和删除文档</p>
        </div>
      </el-form-item>
    </el-form>
    
    <!-- 已分享用户列表 -->
    <div v-if="permissions.length > 0" class="shared-users">
      <h4>已分享给</h4>
      <el-table :data="permissions" size="small">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="permission_type" label="权限">
          <template #default="{ row }">
            <el-tag :type="row.permission_type === 'editor' ? 'warning' : 'info'" size="small">
              {{ row.permission_type === 'editor' ? '编辑者' : '查看者' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button 
              type="danger" 
              text 
              size="small"
              @click="handleRemove(row)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleShare" :loading="loading">
        分享
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { kbPermissionsApi } from '@/api/kb-permissions'
import type { KnowledgeBasePermission } from '@/types'

const props = defineProps<{
  modelValue: boolean
  knowledgeBaseId: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'shared': []
}>()

const visible = ref(props.modelValue)
const loading = ref(false)
const formRef = ref<FormInstance>()
const permissions = ref<KnowledgeBasePermission[]>([])

const form = reactive({
  username: '',
  permission_type: 'viewer' as 'viewer' | 'editor'
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadPermissions()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const loadPermissions = async () => {
  try {
    const res = await kbPermissionsApi.getPermissions(props.knowledgeBaseId)
    permissions.value = res.items.filter(p => p.user_id !== null)
  } catch (e: any) {
    if (e.response?.status === 404) {
      ElMessage.error('知识库不存在')
      visible.value = false
    } else {
      console.error('加载权限列表失败', e)
    }
  }
}

const handleShare = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await kbPermissionsApi.share(props.knowledgeBaseId, {
        username: form.username,
        permission_type: form.permission_type
      })
      ElMessage.success('分享成功')
      form.username = ''
      await loadPermissions()
      emit('shared')
    } catch (e: any) {
      ElMessage.error(e.response?.data?.detail || '分享失败')
    } finally {
      loading.value = false
    }
  })
}

const handleRemove = async (permission: KnowledgeBasePermission) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除 ${permission.username} 的访问权限吗？`,
      '确认移除',
      { type: 'warning' }
    )
    
    await kbPermissionsApi.deletePermission(props.knowledgeBaseId, permission.id)
    ElMessage.success('已移除')
    await loadPermissions()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '移除失败')
    }
  }
}
</script>

<style scoped lang="scss">
.permission-desc {
  margin-top: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.shared-users {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--el-border-color);
  
  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    color: var(--el-text-color-regular);
  }
}
</style>
