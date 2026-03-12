// frontend/src/api/quote.js
import request from '@/utils/request'

/**
 * 搜索报价
 */
export function searchQuotes(params) {
  return request({
    url: '/v1/quotes/search',
    method: 'get',
    params
  })
}
