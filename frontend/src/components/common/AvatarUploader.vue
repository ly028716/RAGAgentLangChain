<template>
  <div class="avatar-uploader">
    <el-upload
      class="avatar-upload"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :http-request="handleUpload"
      accept="image/jpeg,image/png,image/gif,image/webp"
    >
      <div class="avatar-container">
        <el-avatar 
          :size="size" 
          :src="avatarUrl || undefined"
          class="avatar"
        >
          <el-icon v-if="!avatarUrl" :size="size / 2"><User /></el-icon>
        </el-avatar>
        <div class="avatar-overlay" :class="{ 'is-uploading': uploading }">
          <el-icon v-if="uploading" class="is-loading"><Loading /></el-icon>
          <el-icon v-else><Camera /></el-icon>
          <span>{{ uploading ? '上传中...' : (avatarUrl ? '更换头像' : '上传头像') }}</span>
        </div>
      </div>
    </el-upload>
    
    <div v-if="avatarUrl && showDelete" class="avatar-actions">
      <el-button 
        type="danger" 
        text 
        size="small" 
        @click="handleDelete"
        :loading="deleting"
      >
        删除头像
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Camera, Loading } from '@element-plus/icons-vue'
import { userApi } from '@/api/user'

const props = withDefaults(defineProps<{
  modelValue?: string
  size?: number
  showDelete?: boolean
}>(), {
  size: 100,
  showDelete: true
})

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  'change': [url: string | null]
}>()

const uploading = ref(false)
const deleting = ref(false)

const avatarUrl = computed({
  get: () => props.modelValue,
  set: (val: string | null | undefined) => emit('update:modelValue', val ?? null)
})

const beforeUpload = (file: File) => {
  const isImage = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    ElMessage.error('只能上传 JPG/PNG/GIF/WebP 格式的图片')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

const handleUpload = async (options: { file: File }) => {
  uploading.value = true
  try {
    const res = await userApi.uploadAvatar(options.file)
    avatarUrl.value = res.avatar_url
    emit('change', res.avatar_url)
    ElMessage.success('头像上传成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

const handleDelete = async () => {
  deleting.value = true
  try {
    await userApi.deleteAvatar()
    avatarUrl.value = null
    emit('change', null)
    ElMessage.success('头像已删除')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped lang="scss">
.avatar-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-upload {
  cursor: pointer;
}

.avatar-container {
  position: relative;
  
  .avatar {
    border: 2px solid var(--el-border-color);
  }
  
  .avatar-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: white;
    opacity: 0;
    transition: opacity 0.3s;
    font-size: 12px;
    gap: 4px;
    
    .el-icon {
      font-size: 20px;
    }
    
    &.is-uploading {
      opacity: 1;
    }
  }
  
  &:hover .avatar-overlay {
    opacity: 1;
  }
}

.avatar-actions {
  margin-top: 8px;
}
</style>
