# backend/app/core/request_utils.py
"""
请求相关工具函数
"""
from typing import Optional
from fastapi import Request


def get_client_ip(request: Request) -> Optional[str]:
    """获取客户端真实IP

    优先读取反代（如 Nginx）写入的 X-Forwarded-For 头第一段，
    取不到时回退到直连地址 request.client.host
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None
