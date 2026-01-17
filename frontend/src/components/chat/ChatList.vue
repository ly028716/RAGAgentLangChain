<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Edit, Delete, ChatLineSquare } from '@element-plus/icons-vue'
import { useConversationStore } from '@/stores/conversation'

defineProps<{
  collapsed?: boolean
}>()

const router = useRouter()
const route = useRoute()
const conversationStore = useConversationStore()

const editingId = ref<number | null>(null)
const editingTitle = ref('')

function selectConversation(id: number) {
  router.push(`/chat/${id}`)
}

function startEdit(id: number, title: string, event: Event) {
  event.stopPropagation()
  editingId.value = id
  editingTitle.value = title
}

async function saveEdit(id: number) {
  if (editingTitle.value.trim()) {
    await conversationStore.updateConversationTitle(id, editingTitle.value.trim())
  }
  editingId.value = null
}

function cancelEdit() {
  editingId.value = null
}

async function deleteConversation(id: number, event: Event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const success = await conversationStore.deleteConversation(id)
    if (success) {
      ElMessage.success('删除成功')
      if (route.params.id === String(id)) {
        router.push('/chat')
      }
    }
  } catch {
    // 取消操作
  }
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}
</script>

<template>
  <div class="chat-list" :class="{ collapsed }">
    <el-scrollbar>
      <div
        v-for="conv in conversationStore.sortedConversations"
        :key="conv.id"
        class="chat-item"
        :class="{ active: route.params.id === String(conv.id) }"
        @click="selectConversation(conv.id)"
      >
        <template v-if="!collapsed">
          <div class="item-content" v-if="editingId !== conv.id">
            <div class="item-title text-ellipsis">{{ conv.title || '新对话' }}</div>
            <div class="item-time">{{ formatTime(conv.updated_at) }}</div>
          </div>
          <el-input
            v-else
            v-model="editingTitle"
            size="small"
            @blur="saveEdit(conv.id)"
            @keyup.enter="saveEdit(conv.id)"
            @keyup.esc="cancelEdit"
            @click.stop
            autofocus
          />
          <div class="item-actions" v-if="editingId !== conv.id">
            <el-button
              :icon="Edit"
              size="small"
              text
              @click="startEdit(conv.id, conv.title, $event)"
            />
            <el-button
              :icon="Delete"
              size="small"
              text
              @click="deleteConversation(conv.id, $event)"
            />
          </div>
        </template>
        <template v-else>
          <el-tooltip :content="conv.title || '新对话'" placement="right">
            <el-icon><ChatLineSquare /></el-icon>
          </el-tooltip>
        </template>
      </div>
      
      <div v-if="conversationStore.conversations.length === 0" class="empty-tip">
        <span v-if="!collapsed">暂无对话记录</span>
      </div>
    </el-scrollbar>
  </div>
</template>

<style scoped lang="scss">
.chat-list {
  flex: 1;
  overflow: hidden;

  &.collapsed {
    .chat-item {
      justify-content: center;
      padding: 12px;
    }
  }
}

.chat-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  color: $sidebar-text;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    
    .item-actions {
      opacity: 1;
    }
  }

  &.active {
    background: $sidebar-active-bg;
    color: white;
  }
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 14px;
  margin-bottom: 2px;
}

.item-time {
  font-size: 12px;
  opacity: 0.6;
}

.item-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;

  .el-button {
    color: $sidebar-text;
    
    &:hover {
      color: white;
    }
  }
}

.empty-tip {
  text-align: center;
  padding: 20px;
  color: $sidebar-text;
  opacity: 0.6;
  font-size: 13px;
}
</style>
