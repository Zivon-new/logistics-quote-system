import request from '@/utils/request'

export function getOnlineUsers() {
  return request({ url: '/v1/users/online', method: 'get' })
}
