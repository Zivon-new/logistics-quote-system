// frontend/src/api/attachment.js
import request from '@/utils/request'

export function uploadAttachment(routeId, file, agentIndex = null) {
  const form = new FormData()
  form.append('file', file)
  const url = agentIndex !== null
    ? `/v1/attachments/upload/${routeId}?agent_index=${agentIndex}`
    : `/v1/attachments/upload/${routeId}`
  return request({ url, method: 'post', data: form, headers: { 'Content-Type': 'multipart/form-data' } })
}

export function listAttachments(routeId, agentIndex = null) {
  const url = agentIndex !== null
    ? `/v1/attachments/route/${routeId}?agent_index=${agentIndex}`
    : `/v1/attachments/route/${routeId}`
  return request({ url, method: 'get' })
}

export function deleteAttachment(attachmentId) {
  return request({ url: `/v1/attachments/${attachmentId}`, method: 'delete' })
}

export function getDownloadUrl(attachmentId) {
  return `/api/v1/attachments/${attachmentId}/download`
}
