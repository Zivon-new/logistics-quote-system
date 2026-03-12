<template>
  <div class="step2-container">
    <h3 class="step-title">货物信息</h3>

    <!-- 选择录入方式 -->
    <el-radio-group v-model="inputMode" class="input-mode-selector">
      <el-radio-button label="details">货物明细（多种货物）</el-radio-button>
      <el-radio-button label="total">整单货物（单一货物）</el-radio-button>
    </el-radio-group>

    <!-- ==================== 货物明细模式 ==================== -->
    <div v-show="inputMode === 'details'" class="goods-section">
      <div class="section-header">
        <h4>货物明细</h4>
        <el-button type="primary" :icon="Plus" size="small" @click="addGoodsDetail">添加货物</el-button>
      </div>

      <el-table :data="goodsDetails" border stripe class="goods-table" v-if="goodsDetails.length > 0">
        <el-table-column label="货物名称" min-width="140">
          <template #default="scope">
            <el-input v-model="scope.row.货物名称" placeholder="如：Nokia 7750" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="货物种类" width="100">
          <template #default="scope">
            <el-input v-model="scope.row.货物种类" placeholder="如：网络设备" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="是否新品" width="100" align="center">
          <template #default="scope">
            <el-radio-group v-model="scope.row.是否新品" size="small">
              <el-radio :label="1">是</el-radio>
              <el-radio :label="0">否</el-radio>
            </el-radio-group>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="scope">
            <el-input-number :controls="false" v-model="scope.row.数量" :min="0" :precision="0" size="small" style="width: 100%;" @change="calcDetailAuto(scope.row)" />
          </template>
        </el-table-column>
        <el-table-column label="单价" width="110">
          <template #default="scope">
            <el-input-number :controls="false" v-model="scope.row.单价" :min="0" :precision="2" size="small" style="width: 100%;" @change="calcDetailAuto(scope.row)" />
          </template>
        </el-table-column>
        <el-table-column label="币种" width="85">
          <template #default="scope">
            <el-select v-model="scope.row.币种" size="small" style="width: 100%;">
              <el-option label="RMB" value="RMB" />
              <el-option label="USD" value="USD" />
              <el-option label="SGD" value="SGD" />
              <el-option label="EUR" value="EUR" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="重量(kg)" width="110">
          <template #default="scope">
            <el-input-number :controls="false" v-model="scope.row.重量" :min="0" :precision="2" size="small" style="width: 100%;" @change="calcDetailAuto(scope.row)" />
          </template>
        </el-table-column>
        <el-table-column label="总重量(kg)" width="120">
          <template #default="scope">
            <el-input-number :controls="false" v-model="scope.row.总重量" :min="0" :precision="2" size="small" style="width: 100%;" />
          </template>
        </el-table-column>
        <el-table-column label="总价(¥)" width="120">
          <template #default="scope">
            <el-input-number :controls="false" v-model="scope.row.总价" :min="0" :precision="2" size="small" style="width: 100%;" />
          </template>
        </el-table-column>
        <el-table-column label="备注" width="110">
          <template #default="scope">
            <el-input v-model="scope.row.备注" placeholder="可选" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="60" align="center" fixed="right">
          <template #default="scope">
            <el-button type="danger" size="small" link @click="removeGoodsDetail(scope.$index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-else class="empty-tip">
        <el-empty description="暂无货物，点击上方按钮添加" :image-size="80" />
      </div>
    </div>

    <!-- ==================== 整单货物模式 ==================== -->
    <div v-show="inputMode === 'total'" class="goods-section">
      <div class="section-header">
        <h4>整单货物</h4>
        <el-button type="primary" :icon="Plus" size="small" @click="addGoodsTotal">添加整单货物</el-button>
      </div>

      <div v-if="goodsTotal.length > 0">
        <el-card v-for="(item, index) in goodsTotal" :key="index" class="total-card" shadow="hover">
          <template #header>
            <div class="total-card-header">
              <span>整单货物 {{ index + 1 }}</span>
              <el-button type="danger" size="small" link @click="removeGoodsTotal(index)">删除</el-button>
            </div>
          </template>
          <el-form :model="item" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="货物名称">
                  <el-input v-model="item.货物名称" placeholder="如：服务器设备" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="实际重量(kg)">
                  <el-input-number :controls="false" v-model="item.实际重量" :precision="2" :min="0" style="width: 100%;" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="货值(¥)">
                  <el-input-number :controls="false" v-model="item.货值" :precision="2" :min="0" style="width: 100%;" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="总体积(cbm)">
                  <el-input-number :controls="false" v-model="item.总体积" :precision="3" :min="0" style="width: 100%;" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="备注">
                  <el-input v-model="item.备注" placeholder="可选" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>
      </div>

      <div v-else class="empty-tip">
        <el-empty description="暂无整单货物，点击上方按钮添加" :image-size="80" />
      </div>
    </div>

    <el-alert title="提示" type="info" :closable="false" show-icon class="info-alert">
      <template #default>
        <ul style="margin: 0; padding-left: 20px;">
          <li><strong>货物明细：</strong>适合有多种不同货物的情况，每种货物单独记录</li>
          <li><strong>整单货物：</strong>适合单一货物或整批货物的情况，记录整体信息</li>
          <li>添加整单货物时，重量/货值/体积会自动从路线信息同步（可手动修改）</li>
        </ul>
      </template>
    </el-alert>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'

