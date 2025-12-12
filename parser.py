import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


def parse_alert_input(input_text: str) -> Dict[str, Optional[str]]:
    """
    从告警消息的 input 字段中解析出结构化信息
    
    示例 input:
    🔴 **【告警触发】监控告警**
    🌐 **区域 (Region):** IDN
    📊 **指标 (Metric):** ConnectionRate
    🔍 **规则名称 (Rule Name):** IDN-Enterprise-ConnectionRate
    🔗 **告警链接 (GeneratorURL):** https://...
    
    **告警摘要:**
    企业 KrediOne CG 的接通率
    
    **告警详情:**
    在过去十五分钟内的接通率为 14.03%
    呼叫量为 2776
    参考阈值: 0.5%~20%
    """
    result = {
        "alert_type": None,
        "region": None,
        "metric": None,
        "rule_name": None,
        "generator_url": None,
        "alert_summary": None,
        "alert_details": None,
        "script_name": None,
    }
    
    # 解析告警类型
    if "【告警触发】" in input_text:
        result["alert_type"] = "告警触发"
    elif "【告警恢复】" in input_text:
        result["alert_type"] = "告警恢复"
    
    # 解析区域
    region_match = re.search(r"\*\*区域\s*\(Region\):\*\*\s*(\w+)", input_text)
    if region_match:
        result["region"] = region_match.group(1).strip()
    
    # 解析指标
    metric_match = re.search(r"\*\*指标\s*\(Metric\):\*\*\s*(\w+)", input_text)
    if metric_match:
        result["metric"] = metric_match.group(1).strip()
    
    # 解析规则名称
    rule_match = re.search(r"\*\*规则名称\s*\(Rule Name\):\*\*\s*([^\n]+)", input_text)
    if rule_match:
        result["rule_name"] = rule_match.group(1).strip()
    
    # 解析告警链接（支持多种格式）
    url_match = re.search(r"\*\*告警链接\s*\(GeneratorURL\):\*\*\s*(https?://[^\s\n\)]+)", input_text)
    if url_match:
        result["generator_url"] = url_match.group(1).strip()
    
    # 解析告警摘要
    summary_match = re.search(r"\*\*告警摘要:\*\*\s*\n([^\n]+)", input_text)
    if summary_match:
        result["alert_summary"] = summary_match.group(1).strip()
    
    # 解析告警详情
    details_match = re.search(r"\*\*告警详情:\*\*\s*\n((?:.|\n)+?)(?=\n\n|\*\*|$)", input_text)
    if details_match:
        result["alert_details"] = details_match.group(1).strip()
    
    # 从告警摘要或详情中提取话术名称
    # 通常格式：企业 XXX 的接通率 或 企业 XXX CG 的接通率
    # 也可能在企业名称字段中已经提供了完整信息
    script_match = re.search(r"企业\s+([^的\n]+?)(?:\s+CG)?\s+的", input_text)
    if script_match:
        result["script_name"] = script_match.group(1).strip()
    
    # 如果从摘要中提取失败，尝试从 rule_name 中提取（如果包含企业信息）
    if not result["script_name"] and result["rule_name"]:
        # 规则名称可能包含企业信息，如 IDN-Enterprise-ConnectionRate
        # 这里可以根据实际规则命名规范进行调整
        pass
    
    return result


def parse_time(time_str: str) -> datetime:
    """解析时间字符串为 datetime 对象（北京时间）"""
    try:
        # 解析为本地时间（假设输入的是北京时间）
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        # 设置为北京时间时区
        return dt.replace(tzinfo=BEIJING_TZ)
    except ValueError:
        # 尝试其他格式
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
            return dt.replace(tzinfo=BEIJING_TZ)
        except ValueError:
            # 如果解析失败，使用当前北京时间
            return datetime.now(BEIJING_TZ)
