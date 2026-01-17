<script setup lang="ts">
import { MagicStick } from '@element-plus/icons-vue'
</script>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-header">
        <div class="logo">
          <el-icon :size="40" color="#409eff"><MagicStick /></el-icon>
          <h1>AI 智能助手</h1>
        </div>
        <p class="subtitle">基于大语言模型的智能对话系统</p>
      </div>
      <div class="auth-content">
        <slot />
      </div>
    </div>
    <div class="auth-footer">
      <p>© 2026 AI智能助手系统</p>
    </div>
  </div>
</template>

<style scoped lang="scss">
.auth-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-container {
  width: 100%;
  max-width: 420px;
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
  color: white;

  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-bottom: 12px;

    h1 {
      font-size: 28px;
      font-weight: 600;
      margin: 0;
    }

    .el-icon {
      background: white;
      border-radius: 12px;
      padding: 8px;
    }
  }

  .subtitle {
    font-size: 14px;
    opacity: 0.9;
  }
}

.auth-content {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.auth-footer {
  margin-top: 24px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}
</style>
