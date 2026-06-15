<template>
  <div class="step1-container">
    <h3>路线基本信息</h3>
    
    <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px"
      @focusin="onCellFocusIn" @dblclick="onCellDblClick" @mousedown="onCellMouseDown">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="起始地" prop="起始地">
            <el-input
              ref="起始地Ref"
              v-model="formData.起始地"
              placeholder="如：深圳"
              clearable
              @input="handleInput"
              @keydown="handleStep1Keydown($event, '起始地')"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="途径地" prop="途径地">
            <el-input
              ref="途径地Ref"
              v-model="formData.途径地"
              placeholder="可选，如：香港"
              clearable
              @input="handleInput"
              @keydown="handleStep1Keydown($event, '途径地')"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="目的地" prop="目的地">
            <el-input
              ref="目的地Ref"
              v-model="formData.目的地"
              placeholder="如：新加坡"
              clearable
              @input="handleInput"
              @keydown="handleStep1Keydown($event, '目的地')"
            />
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="交易日期" prop="dateRange">
            <div ref="交易日期Ref" style="width: 100%" @keydown="handleStep1Keydown($event, '交易日期')">
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
                @visible-change="onDateRangeVisibleChange"
              />
            </div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="实际重量" prop="实际重量">
            <!-- ✅ 修复：使用 @input 手动处理数字转换 -->
            <el-input
              ref="实际重量Ref"
              v-model="formData.实际重量"
              type="number"
              placeholder="0.00"
              clearable
              @input="handleNumberInput('实际重量', $event)"
              @keydown="handleStep1Keydown($event, '实际重量')"
            >
              <template #append>kg</template>
            </el-input>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="计费重量" prop="计费重量">
            <el-input
              ref="计费重量Ref"
              v-model="formData.计费重量"
              type="number"
              placeholder="0.00"
              clearable
              @input="handleNumberInput('计费重量', $event)"
              @keydown="handleStep1Keydown($event, '计费重量')"
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
              ref="总体积Ref"
              v-model="formData.总体积"
              type="number"
              placeholder="0.00"
              clearable
              @input="handleNumberInput('总体积', $event)"
              @keydown="handleStep1Keydown($event, '总体积')"
            >
              <template #append>cbm</template>
            </el-input>
          </el-form-item>
        </el-col>

        <el-col :span="12">
          <el-form-item label="货值" prop="货值">
            <el-input
              ref="货值Ref"
              :model-value="货值Raw"
              type="text"
              placeholder="如 500000 或 600000*0.8"
              clearable
              @input="on货值Input"
              @blur="on货值Blur"
              @clear="() => { 货值Raw = ''; formData.货值 = 0; handleInput() }"
              @keydown="handleStep1Keydown($event, '货值')"
              style="width: calc(100% - 90px);"
            />
            <el-select
              ref="货值币种Ref"
              v-model="formData.货值币种"
              style="width: 100px; margin-left: 2px;"
              @change="handleInput"
              @keydown="handleStep1Keydown($event, '货值币种')"
            >
              <el-option label="RMB" value="RMB" />
              <el-option label="USD 美元" value="USD" />
              <el-option label="EUR 欧元" value="EUR" />
              <el-option label="GBP 英镑" value="GBP" />
              <el-option label="AUD 澳元" value="AUD" />
              <el-option label="CAD 加元" value="CAD" />
              <el-option label="SGD 新加坡元" value="SGD" />
              <el-option label="HKD 港元" value="HKD" />
              <el-option label="JPY 日元" value="JPY" />
              <el-option label="MYR 林吉特" value="MYR" />
            </el-select>
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
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { useGridEditMode } from '@/composables/useGridEditMode'
import { getTargetCell, LAST_CELL } from './step1GridLayout'

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
  货值: props.modelValue.货值 || 0,
  货值币种: props.modelValue.货值币种 || 'RMB'
})

// 货值字符串状态（type="text" 保留小数点中间状态）
const 货值Raw = ref(formData.货值 > 0 ? String(formData.货值) : '')

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

