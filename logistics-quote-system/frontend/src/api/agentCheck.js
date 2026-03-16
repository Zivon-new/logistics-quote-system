// frontend/src/api/agentCheck.js
import request from '@/utils/request'

export function checkAgent(keyword, rawText, forceRefresh = false) {
  return request({
    url: '/v1/agent-check/check',
    method: 'post',
    data: { keyword, raw_text: rawText, force_refresh: forceRefresh }
  })
}

export function getHistory() {
  return request({ url: '/v1/agent-check/history', method: 'get' })
}

export function getHistoryDetail(id) {
  return request({ url: `/v1/agent-check/history/${id}`, method: 'get' })
}
