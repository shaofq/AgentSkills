# Page 页面组件

Page 是 amis 中最顶层的容器组件，用于包裹整个页面内容。

## 基本用法

```json
{
  "type": "page",
  "title": "页面标题",
  "body": "页面内容"
}
```

## 属性说明

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| type | string | - | 必须为 "page" |
| title | string | - | 页面标题 |
| subTitle | string | - | 副标题 |
| body | SchemaNode | - | 页面内容 |
| aside | SchemaNode | - | 侧边栏内容 |
| toolbar | SchemaNode | - | 工具栏 |
| initApi | API | - | 页面初始化数据接口 |
| initFetch | boolean | true | 是否初始化时拉取数据 |
| className | string | - | 自定义 CSS 类名 |

## 带侧边栏的页面

```json
{
  "type": "page",
  "title": "带侧边栏的页面",
  "aside": {
    "type": "nav",
    "links": [
      {"label": "菜单1", "to": "/page1"},
      {"label": "菜单2", "to": "/page2"}
    ]
  },
  "body": "主内容区域"
}
```

## 带工具栏的页面

```json
{
  "type": "page",
  "title": "带工具栏的页面",
  "toolbar": [
    {
      "type": "button",
      "label": "刷新",
      "actionType": "reload"
    }
  ],
  "body": "页面内容"
}
```

## 初始化数据

```json
{
  "type": "page",
  "title": "用户详情",
  "initApi": "/api/user/${userId}",
  "body": [
    {"type": "tpl", "tpl": "用户名：${username}"},
    {"type": "tpl", "tpl": "邮箱：${email}"}
  ]
}
```
