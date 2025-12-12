"""
测试 API 的简单脚本
"""
import requests
import json
from datetime import datetime

# API 基础 URL
BASE_URL = "http://localhost:8000"

# 测试告警触发数据
test_alert_trigger = {
    "input": """🔴 **【告警触发】监控告警**
🌐 **区域 (Region):** IDN
📊 **指标 (Metric):** ConnectionRate
🔍 **规则名称 (Rule Name):** IDN-Enterprise-ConnectionRate
🔗 **告警链接 (GeneratorURL):** https://monitor.talkbots.cn:443/alerting/grafana/eeze89xvvn7cwd/view?orgId=1

**告警摘要:**
企业 KrediOne CG 的接通率

**告警详情:**
在过去十五分钟内的接通率为 14.03%
呼叫量为 2776
参考阈值: 0.5%~20%""",
    "enterprise_name": "KrediOne CG",
    "time": "2025-12-10 10:25:34",
    "alert_type": "告警触发",
    "template_name": "KrediOne",
    "om_type": "ConnectionRate",
    "alert_key": "KrediOne_CG_ConnectionRate_20251210_102534"
}

# 测试告警恢复数据
test_alert_recovery = {
    "input": """✅ **【告警恢复】监控告警**
🌐 **区域 (Region):** IDN
📊 **指标 (Metric):** ConnectionRate
🔍 **规则名称 (Rule Name):** IDN-Enterprise-ConnectionRate
🔗 **告警链接 (GeneratorURL):** https://monitor.talkbots.cn:443/alerting/grafana/eeze89xvvn7cwd/view?orgId=1

**告警摘要:**
企业 Finture 的接通率

**告警详情:**
在过去十五分钟内的接通率为 10.45%
呼叫量为 766
参考阈值: 0.5%~20%""",
    "enterprise_name": "Finture",
    "time": "2025-12-10 09:25:33",
    "alert_type": "告警恢复",
    "template_name": "Finture",
    "om_type": "ConnectionRate",
    "alert_key": "Finture_ConnectionRate_20251210_092533"
}


def test_health_check():
    """测试健康检查"""
    print("测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}\n")


def test_create_alert(alert_data):
    """测试创建告警"""
    print(f"测试创建告警: {alert_data['enterprise_name']}")
    response = requests.post(
        f"{BASE_URL}/api/alert",
        json=alert_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
        return response.json()["id"]
    else:
        print(f"错误: {response.text}\n")
        return None


def test_get_alerts():
    """测试获取告警列表"""
    print("测试获取告警列表...")
    response = requests.get(f"{BASE_URL}/api/alerts?limit=10")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        alerts = response.json()
        print(f"返回 {len(alerts)} 条告警\n")
        for alert in alerts:
            print(f"  - ID: {alert['id']}, 企业: {alert['enterprise_name']}, 类型: {alert['alert_type']}")
    else:
        print(f"错误: {response.text}\n")


def test_get_alert(alert_id):
    """测试获取单个告警"""
    print(f"测试获取告警 ID: {alert_id}")
    response = requests.get(f"{BASE_URL}/api/alerts/{alert_id}")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")
    else:
        print(f"错误: {response.text}\n")


if __name__ == "__main__":
    print("=" * 50)
    print("API 测试脚本")
    print("=" * 50 + "\n")
    
    try:
        # 测试健康检查
        test_health_check()
        
        # 测试创建告警触发
        alert_id_1 = test_create_alert(test_alert_trigger)
        
        # 测试创建告警恢复
        alert_id_2 = test_create_alert(test_alert_recovery)
        
        # 测试获取告警列表
        test_get_alerts()
        
        # 测试获取单个告警
        if alert_id_1:
            test_get_alert(alert_id_1)
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请确保服务器正在运行 (python main.py)")
    except Exception as e:
        print(f"错误: {str(e)}")

