<template>
  <div class="manual-input-container">
    <el-card>
      <!-- 步骤条 -->
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="路线信息" />
        <el-step title="货物信息" />
        <el-step title="代理商及费用" />
        <el-step title="预览确认" />
      </el-steps>

      <div class="step-content">
        <!-- Step 1: 路线信息 -->
        <Step1RouteInfo
          v-show="currentStep === 0"
          ref="step1Ref"
          :model-value="formData.route"
          @update:model-value="onRouteUpdate"
        />

        <!-- Step 2: 货物信息 -->
        <Step2GoodsInfo
          v-show="currentStep === 1"
          ref="step2Ref"
          v-model:goodsDetails="formData.goodsDetails"
          v-model:goodsTotal="formData.goodsTotal"
          :route-weight="formData.route.实际重量"
          :route-volume="formData.route.总体积"
          :route-value="formData.route.货值"
        />

        <!-- Step 3: 代理商及费用 -->
        <Step3AgentsForm
          v-show="currentStep === 2"
          ref="step3Ref"
          v-model="formData.agents"
          :route-weight="formData.route.计费重量"
          :route-volume="formData.route.总体积"
          :route-value="debugRouteValue"
        />

        <!-- Step 4: 预览确认 -->
        <Step4Preview
          v-show="currentStep === 3"
          :form-data="formData"
        />
      </div>

      <!-- 操作按钮 -->
      <div class="step-actions">
        <el-button v-if="currentStep > 0" @click="prevStep">上一步</el-button>
        <el-button @click="$emit('cancel')">取消</el-button>
        <el-button 
          v-if="currentStep < 3" 
          type="primary" 
          @click="nextStep"
        >
          下一步
        </el-button>
        <el-button 
          v-else 
          type="success" 
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ localEditMode ? '保存修改' : '确认提交' }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createRoute, getRouteDetail, updateRoute } from '@/api/route'
import Step1RouteInfo from './components/Step1RouteInfo.vue'
import Step2GoodsInfo from './components/Step2GoodsInfo.vue'
import Step3AgentsForm from './components/Step3AgentsForm.vue'
import Step4Preview from './components/Step4Preview.vue'

