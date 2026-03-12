# backend/app/api/v1/auth.py
"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.deps import get_db, get_current_user
from ...core.security import create_access_token
from ...crud import user as crud_user
from ...schemas.user import LoginRequest, LoginResponse, UserResponse
from ...models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录接口
    
    - **username**: 用户名
    - **password**: 密码
    """
    user = crud_user.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    # 创建访问令牌
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_user)):
    """
    用户登出接口
    
    注意：JWT Token是无状态的，服务端不需要做任何操作
    客户端只需删除本地存储的Token即可
    """
    return {"message": "登出成功"}
