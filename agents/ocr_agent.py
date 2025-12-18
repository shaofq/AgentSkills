# -*- coding: utf-8 -*-
"""OCR agent specialized in file content recognition."""
import aiohttp
from agentscope.message import Msg
from .base import BaseAgent


class OCRAgent(BaseAgent):
    """
    Specialized agent for OCR file recognition tasks.
    
    Skills:
    - ocr-file-reader: Recognize text from PDF and image files
    """
    
    DEFAULT_SYS_PROMPT = """你是一个专业的 OCR 文件识别助手 OCRReader。

## 你的专长

- 识别 PDF 文件中的文字内容
- 识别图片中的文字信息
- 提取文档中的结构化文本

## 工作原则

1. 接收用户提供的文件路径
2. 调用 OCR 服务识别文件内容
3. 返回清晰、格式化的识别结果
4. 对识别结果进行必要的整理和解释

## 支持的文件格式

- PDF 文件 (.pdf)
- 图片文件 (.png, .jpg, .jpeg, .bmp, .tiff)

## 使用说明

请提供需要识别的文件的完整路径，例如：
- /Users/xxx/documents/report.pdf
- /path/to/image.png
"""
    
    OCR_API_URL = "http://localhost:8009/api/ocr/filepath"
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "qwen3-max",
        max_iters: int = 10,
        skills: list = None,
        ocr_api_url: str = None,
    ):
        """Initialize the OCR agent."""
        default_skills = ["./skill/ocr-file-reader"]
        
        super().__init__(
            name="OCRReader",
            sys_prompt=self.DEFAULT_SYS_PROMPT,
            skills=skills or default_skills,
            api_key=api_key,
            model_name=model_name,
            max_iters=max_iters,
        )
        
        if ocr_api_url:
            self.OCR_API_URL = ocr_api_url
    
    async def recognize_file(self, file_path: str, dpi: int = 144, prompt_mode: str = "prompt_layout_all_en") -> str:
        """
        Call OCR API to recognize file content.
        
        Args:
            file_path: Path to the file to recognize
            dpi: Image resolution (default 144)
            prompt_mode: Recognition mode (default prompt_layout_all_en)
            
        Returns:
            Recognized text content
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "file_path": file_path,
                    "dpi": dpi,
                    "prompt_mode": prompt_mode
                }
                async with session.post(self.OCR_API_URL, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 根据实际 API 返回格式提取文本
                        if isinstance(result, dict):
                            return result.get("text", result.get("content", str(result)))
                        return str(result)
                    else:
                        error_text = await response.text()
                        return f"OCR 识别失败 (状态码: {response.status}): {error_text}"
        except Exception as e:
            return f"OCR 服务调用失败: {str(e)}"
    
    async def __call__(self, msg: Msg) -> Msg:
        """
        Process user message and perform OCR if file path is detected.
        
        Args:
            msg: Input message from user
            
        Returns:
            Response message with OCR result or agent response
        """
        user_input = msg.content if hasattr(msg, 'content') else str(msg)
        
        # 检测是否包含文件路径
        import re
        file_pattern = r'(/[^\s]+\.(pdf|png|jpg|jpeg|bmp|tiff))'
        matches = re.findall(file_pattern, user_input, re.IGNORECASE)
        
        if matches:
            # 提取文件路径并调用 OCR
            file_path = matches[0][0]
            print(f"[OCRAgent] 检测到文件路径: {file_path}")
            
            # 调用 OCR 识别
            ocr_result = await self.recognize_file(file_path)
            
            # 构建响应
            response_content = f"## OCR 识别结果\n\n**文件**: {file_path}\n\n### 识别内容\n\n{ocr_result}"
            
            return Msg(name=self.name, content=response_content, role="assistant")
        
        # 如果没有检测到文件路径，使用基类的处理逻辑
        return await super().__call__(msg)
