# AI Capability Service

一个可直接部署到 Vercel 的 Node.js 统一模型能力调用服务。

已实现内容：

- `POST /v1/capabilities/run`
- `text_summary` capability
- `text_keywords` capability
- 统一成功/失败响应结构
- request id、耗时统计、基础日志
- 最小测试

## 技术栈

- Node.js 20+
- Express 5
- Zod
- Vitest + Supertest

## 安装依赖

```bash
npm install
```

## 本地启动

```bash
npm start
```

默认地址：

- `http://127.0.0.1:3000/health`
- `http://127.0.0.1:3000/v1/capabilities/run`

## 本地测试

```bash
npm test
```

## 部署到 Vercel

项目按 Vercel 官方 Express 入口方式组织，推到 GitHub 后可以直接导入 Vercel 部署。

如果想本地模拟 Vercel：

```bash
npx vercel dev
```

## 示例请求

### 1. 文本摘要

```bash
curl -X POST http://127.0.0.1:3000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "text_summary",
    "input": {
      "text": "Express on Vercel is simple to deploy. This service exposes a single unified capability API. It is designed to be minimal and production-ready enough for the assignment.",
      "max_length": 90
    },
    "request_id": "demo-summary-001"
  }'
```

### 2. 关键词提取

```bash
curl -X POST http://127.0.0.1:3000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "text_keywords",
    "input": {
      "text": "Express on Vercel keeps deployment simple and makes capability services easy to operate.",
      "top_k": 3
    }
  }'
```

## 设计说明

- 使用 Express 5 提供 HTTP 服务，并兼容 Vercel 直接部署
- 使用 Zod 做严格输入校验，输出稳定错误码
- 通过 capability registry 做能力分发，便于继续扩展
- 使用简单文本算法模拟模型调用，满足题目要求且本地可运行
- 增加健康检查、请求耗时与 request id，便于排查问题

