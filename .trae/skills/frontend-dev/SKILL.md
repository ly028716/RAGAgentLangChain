---
name: "frontend-dev"
description: "实现Vue3前端能力。新增页面/组件、Pinia状态、API封装、路由与测试时调用。"
---

# 前端开发 Skill

## 目标

- 在既有UI与状态管理方式下交付一致的用户体验
- 与后端契约对齐，保证类型安全与可测试性

## 协作约束

- 除非用户明确要求，不额外生成文档
- 不随意删除既有文档和代码（除非用户要求）

## 适用场景（触发条件）

- 新增/修改页面（views）、路由（router）、布局（layouts）
- 新增/修改状态（stores）、请求封装（api）与类型（types）
- 交互优化、异常提示、加载态与空态完善

## 代码位置速览

- 页面：frontend/src/views/
- 路由：frontend/src/router/
- 状态：frontend/src/stores/
- API：frontend/src/api/
- 样式：frontend/src/styles/
- 测试：frontend/src/__tests__/

## 默认开发规范

- 以Composition API为主，组件职责单一
- API模块只负责请求与数据整形，业务状态放Pinia
- UI优先复用Element Plus组件与既有样式变量
- 异步交互统一处理：loading、错误提示、重试入口

## 常用交付物

- 视图与状态变更（页面可用）
- 对应API方法与类型定义
- 必要的Vitest用例（关键逻辑与分支）

## 自检清单

- 路由守卫与登录态一致
- 关键操作有确认/撤销或失败提示
- 列表分页、空态、骨架屏或加载态齐全
- 类型定义不使用any兜底，契约可追踪
