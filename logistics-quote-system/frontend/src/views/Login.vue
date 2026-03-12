<template>
  <div class="login-container">
    <!-- 网格背景 -->
    <div class="grid-background"></div>
    
    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo和标题 -->
      <div class="login-header">
        <div class="logo-circle">
          <span class="logo-text">e'</span>
        </div>
        <h1 class="system-title">国际物流报价系统</h1>
        <p class="system-subtitle">Logistics Quote System</p>
      </div>

      <!-- 登录表单 -->
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="rememberMe">记住密码</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 测试账号提示 -->
      <div class="test-accounts">
        <p>测试账号：</p>
        <p>管理员：admin / admin123</p>
        <p>普通用户：user / user123</p>
      </div>
    </div>

    <!-- 页脚 -->
    <div class="login-footer">
      <p>©2026 北京嘉恒利供应链管理有限公司</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

// 登录处理
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      
      try {
        const res = await login(loginForm)
        
        // 保存token和用户信息
        userStore.setToken(res.access_token)
        userStore.setUserInfo(res.user)
        
        ElMessage.success('登录成功')
        
        // 跳转到首页
        router.push('/dashboard')
      } catch (error) {
        console.error('登录失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-circle {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.logo-text {
  font-size: 32px;
  font-weight: bold;
  color: #ffffff;
  font-style: italic;
}

.system-title {
  font-size: 24px;
  font-weight: 600;
  color: #001529;
  margin-bottom: 8px;
}

.system-subtitle {
  font-size: 14px;
  color: #8c8c8c;
}

.login-form {
  margin-top: 30px;
}

.login-button {
  width: 100%;
  height: 45px;
  font-size: 16px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border: none;
}

.login-button:hover {
  background: linear-gradient(135deg, #40a9ff 0%, #1890ff 100%);
}

.test-accounts {
  margin-top: 20px;
  padding: 15px;
  background: #f0f2f5;
  border-radius: 4px;
  font-size: 13px;
  color: #595959;
  line-height: 1.8;
}

.test-accounts p:first-child {
  font-weight: 600;
  margin-bottom: 5px;
}

.login-footer {
  position: absolute;
  bottom: 30px;
  left: 0;
  right: 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}
</style>
