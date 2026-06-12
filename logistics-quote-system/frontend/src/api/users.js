import request from '@/utils/request'

export function getUserActivity() {
  return request({ url: '/v1/users/activity', method: 'get' })
}

export function getLoginHistory() {
  return request({ url: '/v1/users/login_history', method: 'get' })
}
