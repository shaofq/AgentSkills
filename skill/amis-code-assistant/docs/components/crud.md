# CRUD 增删改查组件

CRUD 是 amis 中用于实现数据列表增删改查的核心组件。

## 基本用法

```json
{
  "type": "crud",
  "api": "/api/users",
  "columns": [
    {"name": "id", "label": "ID"},
    {"name": "username", "label": "用户名"},
    {"name": "email", "label": "邮箱"}
  ]
}
```

## 属性说明

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| type | string | - | 必须为 "crud" |
| api | API | - | 数据列表接口 |
| columns | Array | - | 列配置 |
| primaryField | string | "id" | 主键字段名 |
| perPage | number | 10 | 每页显示条数 |
| headerToolbar | Array | - | 顶部工具栏 |
| footerToolbar | Array | - | 底部工具栏 |
| filter | object | - | 筛选表单 |
| bulkActions | Array | - | 批量操作按钮 |

## API 响应格式

```json
{
  "status": 0,
  "msg": "",
  "data": {
    "items": [...],
    "total": 100
  }
}
```

## 带筛选的列表

```json
{
  "type": "crud",
  "api": "/api/users",
  "filter": {
    "body": [
      {"type": "input-text", "name": "username", "label": "用户名"},
      {"type": "select", "name": "status", "label": "状态", "options": [
        {"label": "全部", "value": ""},
        {"label": "启用", "value": 1},
        {"label": "禁用", "value": 0}
      ]}
    ]
  },
  "columns": [
    {"name": "id", "label": "ID"},
    {"name": "username", "label": "用户名"}
  ]
}
```

## 带操作按钮的列表

```json
{
  "type": "crud",
  "api": "/api/users",
  "columns": [
    {"name": "id", "label": "ID"},
    {"name": "username", "label": "用户名"},
    {
      "type": "operation",
      "label": "操作",
      "buttons": [
        {
          "type": "button",
          "label": "编辑",
          "actionType": "dialog",
          "dialog": {
            "title": "编辑用户",
            "body": {
              "type": "form",
              "api": "PUT:/api/users/${id}",
              "body": [
                {"type": "input-text", "name": "username", "label": "用户名"}
              ]
            }
          }
        },
        {
          "type": "button",
          "label": "删除",
          "actionType": "ajax",
          "confirmText": "确定要删除吗？",
          "api": "DELETE:/api/users/${id}"
        }
      ]
    }
  ]
}
```

## 新增按钮

```json
{
  "type": "crud",
  "api": "/api/users",
  "headerToolbar": [
    {
      "type": "button",
      "label": "新增",
      "actionType": "dialog",
      "level": "primary",
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
    },
    "bulkActions"
  ],
  "columns": [...]
}
```

## 批量操作

```json
{
  "type": "crud",
  "api": "/api/users",
  "bulkActions": [
    {
      "type": "button",
      "label": "批量删除",
      "actionType": "ajax",
      "confirmText": "确定要删除选中的 ${selectedItems.length} 条数据吗？",
      "api": "DELETE:/api/users/batch?ids=${ids}"
    }
  ],
  "columns": [...]
}
```

## 分页配置

```json
{
  "type": "crud",
  "api": "/api/users",
  "perPage": 20,
  "footerToolbar": [
    "statistics",
    "switch-per-page",
    "pagination"
  ],
  "columns": [...]
}
```
