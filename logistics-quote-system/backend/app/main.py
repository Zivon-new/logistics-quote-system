# backend/app/main.py
"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .api.v1 import api_router

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="国际物流报价查询系统API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api")


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """根路径 - 欢迎页"""
    return {
        "message": "欢迎使用国际物流报价系统API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
