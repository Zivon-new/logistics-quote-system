// frontend/src/api/recommend.js
import request from '@/utils/request'

/**
 * 获取智能推荐结果
 */
export function getRecommendations(params) {
  return request({
    url: '/v1/recommend',
    method: 'get',
    params
  })
}

/**
 * 获取搜索选项（起始地/目的地下拉列表）
 */
export function getSearchOptions() {
  return request({
    url: '/v1/recommend/options',
    method: 'get'
  })
}
