---
name: ocr-file-reader
description: "OCR 文件识别工具。当需要：(1) 识别 PDF 文件内容，(2) 识别图片中的文字，(3) 提取文档中的文本信息时使用此技能"
---

# OCR 文件识别技能

## 概述

此技能通过调用 OCR API 服务，识别 PDF 文件或图片中的文字内容。支持多种文件格式和识别模式。

## API 配置

### 服务地址

- **Base URL**: `http://localhost:8009`
- **识别接口**: `POST /api/ocr/filepath`

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_path | string | 是 | 文件的完整路径 |
| dpi | number | 否 | 图像分辨率，默认 144 |
| prompt_mode | string | 否 | 识别模式，默认 `prompt_layout_all_en` |

### 识别模式说明

| 模式 | 说明 |
|------|------|
| prompt_layout_all_en | 英文布局识别（默认） |
| prompt_layout_all_cn | 中文布局识别 |
| prompt_text_only | 仅文本识别 |

## 使用示例

### 识别 PDF 文件

```bash
curl -X POST "http://localhost:8009/api/ocr/filepath" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.pdf",
    "dpi": 144,
    "prompt_mode": "prompt_layout_all_en"
  }'
```

### 识别图片文件

```bash
curl -X POST "http://localhost:8009/api/ocr/filepath" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/image.png",
    "dpi": 200,
    "prompt_mode": "prompt_layout_all_cn"
  }'
```

## 响应格式

```json
{
  "success": true,
  "text": "识别出的文本内容...",
  "pages": [
    {
      "page": 1,
      "content": "第一页内容..."
    }
  ]
}
```

## 支持的文件格式

- **PDF**: `.pdf`
- **图片**: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`

## 工作流程

1. **接收文件路径**：用户提供需要识别的文件路径
2. **调用 OCR API**：发送请求到 OCR 服务
3. **解析结果**：提取识别出的文本内容
4. **返回结果**：将文本内容返回给用户

## 注意事项

1. 确保 OCR 服务已启动（端口 8009）
2. 文件路径必须是服务器可访问的绝对路径
3. 大文件识别可能需要较长时间
4. 建议 PDF 文件使用 144 或更高的 DPI 以获得更好的识别效果
