# backend/app/api/v1/__init__.py
"""
API v1路由汇总
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .quotes import router as quotes_router
from .routes import router as routes_router
from .recommend import router as recommend_router
from .analytics import router as analytics_router
from .ports import router as ports_router
from .risk import router as risk_router
from .agent_check import router as agent_check_router

api_router = APIRouter(prefix="/v1")

# 注册各个子路由
api_router.include_router(auth_router)
api_router.include_router(quotes_router)
api_router.include_router(routes_router)
api_router.include_router(recommend_router)
api_router.include_router(analytics_router)
api_router.include_router(ports_router)
api_router.include_router(risk_router)
api_router.include_router(agent_check_router)
