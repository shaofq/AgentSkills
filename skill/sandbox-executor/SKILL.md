---
name: sandbox-executor
description: "AIO Sandbox 执行器 - 在安全沙箱环境中执行 Shell 命令、Python 代码、文件操作和浏览器自动化"
---

# AIO Sandbox 执行器技能

在安全的沙箱环境中执行各种操作，实现类似 Manus 的 AI Agent 能力。

## 可用工具

### 1. sandbox_shell - 执行 Shell 命令

在沙箱中执行 Shell 命令。

**参数:**
- `command` (必需): 要执行的 Shell 命令
- `cwd` (可选): 工作目录

**示例:**
```python
sandbox_shell(command="ls -la /home/user")
sandbox_shell(command="pip install pandas", cwd="/home/user/project")
```

### 2. sandbox_python - 执行 Python 代码

在沙箱的 Jupyter 环境中执行 Python 代码。

**参数:**
- `code` (必需): 要执行的 Python 代码

**示例:**
```python
sandbox_python(code="""
import pandas as pd
df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})
print(df.to_markdown())
""")
```

### 3. sandbox_file_write - 写入文件

在沙箱中创建或写入文件。

**参数:**
- `file_path` (必需): 文件路径
- `content` (必需): 文件内容

**示例:**
```python
sandbox_file_write(
    file_path="/home/user/report.md",
    content="# 报告标题\n\n这是报告内容..."
)
```

### 4. sandbox_file_read - 读取文件

读取沙箱中的文件内容。

**参数:**
- `file_path` (必需): 文件路径

**示例:**
```python
sandbox_file_read(file_path="/home/user/data.json")
```

### 5. sandbox_browser_goto - 浏览器导航

控制沙箱浏览器访问指定 URL。

**参数:**
- `url` (必需): 目标 URL

**示例:**
```python
sandbox_browser_goto(url="https://example.com")
```

### 6. sandbox_browser_screenshot - 浏览器截图

对沙箱浏览器当前页面截图。

**示例:**
```python
sandbox_browser_screenshot()
```

## 使用场景

1. **文档生成**: 在沙箱中创建 Markdown、Word、PDF 文档
2. **数据分析**: 执行 Python 数据分析脚本
3. **网页抓取**: 使用浏览器自动化抓取网页内容
4. **代码执行**: 安全执行用户提供的代码
5. **文件处理**: 读写、转换各种文件格式

## 注意事项

1. 所有操作在隔离的 Docker 容器中执行，确保安全
2. 沙箱会保持状态，文件和安装的包在会话期间持续存在
3. 用户可以通过 VNC 实时观看 Agent 的操作
