# 后端 - FastAPI

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库

1. 确保MySQL已安装并运行
2. 创建数据库（如果还没创建）:
```sql
CREATE DATABASE price_test_v2 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

3. 导入数据库表结构:
```bash
mysql -u root -pJHL181116 price_test_v2 < ../database/price_test_v2.sql
```

### 3. 初始化用户表

```bash
python init_db.py
```

这会创建用户表并添加默认账号:
- 管理员: `admin` / `admin123`
- 普通用户: `user` / `user123`

### 4. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或者直接运行
python -m app.main
```

服务启动后访问:
- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## 📁 项目结构

```
backend/
├── app/
│   ├── api/                # API路由
│   │   └── v1/
│   │       ├── auth.py     # 认证接口
│   │       ├── quotes.py   # 报价查询
│   │       └── routes.py   # 路线管理
│   ├── core/               # 核心功能
│   │   ├── security.py     # 安全(JWT)
│   │   └── deps.py         # 依赖注入
│   ├── crud/               # 数据库操作
│   │   ├── route.py
│   │   └── user.py
│   ├── models/             # SQLAlchemy模型
│   │   ├── route.py
│   │   ├── fee.py
│   │   ├── goods.py
│   │   └── user.py
│   ├── schemas/            # Pydantic模型
│   │   ├── route.py
│   │   ├── quote.py
│   │   └── user.py
│   ├── config.py           # 配置
│   ├── database.py         # 数据库连接
│   └── main.py             # 应用入口
├── init_db.py              # 初始化脚本
├── requirements.txt        # 依赖包
└── .env.example            # 环境变量示例
```

## 🔑 API接口

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户
- `POST /api/v1/auth/logout` - 用户登出

### 报价查询
- `GET /api/v1/quotes/search` - 搜索报价

### 路线管理
- `GET /api/v1/routes` - 获取路线列表
- `GET /api/v1/routes/{id}` - 获取路线详情
- `POST /api/v1/routes` - 创建路线（管理员）
- `PUT /api/v1/routes/{id}` - 更新路线（管理员）
- `DELETE /api/v1/routes/{id}` - 删除路线（管理员）

详细API文档请访问: http://localhost:8000/docs

## ⚙️ 配置说明

编辑 `app/config.py` 或创建 `.env` 文件:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=JHL181116
DB_NAME=price_test_v2
SECRET_KEY=your-secret-key
```

## 🐛 调试

启用调试模式:
```python
# app/config.py
DEBUG = True
```

查看SQL语句:
```python
# app/database.py
echo=True
```

## 📝 注意事项

1. 中文字段名: 数据库使用中文字段名，SQLAlchemy模型已正确配置
2. JWT Token: 默认有效期24小时
3. CORS: 已配置允许前端跨域访问
4. 权限: 管理员才能创建/修改/删除路线

## 🔧 开发建议

1. 使用VS Code插件: Python, Pylance
2. 代码格式化: black, flake8
3. 类型检查: mypy
4. 测试: pytest

## 📞 问题排查

### 1. 数据库连接失败
- 检查MySQL是否运行
- 检查用户名密码是否正确
- 检查数据库名是否存在

### 2. 导入错误
- 确保在backend目录下运行
- 检查依赖是否安装完整

### 3. 端口被占用
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -i :8000
kill -9 <进程ID>
```
