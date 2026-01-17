<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { Promotion, VideoPause } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: string
  disabled?: boolean
  placeholder?: string
  isStreaming?: boolean
}>()

const MAX_LENGTH = 4000

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
  stop: []
}>()

const textareaRef = ref<HTMLTextAreaElement | null>(null)

function updateValue(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

function handleKeydown(event: KeyboardEvent) {
  // Enter发送，Shift+Enter换行
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    if (!props.disabled && props.modelValue.trim()) {
      emit('send')
    }
  }
}

function handleSend() {
  if (!props.disabled && props.modelValue.trim()) {
    emit('send')
  }
}

function handleStop() {
  emit('stop')
}

// 自动调整高度
watch(() => props.modelValue, () => {
  nextTick(() => {
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
      textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px'
    }
  })
})

// 聚焦输入框
function focus() {
  textareaRef.value?.focus()
}

defineExpose({ focus })
</script>

<template>
  <div class="chat-input">
    <div class="input-wrapper">
      <textarea
        ref="textareaRef"
        :value="modelValue"
        :disabled="disabled"
        :placeholder="placeholder || '输入消息，Enter 发送，Shift+Enter 换行'"
        :maxlength="MAX_LENGTH"
        rows="1"
        @input="updateValue"
        @keydown="handleKeydown"
      />
      <div class="input-actions">
        <el-button
          v-if="isStreaming"
          type="danger"
          :icon="VideoPause"
          @click="handleStop"
          circle
        />
        <el-button
          v-else
          type="primary"
          :icon="Promotion"
          :disabled="disabled || !modelValue.trim()"
          @click="handleSend"
          circle
        />
      </div>
    </div>
    <div class="input-tips">
      <span>按 Enter 发送，Shift + Enter 换行</span>
      <span class="char-count">{{ modelValue.length }}/{{ MAX_LENGTH }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-input {
  background: white;
  border-radius: 12px;
  box-shadow: $box-shadow;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 12px 16px;

  textarea {
    flex: 1;
    border: none;
    outline: none;
    resize: none;
    font-size: 14px;
    line-height: 1.6;
    font-family: inherit;
    background: transparent;
    max-height: 200px;
    
    &::placeholder {
      color: $text-placeholder;
    }

    &:disabled {
      background: transparent;
      cursor: not-allowed;
    }
  }
}

.input-actions {
  flex-shrink: 0;
}

.input-tips {
  display: flex;
  justify-content: space-between;
  padding: 0 16px 8px;
  font-size: 12px;
  color: $text-placeholder;
  
  .char-count {
    color: $text-secondary;
  }
}
</style>
