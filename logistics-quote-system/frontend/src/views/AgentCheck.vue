<template>
  <div class="check-page">
    <div class="page-header">
      <h2>AI 企业背调助手</h2>
      <p class="subtitle">输入货运代理公司名称，由 GLM-4 自动生成背景调查报告，结果缓存7天</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：查询 + 历史记录 -->
      <el-col :span="8">

        <!-- 查询框 -->
        <el-card class="query-card" shadow="never">
          <template #header>
            <div class="card-title"><el-icon><Search /></el-icon> 发起背调</div>
          </template>
          <el-input
            v-model="keyword"
            placeholder="输入公司名称，如：中远海运"
            clearable
            size="large"
            style="margin-bottom:12px"
            @keyup.enter="doCheck(false)"
          />
          <div style="display:flex;gap:8px">
            <el-button
              type="primary"
              :loading="loading"
              :icon="MagicStick"
              style="flex:1"
              @click="doCheck(false)"
            >
              {{ loading ? 'AI分析中…' : '生成背调报告' }}
            </el-button>
            <el-tooltip content="忽略缓存，重新调用AI生成" placement="top">
              <el-button :disabled="loading" :icon="Refresh" @click="doCheck(true)" />
            </el-tooltip>
          </div>
          <div v-if="result?.from_cache" class="cache-hint">
            <el-icon><Clock /></el-icon> 来自缓存（{{ result.created_at?.slice(0, 16) }}）
          </div>
          <div v-else-if="result && !result.from_cache" class="api-hint">
            <el-icon><Lightning /></el-icon>
            GLM-4-Flash · {{ result.tokens }} tokens · {{ result.elapsed }}s
          </div>
        </el-card>

        <!-- 历史记录 -->
        <el-card class="history-card" shadow="never" v-loading="loadingHistory">
          <template #header>
            <div class="card-title-row">
              <div class="card-title"><el-icon><Document /></el-icon> 历史背调（最近50条）</div>
              <el-button link size="small" :icon="RefreshRight" @click="loadHistory">刷新</el-button>
            </div>
          </template>

          <el-empty v-if="!history.length" description="暂无背调记录" :image-size="60" />

          <div class="history-list" v-else>
            <div
              v-for="item in history"
              :key="item.id"
              class="history-item"
              :class="{ 'history-active': activeHistoryId === item.id }"
              @click="viewHistory(item.id)"
            >
              <div class="history-row1">
                <span class="history-kw">{{ item.keyword }}</span>
                <el-tag :type="riskTagType(item.risk_level)" size="small">{{ item.risk_level }}</el-tag>
              </div>
              <div class="history-row2">
                <span class="history-time">{{ item.created_at?.slice(0, 16) }}</span>
                <span class="history-user">{{ item.user }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：报告展示 -->
      <el-col :span="16">
        <el-card v-if="!result" shadow="never" class="empty-card">
          <el-empty description="输入公司名称，点击【生成背调报告】" :image-size="80">
            <template #image>
              <el-icon style="font-size:60px;color:#d9d9d9"><Notebook /></el-icon>
            </template>
          </el-empty>
        </el-card>

        <template v-else>
          <!-- 风险评级头部 -->
          <el-card class="risk-header-card" shadow="never"
            :style="{ borderLeft: '4px solid ' + riskColor(result.risk_level) }">
            <div class="risk-header">
              <div class="risk-company">
                <el-icon style="font-size:20px"><OfficeBuilding /></el-icon>
                {{ result.report?.公司名称 || result.keyword }}
              </div>
              <div
                class="risk-level-badge"
                :style="{ background: riskBg(result.risk_level), color: riskColor(result.risk_level), borderColor: riskColor(result.risk_level) }"
              >
                {{ result.risk_level }}
              </div>
            </div>
            <p class="risk-summary">{{ result.summary }}</p>
          </el-card>

          <!-- 六大维度报告 -->
          <el-card class="report-card" shadow="never">
            <template #header>
              <div class="card-title"><el-icon><Files /></el-icon> 详细背调报告</div>
            </template>

            <el-alert
              v-if="parseError"
              type="warning"
              :closable="false"
              title="报告解析异常，以下为 AI 原始输出"
              style="margin-bottom:12px"
            />

            <!-- 结构化报告 -->
            <template v-if="!parseError">
              <div
                v-for="field in reportFields"
                :key="field.key"
                class="report-section"
              >
                <div class="report-section-title">
                  <el-icon><component :is="field.icon" /></el-icon>
                  {{ field.label }}
                </div>
                <div class="report-section-body" :class="{ 'risk-text': field.key === '风险提示' }">
                  {{ result.report[field.key] || '—' }}
                </div>
              </div>
            </template>

            <!-- 原始输出降级 -->
            <pre v-else class="raw-output">{{ result.report?.原始输出 }}</pre>
          </el-card>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search, Refresh, Document, RefreshRight, MagicStick,
  Clock, Lightning, Notebook, OfficeBuilding, Files
} from '@element-plus/icons-vue'
import { checkAgent, getHistory, getHistoryDetail } from '@/api/agentCheck'

