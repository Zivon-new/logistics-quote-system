<template>
  <div class="new-route-container">
    <div class="page-header">
      <h2>{{ isEdit ? '编辑路线' : '新增路线' }}</h2>
      <el-button @click="goBack">返回</el-button>
    </div>

    <!-- 选择导入方式（仅新增时显示） -->
    <el-card v-if="!isEdit && !importMethod" class="method-selector">
      <h3>选择录入方式</h3>
      <div class="method-buttons">
        <el-card 
          class="method-card" 
          shadow="hover"
          @click="selectMethod('manual')"
        >
          <el-icon :size="60" color="#1890ff"><Edit /></el-icon>
          <h4>手动录入</h4>
          <p>逐步填写路线、货物、代理商信息</p>
          <p class="tip">适合单条路线录入</p>
        </el-card>

        <el-card 
          class="method-card" 
          shadow="hover"
          @click="selectMethod('excel')"
        >
          <el-icon :size="60" color="#52c41a"><Upload /></el-icon>
          <h4>Excel导入</h4>
          <p>上传Excel文件自动提取信息</p>
          <p class="tip">适合批量导入，AI辅助提取</p>
        </el-card>
      </div>
    </el-card>

    <!-- 手动录入 -->
    <ManualInput 
      v-if="importMethod === 'manual' || isEdit"
      :route-id="routeId"
      :is-edit="isEdit"
      @success="handleSuccess"
      @cancel="handleCancel"
    />

    <!-- Excel导入 -->
    <ExcelImport
      v-if="importMethod === 'excel'"
      @success="handleSuccess"
      @cancel="handleCancel"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Edit, Upload } from '@element-plus/icons-vue'
import ManualInput from './ManualInput.vue'
import ExcelImport from './ExcelImport.vue'

const route = useRoute()
const router = useRouter()

const importMethod = ref('')

// ✅ 是否为编辑模式
const isEdit = computed(() => {
  return route.name === 'EditRoute' && !!route.params.id
})

// ✅ 用 computed 同步获取 routeId，避免子组件 onMounted 时 routeId 为 null
const routeId = computed(() => route.params.id || null)

// 选择导入方式
const selectMethod = (method) => {
  importMethod.value = method
}

// 返回
const goBack = () => {
  router.push('/route-manage')
}

// 成功回调
const handleSuccess = () => {
  router.push('/route-manage')
}

// 取消回调
const handleCancel = () => {
  if (isEdit.value) {
    goBack()
  } else {
    importMethod.value = ''
  }
}
</script>

<style scoped>
.new-route-container {
  padding: 20px;
  min-height: calc(100vh - 80px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.method-selector {
  max-width: 900px;
  margin: 40px auto;
}

.method-selector h3 {
  text-align: center;
  font-size: 20px;
  margin-bottom: 30px;
}

.method-buttons {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  padding: 20px;
}

.method-card {
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.method-card:hover {
  border-color: #1890ff;
  transform: translateY(-4px);
}

.method-card h4 {
  margin: 16px 0 8px;
  font-size: 18px;
  font-weight: 600;
}

.method-card p {
  margin: 8px 0;
  color: #595959;
  font-size: 14px;
}

.method-card .tip {
  color: #8c8c8c;
  font-size: 12px;
  margin-top: 12px;
}
</style>