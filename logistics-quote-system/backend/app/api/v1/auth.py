# backend/app/api/v1/auth.py
"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from ...core.deps import get_db, get_current_user
from ...core.security import create_access_token, verify_password
from ...core.captcha import generate_captcha, verify_captcha
from ...core.request_utils import get_client_ip
from ...schemas.user import LoginRequest, LoginResponse, UserResponse
from ...models.user import User, UserLoginLog

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

    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    # 原子递增会话版本号（数据库端 +1，避免并发登录时读改写竞态导致版本号重复），
    # 使该账号此前在其他设备/浏览器上的登录态失效（同一时间只允许一处登录）
    db.query(User).filter(User.id == user.id).update(
        {User.session_version: User.session_version + 1}
    )
    db.add(UserLoginLog(user_id=user.id, ip_address=get_client_ip(request)))
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.username, "ver": user.session_version})

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
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户登出接口

    递增会话版本号，使当前Token立即失效（不必等待过期）
    """
    db.query(User).filter(User.id == current_user.id).update(
        {User.session_version: User.session_version + 1}
    )
    db.commit()
    return {"message": "登出成功"}
