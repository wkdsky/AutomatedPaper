<template>
  <div class="login-container">
    <h2>自动阅卷系统登录</h2>
    <form @submit.prevent="handleLogin">
      <input v-model="username" placeholder="账号" required />
      <input v-model="password" type="password" placeholder="密码" required />
      <button type="submit">登录</button>
      <button type="button" @click="showRegister = true">创建账号</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>

    <!-- 注册弹窗 -->
    <div v-if="showRegister" class="register-modal">
      <div class="register-box">
        <h3>免费注册</h3>
        <input v-model="regUsername" placeholder="账号（1-50字符）" maxlength="50" />
        <input v-model="regPassword" type="password" placeholder="密码（1-255字符）" maxlength="255" />
        <button @click="handleRegister">注册</button>
        <button @click="showRegister = false">取消</button>
        <p v-if="regError" class="error">{{ regError }}</p>
        <p v-if="regSuccess" class="success">{{ regSuccess }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

// Hook函数：确保背景图片正确加载
const useBackgroundImage = (imagePath) => {
  const applyBackground = () => {
    const body = document.body
    if (body) {
      body.style.backgroundImage = `url('${imagePath}')`
      body.style.backgroundSize = 'cover'
      body.style.backgroundPosition = 'center'
      body.style.backgroundAttachment = 'fixed'
      body.style.backgroundRepeat = 'no-repeat'
      body.style.minHeight = '100vh'
      body.style.margin = '0'
    }
  }

  const removeBackground = () => {
    const body = document.body
    if (body) {
      body.style.backgroundImage = ''
      body.style.backgroundSize = ''
      body.style.backgroundPosition = ''
      body.style.backgroundAttachment = ''
      body.style.backgroundRepeat = ''
      body.style.minHeight = ''
      body.style.margin = ''
    }
  }

  onMounted(() => {
    // 确保DOM完全渲染后再应用背景
    setTimeout(applyBackground, 0)
  })

  onUnmounted(() => {
    // 组件卸载时清理背景样式
    removeBackground()
  })

  return { applyBackground, removeBackground }
}

// 使用hook函数
useBackgroundImage('/1.jpg')

const username = ref('')
const password = ref('')
const error = ref('')
const showRegister = ref(false)
const regUsername = ref('')
const regPassword = ref('')
const regError = ref('')
const regSuccess = ref('')

const router = useRouter()

const handleLogin = async () => {
  try {
    await axios.post('http://localhost:8001/api/login', {
      username: username.value,
      password: password.value
    })
    localStorage.setItem('username', username.value)
    router.push('/home')
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败'
  }
}

const handleRegister = async () => {
  regError.value = ''
  regSuccess.value = ''
  if (!regUsername.value || !regPassword.value) {
    regError.value = '用户名和密码不能为空'
    return
  }
  try {
    await axios.post('http://localhost:8001/api/register', {
      username: regUsername.value,
      password: regPassword.value
    })
    regSuccess.value = '注册成功，请登录'
    setTimeout(() => {
      showRegister.value = false
      username.value = regUsername.value   // 自动填充账号到登录框
      regUsername.value = ''
      regPassword.value = ''
      regSuccess.value = ''
    }, 500)
  } catch (e) {
    regError.value = e.response?.data?.detail || '注册失败'
  }
}
</script>

<style scoped>
.login-container {
  max-width: 350px;
  margin: 100px auto;
  padding: 32px 24px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.2);
  text-align: center;
  position: relative;
  z-index: 10;
}

/* 添加背景图片样式 - 现在通过hook函数处理 */

.login-container h2 {
  margin-bottom: 24px;
}
.login-container input {
  display: block;
  width: 100%;
  margin: 12px 0;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
}
.login-container button {
  margin: 8px 4px;
  padding: 8px 24px;
  border: none;
  border-radius: 4px;
  background: #23395d;
  color: #fff;
  cursor: pointer;
}
.error {
  color: #e74c3c;
  margin-top: 12px;
}

.register-modal {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.register-box {
  background: #fff;
  padding: 32px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.3);
  text-align: center;
  min-width: 300px;
}
.success {
  color: #27ae60;
  margin-top: 12px;
}
</style>