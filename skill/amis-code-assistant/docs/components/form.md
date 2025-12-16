# Form 表单组件

Form 是 amis 中用于数据录入的核心组件，支持各种表单控件和验证。

## 基本用法

```json
{
  "type": "form",
  "api": "/api/submit",
  "body": [
    {"type": "input-text", "name": "username", "label": "用户名"},
    {"type": "input-text", "name": "email", "label": "邮箱"}
  ]
}
```

## 属性说明

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| type | string | - | 必须为 "form" |
| api | API | - | 表单提交接口 |
| initApi | API | - | 初始化数据接口 |
| body | Array | - | 表单项数组 |
| mode | string | "normal" | 表单模式：normal/horizontal/inline |
| horizontal | object | - | 水平布局配置 |
| submitText | string | "提交" | 提交按钮文字 |
| resetAfterSubmit | boolean | false | 提交后是否重置表单 |
| messages | object | - | 提示消息配置 |

## 常用表单控件

### 文本输入

```json
{"type": "input-text", "name": "username", "label": "用户名", "required": true}
```

### 密码输入

```json
{"type": "input-password", "name": "password", "label": "密码", "required": true}
```

### 下拉选择

```json
{
  "type": "select",
  "name": "status",
  "label": "状态",
  "options": [
    {"label": "启用", "value": 1},
    {"label": "禁用", "value": 0}
  ]
}
```

### 日期选择

```json
{"type": "input-date", "name": "birthday", "label": "生日", "format": "YYYY-MM-DD"}
```

### 开关

```json
{"type": "switch", "name": "isActive", "label": "是否启用"}
```

### 多行文本

```json
{"type": "textarea", "name": "description", "label": "描述", "rows": 5}
```

## 表单验证

```json
{
  "type": "input-text",
  "name": "email",
  "label": "邮箱",
  "required": true,
  "validations": {
    "isEmail": true
  },
  "validationErrors": {
    "isEmail": "请输入有效的邮箱地址"
  }
}
```

## 水平布局

```json
{
  "type": "form",
  "mode": "horizontal",
  "horizontal": {
    "left": 2,
    "right": 10
  },
  "body": [
    {"type": "input-text", "name": "username", "label": "用户名"}
  ]
}
```

## 分组表单

```json
{
  "type": "form",
  "body": [
    {
      "type": "fieldset",
      "title": "基本信息",
      "body": [
        {"type": "input-text", "name": "username", "label": "用户名"},
        {"type": "input-text", "name": "email", "label": "邮箱"}
      ]
    },
    {
      "type": "fieldset",
      "title": "其他信息",
      "body": [
        {"type": "textarea", "name": "remark", "label": "备注"}
      ]
    }
  ]
}
```

## 表单联动

```json
{
  "type": "form",
  "body": [
    {
      "type": "select",
      "name": "type",
      "label": "类型",
      "options": [
        {"label": "个人", "value": "personal"},
        {"label": "企业", "value": "company"}
      ]
    },
    {
      "type": "input-text",
      "name": "companyName",
      "label": "公司名称",
      "visibleOn": "type === 'company'"
    }
  ]
}
```
