# Chart 图表组件

Chart 组件基于 ECharts 实现，用于数据可视化展示。

## 基本用法

```json
{
  "type": "chart",
  "config": {
    "xAxis": {
      "type": "category",
      "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    },
    "yAxis": {
      "type": "value"
    },
    "series": [{
      "data": [150, 230, 224, 218, 135, 147, 260],
      "type": "line"
    }]
  }
}
```

## 属性说明

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| type | string | - | 必须为 "chart" |
| config | object | - | ECharts 配置 |
| api | API | - | 数据接口 |
| width | number | - | 图表宽度 |
| height | number | 300 | 图表高度 |
| replaceChartOption | boolean | false | 是否替换配置 |

## 柱状图

```json
{
  "type": "chart",
  "config": {
    "title": {"text": "销售统计"},
    "xAxis": {
      "type": "category",
      "data": ["Q1", "Q2", "Q3", "Q4"]
    },
    "yAxis": {"type": "value"},
    "series": [{
      "name": "销售额",
      "type": "bar",
      "data": [120, 200, 150, 80]
    }]
  }
}
```

## 饼图

```json
{
  "type": "chart",
  "config": {
    "title": {"text": "访问来源"},
    "series": [{
      "type": "pie",
      "radius": "50%",
      "data": [
        {"value": 1048, "name": "搜索引擎"},
        {"value": 735, "name": "直接访问"},
        {"value": 580, "name": "邮件营销"},
        {"value": 484, "name": "联盟广告"}
      ]
    }]
  }
}
```

## 动态数据

```json
{
  "type": "chart",
  "api": "/api/chart-data",
  "config": {
    "xAxis": {
      "type": "category",
      "data": "${categories}"
    },
    "yAxis": {"type": "value"},
    "series": [{
      "type": "line",
      "data": "${values}"
    }]
  }
}
```

## 多系列图表

```json
{
  "type": "chart",
  "config": {
    "legend": {"data": ["销售额", "利润"]},
    "xAxis": {
      "type": "category",
      "data": ["Q1", "Q2", "Q3", "Q4"]
    },
    "yAxis": {"type": "value"},
    "series": [
      {"name": "销售额", "type": "bar", "data": [120, 200, 150, 80]},
      {"name": "利润", "type": "line", "data": [30, 50, 40, 20]}
    ]
  }
}
```
