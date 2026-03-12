<template>
  <div class="step1-container">
    <h3>路线基本信息</h3>
    
    <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="起始地" prop="起始地">
            <el-input 
              v-model="formData.起始地" 
              placeholder="如：深圳"
              clearable
              @input="handleInput"
            />
          </el-form-item>
        </el-col>
        
        <el-col :span="12">
          <el-form-item label="途径地" prop="途径地">
            <el-input 
              v-model="formData.途径地" 
              placeholder="可选，如：香港"
              clearable
              @input="handleInput"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="目的地" prop="目的地">
            <el-input 
              v-model="formData.目的地" 
              placeholder="如：新加坡"
              clearable
              @input="handleInput"
            />
          </el-form-item>
        </el-col>
        
        <el-col :span="12">
          <el-form-item label="交易日期" prop="dateRange">
            <el-date-picker
              v-model="formData.dateRange"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              @change="handleInput"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="实际重量" prop="实际重量">
            <!-- ✅ 修复：使用 @input 手动处理数字转换 -->
            <el-input 
              v-model="formData.实际重量"
              type="number"
              placeholder="0.00"
              clearable
              @input="handleNumberInput('实际重量', $event)"
            >
              <template #append>kg</template>
            </el-input>
          </el-form-item>
        </el-col>
        
        <el-col :span="12">
          <el-form-item label="计费重量" prop="计费重量">
            <el-input 
              v-model="formData.计费重量"
              type="number"
              placeholder="0.00"
              clearable
              @input="handleNumberInput('计费重量', $event)"
            >
              <template #append>kg</template>
            </el-input>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="总体积" prop="总体积">
            <el-input 
              v-model="formData.总体积"
              type="number"
              placeholder="0.00"
              clearable
              @input="handleNumberInput('总体积', $event)"
            >
              <template #append>cbm</template>
            </el-input>
          </el-form-item>
        </el-col>
        
        <el-col :span="12">
          <el-form-item label="货值" prop="货值">
            <el-input 
              v-model="formData.货值"
              type="number"
              placeholder="0.00"
              clearable
              @input="handleNumberInput('货值', $event)"
            >
              <template #append>¥</template>
            </el-input>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <!-- ✅ 新增：调试信息显示（仅开发环境） -->
    <div v-if="showDebug" class="debug-panel">
      <h4>🔍 调试信息</h4>
      <pre>{{ debugInfo }}</pre>
    </div>

    <div class="tips">
      <el-icon><InfoFilled /></el-icon>
      <div class="tips-content">
        <p>• 起始地和目的地为必填项</p>
        <p>• 交易日期建议选择实际业务日期范围</p>
        <p>• 计费重量用于费用自动计算（如果费用单位为/kg）</p>
        <p>• 总体积用于费用自动计算（如果费用单位为/cbm）</p>
        <p>• 货值会由系统根据货物明细自动计算，也可手动输入</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch, computed } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'validate'])

const formRef = ref(null)
const showDebug = ref(false)  // ✅ 开发时可设为 true

// ✅ 移除 isUpdatingFromProps 标志位，采用新的同步机制
const formData = reactive({
  起始地: props.modelValue.起始地 || '',
  途径地: props.modelValue.途径地 || '',
  目的地: props.modelValue.目的地 || '',
  dateRange: props.modelValue.dateRange || null,
  实际重量: props.modelValue.实际重量 || 0,
  计费重量: props.modelValue.计费重量 || 0,
  总体积: props.modelValue.总体积 || 0,
  货值: props.modelValue.货值 || 0
})

// ✅ 调试信息
const debugInfo = computed(() => {
  return {
    '当前表单值': formData,
    '实际重量类型': typeof formData.实际重量,
    '计费重量类型': typeof formData.计费重量,
    '总体积类型': typeof formData.总体积,
    '货值类型': typeof formData.货值
  }
})

