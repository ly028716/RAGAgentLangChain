---
name: "backend-dev"
description: "实现FastAPI后端能力。新增/修改API、业务逻辑、数据库迁移、LangChain/RAG/Agent集成时调用。"
---

# 后端开发 Skill

## 目标

- 在既有架构约束下交付可维护、可测试的后端功能
- 确保鉴权、校验、错误处理与观测一致

## 协作约束

- 除非用户明确要求，不额外生成文档
- 不随意删除既有文档和代码（除非用户要求）

## 适用场景（触发条件）

- 新增/修改后端API、Schema、Service逻辑、数据访问
- RAG/向量库/Agent工具与执行链路开发
- 数据库迁移、性能优化、稳定性修复

## 代码位置速览

- API：backend/app/api/v1/
- Schema：backend/app/schemas/
- Service：backend/app/services/
- Model：backend/app/models/
- Core：backend/app/core/
- Tests：backend/tests/ 与 backend/test_*.py

## 默认开发规范

- API层只做：鉴权依赖、参数校验、响应序列化、协议适配（HTTP/SSE/WebSocket）
- 业务规则放Service层，避免在路由函数里堆逻辑
- 数据访问集中到Repository或集中访问模块，避免业务层散落SQL细节
- 新增字段/接口优先兼容演进，避免破坏前端与历史数据

## 常用交付物

- 新/改API与OpenAPI一致
- 对应Schema与类型约束
- 单元/集成测试（优先覆盖关键分支与鉴权）
- 必要时提供迁移脚本与回滚思路

## 自检清单

- 鉴权：需要登录/管理员/资源归属检查是否明确
- 输入：Pydantic校验覆盖边界值与非法值
- 错误：异常返回口径一致，不泄露敏感信息
- 性能：分页、索引、N+1、向量检索参数合理
- 观测：关键路径日志/指标具备定位价值