const keyword = ref('')
const loading = ref(false)
const loadingHistory = ref(false)
const result = ref(null)
const history = ref([])
const activeHistoryId = ref(null)

const reportFields = [
  { key: '成立背景',   label: '成立背景',   icon: 'InfoFilled' },
  { key: '主营业务',   label: '主营业务',   icon: 'Box' },
  { key: '经营规模',   label: '经营规模',   icon: 'TrendCharts' },
  { key: '服务网络',   label: '服务网络',   icon: 'Location' },
  { key: '合规资质',   label: '合规资质',   icon: 'Finished' },
  { key: '风险提示',   label: '风险提示',   icon: 'Warning' },
  { key: '综合评价',   label: '综合评价',   icon: 'Star' },
]

const parseError = computed(() =>
  result.value && '原始输出' in (result.value.report || {})
)

const riskTagType = (level) => {
  const map = { '低风险': 'success', '中等风险': 'warning', '高风险': 'danger', '无法评估': 'info' }
  return map[level] || 'info'
}
const riskColor = (level) => {
  const map = { '低风险': '#52c41a', '中等风险': '#faad14', '高风险': '#f5222d', '无法评估': '#8c8c8c' }
  return map[level] || '#8c8c8c'
}
const riskBg = (level) => {
  const map = { '低风险': '#f6ffed', '中等风险': '#fffbe6', '高风险': '#fff2f0', '无法评估': '#fafafa' }
  return map[level] || '#fafafa'
}

const doCheck = async (forceRefresh) => {
  const kw = keyword.value.trim()
  if (!kw) { ElMessage.warning('请输入公司名称'); return }
  loading.value = true
  result.value = null
  activeHistoryId.value = null
  try {
    const res = await checkAgent(kw, forceRefresh)
    result.value = res
    if (res.from_cache) {
      ElMessage.info('命中缓存，直接返回历史报告')
    } else {
      ElMessage.success('报告生成完成')
      loadHistory()   // 刷新历史列表
    }
  } catch (e) {
    ElMessage.error('背调失败：' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const viewHistory = async (id) => {
  activeHistoryId.value = id
  try {
    const res = await getHistoryDetail(id)
    result.value = { ...res, from_cache: true }
    keyword.value = res.keyword
  } catch (e) {
    ElMessage.error('加载失败')
  }
}

const loadHistory = async () => {
  loadingHistory.value = true
  try {
    history.value = await getHistory()
  } catch (e) {
    // 静默失败
  } finally {
    loadingHistory.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.check-page { padding: 0; }
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #262626; margin: 0 0 4px; }
.subtitle { color: #8c8c8c; font-size: 13px; margin: 0; }

.card-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; font-weight: 600; color: #262626;
}
.card-title-row {
  display: flex; align-items: center; justify-content: space-between;
}

/* 左侧 */
.query-card { margin-bottom: 12px; border-radius: 8px; }
.cache-hint, .api-hint {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; margin-top: 8px;
}
.cache-hint { color: #8c8c8c; }
.api-hint { color: #52c41a; }

.history-card { border-radius: 8px; }
.history-list { display: flex; flex-direction: column; gap: 4px; max-height: 520px; overflow-y: auto; }
.history-item {
  padding: 8px 10px; border-radius: 6px; cursor: pointer;
  transition: background .15s; border: 1px solid transparent;
}
.history-item:hover { background: #f5f5f5; }
.history-active { background: #e6f4ff !important; border-color: #91caff !important; }
.history-row1 { display: flex; align-items: center; justify-content: space-between; margin-bottom: 3px; }
.history-kw { font-size: 13px; color: #262626; font-weight: 500; }
.history-row2 { display: flex; justify-content: space-between; }
.history-time, .history-user { font-size: 11px; color: #bfbfbf; }

/* 右侧 */
.empty-card { border-radius: 8px; padding: 40px 0; }

.risk-header-card { margin-bottom: 12px; border-radius: 8px; }
.risk-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.risk-company { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; color: #262626; }
.risk-level-badge {
  font-size: 14px; font-weight: 700; padding: 4px 16px;
  border-radius: 20px; border: 2px solid;
}
.risk-summary { font-size: 13px; color: #595959; line-height: 1.8; margin: 0; }

.report-card { border-radius: 8px; }
.report-section { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0; }
.report-section:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
.report-section-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 600; color: #1890ff;
  margin-bottom: 6px;
}
.report-section-body { font-size: 13px; color: #595959; line-height: 1.8; }
.risk-text { color: #cf1322; background: #fff2f0; padding: 8px 12px; border-radius: 4px; }

.raw-output {
  font-size: 12px; color: #595959; background: #fafafa;
  padding: 12px; border-radius: 4px; white-space: pre-wrap; word-break: break-all;
}
</style>
