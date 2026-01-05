# AI-RSS-Client 墨水屏前端实现方案

> 基于 epaper-with-ai-news 的成功经验，为 AI-RSS-Client 实现前后端分离的墨水屏前端

## 📋 架构分析

### 当前状态

**已完成模块** ✅
- `src/display/epaper_driver.py` - 墨水屏硬件驱动
- `src/display/renderer.py` - 内容渲染器
- `src/display/fonts.py` - 字体管理
- `src/display/layout_engine.py` - 排版引擎
- `lib/waveshare_epd/` - Waveshare 3.52英寸墨水屏底层驱动

**待实现模块** 🚧
- `src/fetchers/` - API 客户端（从 AI-RSS-Hub 获取数据）
- `src/services/` - 业务服务层
- `src/processors/` - 内容处理器
- `src/models/` - 数据模型定义

## 🎯 实现目标

### 核心功能
1. **API 集成** - 从 AI-RSS-Hub 获取文章和摘要
2. **内容管理** - 本地缓存、阅读状态追踪
3. **显示调度** - 定期更新墨水屏显示
4. **离线支持** - 无网络时使用缓存内容
5. **服务化部署** - systemd 服务管理

### 系统架构（前后端分离）

```
┌─────────────────────────────────────────────────────────┐
│                   AI-RSS-Client (前端)                   │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ API Client    │  │ Content Mgr  │  │ Display Svc  │  │
│  │ (fetchers/)   │→ │ (services/)  │→ │ (services/)  │  │
│  └───────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                   ↓                   ↓        │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Display & Rendering System                 │ │
│  │  (renderer, fonts, layout, driver)                  │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           ↓ HTTP API
┌─────────────────────────────────────────────────────────┐
│                  AI-RSS-Hub (后端)                       │
├─────────────────────────────────────────────────────────┤
│  RSS Fetch → AI Summary → Database → REST API           │
└─────────────────────────────────────────────────────────┘
```

## 📁 目录结构规划

```
AI-RSS-Client/
├── src/
│   ├── display/              # 已完成
│   │   ├── epaper_driver.py
│   │   ├── renderer.py
│   │   ├── fonts.py
│   │   └── layout_engine.py
│   │
│   ├── fetchers/             # 🆕 API 客户端
│   │   ├── __init__.py
│   │   ├── api_client.py     # AI-RSS-Hub API 客户端
│   │   └── health_checker.py # 健康检查
│   │
│   ├── services/             # 🆕 业务服务
│   │   ├── __init__.py
│   │   ├── content_manager.py    # 内容管理和缓存
│   │   └── display_scheduler.py  # 显示调度服务
│   │
│   ├── processors/           # 🆕 内容处理
│   │   ├── __init__.py
│   │   └── cache.py          # 缓存管理
│   │
│   ├── models/               # 🆕 数据模型
│   │   ├── __init__.py
│   │   ├── article.py        # Article 模型
│   │   └── feed.py           # Feed 模型
│   │
│   ├── utils/                # 已完成
│   │   └── logger.py
│   │
│   └── config.py             # 已完成
│
├── scripts/                  # 🆕 服务脚本
│   ├── display_service.py         # 显示调度服务
│   ├── api_client_service.py      # API 客户端服务（可选）
│   └── install.sh                 # 安装脚本
│
├── tests/                    # 已有测试 + 🆕 集成测试
│   └── test_integration.py
│
├── config.yml                # 已完成
├── requirements.txt          # 需要更新
└── main.py                   # 🆕 主程序入口
```

## 🔧 技术实现细节

### 1. API 客户端 (fetchers/api_client.py)

