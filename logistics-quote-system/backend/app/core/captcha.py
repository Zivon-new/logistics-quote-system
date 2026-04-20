# backend/app/core/captcha.py
"""
验证码生成与校验（内存存储，TTL=5分钟，一次性使用）
"""
import random
import string
import time
import uuid
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

_store: dict = {}  # {captcha_id: (answer, expires_at)}
_TTL = 300  # 5分钟


def generate_captcha() -> tuple[str, str]:
    """生成验证码，返回 (captcha_id, base64_png)"""
    chars = string.digits + 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # 去掉易混淆的 I/O
    code = ''.join(random.choices(chars, k=4))

    img = Image.new('RGB', (120, 44), color=(248, 248, 248))
    draw = ImageDraw.Draw(img)

    # 干扰线
    for _ in range(4):
        draw.line(
            [(random.randint(0, 120), random.randint(0, 44)),
             (random.randint(0, 120), random.randint(0, 44))],
            fill=(random.randint(160, 210),) * 3,
            width=1
        )

    # 字符（尝试系统字体，失败则用默认字体）
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font = ImageFont.load_default()

    for i, ch in enumerate(code):
        x = 8 + i * 28 + random.randint(-3, 3)
        y = random.randint(4, 10)
        color = (
            random.randint(20, 120),
            random.randint(20, 120),
            random.randint(20, 120),
        )
        draw.text((x, y), ch, fill=color, font=font)

    # 干扰点
    for _ in range(40):
        draw.point(
            (random.randint(0, 120), random.randint(0, 44)),
            fill=(random.randint(100, 200),) * 3
        )

    buf = BytesIO()
    img.save(buf, format='PNG')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    captcha_id = str(uuid.uuid4())
    _store[captcha_id] = (code.upper(), time.time() + _TTL)
    _cleanup()

    return captcha_id, img_b64


def verify_captcha(captcha_id: str, answer: str) -> bool:
    """校验验证码（一次性，校验后立即删除）"""
    entry = _store.pop(captcha_id, None)
    if not entry:
        return False
    code, expires_at = entry
    if time.time() > expires_at:
        return False
    return answer.upper().strip() == code


def _cleanup():
    now = time.time()
    expired = [k for k, (_, exp) in _store.items() if now > exp]
    for k in expired:
        del _store[k]
