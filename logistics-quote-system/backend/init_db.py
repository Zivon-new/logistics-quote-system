# backend/init_db.py
"""
数据库初始化脚本

运行方式:
python init_db.py
"""
from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.core.security import get_password_hash

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
        
        db.commit()
        print("\n✓ 数据库初始化完成！")
        print("\n登录信息:")
        print("  管理员: admin / admin123")
        print("  普通用户: user / user123")
        
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()