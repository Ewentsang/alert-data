from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta
from config import DATABASE_URL

# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

# 配置数据库连接，设置时区
if "postgresql" in DATABASE_URL.lower():
    # PostgreSQL: 在连接参数中设置时区
    connect_args = {
        "options": "-c timezone=Asia/Shanghai"
    }
else:
    # SQLite: 不需要特殊配置，在应用层处理时区
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Alert(Base):
    """告警数据表"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 直接输入的字段
    input = Column(Text)  # 告警消息内容
    enterprise_name = Column(String(200), index=True)  # 企业名称
    time = Column(DateTime, index=True)  # 告警时间
    alert_type = Column(String(50), index=True)  # 告警类型："告警触发" 或 "告警恢复"
    template_name = Column(String(200), index=True)  # 模板名称/话术名称
    om_type = Column(String(100))  # OM 类型
    alert_key = Column(String(200), index=True)  # 告警唯一标识键
    
    # 状态字段
    processed = Column(Boolean, default=False)  # 是否已处理
    timeout_triggered = Column(Boolean, default=False)  # 是否已触发超时通知
    
    # 时间戳（使用北京时间）
    created_at = Column(DateTime, default=lambda: beijing_now())
    updated_at = Column(DateTime, default=lambda: beijing_now(), onupdate=lambda: beijing_now())


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

