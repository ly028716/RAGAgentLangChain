<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Setting, ChatDotRound, Loading } from '@element-plus/icons-vue'
import { useConversationStore } from '@/stores/conversation'
import { useChat } from '@/composables/useChat'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import type { ChatConfig } from '@/types'

const route = useRoute()
const router = useRouter()
const conversationStore = useConversationStore()
const { sendMessage, stopStreaming } = useChat()

const messageListRef = ref<HTMLElement | null>(null)
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null)
const inputContent = ref('')
const showConfig = ref(false)

const config = ref<ChatConfig>({
  temperature: 0.7,
  max_tokens: 2000
})

const currentConversationId = computed(() => {
  const id = route.params.id
  if (!id) return null
  const numId = Number(id)
  // 验证是否为有效的正整数
  return Number.isInteger(numId) && numId > 0 ? numId : null
})

const messages = computed(() => conversationStore.messages)
const isStreaming = computed(() => conversationStore.isStreaming)
const streamingContent = computed(() => conversationStore.streamingContent)
const isLoading = computed(() => conversationStore.isLoading)

// 监听路由变化，加载对话
watch(currentConversationId, async (newId) => {
  conversationStore.clearMessages()
  if (newId) {
    conversationStore.setCurrentConversation(newId)
    await conversationStore.fetchMessages(newId)
    scrollToBottom()
  } else {
    conversationStore.setCurrentConversation(null)
  }
}, { immediate: true })

async function handleSend() {
  const content = inputContent.value.trim()
  if (!content || isStreaming.value) return

  inputContent.value = ''
  scrollToBottom()

  const result = await sendMessage(content, currentConversationId.value, config.value)
  
  if (result.success) {
    // 如果是新对话，跳转到对话页面
    if (result.conversationId && !currentConversationId.value) {
      await conversationStore.fetchConversations()
      router.push(`/chat/${result.conversationId}`)
    }
    scrollToBottom()
  } else {
    ElMessage.error('发送消息失败，请重试')
  }
}

function handleStop() {
  stopStreaming()
}

async function handleRegenerate() {
  // 获取最后一条用户消息
  const lastUserMessage = [...messages.value].reverse().find(m => m.role === 'user')
  if (!lastUserMessage) return

  // 移除最后一条AI回复
  const lastIndex = messages.value.length - 1
  if (messages.value[lastIndex]?.role === 'assistant') {
    conversationStore.messages.pop()
  }

  // 重新发送
  await sendMessage(lastUserMessage.content, currentConversationId.value, config.value)
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function toggleConfig() {
  showConfig.value = !showConfig.value
}

onMounted(() => {
  chatInputRef.value?.focus()
})
</script>

<template>
  <div class="chat-view">
    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <div v-if="isLoading && messages.length === 0" class="loading-state">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <template v-else-if="messages.length > 0 || isStreaming">
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :message="message"
          @regenerate="handleRegenerate"
        />
        
        <!-- 流式输出中的消息 -->
        <ChatMessage
          v-if="isStreaming && streamingContent"
          :message="{ id: -1, role: 'assistant', content: streamingContent, created_at: '' }"
          :is-streaming="true"
        />
      </template>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-icon :size="64" color="#c0c4cc"><ChatDotRound /></el-icon>
        <h3>开始新对话</h3>
        <p>输入您的问题，AI 助手将为您解答</p>
        <div class="quick-prompts">
          <el-tag 
            v-for="prompt in ['帮我写一段Python代码', '解释什么是机器学习', '今天天气怎么样']"
            :key="prompt"
            @click="inputContent = prompt"
            class="prompt-tag"
          >
            {{ prompt }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-toolbar">
        <el-tooltip content="对话配置" placement="top">
          <el-button :icon="Setting" text @click="toggleConfig" />
        </el-tooltip>
      </div>
      <ChatInput
        ref="chatInputRef"
        v-model="inputContent"
        :disabled="isStreaming"
        :is-streaming="isStreaming"
        :placeholder="isStreaming ? '正在生成回复...' : '输入您的问题...'"
        @send="handleSend"
        @stop="handleStop"
      />
    </div>

    <!-- 配置面板 -->
    <el-drawer
      v-model="showConfig"
      title="对话配置"
      direction="rtl"
      size="320px"
    >
      <el-form label-position="top">
        <el-form-item label="温度 (Temperature)">
          <el-slider
            v-model="config.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            show-input
          />
          <div class="form-tip">较低的值使输出更确定，较高的值使输出更随机</div>
        </el-form-item>

        <el-form-item label="最大 Token 数">
          <el-input-number
            v-model="config.max_tokens"
            :min="100"
            :max="4000"
            :step="100"
            style="width: 100%"
          />
          <div class="form-tip">控制回复的最大长度</div>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<style scoped lang="scss">
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: $bg-page;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: $text-secondary;

  h3 {
    margin: 16px 0 8px;
    color: $text-primary;
  }

  p {
    margin: 0;
  }
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 24px;
  justify-content: center;

  .prompt-tag {
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      transform: translateY(-2px);
      box-shadow: $box-shadow-light;
    }
  }
}

.input-area {
  padding: 16px 20px 20px;
  background: $bg-page;
}

.input-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.form-tip {
  font-size: 12px;
  color: $text-secondary;
  margin-top: 4px;
}
</style>
