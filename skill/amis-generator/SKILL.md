---
name: amis-generator
description: "amis 低代码 JSON 配置生成器。当需要：(1) 生成 amis 页面配置，(2) 创建表单、表格、CRUD 等组件，(3) 配置 amis 布局和交互时使用此技能。支持 120+ 内置组件，包括 Page、Form、CRUD、Table、Chart 等。"
---

# amis 代码生成技能

## 概述

amis 是百度开源的低代码前端框架，使用 JSON 配置生成页面。本技能帮助生成符合 amis 规范的 JSON 配置。

## 核心概念

### 1. 基本结构

每个 amis 配置都是一个 JSON 对象，`type` 字段指定组件类型：

```json
{
  "type": "page",
  "body": "Hello World!"
}
```

### 2. 组件树

通过嵌套组件构建复杂页面：

```json
{
  "type": "page",
  "body": {
    "type": "form",
    "body": [
      {"type": "input-text", "name": "name", "label": "姓名"}
    ]
  }
}
```

### 3. 顶级节点

**Page 是唯一的顶级节点**，所有配置必须以 Page 开始。

## 常用组件速查

### 页面容器
- `page` - 页面容器，必须作为顶级节点
- `container` - 通用容器
- `panel` - 面板
- `tabs` - 选项卡

### 表单组件
- `form` - 表单容器
- `input-text` - 文本输入
- `input-number` - 数字输入
- `input-email` - 邮箱输入
- `input-password` - 密码输入
- `select` - 下拉选择
- `radios` - 单选框
- `checkbox` - 复选框
- `switch` - 开关
- `input-date` - 日期选择
- `input-datetime` - 日期时间选择
- `input-file` - 文件上传
- `input-image` - 图片上传
- `textarea` - 多行文本
- `editor` - 代码编辑器
- `rich-text` - 富文本编辑器

### 数据展示
- `crud` - 增删改查表格
- `table` - 表格
- `cards` - 卡片列表
- `list` - 列表
- `chart` - 图表
- `json` - JSON 展示
- `tpl` - 模板渲染
- `image` - 图片
- `video` - 视频
- `audio` - 音频

### 布局组件
- `grid` - 栅格布局
- `flex` - 弹性布局
- `hbox` - 水平布局
- `divider` - 分割线

### 交互组件
- `button` - 按钮
- `action` - 动作按钮
- `dialog` - 弹窗
- `drawer` - 抽屉
- `toast` - 轻提示

## 生成规范

### 1. Form 表单

```json
{
  "type": "page",
  "body": {
    "type": "form",
    "api": "/api/save",
    "body": [
      {"type": "input-text", "name": "name", "label": "姓名", "required": true},
      {"type": "input-email", "name": "email", "label": "邮箱"}
    ]
  }
}
```

**表单模式**：
- 默认模式：标签在上
- `"mode": "horizontal"` - 水平模式，标签在左
- `"mode": "inline"` - 内联模式

### 2. CRUD 增删改查

```json
{
  "type": "page",
  "body": {
    "type": "crud",
    "api": "/api/list",
    "columns": [
      {"name": "id", "label": "ID"},
      {"name": "name", "label": "姓名"},
      {
        "type": "operation",
        "label": "操作",
        "buttons": [
          {"type": "button", "label": "编辑", "actionType": "dialog", "dialog": {...}},
          {"type": "button", "label": "删除", "actionType": "ajax", "api": "delete:/api/delete/$id"}
        ]
      }
    ],
    "headerToolbar": ["bulkActions", "export-excel", "pagination"],
    "footerToolbar": ["statistics", "pagination"]
  }
}
```

### 3. 弹窗表单

```json
{
  "type": "button",
  "label": "新增",
  "actionType": "dialog",
  "dialog": {
    "title": "新增用户",
    "body": {
      "type": "form",
      "api": "/api/create",
      "body": [
        {"type": "input-text", "name": "name", "label": "姓名"}
      ]
    }
  }
}
```

### 4. 数据联动

使用表达式实现联动：

```json
{
  "type": "select",
  "name": "type",
  "label": "类型",
  "options": [{"label": "A", "value": "a"}, {"label": "B", "value": "b"}]
},
{
  "type": "input-text",
  "name": "detail",
  "label": "详情",
  "visibleOn": "data.type === 'a'"
}
```

### 5. 图表配置

```json
{
  "type": "chart",
  "config": {
    "title": {"text": "销售趋势"},
    "xAxis": {"type": "category", "data": ["一月", "二月", "三月"]},
    "yAxis": {"type": "value"},
    "series": [{"type": "line", "data": [100, 200, 150]}]
  }
}
```

## API 配置

### 基本格式

```json
"api": "/api/list"
"api": "post:/api/save"
"api": "delete:/api/delete/$id"
```

### 完整配置

```json
"api": {
  "method": "post",
  "url": "/api/save",
  "data": {
    "name": "${name}",
    "extra": "fixed"
  },
  "headers": {
    "Authorization": "Bearer ${token}"
  }
}
```

## 数据映射

使用 `${}` 语法引用数据：

- `${name}` - 引用字段值
- `${items|json}` - 使用过滤器
- `${&}` - 引用整个数据对象

## 表达式

用于条件判断：

- `visibleOn` - 显示条件
- `hiddenOn` - 隐藏条件
- `disabledOn` - 禁用条件

```json
"visibleOn": "data.type === 'vip'",
"disabledOn": "!data.agreed"
```

## 输出要求

1. **必须是有效 JSON**：确保语法正确
2. **Page 作为顶级节点**：所有配置以 page 开始
3. **合理的组件嵌套**：遵循组件层级关系
4. **完整的必填属性**：如 name、label 等
5. **API 路径使用占位符**：如 `/api/xxx`

## 参考文档

详细组件文档请查阅 `references/` 目录：
- `references/components.md` - 常用组件详解
- `references/form-items.md` - 表单项完整列表
- `references/crud-examples.md` - CRUD 示例集合
