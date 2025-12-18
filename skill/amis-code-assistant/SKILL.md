---
name: amis-code-assistant
description: "低代码平台代码辅助工具。当需要：(1) 根据需求生成 amis JSON 配置代码，(2) 查询 amis 组件用法，(3) 修改或优化现有 amis 配置，(4) 解答 amis 相关问题时使用此技能"
---

# Amis 低代码平台代码辅助

## 概述

此技能帮助你基于 amis 框架生成低代码平台的配置代码。amis 是百度开源的前端低代码框架，通过 JSON 配置即可生成各种页面和表单。

amis 的核心优势：
- **不需要懂前端**：非前端开发者也能做出专业且复杂的后台界面
- **不受前端技术更新影响**：6年多前的页面至今仍可使用
- **内置120+组件**：一站式解决大部分中后台页面开发需求
- **支持扩展**：90%低代码 + 10%代码开发的混合模式
- **可视化编辑器**：可直接上线的页面制作工具

## 文档结构

本技能包含以下文档资源：

- `docs/` - amis 组件和 API 文档（基于官方最新文档）
- `examples/` - 常用场景的代码示例
- `templates/` - 可复用的页面模板

### 核心组件文档

- `page.md` - 页面容器组件
- `form.md` - 表单组件（包含所有表单项）
- `crud.md` - 增删改查列表组件
- `table.md` - 表格组件
- `dialog.md` - 弹窗组件
- `chart.md` - 图表组件

## 工作流程

当用户请求生成 amis 代码时，按以下步骤操作：

1. **理解需求**：明确用户需要什么类型的页面/组件功能
2. **查阅文档**：在 `docs/` 目录查找相关组件文档
3. **参考示例**：在 `examples/` 目录查找类似场景
4. **生成代码**：基于文档和示例生成符合 amis 规范的 JSON 配置
5. **验证输出**：确保 JSON 格式正确且功能完整

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

### 主要组件类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| page | 页面容器 | 所有页面的根组件 |
| form | 表单 | 数据录入、编辑、展示 |
| crud | 增删改查列表 | 数据管理、列表展示 |
| table | 表格 | 纯数据展示（无分页） |
| dialog | 弹窗 | 模态对话框 |
| service | 服务容器 | 数据获取和处理 |

### CRUD vs Table 区别

- **CRUD**：用于需要分页、搜索、排序、批量操作的数据列表，数据必须放在 `items` 字段中
- **Table**：用于简单的表格展示，不需要分页功能

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

### 常用示例

- `examples/basic-form.json` - 基础表单（包含各种表单项）
- `examples/crud-list.json` - CRUD 列表页（增删改查完整功能）
- `examples/dashboard.json` - 仪表盘页面（复杂布局）
- `examples/wizard-form.json` - 向导式表单（多步骤表单）

### 查看示例命令

```bash
ls ./skill/amis-code-assistant/examples/
cat ./skill/amis-code-assistant/examples/crud-list.json
```

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
5. **数据初始化**：合理使用 `initApi` 和静态 `data`
6. **批量操作**：设置 `primaryField` 确保选择功能正常

### 常用配置模式

#### 表单布局模式
- `normal`：默认垂直布局
- `horizontal`：水平布局（标签在左，表单项在右）
- `inline`：内联布局（所有表单项在同一行）

#### CRUD 展示模式
- `table`：表格模式（默认）
- `list`：列表模式
- `cards`：卡片模式

## 高级功能

### 快速编辑
- `quickEdit: true`：启用快速编辑
- `quickSaveApi`：批量保存接口
- `quickSaveItemApi`：单条即时保存接口

### 批量操作
- 配置 `bulkActions` 实现批量操作
- 设置 `keepItemSelectionOnPageChange: true` 保留跨页选择
- 使用 `primaryField` 指定唯一标识字段

### 动态列
- 通过 API 返回 `columns` 数组实现动态列
- 支持运行时修改列配置

### 事件处理
- 支持丰富的事件系统（inited, change, submit 等）
- 可通过 `onEvent` 配置事件监听和动作

## 示例：生成用户管理页面

用户需求：创建一个用户管理页面，包含用户列表和新增用户功能

### 步骤 1：确定使用 CRUD 组件
CRUD 适合需要分页、搜索、编辑、删除的用户管理场景

### 步骤 2：参考 CRUD 文档和示例
```bash
cat ./skill/amis-code-assistant/docs/components/crud.md
cat ./skill/amis-code-assistant/examples/crud-list.json
```

### 步骤 3：生成完整代码
```json
{
  "type": "page",
  "title": "用户管理",
  "body": {
    "type": "crud",
    "api": "/api/users",
    "syncLocation": false,
    "primaryField": "id",
    "headerToolbar": [
      {
        "type": "button",
        "label": "新增用户",
        "level": "primary",
        "actionType": "dialog",
        "dialog": {
          "title": "新增用户",
          "body": {
            "type": "form",
            "api": "POST:/api/users",
            "body": [
              {"type": "input-text", "name": "username", "label": "用户名", "required": true},
              {"type": "input-email", "name": "email", "label": "邮箱", "required": true},
              {"type": "input-password", "name": "password", "label": "密码", "required": true}
            ]
          }
        }
      }
    ],
    "bulkActions": [
      {
        "label": "批量删除",
        "actionType": "ajax",
        "api": "delete:/api/users/${ids|raw}",
        "confirmText": "确定要批量删除?"
      }
    ],
    "columns": [
      {"name": "id", "label": "ID", "width": 50},
      {"name": "username", "label": "用户名"},
      {"name": "email", "label": "邮箱"},
      {"name": "createdAt", "label": "创建时间", "type": "datetime"},
      {
        "type": "operation",
        "label": "操作",
        "width": 120,
        "buttons": [
          {
            "label": "编辑",
            "actionType": "dialog",
            "dialog": {
              "title": "编辑用户",
              "body": {
                "type": "form",
                "initApi": "/api/users/${id}",
                "api": "PUT:/api/users/${id}",
                "body": [
                  {"type": "input-text", "name": "username", "label": "用户名", "required": true},
                  {"type": "input-email", "name": "email", "label": "邮箱", "required": true}
                ]
              }
            }
          },
          {
            "label": "删除",
            "actionType": "ajax",
            "api": "delete:/api/users/${id}",
            "confirmText": "确定要删除?",
            "level": "danger"
          }
        ]
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

## 版本信息

- 基于 amis 官方文档最新版本
- 包含完整的 CRUD、Form、Page 等核心组件文档
- 提供实际可用的代码示例和最佳实践
