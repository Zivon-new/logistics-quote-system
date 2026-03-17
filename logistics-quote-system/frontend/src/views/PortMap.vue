<template>
  <div class="portmap-page">
    <div class="page-header">
      <h2>全球港口地图</h2>
      <p class="subtitle">覆盖全球 {{ allPorts.length }} 个主要港口，{{ stats.countries ?? '—' }} 个国家/地区 — 点击港口查看详情及预警</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stat-row" v-loading="loadingStats">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#e6f4ff">
            <el-icon style="color:#1890ff;font-size:20px"><Location /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats.total ?? '—' }}</div>
            <div class="stat-label">港口总数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#f6ffed">
            <el-icon style="color:#52c41a;font-size:20px"><Flag /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats.countries ?? '—' }}</div>
            <div class="stat-label">覆盖国家</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#fff7e6">
            <el-icon style="color:#fa8c16;font-size:20px"><Ship /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats.by_type?.['海港'] ?? '—' }}</div>
            <div class="stat-label">海港</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background:#f9f0ff">
            <el-icon style="color:#722ed1;font-size:20px"><Cloudy /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats.by_type?.['空港'] ?? '—' }}</div>
            <div class="stat-label">空港</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline>
        <el-form-item label="港口类型">
          <el-checkbox-group v-model="filters.types" size="small" @change="applyFilter">
            <el-checkbox-button v-for="t in typeOptions" :key="t.value" :value="t.value">
              <span :style="{color: t.color}">{{ t.label }}</span>
            </el-checkbox-button>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-checkbox-group v-model="filters.risks" size="small" @change="applyFilter">
            <el-checkbox-button value="低">低风险</el-checkbox-button>
            <el-checkbox-button value="中">中风险</el-checkbox-button>
            <el-checkbox-button value="高">高风险</el-checkbox-button>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="仅显示预警">
          <el-switch v-model="filters.warningOnly" size="small" @change="applyFilter" />
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="港口名/国家/UNLOCODE"
            clearable
            size="small"
            style="width:180px"
            @input="applyFilter"
          />
        </el-form-item>
        <el-form-item>
          <el-button size="small" @click="resetFilter">重置</el-button>
          <span class="filter-count">显示 <strong>{{ filteredPorts.length }}</strong> / {{ allPorts.length }} 个港口</span>
          <span v-if="warningPortCount > 0" class="warning-hint">
            <el-icon style="color:#f5222d;vertical-align:middle"><Warning /></el-icon>
            {{ warningPortCount }} 个港口所在国有风险预警
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 地图容器 -->
    <el-card class="map-card" shadow="never" v-loading="loadingPorts">
      <div ref="mapContainer" class="map-container"></div>
    </el-card>

    <!-- 预警详情对话框 -->
    <el-dialog
      v-model="warningDialogVisible"
      :title="`${warningDialogPort} — 地区风险预警详情`"
      width="560px"
      destroy-on-close
    >
      <div v-if="warningDialogList.length === 0" style="color:#8c8c8c;text-align:center;padding:24px">
        暂无预警信息
      </div>
      <div v-else class="warning-dialog-list">
        <div
          v-for="w in warningDialogList"
          :key="w['预警ID']"
          class="warning-dialog-item"
          :class="`risk-${w['风险等级']}`"
        >
          <div class="wd-header">
            <el-tag
              :type="w['风险等级'] === 3 ? 'danger' : w['风险等级'] === 2 ? 'warning' : 'success'"
              size="small"
              style="margin-right:8px"
            >{{ w['风险等级文字'] }}</el-tag>
            <span class="wd-type">{{ w['风险类型'] }}</span>
            <span class="wd-date">生效：{{ w['生效日期'] }}</span>
          </div>
          <div class="wd-title">{{ w['预警标题'] }}</div>
          <div class="wd-detail">{{ w['预警详情'] }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="warningDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="goSearchFromDialog">查询该目的地路线 →</el-button>
      </template>
    </el-dialog>

    <!-- 图例 -->
    <el-card class="legend-card" shadow="never">
      <div class="legend-title">图例说明</div>
      <div class="legend-body">
        <div class="legend-group">
          <span class="legend-group-label">港口类型（图标颜色）：</span>
          <span v-for="t in typeOptions" :key="t.value" class="legend-item">
            <span class="legend-dot" :style="{background: t.color}"></span>{{ t.label }}
          </span>
        </div>
        <div class="legend-group">
          <span class="legend-group-label">风险等级（边框）：</span>
          <span class="legend-item"><span class="legend-ring" style="border-color:#52c41a"></span>低风险</span>
          <span class="legend-item"><span class="legend-ring" style="border-color:#faad14"></span>中风险</span>
          <span class="legend-item"><span class="legend-ring" style="border-color:#f5222d"></span>高风险</span>
        </div>
        <div class="legend-group">
          <span class="legend-group-label">联动功能：</span>
          <span class="legend-item" style="color:#595959">点击港口弹窗 → 查看预警 + 一键查询该目的地路线</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, Flag, Cloudy, Warning } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getPorts, getPortStats } from '@/api/ports'
