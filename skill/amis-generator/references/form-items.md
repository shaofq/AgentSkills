# amis 表单项完整列表

## 文本输入类

### input-text 文本输入

```json
{
  "type": "input-text",
  "name": "username",
  "label": "用户名",
  "placeholder": "请输入用户名",
  "required": true,
  "validations": {"minLength": 3, "maxLength": 20}
}
```

### input-password 密码输入

```json
{
  "type": "input-password",
  "name": "password",
  "label": "密码"
}
```

### input-email 邮箱输入

```json
{
  "type": "input-email",
  "name": "email",
  "label": "邮箱",
  "validations": {"isEmail": true}
}
```

### input-url URL输入

```json
{
  "type": "input-url",
  "name": "website",
  "label": "网站"
}
```

### textarea 多行文本

```json
{
  "type": "textarea",
  "name": "description",
  "label": "描述",
  "rows": 5,
  "maxLength": 500,
  "showCounter": true
}
```

### input-number 数字输入

```json
{
  "type": "input-number",
  "name": "age",
  "label": "年龄",
  "min": 0,
  "max": 150,
  "step": 1
}
```

### input-range 滑块

```json
{
  "type": "input-range",
  "name": "score",
  "label": "评分",
  "min": 0,
  "max": 100,
  "step": 10
}
```

## 选择类

### select 下拉选择

```json
{
  "type": "select",
  "name": "city",
  "label": "城市",
  "options": [
    {"label": "北京", "value": "beijing"},
    {"label": "上海", "value": "shanghai"}
  ],
  "searchable": true,
  "clearable": true
}
```

**远程数据**：
```json
{
  "type": "select",
  "name": "category",
  "label": "分类",
  "source": "/api/categories"
}
```

**多选**：
```json
{
  "type": "select",
  "name": "tags",
  "label": "标签",
  "multiple": true,
  "options": [...]
}
```

### radios 单选框

```json
{
  "type": "radios",
  "name": "gender",
  "label": "性别",
  "options": [
    {"label": "男", "value": "male"},
    {"label": "女", "value": "female"}
  ]
}
```

### checkboxes 复选框组

```json
{
  "type": "checkboxes",
  "name": "hobbies",
  "label": "爱好",
  "options": [
    {"label": "阅读", "value": "reading"},
    {"label": "运动", "value": "sports"},
    {"label": "音乐", "value": "music"}
  ]
}
```

### checkbox 单个复选框

```json
{
  "type": "checkbox",
  "name": "agree",
  "label": "同意协议",
  "option": "我已阅读并同意用户协议"
}
```

### switch 开关

```json
{
  "type": "switch",
  "name": "enabled",
  "label": "启用",
  "onText": "开",
  "offText": "关"
}
```

### button-group-select 按钮组选择

```json
{
  "type": "button-group-select",
  "name": "status",
  "label": "状态",
  "options": [
    {"label": "待处理", "value": "pending"},
    {"label": "已完成", "value": "done"}
  ]
}
```

## 日期时间类

### input-date 日期选择

```json
{
  "type": "input-date",
  "name": "birthday",
  "label": "生日",
  "format": "YYYY-MM-DD",
  "inputFormat": "YYYY年MM月DD日"
}
```

### input-datetime 日期时间选择

```json
{
  "type": "input-datetime",
  "name": "createTime",
  "label": "创建时间",
  "format": "YYYY-MM-DD HH:mm:ss"
}
```

### input-time 时间选择

```json
{
  "type": "input-time",
  "name": "startTime",
  "label": "开始时间",
  "format": "HH:mm"
}
```

### input-date-range 日期范围

```json
{
  "type": "input-date-range",
  "name": "dateRange",
  "label": "日期范围",
  "format": "YYYY-MM-DD"
}
```

### input-month 月份选择

```json
{
  "type": "input-month",
  "name": "month",
  "label": "月份"
}
```

### input-year 年份选择

```json
{
  "type": "input-year",
  "name": "year",
  "label": "年份"
}
```

## 文件上传类

### input-file 文件上传

```json
{
  "type": "input-file",
  "name": "file",
  "label": "附件",
  "receiver": "/api/upload",
  "accept": ".pdf,.doc,.docx",
  "maxSize": 10485760
}
```

