<template>
  <div class="excel-import-container">
    <el-card>
      <template #header>
        <h3>Excel批量导入</h3>
      </template>

      <!-- 步骤1：上传文件 -->
      <div v-if="currentStep === 1" class="upload-section">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :accept="'.xlsx,.xls'"
          :limit="1"
          drag
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>将Excel文件拖到此处，或<em>点击上传</em></p>
            <p class="upload-tip">支持 .xlsx 和 .xls 格式</p>
          </div>
        </el-upload>

        <div v-if="selectedFile" class="file-info">
          <el-icon><Document /></el-icon>
          <span>{{ selectedFile.name }}</span>
          <el-button link type="danger" @click="clearFile">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>

        <div class="excel-format-tips">
          <h4>Excel文件格式说明：</h4>
          <ul>
            <li>• 支持一个文件包含<strong>多条路线</strong>（推荐每周报价汇总）</li>
            <li>• 每行一条路线信息，自动识别起始地、目的地、日期等</li>
            <li>• Sheet名称建议使用日期或客户名称，方便识别</li>
            <li>• 代理商、费用信息也会自动提取</li>
          </ul>
        </div>

        <div class="ai-option">
          <el-checkbox v-model="enableAI">
            启用AI增强（提高准确率，但速度较慢）
          </el-checkbox>
          <el-tooltip content="AI会更准确地识别复杂格式，但需要更长时间" placement="top">
            <el-icon><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>

        <div class="actions">
          <el-button @click="$emit('cancel')">取消</el-button>
          <el-button 
            type="primary" 
            @click="startExtract"
            :disabled="!selectedFile"
            :loading="extracting"
          >
            {{ extracting ? '提取中...' : '开始提取' }}
          </el-button>
        </div>
      </div>

      <!-- 步骤2：显示识别结果（多条路线） -->
      <div v-else-if="currentStep === 2" class="preview-section">
        <div class="preview-header">
          <h4>识别到 {{ extractedRoutes.length }} 条路线</h4>
          <p>请核对信息，可直接编辑修改</p>
        </div>

        <!-- ✅ 新增：路线卡片列表，更直观 -->
        <div class="routes-list">
          <el-card 
            v-for="(route, index) in extractedRoutes" 
            :key="index"
            class="route-card"
            :class="{ 'route-card-editing': currentEditIndex === index }"
          >
            <template #header>
              <div class="route-card-header">
                <div class="route-title">
                  <el-tag type="primary" size="small">路线 {{ index + 1 }}</el-tag>
                  <strong>{{ route.起始地 || '未知' }}</strong>
                  <el-icon><Right /></el-icon>
                  <strong>{{ route.目的地 || '未知' }}</strong>
                  <span class="date-info">
                    {{ route.交易开始日期 }} ~ {{ route.交易结束日期 }}
                  </span>
                </div>
                <div class="route-actions">
                  <el-button 
                    link 
                    type="primary" 
                    @click="toggleEdit(index)"
                  >
                    完整编辑
                  </el-button>
                  <el-button 
                    link 
                    type="danger" 
                    @click="deleteRoute(index)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </template>

            <!-- 基本信息概览 -->
            <div class="route-summary">
              <div class="summary-item">
                <span class="label">重量：</span>
                <span class="value">{{ route.计费重量 || 0 }} kg</span>
              </div>
              <div class="summary-item">
                <span class="label">体积：</span>
                <span class="value">{{ route.总体积 || 0 }} cbm</span>
              </div>
              <div class="summary-item">
                <span class="label">货值：</span>
                <span class="value">{{ route.货值币种 || 'RMB' }} {{ route.货值 || 0 }}</span>
              </div>
              <div class="summary-item">
                <span class="label">代理商：</span>
                <span class="value">{{ getAgentNames(route.agents) }}</span>
              </div>
            </div>
          </el-card>
        </div>

        <div class="preview-actions">
          <el-button @click="backToUpload">重新上传</el-button>
          <el-button 
            type="primary" 
            @click="saveAll"
            :loading="saving"
          >
            保存全部 {{ extractedRoutes.length }} 条路线
          </el-button>
        </div>
      </div>

      <!-- 进度提示 -->
      <el-progress 
        v-if="extracting" 
        :percentage="progress" 
        :status="progress === 100 ? 'success' : 'active'"
      />
    </el-card>

    <!-- ✅ 步骤3：完整编辑某条路线 -->
    <div v-if="currentStep === 3" class="excel-edit-page">
      <div class="excel-edit-header">
        <el-button @click="cancelEdit" :icon="ArrowLeft">返回列表</el-button>
        <span class="edit-tip">正在编辑第 {{ currentEditIndex + 1 }} 条路线 · 保存修改后返回列表统一提交</span>
      </div>
      <ManualInput
        :key="'excel-edit-' + currentEditIndex"
        :initial-data="currentEditRoute"
        :local-edit-mode="true"
        @local-save="handleLocalSave"
        @cancel="cancelEdit"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadAndExtractExcel, createRoute } from '@/api/route'
