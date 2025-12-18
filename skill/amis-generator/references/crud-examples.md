# amis CRUD 示例集合

## 基础 CRUD

最简单的增删改查表格：

```json
{
  "type": "page",
  "title": "用户管理",
  "body": {
    "type": "crud",
    "api": "/api/users",
    "columns": [
      {"name": "id", "label": "ID"},
      {"name": "name", "label": "姓名"},
      {"name": "email", "label": "邮箱"},
      {"name": "createdAt", "label": "创建时间"}
    ]
  }
}
```

## 带筛选的 CRUD

```json
{
  "type": "page",
  "title": "订单管理",
  "body": {
    "type": "crud",
    "api": "/api/orders",
    "filter": {
      "title": "筛选",
      "body": [
        {"type": "input-text", "name": "orderNo", "label": "订单号"},
        {"type": "select", "name": "status", "label": "状态", "options": [
          {"label": "待支付", "value": "pending"},
          {"label": "已支付", "value": "paid"},
          {"label": "已完成", "value": "done"}
        ]},
        {"type": "input-date-range", "name": "dateRange", "label": "日期范围"}
      ]
    },
    "columns": [
      {"name": "orderNo", "label": "订单号"},
      {"name": "customerName", "label": "客户"},
      {"name": "amount", "label": "金额"},
      {"name": "status", "label": "状态", "type": "mapping", "map": {
        "pending": "<span class='label label-warning'>待支付</span>",
        "paid": "<span class='label label-info'>已支付</span>",
        "done": "<span class='label label-success'>已完成</span>"
      }},
      {"name": "createdAt", "label": "创建时间"}
    ]
  }
}
```

## 完整 CRUD（新增、编辑、删除）

```json
{
  "type": "page",
  "title": "商品管理",
  "body": {
    "type": "crud",
    "api": "/api/products",
    "headerToolbar": [
      {
        "type": "button",
        "label": "新增商品",
        "actionType": "dialog",
        "level": "primary",
        "dialog": {
          "title": "新增商品",
          "body": {
            "type": "form",
            "api": "post:/api/products",
            "body": [
              {"type": "input-text", "name": "name", "label": "商品名称", "required": true},
              {"type": "input-number", "name": "price", "label": "价格", "required": true},
              {"type": "input-number", "name": "stock", "label": "库存"},
              {"type": "select", "name": "category", "label": "分类", "source": "/api/categories"},
              {"type": "textarea", "name": "description", "label": "描述"},
              {"type": "input-image", "name": "image", "label": "图片", "receiver": "/api/upload"}
            ]
          }
        }
      },
      "bulkActions",
      "export-excel"
    ],
    "bulkActions": [
      {
        "type": "button",
        "label": "批量删除",
        "actionType": "ajax",
        "confirmText": "确定要删除选中的商品吗？",
        "api": "delete:/api/products/batch?ids=${ids|raw}"
      }
    ],
    "columns": [
      {"name": "id", "label": "ID", "sortable": true},
      {"name": "image", "label": "图片", "type": "image", "width": 60},
      {"name": "name", "label": "商品名称", "searchable": true},
      {"name": "price", "label": "价格", "sortable": true},
      {"name": "stock", "label": "库存"},
      {"name": "category", "label": "分类"},
      {
        "type": "operation",
        "label": "操作",
        "buttons": [
          {
            "type": "button",
            "label": "编辑",
            "actionType": "dialog",
            "dialog": {
              "title": "编辑商品",
              "body": {
                "type": "form",
                "api": "put:/api/products/$id",
                "body": [
                  {"type": "input-text", "name": "name", "label": "商品名称", "required": true},
                  {"type": "input-number", "name": "price", "label": "价格", "required": true},
                  {"type": "input-number", "name": "stock", "label": "库存"},
                  {"type": "select", "name": "category", "label": "分类", "source": "/api/categories"},
                  {"type": "textarea", "name": "description", "label": "描述"},
                  {"type": "input-image", "name": "image", "label": "图片", "receiver": "/api/upload"}
                ]
              }
            }
          },
          {
            "type": "button",
            "label": "删除",
            "actionType": "ajax",
            "level": "danger",
            "confirmText": "确定要删除该商品吗？",
            "api": "delete:/api/products/$id"
          }
        ]
      }
    ],
    "footerToolbar": ["statistics", "switch-per-page", "pagination"]
  }
}
```

## 带详情查看的 CRUD

