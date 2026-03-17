
# AI 应用全栈工程师 - Technical Assignment

## 操作说明

### 1️⃣ 创建 GitHub 仓库

- 创建一个新的 GitHub 仓库（私有或公开均可）
- 仓库命名为：`ai-capability-service-[你的名字]`
- 添加面试官为协作者（我们会提供 GitHub ID） @IslandDancerJL

### 2️⃣ 时间限制

- 收到本邮件起 **90 分钟内**完成并提交
- 在截止时间前通过邮件发送：
  - GitHub 仓库链接
  - 仓库的 zip 压缩文件

### 3️⃣ 允许使用 AI

- 强烈鼓励使用 AI 工具（ChatGPT / Cursor / Claude 等）

---

## 任务说明

请实现一个“模型能力统一调用”的最小独立后端服务。

---

## 接口规范

实现如下接口：

**POST /v1/capabilities/run**

### 请求示例：

```json
{
  "capability": "text_summary",
  "input": {
    "text": "Long text content...",
    "max_length": 120
  },
  "request_id": "optional-id"
}
```

### 成功返回：

```json
{
  "ok": true,
  "data": {
    "result": "..."
  },
  "meta": {
    "request_id": "...",
    "capability": "text_summary",
    "elapsed_ms": 12
  }
}
```

### 失败返回：

```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  },
  "meta": {
    "request_id": "...",
    "capability": "text_summary",
    "elapsed_ms": 12
  }
}
```

---

## 基础要求

- 至少实现 `text_summary` capability
- 可使用简单逻辑模拟模型调用（无需真实模型）
- 服务可本地运行
- 提供 README，包含：
  - 启动方式
  - 示例 curl 请求
- 请按 production-ready 标准实现

---

## 加分项（可选）

- 接入真实模型 API（如 OpenAI / Claude 等）
- 支持第二个 capability
- 提供最小测试
- 简单的日志或耗时统计
