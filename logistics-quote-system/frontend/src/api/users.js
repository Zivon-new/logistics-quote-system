import request from '@/utils/request'

export function getOnlineUsers() {
  return request({ url: '/v1/users/online', method: 'get' })
}

export function getLoginHistory() {
  return request({ url: '/v1/users/login_history', method: 'get' })
}