const props = defineProps({
  isEdit: {
    type: Boolean,
    default: false
  },
  routeId: {
    type: [String, Number],
    default: null
  },
  initialData: {
    type: Object,
    default: null
  },
  localEditMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['success', 'cancel', 'localSave'])

const currentStep = ref(0)
const submitting = ref(false)
const step1Ref = ref(null)
const step2Ref = ref(null)
const step3Ref = ref(null)

const formData = reactive({
  route: {
    起始地: '',
    途径地: '',
    目的地: '',
    交易开始日期: '',
    交易结束日期: '',
    实际重量: 0,
    计费重量: 0,
    总体积: 0,
    货值: 0
  },
  goodsDetails: [],
  goodsTotal: [],
  agents: [
    {
      代理商: '',
      运输方式: '',
      贸易类型: '',
      时效: '',
      时效备注: '',
      不含: '',
      是否赔付: '0',
      赔付内容: '',
      代理备注: '',
      fee_items: [],
      fee_total: [],
      summary: {
        税率: 0,
        汇损率: 0,
        备注: ''
      }
    }
  ]
})

const debugRouteValue = computed(() => {
  const value = formData.route.货值
  console.log('=== ManualInput传递货值 ===')
  console.log('原始货值:', value, '类型:', typeof value)
  console.log('转数字:', parseFloat(value))
  console.log('========================')
  return value
})

watch(() => props.initialData, (newVal) => {
  console.log('🔥🔥🔥 ManualInput收到新的initialData 🔥🔥🔥')
  console.log('新的initialData:', newVal)
  
  if (newVal) {
    formData.route.起始地 = newVal.起始地 || newVal.起点 || ''
    formData.route.途径地 = newVal.途径地 || ''
    formData.route.目的地 = newVal.目的地 || newVal.终点 || ''
    formData.route.交易开始日期 = newVal.交易开始日期 || newVal.开始日期 || ''
    formData.route.交易结束日期 = newVal.交易结束日期 || newVal.结束日期 || ''
    formData.route.实际重量 = newVal['实际重量(/kg)'] || newVal.实际重量 || newVal['实际重量_kg'] || 0
    formData.route.计费重量 = newVal['计费重量(/kg)'] || newVal.计费重量 || newVal['计费重量_kg'] || 0
    formData.route.总体积 = newVal['总体积(/cbm)'] || newVal.总体积 || newVal['总体积_cbm'] || 0
    formData.route.货值 = newVal.货值 || 0
    
    console.log('✅ ManualInput数据更新完成:', formData.route)
  }
}, { deep: true, immediate: true })

watch(() => props.routeId, async (newId) => {
  if (props.isEdit && newId && !props.initialData) {
    console.log('🔄 routeId 变化，重新加载编辑数据, routeId:', newId)
    await loadEditData(newId)
  }
})

const loadEditData = async (routeId) => {
  try {
    const res = await getRouteDetail(routeId)
    const d = (res.success && res.data) ? res.data : res

    formData.route.起始地 = d.起始地 || ''
    formData.route.途径地 = d.途径地 || ''
    formData.route.目的地 = d.目的地 || ''
    formData.route.交易开始日期 = d.交易开始日期 || ''
    formData.route.交易结束日期 = d.交易结束日期 || ''
    formData.route.实际重量 = d['实际重量(/kg)'] || d.实际重量 || 0
    formData.route.计费重量 = d['计费重量(/kg)'] || d.计费重量 || 0
    formData.route.总体积 = d['总体积(/cbm)'] || d.总体积 || 0
    formData.route.货值 = d.货值 || 0

    formData.goodsDetails = (d.goods_details || []).map(g => ({
      货物名称: g.货物名称 || '',
      是否新品: g.是否新品 ? 1 : 0,
      货物种类: g.货物种类 || '',
      数量: g.数量 || 0,
      单价: g.单价 || 0,
      币种: g.币种 || 'RMB',
      重量: g['重量(/kg)'] || g.重量 || 0,
      总重量: g['总重量(/kg)'] || g.总重量 || 0,
      总价: g.总价 || 0,
      备注: g.备注 || ''
    }))

    formData.goodsTotal = (d.goods_total || []).map(g => ({
      货物名称: g.货物名称 || '',
      实际重量: g['实际重量(/kg)'] || g.实际重量 || 0,
      货值: g.货值 || 0,
      总体积: g['总体积(/cbm)'] || g.总体积 || 0,
      备注: g.备注 || ''
    }))

    formData.agents = (d.agents || []).map(a => ({
      代理商: a.代理商 || '',
      运输方式: a.运输方式 || '',
      贸易类型: a.贸易类型 || '',
      时效: a.时效 || '',
      时效备注: a.时效备注 || '',
      不含: a.不含 || '',
      是否赔付: String(a.是否赔付 ?? '0'),
      赔付内容: a.赔付内容 || '',
      代理备注: a.代理备注 || '',
      fee_items: a.fee_items || [],
      fee_total: a.fee_total || [],
      summary: a.summary || { 税率: 0, 汇损率: 0, 备注: '' }
    }))

    await nextTick()
    if (step1Ref.value?.populate) {
      step1Ref.value.populate(formData.route)
    }
    console.log('✅ 编辑数据加载完成, routeId:', routeId)
  } catch (error) {
    console.error('❌ 加载路线数据失败:', error)
    ElMessage.error('加载路线数据失败')
  }
}

onMounted(async () => {
  console.log('========== ManualInput onMounted ==========')
  console.log('props.initialData:', props.initialData)
  console.log('props.isEdit:', props.isEdit)
  console.log('props.routeId:', props.routeId)
  console.log('==========================================')
  
  if (props.initialData) {
    console.log('📝 使用initialData填充表单')
    console.log('initialData完整内容:', JSON.stringify(props.initialData, null, 2))
    
    await nextTick()
    
    formData.route.起始地 = props.initialData.起始地 || props.initialData.起点 || ''
    formData.route.途径地 = props.initialData.途径地 || ''
    formData.route.目的地 = props.initialData.目的地 || props.initialData.终点 || ''
    formData.route.交易开始日期 = props.initialData.交易开始日期 || props.initialData.开始日期 || ''
    formData.route.交易结束日期 = props.initialData.交易结束日期 || props.initialData.结束日期 || ''
    formData.route.实际重量 = props.initialData['实际重量(/kg)'] || props.initialData.实际重量 || props.initialData['实际重量_kg'] || 0
    formData.route.计费重量 = props.initialData['计费重量(/kg)'] || props.initialData.计费重量 || props.initialData['计费重量_kg'] || 0
    formData.route.总体积 = props.initialData['总体积(/cbm)'] || props.initialData.总体积 || props.initialData['总体积_cbm'] || 0
    formData.route.货值 = props.initialData.货值 || 0
    
    console.log('✅ 路线基本信息填充完成:', formData.route)
    
    await nextTick()
    console.log('✅✅ nextTick后，formData.route:', formData.route)
    
    if (props.initialData.goods_details) {
      formData.goodsDetails = props.initialData.goods_details.map(g => ({
        货物名称: g.货物名称 || '',
        是否新品: g.是否新品 ? 1 : 0,
        货物种类: g.货物种类 || '',
        数量: g.数量 || 0,
        单价: g.单价 || 0,
        币种: g.币种 || 'RMB',
        重量: g['重量(/kg)'] || 0,
        总重量: g['总重量(/kg)'] || 0,
        总价: g.总价 || 0,
        备注: g.备注 || ''
      }))
    }
    
    if (props.initialData.goods_total) {
      formData.goodsTotal = props.initialData.goods_total.map(g => ({
        货物名称: g.货物名称 || '',
        实际重量: g['实际重量(/kg)'] || 0,
        货值: g.货值 || 0,
        总体积: g['总体积(/cbm)'] || 0,
        备注: g.备注 || ''
      }))
    }
    
    if (props.initialData.agents && props.initialData.agents.length > 0) {
      formData.agents = props.initialData.agents.map(a => ({
        代理商: a.代理商 || '',
        运输方式: a.运输方式 || '',
        贸易类型: a.贸易类型 || '',
        时效: a.时效 || '',
        时效备注: a.时效备注 || '',
        不含: a.不含 || '',
        是否赔付: String(a.是否赔付 ?? '0'),
        赔付内容: a.赔付内容 || '',
        代理备注: a.代理备注 || '',
        fee_items: a.fee_items || [],
        fee_total: a.fee_total || [],
        summary: a.summary || {
          税率: 0,
          汇损率: 0,
          备注: ''
        }
      }))
    }
    
    console.log('✅ 表单数据填充完成:', formData)
    await nextTick()
    if (step1Ref.value?.populate) {
      step1Ref.value.populate(formData.route)
    }
  } 
  else if (props.isEdit && props.routeId) {
    await loadEditData(props.routeId)
  }
})

const nextStep = async () => {
  try {
    if (currentStep.value === 0 && step1Ref.value) {
      const valid = await step1Ref.value.validate()
      if (!valid) return
    }
    
    if (currentStep.value === 1 && step2Ref.value) {
      const valid = await step2Ref.value.validate()
      if (!valid) return
    }
    
    if (currentStep.value === 2 && step3Ref.value) {
      const valid = await step3Ref.value.validate()
      if (!valid) return
    }
    
    currentStep.value++
  } catch (error) {
    console.error('验证失败:', error)
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const onRouteUpdate = (val) => {
  if (!val) return
  formData.route.起始地 = val.起始地 ?? formData.route.起始地
  formData.route.途径地 = val.途径地 ?? formData.route.途径地
  formData.route.目的地 = val.目的地 ?? formData.route.目的地
  formData.route.交易开始日期 = val.交易开始日期 ?? formData.route.交易开始日期
  formData.route.交易结束日期 = val.交易结束日期 ?? formData.route.交易结束日期
  if (val.实际重量 !== undefined) formData.route.实际重量 = val.实际重量
  if (val.计费重量 !== undefined) formData.route.计费重量 = val.计费重量
  if (val.总体积 !== undefined) formData.route.总体积 = val.总体积
  if (val.货值 !== undefined) formData.route.货值 = val.货值
}

const handleSubmit = async () => {
  if (submitting.value) {
    console.warn('⚠️ 正在提交中，忽略重复点击')
    return
  }
  
  submitting.value = true
  
  try {
    console.log('========== 🔥 提交前完整诊断 🔥 ==========')
    console.log('📍 当前模式:', {
      'isEdit': props.isEdit,
      'routeId': props.routeId,
      'localEditMode': props.localEditMode
    })
    console.log('📍 agents数量:', formData.agents.length)
    
    // ✅ 核心修复：无条件从Step1读取值，强制数字转换
    console.log('📋 BEFORE getValues - formData.route:', JSON.stringify(formData.route))
    
    if (step1Ref.value?.getValues) {
      const s1 = step1Ref.value.getValues()
      console.log('📋 step1Ref.getValues() 返回:', s1)
      
      // ✅ 关键改动：无条件覆盖，强制转换为数字
      formData.route.实际重量 = Number(s1.实际重量 ?? 0)
      formData.route.计费重量 = Number(s1.计费重量 ?? 0)
      formData.route.总体积   = Number(s1.总体积   ?? 0)
      formData.route.货值     = Number(s1.货值     ?? 0)
      formData.route.交易开始日期 = s1.交易开始日期 || ''
      formData.route.交易结束日期 = s1.交易结束日期 || ''
      
      console.log('✅ 已从 step1 强制更新 formData.route')
      console.log('📋 AFTER getValues - formData.route:', JSON.stringify(formData.route))
    } else {
      console.error('❌ step1Ref.value.getValues 不存在！')
    }

    // ✅ pickNum：优先使用route的值（用户在Step1填的）
    const gt0 = formData.goodsTotal[0] || {}
    const pickNum = (routeVal, goodsVal, fieldName) => {
      const a = Number(routeVal ?? 0)
      const b = Number(goodsVal ?? 0)
      
      console.log(`  🔢 pickNum(${fieldName}): route=${a}, goods=${b}`)
      
      // 优先用route的值
      if (a !== 0) {
        console.log(`    → 选择 route: ${a}`)
        return a
      }
      if (b !== 0) {
        console.log(`    → 选择 goods: ${b}`)
        return b
      }
      
      console.log(`    → 都为0，返回 0`)
      return 0
    }
    
    const cleanRoute = {
      起始地:       formData.route.起始地 || '',
      途径地:       formData.route.途径地 || '',
      目的地:       formData.route.目的地 || '',
      交易开始日期: formData.route.交易开始日期 || '',
      交易结束日期: formData.route.交易结束日期 || '',
      实际重量: pickNum(formData.route.实际重量, gt0.实际重量, '实际重量'),
      计费重量: pickNum(formData.route.计费重量, gt0.计费重量, '计费重量'),
      总体积:   pickNum(formData.route.总体积,   gt0.总体积,   '总体积'),
      货值:     pickNum(formData.route.货值,     gt0.货值,     '货值')
    }
    console.log('📦 cleanRoute:', JSON.stringify(cleanRoute))
    
    // ✅ 清理agents数据
    let cleanAgents = formData.agents
      .filter((agent, index) => {
        const hasAgentName = agent.代理商 && agent.代理商.trim() !== ''
        if (!hasAgentName) {
          console.warn(`⚠️ 跳过空代理商 (index: ${index})`)
        }
        return hasAgentName
      })
      .map(agent => {
      const cleanAgent = {
        代理商: agent.代理商 || '',
        运输方式: agent.运输方式 || '',
        贸易类型: agent.贸易类型 || '',
        时效: agent.时效 || '',
        时效备注: agent.时效备注 || '',
        不含: agent.不含 || '',
        是否赔付: String(agent.是否赔付 ?? '0'),
        赔付内容: agent.赔付内容 || '',
        代理备注: agent.代理备注 || '',
        fee_items: [],
        fee_total: [],
        summary: {}
      }
      
      if (agent.fee_items && Array.isArray(agent.fee_items) && agent.fee_items.length > 0) {
        cleanAgent.fee_items = agent.fee_items.map(item => ({
          费用类型: item.费用类型 || '',
          单价: Number(item.单价) || 0,
          单位: item.单位 || '',
          数量: Number(item.数量) || 0,
          币种: item.币种 || 'RMB',
          原币金额: Number(item.原币金额) || 0,
          人民币金额: Number(item.人民币金额) || 0,
          备注: item.备注 || ''
        }))
      }
      
      if (agent.fee_total && Array.isArray(agent.fee_total) && agent.fee_total.length > 0) {
        cleanAgent.fee_total = agent.fee_total.map(total => ({
          费用名称: total.费用名称 || '',
          原币金额: Number(total.原币金额) || 0,
          币种: total.币种 || 'RMB',
          人民币金额: Number(total.人民币金额) || 0,
          备注: total.备注 || ''
        }))
      }
      
      if (agent.summary && typeof agent.summary === 'object' && Object.keys(agent.summary).length > 0) {
        cleanAgent.summary = {
          小计: Number(agent.summary.小计) || 0,
          税率: Number(agent.summary.税率) || 0,
          税金: Number(agent.summary.税金) || 0,
          汇损率: Number(agent.summary.汇损率) || 0,
          汇损: Number(agent.summary.汇损) || 0,
          总计: Number(agent.summary.总计) || 0,
          备注: agent.summary.备注 || ''
        }
      }
      
      return cleanAgent
    })
    
    // ✅ 代理商去重
    const agentMap = new Map()
    cleanAgents.forEach(agent => {
      if (agentMap.has(agent.代理商)) {
        const existing = agentMap.get(agent.代理商)
        if (props.localEditMode) {
          const hasFeeData = (a) => (a.fee_items && a.fee_items.length > 0) ||
                                    (a.fee_total && a.fee_total.length > 0) ||
                                    (a.summary && Object.keys(a.summary).length > 0 && a.summary.总计)
          if (hasFeeData(agent) && !hasFeeData(existing)) {
            agentMap.set(agent.代理商, agent)
          } else if (hasFeeData(agent) && hasFeeData(existing)) {
            const merged = { ...agent }
            merged.fee_items = [...(existing.fee_items || []), ...(agent.fee_items || [])]
            merged.fee_total = [...(existing.fee_total || []), ...(agent.fee_total || [])]
            agentMap.set(agent.代理商, merged)
          }
        } else {
          agentMap.set(agent.代理商, agent)
        }
      } else {
        agentMap.set(agent.代理商, agent)
      }
    })
    const uniqueAgents = Array.from(agentMap.values())
    
    console.log('✅ 去重前agents数量:', cleanAgents.length)
    console.log('✅ 去重后agents数量:', uniqueAgents.length)
    
    cleanAgents = uniqueAgents
    
    if (cleanAgents.length > 1) {
      console.warn('⚠️⚠️ 检测到多个代理商！', cleanAgents)
      const confirmed = confirm(`检测到 ${cleanAgents.length} 个代理商，是否继续提交？\n\n代理商列表：\n${cleanAgents.map((a, i) => `${i+1}. ${a.代理商}`).join('\n')}`)
      if (!confirmed) {
        submitting.value = false
        return
      }
    }
    
    // ✅ 清理goods_details数据
    const cleanGoodsDetails = formData.goodsDetails.map(goods => ({
      货物名称: goods.货物名称 || '',
      是否新品: goods.是否新品 ? 1 : 0,
      货物种类: goods.货物种类 || '',
      数量: goods.数量 || 0,
      单价: goods.单价 || 0,
      币种: goods.币种 || 'RMB',
      重量: goods['重量'] || goods['重量(/kg)'] || 0,
      总重量: goods['总重量'] || goods['总重量(/kg)'] || 0,
      总价: goods.总价 || 0,
      备注: goods.备注 || ''
    }))
    
    // ✅ 清理goods_total数据
    const cleanGoodsTotal = formData.goodsTotal.map(goods => ({
      货物名称: goods.货物名称 || '',
      实际重量: goods['实际重量'] || goods['实际重量(/kg)'] || 0,
      货值: goods.货值 || 0,
      总体积: goods['总体积'] || goods['总体积(/cbm)'] || 0,
      备注: goods.备注 || ''
    }))
    
    const submitData = {
      route: cleanRoute,
      goods_details: cleanGoodsDetails,
      goods_total: cleanGoodsTotal,
      agents: cleanAgents,
      _requestId: Date.now() + '-' + Math.random().toString(36).substr(2, 9)
    }
    
    console.log('🚀 最终提交数据:', submitData)
    console.log('🔑 请求ID:', submitData._requestId)
    console.log('📦 route:', JSON.stringify(cleanRoute, null, 2))
    console.log('📦 agents:', JSON.stringify(cleanAgents, null, 2))
    console.log('==========================================')

    if (props.localEditMode) {
      emit('localSave', submitData)
      ElMessage.success('修改已保存，可继续编辑其他路线')
      return
    }

    if (props.isEdit) {
      console.log('📤 调用 updateRoute, routeId:', props.routeId)
      const res = await updateRoute(props.routeId, submitData)
      console.log('✅ updateRoute 返回:', res)
      ElMessage.success('路线更新成功')
    } else {
      console.log('📤 调用 createRoute（新建）')
      await createRoute(submitData)
      ElMessage.success('路线创建成功')
    }
    
    emit('success')
  } catch (error) {
    console.error('❌ 提交失败:', error)
    console.error('❌ 错误详情:', error.response?.data)
    
    let errorMessage = '提交失败'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.manual-input-container {
  padding: 20px;
}

.step-content {
  margin: 40px 0;
  min-height: 400px;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}
</style>