<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="not-found">
    <div class="content">
      <h1>404</h1>
      <p>抱歉，您访问的页面不存在</p>
      <el-button type="primary" @click="goHome">返回首页</el-button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.not-found {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-page;
}

.content {
  text-align: center;

  h1 {
    font-size: 120px;
    color: $primary-color;
    margin: 0;
    line-height: 1;
  }

  p {
    font-size: 18px;
    color: $text-secondary;
    margin: 20px 0 30px;
  }
}
</style>
