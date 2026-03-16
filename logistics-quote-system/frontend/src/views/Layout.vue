<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
      <!-- Logo区域 -->
      <div class="logo-container">
        <div class="logo-circle-small">
          <span>e'</span>
        </div>
        <transition name="fade">
          <span v-show="!isCollapse" class="logo-title">物流报价系统</span>
        </transition>
      </div>

      <!-- 菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="#001529"
        text-color="#ffffff"
        active-text-color="#1890ff"
        :unique-opened="true"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <el-menu-item index="/quote-search">
          <el-icon><Search /></el-icon>
          <template #title>报价查询</template>
        </el-menu-item>

        <el-menu-item index="/route-manage">
          <el-icon><Box /></el-icon>
          <template #title>路线管理</template>
        </el-menu-item>

        <el-menu-item index="/analytics">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>价格看板</template>
        </el-menu-item>

        <el-menu-item index="/port-map">
          <el-icon><MapLocation /></el-icon>
          <template #title>港口地图</template>
        </el-menu-item>

        <el-menu-item index="/risk-profile">
          <el-icon><Warning /></el-icon>
          <template #title>航线风险</template>
        </el-menu-item>

        <el-menu-item index="/agent-check">
          <el-icon><Aim /></el-icon>
          <template #title>企业背调</template>
        </el-menu-item>

      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon 
            class="collapse-icon" 
            @click="toggleCollapse"
          >
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
        </div>

        <div class="header-right">
          <!-- 用户信息 -->
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32">
                {{ userStore.userInfo.username?.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ userStore.userInfo.full_name || userStore.userInfo.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <el-tag v-if="userStore.userInfo.is_admin" type="danger" size="small">管理员</el-tag>
                  <el-tag v-else type="info" size="small">普通用户</el-tag>
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { House, Search, Box, SwitchButton, Expand, Fold, DataAnalysis, MapLocation, Warning, Aim } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { logout } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 切换侧边栏折叠
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 处理下拉菜单命令
const handleCommand = async (command) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })

      // 调用登出接口
      await logout()
      
      // 清除本地信息
      userStore.clearAuth()
      
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch (error) {
      // 取消操作
    }
  }
}
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100vh;
}

.sidebar {
  background: #001529;
  transition: width 0.3s;
  overflow-x: hidden;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo-circle-small {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-circle-small span {
  color: #ffffff;
  font-size: 16px;
  font-weight: bold;
  font-style: italic;
}

.logo-title {
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.el-menu {
  border-right: none;
}

.header {
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-icon {
  font-size: 20px;
  cursor: pointer;
  transition: color 0.3s;
}

.collapse-icon:hover {
  color: #1890ff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f0f2f5;
}

.username {
  font-size: 14px;
  color: #262626;
}

.main-content {
  background: #f0f2f5;
  overflow-y: auto;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
