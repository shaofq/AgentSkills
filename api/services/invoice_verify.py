# -*- coding: utf-8 -*-
"""发票验证服务 - 模拟后台验证接口"""
import random
from datetime import datetime
from typing import Dict, Any, List, Optional


class InvoiceVerifyService:
    """发票验证服务（模拟）"""
    
    # 模拟的有效发票库
    VALID_INVOICES = {
        "35503648": {"amount": 48.00, "date": "2025-12-30", "seller": "天津高速路网运营管理有限公司"},
        "12345678": {"amount": 100.00, "date": "2025-01-01", "seller": "测试公司"},
        "87654321": {"amount": 200.50, "date": "2025-06-15", "seller": "示例企业"},
    }
    
    # 验证结果缓存
    _verify_cache: Dict[str, Dict] = {}
    
    @classmethod
    def verify_invoice(
        cls,
        invoice_no: str,
        amount: Optional[float] = None,
        invoice_date: Optional[str] = None,
        seller_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        验证发票信息。
        
        Args:
            invoice_no: 发票号码
            amount: 金额
            invoice_date: 开票日期
            seller_name: 销售方名称
            
        Returns:
            验证结果，包含:
            - passed: 是否通过
            - errors: 错误列表，每个错误包含 field(字段名) 和 message(错误信息)
            - invoice_info: 发票信息（如果查到）
        """
        result = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "invoice_no": invoice_no,
            "verified_at": datetime.now().isoformat(),
        }
        
        # 检查发票号是否存在
        if invoice_no not in cls.VALID_INVOICES:
            result["passed"] = False
            result["errors"].append({
                "field": "invoice_no",
                "field_name": "发票号码",
                "value": invoice_no,
                "message": f"发票号 {invoice_no} 在系统中未找到记录"
            })
            return result
        
        # 获取真实发票信息
        real_invoice = cls.VALID_INVOICES[invoice_no]
        result["invoice_info"] = real_invoice
        
        # 验证金额
        if amount is not None:
            real_amount = real_invoice["amount"]
            if abs(amount - real_amount) > 0.01:  # 允许0.01误差
                result["passed"] = False
                result["errors"].append({
                    "field": "amount",
                    "field_name": "金额",
                    "value": amount,
                    "expected": real_amount,
                    "message": f"金额不符：识别为 {amount}，实际应为 {real_amount}"
                })
        
        # 验证日期
        if invoice_date is not None:
            real_date = real_invoice["date"]
            # 简单比较，实际可能需要更复杂的日期处理
            if invoice_date != real_date:
                result["warnings"].append({
                    "field": "invoice_date",
                    "field_name": "开票日期",
                    "value": invoice_date,
                    "expected": real_date,
                    "message": f"日期可能不符：识别为 {invoice_date}，系统记录为 {real_date}"
                })
        
        # 验证销售方
        if seller_name is not None:
            real_seller = real_invoice["seller"]
            if seller_name not in real_seller and real_seller not in seller_name:
                result["warnings"].append({
                    "field": "seller_name",
                    "field_name": "销售方",
                    "value": seller_name,
                    "expected": real_seller,
                    "message": f"销售方名称可能不符"
                })
        
        # 缓存结果
        cls._verify_cache[invoice_no] = result
        
        return result
    
    @classmethod
    def extract_invoice_fields(cls, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        从 OCR 结果中提取发票关键字段。
        
        Args:
            ocr_result: OCR 识别结果
            
        Returns:
            提取的字段，包含:
            - invoice_no: 发票号码
            - amount: 金额
            - invoice_date: 开票日期
            - seller_name: 销售方
            - field_positions: 各字段对应的 block_id
        """
        import re
        
        extracted = {
            "invoice_no": None,
            "amount": None,
            "invoice_date": None,
            "seller_name": None,
            "field_positions": {}  # 字段名 -> block_id 的映射
        }
        
        # 获取 blocks（支持多页 PDF 结构）
        blocks = ocr_result.get("blocks", [])
        
        # 如果是多页 PDF，从 pages 中提取 blocks
        if not blocks and "pages" in ocr_result:
            for page in ocr_result.get("pages", []):
                blocks.extend(page.get("blocks", []))
        
        full_text = ocr_result.get("full_text", "")
        
        print(f"[InvoiceVerify] 提取字段，blocks 数量: {len(blocks)}")
        
        for block in blocks:
            text = block.get("text", "")
            block_id = block.get("id")
            
            print(f"[InvoiceVerify] Block {block_id}: {text[:50]}...")
            
            # 提取发票号码（支持多种格式）
            if extracted["invoice_no"] is None:
                # 1. 包含"发票号码"或"发票号"关键字
                if "发票号码" in text or "发票号" in text:
                    match = re.search(r'(\d{8,})', text)
                    if match:
                        extracted["invoice_no"] = match.group(1)
                        extracted["field_positions"]["invoice_no"] = block_id
                        print(f"[InvoiceVerify] 找到发票号(关键字): {extracted['invoice_no']}")
                # 2. 纯8位数字块
                elif re.match(r'^\d{8}$', text.strip()):
                    extracted["invoice_no"] = text.strip()
                    extracted["field_positions"]["invoice_no"] = block_id
                    print(f"[InvoiceVerify] 找到发票号(纯数字): {extracted['invoice_no']}")
                # 3. 包含"号码"并有数字
                elif "号码" in text:
                    match = re.search(r'(\d{8,})', text)
                    if match:
                        extracted["invoice_no"] = match.group(1)
                        extracted["field_positions"]["invoice_no"] = block_id
                        print(f"[InvoiceVerify] 找到发票号(号码): {extracted['invoice_no']}")
            
            # 提取金额
            if extracted["amount"] is None and ("金额" in text or "合计" in text or "¥" in text or "￥" in text):
                match = re.search(r'[¥￥]?\s*(\d+\.?\d*)', text)
                if match:
                    try:
                        extracted["amount"] = float(match.group(1))
                        extracted["field_positions"]["amount"] = block_id
                        print(f"[InvoiceVerify] 找到金额: {extracted['amount']}")
                    except:
                        pass
            
            # 提取日期
            if extracted["invoice_date"] is None and ("日期" in text or "年" in text):
                match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', text)
                if match:
                    extracted["invoice_date"] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    extracted["field_positions"]["invoice_date"] = block_id
                    print(f"[InvoiceVerify] 找到日期: {extracted['invoice_date']}")
            
            # 提取销售方名称
            if extracted["seller_name"] is None and "销" in text and "名" in text:
                match = re.search(r'称[：:]\s*(.+公司)', text)
                if match:
                    extracted["seller_name"] = match.group(1)
                    extracted["field_positions"]["seller_name"] = block_id
                    print(f"[InvoiceVerify] 找到销售方: {extracted['seller_name']}")
        
        # 如果从 blocks 中没找到发票号，尝试从 full_text 中提取
        if extracted["invoice_no"] is None and full_text:
            # 尝试匹配"发票号码：XXXXXXXX"格式
            match = re.search(r'发票号[码]?[：:]\s*(\d{8,})', full_text)
            if match:
                extracted["invoice_no"] = match.group(1)
                print(f"[InvoiceVerify] 从full_text找到发票号: {extracted['invoice_no']}")
        
        print(f"[InvoiceVerify] 提取结果: {extracted}")
        return extracted
    
    @classmethod
    def get_cached_result(cls, invoice_no: str) -> Optional[Dict]:
        """获取缓存的验证结果"""
        return cls._verify_cache.get(invoice_no)
    
    @classmethod
    def add_valid_invoice(cls, invoice_no: str, amount: float, date: str, seller: str):
        """添加有效发票到模拟库（用于测试）"""
        cls.VALID_INVOICES[invoice_no] = {
            "amount": amount,
            "date": date,
            "seller": seller
        }


# 单例
_invoice_verify_service: Optional[InvoiceVerifyService] = None


def get_invoice_verify_service() -> InvoiceVerifyService:
    """获取发票验证服务单例"""
    global _invoice_verify_service
    if _invoice_verify_service is None:
        _invoice_verify_service = InvoiceVerifyService()
    return _invoice_verify_service
