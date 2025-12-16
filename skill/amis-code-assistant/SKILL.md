---
name: amis-code-assistant
description: "低代码平台代码辅助工具。当需要：(1) 根据需求生成 amis JSON 配置代码，(2) 查询 amis 组件用法，(3) 修改或优化现有 amis 配置，(4) 解答 amis 相关问题时使用此技能"
---

# Amis 低代码平台代码辅助

## 概述

此技能帮助你基于 amis 框架生成低代码平台的配置代码。amis 是百度开源的前端低代码框架，通过 JSON 配置即可生成各种页面和表单。

## 快速开始

### 文档结构

本技能包含以下文档资源：

- `docs/` - amis 组件和 API 文档
- `examples/` - 常用场景的代码示例
- `templates/` - 可复用的页面模板

### 工作流程

当用户请求生成 amis 代码时，按以下步骤操作：

1. **理解需求**：明确用户需要什么类型的页面/组件
2. **查阅文档**：在 `docs/` 目录查找相关组件文档
3. **参考示例**：在 `examples/` 目录查找类似场景
4. **生成代码**：基于文档和示例生成 JSON 配置
5. **验证输出**：确保 JSON 格式正确且符合 amis 规范

## 核心概念

### amis 基础结构

每个 amis 页面都是一个 JSON 配置，基本结构如下：

```json
{
  "type": "page",
  "title": "页面标题",
  "body": [
    // 页面内容组件
  ]
}
```

### 常用组件类型

| 类型 | 说明 | 文档位置 |
|------|------|----------|
| page | 页面容器 | docs/components/page.md |
| form | 表单 | docs/components/form.md |
| crud | 增删改查列表 | docs/components/crud.md |
| table | 表格 | docs/components/table.md |
| dialog | 弹窗 | docs/components/dialog.md |
| chart | 图表 | docs/components/chart.md |

## 查询文档

### 查找组件文档

```bash
# 列出所有组件文档
ls ./skill/amis-code-assistant/docs/components/

# 查看特定组件文档
cat ./skill/amis-code-assistant/docs/components/form.md
```

### 搜索关键词

```bash
# 在文档中搜索关键词
grep -r "关键词" ./skill/amis-code-assistant/docs/
```

## 查看示例

### 列出示例

```bash
ls ./skill/amis-code-assistant/examples/
```

### 常用示例

- `examples/basic-form.json` - 基础表单
- `examples/crud-list.json` - CRUD 列表页
- `examples/dashboard.json` - 仪表盘页面
- `examples/wizard-form.json` - 向导式表单

## 代码生成规范

### JSON 格式要求

1. 使用双引号包裹键名和字符串值
2. 确保 JSON 格式有效，无语法错误
3. 添加必要的注释说明（使用 `//` 或在单独字段中）

### 命名规范

- 组件 name 使用 camelCase：`userName`, `orderList`
- API 路径使用 kebab-case：`/api/user-info`, `/api/order-list`
- 标签使用中文：`"label": "用户名"`

### 最佳实践

1. **表单验证**：始终为必填字段添加 `required: true`
2. **API 配置**：使用相对路径，便于环境切换
3. **响应式布局**：使用 `columnCount` 或 `horizontal` 控制布局
4. **错误处理**：配置 `messages` 提供友好的错误提示

## 示例：生成一个用户管理页面

用户需求：创建一个用户管理页面，包含用户列表和新增用户功能

### 步骤 1：查阅 CRUD 文档

```bash
cat ./skill/amis-code-assistant/docs/components/crud.md
```

### 步骤 2：参考示例

```bash
cat ./skill/amis-code-assistant/examples/crud-list.json
```

### 步骤 3：生成代码

```json
{
  "type": "page",
  "title": "用户管理",
  "body": {
    "type": "crud",
    "api": "/api/users",
    "columns": [
      {"name": "id", "label": "ID"},
      {"name": "username", "label": "用户名"},
      {"name": "email", "label": "邮箱"},
      {"name": "createdAt", "label": "创建时间"}
    ],
    "headerToolbar": [
      {
        "type": "button",
        "label": "新增用户",
        "actionType": "dialog",
        "dialog": {
          "title": "新增用户",
          "body": {
            "type": "form",
            "api": "POST:/api/users",
            "body": [
              {"type": "input-text", "name": "username", "label": "用户名", "required": true},
              {"type": "input-text", "name": "email", "label": "邮箱", "required": true}
            ]
          }
        }
      }
    ]
  }
}
```

## 依赖

此技能依赖以下工具（应已安装）：

- 文本查看工具：`cat`, `less`
- 搜索工具：`grep`, `find`
- JSON 验证：`python -m json.tool`