import request from '@/utils/request'

const router = useRouter()

// 修复 Leaflet 默认图标路径问题（Vite 打包时的已知 bug）
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

// 港口类型配置
const typeOptions = [
  { value: '海港',     label: '海港',     color: '#1890ff' },
  { value: '空港',     label: '空港',     color: '#722ed1' },
  { value: '内陆港',   label: '内陆港',   color: '#52c41a' },
  { value: '铁路港',   label: '铁路港',   color: '#fa8c16' },
  { value: '多式联运', label: '多式联运', color: '#eb2f96' },
]
const typeColorMap = Object.fromEntries(typeOptions.map(t => [t.value, t.color]))
const riskBorderMap = { '低': '#52c41a', '中': '#faad14', '高': '#f5222d' }
const riskLevelLabel = { 1: '低风险', 2: '中等风险', 3: '高风险' }
const riskLevelColor = { 1: '#52c41a', 2: '#faad14', 3: '#f5222d' }

const mapContainer = ref(null)
const loadingPorts = ref(true)
const loadingStats = ref(true)
const allPorts = ref([])
const filteredPorts = ref([])
const stats = ref({})

// 预警数据：{ 国家代码: [预警列表] }
const warningsByCountry = ref({})

// 预警详情对话框
const warningDialogVisible = ref(false)
const warningDialogPort = ref('')
const warningDialogList = ref([])
const warningDialogCountry = ref('')  // 用于对话框内"查询路线"按钮

const goSearchFromDialog = () => {
  warningDialogVisible.value = false
  router.push({ name: 'QuoteSearch', query: { dest: warningDialogCountry.value } })
}

const filters = reactive({
  types: ['海港', '空港', '内陆港', '铁路港', '多式联运'],
  risks: ['低', '中', '高'],
  keyword: '',
  warningOnly: false,
})

// 有预警的港口数量
const warningPortCount = computed(() =>
  allPorts.value.filter(p => warningsByCountry.value[p.country_code]?.length > 0).length
)

let map = null
const markersLayer = ref(null)

