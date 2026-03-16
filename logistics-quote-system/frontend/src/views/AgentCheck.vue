<template>
  <div class="check-page">
    <div class="page-header">
      <h2>AI 企业背调助手</h2>
      <p class="subtitle">从天眼查/企查查复制企业信息，由 GLM-4 进行结构化解析与风险评估</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：输入区 + 历史记录 -->
      <el-col :span="9">

        <!-- 输入区 -->
        <el-card class="query-card" shadow="never">
          <template #header>
            <div class="card-title"><el-icon><EditPen /></el-icon> 发起背调</div>
          </template>

          <!-- 第一步：公司名称 -->
          <div class="step-label">① 输入公司名称</div>
          <el-input
            v-model="keyword"
            placeholder="如：北京嘉恒利供应链有限公司"
            clearable
            style="margin-bottom:12px"
          />

          <!-- 第二步：粘贴原始信息 -->
          <div class="step-label">
            ② 粘贴企业信息
            <span class="step-tip">（从天眼查 / 企查查 / 爱企查等平台复制）</span>
          </div>
          <el-input
            v-model="rawText"
            type="textarea"
            :rows="12"
            placeholder="将天眼查或企查查上的公司工商信息、股东结构、风险记录等内容粘贴到此处..."
            style="margin-bottom:12px"
          />

          <div class="char-count">已输入 {{ rawText.length }} 字符</div>

          <el-button
            type="primary"
            :loading="loading"
            :icon="MagicStick"
            style="width:100%;margin-top:8px"
            @click="doCheck"
          >
            {{ loading ? 'AI 分析中…' : 'AI 分析并生成报告' }}
          </el-button>

          <div v-if="result && !result.from_cache" class="api-hint">
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
      <el-col :span="15">
        <el-card v-if="!result" shadow="never" class="empty-card">
          <el-empty description="在左侧粘贴企业信息，点击【AI 分析并生成报告】" :image-size="80">
            <template #image>
              <el-icon style="font-size:60px;color:#d9d9d9"><Notebook /></el-icon>
            </template>
          </el-empty>
          <!-- 使用说明 -->
          <div class="usage-guide">
            <div class="usage-title">使用方法</div>
            <div class="usage-steps">
              <div class="usage-step">
                <span class="usage-num">1</span>
                <span>打开 <strong>tianyancha.com</strong> 或 <strong>qichacha.com</strong>，搜索目标公司</span>
              </div>
              <div class="usage-step">
                <span class="usage-num">2</span>
                <span>复制工商基本信息、股东结构、风险记录等内容</span>
              </div>
              <div class="usage-step">
                <span class="usage-num">3</span>
                <span>粘贴到左侧文本框，点击"AI 分析"按钮</span>
              </div>
              <div class="usage-step">
                <span class="usage-num">4</span>
                <span>AI 自动解析数据，输出结构化风险评估报告</span>
              </div>
            </div>
          </div>
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

          <!-- 详细报告 -->
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

            <template v-if="!parseError">
              <div v-for="field in reportFields" :key="field.key" class="report-section">
                <div class="report-section-title">
                  <el-icon><component :is="field.icon" /></el-icon>
                  {{ field.label }}
                </div>
                <div
                  class="report-section-body"
                  :class="{ 'risk-text': field.key === '风险提示' }"
                >
                  {{ result.report[field.key] || '—' }}
                </div>
              </div>
            </template>

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
  EditPen, Document, RefreshRight, MagicStick,
  Lightning, Notebook, OfficeBuilding, Files
} from '@element-plus/icons-vue'
import { checkAgent, getHistory, getHistoryDetail } from '@/api/agentCheck'

const keyword = ref('')
const rawText = ref('')
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

const doCheck = async () => {
  if (!keyword.value.trim()) { ElMessage.warning('请输入公司名称'); return }
  if (!rawText.value.trim()) { ElMessage.warning('请粘贴企业信息后再分析'); return }

  loading.value = true
  result.value = null
  activeHistoryId.value = null
  try {
    const res = await checkAgent(keyword.value.trim(), rawText.value.trim())
    result.value = res
    ElMessage.success('分析完成')
    loadHistory()
  } catch (e) {
    ElMessage.error('分析失败：' + (e.message || '未知错误'))
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
    rawText.value = ''
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
.card-title-row { display: flex; align-items: center; justify-content: space-between; }

/* 输入区 */
.query-card { margin-bottom: 12px; border-radius: 8px; }
.step-label { font-size: 13px; font-weight: 600; color: #262626; margin-bottom: 6px; }
.step-tip { font-size: 12px; color: #8c8c8c; font-weight: 400; }
.char-count { font-size: 12px; color: #bfbfbf; text-align: right; margin-top: -8px; }
.api-hint {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: #52c41a; margin-top: 8px;
}

/* 历史 */
.history-card { border-radius: 8px; }
.history-list { display: flex; flex-direction: column; gap: 4px; max-height: 400px; overflow-y: auto; }
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
.empty-card { border-radius: 8px; }
.empty-card :deep(.el-card__body) { padding: 40px 24px 24px; }

/* 使用说明 */
.usage-guide { margin-top: 24px; padding: 16px; background: #f0f9ff; border-radius: 8px; }
.usage-title { font-size: 13px; font-weight: 600; color: #096dd9; margin-bottom: 12px; }
.usage-steps { display: flex; flex-direction: column; gap: 10px; }
.usage-step { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: #595959; }
.usage-num {
  width: 20px; height: 20px; border-radius: 50%; background: #1890ff;
  color: #fff; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 1px;
}

/* 报告 */
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
  font-size: 13px; font-weight: 600; color: #1890ff; margin-bottom: 6px;
}
.report-section-body { font-size: 13px; color: #595959; line-height: 1.8; }
.risk-text { color: #cf1322; background: #fff2f0; padding: 8px 12px; border-radius: 4px; }

.raw-output {
  font-size: 12px; color: #595959; background: #fafafa;
  padding: 12px; border-radius: 4px; white-space: pre-wrap; word-break: break-all;
}
</style>
