// frontend/src/api/analytics.js
import request from '@/utils/request'

export function getOverview() {
  return request({ url: '/v1/analytics/overview', method: 'get' })
}

export function getByDestination() {
  return request({ url: '/v1/analytics/by-destination', method: 'get' })
}

export function getByTransport() {
  return request({ url: '/v1/analytics/by-transport', method: 'get' })
}

export function getByAgent() {
  return request({ url: '/v1/analytics/by-agent', method: 'get' })
}

export function getTrend() {
  return request({ url: '/v1/analytics/trend', method: 'get' })
}

export function getPriceDistribution() {
  return request({ url: '/v1/analytics/price-distribution', method: 'get' })
}
