<template>
  <div class="recommend-page">
    <!-- 页头 -->
    <div class="page-header">
      <h2>智能推荐引擎</h2>
      <p class="subtitle">基于历史报价综合打分，为您推荐最匹配的物流方案</p>
    </div>

    <!-- 搜索表单 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" label-width="70px">
        <el-row :gutter="16">
          <!-- 第一行：起始地 / 目的地 / 货物关键词 -->
          <el-col :span="5">
            <el-form-item label="起始地" required>
              <el-autocomplete
                v-model="searchForm.origin"
                :fetch-suggestions="queryOrigins"
                placeholder="如：深圳"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="5">
            <el-form-item label="目的地" required>
              <el-autocomplete
                v-model="searchForm.destination"
                :fetch-suggestions="queryDestinations"
                placeholder="如：新加坡"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="6">
            <el-form-item label="货物名称">
              <el-autocomplete
                v-model="searchForm.goods_keyword"
                :fetch-suggestions="queryGoods"
                placeholder="如：服务器（模糊匹配）"
                clearable
                style="width: 100%"
              >
                <template #suffix>
                  <el-tooltip content="输入货物关键词可筛选同类货物的历史报价，不填则返回所有货物类型" placement="top">
                    <el-icon style="cursor:help; color:#8c8c8c"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </template>
              </el-autocomplete>
            </el-form-item>
          </el-col>

          <el-col :span="4">
            <el-form-item label="运输方式">
              <el-select
                v-model="searchForm.transport_mode"
                placeholder="不限"
                clearable
                style="width: 100%"
              >
                <el-option v-for="m in options.transport_modes" :key="m" :label="m" :value="m" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="4">
            <el-form-item label=" " label-width="20px">
              <el-button
                type="primary"
                :loading="loading"
                :disabled="!searchForm.origin || !searchForm.destination"
                style="width: 100%"
                @click="handleSearch"
              >
                开始推荐
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 推荐结果区 -->
    <div v-if="result" class="result-area">

      <!-- 结果摘要栏 -->
      <div class="result-summary">
        <!-- 目的国信息 -->
        <el-card class="summary-card dest-card" shadow="never">
          <div class="summary-title">目的国物流信息</div>
          <div class="summary-body">
            <div class="info-row">
              <span class="info-label">目的地</span>
              <span class="info-val bold">{{ searchForm.destination }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">对应国家</span>
              <span class="info-val">{{ result.目的国名称 || '无LPI数据' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">LPI评分</span>
              <span class="info-val lpi-val" v-if="result.目的国LPI">
                {{ result.目的国LPI }} <small>/ 5.0</small>
              </span>
              <span class="info-val dim" v-else>暂无数据</span>
            </div>
            <div class="info-row">
              <span class="info-label">风险等级</span>
              <el-tag :type="riskTagType(result.目的国风险等级)" size="small">
                {{ result.目的国风险等级 }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <!-- 搜索条件 -->
        <el-card class="summary-card filter-card" shadow="never">
          <div class="summary-title">本次搜索条件</div>
          <div class="summary-body">
            <div class="info-row">
              <span class="info-label">航线</span>
              <span class="info-val bold">{{ searchForm.origin }} → {{ searchForm.destination }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">货物关键词</span>
              <span class="info-val">{{ searchForm.goods_keyword || '未限定' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">运输方式</span>
              <span class="info-val">{{ searchForm.transport_mode || '不限' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">匹配方案数</span>
              <span class="info-val bold blue">{{ result.total }} 条</span>
            </div>
          </div>
        </el-card>

        <!-- 排序控制 -->
        <el-card class="summary-card sort-card" shadow="never">
          <div class="summary-title">排序方式</div>
          <el-radio-group v-model="sortBy" @change="handleSortChange" class="sort-group">
            <el-radio-button value="score">综合评分</el-radio-button>
            <el-radio-button value="time">时效优先</el-radio-button>
            <el-radio-button value="price">价格优先</el-radio-button>
          </el-radio-group>
          <div class="sort-tip">
            <span v-if="sortBy === 'score'">按综合加权评分排序</span>
            <span v-else-if="sortBy === 'time'">按时效天数升序</span>
            <span v-else>按报价总价升序</span>
          </div>
        </el-card>
      </div>

      <!-- 无结果 -->
      <el-empty
        v-if="result.results.length === 0"
        description="未找到匹配的报价记录，请尝试：去掉货物限定 / 更换运输方式 / 扩大地区范围"
        :image-size="120"
      />

      <!-- 推荐卡片列表 -->
      <div v-else class="recommend-list">
        <transition-group name="card-slide">
          <div
            v-for="item in result.results"
            :key="item.代理路线ID"
            class="recommend-card"
            :class="{ 'top1': item.rank === 1, 'top3': item.rank <= 3 && item.rank > 1 }"
          >
            <!-- 排名 -->
            <div class="rank-col">
              <div class="rank-badge" :class="`rank-${Math.min(item.rank, 4)}`">
                <span v-if="item.rank <= 3">{{ ['🥇','🥈','🥉'][item.rank-1] }}</span>
                <span v-else>{{ item.rank }}</span>
              </div>
            </div>

            <!-- 代理商信息 -->
            <div class="agent-col">
              <div class="agent-name">{{ item.代理商 }}</div>
              <div class="agent-tags">
                <el-tag size="small" type="info" v-if="item.运输方式">{{ item.运输方式 }}</el-tag>
                <el-tag size="small" type="success" v-if="item.是否赔付">有赔付</el-tag>
                <el-tag size="small" type="danger" v-else>无赔付</el-tag>
              </div>
              <!-- 货物名称 -->
              <div class="goods-info" v-if="item.货物名称">
                <el-icon><Box /></el-icon>
                <span>{{ item.货物名称 }}</span>
              </div>
              <!-- 赔付内容 -->
              <div class="compensate-info" v-if="item.是否赔付 && item.赔付内容">
                <el-icon><Check /></el-icon>
                <span class="compensate-text">{{ item.赔付内容 }}</span>
              </div>
              <!-- 不含项 -->
              <div class="exclude-info" v-if="item.不含">
                <el-icon><Warning /></el-icon>
                <span class="exclude-text">不含：{{ item.不含 }}</span>
              </div>
            </div>

            <!-- 关键指标 -->
            <div class="metric-col">
              <div class="metric-item">
                <div class="metric-label">时效</div>
                <div class="metric-value time-val">
                  {{ item.时效天数 ? item.时效天数 + ' 天' : (item.时效 || '—') }}
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-label">总价 (RMB)</div>
                <div class="metric-value price-val">
                  {{ item.总价 != null ? '¥ ' + item.总价.toLocaleString() : '—' }}
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-label">单价/kg</div>
                <div class="metric-value unit-val">
                  {{ item.单价_per_kg != null ? '¥ ' + item.单价_per_kg : '—' }}
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-label">报价日期</div>
                <div class="metric-value date-val">
                  {{ item.交易开始日期 ? item.交易开始日期.slice(0, 10) : '—' }}
                </div>
              </div>
            </div>

            <!-- 评分区 -->
            <div class="score-col">
              <el-progress
                type="circle"
                :percentage="item.综合评分"
                :color="scoreColor(item.综合评分)"
                :width="72"
                :stroke-width="6"
              >
                <template #default>
                  <span class="score-num">{{ item.综合评分 }}</span>
                </template>
              </el-progress>
              <div class="score-label">综合评分</div>

              <!-- 四维条形 -->
              <div class="sub-scores">
                <div class="sub-row" v-for="dim in scoreDims(item)" :key="dim.label">
                  <span class="sub-label">{{ dim.label }}</span>
                  <el-progress
                    :percentage="dim.val"
                    :color="scoreColor(dim.val)"
                    :show-text="false"
                    :stroke-width="5"
                    style="flex:1"
                  />
                  <span class="sub-val">{{ dim.val }}</span>
                </div>
              </div>
            </div>
          </div>
        </transition-group>
      </div>

      <!-- 评分说明 -->
      <el-card class="score-explain" shadow="never">
        <div class="explain-title">评分权重说明</div>
        <div class="explain-grid">
          <div class="explain-item">
            <el-tag type="primary" size="small">时效 30%</el-tag>
            <span>历史运输天数，越短越高；无记录给60分</span>
          </div>
          <div class="explain-item">
            <el-tag type="success" size="small">价格 30%</el-tag>
            <span>历史报价总额，越低越高；无记录给60分</span>
          </div>
          <div class="explain-item">
            <el-tag type="warning" size="small">LPI 20%</el-tag>
            <span>世界银行2023年目的国物流绩效指数（1-5分）</span>
          </div>
          <div class="explain-item">
            <el-tag type="danger" size="small">信用 20%</el-tag>
            <span>代理商信用评分（1-100），未录入默认60分</span>
          </div>
        </div>
        <div class="explain-note">
          注：推荐结果基于历史数据，实际报价请联系代理商确认。货物不同价格差异可能较大，建议填写货物关键词精确筛选。
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { QuestionFilled, Box, Warning, Check } from '@element-plus/icons-vue'
import { getRecommendations, getSearchOptions } from '@/api/recommend'

const loading = ref(false)
const result = ref(null)
const sortBy = ref('score')

const searchForm = ref({
  origin: '',
  destination: '',
  goods_keyword: '',
  transport_mode: ''
})

const options = ref({
  origins: [],
  destinations: [],
  goods: [],
  transport_modes: ['海运', '空运', '铁路', '陆运', '多式联运']
})

onMounted(async () => {
  try {
    const res = await getSearchOptions()
    options.value = res
  } catch (e) {
    // 选项加载失败不影响主功能
  }
})

const queryOrigins = (q, cb) => cb(
  options.value.origins
    .filter(o => !q || o.includes(q))
    .map(o => ({ value: o }))
)

const queryDestinations = (q, cb) => cb(
  options.value.destinations
    .filter(d => !q || d.includes(q))
    .map(d => ({ value: d }))
)

const queryGoods = (q, cb) => cb(
  options.value.goods
    .filter(g => !q || g.includes(q))
    .map(g => ({ value: g }))
)

const handleSearch = async () => {
  loading.value = true
  result.value = null
  try {
    const params = {
      origin: searchForm.value.origin,
      destination: searchForm.value.destination,
      sort_by: sortBy.value
    }
    if (searchForm.value.goods_keyword) params.goods_keyword = searchForm.value.goods_keyword
    if (searchForm.value.transport_mode) params.transport_mode = searchForm.value.transport_mode
    result.value = await getRecommendations(params)
    if (result.value.total === 0) {
      ElMessage.warning('未找到匹配记录，已显示提示')
    }
  } catch (e) {
    ElMessage.error('推荐请求失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleSortChange = async () => {
  if (!result.value) return
  await handleSearch()
}

const scoreColor = (score) => {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#1890ff'
  if (score >= 40) return '#faad14'
  return '#ff4d4f'
}

const riskTagType = (level) => {
  const map = { '低': 'success', '中低': 'success', '中': 'warning', '中高': 'warning', '高': 'danger' }
  return map[level] || 'info'
}

const scoreDims = (item) => [
  { label: '时效', val: item.各项得分.时效得分 },
  { label: '价格', val: item.各项得分.价格得分 },
  { label: 'LPI', val: item.各项得分.LPI得分 },
  { label: '信用', val: item.各项得分.信用得分 },
]
</script>

<style scoped>
.recommend-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 20px; font-weight: 600; margin: 0 0 4px; color: #262626; }
.subtitle { color: #8c8c8c; font-size: 13px; margin: 0; }

/* 搜索卡片 */
.search-card { margin-bottom: 16px; border-radius: 8px; }
.search-card :deep(.el-form-item) { margin-bottom: 0; }

/* 结果摘要栏 */
.result-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.summary-card {
  flex: 1;
  min-width: 200px;
  border-radius: 8px;
}

.summary-title {
  font-size: 12px;
  font-weight: 600;
  color: #8c8c8c;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.summary-body { display: flex; flex-direction: column; gap: 6px; }

.info-row { display: flex; align-items: center; gap: 8px; }
.info-label { font-size: 12px; color: #8c8c8c; width: 72px; flex-shrink: 0; }
.info-val { font-size: 13px; color: #262626; }
.info-val.bold { font-weight: 600; }
.info-val.blue { color: #1890ff; }
.info-val.lpi-val { color: #1890ff; font-weight: 600; font-size: 15px; }
.info-val.dim { color: #bfbfbf; }

.sort-card { min-width: 220px; }
.sort-group { display: flex; flex-direction: column; gap: 0; }
.sort-tip { font-size: 12px; color: #8c8c8c; margin-top: 8px; }

/* 推荐卡片列表 */
.recommend-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }

.recommend-card {
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 16px 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.recommend-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.top1 { border-color: #ffd700; background: linear-gradient(135deg, #fffdf0 0%, #fff 60%); }
.top3 { border-color: #d6e4ff; background: linear-gradient(135deg, #f0f8ff 0%, #fff 60%); }

/* 排名列 */
.rank-col { width: 44px; flex-shrink: 0; display: flex; justify-content: center; padding-top: 4px; }
.rank-badge {
  width: 36px; height: 36px; border-radius: 50%;
  background: #f5f5f5; display: flex; align-items: center;
  justify-content: center; font-weight: 700; font-size: 14px; color: #595959;
}
.rank-1, .rank-2, .rank-3 { background: transparent; font-size: 26px; width: 36px; height: 36px; }
.rank-4 { background: #f0f0f0; }

/* 代理商列 */
.agent-col { flex: 1.2; min-width: 0; }
.agent-name { font-size: 16px; font-weight: 600; color: #262626; margin-bottom: 6px; }
.agent-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.goods-info, .exclude-info, .compensate-info {
  display: flex; align-items: flex-start; gap: 4px;
  font-size: 12px; color: #8c8c8c; margin-top: 4px;
}
.compensate-info { color: #52c41a; }
.compensate-text, .exclude-text {
  line-height: 1.4; word-break: break-all;
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden;
}
.exclude-text { color: #fa8c16; }

/* 关键指标列 */
.metric-col { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.metric-item { display: flex; align-items: center; gap: 8px; }
.metric-label { font-size: 12px; color: #8c8c8c; width: 72px; flex-shrink: 0; }
.metric-value { font-size: 13px; color: #262626; }
.time-val { font-weight: 600; color: #096dd9; }
.price-val { font-weight: 600; color: #d4380d; }
.unit-val { color: #ad6800; }
.date-val { color: #8c8c8c; }

/* 评分列 */
.score-col { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 200px; }
.score-num { font-size: 16px; font-weight: 700; }
.score-label { font-size: 12px; color: #8c8c8c; }

.sub-scores { width: 100%; display: flex; flex-direction: column; gap: 5px; }
.sub-row { display: flex; align-items: center; gap: 6px; }
.sub-label { font-size: 12px; color: #8c8c8c; width: 24px; flex-shrink: 0; }
.sub-val { font-size: 12px; color: #595959; width: 32px; text-align: right; flex-shrink: 0; }

/* 评分说明 */
.score-explain { border-radius: 8px; background: #fafafa; }
.explain-title { font-size: 13px; font-weight: 600; color: #595959; margin-bottom: 10px; }
.explain-grid { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; }
.explain-item { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #8c8c8c; }
.explain-note { font-size: 12px; color: #faad14; background: #fffbe6; padding: 8px 12px; border-radius: 4px; border: 1px solid #ffe58f; }

/* 动画 */
.card-slide-enter-active { transition: all 0.3s ease; }
.card-slide-enter-from { opacity: 0; transform: translateY(10px); }
</style>
