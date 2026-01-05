# AI-RSS-Hub API 使用说明书

> 为客户端开发者提供的完整 API 集成指南

---

## 📋 目录

- [基础信息](#基础信息)
- [认证方式](#认证方式)
- [API 端点](#api-端点)
  - [健康检查](#1-健康检查)
  - [系统状态](#2-系统状态)
  - [获取 RSS 源列表](#3-获取-rss-源列表)
  - [添加 RSS 源](#4-添加-rss-源)
  - [获取文章列表](#5-获取文章列表)
  - [手动触发抓取](#6-手动触发抓取)
- [数据模型](#数据模型)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [代码示例](#代码示例)

---

## 基础信息

### 服务器信息

- **Base URL**: `http://your-server:8000` (或你的域名)
- **API 前缀**: `/api`
- **数据格式**: `application/json`
- **字符编码**: `UTF-8`

### 请求示例

```bash
# 完整 URL 示例
http://your-server:8000/api/feeds
http://your-server:8000/api/articles?limit=50
```

---

## 认证方式

### 认证说明

AI-RSS-Hub 使用 **API Token** 认证方式保护敏感操作。

- **公开接口**（无需认证）：
  - 获取 RSS 源列表
  - 获取文章列表
  - 健康检查
  - 系统状态

- **受保护接口**（需要认证）：
  - 添加 RSS 源
  - 手动触发抓取

### 请求头设置

对于需要认证的接口，需要在请求头中添加：

```http
X-API-Token: your_api_token_here
```

### 获取 API Token

API Token 由服务器管理员配置，在服务器的 `.env` 文件中设置：

```bash
API_TOKEN=your_secure_token_here
```

生成安全的 Token：

```bash
python scripts/generate_token.py
```

---

## API 端点

### 1. 健康检查

检查服务是否正常运行。

**端点**: `GET /api/health`

**认证**: 不需要

**请求示例**:

```bash
curl http://your-server:8000/api/health
```

**响应示例**:

```json
{
  "status": "ok",
  "message": "AI-RSS-Hub is running"
}
```

**用途**:
- 服务健康监控
- 负载均衡器健康检查
- 客户端连接测试

---

### 2. 系统状态

获取系统运行状态和配置信息。

**端点**: `GET /api/status`

**认证**: 不需要

**请求示例**:

```bash
curl http://your-server:8000/api/status
```

**响应示例**:

```json
{
  "status": "running",
  "scheduler": {
    "status": "running",
    "next_run_time": "2025-12-25T11:00:00"
  },
  "database": "sqlite:///./ai_rss_hub.db",
  "fetch_interval_hours": 1,
  "llm_configured": true
}
```

**字段说明**:
- `status`: 服务运行状态
- `scheduler`: 定时任务调度器信息
  - `status`: 调度器状态
  - `next_run_time`: 下次抓取时间
- `database`: 数据库连接信息
- `fetch_interval_hours`: RSS 抓取间隔（小时）
- `llm_configured`: LLM 是否已配置

**用途**:
- 监控系统状态
- 确认配置是否正确
- 查看下次自动抓取时间

---

### 3. 获取 RSS 源列表

获取所有已配置的 RSS 源。

**端点**: `GET /api/feeds`

**认证**: 不需要

**查询参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| `active_only` | boolean | 否 | 是否只返回启用的源 | `false` |

**请求示例**:

```bash
# 获取所有 RSS 源
curl http://your-server:8000/api/feeds

# 只获取启用的 RSS 源
curl http://your-server:8000/api/feeds?active_only=true
```

**响应示例**:

```json
[
  {
    "id": 1,
    "name": "Hacker News",
    "url": "https://hnrss.org/frontpage",
    "category": "tech",
    "is_active": true,
    "created_at": "2025-12-25T10:00:00"
  },
  {
    "id": 2,
    "name": "TechCrunch",
    "url": "https://techcrunch.com/feed/",
    "category": "tech",
    "is_active": true,
    "created_at": "2025-12-25T10:00:00"
  }
]
```

**字段说明**:
- `id`: RSS 源唯一标识
- `name`: RSS 源名称
- `url`: RSS 源地址
- `category`: 分类标签
- `is_active`: 是否启用
- `created_at`: 创建时间（ISO 8601 格式）

**用途**:
- 展示所有可用的 RSS 源
- 让用户选择订阅的源
- 按 category 分类展示

---

### 4. 添加 RSS 源

添加新的 RSS 源到系统中。

**端点**: `POST /api/feeds`

**认证**: **需要**

**请求头**:

```http
Content-Type: application/json
X-API-Token: your_api_token_here
```

**请求体**:

```json
{
  "name": "GitHub Blog",
  "url": "https://github.blog/feed/",
  "category": "tech",
  "is_active": true
}
```

**字段说明**:

| 字段 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| `name` | string | 是 | RSS 源名称 | - |
| `url` | string | 是 | RSS 源 URL（必须是有效 URL） | - |
| `category` | string | 否 | 分类标签 | `"tech"` |
| `is_active` | boolean | 否 | 是否启用 | `true` |

**请求示例**:

```bash
curl -X POST http://your-server:8000/api/feeds \
  -H "Content-Type: application/json" \
  -H "X-API-Token: your_api_token_here" \
  -d '{
    "name": "GitHub Blog",
    "url": "https://github.blog/feed/",
    "category": "tech",
    "is_active": true
  }'
```

**成功响应** (201 Created):

```json
{
  "id": 4,
  "name": "GitHub Blog",
  "url": "https://github.blog/feed/",
  "category": "tech",
  "is_active": true,
  "created_at": "2025-12-25T10:30:00"
}
```

**错误响应**:

```json
# 401 Unauthorized - Token 缺失或无效
{
  "detail": "API Token 缺失，请在请求头中提供 X-API-Token"
}

# 400 Bad Request - URL 已存在
{
  "detail": "RSS 源已存在: https://github.blog/feed/"
}

# 422 Unprocessable Entity - URL 格式无效
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "无效的 URL 格式",
      "type": "value_error.url.scheme"
    }
  ]
}
```

**URL 验证规则**:
- 必须是有效的 HTTP/HTTPS URL
- 必须指向一个有效的 RSS/Atom feed
- 不允许重复的 URL

---

### 5. 获取文章列表

获取文章列表，支持多种筛选条件。

**端点**: `GET /api/articles`

**认证**: 不需要

**查询参数**:

| 参数 | 类型 | 必填 | 说明 | 默认值 | 限制 |
|------|------|------|------|--------|------|
| `limit` | integer | 否 | 返回数量限制 | `50` | 1-200 |
| `category` | string | 否 | 按分类筛选 | `null` | - |
| `days` | integer | 否 | 获取最近 N 天的文章 | `null` | 1-365 |

**请求示例**:

```bash
# 获取最近 50 篇文章
curl http://your-server:8000/api/articles?limit=50

# 获取最近 20 篇 tech 类别的文章
curl "http://your-server:8000/api/articles?category=tech&limit=20"

# 获取最近 7 天的 100 篇文章
curl "http://your-server:8000/api/articles?days=7&limit=100"

# 组合查询：最近 3 天的 tech 类别文章，最多 30 篇
curl "http://your-server:8000/api/articles?category=tech&days=3&limit=30"
```

**响应示例**:

```json
[
  {
    "id": 1,
    "title": "Show HN: I built a tool to...",
    "link": "https://news.ycombinator.com/item?id=123456",
    "summary": "一位开发者分享了他构建的工具，该工具可以帮助开发者更高效地管理项目。工具支持多种编程语言，并提供详细的文档和示例。",
    "summary_en": "A developer shared a tool they built to help developers manage projects more efficiently. The tool supports multiple programming languages and provides detailed documentation and examples.",
    "published_at": "2025-12-25T09:30:00",
    "feed_id": 1,
    "feed_name": "Hacker News",
    "created_at": "2025-12-25T10:00:00"
  },
  {
    "id": 2,
    "title": "AI Breakthrough in Language Models",
    "link": "https://techcrunch.com/2025/12/25/ai-breakthrough",
    "summary": "研究人员在语言模型领域取得重大突破，新的模型在多个基准测试中超越了以往的记录。这项技术有望应用于更多实际场景。",
    "summary_en": "Researchers have made a major breakthrough in language models, with new models surpassing previous records across multiple benchmarks. This technology is expected to be applied to more real-world scenarios.",
    "published_at": "2025-12-25T08:15:00",
    "feed_id": 2,
    "feed_name": "TechCrunch",
    "created_at": "2025-12-25T10:00:00"
  }
]
```

**字段说明**:
- `id`: 文章唯一标识
- `title`: 文章标题
- `link`: 文章原始链接
- `summary`: AI 生成的中文摘要（可能为 `null` 如果尚未生成）
- `summary_en`: AI 生成的英文摘要（可能为 `null` 如果尚未生成，或旧文章未更新）
- `published_at`: 文章发布时间（ISO 8601 格式）
- `feed_id`: 所属 RSS 源 ID
- `feed_name`: 所属 RSS 源名称
- `created_at**: 记录创建时间

**排序规则**:
- 默认按 `published_at` 降序排列（最新的在前）
- 如果 `published_at` 相同，按 `created_at` 降序

**分页建议**:
- 客户端可以实现分页，使用 `limit` 参数控制每页数量
- 可以在客户端记录已获取的最大 `id`，下次请求时跳过

---

### 6. 手动触发抓取

手动触发 RSS 抓取任务，立即获取所有源的最新文章。

**端点**: `POST /api/feeds/fetch`

**认证**: **需要**

**请求头**:

```http
X-API-Token: your_api_token_here
```

**请求示例**:

```bash
curl -X POST http://your-server:8000/api/feeds/fetch \
  -H "X-API-Token: your_api_token_here"
```

**成功响应** (200 OK):

```json
{
  "status": "success",
  "message": "成功抓取 3 个源，获取 15 篇新文章",
  "stats": {
    "total_feeds": 3,
    "successful_feeds": 3,
    "failed_feeds": 0,
    "total_articles": 15,
    "details": [
      {
        "feed_name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "articles_count": 5,
        "status": "success"
      },
      {
        "feed_name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "articles_count": 6,
        "status": "success"
      },
      {
        "feed_name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "articles_count": 4,
        "status": "success"
      }
    ]
  }
}
```

**错误响应**:

```json
# 401 Unauthorized - Token 缺失或无效
{
  "detail": "API Token 缺失，请在请求头中提供 X-API-Token"
}

# 500 Internal Server Error - 抓取失败
{
  "detail": "抓取失败: 网络连接超时"
}
```

**字段说明**:
- `status`: 执行状态
- `message`: 结果摘要
- `stats`: 详细统计
  - `total_feeds`: 总源数
  - `successful_feeds`: 成功抓取的源数
  - `failed_feeds`: 失败的源数
  - `total_articles`: 获取的文章总数
  - `details`: 每个源的详细结果

**注意事项**:
- 此操作是同步的，可能需要较长时间（取决于源数量）
- 建议客户端显示加载状态
- 不要频繁调用（建议至少间隔 5 分钟）
- 如果正在自动抓取，此请求会排队等待

**用途**:
- 用户主动刷新内容
- 测试新增的 RSS 源
- 内容更新后的即时同步

---

## 数据模型

### Feed 模型

RSS 源的数据结构。

```json
{
  "id": 1,                           // 整数，唯一标识
  "name": "Hacker News",             // 字符串，源名称
  "url": "https://hnrss.org/frontpage",  // 字符串，源 URL
  "category": "tech",                // 字符串，分类
  "is_active": true,                 // 布尔值，是否启用
  "created_at": "2025-12-25T10:00:00"  // 字符串，ISO 8601 格式时间
}
```

### Article 模型

文章的数据结构。

```json
{
  "id": 1,                           // 整数，唯一标识
  "title": "Article Title",          // 字符串，文章标题
  "link": "https://example.com/article",  // 字符串，文章链接
  "summary": "AI生成摘要...",  // 字符串或 null，AI 中文摘要
  "summary_en": "AI generated summary...",  // 字符串或 null，AI 英文摘要（新增）
  "published_at": "2025-12-25T09:30:00",  // 字符串或 null，发布时间
  "feed_id": 1,                      // 整数，所属源 ID
  "feed_name": "Hacker News",        // 字符串或 null，源名称
  "created_at": "2025-12-25T10:00:00"  // 字符串，记录创建时间
}
```

### 时间格式

所有时间字段使用 **ISO 8601** 格式：

```
2025-12-25T10:30:00
2025-12-25T10:30:00.123456  // 包含微秒
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 | 示例场景 |
|--------|------|----------|
| 200 OK | 请求成功 | 获取列表成功、手动抓取完成 |
| 201 Created | 资源创建成功 | 添加 RSS 源成功 |
| 400 Bad Request | 请求参数错误 | URL 已存在、参数验证失败 |
| 401 Unauthorized | 未认证 | 缺少 API Token |
| 403 Forbidden | 无权限 | API Token 无效 |
| 404 Not Found | 资源不存在 | 访问不存在的端点 |
| 422 Unprocessable Entity | 参数验证失败 | URL 格式无效、参数类型错误 |
| 429 Too Many Requests | 请求过于频繁 | 触发速率限制 |
| 500 Internal Server Error | 服务器错误 | 数据库错误、网络错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

或（参数验证失败）：

```json
{
  "detail": [
    {
      "loc": ["body", "url"],
      "msg": "无效的 URL 格式",
      "type": "value_error.url.scheme"
    }
  ]
}
```

### 错误处理建议

1. **网络错误**：实现重试机制（指数退避）
2. **429 错误**：等待后重试（建议 60 秒后）
3. **5xx 错误**：记录日志，稍后重试
4. **4xx 错误**：检查请求参数，不要重试
5. **超时处理**：设置合理的超时时间（建议 30 秒）

---

## 最佳实践

### 1. 认证管理

**Token 存储**:
```javascript
// ❌ 不要：硬编码在代码中
const token = "my-token-123";

// ✅ 推荐：使用环境变量或配置文件
const token = process.env.API_TOKEN;
```

**Token 传输**:
```javascript
// ✅ 推荐：每次请求都从安全存储中获取
const headers = {
  'X-API-Token': getSecureToken()
};
```

### 2. 请求优化

**缓存策略**:
- 文章列表可以缓存 5-10 分钟
- RSS 源列表可以缓存更长时间（30 分钟）
- 使用 ETag 或 Last-Modified 标记（如果未来支持）

**请求合并**:
```javascript
// ❌ 不推荐：多次请求
const feeds = await fetchFeeds();
const articles = await fetchArticles();

// ✅ 推荐：并行请求
const [feeds, articles] = await Promise.all([
  fetchFeeds(),
  fetchArticles()
]);
```

**分页加载**:
```javascript
// ✅ 推荐：初始加载少量，按需加载更多
const initialArticles = await fetchArticles({ limit: 20 });
// 用户滚动时加载更多
const moreArticles = await fetchArticles({ limit: 20, offset: 20 });
```

### 3. 错误处理

```javascript
try {
  const response = await fetch(url, options);
  if (!response.ok) {
    if (response.status === 429) {
      // 速率限制，等待后重试
      await wait(60000);
      return retryRequest();
    }
    throw new Error(`HTTP ${response.status}`);
  }
  return await response.json();
} catch (error) {
  console.error('Request failed:', error);
  // 显示用户友好的错误信息
  showError('获取数据失败，请稍后重试');
}
```

### 4. 用户体验

**加载状态**:
- 显示加载指示器
- 显示预估等待时间
- 允许用户取消操作

**离线支持**:
- 缓存已获取的文章
- 离线时显示缓存内容
- 网络恢复后自动同步

**刷新策略**:
```javascript
// ✅ 推荐：下拉刷新 + 定期自动刷新
// 用户下拉时刷新
onPullToRefresh: () => fetchArticles({ limit: 20 });

// 后台定期刷新（每 30 分钟）
setInterval(() => {
  fetchArticles({ limit: 20, silent: true });
}, 30 * 60 * 1000);
```

### 5. 性能优化

**图片懒加载**:
```html
<img data-src="article-image.jpg" loading="lazy" />
```

**虚拟滚动**（长列表）:
```javascript
// 使用虚拟滚动库如 react-window、vue-virtual-scroller
import { FixedSizeList } from 'react-window';
```

**数据去重**:
```javascript
// ✅ 推荐：使用 id 或 link 去重
const uniqueArticles = articles.filter((article, index, self) =>
  index === self.findIndex(a => a.id === article.id)
);
```

### 6. 安全建议

**不要暴露 Token**:
- 使用 HTTPS（生产环境）
- Token 不要存储在本地存储（LocalStorage）
- 考虑使用代理服务器隐藏 Token

**输入验证**:
```javascript
// ✅ 推荐：客户端也做验证
function validateUrl(url) {
  try {
    new URL(url);
    return url.startsWith('http://') || url.startsWith('https://');
  } catch {
    return false;
  }
}
```

---

## 代码示例

### JavaScript / TypeScript

#### 基础配置

```typescript
// config.ts
const API_CONFIG = {
  baseURL: 'http://your-server:8000',
  apiToken: 'your_api_token_here'
};

export default API_CONFIG;
```

#### API 客户端

```typescript
// api-client.ts
import API_CONFIG from './config';

class RSSClient {
  private baseURL: string;
  private token: string;

  constructor(baseURL: string, token: string) {
    this.baseURL = baseURL;
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // 添加认证头（如果需要）
    if (options.requiresAuth && this.token) {
      headers['X-API-Token'] = this.token;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // 健康检查
  async healthCheck(): Promise<{ status: string; message: string }> {
    return this.request('/api/health');
  }

  // 获取系统状态
  async getStatus(): Promise<any> {
    return this.request('/api/status');
  }

  // 获取 RSS 源列表
  async getFeeds(activeOnly: boolean = false): Promise<Feed[]> {
    const params = activeOnly ? '?active_only=true' : '';
    return this.request(`/api/feeds${params}`);
  }

  // 添加 RSS 源
  async addFeed(feedData: {
    name: string;
    url: string;
    category?: string;
    is_active?: boolean;
  }): Promise<Feed> {
    return this.request('/api/feeds', {
      method: 'POST',
      requiresAuth: true,
      body: JSON.stringify(feedData),
    });
  }

  // 获取文章列表
  async getArticles(params: {
    limit?: number;
    category?: string;
    days?: number;
  } = {}): Promise<Article[]> {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.category) queryParams.append('category', params.category);
    if (params.days) queryParams.append('days', params.days.toString());

    const queryString = queryParams.toString();
    const endpoint = queryString ? `/api/articles?${queryString}` : '/api/articles';

    return this.request(endpoint);
  }

  // 手动触发抓取
  async triggerFetch(): Promise<{
    status: string;
    message: string;
    stats: any;
  }> {
    return this.request('/api/feeds/fetch', {
      method: 'POST',
      requiresAuth: true,
    });
  }
}

// 类型定义
interface Feed {
  id: number;
  name: string;
  url: string;
  category: string;
  is_active: boolean;
  created_at: string;
}

interface Article {
  id: number;
  title: string;
  link: string;
  summary: string | null;
  summary_en: string | null;
  published_at: string | null;
  feed_id: number;
  feed_name: string | null;
  created_at: string;
}

// 使用示例
const client = new RSSClient(API_CONFIG.baseURL, API_CONFIG.apiToken);

// 获取文章
const articles = await client.getArticles({ limit: 50 });
console.log('Articles:', articles);

// 添加新源
const newFeed = await client.addFeed({
  name: 'My Blog',
  url: 'https://example.com/feed',
  category: 'tech'
});
console.log('New feed added:', newFeed);
```

#### React Hook 示例

```typescript
// hooks/useArticles.ts
import { useState, useEffect } from 'react';
import { RSSClient, Article } from '../api-client';

const client = new RSSClient(
  process.env.REACT_APP_API_URL || 'http://localhost:8000',
  process.env.REACT_APP_API_TOKEN || ''
);

export function useArticles(options: {
  limit?: number;
  category?: string;
  days?: number;
} = {}) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchArticles = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await client.getArticles(options);
      setArticles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, [options.limit, options.category, options.days]);

  return { articles, loading, error, refetch: fetchArticles };
}

// 使用
function ArticleList() {
  const { articles, loading, error, refetch } = useArticles({ limit: 20 });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <button onClick={() => refetch()}>刷新</button>
      <ul>
        {articles.map(article => (
          <li key={article.id}>
            <h3>{article.title}</h3>
            <p>{article.summary}</p>
            <small>来源: {article.feed_name}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Python

```python
# rss_client.py
import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Feed:
    id: int
    name: str
    url: str
    category: str
    is_active: bool
    created_at: str

@dataclass
class Article:
    id: int
    title: str
    link: str
    summary: Optional[str]
    summary_en: Optional[str]
    published_at: Optional[str]
    feed_id: int
    feed_name: Optional[str]
    created_at: str

class RSSClient:
    def __init__(self, base_url: str, api_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop('headers', {})

        # 添加认证头
        if kwargs.get('requires_auth') and self.api_token:
            headers['X-API-Token'] = self.api_token

        headers['Content-Type'] = 'application/json'

        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise

    def health_check(self) -> Dict[str, str]:
        """健康检查"""
        return self._request('GET', '/api/health')

    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return self._request('GET', '/api/status')

    def get_feeds(self, active_only: bool = False) -> List[Feed]:
        """获取 RSS 源列表"""
        params = {'active_only': 'true'} if active_only else {}
        response = self._request('GET', '/api/feeds', params=params)
        return [Feed(**item) for item in response]

    def add_feed(self, name: str, url: str, category: str = 'tech',
                 is_active: bool = True) -> Feed:
        """添加 RSS 源"""
        data = {
            'name': name,
            'url': url,
            'category': category,
            'is_active': is_active
        }
        response = self._request(
            'POST',
            '/api/feeds',
            json=data,
            requires_auth=True
        )
        return Feed(**response)

    def get_articles(self, limit: int = 50, category: str = None,
                     days: int = None) -> List[Article]:
        """获取文章列表"""
        params = {'limit': limit}
        if category:
            params['category'] = category
        if days:
            params['days'] = days

        response = self._request('GET', '/api/articles', params=params)
        return [Article(**item) for item in response]

    def trigger_fetch(self) -> Dict[str, Any]:
        """手动触发抓取"""
        return self._request('POST', '/api/feeds/fetch', requires_auth=True)

# 使用示例
if __name__ == '__main__':
    client = RSSClient(
        base_url='http://localhost:8000',
        api_token='your_api_token_here'
    )

    # 获取文章
    articles = client.get_articles(limit=20)
    print(f"获取到 {len(articles)} 篇文章")

    for article in articles[:5]:
        print(f"\n标题: {article.title}")
        print(f"摘要: {article.summary}")
        print(f"来源: {article.feed_name}")

    # 添加新源
    try:
        new_feed = client.add_feed(
            name='Example Feed',
            url='https://example.com/feed',
            category='tech'
        )
        print(f"\n成功添加源: {new_feed.name}")
    except Exception as e:
        print(f"\n添加失败: {e}")
```

### cURL 示例

```bash
#!/bin/bash

API_BASE="http://your-server:8000"
API_TOKEN="your_api_token_here"

# 健康检查
echo "=== 健康检查 ==="
curl -s "$API_BASE/api/health" | jq '.'

echo -e "\n=== 获取系统状态 ==="
curl -s "$API_BASE/api/status" | jq '.'

echo -e "\n=== 获取 RSS 源 ==="
curl -s "$API_BASE/api/feeds" | jq '.'

echo -e "\n=== 获取文章（最近 10 篇）==="
curl -s "$API_BASE/api/articles?limit=10" | jq '.[] | {title, feed_name}'

echo -e "\n=== 添加新 RSS 源 ==="
curl -s -X POST "$API_BASE/api/feeds" \
  -H "Content-Type: application/json" \
  -H "X-API-Token: $API_TOKEN" \
  -d '{
    "name": "BBC News",
    "url": "http://feeds.bbci.co.uk/news/rss.xml",
    "category": "news",
    "is_active": true
  }' | jq '.'

echo -e "\n=== 手动触发抓取 ==="
curl -s -X POST "$API_BASE/api/feeds/fetch" \
  -H "X-API-Token: $API_TOKEN" | jq '.'
```

---

## 附录

### A. 完整的错误码列表

| 错误码 | HTTP 状态 | 说明 | 解决方案 |
|--------|-----------|------|----------|
| AUTH_MISSING | 401 | 缺少 API Token | 添加 X-API-Token 请求头 |
| AUTH_INVALID | 403 | API Token 无效 | 检查 Token 是否正确 |
| URL_EXISTS | 400 | RSS 源 URL 已存在 | 不要重复添加相同 URL |
| URL_INVALID | 422 | URL 格式无效 | 检查 URL 格式 |
| RATE_LIMIT | 429 | 请求过于频繁 | 降低请求频率 |
| SERVER_ERROR | 500 | 服务器内部错误 | 联系管理员或稍后重试 |

### B. 常见问题

**Q: 为什么有些文章的 summary 或 summary_en 是 null？**
A: AI 摘要正在生成中，或者 LLM API 调用失败。对于旧文章，可能尚未生成英文摘要（summary_en）。稍后刷新即可。

**Q: 如何获取所有文章？**
A: 分批获取，每次最多 200 篇：`?limit=200&days=365`

**Q: API 有速率限制吗？**
A: 是的，默认每分钟 60 次请求。超过会返回 429 错误。

**Q: 如何监控抓取状态？**
A: 调用 `/api/status` 查看调度器状态和下次抓取时间。

**Q: 能否修改或删除 RSS 源？**
A: 当前版本不支持。需要此功能请联系管理员。

### C. 性能参考

| 操作 | 预期响应时间 | 备注 |
|------|--------------|------|
| 健康检查 | < 100ms | 极快 |
| 获取文章列表 | 100-500ms | 取决于 limit |
| 获取 RSS 源 | < 100ms | 通常很快 |
| 添加 RSS 源 | 200-1000ms | 包含 URL 验证 |
| 手动触发抓取 | 5-30秒 | 取决于源数量 |

### D. 更新日志

**v1.0.0** (2025-12-25)
- 初始版本
- 支持 RSS 源管理
- 支持 AI 摘要
- API Token 认证
- 速率限制

---

## 技术支持

如有问题，请联系：
- GitHub Issues: https://github.com/goodniuniu/AI-RSS-Hub/issues
- Email: your-email@example.com

---

**最后更新**: 2026-01-04
**API 版本**: 1.0.0
