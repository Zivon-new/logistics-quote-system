// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'quote-search',
        name: 'QuoteSearch',
        component: () => import('@/views/QuoteSearch.vue'),
        meta: { title: '报价查询' }
      },
      {
        path: 'route-manage',
        name: 'RouteManage',
        component: () => import('@/views/RouteManage.vue'),
        meta: { title: '路线管理' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue'),
        meta: { title: '价格看板' }
      },
      {
        path: 'port-map',
        name: 'PortMap',
        component: () => import('@/views/PortMap.vue'),
        meta: { title: '港口地图' }
      },
      {
        path: 'risk-profile',
        name: 'RiskProfile',
        component: () => import('@/views/RiskProfile.vue'),
        meta: { title: '航线风险' }
      },
      {
        path: 'agent-check',
        name: 'AgentCheck',
        component: () => import('@/views/AgentCheck.vue'),
        meta: { title: 'AI企业背调' }
      },
    ]
  },
  {
    path: '/route-manage/new',
    name: 'NewRoute',
    component: () => import('@/views/NewRoute/index.vue'),
    meta: { 
      title: '新增路线',
      requiresAuth: true,
      requiresAdmin: true  // 需要管理员权限
    }
  },
  {
    path: '/route-manage/edit/:id',
    name: 'EditRoute',
    component: () => import('@/views/NewRoute/index.vue'),
    meta: {
      title: '编辑路线',
      requiresAuth: true,
      requiresAdmin: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

function isTokenExpired(token) {
  try {
    // JWT uses base64url: replace - → + and _ → / before atob
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64))
    return Date.now() / 1000 > payload.exp
  } catch {
    return true
  }
}

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token

  if (to.meta.requiresAuth) {
    if (!token || isTokenExpired(token)) {
      // token 不存在或已过期：清掉再去登录，避免进入页面后才发现
      userStore.clearAuth()
      next('/login')
      return
    }
  }

  if (to.path === '/login' && token && !isTokenExpired(token)) {
    // 已登录且 token 有效时访问登录页，跳转到首页
    next('/dashboard')
  } else {
    next()
  }
})

export default router
