// frontend/src/api/risk.js
import request from '@/utils/request'

export function getLpiList() {
  return request({ url: '/v1/risk/lpi-list', method: 'get' })
}

export function getRouteRisk(origin, destination) {
  return request({
    url: '/v1/risk/route-risk',
    method: 'get',
    params: { origin, destination }
  })
}