import { UploadFilled, Document, Delete, QuestionFilled, Right, ArrowLeft } from '@element-plus/icons-vue'
import ManualInput from './ManualInput.vue'

const emit = defineEmits(['success', 'cancel'])

const currentStep = ref(1)
const selectedFile = ref(null)
const enableAI = ref(false)
const extracting = ref(false)
const saving = ref(false)
const progress = ref(0)
const extractedRoutes = ref([])
const currentEditRoute = ref(null)
const currentEditIndex = ref(-1)

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file
}

// 清除文件
const clearFile = () => {
  selectedFile.value = null
}

// 开始提取
const startExtract = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  extracting.value = true
  progress.value = 0

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value.raw)
    formData.append('enable_llm', enableAI.value)

    // 模拟进度
    const interval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += 10
      }
    }, 500)

    const result = await uploadAndExtractExcel(formData)
    
    clearInterval(interval)
    progress.value = 100

    // ✅ 处理多条路线结果
    if (result.data && result.data.routes) {
      console.log('========== Excel提取数据 ==========')
      console.log('routes数量:', result.data.routes.length)
      console.log('第一条路线数据:', result.data.routes[0])
      console.log('goods_details:', result.data.goods_details)
      console.log('agents:', result.data.agents)
      console.log('===================================')
      
      extractedRoutes.value = result.data.routes.map((route, index) => ({
        ...route,
        // 字段名标准化（后端输出带单位后缀，统一转为无后缀）
        实际重量: route['实际重量(/kg)'] ?? route.实际重量 ?? 0,
        计费重量: route['计费重量(/kg)'] ?? route.计费重量 ?? 0,
        总体积:   route['总体积(/cbm)'] ?? route.总体积   ?? 0,
        _index: index,
        // 关联货物和代理商数据
        goods_details: result.data.goods_details?.filter(g => g.路线索引 === index) || [],
        agents: result.data.agents?.filter(a => a.路线索引 === index) || []
      }))
      
      console.log('========== 组装后的extractedRoutes ==========')
      console.log('第一条路线:', extractedRoutes.value[0])
      console.log('===========================================')
      
      if (extractedRoutes.value.length === 0) {
        ElMessage.warning('未识别到路线信息，请检查Excel格式')
        return
      }

      ElMessage.success(`成功识别 ${extractedRoutes.value.length} 条路线`)
      currentStep.value = 2
    } else {
      ElMessage.error('数据提取失败，请检查Excel格式')
    }
  } catch (error) {
    ElMessage.error(error.message || '提取失败')
  } finally {
    extracting.value = false
  }
}

// 获取代理商名称列表
const getAgentNames = (agents) => {
  if (!agents || agents.length === 0) return '无'
  return agents.map(a => a.代理商).join('、')
}

// ✅ 进入完整编辑页（step 3）
const toggleEdit = (index) => {
  currentEditIndex.value = index
  currentEditRoute.value = JSON.parse(JSON.stringify(extractedRoutes.value[index]))
  currentStep.value = 3
}

// ✅ ManualInput 本地保存回调：把数据写回列表，返回步骤2
const handleLocalSave = (submitData) => {
  console.log('=== handleLocalSave 收到数据 ===')
  console.log('submitData.agents:', JSON.stringify(submitData.agents, null, 2))
  console.log('submitData.goods_details:', JSON.stringify(submitData.goods_details, null, 2))
  console.log('===============================')
  const original = extractedRoutes.value[currentEditIndex.value]
  extractedRoutes.value[currentEditIndex.value] = {
    ...original,
    起始地: submitData.route?.起始地 ?? original.起始地,
    途径地: submitData.route?.途径地 ?? original.途径地,
    目的地: submitData.route?.目的地 ?? original.目的地,
    交易开始日期: submitData.route?.交易开始日期 ?? original.交易开始日期,
    交易结束日期: submitData.route?.交易结束日期 ?? original.交易结束日期,
    实际重量: submitData.route?.实际重量 ?? original.实际重量,
    计费重量: submitData.route?.计费重量 ?? original.计费重量,
    总体积: submitData.route?.总体积 ?? original.总体积,
    货值: submitData.route?.货值 ?? original.货值,
    agents: submitData.agents || original.agents || [],
    goods_details: submitData.goods_details || original.goods_details || [],
    goods_total: submitData.goods_total || original.goods_total || []
  }
  currentStep.value = 2
}

