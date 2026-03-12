# 🚢 国际物流报价查询系统

一个基于 FastAPI + Vue 3 的企业级国际物流报价管理系统

## 📋 项目信息

- **开发周期**: 2026年2月 - 3月
- **上线目标**: 3月10日
- **目标用户**: 公司内部员工（国际部、总裁办）
- **并发用户**: 15-20人
- **技术栈**: FastAPI + Vue 3 + MySQL + Element Plus

## ✨ 核心功能

### 第一版 (MVP - 3月10日)
- ✅ **用户认证**: 登录/登出，权限管理（管理员/普通用户）
- ✅ **报价查询**: 多条件搜索（起始地、目的地、时间、重量、体积、代理商）
- ✅ **路线管理**: 增删改查，Excel批量导入
- ✅ **数据展示**: 代理商对比、费用明细、导出Excel

### 第二版 (3月-5月优化)
- ⏳ 数据统计分析（图表）
- ⏳ PDF报价单导出
- ⏳ 高级筛选和搜索
- ⏳ 操作日志

## 🏗️ 技术架构

```
┌─────────────┐
│  Vue 3      │  前端 (Element Plus)
│  前端界面   │  http://localhost:5173
└──────┬──────┘
       │ REST API
┌──────▼──────┐
│  FastAPI    │  后端 (Python 3.11+)
│  后端服务   │  http://localhost:8000
└──────┬──────┘
       │ SQL
┌──────▼──────┐
│  MySQL 8.0  │  数据库
│  price_test_v2
└─────────────┘
```

## 📁 项目结构

```
logistics-quote-system/
├── backend/              ✅ 已完成
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── models/      # 数据模型
│   │   ├── schemas/     # 数据验证
│   │   └── crud/        # 数据库操作
│   └── init_db.py       # 初始化脚本
│
├── frontend/             🚧 进行中
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── components/  # 通用组件
│   │   ├── api/         # API调用
│   │   └── router/      # 路由配置
│   └── package.json
│
├── database/             ✅ 已完成
│   └── price_test_v2.sql
│
├── scripts/              ✅ 已完成（原有）
│   └── (数据处理脚本)
│
└── docs/
    └── 完整启动指南.md   ✅ 已完成
```

## 🚀 快速开始

### 1️⃣ 数据库准备
```bash
# 创建数据库
mysql -u root -pJHL181116 -e "CREATE DATABASE IF NOT EXISTS price_test_v2"

# 导入表结构
mysql -u root -pJHL181116 price_test_v2 < database/price_test_v2.sql
```

### 2️⃣ 启动后端
```bash
cd backend
pip install -r requirements.txt
python init_db.py            # 创建用户表
uvicorn app.main:app --reload
```

✅ 访问: http://localhost:8000/docs

### 3️⃣ 启动前端
```bash
cd frontend
npm install
npm run dev
```

✅ 访问: http://localhost:5173

### 🔑 默认账号
- **管理员**: admin / admin123
- **普通用户**: user / user123

## 📖 详细文档

- [📘 完整启动指南](./完整启动指南.md) - 第一次运行必看
- [📗 后端API文档](http://localhost:8000/docs) - 启动后访问
- [📙 数据库设计文档](../database/README.md) - 数据库字段说明

## 🎨 UI设计

### 颜色主题（仿公司系统）
- **主色调**: #001529 (深蓝)
- **辅助色**: #1890ff (亮蓝)
- **背景色**: #f0f2f5 (浅灰)

### 页面布局
- **登录页**: 深蓝背景 + 网格动效 + 居中卡片
- **主界面**: 左侧深蓝导航 + 白色内容区

## 📊 当前进度

### ✅ 已完成
- [x] 需求分析
- [x] 数据库设计
- [x] 后端API开发（100%）
- [x] 数据模型（中文字段名支持）
- [x] 用户认证（JWT）
- [x] 报价查询接口
- [x] 路线管理接口

### 🚧 进行中
- [ ] 前端界面开发
- [ ] 登录页（深蓝主题）
- [ ] 主界面框架
- [ ] 报价查询页面
- [ ] 路线管理页面
- [ ] Excel导入集成

### ⏳ 待开始
- [ ] 数据统计图表
- [ ] PDF导出
- [ ] 移动端适配

## 🔧 开发环境

### 必需软件
- Python 3.11+
- Node.js 18+
- MySQL 8.0
- Git

### 推荐工具
- VS Code
- Postman (API测试)
- MySQL Workbench
- Chrome + Vue Devtools

## 📝 开发规范

### 后端
- 代码风格: PEP 8
- 命名: 蛇形命名法 (snake_case)
- 注释: 中文注释
- 提交: 使用git commit前先测试

### 前端
- 代码风格: Vue 3 Composition API
- 命名: 驼峰命名法 (camelCase)
- 组件: 单文件组件 (.vue)
- 状态: Pinia

## 🐛 问题排查

### 后端启动失败
1. 检查Python版本: `python --version`
2. 检查依赖安装: `pip list`
3. 检查MySQL连接: `mysql -u root -pJHL181116`

### 前端启动失败
1. 检查Node版本: `node --version`
2. 清除缓存: `rm -rf node_modules && npm install`
3. 检查端口占用: `netstat -ano | findstr :5173`

### 数据库问题
1. 确保MySQL运行: `net start MySQL80`
2. 检查数据库存在: `SHOW DATABASES;`
3. 检查表结构: `USE price_test_v2; SHOW TABLES;`

## 📈 项目时间线

```
2月12日  项目启动，后端开发
2月20日  后端完成，前端开始
2月28日  前端主要功能完成
3月5日   集成测试
3月10日  第一版上线 ✅
------- 第一版上线分割线 -------
3月-5月  功能优化和完善
```

## 🤝 贡献者

- 开发者: [你的名字]
- 指导: Claude (Anthropic)
- 公司: 北京嘉恒利供应链管理有限公司

## 📄 许可证

内部项目，仅供公司使用

## 🎯 下一步行动

1. ✅ **测试后端**: 
   - 启动后端服务
   - 访问 http://localhost:8000/docs
   - 测试登录接口

2. 🚧 **开发前端**:
   - 等待后端测试通过
   - 开始创建Vue组件
   - 对接后端API

3. ⏳ **集成测试**:
   - 前后端联调
   - 功能测试
   - Bug修复

---

**当前状态**: 后端已完成，等待测试。前端开发中。

**遇到问题？** 查看 [完整启动指南.md](./完整启动指南.md) 或联系开发者。

**Good luck! 💪**
