# -*- coding: utf-8 -*-
"""护照 OCR 识别服务 - 使用 qwen3-vl 多模态模型"""
import os
import base64
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from config.settings import DASHSCOPE_API_KEY


class PassportOCRService:
    """
    护照识别服务，使用 qwen3-vl 多模态模型提取护照信息。
    """
    
    PASSPORT_PROMPT = """你是一个专业的护照信息识别助手。请识别这张护照图片中的关键信息。

## 需要提取的字段
1. **surname** - 姓（英文）
2. **given_names** - 名（英文）
3. **full_name** - 完整姓名（英文）
4. **full_name_cn** - 中文姓名（如有）
5. **nationality** - 国籍
6. **date_of_birth** - 出生日期（格式：YYYY-MM-DD）
7. **sex** - 性别（M/F 或 男/女）
8. **place_of_birth** - 出生地点
9. **passport_no** - 护照号码
10. **date_of_issue** - 签发日期（格式：YYYY-MM-DD）
11. **date_of_expiry** - 有效期至（格式：YYYY-MM-DD）
12. **issuing_authority** - 签发机关

## 输出要求
请严格按照以下 JSON 格式输出，无法识别的字段填 null：
```json
{
  "surname": "ZHANG",
  "given_names": "SAN",
  "full_name": "ZHANG SAN",
  "full_name_cn": "张三",
  "nationality": "CHINA",
  "date_of_birth": "1990-01-15",
  "sex": "M",
  "place_of_birth": "BEIJING",
  "passport_no": "E12345678",
  "date_of_issue": "2020-01-01",
  "date_of_expiry": "2030-01-01",
  "issuing_authority": "MPS EXIT & ENTRY ADMINISTRATION",
  "confidence": 0.95,
  "raw_text": "原始识别文本..."
}
```

注意：
- 日期统一转换为 YYYY-MM-DD 格式
- 姓名统一大写
- 如果是克罗地亚等国护照，nationality 填写对应国家名
- confidence 表示整体识别置信度（0-1）
"""
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "qwen-vl-max-latest",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        self.api_key = api_key if api_key else DASHSCOPE_API_KEY
        if not self.api_key:
            self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        self.model_name = model_name
        self.base_url = base_url
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        print(f"[PassportOCR] 初始化完成: model={self.model_name}")
    
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_mime_type(self, image_path: str) -> str:
        """获取图片 MIME 类型"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }
        return mime_types.get(ext, "image/jpeg")
    
    async def recognize_passport(self, image_path: str) -> Dict[str, Any]:
        """
        识别护照图片，提取关键信息。
        
        Args:
            image_path: 护照图片路径
            
        Returns:
            护照信息字典
        """
        if not os.path.exists(image_path):
            return {"error": f"文件不存在: {image_path}"}
        
        print(f"[PassportOCR] 开始识别: {image_path}")
        
        # 编码图片
        base64_image = self._encode_image(image_path)
        mime_type = self._get_mime_type(image_path)
        
        try:
            import asyncio
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": self.PASSPORT_PROMPT
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            
            content = response.choices[0].message.content
            result = self._parse_response(content)
            result["image_path"] = image_path
            result["file_name"] = Path(image_path).name
            
            print(f"[PassportOCR] 识别完成: {result.get('full_name', 'Unknown')}")
            return result
            
        except Exception as e:
            print(f"[PassportOCR] 识别失败: {e}")
            return {
                "error": str(e),
                "image_path": image_path,
                "file_name": Path(image_path).name
            }
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析模型返回的 JSON 响应"""
        # 尝试匹配 ```json ... ``` 块
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 尝试直接匹配 JSON 对象
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return {"raw_text": content, "parse_error": "未找到JSON"}
        
        try:
            result = json.loads(json_str)
            result["raw_response"] = content
            return result
        except json.JSONDecodeError as e:
            return {"raw_text": content, "parse_error": str(e)}
    
    def normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """标准化日期格式为 YYYY-MM-DD"""
        if not date_str:
            return None
        
        # 移除空格
        date_str = date_str.strip()
        
        # 尝试各种日期格式
        import re
        from datetime import datetime
        
        patterns = [
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),  # 2020-01-15
            (r'(\d{4})/(\d{2})/(\d{2})', '%Y/%m/%d'),  # 2020/01/15
            (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),  # 15/01/2020
            (r'(\d{2})-(\d{2})-(\d{4})', '%d-%m-%Y'),  # 15-01-2020
            (r'(\d{8})', '%Y%m%d'),                     # 20200115
        ]
        
        for pattern, fmt in patterns:
            if re.match(pattern, date_str):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
        
        return date_str  # 无法解析则返回原值


# 单例实例
_passport_ocr_service: Optional[PassportOCRService] = None


def get_passport_ocr_service() -> PassportOCRService:
    """获取护照识别服务单例"""
    global _passport_ocr_service
    if _passport_ocr_service is None:
        _passport_ocr_service = PassportOCRService()
    return _passport_ocr_service
