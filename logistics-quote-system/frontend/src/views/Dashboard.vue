<template>
  <div class="dashboard-container">
    <h2 class="page-title">欢迎使用国际物流报价系统</h2>

    <!-- 数据卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon" style="background: #e6f7ff;">
              <el-icon :size="32" color="#1890ff"><Box /></el-icon>
            </div>
            <div class="stats-info">
              <p class="stats-value">{{ stats.totalRoutes }}</p>
              <p class="stats-label">总路线数</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon" style="background: #f0f5ff;">
              <el-icon :size="32" color="#597ef7"><User /></el-icon>
            </div>
            <div class="stats-info">
              <p class="stats-value">{{ stats.totalAgents }}</p>
              <p class="stats-label">代理商数量</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon" style="background: #fff7e6;">
              <el-icon :size="32" color="#faad14"><Calendar /></el-icon>
            </div>
            <div class="stats-info">
              <p class="stats-value">{{ stats.thisMonthRoutes }}</p>
              <p class="stats-label">本月新增</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-card class="quick-actions">
      <template #header>
        <div class="card-header">
          <span>快捷操作</span>
        </div>
      </template>
      <div class="actions-grid">
        <div class="action-item" @click="$router.push('/quote-search')">
          <el-icon :size="40" color="#1890ff"><Search /></el-icon>
          <p>报价查询</p>
        </div>
        <div class="action-item" @click="$router.push('/route-manage')">
          <el-icon :size="40" color="#52c41a"><Box /></el-icon>
          <p>路线管理</p>
        </div>
      </div>
    </el-card>

    <!-- 系统信息 -->
    <el-card class="system-info">
      <template #header>
        <div class="card-header">
          <span>系统信息</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="当前用户">
          {{ userStore.userInfo.full_name || userStore.userInfo.username }}
        </el-descriptions-item>
        <el-descriptions-item label="用户权限">
          <el-tag v-if="userStore.userInfo.is_admin" type="danger" size="small">管理员</el-tag>
          <el-tag v-else type="info" size="small">普通用户</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="登录时间">
          {{ new Date().toLocaleString('zh-CN') }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getStats } from '@/api/route'

const userStore = useUserStore()

const stats = ref({
  totalRoutes: 0,
  totalAgents: 0,
  thisMonthRoutes: 0
})

onMounted(async () => {
  try {
    const res = await getStats()
    // ✅ 修复：正确解析返回数据
    if (res.success && res.data) {
      stats.value = {
        totalRoutes: res.data.total_routes || 0,
        totalAgents: res.data.total_agents || 0,
        thisMonthRoutes: res.data.month_routes || 0  // ✅ 修复：使用正确的字段名
      }
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    // 失败也不影响页面显示，只是数据为0
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #262626;
}

.stats-row {
  margin-bottom: 24px;
}

.stats-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stats-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.stats-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-info {
  flex: 1;
}

.stats-value {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: #262626;
}

.stats-label {
  font-size: 14px;
  color: #8c8c8c;
  margin: 0;
}

.quick-actions {
  margin-bottom: 24px;
}

.card-header {
  font-weight: 600;
  font-size: 16px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
  transform: translateY(-2px);
}

.action-item p {
  margin-top: 12px;
  font-size: 14px;
  color: #595959;
}

.system-info {
  margin-bottom: 24px;
}
</style>