const rules = {
  起始地: [
    { required: true, message: '请输入起始地', trigger: 'blur' }
  ],
  目的地: [
    { required: true, message: '请输入目的地', trigger: 'blur' }
  ],
  dateRange: [
    { 
      required: true, 
      message: '请选择交易日期', 
      trigger: 'change',
      validator: (rule, value, callback) => {
        if (!value || (Array.isArray(value) && value.length !== 2)) {
          callback(new Error('请选择交易日期'))
        } else {
          callback()
        }
      }
    }
  ]
}

// ✅ 新增：手动处理数字输入
const handleNumberInput = (field, value) => {
  console.log(`🔢 handleNumberInput: ${field} = ${value} (type: ${typeof value})`)
  
  // 转换为数字，如果是空字符串或无效值，设为0
  const numValue = value === '' || value === null ? 0 : parseFloat(value)
  
  if (!isNaN(numValue)) {
    formData[field] = numValue
    console.log(`✅ 已更新 formData.${field} = ${formData[field]} (type: ${typeof formData[field]})`)
  } else {
    console.warn(`⚠️ 无效的数字值: ${value}`)
    formData[field] = 0
  }
  
  // 触发emit
  handleInput()
}

// ✅ 通用输入处理（文本字段 + 日期）
const handleInput = () => {
  const updateData = { ...formData }
  
  // 将dateRange转换为交易开始/结束日期
  if (formData.dateRange && Array.isArray(formData.dateRange) && formData.dateRange.length === 2) {
    updateData.交易开始日期 = formData.dateRange[0]
    updateData.交易结束日期 = formData.dateRange[1]
  }
  
  console.log('📤 Step1RouteInfo emit update:modelValue:', updateData)
  emit('update:modelValue', updateData)
}

// ✅ 删除原来的 watch，不再监听 props.modelValue
// 采用显式的 populate 方法来回填数据

// 验证方法
const validate = async () => {
  try {
    await formRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

// ✅ 供父组件提交时直接读取当前表单值
const getValues = () => {
  const d = { ...formData }
  if (Array.isArray(d.dateRange) && d.dateRange.length === 2) {
    d.交易开始日期 = d.dateRange[0]
    d.交易结束日期 = d.dateRange[1]
  } else {
    d.交易开始日期 = ''
    d.交易结束日期 = ''
  }
  
  console.log('📋 Step1 getValues 返回:', d)
  return d
}

// ✅ 供父组件主动填充数据（编辑模式/Excel导入）
const populate = (data) => {
  if (!data) return
  
  console.log('📥 Step1 populate 收到数据:', data)
  
  // ✅ 逐字段赋值，确保响应式更新
  formData.起始地   = data.起始地   || ''
  formData.途径地   = data.途径地   || ''
  formData.目的地   = data.目的地   || ''
  
  // ✅ 数字字段：强制转换为数字类型
  formData.实际重量 = parseFloat(data.实际重量) || 0
  formData.计费重量 = parseFloat(data.计费重量) || 0
  formData.总体积   = parseFloat(data.总体积)   || 0
  formData.货值     = parseFloat(data.货值)     || 0
  
  if (data.交易开始日期 && data.交易结束日期) {
    formData.dateRange = [data.交易开始日期, data.交易结束日期]
  }
  
  console.log('✅ Step1 populate 完成，当前 formData:', formData)
}

defineExpose({ validate, getValues, populate })
</script>

<style scoped>
.step1-container {
  padding: 20px;
}

h3 {
  margin-bottom: 24px;
  font-size: 18px;
  font-weight: 600;
}

:deep(.el-input__inner) {
  height: 40px !important;
  font-size: 14px;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  display: none !important;
}

.tips {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  padding: 16px;
  background: #f0f9ff;
  border-left: 4px solid #1890ff;
  border-radius: 4px;
}

.tips .el-icon {
  color: #1890ff;
  font-size: 20px;
  margin-top: 2px;
}

.tips-content p {
  margin: 4px 0;
  font-size: 13px;
  color: #595959;
  line-height: 1.6;
}

/* ✅ 调试面板样式 */
.debug-panel {
  margin-top: 20px;
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
}

.debug-panel h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #856404;
}

.debug-panel pre {
  margin: 0;
  font-size: 12px;
  color: #856404;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>