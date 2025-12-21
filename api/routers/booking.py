"""
订舱 API 路由
提供订舱提交和状态查询的 REST API 端点
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import random
import string

router = APIRouter(prefix="/api/v1", tags=["booking"])

# 模拟数据库存储
bookings_db = {}


class BookingRequest(BaseModel):
    """订舱请求模型"""
    shipper_name: str = Field(..., min_length=1, max_length=100, description="发货人名称")
    consignee_name: str = Field(..., min_length=1, max_length=100, description="收货人名称")
    origin_port: str = Field(..., min_length=3, max_length=50, description="起运港")
    destination_port: str = Field(..., min_length=3, max_length=50, description="目的港")
    cargo_description: str = Field(..., min_length=10, max_length=500, description="货物描述")
    container_type: str = Field(..., description="集装箱类型")
    number_of_containers: int = Field(..., ge=1, le=999, description="集装箱数量")
    expected_departure_date: str = Field(..., description="预计发货日期")
    special_instructions: Optional[str] = Field(None, max_length=200, description="特殊说明")
    reference_number: Optional[str] = Field(None, max_length=50, description="参考号")
    commodity_type: Optional[str] = Field(None, max_length=50, description="商品类型")


class BookingResponse(BaseModel):
    """订舱响应模型"""
    booking_reference: str
    bill_of_lading_number: str
    status: str
    shipper_name: str
    consignee_name: str
    origin_port: str
    destination_port: str
    cargo_description: str
    container_type: str
    number_of_containers: int
    expected_departure_date: str
    special_instructions: Optional[str] = None
    created_at: str
    updated_at: str


def generate_reference(length: int = 10) -> str:
    """生成随机参考号"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_bol_number() -> str:
    """生成提单号"""
    prefix = ''.join(random.choices(string.ascii_uppercase, k=3))
    number = ''.join(random.choices(string.digits, k=9))
    return f"{prefix}{number}"


@router.post("/bookings", response_model=BookingResponse)
async def create_booking(request: BookingRequest):
    """
    创建新的订舱申请
    """
    # 验证集装箱类型
    valid_container_types = ["20GP", "40GP", "40HQ", "45HQ"]
    if request.container_type not in valid_container_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的集装箱类型，必须是以下之一: {', '.join(valid_container_types)}"
        )
    
    # 验证日期格式
    try:
        datetime.strptime(request.expected_departure_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式无效，必须是 YYYY-MM-DD 格式"
        )
    
    # 生成订舱信息
    booking_reference = generate_reference()
    bol_number = generate_bol_number()
    now = datetime.now().isoformat()
    
    # 创建订舱记录
    booking = BookingResponse(
        booking_reference=booking_reference,
        bill_of_lading_number=bol_number,
        status="Booking Confirmed",
        shipper_name=request.shipper_name,
        consignee_name=request.consignee_name,
        origin_port=request.origin_port,
        destination_port=request.destination_port,
        cargo_description=request.cargo_description,
        container_type=request.container_type,
        number_of_containers=request.number_of_containers,
        expected_departure_date=request.expected_departure_date,
        special_instructions=request.special_instructions,
        created_at=now,
        updated_at=now
    )
    
    # 存储到模拟数据库
    bookings_db[bol_number] = booking.model_dump()
    
    return booking


@router.get("/bookings/{bol_number}")
async def get_booking_status(bol_number: str):
    """
    根据提单号查询订舱状态
    """
    if len(bol_number) < 5:
        raise HTTPException(
            status_code=400,
            detail="提单号无效，至少需要5个字符"
        )
    
    # 查询订舱记录
    if bol_number in bookings_db:
        return bookings_db[bol_number]
    
    # 未找到记录
    raise HTTPException(
        status_code=404,
        detail=f"未找到提单号为 {bol_number} 的订舱记录"
    )


@router.get("/bookings")
async def list_bookings():
    """
    列出所有订舱记录
    """
    return list(bookings_db.values())
