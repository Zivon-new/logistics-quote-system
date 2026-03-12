<template>
  <!-- ✅ 全屏抽屉，替代小浮窗 -->
  <el-drawer
    v-model="drawerVisible"
    :title="title"
    direction="rtl"
    size="85%"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleClose"
  >
    <div class="edit-drawer-body">
      <ManualInput
        ref="manualInputRef"
        :key="'edit-' + (routeData?.路线ID)"
        :is-edit="true"
        :route-id="routeData?.路线ID"
        :initial-data="null"
        @success="handleManualSuccess"
        @cancel="handleClose"
      />
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import ManualInput from '../ManualInput.vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  routeData: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'edit'
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'cancel'])

const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const title = computed(() => {
  const origin = props.routeData?.起始地 || '未知'
  const dest = props.routeData?.目的地 || '未知'
  return `编辑路线：${origin} → ${dest}`
})

const manualInputRef = ref(null)

// ✅ ManualInput 自带"确认提交"按钮，提交成功后 emit success
// 不再需要额外的"保存修改"按钮，避免双按钮冲突
const handleManualSuccess = () => {
  emit('success')
  drawerVisible.value = false
}

const handleClose = () => {
  emit('cancel')
  drawerVisible.value = false
}
</script>

<style scoped>
.edit-drawer-body {
  height: 100%;
  overflow-y: auto;
}

/* 隐藏 drawer 默认的 footer，让 ManualInput 自己的按钮作为操作区 */
:deep(.el-drawer__footer) {
  display: none;
}
</style>