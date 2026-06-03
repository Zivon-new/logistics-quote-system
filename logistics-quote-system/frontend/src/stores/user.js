// frontend/src/stores/user.js
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))
  const authExpired = ref(false)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUserInfo(info) {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  function clearAuth() {
    token.value = ''
    userInfo.value = {}
    authExpired.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  function setAuthExpired(val) {
    authExpired.value = val
  }

  return {
    token,
    userInfo,
    authExpired,
    setToken,
    setUserInfo,
    clearAuth,
    setAuthExpired,
  }
})
