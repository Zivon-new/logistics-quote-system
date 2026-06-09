# backend/app/api/v1/users.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...database import get_db
from ...core.deps import get_current_user
from ...models.user import User

router = APIRouter(prefix="/users", tags=["用户"])

ONLINE_THRESHOLD_MINUTES = 5


@router.get("/online")
async def get_online_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.username != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")

    cutoff = datetime.now() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    users = db.query(User).filter(
        User.is_active == True,
        User.last_active >= cutoff
    ).order_by(User.last_active.desc()).all()

    return [
        {
            "username": u.username,
            "full_name": u.full_name or u.username,
            "last_active": u.last_active.strftime("%H:%M:%S") if u.last_active else None,
        }
        for u in users
    ]