// 货值：允许算术表达式（如 600000*0.8），输入时只过滤明显非法字符
const on货值Input = (val) => {
  // 允许数字、小数点、运算符、括号、空格
  const filtered = val.replace(/[^\d.+\-*/() ]/g, '')
  货值Raw.value = filtered
  // 如果是纯数字，实时更新货值；否则等失焦时再求值
  const asNum = parseFloat(filtered)
  if (!isNaN(asNum) && String(asNum) === filtered.trim()) {
    formData.货值 = asNum
    handleInput()
  }
}

// 失焦时对表达式求值
const on货值Blur = () => {
  const raw = 货值Raw.value.trim()
  if (!raw) {
    formData.货值 = 0
    handleInput()
    return
  }
  try {
    // eslint-disable-next-line no-new-func
    const result = Function('"use strict"; return (' + raw + ')')()
    if (typeof result === 'number' && isFinite(result) && result >= 0) {
      formData.货值 = Math.round(result * 100) / 100
      货值Raw.value = String(formData.货值)
    } else {
      ElMessage.warning('货值计算结果无效，请检查表达式（结果须为正数）')
      货值Raw.value = formData.货值 > 0 ? String(formData.货值) : ''
    }
  } catch {
    ElMessage.warning('货值表达式格式错误，已恢复原值')
    货值Raw.value = formData.货值 > 0 ? String(formData.货值) : ''
  }
  handleInput()
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
  货值Raw.value     = data.货值 > 0 ? String(data.货值) : ''
  formData.货值币种 = data.货值币种 || 'RMB'
  
  if (data.交易开始日期 && data.交易结束日期) {
    formData.dateRange = [data.交易开始日期, data.交易结束日期]
  }
  
  console.log('✅ Step1 populate 完成，当前 formData:', formData)
}

// ========== 单元格选中态/编辑态导航（ADR-0001） ==========
const { onCellFocusIn, onCellDblClick, onCellMouseDown, handleEditTransition } = useGridEditMode()

const 起始地Ref = ref(null)
const 途径地Ref = ref(null)
const 目的地Ref = ref(null)
const 实际重量Ref = ref(null)
const 计费重量Ref = ref(null)
const 总体积Ref = ref(null)
const 货值Ref = ref(null)
const 货值币种Ref = ref(null)
const 交易日期Ref = ref(null)
const dateRangePickerOpen = ref(false)

const cellRefs = {
  起始地: 起始地Ref,
  途径地: 途径地Ref,
  目的地: 目的地Ref,
  实际重量: 实际重量Ref,
  计费重量: 计费重量Ref,
  总体积: 总体积Ref,
  货值: 货值Ref,
  货值币种: 货值币种Ref,
}

const onDateRangeVisibleChange = (visible) => {
  dateRangePickerOpen.value = visible
}

const focusStep1Cell = (cellId) => {
  if (cellId === '交易日期开始' || cellId === '交易日期结束') {
    const inputs = 交易日期Ref.value?.querySelectorAll('input')
    const input = cellId === '交易日期开始' ? inputs?.[0] : inputs?.[1]
    input?.focus()
    return
  }
  cellRefs[cellId]?.value?.focus?.()
}

const handleStep1Keydown = (e, rawCellId) => {
  let cellId = rawCellId
  if (cellId === '交易日期') {
    const inputs = [...(交易日期Ref.value?.querySelectorAll('input') || [])]
    cellId = inputs.indexOf(e.target) === 1 ? '交易日期结束' : '交易日期开始'
  }

  if (e.key === 'Tab') {
    if (cellId === LAST_CELL) e.preventDefault()
    return
  }

  // 日历面板展开时视为编辑态：方向键交给日历自身导航，仅Enter仍提交并跳格
  const isDateCell = cellId === '交易日期开始' || cellId === '交易日期结束'
  if (isDateCell && dateRangePickerOpen.value && e.key !== 'Enter') return

  if (!handleEditTransition(e)) return

  if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
    const target = getTargetCell(cellId, e.key)
    if (!target) return
    e.preventDefault()
    focusStep1Cell(target)
    return
  }

  e.preventDefault()
  const target = getTargetCell(cellId, e.key)
  if (target) focusStep1Cell(target)
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