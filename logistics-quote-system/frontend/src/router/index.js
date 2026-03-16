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
        path: 'recommend',
        name: 'Recommend',
        component: () => import('@/views/Recommend.vue'),
        meta: { title: '智能推荐' }
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token

  if (to.meta.requiresAuth && !token) {
    // 需要登录但未登录，跳转到登录页
    next('/login')
  } else if (to.path === '/login' && token) {
    // 已登录访问登录页，跳转到首页
    next('/dashboard')
  } else {
    next()
  }
})

export default router
