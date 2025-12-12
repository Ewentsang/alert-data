from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
import httpx
import asyncio
import os
import logging
import json
from typing import List

from database import get_db, Alert, init_db, SessionLocal
from models import AlertInput, AlertResponse
from parser import parse_time
from config import (
    DIFY_WEBHOOK_URL, 
    DIFY_WEBHOOK_URL_TIMEOUT, 
    DIFY_API_KEY,
    DIFY_USER_ID,
    ALERT_TIMEOUT_MINUTES,
    CHECK_INTERVAL_SECONDS
)

# 配置日志 - 使用北京时间
class BeijingFormatter(logging.Formatter):
    """使用北京时间的日志格式化器"""
    def formatTime(self, record, datefmt=None):
        # 获取北京时间
        beijing_tz = timezone(timedelta(hours=8))
        beijing_time = datetime.fromtimestamp(record.created, beijing_tz)
        
        if datefmt:
            return beijing_time.strftime(datefmt)
        else:
            # 默认格式：YYYY-MM-DD HH:MM:SS,毫秒
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]

# 创建日志处理器
file_handler = logging.FileHandler('app.log', encoding='utf-8')
console_handler = logging.StreamHandler()

# 设置格式化器（使用北京时间）
formatter = BeijingFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 配置根日志记录器
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Alert Database API", version="1.0.0")

# 添加 CORS 中间件（允许跨域请求）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求的详细信息"""
    # 使用北京时间
    beijing_tz = timezone(timedelta(hours=8))
    start_time = datetime.now(beijing_tz)
    
    # 记录请求基本信息（不读取 body，避免影响下游处理）
    log_data = {
        "timestamp": start_time.isoformat(),
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": {k: v for k, v in request.headers.items() if k.lower() not in ['authorization', 'cookie']},  # 排除敏感信息
        "client": request.client.host if request.client else None,
    }
    
    logger.info(f"收到请求: {request.method} {request.url.path}")
    logger.debug(f"请求详情: {json.dumps(log_data, indent=2, ensure_ascii=False)}")
    
    # 处理请求
    try:
        response = await call_next(request)
        
        # 记录响应信息（使用北京时间）
        process_time = (datetime.now(beijing_tz) - start_time).total_seconds()
        
        logger.info(f"响应: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)")
        
        # 如果是 404，记录详细信息
        if response.status_code == 404:
            logger.warning(f"404 错误 - 路径不存在: {request.url.path}")
            logger.warning(f"完整 URL: {request.url}")
            available_routes = []
            for route in app.routes:
                if hasattr(route, 'path'):
                    methods = list(route.methods) if hasattr(route, 'methods') and route.methods else ['GET']
                    available_routes.append(f"{methods[0]} {route.path}")
            logger.warning(f"可用路由 ({len(available_routes)} 个): {available_routes}")
        
        return response
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
        raise


@app.get("/")
async def root():
    """根路径，返回服务信息"""
    logger.info("访问根路径")
    return {
        "service": "Alert Database API",
        "version": "1.0.0",
        "description": "告警数据库服务 API",
        "endpoints": {
            "api_docs": "/docs",
            "api_redoc": "/redoc",
            "health": "/health",
            "create_alert": "POST /api/alert",
            "list_alerts": "GET /api/alerts",
            "get_alert": "GET /api/alerts/{alert_id}",
            "debug_routes": "GET /debug/routes"
        },
        "database": {
            "type": "PostgreSQL" if "postgresql" in os.getenv("DATABASE_URL", "").lower() else "SQLite",
            "status": "connected"
        }
    }


