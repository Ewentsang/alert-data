"""
测试 API 并查看日志的脚本
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_endpoint(method, path, data=None, description=""):
    """测试 API 端点"""
    url = f"{BASE_URL}{path}"
    print(f"\n测试: {method} {path}")
    if description:
        print(f"说明: {description}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=5)
        else:
            print(f"不支持的方法: {method}")
            return
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应: {response.text}")
        elif response.status_code == 404:
            print("❌ 404 错误 - 路径不存在")
            try:
                error_info = response.json()
                if "available_routes" in error_info:
                    print("\n可用路由:")
                    for route in error_info.get("available_routes", []):
                        print(f"  - {route}")
                if "suggestions" in error_info:
                    print("\n建议的端点:")
                    for key, value in error_info["suggestions"].items():
                        print(f"  - {key}: {value}")
            except:
                print(f"错误响应: {response.text}")
        else:
            print(f"响应: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("请确保服务正在运行: docker-compose up 或 python main.py")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

def main():
    print_section("API 测试和调试工具")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服务地址: {BASE_URL}")
    
    # 1. 测试健康检查
    print_section("1. 健康检查")
    test_endpoint("GET", "/health", description="检查服务是否运行")
    
    # 2. 查看所有路由
    print_section("2. 查看所有可用路由")
    test_endpoint("GET", "/debug/routes", description="显示所有注册的路由")
    
    # 3. 测试根路径
    print_section("3. 根路径")
    test_endpoint("GET", "/", description="获取服务信息")
    
    # 4. 测试创建告警（正确路径）
    print_section("4. 测试创建告警（正确路径: /api/alert）")
    test_data = {
        "input": "🔴 **【告警触发】监控告警**\n测试告警消息",
        "enterprise_name": "测试企业",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alert_type": "告警触发",
        "template_name": "测试模板",
        "om_type": "ConnectionRate",
        "alert_key": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    test_endpoint("POST", "/api/alert", data=test_data, description="创建告警记录")
    
    # 5. 测试错误路径（演示 404）
    print_section("5. 测试错误路径（演示 404 错误）")
    test_endpoint("POST", "/api/alerts", data=test_data, description="错误的路径（应该是 /api/alert）")
    
    # 6. 查询告警列表
    print_section("6. 查询告警列表")
    test_endpoint("GET", "/api/alerts", description="获取所有告警")
    
    # 7. 测试查询单个告警
    print_section("7. 查询单个告警")
    test_endpoint("GET", "/api/alerts/1", description="查询 ID=1 的告警")
    
    print_section("测试完成")
    print("\n💡 提示:")
    print("1. 如果出现 404 错误，请检查路径是否正确")
    print("2. 查看日志文件: app.log")
    print("3. 查看 Docker 日志: docker-compose logs -f backend")
    print("4. 使用 /debug/routes 查看所有可用路由")

if __name__ == "__main__":
    main()


