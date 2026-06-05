# backend/init_db.py
"""
数据库初始化脚本

运行方式:
python init_db.py
"""
from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.core.security import get_password_hash

# ────────────────────────────────────────────────────────────
# 在下方填写要创建的账号。已存在的用户名会自动跳过。
# username: 登录用，英文/拼音，不能重复
# full_name: 显示姓名
# password: 初始密码
# is_admin: True = 管理员，False = 普通用户
# ────────────────────────────────────────────────────────────
_PWD = "JHL181116"
USERS_TO_CREATE = [
    {"username": "sdream",   "full_name": "Sdream 谢斯俊", "password": _PWD, "is_admin": True},
    {"username": "anna",     "full_name": "Anna 李瑾",     "password": _PWD, "is_admin": True},
    {"username": "sivan",    "full_name": "Sivan 孙万鹏",  "password": _PWD, "is_admin": True},
    {"username": "leo",      "full_name": "Leo 王晶",      "password": _PWD, "is_admin": True},
    {"username": "sean",     "full_name": "Sean 尹航",     "password": _PWD, "is_admin": True},
    {"username": "helena",   "full_name": "Helena 贺影",   "password": _PWD, "is_admin": True},
    {"username": "allie",    "full_name": "Allie 马媛",    "password": _PWD, "is_admin": True},
    {"username": "jessie",   "full_name": "Jessie 苏桐渲", "password": _PWD, "is_admin": True},
    {"username": "sally",    "full_name": "Sally 闫思琪",  "password": _PWD, "is_admin": True},
    {"username": "blanche",  "full_name": "Blanche 韩文静","password": _PWD, "is_admin": True},
    {"username": "jade",     "full_name": "Jade 郝佳",     "password": _PWD, "is_admin": True},
    {"username": "ethan",    "full_name": "Ethan 荆博恩",  "password": _PWD, "is_admin": True},
    {"username": "mary",     "full_name": "Mary 梁锐欣",   "password": _PWD, "is_admin": True},
    {"username": "nina",     "full_name": "Nina 卢立坤",   "password": _PWD, "is_admin": True},
    {"username": "bonnie",   "full_name": "Bonnie 王玮",   "password": _PWD, "is_admin": True},
    {"username": "mia",      "full_name": "Mia 虞靓",      "password": _PWD, "is_admin": True},
    {"username": "simon",    "full_name": "Simon 廖威",     "password": _PWD, "is_admin": True},
]


def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 创建所有表（如果不存在）
    # 注意：这只会创建users表，其他表已经通过.sql文件创建
    Base.metadata.create_all(bind=engine)
    print("✓ 数据表创建完成")
    
    # 创建默认用户
    db = SessionLocal()
    try:
        # 检查是否已存在admin用户
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                email="admin@company.com",
                is_admin=True,
                is_active=True
            )
            db.add(admin)
            print("✓ 创建管理员账号: admin / admin123")
        else:
            print("⚠ 管理员账号已存在，跳过")
        
        # 创建测试用户
        user = db.query(User).filter(User.username == "user").first()
        if not user:
            user = User(
                username="user",
                hashed_password=get_password_hash("user123"),
                full_name="测试用户",
                email="user@company.com",
                is_admin=False,
                is_active=True
            )
            db.add(user)
            print("✓ 创建普通用户: user / user123")
        else:
            print("⚠ 普通用户已存在，跳过")
        
        # 批量创建 USERS_TO_CREATE 中的账号
        for u in USERS_TO_CREATE:
            exists = db.query(User).filter(User.username == u["username"]).first()
            if not exists:
                db.add(User(
                    username=u["username"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    is_admin=u.get("is_admin", False),
                    is_active=True,
                ))
                print(f"✓ 创建用户: {u['username']} ({u['full_name']})")
            else:
                print(f"⚠ 已存在，跳过: {u['username']}")

        db.commit()
        print("\n✓ 数据库初始化完成！")
        
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()