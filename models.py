from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertInput(BaseModel):
    """接收告警数据的模型"""
    input: str  # 告警消息内容
    enterprise_name: str  # 企业名称
    time: str  # 时间字符串，格式：YYYY-MM-DD HH:MM:SS
    alert_type: str  # 告警类型："告警触发" 或 "告警恢复"
    template_name: str  # 模板名称/话术名称
    om_type: str  # OM 类型
    alert_key: str  # 告警唯一标识键


class AlertResponse(BaseModel):
    """告警响应模型"""
    id: int
    input: str
    enterprise_name: str
    time: datetime
    alert_type: str
    template_name: str
    om_type: str
    alert_key: str
    processed: bool
    timeout_triggered: bool
    
    model_config = {"from_attributes": True}