@app.get("/debug/routes")
async def debug_routes():
    """调试端点：显示所有注册的路由"""
    routes = []
    for route in app.routes:
        route_info = {
            "path": route.path,
            "methods": getattr(route, "methods", None),
            "name": getattr(route, "name", None),
        }
        routes.append(route_info)
    
    logger.info(f"查询所有路由，共 {len(routes)} 个")
    return {
        "total_routes": len(routes),
        "routes": routes
    }


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库和后台任务"""
    init_db()
    # 启动后台检查任务
    asyncio.create_task(check_timeout_alerts_periodically())
    # 启动定时删除任务
    asyncio.create_task(schedule_daily_cleanup())


@app.post("/api/alert", response_model=AlertResponse)
async def receive_alert(
    alert_data: AlertInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    接收来自 Dify workflow 的告警数据
    这个接口会被 Dify workflow 调用，接收筛选后的告警信息
    """
    logger.info(f"收到告警数据: 企业={alert_data.enterprise_name}, 类型={alert_data.om_type}")
    try:
        # 解析时间
        alert_time = parse_time(alert_data.time)
        logger.debug(f"解析后的时间: {alert_time}")
        
        # 创建告警记录
        alert = Alert(
            input=alert_data.input,
            enterprise_name=alert_data.enterprise_name,
            time=alert_time,
            alert_type=alert_data.alert_type,
            template_name=alert_data.template_name,
            om_type=alert_data.om_type,
            alert_key=alert_data.alert_key,
            processed=False,
            timeout_triggered=False
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"成功创建告警记录: ID={alert.id}")
        
        # 如果是"告警触发"，启动超时检查任务
        if alert_data.om_type == "告警触发":
            background_tasks.add_task(check_timeout_for_alert, alert.id)
            logger.info(f"已启动超时检查任务: 告警 ID={alert.id}")
        
        # 如果是"告警恢复"，取消所有匹配的"告警触发"的超时通知
        elif alert_data.om_type == "告警恢复":
            # 查找所有同 enterprise_name 和 alert_key 的未处理且未触发超时的"告警触发"记录
            matching_triggers = db.query(Alert).filter(
                and_(
                    Alert.enterprise_name == alert_data.enterprise_name,
                    Alert.alert_key == alert_data.alert_key,
                    Alert.om_type == "告警触发",
                    Alert.processed == False,  # 未处理
                    Alert.timeout_triggered == False,  # 未触发超时
                    Alert.time <= alert_time  # 告警恢复时间应该晚于告警触发时间
                )
            ).all()
            
            if matching_triggers:
                # 使用 processed 字段标记为已处理（因为收到告警恢复而取消）
                for trigger in matching_triggers:
                    trigger.processed = True
                db.commit()
                logger.info(f"告警恢复已取消 {len(matching_triggers)} 个匹配的告警触发的超时通知（标记为 processed=True）")
        
        response = AlertResponse(
            id=alert.id,
            input=alert.input,
            enterprise_name=alert.enterprise_name,
            time=alert.time,
            alert_type=alert.alert_type,
            template_name=alert.template_name,
            om_type=alert.om_type,
            alert_key=alert.alert_key,
            processed=alert.processed,
            timeout_triggered=alert.timeout_triggered
        )
        
        logger.info(f"返回响应: 告警 ID={alert.id}")
        return response
    except Exception as e:
        db.rollback()
        logger.error(f"处理告警数据时出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理告警数据时出错: {str(e)}")


