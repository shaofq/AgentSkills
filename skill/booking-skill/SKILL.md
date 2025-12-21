---
name: booking-skill
description: 订舱管理技能，提供以下功能：
  1. 收集客户订舱数据并验证后提交
  2. 根据提单号查询订舱状态
  
  当客户需要提交新订舱或查询订舱状态时激活此技能。
freedom_level: medium
---

# 订舱技能使用指南

## 重要提示

**必须使用 tools.py 中提供的工具函数进行操作，禁止自行编写代码模拟 API 调用。**

## 可用工具

### 1. submit_booking - 提交订舱

提交新的订舱申请，调用方式：

```python
from skill.booking_skill.tools import submit_booking

result = submit_booking(
    shipper_name="发货人名称",           # 必填，1-100字符
    consignee_name="收货人名称",         # 必填，1-100字符
    origin_port="起运港",                # 必填，3-50字符
    destination_port="目的港",           # 必填，3-50字符
    cargo_description="货物描述",        # 必填，10-500字符
    container_type="20GP",               # 必填，20GP/40GP/40HQ/45HQ
    number_of_containers=1,              # 必填，1-999
    expected_departure_date="2025-01-15", # 必填，YYYY-MM-DD格式
    special_instructions="特殊说明",     # 可选，0-200字符
    reference_number="参考号",           # 可选，0-50字符
    commodity_type="商品类型"            # 可选，0-50字符
)
```

### 2. query_booking_status - 查询订舱状态

根据提单号查询订舱状态：

```python
from skill.booking_skill.tools import query_booking_status

result = query_booking_status(
    bill_of_lading_number="RCV0252YS3CM"  # 必填，至少5个字符
)
```

## 工作流程

### 提交订舱流程

1. **收集信息**：向客户询问所有必填字段
2. **确认信息**：向客户确认收集到的信息是否正确
3. **调用工具**：使用 `submit_booking` 函数提交
4. **返回结果**：将 API 响应格式化后返回给客户

### 查询状态流程

1. **获取提单号**：向客户询问提单号
2. **确认提单号**：确认提单号格式正确（至少5个字符）
3. **调用工具**：使用 `query_booking_status` 函数查询
4. **返回结果**：将查询结果格式化后返回给客户

## 错误处理

- 如果工具返回验证错误，向客户说明哪些字段需要修正
- 如果 API 连接失败，告知客户稍后重试
- 如果查询不到记录，建议客户确认提单号是否正确

## 响应格式

成功响应示例：
```json
{
  "status": "success",
  "message": "订舱提交成功",
  "data": {
    "booking_reference": "1759ZTWUIO",
    "bill_of_lading_number": "RCV0252YS3CM"
  }
}
```

错误响应示例：
```json
{
  "status": "error",
  "message": "数据验证失败",
  "errors": ["shipper_name 是必填字段"]
}
```
