// frontend/src/api/auth.js
import request from '@/utils/request'

/**
 * 用户登录
 */
export function login(data) {
  return request({
    url: '/v1/auth/login',
    method: 'post',
    data
  })
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
  return request({
    url: '/v1/auth/me',
    method: 'get'
  })
}

/**
 * 用户登出
 */
export function logout() {
  return request({
    url: '/v1/auth/logout',
    method: 'post'
  })
}
