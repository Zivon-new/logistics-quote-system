<template>
  <div class="attachment-panel">
    <!-- 上传区（只读模式隐藏） -->
    <div v-if="!readonly" class="upload-area">
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

    <!-- 附件表格 -->
    <table v-if="attachments.length" class="attachment-table">
      <thead>
        <tr>
          <th>内容</th>
          <th>日期</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in attachments" :key="item.attachment_id">
          <td class="file-cell">
            <img
              v-if="item.file_type === 'image' && thumbUrls[item.attachment_id]"
              :src="thumbUrls[item.attachment_id]"
              class="file-thumb"
            />
            <span v-else class="file-icon" v-html="typeIcon(item.file_type)" />
            <span class="file-name" :title="item.original_name">{{ item.original_name }}</span>
          </td>
          <td class="date-cell">{{ item.upload_time?.slice(0, 16) }}</td>
          <td class="action-cell">
            <el-button link size="small" type="primary" @click="previewFile(item)">预览</el-button>
            <el-button link size="small" type="primary" @click="downloadFile(item)">下载</el-button>
            <el-popconfirm
              v-if="!readonly"
              title="确认删除这个附件？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm="handleDelete(item)"
            >
              <template #reference>
                <el-button link size="small" type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </td>
        </tr>
      </tbody>
    </table>

    <el-empty v-else-if="!loading" description="暂无附件" :image-size="48" />

    <!-- 图片预览 -->
    <el-image-viewer
      v-if="imageViewerVisible"
      :url-list="[previewUrl]"
      @close="closeImageViewer"
    />

    <!-- Word / Excel 预览弹窗 -->
    <el-dialog
      v-model="docDialogVisible"
      :title="docDialogTitle"
      width="80%"
      top="5vh"
      destroy-on-close
    >
      <!-- Excel 多 Sheet 标签 -->
      <div v-if="excelSheets.length > 1" class="sheet-tabs">
        <button
          v-for="(sheet, i) in excelSheets"
          :key="sheet.name"
          :class="['sheet-tab', { active: activeSheetIndex === i }]"
          @click="activeSheetIndex = i"
        >{{ sheet.name }}</button>
      </div>
      <div class="doc-preview-body" v-html="excelSheets.length ? excelSheets[activeSheetIndex]?.html : docHtml" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import mammoth from 'mammoth'
import * as XLSX from 'xlsx'
import { uploadAttachment, listAttachments, deleteAttachment, getDownloadUrl } from '@/api/attachment'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  routeId: { type: Number, required: true },
  readonly: { type: Boolean, default: false }
})

const userStore = useUserStore()
const attachments = ref([])
const loading = ref(false)
const uploading = ref(false)
const thumbUrls = reactive({})

// 图片预览
const imageViewerVisible = ref(false)
const previewUrl = ref('')
let previewBlobUrl = ''

// Word / Excel 预览弹窗
const docDialogVisible = ref(false)
const docDialogTitle = ref('')
const docHtml = ref('')          // Word 用
const excelSheets = ref([])      // Excel 用：[{ name, html }]
const activeSheetIndex = ref(0)

// ── SVG 图标（正方形 36×36）───────────────────────────────────────
const typeIcon = (type) => {
  if (type === 'pdf') return `<svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="36" rx="4" fill="#E53935"/>
    <text x="18" y="23" font-size="11" font-weight="bold" fill="white" text-anchor="middle" font-family="Arial">PDF</text>
  </svg>`
  if (type === 'word') return `<svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="36" rx="4" fill="#1565C0"/>
    <text x="18" y="25" font-size="18" font-weight="bold" fill="white" text-anchor="middle" font-family="Arial">W</text>
  </svg>`
  if (type === 'excel') return `<svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="36" rx="4" fill="#2E7D32"/>
    <text x="18" y="23" font-size="11" font-weight="bold" fill="white" text-anchor="middle" font-family="Arial">XLS</text>
  </svg>`
  return `<svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg">
    <rect width="36" height="36" rx="4" fill="#757575"/>
    <text x="18" y="23" font-size="11" font-weight="bold" fill="white" text-anchor="middle" font-family="Arial">FILE</text>
  </svg>`
}

