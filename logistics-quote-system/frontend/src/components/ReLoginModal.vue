<template>
  <el-dialog
    v-model="visible"
    title="登录已过期，请重新登录"
    width="400px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    align-center
  >
    <p class="tip-text">你的登录状态已过期，当前页面数据仍然保留。重新登录后可继续操作。</p>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @keyup.enter="handleReLogin">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>
      <el-form-item label="验证码" prop="captchaAnswer">
        <div class="captcha-row">
          <el-input v-model="form.captchaAnswer" style="flex:1" />
          <img
            v-if="captchaImage"
            :src="captchaImage"
            class="captcha-img"
            title="点击刷新"
            @click="loadCaptcha"
          />
          <el-button v-else link @click="loadCaptcha">加载验证码</el-button>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleLogout">退出登录（放弃当前操作）</el-button>
      <el-button type="primary" :loading="loading" @click="handleReLogin">重新登录</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getCaptcha, login } from '@/api/auth'
import router from '@/router'

const userStore = useUserStore()
const visible = ref(false)
const loading = ref(false)
const captchaId = ref('')
const captchaImage = ref('')

const formRef = ref(null)
const form = ref({
  username: '',
  password: '',
  captchaAnswer: '',
})

const rules = {
  username:      [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password:      [{ required: true, message: '请输入密码',   trigger: 'blur' }],
  captchaAnswer: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
}

watch(() => userStore.authExpired, (val) => {
  if (val) {
    form.value.username = userStore.userInfo?.username || ''
    form.value.password = ''
    form.value.captchaAnswer = ''
    visible.value = true
    loadCaptcha()
  } else {
    visible.value = false
  }
})

const loadCaptcha = async () => {
  try {
    const res = await getCaptcha()
    captchaId.value = res.captcha_id
    captchaImage.value = res.image
  } catch {
    ElMessage.error('验证码加载失败，请重试')
  }
}

const handleReLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await login({
        username:       form.value.username,
        password:       form.value.password,
        captcha_id:     captchaId.value,
        captcha_answer: form.value.captchaAnswer,
      })
      userStore.setToken(res.access_token)
      userStore.setUserInfo(res.user)
      userStore.setAuthExpired(false)
      ElMessage.success('重新登录成功，请继续操作')
    } catch {
      form.value.captchaAnswer = ''
      loadCaptcha()
    } finally {
      loading.value = false
    }
  })
}

const handleLogout = () => {
  userStore.clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.tip-text {
  color: #666;
  font-size: 13px;
  margin-bottom: 16px;
  line-height: 1.6;
}
.captcha-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.captcha-img {
  height: 36px;
  cursor: pointer;
  border-radius: 4px;
  border: 1px solid #ddd;
}
</style>
