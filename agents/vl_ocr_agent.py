# -*- coding: utf-8 -*-
"""VL OCR Agent - 使用 qwen3-vl 模型实现 OCR 识别，支持定位信息"""
import os
import base64
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
from config.settings import DASHSCOPE_API_KEY


class VLOCRAgent:
    """
    基于视觉语言模型的 OCR 智能体。
    支持 PDF 和图片的文字识别，可返回定位信息。
    """
    
    DEFAULT_MODEL = "qwen-vl-flash"
    DEFAULT_SYS_PROMPT = """你是一个专业的 OCR 识别助手，使用视觉能力识别图片和文档中的文字。

## 任务要求
1. 识别图片/文档中的所有文字内容
2. 返回每个文字区域的定位信息（边界框坐标）
3. 按照从上到下、从左到右的阅读顺序组织结果

## 输出格式
请严格按照以下 JSON 格式输出：
```json
{
  "blocks": [
    {
      "id": 1,
      "text": "识别的文字内容",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95,
      "type": "text|title|table|list"
    }
  ],
  "full_text": "完整的文本内容，按阅读顺序拼接",
  "page_info": {
    "width": 页面宽度,
    "height": 页面高度
  }
}
```

## 注意事项
- bbox 坐标为 [左上角x, 左上角y, 右下角x, 右下角y]，相对于图片尺寸的比例值(0-1)
- type 字段标识文本类型：text(正文)、title(标题)、table(表格)、list(列表)
- 确保返回有效的 JSON 格式
"""
    
    def __init__(
        self,
        api_key: str = "",
        model_name: str = "qwen3-vl-flash",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        """
        初始化 VL OCR 智能体。
        
        Args:
            api_key: DashScope API 密钥
            model_name: 模型名称，默认 qwen-vl-max-latest
            base_url: API 基础 URL
        """
        # 优先使用传入的 api_key，否则从环境变量读取
        self.api_key = api_key if api_key else DASHSCOPE_API_KEY
        if not self.api_key:
            import os
            self.api_key = os.environ.get("DASHSCOPE_API_KEY", "")
        self.model_name = model_name
        self.base_url = base_url
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
        print(f"[VLOCRAgent] 初始化完成:")
        print(f"  - api_key: {self.api_key[:8]}...{self.api_key[-4:] if len(self.api_key) > 12 else ''}")
        print(f"  - model: {self.model_name}")
        print(f"  - base_url: {self.base_url}")
    
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_image_mime_type(self, image_path: str) -> str:
        """获取图片的 MIME 类型"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
        }
        return mime_types.get(ext, "image/jpeg")
    
    def _convert_pdf_to_images(self, pdf_path: str, dpi: int = 150) -> List[str]:
        """
        将 PDF 转换为图片列表。
        
        Args:
            pdf_path: PDF 文件路径
            dpi: 转换分辨率
            
        Returns:
            图片文件路径列表
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("请安装 PyMuPDF: pip install PyMuPDF")
        
        doc = fitz.open(pdf_path)
        image_paths = []
        
        # 创建临时目录
        temp_dir = Path("/tmp/vl_ocr_images")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # 设置缩放因子
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # 保存为图片
            image_path = temp_dir / f"{Path(pdf_path).stem}_page_{page_num + 1}.png"
            pix.save(str(image_path))
            image_paths.append(str(image_path))
            
            # 打印第一页的图片尺寸
            if page_num == 0:
                print(f"[VLOCRAgent] PDF 第1页转图片: {pix.width}x{pix.height}")
        
        doc.close()
        return image_paths
    
    async def recognize(
        self,
        file_path: str,
        dpi: int = 150,
        return_positions: bool = True,
    ) -> Dict[str, Any]:
        """
        识别文件内容。
        
        Args:
            file_path: 文件路径 (PDF 或图片)
            dpi: PDF 转换分辨率
            return_positions: 是否返回定位信息
            
        Returns:
            识别结果，包含文本和定位信息
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {"error": f"文件不存在: {file_path}"}
        
        # 判断文件类型
        ext = file_path.suffix.lower()
        
        if ext == ".pdf":
            # PDF 文件：转换为图片后逐页识别
            image_paths = self._convert_pdf_to_images(str(file_path), dpi)
            results = []
            
            for i, img_path in enumerate(image_paths):
                page_result = await self._recognize_image(img_path, return_positions)
                page_result["page"] = i + 1
                results.append(page_result)
                
                # 清理临时图片
                try:
                    os.remove(img_path)
                except:
                    pass
            
            # 合并结果
            return self._merge_results(results, str(file_path))
        else:
            # 图片文件：直接识别
            result = await self._recognize_image(str(file_path), return_positions)
            result["file_path"] = str(file_path)
            result["page"] = 1
            result["total_pages"] = 1
            return result
    
    def _get_image_size(self, image_path: str) -> tuple:
        """获取图片尺寸"""
        from PIL import Image
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    
    def _normalize_bbox(self, bbox: list, img_width: int, img_height: int) -> list:
        """将坐标转换为 0-1 比例值"""
        if not bbox or len(bbox) != 4:
            return bbox
        x1, y1, x2, y2 = bbox
        
        # 如果坐标已经是比例值（0-1），直接返回
        if all(0 <= v <= 1 for v in [x1, y1, x2, y2]):
            return bbox
        
        # 如果是 0-1000 范围的归一化坐标，转换为 0-1
        if all(0 <= v <= 1000 for v in [x1, y1, x2, y2]) and max(x1, y1, x2, y2) > 1:
            return [
                x1 / 1000,
                y1 / 1000,
                x2 / 1000,
                y2 / 1000
            ]
        
        # 否则假设是像素坐标，转换为比例值
        return [
            x1 / img_width,
            y1 / img_height,
            x2 / img_width,
            y2 / img_height
        ]
    
    async def _recognize_image(
        self,
        image_path: str,
        return_positions: bool = True,
    ) -> Dict[str, Any]:
        """
        识别单张图片。
        
        Args:
            image_path: 图片路径
            return_positions: 是否返回定位信息
            
        Returns:
            识别结果
        """
        # 获取图片尺寸（用于坐标转换）
        try:
            img_width, img_height = self._get_image_size(image_path)
        except:
            img_width, img_height = 1000, 1000  # 默认值
        
        # 编码图片
        base64_image = self._encode_image(image_path)
        mime_type = self._get_image_mime_type(image_path)
        
        # 构建提示词
        if return_positions:
            prompt = f"""请对这张图片进行OCR识别，输出所有文字内容及其边界框坐标。

要求：
1. 识别图片中的每一段文字
2. 为每段文字提供精确的边界框坐标 <box>x1,y1,x2,y2</box>
3. 坐标使用 0-1000 的归一化值（相对于图片宽高的千分比）

输出JSON格式：
```json
{{
  "blocks": [
    {{"id": 1, "text": "文字内容", "bbox": [x1, y1, x2, y2]}}
  ]
}}
```

bbox 说明：
- 使用 0-1000 范围的归一化坐标
- x1,y1 是左上角，x2,y2 是右下角
- 例如：图片左上角1/4区域的文字，bbox 约为 [0, 0, 250, 250]

请逐行识别，确保每个文字块的边界框准确包围对应文字。"""
        else:
            prompt = "请识别这张图片中的所有文字内容，按阅读顺序输出。"
        
        try:
            # 使用 asyncio.to_thread 避免阻塞事件循环
            import asyncio
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.DEFAULT_SYS_PROMPT,
                    },
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
                                "text": prompt
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析 JSON
            if return_positions:
                result = self._parse_json_response(content)
                
                # 将像素坐标转换为比例值
                if "blocks" in result and result["blocks"]:
                    print(f"[VLOCRAgent] 图片尺寸: {img_width}x{img_height}")
                    print(f"[VLOCRAgent] 原始第一个 bbox: {result['blocks'][0].get('bbox')}")
                    for block in result["blocks"]:
                        if "bbox" in block:
                            block["bbox"] = self._normalize_bbox(
                                block["bbox"], img_width, img_height
                            )
                    print(f"[VLOCRAgent] 转换后第一个 bbox: {result['blocks'][0].get('bbox')}")
                
                # 记录图片尺寸
                result["page_info"] = {
                    "width": img_width,
                    "height": img_height
                }
            else:
                result = {
                    "full_text": content,
                    "blocks": [],
                    "page_info": {"width": img_width, "height": img_height}
                }
            
            return result
            
        except Exception as e:
            print(f"[VLOCRAgent] 识别失败: {e}")
            return {
                "error": str(e),
                "full_text": "",
                "blocks": [],
                "page_info": {"width": 1.0, "height": 1.0}
            }
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析模型返回的 JSON 响应"""
        import re
        
        print(f"[VLOCRAgent] 开始解析响应，长度: {len(content)}")
        
        # 尝试匹配 ```json ... ``` 块
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            print(f"[VLOCRAgent] 匹配到 json 代码块")
        else:
            # 尝试匹配 { ... } 块
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                print(f"[VLOCRAgent] 匹配到 JSON 对象")
            else:
                print(f"[VLOCRAgent] 未匹配到 JSON，返回原始文本")
                return {
                    "full_text": content,
                    "blocks": [],
                    "page_info": {"width": 1.0, "height": 1.0}
                }
        
        # 修复常见的 JSON 格式问题
        # 1. 如果以 "blocks" 开头，添加 { 
        if json_str.strip().startswith('"blocks"'):
            json_str = '{' + json_str + '}'
            print(f"[VLOCRAgent] 修复：添加缺失的花括号")
        
        # 2. 移除尾部多余的逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        try:
            result = json.loads(json_str)
            print(f"[VLOCRAgent] JSON 解析成功，blocks 数量: {len(result.get('blocks', []))}")
            if "blocks" not in result:
                result["blocks"] = []
            if "full_text" not in result:
                # 从 blocks 生成 full_text
                texts = [b.get("text", "") for b in result.get("blocks", [])]
                result["full_text"] = "\n".join(texts) if texts else content
            if "page_info" not in result:
                result["page_info"] = {"width": 1.0, "height": 1.0}
            return result
        except json.JSONDecodeError as e:
            print(f"[VLOCRAgent] JSON 解析失败: {e}")
            # 尝试用正则提取 blocks
            blocks = self._extract_blocks_by_regex(json_str)
            if blocks:
                print(f"[VLOCRAgent] 正则提取成功，blocks 数量: {len(blocks)}")
                texts = [b.get("text", "") for b in blocks]
                return {
                    "full_text": "\n".join(texts),
                    "blocks": blocks,
                    "page_info": {"width": 1.0, "height": 1.0}
                }
            return {
                "full_text": content,
                "blocks": [],
                "page_info": {"width": 1.0, "height": 1.0}
            }
    
    def _extract_blocks_by_regex(self, content: str) -> List[Dict]:
        """使用正则表达式提取 blocks"""
        import re
        blocks = []
        # 匹配每个 block 对象
        pattern = r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"text"\s*:\s*"([^"]*)"[^}]*"bbox"\s*:\s*\[([^\]]+)\][^}]*\}'
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            try:
                block_id = int(match[0])
                text = match[1]
                bbox_str = match[2]
                bbox = [float(x.strip()) for x in bbox_str.split(',')]
                if len(bbox) == 4:
                    blocks.append({
                        "id": block_id,
                        "text": text,
                        "bbox": bbox,
                        "confidence": 0.9,
                        "type": "text"
                    })
            except:
                continue
        return blocks
    
    def _merge_results(self, results: List[Dict], file_path: str) -> Dict[str, Any]:
        """合并多页结果"""
        merged = {
            "file_path": file_path,
            "total_pages": len(results),
            "pages": results,
            "full_text": "\n\n".join([
                f"--- 第 {r.get('page', i+1)} 页 ---\n{r.get('full_text', '')}"
                for i, r in enumerate(results)
            ]),
        }
        return merged


# 单例实例
_vl_ocr_agent: Optional[VLOCRAgent] = None


def get_vl_ocr_agent(
    api_key: str = "",
    model_name: str = "qwen3-vl-flash",
) -> VLOCRAgent:
    """获取 VL OCR 智能体单例"""
    global _vl_ocr_agent
    if _vl_ocr_agent is None:
        _vl_ocr_agent = VLOCRAgent(api_key=api_key, model_name=model_name)
    return _vl_ocr_agent