// ✅ 取消编辑，返回列表
const cancelEdit = () => {
  currentStep.value = 2
  currentEditRoute.value = null
}

// 删除路线
const deleteRoute = (index) => {
  extractedRoutes.value.splice(index, 1)
  ElMessage.success('已删除')
}

// 返回上传
const backToUpload = () => {
  currentStep.value = 1
  extractedRoutes.value = []
  selectedFile.value = null
}

// 保存所有路线
const saveAll = async () => {
  if (extractedRoutes.value.length === 0) {
    ElMessage.warning('没有可保存的路线')
    return
  }

  saving.value = true
  
  try {
    // ✅ 批量保存多条路线
    let successCount = 0
    let failCount = 0

    for (const route of extractedRoutes.value) {
      try {
        const cleanAgents = (route.agents || []).map(a => ({
          代理商: a.代理商 || '',
          运输方式: a.运输方式 || '',
          贸易类型: a.贸易类型 || '',
          时效: a.时效 || '',
          时效备注: a.时效备注 || '',
          不含: a.不含 || '',
          是否赔付: a.是否赔付 || '0',
          赔付内容: a.赔付内容 || '',
          代理备注: a.代理备注 || '',
          fee_items: a.fee_items || [],
          fee_total: a.fee_total || [],
          summary: a.summary || {}
        }))
        const submitData = {
          route: {
            起始地: route.起始地 || '',
            途径地: route.途径地 || '',
            目的地: route.目的地 || '',
            交易开始日期: route.交易开始日期 || '',
            交易结束日期: route.交易结束日期 || '',
            实际重量: route.实际重量 || 0,
            计费重量: route.计费重量 || 0,
            总体积: route.总体积 || 0,
            货值: route.货值 || 0
          },
          goods_details: route.goods_details || [],
          goods_total: route.goods_total || [],
          agents: cleanAgents
        }
        
        console.log(`=== 保存路线 ${route.起始地}→${route.目的地} ===`)
        console.log('agents数量:', submitData.agents.length)
        console.log('agents详情:', JSON.stringify(submitData.agents, null, 2))
        console.log('goods_details数量:', submitData.goods_details.length)
        await createRoute(submitData)
        successCount++
      } catch (error) {
        failCount++
        console.error(`路线 ${route.起始地}-${route.目的地} 保存失败:`, error)
      }
    }

    if (failCount === 0) {
      ElMessage.success(`成功导入 ${successCount} 条路线`)
      emit('success')
    } else {
      ElMessage.warning(`成功 ${successCount} 条，失败 ${failCount} 条`)
    }
  } catch (error) {
    ElMessage.error('批量保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.excel-import-container {
  padding: 20px;
}

.upload-section {
  padding: 20px;
}

.upload-icon {
  font-size: 60px;
  color: #409EFF;
}

.upload-text {
  margin-top: 16px;
}

.upload-text p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.excel-format-tips {
  margin-top: 24px;
  padding: 16px;
  background: #fff7e6;
  border-left: 4px solid #faad14;
  border-radius: 4px;
}

.excel-format-tips h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.excel-format-tips ul {
  margin: 0;
  padding-left: 20px;
  list-style: none;
}

.excel-format-tips li {
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.6;
}

.ai-option {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

/* ✅ 路线卡片样式 */
.preview-header {
  margin-bottom: 20px;
}

.preview-header h4 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.preview-header p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.routes-list {
  max-height: 600px;
  overflow-y: auto;
  margin-bottom: 20px;
}

.route-card {
  margin-bottom: 16px;
}

.route-card-editing {
  border-color: #409EFF;
}

.route-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.route-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.route-title strong {
  font-size: 16px;
}

.date-info {
  font-size: 13px;
  color: #909399;
  margin-left: auto;
}

.route-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-item .label {
  font-size: 12px;
  color: #909399;
}

.summary-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.route-edit-form {
  margin-top: 16px;
}

.preview-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

/* ✅ Excel 编辑页样式 */
.excel-edit-page {
  padding: 0;
}

.excel-edit-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  margin-bottom: 16px;
  background: #fff7e6;
  border-left: 4px solid #faad14;
  border-radius: 4px;
}

.edit-tip {
  font-size: 14px;
  color: #8c6914;
}
</style>