### input-image 图片上传

```json
{
  "type": "input-image",
  "name": "avatar",
  "label": "头像",
  "receiver": "/api/upload/image",
  "accept": ".jpg,.png,.gif",
  "crop": true,
  "limit": {"width": 200, "height": 200}
}
```

### input-excel Excel导入

```json
{
  "type": "input-excel",
  "name": "excelData",
  "label": "导入Excel"
}
```

## 富文本类

### editor 代码编辑器

```json
{
  "type": "editor",
  "name": "code",
  "label": "代码",
  "language": "javascript",
  "size": "lg"
}
```

### input-rich-text 富文本编辑器

```json
{
  "type": "input-rich-text",
  "name": "content",
  "label": "内容",
  "vendor": "tinymce"
}
```

### markdown-editor Markdown编辑器

```json
{
  "type": "markdown-editor",
  "name": "markdown",
  "label": "Markdown"
}
```

## 特殊类型

### hidden 隐藏字段

```json
{
  "type": "hidden",
  "name": "id"
}
```

### static 静态展示

```json
{
  "type": "static",
  "name": "createTime",
  "label": "创建时间"
}
```

### input-color 颜色选择

```json
{
  "type": "input-color",
  "name": "color",
  "label": "颜色"
}
```

### input-rating 评分

```json
{
  "type": "input-rating",
  "name": "rating",
  "label": "评分",
  "count": 5,
  "half": true
}
```

### input-tag 标签输入

```json
{
  "type": "input-tag",
  "name": "tags",
  "label": "标签",
  "options": ["标签1", "标签2"]
}
```

### input-tree 树形选择

```json
{
  "type": "input-tree",
  "name": "department",
  "label": "部门",
  "source": "/api/departments",
  "multiple": true
}
```

### transfer 穿梭器

```json
{
  "type": "transfer",
  "name": "selected",
  "label": "选择",
  "source": "/api/options",
  "searchable": true
}
```

### picker 列表选择器

```json
{
  "type": "picker",
  "name": "user",
  "label": "选择用户",
  "source": "/api/users",
  "labelField": "name",
  "valueField": "id"
}
```

## 组合类

### combo 组合输入

```json
{
  "type": "combo",
  "name": "contacts",
  "label": "联系人",
  "multiple": true,
  "items": [
    {"type": "input-text", "name": "name", "label": "姓名"},
    {"type": "input-text", "name": "phone", "label": "电话"}
  ]
}
```

### input-table 表格输入

```json
{
  "type": "input-table",
  "name": "items",
  "label": "明细",
  "addable": true,
  "removable": true,
  "columns": [
    {"name": "product", "label": "产品", "type": "input-text"},
    {"name": "quantity", "label": "数量", "type": "input-number"}
  ]
}
```

### input-sub-form 子表单

```json
{
  "type": "input-sub-form",
  "name": "address",
  "label": "地址",
  "form": {
    "body": [
      {"type": "input-text", "name": "province", "label": "省"},
      {"type": "input-text", "name": "city", "label": "市"}
    ]
  }
}
```

## 表单项通用属性

| 属性 | 类型 | 说明 |
|------|------|------|
| name | string | 字段名（必填） |
| label | string | 标签 |
| required | boolean | 是否必填 |
| disabled | boolean | 是否禁用 |
| hidden | boolean | 是否隐藏 |
| visibleOn | string | 显示条件表达式 |
| disabledOn | string | 禁用条件表达式 |
| placeholder | string | 占位提示 |
| description | string | 描述说明 |
| value | any | 默认值 |
| validations | object | 校验规则 |
| validationErrors | object | 校验错误提示 |

## 校验规则

```json
{
  "type": "input-text",
  "name": "phone",
  "label": "手机号",
  "validations": {
    "isPhoneNumber": true
  },
  "validationErrors": {
    "isPhoneNumber": "请输入正确的手机号"
  }
}
```

常用校验：
- `isRequired` - 必填
- `isEmail` - 邮箱格式
- `isUrl` - URL格式
- `isNumeric` - 数字
- `isPhoneNumber` - 手机号
- `minLength` - 最小长度
- `maxLength` - 最大长度
- `minimum` - 最小值
- `maximum` - 最大值
- `matchRegexp` - 正则匹配
