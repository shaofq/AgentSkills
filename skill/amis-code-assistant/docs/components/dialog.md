# Dialog 弹窗组件

Dialog 用于在页面上弹出对话框，常用于表单编辑、详情展示等场景。

## 基本用法

```json
{
  "type": "button",
  "label": "打开弹窗",
  "actionType": "dialog",
  "dialog": {
    "title": "弹窗标题",
    "body": "弹窗内容"
  }
}
```

## 属性说明

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| title | string | - | 弹窗标题 |
| body | SchemaNode | - | 弹窗内容 |
| size | string | - | 弹窗大小：xs/sm/md/lg/xl/full |
| actions | Array | - | 底部按钮 |
| closeOnEsc | boolean | false | 按 ESC 关闭 |
| closeOnOutside | boolean | false | 点击外部关闭 |
| showCloseButton | boolean | true | 显示关闭按钮 |

## 带表单的弹窗

```json
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
```

## 确认弹窗

```json
{
  "type": "button",
  "label": "删除",
  "actionType": "ajax",
  "confirmText": "确定要删除这条记录吗？",
  "api": "DELETE:/api/users/${id}"
}
```

## 自定义按钮

```json
{
  "type": "button",
  "label": "打开弹窗",
  "actionType": "dialog",
  "dialog": {
    "title": "自定义按钮",
    "body": "弹窗内容",
    "actions": [
      {
        "type": "button",
        "label": "取消",
        "actionType": "close"
      },
      {
        "type": "button",
        "label": "确定",
        "level": "primary",
        "actionType": "confirm"
      }
    ]
  }
}
```

## 大尺寸弹窗

```json
{
  "type": "button",
  "label": "大弹窗",
  "actionType": "dialog",
  "dialog": {
    "title": "大尺寸弹窗",
    "size": "lg",
    "body": "这是一个大尺寸的弹窗"
  }
}
```

## 抽屉式弹窗

```json
{
  "type": "button",
  "label": "打开抽屉",
  "actionType": "drawer",
  "drawer": {
    "title": "抽屉标题",
    "position": "right",
    "body": "抽屉内容"
  }
}
```
