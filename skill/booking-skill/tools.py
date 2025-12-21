"""
订舱技能工具集 - Booking Skill Tools
提供订舱提交和状态查询的 API 接口
"""

import json
import requests
from typing import Optional
from datetime import datetime


# API 配置
BOOKING_API_BASE_URL = "http://localhost:8000/api/v1"
API_TIMEOUT = 30


def submit_booking(
    shipper_name: str,
    consignee_name: str,
    origin_port: str,
    destination_port: str,
    cargo_description: str,
    container_type: str,
    number_of_containers: int,
    expected_departure_date: str,
    special_instructions: Optional[str] = None,
    reference_number: Optional[str] = None,
    commodity_type: Optional[str] = None
) -> str:
    """
    提交新的订舱申请
    
    Args:
        shipper_name: 发货人名称，1-100字符
        consignee_name: 收货人名称，1-100字符
        origin_port: 起运港，3-50字符
        destination_port: 目的港，3-50字符
        cargo_description: 货物描述，10-500字符
        container_type: 集装箱类型，必须是 20GP/40GP/40HQ/45HQ 之一
        number_of_containers: 集装箱数量，1-999
        expected_departure_date: 预计发货日期，格式 YYYY-MM-DD
        special_instructions: 特殊说明（可选），0-200字符
        reference_number: 参考号（可选），0-50字符
        commodity_type: 商品类型（可选），0-50字符
    
    Returns:
        JSON 格式的响应，包含订舱结果
    """
    # 验证必填字段
    errors = []
    
    # 字符串长度验证
    validations = [
        (shipper_name, "shipper_name", 1, 100),
        (consignee_name, "consignee_name", 1, 100),
        (origin_port, "origin_port", 3, 50),
        (destination_port, "destination_port", 3, 50),
        (cargo_description, "cargo_description", 10, 500),
    ]
    
    for value, field_name, min_len, max_len in validations:
        if not value:
            errors.append(f"{field_name} 是必填字段")
        elif len(value) < min_len or len(value) > max_len:
            errors.append(f"{field_name} 长度必须在 {min_len}-{max_len} 字符之间")
    
    # 集装箱类型验证
    valid_container_types = ["20GP", "40GP", "40HQ", "45HQ"]
    if container_type not in valid_container_types:
        errors.append(f"container_type 必须是以下之一: {', '.join(valid_container_types)}")
    
    # 集装箱数量验证
    if not isinstance(number_of_containers, int) or number_of_containers < 1 or number_of_containers > 999:
        errors.append("number_of_containers 必须是 1-999 之间的整数")
    
    # 日期格式验证
    try:
        datetime.strptime(expected_departure_date, "%Y-%m-%d")
    except ValueError:
        errors.append("expected_departure_date 必须是 YYYY-MM-DD 格式")
    
    # 可选字段长度验证
    if special_instructions and len(special_instructions) > 200:
        errors.append("special_instructions 长度不能超过 200 字符")
    if reference_number and len(reference_number) > 50:
        errors.append("reference_number 长度不能超过 50 字符")
    if commodity_type and len(commodity_type) > 50:
        errors.append("commodity_type 长度不能超过 50 字符")
    
    # 如果有验证错误，返回错误信息
    if errors:
        return json.dumps({
            "status": "error",
            "message": "数据验证失败",
            "errors": errors
        }, ensure_ascii=False, indent=2)
    
    # 构建请求数据
    booking_data = {
        "shipper_name": shipper_name,
        "consignee_name": consignee_name,
        "origin_port": origin_port,
        "destination_port": destination_port,
        "cargo_description": cargo_description,
        "container_type": container_type,
        "number_of_containers": number_of_containers,
        "expected_departure_date": expected_departure_date,
    }
    
    # 添加可选字段
    if special_instructions:
        booking_data["special_instructions"] = special_instructions
    if reference_number:
        booking_data["reference_number"] = reference_number
    if commodity_type:
        booking_data["commodity_type"] = commodity_type
    
    try:
        # 调用订舱 API
        response = requests.post(
            f"{BOOKING_API_BASE_URL}/bookings",
            json=booking_data,
            timeout=API_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            return json.dumps({
                "status": "success",
                "message": "订舱提交成功",
                "data": result
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": f"API 调用失败，状态码: {response.status_code}",
                "details": response.text
            }, ensure_ascii=False, indent=2)
            
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "status": "error",
            "message": "无法连接到订舱服务，请检查服务是否运行",
            "suggestion": "请联系系统管理员确认订舱服务状态"
        }, ensure_ascii=False, indent=2)
    except requests.exceptions.Timeout:
        return json.dumps({
            "status": "error",
            "message": "订舱服务响应超时",
            "suggestion": "请稍后重试或联系系统管理员"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"提交订舱时发生错误: {str(e)}"
        }, ensure_ascii=False, indent=2)


def query_booking_status(bill_of_lading_number: str) -> str:
    """
    根据提单号查询订舱状态
    
    Args:
        bill_of_lading_number: 提单号，至少5个字符
    
    Returns:
        JSON 格式的响应，包含订舱状态信息
    """
    # 验证提单号
    if not bill_of_lading_number or len(bill_of_lading_number) < 5:
        return json.dumps({
            "status": "error",
            "message": "提单号无效，至少需要5个字符"
        }, ensure_ascii=False, indent=2)
    
    try:
        # 调用状态查询 API
        response = requests.get(
            f"{BOOKING_API_BASE_URL}/bookings/{bill_of_lading_number}",
            timeout=API_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return json.dumps({
                "status": "success",
                "message": "查询成功",
                "data": result
            }, ensure_ascii=False, indent=2)
        elif response.status_code == 404:
            return json.dumps({
                "status": "error",
                "message": f"未找到提单号为 {bill_of_lading_number} 的订舱记录",
                "suggestion": "请确认提单号是否正确"
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": f"API 调用失败，状态码: {response.status_code}",
                "details": response.text
            }, ensure_ascii=False, indent=2)
            
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "status": "error",
            "message": "无法连接到订舱服务，请检查服务是否运行",
            "suggestion": "请联系系统管理员确认订舱服务状态"
        }, ensure_ascii=False, indent=2)
    except requests.exceptions.Timeout:
        return json.dumps({
            "status": "error",
            "message": "订舱服务响应超时",
            "suggestion": "请稍后重试或联系系统管理员"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"查询订舱状态时发生错误: {str(e)}"
        }, ensure_ascii=False, indent=2)
