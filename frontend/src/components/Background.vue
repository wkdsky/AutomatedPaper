<template>
  <div class="background-container"></div>
</template>

<script setup>
// 无需额外脚本逻辑
</script>

<style scoped>
.background-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-image: url('/background.jpg');
  background-size: cover;
  background-attachment: fixed;
  background-position: center;
  z-index: -1; /* 确保在所有内容之下 */
  opacity: 0.9; /* 可以调整透明度 */
}
</style> 