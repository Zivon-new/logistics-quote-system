# backend/app/schemas/user.py
"""
用户相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    full_name: Optional[str] = Field(None, max_length=100, description="姓名")
    email: Optional[str] = Field(None, description="邮箱")
    is_admin: bool = Field(False, description="是否管理员")


class UserCreate(UserBase):
    """创建用户Schema"""
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """更新用户Schema"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserResponse(UserBase):
    """用户响应Schema"""
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token Schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据Schema"""
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求Schema"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应Schema"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
