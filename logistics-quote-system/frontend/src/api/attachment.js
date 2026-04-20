// frontend/src/api/attachment.js
import request from '@/utils/request'

export function uploadAttachment(routeId, file) {
  const form = new FormData()
  form.append('file', file)
  return request({
    url: `/v1/attachments/upload/${routeId}`,
    method: 'post',
    data: form,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function listAttachments(routeId) {
  return request({ url: `/v1/attachments/route/${routeId}`, method: 'get' })
}

export function deleteAttachment(attachmentId) {
  return request({ url: `/v1/attachments/${attachmentId}`, method: 'delete' })
}

export function getDownloadUrl(attachmentId) {
  return `/api/v1/attachments/${attachmentId}/download`
}
