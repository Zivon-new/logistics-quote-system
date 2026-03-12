# backend/app/schemas/__init__.py
"""
数据Schema（用于API请求和响应验证）
"""
from .route import (
    RouteCreate,
    RouteUpdate,
    RouteResponse,
    RouteDetailResponse,
    AgentCreate,
    AgentResponse,
    FeeItemResponse,
)
from .quote import (
    QuoteSearchRequest,
    QuoteSearchResponse,
    QuoteResult,
    AgentWithFees,
)
from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
    TokenData,
    LoginRequest,
    LoginResponse,
)

__all__ = [
    # Route
    "RouteCreate",
    "RouteUpdate",
    "RouteResponse",
    "RouteDetailResponse",
    "AgentCreate",
    "AgentResponse",
    "FeeItemResponse",
    # Quote
    "QuoteSearchRequest",
    "QuoteSearchResponse",
    "QuoteResult",
    "AgentWithFees",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Token",
    "TokenData",
    "LoginRequest",
    "LoginResponse",
]
