// frontend/src/api/ports.js
import request from '@/utils/request'

export function getPorts() {
  return request({ url: '/v1/ports', method: 'get' })
}

export function getPortStats() {
  return request({ url: '/v1/ports/stats', method: 'get' })
}
