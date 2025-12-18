# amis 常用组件详解

## Page 页面

页面是 amis 的顶级容器，所有配置必须以 Page 开始。

```json
{
  "type": "page",
  "title": "页面标题",
  "subTitle": "副标题",
  "toolbar": [],
  "body": []
}
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| title | string | 页面标题 |
| subTitle | string | 副标题 |
| toolbar | array | 工具栏 |
| body | array/object | 页面内容 |
| aside | array/object | 侧边栏 |
| initApi | API | 初始化数据接口 |

## Form 表单

表单是 amis 核心组件，用于数据提交和展示。

```json
{
  "type": "form",
  "api": "/api/save",
  "mode": "horizontal",
  "body": [
    {"type": "input-text", "name": "name", "label": "姓名"}
  ]
}
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| api | API | 提交接口 |
| initApi | API | 初始化接口 |
| mode | string | 展示模式：normal/horizontal/inline |
| horizontal | object | 水平模式配置 |
| wrapWithPanel | boolean | 是否包裹 Panel |
| actions | array | 底部按钮 |
| submitText | string | 提交按钮文字 |
| resetAfterSubmit | boolean | 提交后重置 |

### 表单模式示例

**水平模式**：
```json
{
  "type": "form",
  "mode": "horizontal",
  "horizontal": {"left": 2, "right": 10},
  "body": [...]
}
```

**内联模式**：
```json
{
  "type": "form",
  "mode": "inline",
  "body": [...]
}
```

## CRUD 增删改查

CRUD 是最常用的数据管理组件。

```json
{
  "type": "crud",
  "api": "/api/list",
  "columns": [
    {"name": "id", "label": "ID", "sortable": true},
    {"name": "name", "label": "姓名", "searchable": true}
  ],
  "headerToolbar": ["bulkActions", "export-excel"],
  "footerToolbar": ["statistics", "pagination"]
}
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| api | API | 数据接口 |
| columns | array | 列配置 |
| headerToolbar | array | 顶部工具栏 |
| footerToolbar | array | 底部工具栏 |
| bulkActions | array | 批量操作按钮 |
| itemActions | array | 行操作按钮 |
| filter | object | 筛选表单 |
| draggable | boolean | 是否可拖拽排序 |
| quickSaveApi | API | 快速保存接口 |

### 列配置

```json
{
  "name": "status",
  "label": "状态",
  "type": "mapping",
  "map": {
    "1": "启用",
    "0": "禁用"
  },
  "sortable": true,
  "searchable": {
    "type": "select",
    "options": [{"label": "启用", "value": 1}]
  }
}
```

### 操作列

```json
{
  "type": "operation",
  "label": "操作",
  "buttons": [
    {
      "type": "button",
      "label": "编辑",
      "actionType": "dialog",
      "dialog": {
        "title": "编辑",
        "body": {"type": "form", "api": "/api/update/$id", "body": [...]}
      }
    },
    {
      "type": "button",
      "label": "删除",
      "actionType": "ajax",
      "confirmText": "确定删除？",
      "api": "delete:/api/delete/$id"
    }
  ]
}
```

## Table 表格

纯展示表格，不带 CRUD 功能。

```json
{
  "type": "table",
  "source": "${list}",
  "columns": [
    {"name": "id", "label": "ID"},
    {"name": "name", "label": "姓名"}
  ]
}
```

## Dialog 弹窗

```json
{
  "type": "button",
  "label": "打开弹窗",
  "actionType": "dialog",
  "dialog": {
    "title": "弹窗标题",
    "size": "lg",
    "body": {...},
    "actions": [
      {"type": "button", "label": "取消", "actionType": "close"},
      {"type": "button", "label": "确定", "actionType": "confirm", "primary": true}
    ]
  }
}
```

### 弹窗尺寸

- `sm` - 小
- `md` - 中（默认）
- `lg` - 大
- `xl` - 超大
- `full` - 全屏

## Drawer 抽屉

```json
{
  "type": "button",
  "label": "打开抽屉",
  "actionType": "drawer",
  "drawer": {
    "title": "抽屉标题",
    "position": "right",
    "size": "md",
    "body": {...}
  }
}
```

## Service 服务

用于获取数据并渲染。

```json
{
  "type": "service",
  "api": "/api/getData",
  "body": {
    "type": "tpl",
    "tpl": "数据：${data}"
  }
}
```

## Chart 图表

基于 ECharts 的图表组件。

```json
{
  "type": "chart",
  "api": "/api/chartData",
  "config": {
    "title": {"text": "图表标题"},
    "xAxis": {"type": "category", "data": ["A", "B", "C"]},
    "yAxis": {"type": "value"},
    "series": [{"type": "bar", "data": [10, 20, 30]}]
  }
}
```

## Tabs 选项卡

```json
{
  "type": "tabs",
  "tabs": [
    {"title": "选项卡1", "body": {...}},
    {"title": "选项卡2", "body": {...}}
  ]
}
```

## Grid 栅格布局

```json
{
  "type": "grid",
  "columns": [
    {"body": {...}, "md": 6},
    {"body": {...}, "md": 6}
  ]
}
```

## Flex 弹性布局

```json
{
  "type": "flex",
  "justify": "space-between",
  "items": [
    {"type": "tpl", "tpl": "左侧"},
    {"type": "tpl", "tpl": "右侧"}
  ]
}
```