const props = defineProps({
  goodsDetails: { type: Array, default: () => [] },
  goodsTotal: { type: Array, default: () => [] },
  routeWeight: { type: Number, default: 0 },
  routeVolume: { type: Number, default: 0 },
  routeValue: { type: Number, default: 0 }
})

const emit = defineEmits(['update:goodsDetails', 'update:goodsTotal'])
const inputMode = ref('details')

const goodsDetails = computed({
  get: () => props.goodsDetails,
  set: (val) => emit('update:goodsDetails', val)
})

const goodsTotal = computed({
  get: () => props.goodsTotal,
  set: (val) => emit('update:goodsTotal', val)
})

// ========== 货物明细 ==========
const addGoodsDetail = () => {
  goodsDetails.value.push({
    货物名称: '', 货物种类: '', 是否新品: 1,
    数量: 1, 单价: 0, 币种: 'RMB',
    重量: 0, 总重量: 0, 总价: 0, 备注: ''
  })
}

const removeGoodsDetail = (index) => {
  goodsDetails.value.splice(index, 1)
}

const calcDetailAuto = (row) => {
  if (row.重量 && row.数量) {
    row.总重量 = parseFloat((row.重量 * row.数量).toFixed(3))
  }
  if (row.单价 && row.数量) {
    row.总价 = parseFloat((row.单价 * row.数量).toFixed(2))
  }
}

// ========== 整单货物 ==========
const addGoodsTotal = () => {
  goodsTotal.value.push({
    货物名称: '',
    实际重量: props.routeWeight || 0,
    货值: props.routeValue || 0,
    总体积: props.routeVolume || 0,
    备注: ''
  })
}

const removeGoodsTotal = (index) => {
  goodsTotal.value.splice(index, 1)
}

const validate = () => Promise.resolve(true)

defineExpose({ validate })
</script>

<style scoped>
.step2-container { max-width: 1200px; margin: 0 auto; }
.step-title { font-size: 18px; font-weight: 600; margin-bottom: 24px; padding-bottom: 12px; border-bottom: 2px solid #1890ff; }
.input-mode-selector { margin-bottom: 24px; }
.goods-section { margin-bottom: 24px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h4 { margin: 0; font-size: 16px; font-weight: 600; }
.goods-table { margin-bottom: 16px; }
.total-card { margin-bottom: 16px; }
.total-card-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; }
.empty-tip { padding: 40px 0; }
.info-alert { margin-top: 24px; }
</style>