**功能**:
- 连接到 AI-RSS-Hub (http://localhost:8000)
- 获取文章列表 (GET /api/articles)
- 获取 RSS 源列表 (GET /api/feeds)
- 健康检查 (GET /api/health)
- 错误处理和重试机制

**关键方法**:
```python
class AIRSSHubClient:
    def fetch_articles(limit: int = 50, days: int = 7) -> List[Article]
    def fetch_feeds(active_only: bool = True) -> List[Feed]
    def check_health() -> bool
    def trigger_fetch() -> bool  # POST /api/feeds/fetch
```

### 2. 内容管理器 (services/content_manager.py)

**功能**:
- 定期从 AI-RSS-Hub 获取新文章
- 本地缓存（文件系统 + SQLite）
- 阅读状态追踪（已读/未读）
- 离线内容管理

**数据流**:
```
API Client → Fetch Articles → Cache Locally → Track Read Status
```

**缓存策略**:
- L1: 内存缓存（最近显示的文章）
- L2: SQLite 数据库（所有文章）
- L3: JSON 文件备份（离线恢复）

### 3. 显示调度器 (services/display_scheduler.py)

**功能**:
- 定期更新墨水屏显示（默认 1 分钟）
- 选择未读文章优先显示
- 所有文章读完时随机选择
- 生成渲染图像并刷新硬件

**调度逻辑**:
```python
while True:
    # 1. 从内容管理器获取文章
    articles = content_manager.get_undisplayed_articles()

    # 2. 选择一篇文章
    if articles:
        article = select_article(articles)
    else:
        article = content_manager.get_random_read_article()

    # 3. 渲染并显示
    renderer.display_article(article)

    # 4. 标记为已读
    content_manager.mark_as_displayed(article.id)

    # 5. 等待下次刷新
    sleep(interval_minutes * 60)
```

### 4. 数据模型 (models/)

**Article 模型** (与后端 API 对应):
```python
@dataclass
class Article:
    id: int
    feed_id: int
    title: str
    link: str
    content: Optional[str]
    summary: Optional[str]  # AI 生成的摘要
    published_at: Optional[str]
    created_at: str

    # 前端扩展字段
    displayed_at: Optional[str] = None  # 显示时间
    display_count: int = 0              # 显示次数
    is_favorite: bool = False           # 是否收藏
```

**Feed 模型**:
```python
@dataclass
class Feed:
    id: int
    name: str
    url: str
    category: str
    is_active: bool
    created_at: str
```

## 🔄 与 epaper-with-ai-news 的对应关系

| epaper-with-ai-news | AI-RSS-Client | 说明 |
|---------------------|---------------|------|
| 直接获取 RSS 源 | 从 AI-RSS-Hub API 获取 | 前后端分离 |
| 内置 AI 摘要 | 后端提供摘要字段 | 复用后端能力 |
| 本地内容爬取 | 后端负责内容获取 | 前端只负责显示 |
| 单体应用 | 前后端分离架构 | 更清晰的职责划分 |

**保留的模块**:
- ✅ 墨水屏驱动和渲染系统（完全复用）
- ✅ 排版和字体管理（完全复用）
- ✅ 显示调度逻辑（参考实现）
- ✅ 缓存和离线支持（参考实现）

**简化的模块**:
- ❌ 不需要 RSS 解析（后端处理）
- ❌ 不需要 AI 摘要生成（后端处理）
- ❌ 不需要内容爬取（后端处理）

## 📝 配置文件 (config.yml)

需要添加的配置项：

```yaml
# API 配置
api:
  base_url: "http://localhost:8000"
  timeout: 10
  retry_attempts: 3
  retry_delay: 2

# 内容获取
content_fetch:
  interval_minutes: 20       # 从 API 获取内容的间隔
  batch_size: 50             # 每次获取的文章数
  max_cached_articles: 500   # 最大缓存文章数

# 显示调度
display_scheduler:
  interval_minutes: 1        # 显示刷新间隔
  random_on_empty: true      # 无未读时随机显示
  mark_as_read: true         # 显示后标记为已读

# 缓存配置
cache:
  sqlite_db: "data/articles.db"
  offline_backup: "data/offline_cache.json"
```

## 🚀 实现步骤

### Phase 1: API 客户端 (优先级: 🔴 高)
1. 实现 `fetchers/api_client.py`
2. 实现健康检查和错误处理
3. 测试与 AI-RSS-Hub 的连接
4. 编写单元测试

### Phase 2: 数据模型和缓存 (优先级: 🔴 高)
1. 实现 `models/article.py` 和 `models/feed.py`
2. 实现 `processors/cache.py` (SQLite + JSON)
3. 实现阅读状态追踪
4. 编写数据访问层测试

### Phase 3: 内容管理器 (优先级: 🟡 中)
1. 实现 `services/content_manager.py`
2. 集成 API 客户端和缓存
3. 实现定期获取逻辑
4. 添加离线支持
5. 集成测试

### Phase 4: 显示调度器 (优先级: 🟡 中)
1. 实现 `services/display_scheduler.py`
2. 集成现有的渲染系统
3. 实现调度逻辑（未读优先、随机显示）
4. 添加显示状态追踪

### Phase 5: 服务化部署 (优先级: 🟢 低)
1. 实现 `scripts/display_service.py`
2. 创建 systemd 服务文件
3. 编写安装脚本 `scripts/install.sh`
4. 测试开机自启
5. 编写运维文档

### Phase 6: 优化和完善 (优先级: 🟢 低)
1. 性能优化和内存管理
2. 日志和监控
3. 错误恢复机制
4. 配置管理工具
5. 集成测试覆盖

## 🧪 测试策略

### 单元测试
- API 客户端 mock 测试
- 缓存层测试
- 内容管理器测试
- 显示调度器逻辑测试

### 集成测试
- 与 AI-RSS-Hub 端到端测试
- 墨水屏硬件显示测试
- 离线模式测试

### 手动测试
```bash
# 1. 测试 API 连接
python tests/test_api_client.py

# 2. 测试内容获取
python tests/test_content_manager.py

# 3. 测试显示功能
python tests/test_display.py

# 4. 测试完整流程
python main.py --once
```

## 📊 性能指标

参考 epaper-with-ai-news 的性能：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 显示刷新时间 | < 3 秒 | 硬件刷新 + 渲染 |
| API 响应时间 | < 1 秒 | 获取 50 篇文章 |
| 内存占用 | < 100MB | 包含缓存 |
| 启动时间 | < 5 秒 | 从启动到首次显示 |
| 缓存命中率 | > 90% | 大部分请求使用缓存 |

## 🔐 安全考虑

1. **API Token 管理** - 如果后端需要认证，从环境变量读取
2. **HTTPS 支持** - 生产环境使用 HTTPS 连接后端
3. **输入验证** - 验证 API 返回的数据格式
4. **错误信息** - 不在日志中暴露敏感信息

## 📚 参考资源

### 内部参考
- `epaper-with-ai-news/` - 功能参考
- `AI-RSS-Hub/` - 后端 API 文档

### 外部参考
- FastAPI 官方文档
- Waveshare 墨水屏文档
- systemd 服务管理

## 📌 下一步行动

1. **等待 AI-RSS-Hub API 文档** - 确认 API 接口规范
2. **实现 Phase 1** - API 客户端
3. **逐步迭代** - 按优先级实现各模块
4. **持续测试** - 每个阶段完成后进行测试

---

**文档版本**: v1.0
**创建日期**: 2026-01-04
**作者**: Claude Code
**状态**: 待实施
