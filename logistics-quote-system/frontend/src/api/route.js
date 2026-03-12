// src/api/route.js
// 路线相关API接口

import request from '@/utils/request'

/**
 * 获取路线列表
 */
export function getRoutes(params) {
  return request({
    url: '/v1/routes',
    method: 'get',
    params
  })
}

/**
 * 获取路线详情
 */
export function getRouteDetail(id) {
  return request({
    url: `/v1/routes/${id}`,
    method: 'get'
  })
}

/**
 * 获取路线编辑数据
 */
export function getRouteForEdit(id) {
  return request({
    url: `/v1/routes/${id}`,
    method: 'get'
  })
}

/**
 * 创建新路线
 */
export function createRoute(data) {
  return request({
    url: '/v1/routes/full',
    method: 'post',
    data
  })
}

/**
 * 更新路线信息
 */
export function updateRoute(id, data) {
  return request({
    url: `/v1/routes/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除路线
 */
export function deleteRoute(id) {
  return request({
    url: `/v1/routes/${id}`,
    method: 'delete'
  })
}

/**
 * 上传Excel并提取数据
 */
export function uploadAndExtractExcel(formData) {
  return request({
    url: '/v1/routes/import/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 300000
  })
}

/**
 * 保存Excel导入的数据
 */
export function saveImportedData(data) {
  return request({
    url: '/v1/routes/import/save',
    method: 'post',
    data
  })
}

/**
 * 为路线添加代理商
 */
export function addAgentToRoute(routeId, agentData) {
  return request({
    url: `/v1/routes/${routeId}/agents`,
    method: 'post',
    data: agentData
  })
}

/**
 * 删除代理商
 */
export function deleteAgent(routeId, agentId) {
  return request({
    url: `/v1/routes/${routeId}/agents/${agentId}`,
    method: 'delete'
  })
}

/**
 * 获取汇率列表
 */
export function getExchangeRates() {
  return request({
    url: '/v1/routes/forex_rates',
    method: 'get'
  })
}

/**
 * 获取统计数据
 */
export function getStats() {
  return request({
    url: '/v1/routes/stats',
    method: 'get'
  })
}

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