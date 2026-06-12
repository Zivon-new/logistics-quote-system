# backend/app/api/v1/users.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User, UserLoginLog

router = APIRouter(prefix="/users", tags=["用户"])

ONLINE_THRESHOLD_MINUTES = 2
LOGIN_HISTORY_LIMIT = 20


@router.get("/activity")
async def get_user_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    cutoff = datetime.now() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    # MySQL 的 DESC 排序会把 NULL 排在最后，从未活跃过的用户自然落到列表底部
    users = db.query(User).filter(
        User.is_active == True
    ).order_by(User.last_active.desc()).all()

    return [
        {
            "username": u.username,
            "full_name": u.full_name or u.username,
            "last_active": u.last_active.strftime("%m-%d %H:%M") if u.last_active else None,
            "is_online": bool(u.last_active and u.last_active >= cutoff),
        }
        for u in users
    ]


@router.get("/login_history")
async def get_login_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    logs = (
        db.query(UserLoginLog, User)
        .join(User, UserLoginLog.user_id == User.id)
        .order_by(UserLoginLog.login_at.desc())
        .limit(LOGIN_HISTORY_LIMIT)
        .all()
    )

    return [
        {
            "id": log.id,
            "username": u.username,
            "full_name": u.full_name or u.username,
            "login_at": log.login_at.strftime("%m-%d %H:%M") if log.login_at else None,
            "ip_address": log.ip_address,
        }
        for log, u in logs
    ]