async def check_timeout_for_alert(alert_id: int):
    """
    检查特定告警是否超时（20分钟内没有收到同 enterprise_name 和 alert_key 的"告警恢复"）
    """
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert or alert.om_type != "告警触发":
            logger.debug(f"[异步任务] 告警 ID={alert_id} 不是告警触发类型或不存在，跳过检查")
            return
        
        logger.info(f"[异步任务] 启动超时检查任务: 告警 ID={alert.id}, "
                   f"告警时间={alert.time.strftime('%Y-%m-%d %H:%M:%S')}, "
                   f"企业={alert.enterprise_name}, "
                   f"alert_key={alert.alert_key}, "
                   f"等待{ALERT_TIMEOUT_MINUTES}分钟后检查")
        
        # 等待超时时间
        wait_seconds = ALERT_TIMEOUT_MINUTES * 60
        logger.info(f"[异步任务] 等待 {wait_seconds} 秒 ({ALERT_TIMEOUT_MINUTES} 分钟)...")
        await asyncio.sleep(wait_seconds)
        
        # 重新查询（可能已更新）- 使用新的数据库会话确保读取最新数据
        db.close()  # 关闭旧会话
        db = SessionLocal()  # 创建新会话
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        # 如果已被处理（收到告警恢复）或已触发超时，则不再处理
        if not alert:
            logger.debug(f"[异步任务] 告警 ID={alert_id} 已不存在，跳过检查")
            return
        if alert.processed:
            logger.info(f"[异步任务] 告警 ID={alert_id} 已被处理（收到告警恢复），跳过超时检查")
            return
        if alert.timeout_triggered:
            logger.info(f"[异步任务] 告警 ID={alert_id} 已触发超时通知（可能由定期检查触发），跳过重复检查")
            return
        
        # 检查20分钟内是否有同 enterprise_name 和 alert_key 的"告警恢复"
        # 开始时间：使用数据库中的 time 字段（告警触发时间）
        check_start_time = alert.time
        # 结束时间：开始时间 + 20分钟
        check_end_time = check_start_time + timedelta(minutes=ALERT_TIMEOUT_MINUTES)
        
        logger.info(f"[异步任务] 检查告警 ID={alert.id}: "
                   f"开始时间={check_start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                   f"结束时间={check_end_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                   f"企业={alert.enterprise_name}, "
                   f"alert_key={alert.alert_key}")
        
        recent_recovery = db.query(Alert).filter(
            and_(
                Alert.enterprise_name == alert.enterprise_name,
                Alert.alert_key == alert.alert_key,
                Alert.om_type == "告警恢复",
                Alert.time > check_start_time,  # 告警恢复时间应该晚于告警触发时间（数据库中的time字段）
                Alert.time <= check_end_time    # 告警恢复时间必须在20分钟内
            )
        ).first()
        
        # 如果没有找到"告警恢复"，触发超时通知
        if not recent_recovery:
            # 再次检查 timeout_triggered，防止并发情况下定期检查已经触发
            db.refresh(alert)  # 刷新对象，确保读取最新数据
            if alert.timeout_triggered:
                logger.info(f"[异步任务] 告警 ID={alert.id} 在检查期间已被定期检查触发超时，跳过重复触发")
                return
            
            logger.warning(f"[异步任务] ⚠️ 告警触发超时! ID={alert.id}, "
                          f"告警时间={check_start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                          f"企业={alert.enterprise_name}, "
                          f"alert_key={alert.alert_key}, "
                          f"未在{ALERT_TIMEOUT_MINUTES}分钟内收到告警恢复")
            await trigger_timeout_workflow(alert)
            # 标记为已触发
            alert.timeout_triggered = True
            db.commit()
            logger.info(f"[异步任务] ✅ 已触发超时通知并标记: 告警 ID={alert.id}")
        else:
            logger.info(f"[异步任务] ✓ 告警触发已收到恢复: ID={alert.id}, "
                       f"恢复时间={recent_recovery.time.strftime('%Y-%m-%d %H:%M:%S')}, "
                       f"告警时间={check_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    finally:
        db.close()


async def check_timeout_alerts_periodically():
    """
    定期检查所有未处理的"告警触发"是否超时
    这是一个额外的保障机制，防止异步任务丢失
    """
    logger.info(f"定期检查任务已启动，检查间隔: {CHECK_INTERVAL_SECONDS}秒，超时时间: {ALERT_TIMEOUT_MINUTES}分钟")
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            db = SessionLocal()
            try:
                # 查找所有未处理的"告警触发"记录（使用北京时间）
                # 注意：不再使用 cutoff_time 筛选，而是检查所有未处理的告警
                beijing_tz = timezone(timedelta(hours=8))
                now = datetime.now(beijing_tz)
                
                logger.info(f"[定期检查] 开始检查超时告警 - 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 查找所有未处理的"告警触发"记录（不再使用 time <= cutoff_time 筛选）
                timeout_alerts = db.query(Alert).filter(
                    and_(
                        Alert.om_type == "告警触发",
                        Alert.processed == False,  # 未处理（未收到告警恢复）
                        Alert.timeout_triggered == False  # 未触发超时
                        # ✅ 移除 Alert.time <= cutoff_time 筛选条件
                    )
                ).all()
                
                if timeout_alerts:
                    logger.info(f"[定期检查] 找到 {len(timeout_alerts)} 个未处理的告警触发记录")
                    for a in timeout_alerts:
                        logger.info(f"[定期检查]   - 告警 ID={a.id}, 时间={a.time.strftime('%Y-%m-%d %H:%M:%S')}, 企业={a.enterprise_name}, alert_key={a.alert_key}")
                else:
                    logger.info(f"[定期检查] 未找到未处理的告警触发记录")
                
                for alert in timeout_alerts:
                    # 确定检查窗口（基于告警的 time 字段）
                    # 处理时区：如果 alert.time 没有时区信息，添加北京时间时区
                    check_start_time = alert.time
                    if check_start_time.tzinfo is None:
                        beijing_tz = timezone(timedelta(hours=8))
                        check_start_time = check_start_time.replace(tzinfo=beijing_tz)
                    
                    check_end_time = check_start_time + timedelta(minutes=ALERT_TIMEOUT_MINUTES)
                    
                    # ✅ 判断检查窗口是否已过期
                    if now <= check_end_time:
                        # 窗口未过期，跳过（不触发超时）
                        logger.info(f"[定期检查] 告警 ID={alert.id} 检查窗口未过期，跳过检查 "
                                  f"(当前时间={now.strftime('%H:%M:%S')}, "
                                  f"窗口结束时间={check_end_time.strftime('%H:%M:%S')})")
                        continue
                    
                    # 窗口已过期，继续检查是否有恢复
                    # 计算已过去的时间
                    time_elapsed = (now - check_start_time).total_seconds() / 60  # 转换为分钟
                    
                    # 计算检查窗口的间隔时间（秒）
                    window_duration = (check_end_time - check_start_time).total_seconds()
                    
                    logger.info(f"[定期检查] 检查告警 ID={alert.id}: "
                              f"告警时间={check_start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                              f"检查窗口开始={check_start_time.strftime('%H:%M:%S')}, "
                              f"检查窗口结束={check_end_time.strftime('%H:%M:%S')}, "
                              f"间隔时间={window_duration:.1f}秒, "
                              f"已过去={time_elapsed:.2f}分钟, "
                              f"企业={alert.enterprise_name}, "
                              f"alert_key={alert.alert_key}")
                    
                    # 检查窗口内是否有对应的"告警恢复"
                    recent_recovery = db.query(Alert).filter(
                        and_(
                            Alert.enterprise_name == alert.enterprise_name,
                            Alert.alert_key == alert.alert_key,
                            Alert.om_type == "告警恢复",
                            Alert.time >= check_start_time,  # 告警恢复时间应该晚于或等于告警触发时间
                            Alert.time <= check_end_time     # 告警恢复时间必须在检查窗口内
                        )
                    ).first()
                    
                    # 如果窗口已过期且没有找到"告警恢复"，触发超时通知
                    if not recent_recovery:
                        logger.warning(f"[定期检查] ⚠️ 告警触发超时! ID={alert.id}, "
                                     f"告警时间={check_start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                                     f"已过去={time_elapsed:.2f}分钟, "
                                     f"企业={alert.enterprise_name}, "
                                     f"alert_key={alert.alert_key}")
                        await trigger_timeout_workflow(alert)
                        alert.timeout_triggered = True
                        db.commit()
                        logger.info(f"[定期检查] ✅ 已触发超时通知并标记: 告警 ID={alert.id}")
                    else:
                        logger.info(f"[定期检查] ✓ 告警触发已收到恢复: ID={alert.id}, "
                                  f"恢复时间={recent_recovery.time.strftime('%Y-%m-%d %H:%M:%S')}, "
                                  f"告警时间={check_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[定期检查] ❌ 检查超时告警时出错: {str(e)}", exc_info=True)


async def trigger_timeout_workflow(alert: Alert):
    """
    触发超时后的 Dify workflow API
    使用 Dify 官方 API 格式：POST /v1/workflows/run
    在 inputs 中发送 input、enterprise_name、time 三个字段
    """
    logger.info(f"[触发超时] 准备触发超时通知: 告警 ID={alert.id}, 企业={alert.enterprise_name}, alert_key={alert.alert_key}")
    
    if not DIFY_WEBHOOK_URL_TIMEOUT:
        logger.error(f"[触发超时] ❌ 未配置 DIFY_WEBHOOK_URL_TIMEOUT，无法触发超时通知! 告警 ID={alert.id}")
        return
    
    if not DIFY_API_KEY:
        logger.warning(f"[触发超时] ⚠️ 未配置 DIFY_API_KEY，将尝试不使用认证发送请求")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 格式化时间为字符串（北京时间格式：YYYY-MM-DD HH:MM:SS）
            if isinstance(alert.time, datetime):
                # 如果有时区信息，转换为北京时间
                if alert.time.tzinfo:
                    beijing_tz = timezone(timedelta(hours=8))
                    beijing_time = alert.time.astimezone(beijing_tz)
                    time_str = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # 如果没有时区信息，直接格式化
                    time_str = alert.time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = str(alert.time)
            
            # 按照 Dify 官方 API 格式构建请求
            # inputs 字段包含工作流变量
            payload = {
                "inputs": {
                    "input": alert.input,
                    "enterprise_name": alert.enterprise_name,
                    "time": time_str
                },
                "response_mode": "blocking",  # 阻塞模式，等待响应
                "user": DIFY_USER_ID
            }
            
            # 构建请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            # 如果配置了 API Key，添加到 Authorization header
            if DIFY_API_KEY:
                headers["Authorization"] = f"Bearer {DIFY_API_KEY}"
            
            logger.info(f"[触发超时] 发送超时通知到 Dify workflow，告警 ID: {alert.id}")
            logger.info(f"[触发超时] 请求 URL: {DIFY_WEBHOOK_URL_TIMEOUT}")
            logger.info(f"[触发超时] 请求 Headers: {json.dumps({k: v if k != 'Authorization' else 'Bearer ***' for k, v in headers.items()}, ensure_ascii=False)}")
            logger.info(f"[触发超时] 请求 Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            response = await client.post(
                DIFY_WEBHOOK_URL_TIMEOUT,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"[触发超时] ✅ 成功触发超时通知 workflow，告警 ID: {alert.id}, 响应状态: {response.status_code}")
            
            # 记录响应内容（如果有）
            if response.text:
                logger.info(f"[触发超时] 响应内容: {response.text[:500]}")  # 只记录前500字符
    except httpx.HTTPStatusError as e:
        logger.error(f"[触发超时] ❌ HTTP 错误: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"[触发超时] ❌ 触发超时通知 workflow 时出错: {str(e)}", exc_info=True)


async def delete_old_alerts():
    """
    删除旧数据：每天删除前一天的记录
    保留条件：昨天 23:35 之后且未处理且未超时的记录
    """
    beijing_tz = timezone(timedelta(hours=8))
    db = SessionLocal()
    try:
        now = datetime.now(beijing_tz)
        # 计算时间边界
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_23_35 = today_start - timedelta(minutes=25)  # 昨天 23:35:00
        
        logger.info(f"[定时删除] 开始执行定时删除任务 - 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"[定时删除] 删除时间范围: < {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"[定时删除] 保留时间窗口: {yesterday_23_35.strftime('%Y-%m-%d %H:%M:%S')} ~ {today_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 统计：查询所有需要删除的记录（用于日志）
        all_to_delete = db.query(Alert).filter(
            Alert.time < today_start
        ).all()
        
        # 统计：查询保留的记录
        kept_records = db.query(Alert).filter(
            and_(
                Alert.time >= yesterday_23_35,
                Alert.time < today_start,
                Alert.timeout_triggered == False,
                Alert.processed == False
            )
        ).all()
        
        # 统计：按类型分组
        to_delete_by_type = {
            "告警触发": 0,
            "告警恢复": 0,
            "其他": 0
        }
        kept_by_type = {
            "告警触发": 0,
            "告警恢复": 0,
            "其他": 0
        }
        
        for alert in all_to_delete:
            # 检查是否应该保留
            should_keep = (
                alert.time >= yesterday_23_35
                and alert.time < today_start
                and alert.timeout_triggered == False
                and alert.processed == False
            )
            
            if not should_keep:
                # 统计要删除的记录
                om_type = alert.om_type or "其他"
                if om_type in to_delete_by_type:
                    to_delete_by_type[om_type] += 1
                else:
                    to_delete_by_type["其他"] += 1
        
        for alert in kept_records:
            # 统计保留的记录
            om_type = alert.om_type or "其他"
            if om_type in kept_by_type:
                kept_by_type[om_type] += 1
            else:
                kept_by_type["其他"] += 1
        
        # 执行删除
        # 删除条件1：所有前几天的数据 + 昨天23:35之前的数据
        deleted_count_1 = db.query(Alert).filter(
            Alert.time < yesterday_23_35
        ).delete(synchronize_session=False)
        
        # 删除条件2：昨天23:35-23:59:59之间，但已处理或已超时的数据
        deleted_count_2 = db.query(Alert).filter(
            and_(
                Alert.time >= yesterday_23_35,
                Alert.time < today_start,
                or_(Alert.timeout_triggered == True, Alert.processed == True)
            )
        ).delete(synchronize_session=False)
        
        db.commit()
        deleted_count = deleted_count_1 + deleted_count_2
        
        # 记录日志
        logger.info(f"[定时删除] ✅ 删除完成")
        logger.info(f"[定时删除] 删除记录总数: {deleted_count}")
        logger.info(f"[定时删除] 删除记录统计 - 告警触发: {to_delete_by_type['告警触发']}, 告警恢复: {to_delete_by_type['告警恢复']}, 其他: {to_delete_by_type['其他']}")
        logger.info(f"[定时删除] 保留记录总数: {len(kept_records)}")
        logger.info(f"[定时删除] 保留记录统计 - 告警触发: {kept_by_type['告警触发']}, 告警恢复: {kept_by_type['告警恢复']}, 其他: {kept_by_type['其他']}")
        
        # 如果有保留的记录，记录详细信息
        if kept_records:
            logger.info(f"[定时删除] 保留的记录详情:")
            for alert in kept_records:
                logger.info(f"[定时删除]   - ID={alert.id}, time={alert.time.strftime('%Y-%m-%d %H:%M:%S')}, "
                          f"om_type={alert.om_type}, enterprise_name={alert.enterprise_name}, "
                          f"alert_key={alert.alert_key}")
        
    except Exception as e:
        logger.error(f"[定时删除] ❌ 删除旧数据时出错: {str(e)}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def schedule_daily_cleanup():
    """
    定时删除任务调度器：每天 00:00:05 执行删除
    """
    beijing_tz = timezone(timedelta(hours=8))
    logger.info(f"[定时删除] 定时删除任务调度器已启动，将在每天 00:00:05 执行删除")
    
    while True:
        try:
            now = datetime.now(beijing_tz)
            # 计算下一次执行时间（今天或明天的 00:00:05）
            next_run = now.replace(hour=0, minute=0, second=5, microsecond=0)
            if next_run <= now:
                # 如果今天的 00:00:05 已过，则设置为明天的 00:00:05
                next_run += timedelta(days=1)
            
            # 计算需要等待的秒数
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"[定时删除] 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}, 等待 {wait_seconds:.0f} 秒")
            
            # 等待到执行时间
            await asyncio.sleep(wait_seconds)
            
            # 执行删除
            await delete_old_alerts()
            
        except Exception as e:
            logger.error(f"[定时删除] ❌ 定时删除任务调度器出错: {str(e)}", exc_info=True)
            # 出错后等待 1 小时再重试
            await asyncio.sleep(3600)


@app.get("/api/alerts", response_model=List[AlertResponse])
async def get_alerts(
    enterprise_name: str = None,
    alert_type: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """查询告警列表"""
    query = db.query(Alert)
    
    if enterprise_name:
        query = query.filter(Alert.enterprise_name == enterprise_name)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    alerts = query.order_by(Alert.time.desc()).offset(skip).limit(limit).all()
    return [AlertResponse.model_validate(alert) for alert in alerts]


@app.get("/api/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """查询单个告警详情"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警记录不存在")
    return AlertResponse.model_validate(alert)


@app.get("/health")
async def health_check():
    """健康检查"""
    logger.debug("健康检查请求")
    return {"status": "ok"}


# 404 错误处理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """自定义 404 错误处理，记录详细信息"""
    logger.warning(f"404 错误 - 请求路径: {request.url.path}")
    logger.warning(f"请求方法: {request.method}")
    logger.warning(f"请求 URL: {request.url}")
    logger.warning(f"可用路由: {[route.path for route in app.routes]}")
    
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"路径 '{request.url.path}' 不存在",
            "method": request.method,
            "available_routes": [route.path for route in app.routes],
            "suggestions": {
                "create_alert": "POST /api/alert",
                "list_alerts": "GET /api/alerts",
                "get_alert": "GET /api/alerts/{alert_id}",
                "health": "GET /health",
                "api_docs": "GET /docs"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