// ── 鉴权 fetch ────────────────────────────────────────────────────
const authFetch = async (attachmentId) => {
  const url = getDownloadUrl(attachmentId)
  const res = await fetch('/api' + url.replace('/api', ''), {
    headers: { Authorization: `Bearer ${userStore.token}` }
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.blob()
}

// ── 加载列表 ──────────────────────────────────────────────────────
const loadList = async () => {
  if (!props.routeId) return
  loading.value = true
  try {
    attachments.value = await listAttachments(props.routeId)
    attachments.value
      .filter(a => a.file_type === 'image')
      .forEach(async (a) => {
        try {
          const blob = await authFetch(a.attachment_id)
          if (thumbUrls[a.attachment_id]) URL.revokeObjectURL(thumbUrls[a.attachment_id])
          thumbUrls[a.attachment_id] = URL.createObjectURL(blob)
        } catch { /* 缩略图失败不影响列表 */ }
      })
  } finally {
    loading.value = false
  }
}

watch(() => props.routeId, loadList, { immediate: true })

// ── 上传 ──────────────────────────────────────────────────────────
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
  return false
}

// ── 删除 ──────────────────────────────────────────────────────────
const handleDelete = async (item) => {
  await deleteAttachment(item.attachment_id)
  ElMessage.success('已删除')
  if (thumbUrls[item.attachment_id]) {
    URL.revokeObjectURL(thumbUrls[item.attachment_id])
    delete thumbUrls[item.attachment_id]
  }
  attachments.value = attachments.value.filter(a => a.attachment_id !== item.attachment_id)
}

// ── 预览 ──────────────────────────────────────────────────────────
const previewFile = async (item) => {
  try {
    const blob = await authFetch(item.attachment_id)

    if (item.file_type === 'image') {
      if (previewBlobUrl) URL.revokeObjectURL(previewBlobUrl)
      previewBlobUrl = URL.createObjectURL(blob)
      previewUrl.value = previewBlobUrl
      imageViewerVisible.value = true

    } else if (item.file_type === 'pdf') {
      const blobUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.target = '_blank'
      a.rel = 'noopener'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      setTimeout(() => URL.revokeObjectURL(blobUrl), 10000)

    } else if (item.file_type === 'word') {
      const arrayBuffer = await blob.arrayBuffer()
      const result = await mammoth.convertToHtml({ arrayBuffer })
      excelSheets.value = []
      docDialogTitle.value = item.original_name
      docHtml.value = result.value
      docDialogVisible.value = true

    } else if (item.file_type === 'excel') {
      const arrayBuffer = await blob.arrayBuffer()
      const workbook = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array', cellStyles: true })
      excelSheets.value = workbook.SheetNames.map(name => {
        try {
          return { name, html: XLSX.utils.sheet_to_html(workbook.Sheets[name], { editable: false }) }
        } catch {
          // fallback：sheet_to_json → 手动拼表格
          const rows = XLSX.utils.sheet_to_json(workbook.Sheets[name], { header: 1, defval: '' })
          const trs = rows.map(row =>
            '<tr>' + row.map(cell => `<td>${cell}</td>`).join('') + '</tr>'
          ).join('')
          return { name, html: `<table>${trs}</table>` }
        }
      })
      activeSheetIndex.value = 0
      docDialogTitle.value = item.original_name
      docDialogVisible.value = true
    }
  } catch (e) {
    ElMessage.error('预览失败：' + e.message)
  }
}

const closeImageViewer = () => {
  imageViewerVisible.value = false
  if (previewBlobUrl) {
    URL.revokeObjectURL(previewBlobUrl)
    previewBlobUrl = ''
    previewUrl.value = ''
  }
}

// ── 下载 ──────────────────────────────────────────────────────────
const downloadFile = async (item) => {
  try {
    const blob = await authFetch(item.attachment_id)
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = item.original_name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(blobUrl), 10000)
  } catch (e) {
    ElMessage.error('下载失败：' + e.message)
  }
}
</script>

<style scoped>
.attachment-panel { padding: 4px 0; }

.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.upload-tip { font-size: 12px; color: #8c8c8c; }

.attachment-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.attachment-table th {
  text-align: left;
  padding: 8px 12px;
  font-weight: 600;
  color: #606266;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}
.attachment-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}
.attachment-table tr:last-child td { border-bottom: none; }
.attachment-table tr:hover td { background: #fafafa; }

.file-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.file-thumb {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
  border: 1px solid #e4e7ed;
}
.file-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  line-height: 0;
}
.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 260px;
  color: #262626;
}

.date-cell { color: #8c8c8c; white-space: nowrap; }
.action-cell { white-space: nowrap; }

/* Sheet 标签 */
.sheet-tabs {
  display: flex;
  gap: 4px;
  padding: 0 0 12px 0;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.sheet-tab {
  padding: 4px 14px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all .15s;
}
.sheet-tab:hover { border-color: #409eff; color: #409eff; }
.sheet-tab.active { background: #409eff; border-color: #409eff; color: #fff; }

/* Word / Excel 预览弹窗内容 */
.doc-preview-body {
  max-height: 70vh;
  overflow: auto;
  font-size: 14px;
  line-height: 1.6;
}
/* SheetJS 生成的表格样式 */
.doc-preview-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
}
.doc-preview-body :deep(td),
.doc-preview-body :deep(th) {
  border: 1px solid #d0d0d0;
  padding: 4px 8px;
  white-space: nowrap;
}
</style>
