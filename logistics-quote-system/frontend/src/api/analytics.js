// frontend/src/api/analytics.js
import request from '@/utils/request'

export function getOverview() {
  return request({ url: '/v1/analytics/overview', method: 'get' })
}

export function getRouteUsage() {
  return request({ url: '/v1/analytics/route-usage', method: 'get' })
}

export function getRouteAgentDist(params = {}) {
  return request({ url: '/v1/analytics/route-agent-dist', method: 'get', params })
}

export function getTrend(granularity = 'month') {
  return request({ url: '/v1/analytics/trend', method: 'get', params: { granularity } })
}

export function getByAgent() {
  return request({ url: '/v1/analytics/by-agent', method: 'get' })
}

export function getPriceDistribution() {
  return request({ url: '/v1/analytics/price-distribution', method: 'get' })
}
