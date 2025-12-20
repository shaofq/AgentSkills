---
name: ocr-file-reader
description: "OCR 文件识别。只能用 curl 调用 http://localhost:8009/api/ocr/filepath 接口，禁止查看代码、禁止导入模块、禁止分析源码。"
---

# OCR 文件识别技能

## ⚠️ 强制规则（违反即失败）

1. **只能使用 curl 命令调用 API**
2. **禁止使用 view_text_file 查看任何 .py 文件**
3. **禁止使用 execute_python_code 执行任何代码**
4. **禁止使用 find 命令搜索代码文件**
5. **禁止分析、查看、导入任何 Python 模块或源代码**

## 唯一正确的执行流程

### 第一步：检查文件

```bash
ls -la "<用户提供的文件路径>"
```

### 第二步：调用 API（这是唯一的识别方式）

```bash
curl -s -X POST "http://localhost:8009/api/ocr/filepath" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "<文件绝对路径>", "dpi": 144, "prompt_mode": "prompt_layout_all_cn"}'
```

### 第三步：返回结果

- 如果 curl 成功：返回识别的文本内容
- 如果 curl 失败：返回 `❌ OCR 服务调用失败，请确保 OCR 服务已在端口 8009 启动`

## API 参数

| 参数 | 值 |
|------|-----|
| URL | `http://localhost:8009/api/ocr/filepath` |
| Method | POST |
| file_path | 文件绝对路径（必填） |
| dpi | 144（可选） |
| prompt_mode | prompt_layout_all_cn（可选） |

## 示例

用户说："识别 /Users/shaoqiang/work/workspace/dots.ocr-adapter_mps/demo/ab.pdf"

正确执行：
```bash
curl -s -X POST "http://localhost:8009/api/ocr/filepath" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/Users/test/doc.pdf", "dpi": 144, "prompt_mode": "prompt_layout_all_cn"}'
```

## 错误处理

| 情况 | 返回 |
|------|------|
| 文件不存在 | `❌ 文件不存在: <路径>` |
| API 连接失败 | `❌ OCR 服务未启动，请先启动 OCR 服务（端口 8009）` |
| API 返回错误 | `❌ OCR 识别失败: <错误信息>` |

**不要尝试其他方法，直接返回错误信息。**
