# backend/app/api/v1/auth.py
"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from ...core.deps import get_db, get_current_user
from ...core.security import create_access_token
from ...core.captcha import generate_captcha, verify_captcha
from ...crud import user as crud_user
from ...schemas.user import LoginRequest, LoginResponse, UserResponse
from ...models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/captcha", summary="获取验证码")
async def get_captcha():
    """返回 base64 PNG 验证码图片及对应 ID"""
    captcha_id, image_b64 = generate_captcha()
    return {
        "captcha_id": captcha_id,
        "image": f"data:image/png;base64,{image_b64}"
    }


@router.post("/login", response_model=LoginResponse, summary="用户登录")
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录接口

    - **username**: 用户名
    - **password**: 密码
    - **captcha_id**: 验证码ID（从 /captcha 获取）
    - **captcha_answer**: 验证码内容
    """
    # 校验验证码
    if not verify_captcha(login_data.captcha_id, login_data.captcha_answer):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    user = crud_user.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")

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
    用户登出接口（JWT无状态，客户端删除Token即可）
    """
    return {"message": "登出成功"}
