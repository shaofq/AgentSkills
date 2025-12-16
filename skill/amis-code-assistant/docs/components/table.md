# Table 表格组件

Table 用于展示数据列表，通常配合 CRUD 或 Service 使用。

## 基本用法

```json
{
  "type": "table",
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
| type | string | - | 必须为 "table" |
| columns | Array | - | 列配置 |
| source | string | "${items}" | 数据源 |
| combineNum | number | - | 合并单元格数量 |
| affixHeader | boolean | true | 是否固定表头 |
| footable | boolean | false | 是否开启响应式表格 |

## 列配置

### 基础列

```json
{"name": "username", "label": "用户名", "width": 200}
```

### 带格式化的列

```json
{
  "name": "createdAt",
  "label": "创建时间",
  "type": "date",
  "format": "YYYY-MM-DD HH:mm:ss"
}
```

### 状态映射列

```json
{
  "name": "status",
  "label": "状态",
  "type": "mapping",
  "map": {
    "1": "<span class='label label-success'>启用</span>",
    "0": "<span class='label label-danger'>禁用</span>"
  }
}
```

### 图片列

```json
{
  "name": "avatar",
  "label": "头像",
  "type": "image",
  "width": 50,
  "height": 50
}
```

### 链接列

```json
{
  "name": "url",
  "label": "链接",
  "type": "link",
  "body": "点击查看"
}
```

## 可排序表格

```json
{
  "type": "table",
  "columns": [
    {"name": "id", "label": "ID", "sortable": true},
    {"name": "username", "label": "用户名", "sortable": true},
    {"name": "createdAt", "label": "创建时间", "sortable": true}
  ]
}
```

## 固定列

```json
{
  "type": "table",
  "columns": [
    {"name": "id", "label": "ID", "fixed": "left"},
    {"name": "username", "label": "用户名"},
    {"name": "email", "label": "邮箱"},
    {"type": "operation", "label": "操作", "fixed": "right", "buttons": [...]}
  ]
}
```

## 嵌套表格

```json
{
  "type": "table",
  "columns": [
    {"name": "id", "label": "ID"},
    {"name": "username", "label": "用户名"},
    {
      "type": "container",
      "label": "订单",
      "body": {
        "type": "table",
        "source": "${orders}",
        "columns": [
          {"name": "orderId", "label": "订单号"},
          {"name": "amount", "label": "金额"}
        ]
      }
    }
  ]
}
```