// 创建自定义圆形图标
const createIcon = (port) => {
  const color = typeColorMap[port.type] || '#1890ff'
  const border = riskBorderMap[port.lpi_risk] || '#faad14'
  const hasWarning = (warningsByCountry.value[port.country_code] || []).length > 0
  // 有预警时增加外圈闪烁效果（用更粗的红色描边）
  const outerRing = hasWarning
    ? `<circle cx="12" cy="12" r="11" fill="none" stroke="#f5222d" stroke-width="1.5" stroke-dasharray="3,2" opacity="0.8"/>`
    : ''
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
      ${outerRing}
      <circle cx="12" cy="12" r="9" fill="${color}" fill-opacity="0.85" stroke="${border}" stroke-width="2.5"/>
      <circle cx="12" cy="12" r="4" fill="white" fill-opacity="0.7"/>
    </svg>`
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  })
}

const buildPopup = (port) => {
  const riskColor = riskBorderMap[port.lpi_risk] || '#faad14'
  const clearance = port.clearance_days != null ? `${port.clearance_days} 天` : '暂无数据'
  const warnings = warningsByCountry.value[port.country_code] || []

  // 预警区块
  let warningBlock = ''
  if (warnings.length > 0) {
    const items = warnings.slice(0, 3).map(w => {
      const wc = riskLevelColor[w['风险等级']] || '#faad14'
      const wl = riskLevelLabel[w['风险等级']] || '风险'
      return `<div style="margin-top:4px;padding:4px 6px;background:#fff1f0;border-radius:4px;border-left:3px solid ${wc}">
        <span style="color:${wc};font-weight:600;font-size:11px">[${wl}]</span>
        <span style="color:#434343;font-size:12px"> ${w['预警标题']}</span>
      </div>`
    }).join('')
    const moreHint = warnings.length > 3 ? `<div style="color:#8c8c8c;font-size:11px;margin-top:2px">还有 ${warnings.length - 3} 条预警…</div>` : ''
    warningBlock = `
      <div style="margin-top:8px;border-top:1px solid #f0f0f0;padding-top:6px">
        <div style="color:#f5222d;font-weight:600;font-size:12px;margin-bottom:4px">⚠ 所在地区预警（${warnings.length}条）</div>
        ${items}${moreHint}
      </div>`
  }

  // 路线查询按钮（用 window 函数桥接 Vue router）
  const btnStyle = 'display:inline-block;margin-top:8px;padding:4px 10px;background:#1890ff;color:#fff;border-radius:4px;font-size:12px;cursor:pointer;border:none;'
  const riskBtnStyle = 'display:inline-block;margin-top:8px;margin-left:6px;padding:4px 10px;background:#fff1f0;color:#f5222d;border-radius:4px;font-size:12px;cursor:pointer;border:1px solid #ffa39e;'

  // 转义单引号，避免 onclick 字符串中断
  const safeName = port.name.replace(/'/g, "\\'")
  const safeCountry = port.country.replace(/'/g, "\\'")

  return `
    <div style="min-width:220px;max-width:300px;font-size:13px;line-height:1.8">
      <div style="font-size:15px;font-weight:700;color:#262626;margin-bottom:6px">
        ${port.name}
        <span style="font-size:11px;color:#8c8c8c;font-weight:400">&nbsp;${port.unlocode}</span>
      </div>
      ${port.name_en ? `<div style="color:#595959;font-size:12px;margin-bottom:4px">${port.name_en}</div>` : ''}
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="color:#8c8c8c;width:70px">国家</td><td>${port.country}（${port.country_code}）</td></tr>
        <tr><td style="color:#8c8c8c">城市</td><td>${port.city || '—'}</td></tr>
        <tr><td style="color:#8c8c8c">类型</td><td>${port.type}</td></tr>
        <tr><td style="color:#8c8c8c">时区</td><td>${port.timezone || '—'}</td></tr>
        <tr><td style="color:#8c8c8c">清关</td><td>${clearance}</td></tr>
        <tr>
          <td style="color:#8c8c8c">LPI风险</td>
          <td><span style="color:${riskColor};font-weight:600">${port.lpi_risk ?? '—'}风险</span></td>
        </tr>
        ${port.remark ? `<tr><td style="color:#8c8c8c">备注</td><td style="font-size:12px;color:#595959">${port.remark}</td></tr>` : ''}
      </table>
      ${warningBlock}
      <div style="margin-top:6px">
        <button style="${btnStyle}" onclick="window.__portMapGoSearch('${safeCountry}')">
          查询该目的地路线 →
        </button>
        ${warnings.length > 0 ? `<button style="${riskBtnStyle}" onclick="window.__portMapShowWarnings('${port.country_code}','${safeName}','${safeCountry}')">查看预警详情（${warnings.length}条）</button>` : ''}
      </div>
    </div>`
}

const renderMarkers = () => {
  if (!map) return
  if (markersLayer.value) {
    markersLayer.value.clearLayers()
  } else {
    markersLayer.value = L.layerGroup().addTo(map)
  }
  filteredPorts.value.forEach(port => {
    const marker = L.marker([port.lat, port.lng], { icon: createIcon(port) })
    marker.bindPopup(buildPopup(port), { maxWidth: 320 })
    markersLayer.value.addLayer(marker)
  })
}

const applyFilter = () => {
  const kw = filters.keyword.trim().toLowerCase()
  filteredPorts.value = allPorts.value.filter(p => {
    if (!filters.types.includes(p.type)) return false
    if (!filters.risks.includes(p.lpi_risk)) return false
    if (filters.warningOnly && !(warningsByCountry.value[p.country_code]?.length > 0)) return false
    if (kw && !p.name.toLowerCase().includes(kw) &&
        !p.country.toLowerCase().includes(kw) &&
        !(p.name_en || '').toLowerCase().includes(kw) &&
        !p.unlocode.toLowerCase().includes(kw)) return false
    return true
  })
  renderMarkers()
}

const resetFilter = () => {
  filters.types = ['海港', '空港', '内陆港', '铁路港', '多式联运']
  filters.risks = ['低', '中', '高']
  filters.keyword = ''
  filters.warningOnly = false
  applyFilter()
}

// 注册全局桥接函数（供 popup HTML onclick 调用）
const setupGlobalBridge = () => {
  window.__portMapGoSearch = (country) => {
    router.push({ name: 'QuoteSearch', query: { dest: country } })
  }
  window.__portMapShowWarnings = (countryCode, portName, country) => {
    warningDialogPort.value = portName
    warningDialogCountry.value = country
    warningDialogList.value = warningsByCountry.value[countryCode] || []
    warningDialogVisible.value = true
  }
}

onMounted(async () => {
  setupGlobalBridge()

  // 并行加载：统计 + 港口 + 预警
  const [portsData, statsData, warningsData] = await Promise.allSettled([
    getPorts(),
    getPortStats(),
    request({ url: '/v1/warnings/list', method: 'get' }),
  ])

  // 处理统计
  if (statsData.status === 'fulfilled') {
    stats.value = statsData.value
  }
  loadingStats.value = false

  // 处理预警：按国家代码分组
  if (warningsData.status === 'fulfilled') {
    const wMap = {}
    for (const w of warningsData.value) {
      const code = w['国家代码']
      if (!wMap[code]) wMap[code] = []
      wMap[code].push(w)
    }
    warningsByCountry.value = wMap
  }

  // 处理港口
  if (portsData.status === 'rejected') {
    ElMessage.error('港口数据加载失败')
    loadingPorts.value = false
    return
  }
  allPorts.value = portsData.value
  filteredPorts.value = portsData.value
  loadingPorts.value = false

  // 初始化地图
  await nextTick()
  map = L.map(mapContainer.value, {
    center: [20, 110],
    zoom: 3,
    minZoom: 2,
    maxZoom: 14,
  })

  // 高德地图瓦片（中文标注）
  // 如因网络环境无法加载，可改用 OpenStreetMap 标准瓦片
  const amapTile = L.tileLayer(
    'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
    {
      subdomains: ['1','2','3','4'],
      attribution: '© <a href="https://www.amap.com/">高德地图</a>',
      maxZoom: 18,
    }
  )
  const osmFallback = L.tileLayer(
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }
  )

  // 尝试加载高德，失败则切换到 OSM
  amapTile.on('tileerror', () => {
    if (map.hasLayer(amapTile)) {
      map.removeLayer(amapTile)
      osmFallback.addTo(map)
    }
  })
  amapTile.addTo(map)

  // 图层控制器
  L.control.layers(
    { '高德地图（中文）': amapTile, 'OpenStreetMap': osmFallback },
    {},
    { position: 'topright' }
  ).addTo(map)

  renderMarkers()
})

onBeforeUnmount(() => {
  // 清理全局函数
  delete window.__portMapGoSearch
  delete window.__portMapGoRisk
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.portmap-page { padding: 0; }
.page-header { margin-bottom: 16px; }
.page-header h2 { font-size: 22px; font-weight: 600; color: #262626; margin: 0 0 4px; }
.subtitle { color: #8c8c8c; font-size: 13px; margin: 0; }

/* 统计卡片 */
.stat-row { margin-bottom: 12px; }
.stat-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border-radius: 8px;
  padding: 14px 16px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.stat-icon {
  width: 44px; height: 44px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.stat-num { font-size: 24px; font-weight: 700; color: #262626; }
.stat-label { font-size: 12px; color: #8c8c8c; margin-top: 2px; }

/* 筛选栏 */
.filter-card { margin-bottom: 12px; border-radius: 8px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.filter-card :deep(.el-form-item) { margin-bottom: 0; margin-right: 20px; }
.filter-count { font-size: 13px; color: #8c8c8c; margin-left: 12px; }
.filter-count strong { color: #1890ff; }
.warning-hint { font-size: 13px; color: #f5222d; margin-left: 16px; }

/* 地图 */
.map-card { margin-bottom: 12px; border-radius: 8px; }
.map-card :deep(.el-card__body) { padding: 0; overflow: hidden; border-radius: 8px; }
.map-container { height: 540px; width: 100%; border-radius: 8px; }

/* 图例 */
.legend-card { border-radius: 8px; }
.legend-card :deep(.el-card__body) { padding: 12px 16px; }
.legend-title { font-size: 13px; font-weight: 600; color: #262626; margin-bottom: 8px; }
.legend-body { display: flex; flex-wrap: wrap; gap: 20px; }
.legend-group { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; font-size: 13px; }
.legend-group-label { color: #8c8c8c; white-space: nowrap; }
.legend-item { display: flex; align-items: center; gap: 5px; color: #595959; }
.legend-dot {
  width: 12px; height: 12px; border-radius: 50%;
  display: inline-block; flex-shrink: 0;
}
.legend-ring {
  width: 12px; height: 12px; border-radius: 50%;
  border: 2.5px solid; display: inline-block; flex-shrink: 0;
}

/* 预警对话框 */
.warning-dialog-list { display: flex; flex-direction: column; gap: 12px; max-height: 440px; overflow-y: auto; }
.warning-dialog-item {
  border-radius: 6px; padding: 12px 14px;
  border-left: 4px solid #faad14; background: #fffbe6;
}
.warning-dialog-item.risk-3 { border-left-color: #f5222d; background: #fff1f0; }
.warning-dialog-item.risk-2 { border-left-color: #faad14; background: #fffbe6; }
.warning-dialog-item.risk-1 { border-left-color: #52c41a; background: #f6ffed; }
.wd-header { display: flex; align-items: center; margin-bottom: 6px; gap: 6px; }
.wd-type { font-size: 12px; color: #595959; background: #f5f5f5; padding: 1px 6px; border-radius: 3px; }
.wd-date { font-size: 11px; color: #8c8c8c; margin-left: auto; }
.wd-title { font-size: 14px; font-weight: 600; color: #262626; margin-bottom: 4px; }
.wd-detail { font-size: 13px; color: #595959; line-height: 1.6; }
</style>
