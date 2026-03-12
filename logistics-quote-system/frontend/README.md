# 前端 - Vue 3

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

**如果速度慢，使用国内镜像**：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

服务启动后访问: http://localhost:5173

### 3. 登录系统

默认账号：
- 管理员: `admin` / `admin123`
- 普通用户: `user` / `user123`

## 📁 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API接口
│   │   ├── auth.js    # 认证接口
│   │   ├── quote.js   # 报价查询
│   │   └── route.js   # 路线管理
│   ├── assets/         # 资源文件
│   │   └── styles/    # 样式文件
│   ├── components/     # 组件
│   ├── router/         # 路由配置
│   ├── stores/         # 状态管理(Pinia)
│   ├── utils/          # 工具函数
│   │   └── request.js # axios封装
│   ├── views/          # 页面
│   │   ├── Login.vue       # 登录页
│   │   ├── Layout.vue      # 主布局
│   │   ├── Dashboard.vue   # 首页
│   │   ├── QuoteSearch.vue # 报价查询
│   │   └── RouteManage.vue # 路线管理
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── index.html          # HTML模板
├── vite.config.js      # Vite配置
└── package.json        # 依赖配置
```

## 🎨 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **图标**: Element Plus Icons

## 🔧 配置说明

### API代理配置

在 `vite.config.js` 中配置了API代理：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // 后端地址
    changeOrigin: true
  }
}
```

所有 `/api/*` 的请求会被代理到后端服务 `http://localhost:8000`

### 路由守卫

在 `src/router/index.js` 中配置了路由守卫：
- 未登录访问需要认证的页面 → 跳转到登录页
- 已登录访问登录页 → 跳转到首页

## 📄 页面说明

### 1. 登录页 (Login.vue)
- 深蓝色渐变背景（仿公司UI）
- 用户名密码登录
- 记住密码功能
- 显示测试账号

### 2. 主布局 (Layout.vue)
- 左侧深蓝色导航栏（仿公司UI）
- 可折叠侧边栏
- 顶部用户信息和退出
- 内容区域

### 3. 首页 (Dashboard.vue)
- 数据统计卡片
- 快捷操作入口
- 系统信息

### 4. 报价查询 (QuoteSearch.vue)
- 多条件搜索表单
- 查询结果列表
- 费用详情弹窗
- 分页功能

### 5. 路线管理 (RouteManage.vue)
- 路线列表展示
- 搜索筛选
- 查看详情
- 增删改（管理员）

## 🐛 开发调试

### 查看API请求

打开浏览器开发者工具 → Network 标签页

### Vue Devtools

安装 Vue.js devtools 浏览器插件进行调试

### 热重载

修改代码后会自动刷新，支持热模块替换(HMR)

## 📦 构建打包

```bash
# 生产环境打包
npm run build

# 预览打包结果
npm run preview
```

打包后的文件在 `dist/` 目录

## ⚙️ 环境变量

创建 `.env.local` 文件（可选）：

```env
# API基础路径
VITE_API_BASE_URL=/api

# 其他配置...
```

## 🎯 待开发功能

- [ ] Excel导入功能
- [ ] Excel导出优化
- [ ] 路线新增/编辑表单
- [ ] 数据统计图表
- [ ] 移动端适配

## 📝 注意事项

1. **后端必须先启动**: 确保后端服务运行在 `http://localhost:8000`
2. **Token过期**: Token有效期24小时，过期后需重新登录
3. **权限控制**: 部分功能仅管理员可用（新增、编辑、删除）

## 🔍 故障排查

### 1. 依赖安装失败
```bash
# 清除缓存
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 2. 端口被占用
```bash
# 修改端口（vite.config.js）
server: {
  port: 5174  // 改成其他端口
}
```

### 3. API请求失败
- 检查后端是否启动
- 检查后端地址是否正确
- 查看浏览器控制台错误信息

### 4. 登录后跳转失败
- 清除浏览器缓存
- 清除 localStorage
```javascript
localStorage.clear()
```

## 📞 技术支持

遇到问题查看：
1. 浏览器控制台 (F12)
2. 后端API文档 (http://localhost:8000/docs)
3. Element Plus文档 (https://element-plus.org/)

---

**开发愉快！** 🎉
