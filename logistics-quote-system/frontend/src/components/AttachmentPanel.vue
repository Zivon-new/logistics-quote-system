<template>
  <div class="attachment-panel">
    <!-- 上传区 -->
    <div class="upload-area">
      <el-upload
        :before-upload="handleBeforeUpload"
        :show-file-list="false"
        :disabled="uploading"
        accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx"
        multiple
      >
        <el-button :loading="uploading" :icon="Upload" size="small" type="primary">
          上传附件
        </el-button>
      </el-upload>
      <span class="upload-tip">支持 图片 / PDF / Word / Excel，单文件最大 20MB</span>
    </div>

    <!-- 附件列表 -->
    <div v-if="attachments.length" class="attachment-list">
      <div
        v-for="item in attachments"
        :key="item.attachment_id"
        class="attachment-item"
      >
        <!-- 文件图标 -->
        <span class="file-icon">{{ fileIcon(item.file_type) }}</span>

        <!-- 文件信息 -->
        <div class="file-info">
          <span class="file-name" :title="item.original_name">{{ item.original_name }}</span>
          <span class="file-meta">{{ formatSize(item.file_size) }} · {{ item.upload_time?.slice(0, 16) }}</span>
        </div>

        <!-- 操作 -->
        <div class="file-actions">
          <!-- 图片：点击预览 -->
          <el-button
            v-if="item.file_type === 'image'"
            link size="small" type="primary"
            @click="previewImage(item)"
          >预览</el-button>

          <!-- PDF/Word/Excel：新标签页打开（PDF浏览器内预览，其他下载） -->
          <el-button
            v-else
            link size="small" type="primary"
            @click="openFile(item)"
          >{{ item.file_type === 'pdf' ? '预览' : '下载' }}</el-button>

          <!-- 所有类型都有下载按钮 -->
          <el-button link size="small" @click="downloadFile(item)">下载</el-button>

          <el-popconfirm
            title="确认删除这个附件？"
            confirm-button-text="删除"
            cancel-button-text="取消"
            @confirm="handleDelete(item)"
          >
            <template #reference>
              <el-button link size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </div>

    <el-empty v-else-if="!loading" description="暂无附件" :image-size="48" />

    <!-- 图片预览 -->
    <el-image-viewer
      v-if="imageViewerVisible"
      :url-list="[previewUrl]"
      @close="imageViewerVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { uploadAttachment, listAttachments, deleteAttachment, getDownloadUrl } from '@/api/attachment'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  routeId: { type: Number, required: true }
})

const userStore = useUserStore()
const attachments = ref([])
const loading = ref(false)
const uploading = ref(false)
const imageViewerVisible = ref(false)
const previewUrl = ref('')

const loadList = async () => {
  if (!props.routeId) return
  loading.value = true
  try {
    attachments.value = await listAttachments(props.routeId)
  } finally {
    loading.value = false
  }
}

watch(() => props.routeId, loadList, { immediate: true })

const handleBeforeUpload = async (file) => {
  uploading.value = true
  try {
    await uploadAttachment(props.routeId, file)
    ElMessage.success(`${file.name} 上传成功`)
    await loadList()
  } catch (e) {
    ElMessage.error('上传失败：' + (e?.response?.data?.detail || e.message))
  } finally {
    uploading.value = false
  }
  return false  // 阻止 el-upload 默认行为
}

const handleDelete = async (item) => {
  await deleteAttachment(item.attachment_id)
  ElMessage.success('已删除')
  attachments.value = attachments.value.filter(a => a.attachment_id !== item.attachment_id)
}

const previewImage = (item) => {
  previewUrl.value = getDownloadUrl(item.attachment_id) + `?token=${userStore.token}`
  imageViewerVisible.value = true
}

const openFile = (item) => {
  const url = getDownloadUrl(item.attachment_id)
  // 带 token（通过请求头鉴权暂不支持新标签页，改用带参数方式）
  // 此处直接跳转，后端通过 Authorization header 鉴权需要中间件支持
  // 简单处理：用 fetch 获取 blob 后打开
  fetchAndOpen(item)
}

const downloadFile = (item) => {
  fetchAndOpen(item, true)
}

const fetchAndOpen = async (item, forceDownload = false) => {
  try {
    const url = getDownloadUrl(item.attachment_id)
    const res = await fetch('/api' + url.replace('/api', ''), {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    if (!res.ok) throw new Error('获取失败')
    const blob = await res.blob()
    const blobUrl = URL.createObjectURL(blob)

    if (forceDownload || !['image', 'pdf'].includes(item.file_type)) {
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = item.original_name
      a.click()
    } else {
      window.open(blobUrl, '_blank')
    }
    setTimeout(() => URL.revokeObjectURL(blobUrl), 10000)
  } catch (e) {
    ElMessage.error('操作失败：' + e.message)
  }
}

const fileIcon = (type) => {
  const map = { image: '🖼️', pdf: '📄', word: '📝', excel: '📊' }
  return map[type] || '📎'
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}
</script>

<style scoped>
.attachment-panel { padding: 4px 0; }

.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.upload-tip { font-size: 12px; color: #8c8c8c; }

.attachment-list { display: flex; flex-direction: column; gap: 6px; }

.attachment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  transition: border-color .2s;
}
.attachment-item:hover { border-color: #1890ff; }

.file-icon { font-size: 20px; flex-shrink: 0; }

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.file-name {
  font-size: 13px;
  font-weight: 500;
  color: #262626;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-meta { font-size: 11px; color: #8c8c8c; }

.file-actions { display: flex; align-items: center; flex-shrink: 0; }
</style>
