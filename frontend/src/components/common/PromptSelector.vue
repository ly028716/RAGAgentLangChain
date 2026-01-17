<template>
  <div class="prompt-selector">
    <el-select
      v-model="selectedId"
      placeholder="选择系统提示词"
      clearable
      :loading="loading"
      @change="handleChange"
    >
      <el-option-group label="系统提示词">
        <el-option
          v-for="prompt in systemPrompts"
          :key="prompt.id"
          :label="prompt.name"
          :value="prompt.id"
        >
          <div class="prompt-option">
            <span class="name">{{ prompt.name }}</span>
            <el-tag v-if="prompt.is_default" size="small" type="success">默认</el-tag>
          </div>
        </el-option>
      </el-option-group>
      
      <el-option-group v-if="userPrompts.length > 0" label="我的提示词">
        <el-option
          v-for="prompt in userPrompts"
          :key="prompt.id"
          :label="prompt.name"
          :value="prompt.id"
        >
          <div class="prompt-option">
            <span class="name">{{ prompt.name }}</span>
            <el-tag v-if="prompt.is_default" size="small" type="success">默认</el-tag>
          </div>
        </el-option>
      </el-option-group>
    </el-select>
    
    <el-button 
      v-if="showManage" 
      text 
      type="primary" 
      @click="showManageDialog = true"
    >
      管理提示词
    </el-button>
    
    <!-- 提示词管理弹窗 -->
    <el-dialog
      v-model="showManageDialog"
      title="管理提示词"
      width="600px"
    >
      <div class="prompt-manager">
        <div class="prompt-list">
          <div 
            v-for="prompt in allPrompts" 
            :key="prompt.id"
            class="prompt-item"
            :class="{ 'is-system': prompt.is_system }"
          >
            <div class="prompt-info">
              <div class="prompt-header">
                <span class="name">{{ prompt.name }}</span>
                <el-tag v-if="prompt.is_system" size="small">系统</el-tag>
                <el-tag v-if="prompt.is_default" size="small" type="success">默认</el-tag>
              </div>
              <p class="content">{{ prompt.content.substring(0, 100) }}...</p>
            </div>
            <div class="prompt-actions">
              <el-button 
                v-if="!prompt.is_default"
                text 
                size="small"
                @click="handleSetDefault(prompt.id)"
              >
                设为默认
              </el-button>
              <el-button 
                v-if="!prompt.is_system"
                text 
                type="danger"
                size="small"
                @click="handleDelete(prompt.id)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
        
        <el-divider />
        
        <el-form :model="newPrompt" label-width="80px">
          <el-form-item label="名称">
            <el-input v-model="newPrompt.name" placeholder="提示词名称" />
          </el-form-item>
          <el-form-item label="内容">
            <el-input 
              v-model="newPrompt.content" 
              type="textarea" 
              :rows="4"
              placeholder="提示词内容"
              maxlength="10000"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="newPrompt.category">
              <el-option label="通用" value="general" />
              <el-option label="专业" value="professional" />
              <el-option label="创意" value="creative" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleCreate" :loading="creating">
              创建提示词
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePromptsStore } from '@/stores/prompts'
import type { SystemPrompt } from '@/types'

const props = withDefaults(defineProps<{
  modelValue?: number | null
  showManage?: boolean
}>(), {
  showManage: false
})

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
  'change': [prompt: SystemPrompt | null]
}>()

const promptsStore = usePromptsStore()
const showManageDialog = ref(false)
const creating = ref(false)

const newPrompt = reactive({
  name: '',
  content: '',
  category: 'general'
})

const selectedId = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val ?? null)
})

const loading = computed(() => promptsStore.loading)
const systemPrompts = computed(() => promptsStore.systemPrompts)
const userPrompts = computed(() => promptsStore.userPrompts)
const allPrompts = computed(() => promptsStore.prompts)

onMounted(async () => {
  if (!promptsStore.hasPrompts) {
    await promptsStore.fetchPrompts()
  }
})

const handleChange = (id: number | null) => {
  const prompt = id ? allPrompts.value.find(p => p.id === id) : null
  emit('change', prompt ?? null)
}

const handleSetDefault = async (id: number) => {
  try {
    await promptsStore.setDefaultPrompt(id)
    ElMessage.success('已设为默认')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '设置失败')
  }
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个提示词吗？', '确认删除', { type: 'warning' })
    await promptsStore.deletePrompt(id)
    ElMessage.success('已删除')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

const handleCreate = async () => {
  if (!newPrompt.name || !newPrompt.content) {
    ElMessage.warning('请填写名称和内容')
    return
  }
  
  creating.value = true
  try {
    await promptsStore.createPrompt({
      name: newPrompt.name,
      content: newPrompt.content,
      category: newPrompt.category
    })
    ElMessage.success('创建成功')
    newPrompt.name = ''
    newPrompt.content = ''
    newPrompt.category = 'general'
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}
</script>

<style scoped lang="scss">
.prompt-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt-option {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .name {
    flex: 1;
  }
}

.prompt-manager {
  .prompt-list {
    max-height: 300px;
    overflow-y: auto;
  }
  
  .prompt-item {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 12px;
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    margin-bottom: 8px;
    
    &.is-system {
      background: var(--el-fill-color-light);
    }
    
    .prompt-info {
      flex: 1;
      
      .prompt-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
        
        .name {
          font-weight: 500;
        }
      }
      
      .content {
        margin: 0;
        font-size: 12px;
        color: var(--el-text-color-secondary);
        line-height: 1.5;
      }
    }
    
    .prompt-actions {
      display: flex;
      gap: 4px;
    }
  }
}
</style>