```json
{
  "type": "page",
  "title": "文章管理",
  "body": {
    "type": "crud",
    "api": "/api/articles",
    "columns": [
      {"name": "id", "label": "ID"},
      {"name": "title", "label": "标题"},
      {"name": "author", "label": "作者"},
      {"name": "status", "label": "状态", "type": "mapping", "map": {
        "draft": "草稿",
        "published": "已发布"
      }},
      {"name": "createdAt", "label": "创建时间"},
      {
        "type": "operation",
        "label": "操作",
        "buttons": [
          {
            "type": "button",
            "label": "查看",
            "actionType": "drawer",
            "drawer": {
              "title": "文章详情",
              "size": "lg",
              "body": {
                "type": "service",
                "api": "/api/articles/$id",
                "body": [
                  {"type": "static", "name": "title", "label": "标题"},
                  {"type": "static", "name": "author", "label": "作者"},
                  {"type": "static", "name": "content", "label": "内容"},
                  {"type": "static", "name": "createdAt", "label": "创建时间"}
                ]
              }
            }
          },
          {
            "type": "button",
            "label": "编辑",
            "actionType": "dialog",
            "dialog": {
              "title": "编辑文章",
              "size": "lg",
              "body": {
                "type": "form",
                "api": "put:/api/articles/$id",
                "body": [
                  {"type": "input-text", "name": "title", "label": "标题", "required": true},
                  {"type": "input-text", "name": "author", "label": "作者"},
                  {"type": "input-rich-text", "name": "content", "label": "内容"},
                  {"type": "select", "name": "status", "label": "状态", "options": [
                    {"label": "草稿", "value": "draft"},
                    {"label": "已发布", "value": "published"}
                  ]}
                ]
              }
            }
          }
        ]
      }
    ]
  }
}
```

## 树形 CRUD

```json
{
  "type": "page",
  "title": "部门管理",
  "body": {
    "type": "crud",
    "api": "/api/departments",
    "columns": [
      {"name": "name", "label": "部门名称"},
      {"name": "code", "label": "部门编码"},
      {"name": "manager", "label": "负责人"},
      {
        "type": "operation",
        "label": "操作",
        "buttons": [
          {"type": "button", "label": "编辑", "actionType": "dialog", "dialog": {...}},
          {"type": "button", "label": "删除", "actionType": "ajax", "api": "delete:/api/departments/$id"}
        ]
      }
    ],
    "childrenColumnName": "children",
    "expandConfig": {"expand": "first"}
  }
}
```

## 卡片列表 CRUD

```json
{
  "type": "page",
  "title": "项目列表",
  "body": {
    "type": "crud",
    "api": "/api/projects",
    "mode": "cards",
    "card": {
      "header": {
        "title": "${name}",
        "subTitle": "${description}"
      },
      "body": [
        {"type": "tpl", "tpl": "负责人：${owner}"},
        {"type": "tpl", "tpl": "创建时间：${createdAt}"}
      ],
      "actions": [
        {"type": "button", "label": "查看", "actionType": "url", "url": "/project/${id}"},
        {"type": "button", "label": "编辑", "actionType": "dialog", "dialog": {...}}
      ]
    }
  }
}
```

## 快速编辑 CRUD

```json
{
  "type": "page",
  "title": "库存管理",
  "body": {
    "type": "crud",
    "api": "/api/inventory",
    "quickSaveApi": "/api/inventory/batch",
    "quickSaveItemApi": "/api/inventory/$id",
    "columns": [
      {"name": "id", "label": "ID"},
      {"name": "productName", "label": "商品名称"},
      {
        "name": "stock",
        "label": "库存",
        "quickEdit": {
          "type": "input-number",
          "min": 0
        }
      },
      {
        "name": "price",
        "label": "价格",
        "quickEdit": {
          "type": "input-number",
          "precision": 2
        }
      },
      {
        "name": "status",
        "label": "状态",
        "quickEdit": {
          "type": "switch",
          "onText": "上架",
          "offText": "下架"
        }
      }
    ],
    "headerToolbar": ["bulkActions", "quickSave"]
  }
}
```

## 带统计的 CRUD

```json
{
  "type": "page",
  "title": "销售统计",
  "body": [
    {
      "type": "grid",
      "columns": [
        {
          "type": "card",
          "body": [
            {"type": "tpl", "tpl": "<h3>${totalOrders}</h3><p>总订单数</p>"}
          ]
        },
        {
          "type": "card",
          "body": [
            {"type": "tpl", "tpl": "<h3>${totalAmount}</h3><p>总金额</p>"}
          ]
        }
      ]
    },
    {
      "type": "crud",
      "api": "/api/sales",
      "columns": [
        {"name": "date", "label": "日期"},
        {"name": "orders", "label": "订单数"},
        {"name": "amount", "label": "金额"},
        {"name": "growth", "label": "增长率"}
      ],
      "footerToolbar": ["statistics", "pagination"]
    }
  ]
}
```

## API 返回格式

CRUD 接口需要返回以下格式：

```json
{
  "status": 0,
  "msg": "success",
  "data": {
    "items": [
      {"id": 1, "name": "张三"},
      {"id": 2, "name": "李四"}
    ],
    "total": 100
  }
}
```

或者简化格式（需配置 `"loadDataOnce": true`）：

```json
{
  "status": 0,
  "msg": "success",
  "data": [
    {"id": 1, "name": "张三"},
    {"id": 2, "name": "李四"}
  ]
}
```
