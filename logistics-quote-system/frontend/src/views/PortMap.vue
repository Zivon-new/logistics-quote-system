<template>
  <div class="portmap-page">
    <div class="page-header">
      <h2>全球港口地图</h2>
      <p class="subtitle">基于UN/LOCODE数据，覆盖全球主要海港、空港和内陆港</p>
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
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 地图容器 -->
    <el-card class="map-card" shadow="never" v-loading="loadingPorts">
      <div ref="mapContainer" class="map-container"></div>
    </el-card>

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
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Location, Flag, Cloudy } from '@element-plus/icons-vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getPorts, getPortStats } from '@/api/ports'

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

const mapContainer = ref(null)
const loadingPorts = ref(true)
const loadingStats = ref(true)
const allPorts = ref([])
const filteredPorts = ref([])
const stats = ref({})

const filters = reactive({
  types: ['海港', '空港', '内陆港', '铁路港', '多式联运'],
  risks: ['低', '中', '高'],
  keyword: '',
})

let map = null
const markersLayer = ref(null)

// 创建自定义圆形图标
const createIcon = (port) => {
  const color = typeColorMap[port.type] || '#1890ff'
  const border = riskBorderMap[port.lpi_risk] || '#faad14'
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
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
  return `
    <div style="min-width:200px;font-size:13px;line-height:1.8">
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
          <td style="color:#8c8c8c">风险</td>
          <td><span style="color:${riskColor};font-weight:600">${port.lpi_risk ?? '—'}风险</span></td>
        </tr>
        ${port.remark ? `<tr><td style="color:#8c8c8c">备注</td><td style="font-size:12px;color:#595959">${port.remark}</td></tr>` : ''}
      </table>
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
    marker.bindPopup(buildPopup(port), { maxWidth: 280 })
    markersLayer.value.addLayer(marker)
  })
}

const applyFilter = () => {
  const kw = filters.keyword.trim().toLowerCase()
  filteredPorts.value = allPorts.value.filter(p => {
    if (!filters.types.includes(p.type)) return false
    if (!filters.risks.includes(p.lpi_risk)) return false
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
  applyFilter()
}

onMounted(async () => {
  // 加载统计数据
  getPortStats()
    .then(data => { stats.value = data })
    .catch(() => {})
    .finally(() => { loadingStats.value = false })

  // 加载港口数据
  try {
    const data = await getPorts()
    allPorts.value = data
    filteredPorts.value = data
  } catch (e) {
    ElMessage.error('港口数据加载失败')
    return
  } finally {
    loadingPorts.value = false
  }

  // 初始化地图
  await nextTick()
  map = L.map(mapContainer.value, {
    center: [20, 110],
    zoom: 3,
    minZoom: 2,
    maxZoom: 12,
  })

  // 使用 OpenStreetMap 瓦片
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map)

  renderMarkers()
})

onBeforeUnmount(() => {
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
.filter-card :deep(.el-form-item) { margin-bottom: 0; margin-right: 24px; }
.filter-count { font-size: 13px; color: #8c8c8c; margin-left: 12px; }
.filter-count strong { color: #1890ff; }

/* 地图 */
.map-card { margin-bottom: 12px; border-radius: 8px; }
.map-card :deep(.el-card__body) { padding: 0; overflow: hidden; border-radius: 8px; }
.map-container { height: 520px; width: 100%; border-radius: 8px; }

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
</style>
