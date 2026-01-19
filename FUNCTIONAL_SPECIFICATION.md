# AI-RSS-Client 功能说明书

## 📋 项目概述

**AI-RSS-Client** 是一个基于树莓派的墨水屏RSS阅读器前端系统，作为 **AI-RSS-PROJECT** 单体仓库的一部分，与 **AI-RSS-Hub** 后端API配合工作。

### 核心特性
- 📱 **硬件支持**：Waveshare 3.52英寸电子墨水屏（240×360像素）
- 🤖 **AI增强**：支持AI生成的中英文摘要
- 🔄 **双服务架构**：内容获取与显示完全分离
- 💾 **本地缓存**：SQLite数据库 + JSON离线备份
- 🎨 **智能排版**：中英文混排自动换行与布局优化
- 🌤️ **天气显示**：实时天气信息集成
- 📡 **网络API**：与AI-RSS-Hub后端通信

### 技术栈
- **语言**：Python 3.11+
- **硬件**：树莓派 + Waveshare 3.52" E-Paper
- **数据库**：SQLite3
- **HTTP客户端**：requests
- **图像处理**：Pillow (PIL)
- **服务管理**：systemd
- **代码量**：约4300行Python代码

---

## 🏗️ 系统架构

### 双服务架构

项目采用**双服务架构**，将内容获取和显示逻辑完全分离：

```
┌─────────────────────────────────────┐
│         AI-RSS-Client               │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐  │
│  │  ContentFetchService         │  │
│  │  (内容获取服务)               │  │
│  │  - 每20分钟获取新文章         │  │
│  │  - 独立进程运行               │  │
│  │  - 支持优雅关闭               │  │
│  └──────────────────────────────┘  │
│              ↓                       │
│        ┌──────────┐                 │
│        │   缓存   │ ← SQLite + JSON │
│        │ (共享)   │                 │
│        └──────────┘                 │
│              ↑                       │
│  ┌──────────────────────────────┐  │
│  │  DisplayService              │  │
│  │  (显示服务)                   │  │
│  │  - 每30秒更新显示             │  │
│  │  - 独立进程运行               │  │
│  │  - 负责墨水屏渲染             │  │
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
         ↓                 ↓
    ┌────────┐        ┌─────────┐
    │ API    │        │ E-Paper │
    │ Server │        │ Display │
    └────────┘        └─────────┘
```

### 架构优势

✅ **独立运行**：内容获取和显示完全独立，互不影响
✅ **故障隔离**：一个服务崩溃不影响另一个
✅ **灵活管理**：可单独重启、监控和调试
✅ **资源优化**：显示服务无需等待网络请求
✅ **离线支持**：显示服务可在无网络时继续运行

---

## 📁 模块详解

### 1️⃣ 数据模型层 (src/models/)

#### Article (src/models/article.py)

**文章数据模型**，对应后端API的文章对象。

**字段**：
- **后端字段**（来自API）：
  - `id`：文章唯一ID
  - `feed_id`：RSS源ID
  - `title`：文章标题
  - `link`：原文链接
  - `content`：完整内容（可选）
  - `summary`：AI生成的中文摘要
  - `summary_en`：AI生成的英文摘要
  - `published_at`：发布时间
  - `created_at`：创建时间

- **前端字段**（本地维护）：
  - `displayed_at`：最后显示时间
  - `display_count`：显示次数
  - `is_favorite`：是否收藏
  - `status`：显示状态（new/displayed/favorite）

**核心方法**：
- `display_title`：获取显示用标题（超长截断）
- `display_content`：获取显示用内容（优先摘要）
- `display_content_en`：获取英文内容
- `display_date`：格式化日期
- `to_dict()` / `from_dict()`：序列化支持
- `from_api_response()`：从API响应创建对象

**数据验证**：
- 自动验证和清理空标题、链接
- 解析和验证时间戳格式
- 提供默认值处理

#### Feed (src/models/feed.py)

**RSS源数据模型**。

**字段**：
- `id`：RSS源唯一ID
- `name`：源名称
- `url`：RSS订阅URL
- `category`：分类（如 tech, news）
- `is_active`：是否活跃
- `created_at`：创建时间

**核心方法**：
- `display_name`：获取显示名称
- `display_category`：格式化分类显示
- `to_dict()` / `from_dict()`：序列化支持

---

### 2️⃣ API客户端层 (src/fetchers/)

#### AIRSSHubClient (src/fetchers/api_client.py)

**AI-RSS-Hub API客户端**，处理与后端的所有HTTP通信。

**核心功能**：

**1. 连接管理**
- 连接池复用（requests.Session）
- 自动重试机制（默认3次）
- 指数退避策略
- 请求超时控制（默认30秒）

**2. API端点**
```python
# 健康检查
health_check() -> Dict

# 系统状态
get_status() -> Dict

# RSS源管理
get_feeds(active_only=False) -> List[Feed]
add_feed(name, url, category, is_active) -> Feed

# 文章获取（支持多种过滤条件）
get_articles(limit, category, days, start_date, end_date,
            after, before, since, feed_id) -> List[Article]

# 手动触发获取
trigger_fetch() -> Dict
```

**3. 错误处理**
- 自定义 `APIError` 异常
- HTTP状态码处理（401/403/429等）
- 超时和连接错误重试
- 速率限制自动等待

**4. 认证支持**
- 可选的API Token认证
- `X-API-Token` 头部自动添加

**使用示例**：
```python
# 创建客户端
client = AIRSSHubClient(base_url="http://8.134.202.27:8000")

# 获取最近3天的文章（最多200篇）
articles = client.get_articles(days=3, limit=200)

# 按分类获取
tech_articles = client.get_articles(category="tech", limit=50)

# 增量获取
latest = cache.get_latest_article()
new_articles = client.get_articles(after=latest.published_at)
```

---

### 3️⃣ 缓存层 (src/processors/)

#### ArticleCache (src/processors/cache.py)

**文章缓存管理器**，提供SQLite数据库存储和JSON离线备份。

**存储架构**：
```
SQLite Database (data/articles.db)
├── articles 表
│   ├── 后端字段
│   └── 前端字段（displayed_at, display_count等）
└── feeds 表

JSON Backup (data/offline_cache.json)
└── 完整缓存快照（用于离线恢复）
```

**核心功能**：

**1. 文章存储**
```python
add_articles(articles: List[Article]) -> int
```
- 批量添加文章
- 自动去重（基于ID）
- 自动触发缓存清理
- 更新JSON备份

**2. 文章查询**
```python
# 按显示时间查询（实现轮询）
get_articles_by_display_time(limit=50, days=3) -> List[Article]

# 未显示文章
get_undisplayed_articles(limit=50) -> List[Article]

# 最近文章
get_recent_articles(limit=50, days=3) -> List[Article]

# 最旧未显示
get_random_article() -> Article

# 最新的单篇文章
get_latest_article() -> Article
```

**3. 显示时间管理（轮询机制）**
```python
mark_as_displayed(article_id) -> bool
```
- 更新 `displayed_at` 为当前时间
- 递增 `display_count`
- **保留status为"new"**（支持循环播放）
- 更新JSON备份

**4. 统计信息**
```python
get_stats() -> Dict
{
    'total_articles': 1154,
    'undisplayed_count': 500,
    'displayed_count': 654,
    'favorite_count': 10,
    'with_summary_count': 1100,
    'latest_published': '2026-01-19T01:09:38'
}
```

**5. 缓存管理**
- 自动清理：当缓存超过 `max_articles` 时，删除旧文章
- JSON备份：每次更新后自动备份
- 离线恢复：`restore_from_backup()` 从JSON恢复

**轮询算法**：
```sql
ORDER BY
    CASE WHEN displayed_at IS NULL THEN 0 ELSE 1 END,
    displayed_at ASC,
    published_at DESC
```
- 优先显示从未显示的文章（displayed_at IS NULL）
- 按显示时间升序（最久未显示的优先）
- 相同时间按发布时间降序（最新的优先）

---

### 4️⃣ 服务层 (src/services/)

#### ContentManager (src/services/content_manager.py)

**内容管理器**，协调API客户端和缓存，提供高层次的内容操作。

**职责**：
- 从API获取文章
- 管理本地缓存
- 选择文章用于显示
- 追踪读取状态

**核心方法**：

**1. 内容获取**
```python
fetch_and_process_content(
    category=None, days=3, start_date=None,
    end_date=None, incremental=False, feed_id=None
) -> bool
```
- 支持多种获取策略：
  - **日期范围**：获取指定日期范围的文章
  - **天数**：获取最近N天的文章
  - **增量**：只获取比最新缓存文章更新的内容
  - **RSS源**：获取特定RSS源的文章
- 自动去重添加到缓存
- 返回成功状态

**2. 文章选择（真正的循环播放）**
```python
get_article_for_display() -> Article
```

三级选择策略：
1. **优先级1**：获取最近N天内最久未显示的文章
   - 按displayed_at ASC排序
   - 实现真正的轮询

2. **优先级2**：随机选择一篇从未显示的文章
   - status='new'的文章

3. **优先级3**：完全随机选择任意文章
   - 兜底方案

**3. 状态管理**
```python
should_fetch() -> bool
```
- 检查是否到达下次获取时间
- 基于 `fetch_interval_minutes` 配置

**4. 其他功能**
```python
mark_as_displayed(article_id) -> bool
trigger_backend_fetch() -> bool
fetch_by_feed(feed_id) -> bool
fetch_by_date_range(start, end) -> bool
fetch_incremental() -> bool
```

---

#### DisplayScheduler (src/services/display_scheduler.py)

**显示调度器**，管理墨水屏的周期性更新。

**职责**：
- 从ContentManager获取文章
- 调用渲染器生成图像
- 驱动墨水屏硬件更新
- 追踪显示状态

**核心方法**：

**1. 显示更新**
```python
update_display(save_debug=False) -> bool
```
流程：
1. 从ContentManager获取文章
2. 调用ContentRenderer渲染图像
3. 通过EpaperDriver显示到墨水屏
4. 标记文章为已显示
5. 保存调试图像（可选）

**2. 守护进程**
```python
run_daemon(cycles=None)
```
- 无限循环或指定次数
- 每30秒执行一次更新
- 计算并等待合适的睡眠时间
- 处理KeyboardInterrupt优雅退出

**3. 测试模式**
```python
test_display()
```
- 运行一次测试显示
- 用于硬件验证

**4. IP地址检测**
```python
_get_local_ip() -> Optional[str]
```
- 优先获取无线网卡IP（wlan0）
- 回退到第一个非本地环回IP
- 用于底部显示

---

#### ContentFetchService (src/services/content_fetch_service.py) ⭐新增

**内容获取服务**，独立的守护进程，定期从API获取新内容。

**架构设计**：
```python
ContentFetchService
├── __init__(config, base_url, api_token)
│   └── 创建ContentManager
├── fetch_once() -> bool
│   └── 执行一次内容获取
├── run_daemon(cycles=None)
│   ├── 启动时执行一次获取
│   ├── while not shutdown:
│   │   ├── 等待interval_minutes分钟
│   │   └── 执行fetch_once()
│   └── 优雅关闭
└── stop() / close()
```

**核心功能**：

**1. 定时获取**
- 默认每20分钟获取一次
- 可配置 `interval_minutes`
- 支持 `cycles` 限制获取次数

**2. 获取策略**
根据配置自动选择：
- **增量模式**（`incremental_fetch=true`）：
  - 只获取新文章
  - 节省带宽和处理时间

- **指定RSS源**（`fetch_feed_ids`）：
  - 获取特定源的文章
  - 支持多源批量获取

- **默认模式**（`fetch_days=3`）：
  - 获取最近N天的文章

**3. 信号处理**
- 注册SIGTERM和SIGINT处理器
- 收到信号时优雅关闭
- 完成当前获取后退出

**4. 可中断睡眠**
```python
_interruptible_sleep(seconds)
```
- 每秒检查关闭信号
- 支持快速响应关闭请求

**使用示例**：
```python
# 命令行启动
python3 main.py fetch-daemon --base-url http://8.134.202.27:8000

# 程序化使用
service = ContentFetchService(config)
service.run_daemon()
```

---

#### DisplayService (src/services/display_service.py) ⭐新增

**显示服务**，独立的守护进程，定期更新墨水屏显示。

**架构设计**：
```python
DisplayService
├── __init__(config, base_url, display_interval_minutes)
│   ├── 创建ContentManager
│   └── 创建DisplayScheduler
├── run_daemon(cycles=None)
│   ├── 初始化显示硬件
│   ├── while not shutdown:
│   │   ├── scheduler.update_display()
│   │   └── 等待display_interval_minutes分钟
│   └── 清理资源
├── run_test_display() -> bool
│   └── 测试硬件显示
└── stop() / close()
```

**核心功能**：

**1. 定时显示**
- 默认每30秒更新一次
- 可配置 `display_interval_minutes`
- 支持 `cycles` 限制显示次数

**2. 硬件管理**
- 自动初始化墨水屏驱动
- 无头模式：硬件失败时继续运行（不更新显示）
- 退出时自动睡眠硬件

**3. 信号处理**
- 支持SIGTERM和SIGINT
- 优雅关闭显示硬件
- 保存调试图像

**4. 状态查询**
```python
get_status() -> Dict
{
    'service': 'display',
    'running': True,
    'display_cycles': 12345,
    'last_display_time': '2026-01-19T10:00:00',
    'current_article': {'id': 1234, 'title': '...'},
    'hardware_initialized': True
}
```

**使用示例**：
```python
# 命令行启动
python3 main.py run --base-url http://8.134.202.27:8000
# 或
python3 main.py display-daemon --base-url http://8.134.202.27:8000

# 自定义显示间隔
python3 main.py run --interval 1.0  # 每1分钟更新
```

---

### 5️⃣ 显示层 (src/display/)

#### EpaperDriver (src/display/epaper_driver.py)

**墨水屏驱动封装**，抽象硬件操作。

**硬件支持**：
- Waveshare 3.52英寸 E-Paper (240×360)
- 控制芯片：支持局部刷新和全局刷新
- 接口：SPI (GPIO)

**核心功能**：

**1. 自动模式切换**
```python
_load_hardware_driver()
```
- 尝试加载硬件驱动（`lib/waveshare_epd/epd3in52.py`）
- 失败时自动切换到Mock模式
- Mock模式：仅生成调试图像，不操作硬件

**2. 硬件初始化**
```python
init_display()
```
- 初始化SPI和GPIO
- 清屏并设置唤醒序列
- 完整刷新（清除历史）

**3. 显示方法**
```python
display(image, save_debug=False)
```
- 支持全局刷新和局部刷新
- 自动选择刷新模式
- 保存调试图像（可选）

**4. 硬件清理**
```python
sleep()
clear()
close()
```
- 墨水屏进入低功耗模式
- 清空屏幕内容
- 释放GPIO资源

**错误处理**：
- 硬件冲突检测（SPI设备占用）
- 自动切换到Mock模式
- 详细的错误日志

---

#### ContentRenderer (src/display/renderer.py)

**内容渲染器**，将文章数据转换为墨水屏图像。

**渲染布局**（双语模式）：
```
┌─────────────────────────┐
│ Header (35px)           │ ← 黑底白字标题栏
│ "AI-NEWS" | 天气  | IP  │
├─────────────────────────┤
│ Title                   │ ← 文章标题
│ （最多3行，18pt）       │
├─────────────────────────┤
│ 中文摘要                │ ← 主要内容
│ （最多8行，15pt）       │
│                         │
├─────────────────────────┤
│ 英文摘要                │ ← 学习区域
│ （最多2行，12pt）       │
├─────────────────────────┤
│ Footer (20px)           │ ← 元数据
│ 来源 | 日期 | 文章#     │
└─────────────────────────┘
```

**核心功能**：

**1. 主渲染方法**
```python
render_news_card(article, index, total, ip_address, bilingual=True)
```
- 生成完整的新闻卡片
- 支持双语显示（中英文）
- 集成天气信息
- 显示IP地址

**2. 天气集成**
```python
_update_weather()
```
- 从wttr.in获取天气
- 缓存10分钟
- 超时保护（5秒）
- 格式：`20°C, Sunny`

**3. 布局计算**
- 自动分配各区域高度
- 动态调整字号和行距
- 响应式布局

**4. 文本处理**
- 自动截断超长文本
- 保留关键词信息
- 中英文混排优化

**渲染特性**：
- 黑白两色优化（墨水屏特性）
- 高对比度设计
- 清晰的层次结构
- 信息密度最大化

---

#### LayoutEngine (src/display/layout_engine.py)

**排版引擎**，处理文本布局、自动换行、截断等。

**核心功能**：

**1. 智能自动换行**
```python
wrap_text(text, font, max_width) -> List[str]
```
- 中英文混排支持
- 中文：每个字符独立
- 英文：单词为单位，避免在单词中间断开
- 空格处理：作为分隔符

**算法**：
```
遍历字符:
  if 中文字符:
    尝试添加到当前行
    如果超宽: 换行
  elif 英文字符:
    累积成单词
    遇到空格: 尝试添加整个单词
    如果超宽: 换行后添加
```

**2. 文本截断**
```python
truncate_text(text, font, max_width, max_lines, add_ellipsis=True)
```
- 先换行
- 保留前N行
- 最后一行添加省略号（...）
- 确保省略号不超宽

**3. 高度计算**
```python
calculate_text_height(text, font, max_width) -> int
```
- 计算文本块总高度
- 行数 × 行高 × 行距
- 用于动态布局

**4. 居中对齐**
```python
center_text(text, font, container_width, container_height) -> (x, y)
```
- 计算文本块尺寸
- 居中坐标
- 支持最大宽度限制

**5. 区域适配**
```python
fit_text_in_area(text, font, area_width, area_height) -> str
```
- 自动截断以适应区域
- 计算最大行数
- 返回适配后的文本

**中英文判断**：
```python
_is_cjk(char) -> bool
```
- CJK统一表意文字（0x4E00-0x9FFF）
- CJK扩展A（0x3400-0x4DBF）
- CJK扩展B-F（0x20000-0x2EBEF）
- 全角标点（0xFF00-0xFFEF）

**PIL版本兼容**：
```python
_get_text_width(text, font)
_get_font_height(font)
```
- 新版PIL（>=10.0.0）：使用 `getlength()` 和 `getbbox()`
- 旧版PIL：使用 `getsize()`
- 自动检测和回退

---

#### FontManager (src/display/fonts.py)

**字体管理器**，统一管理字体资源。

**核心功能**：

**1. 字体加载**
```python
get_font(size: int) -> ImageFont.FreeTypeFont
```
- 主字体：优先使用
- 回退字体：主字体失败时使用
- 字体缓存：避免重复加载

**2. 字体验证**
```python
_validate_fonts()
```
- 检查字体文件是否存在
- 记录警告日志
- 自动切换到回退字体

**3. 字体缓存**
```python
{(font_path, size): font_object}
```
- 键：字体路径和大小
- 值：加载后的字体对象
- 性能优化

**4. 回退机制**
```
尝试主字体
  ↓ 失败
记录警告
  ↓
使用回退字体
```

**默认配置**：
```yaml
font_file: "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
font_file_fallback: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
```

**支持字号**：
- 标题：18pt
- 正文（中文）：15pt
- 正文（英文）：12pt
- 元数据：12pt

---

### 6️⃣ 配置层 (src/config.py)

#### Config (src/config.py)

**配置管理器**，基于YAML的配置系统。

**配置结构**：
```yaml
# API配置
api:
  base_url: "http://8.134.202.27:8000"
  timeout: 10
  retry_attempts: 3
  api_token: null

# 显示配置
display:
  width: 240
  height: 360
  font_file: "...wqy-microhei.ttc"
  font_size_title: 18
  font_size_summary: 15
  margin: 6
  title_height: 35
  footer_height: 20

# 内容获取服务配置
services:
  enabled: true
  interval_minutes: 20
  max_articles_per_fetch: 200
  fetch_days: 3
  max_cached_articles: 1000
  incremental_fetch: false
  fetch_feed_ids: []

# 显示调度服务配置
display_scheduler:
  enabled: true
  interval_minutes: 0.5  # 30秒
  display_days: 3
  mark_as_read_after_display: false

# 日志配置
logging:
  level: "INFO"
  logfile: "data/logs/service.log"
  max_log_size: 10485760  # 10MB

# 网络配置
network:
  timeout_seconds: 10
  retries: 3
  retry_delay: 5
```

**核心功能**：

**1. 配置加载**
```python
config = Config(config_path="config.yml")
```
- YAML格式配置文件
- 类型安全（dataclass）
- 自动验证必需字段

**2. 配置验证**
```python
_validate(data: Dict)
```
- 检查必需的配置节
- 友好的错误提示
- 启动时验证

**3. 访问配置**
```python
config.display.width
config.services.interval_minutes
config.display_scheduler.display_days
```

**4. 日志设置**
```python
setup_logging(config: Config)
```
- 文件日志（带轮转）
- 控制台日志
- 可配置日志级别

---

### 7️⃣ 主入口 (main.py)

**命令行接口**，项目的启动入口。

**可用命令**：

```bash
# 测试API连接
python3 main.py test-api --base-url http://8.134.202.27:8000

# 手动获取一次内容
python3 main.py fetch --base-url http://8.134.202.27:8000

# 启动内容获取服务（守护进程）
python3 main.py fetch-daemon --base-url http://8.134.202.27:8000

# 启动显示服务（守护进程）
python3 main.py run --base-url http://8.134.202.27:8000
# 或
python3 main.py display-daemon --base-url http://8.134.202.27:8000

# 显示系统状态
python3 main.py status --base-url http://8.134.202.27:8000

# 测试显示硬件
python3 main.py test-display --base-url http://8.134.202.27:8000
```

**命令行参数**：

```bash
--base-url URL        # API服务器地址
--api-token TOKEN     # API认证令牌
--interval MINUTES    # 显示间隔（分钟）
--cycles N            # 运行次数（默认无限）
--limit N             # 获取文章数量
--debug               # 启用调试日志
```

**使用示例**：

```bash
# 运行5次测试
python3 main.py run --cycles 5 --base-url http://8.134.202.27:8000

# 自定义显示间隔为1分钟
python3 main.py run --interval 1.0 --base-url http://8.134.202.27:8000

# 获取100篇文章
python3 main.py fetch --limit 100 --base-url http://8.134.202.27:8000
```

---

## 🔄 完整工作流程

### 启动流程

**1. 内容获取服务启动**
```
ContentFetchService.__init__()
  ↓
加载配置 (config.yml)
  ↓
创建API客户端 (AIRSSHubClient)
  ↓
创建内容管理器 (ContentManager)
  ↓
run_daemon()
  ↓
执行初始获取: fetch_once()
  ├─ should_fetch()? → Yes
  ├─ fetch_and_process_content(days=3)
  ├─ 从API获取200篇文章
  ├─ 添加到SQLite缓存
  └─ 更新JSON备份
  ↓
等待 20 分钟
  ↓
循环: fetch_once()
```

**2. 显示服务启动**
```
DisplayService.__init__()
  ↓
加载配置 (config.yml)
  ↓
创建API客户端
  ↓
创建内容管理器 (ContentManager)
  ↓
创建显示调度器 (DisplayScheduler)
  ↓
run_daemon()
  ↓
初始化墨水屏硬件
  ├─ 加载驱动: lib/waveshare_epd/epd3in52.py
  ├─ 初始化SPI和GPIO
  └─ 清屏并唤醒
  ↓
初始化渲染器
  ├─ 加载字体 (FontManager)
  ├─ 创建排版引擎 (LayoutEngine)
  └─ 获取天气信息
  ↓
循环: update_display()
  ├─ 从ContentManager获取文章
  ├─ 调用ContentRenderer渲染图像
  ├─ 通过EpaperDriver显示到墨水屏
  ├─ 标记为已显示
  └─ 等待 30 秒
```

### 运行时交互

```
ContentFetchService         DisplayService
      │                           │
      │ fetch_once()             │ update_display()
      │                           │
      ├─ API.get_articles() ──────┼─ ContentManager.get_article_for_display()
      │   │                       │   │
      │   └─> [200篇文章]         │   ├─> Cache.get_articles_by_display_time()
      │                           │   │   │
      ├─> Cache.add_articles() ───┼──┴──> [SELECT ... ORDER BY displayed_at ASC]
      │   │                       │
      │   └─> 存储到SQLite         │   <article>
      │                           │   │
      └─> 等待20分钟              ├─> Renderer.render_news_card()
                                  │   │
                                  ├─> 生成240×360图像
                                  │   │
                                  └─> Driver.display()
                                      │
                                      └─> 墨水屏更新
                                          │
                                          └─> 等待30秒
```

---

## 📊 数据流图

### 内容获取流程
```
AI-RSS-Hub API
    ↓
AIRSSHubClient.get_articles(days=3, limit=200)
    ↓
[Article对象列表]
    ↓
ContentManager.fetch_and_process_content()
    ↓
ArticleCache.add_articles()
    ├─ 插入SQLite (去重)
    ├─ 自动清理旧文章
    └─ 更新JSON备份
    ↓
本地缓存
├── data/articles.db (SQLite)
└── data/offline_cache.json (JSON)
```

### 显示更新流程
```
DisplayService (每30秒)
    ↓
ContentManager.get_article_for_display()
    ↓
ArticleCache.get_articles_by_display_time()
    ├─ SQL查询 (ORDER BY displayed_at ASC)
    └─ 返回[最久未显示的文章]
    ↓
DisplayScheduler.update_display()
    ├─ ContentRenderer.render_news_card()
    │   ├─ FontManager.get_font()
    │   ├─ LayoutEngine.wrap_text()
    │   ├─ 绘制标题、摘要、天气、IP
    │   └─ 返回PIL Image
    │
    ├─ EpaperDriver.display()
    │   ├─ 转换为位图
    │   ├─ 初始化墨水屏
    │   └─ 发送到硬件
    │
    ├─ ArticleCache.mark_as_displayed()
    │   └─ 更新displayed_at和display_count
    │
    └─ 保存调试图像 (data/debug_current_view.png)
```

---

## 🛠️ 配置说明

### 关键配置项

**内容获取频率** (`services.interval_minutes`)
- **默认值**：20分钟
- **作用**：ContentFetchService获取新内容的间隔
- **建议**：10-60分钟，根据新闻源更新频率调整

**显示更新频率** (`display_scheduler.interval_minutes`)
- **默认值**：0.5分钟（30秒）
- **作用**：DisplayService切换文章的间隔
- **建议**：0.5-2分钟，过快会增加硬件磨损

**获取天数** (`services.fetch_days`)
- **默认值**：3天
- **作用**：从API获取最近N天的文章
- **建议**：1-7天，根据阅读量和存储容量

**显示天数** (`display_scheduler.display_days`)
- **默认值**：3天
- **作用**：循环播放最近N天的文章
- **建议**：与fetch_days相同或略小

**最大缓存数** (`services.max_cached_articles`)
- **默认值**：1000篇
- **作用**：SQLite数据库最大文章数
- **建议**：500-2000篇，根据磁盘容量

**单次获取数** (`services.max_articles_per_fetch`)
- **默认值**：200篇
- **作用**：每次从API获取的最大文章数
- **建议**：100-500篇，API限制为200篇

### 性能优化建议

**1. 网络优化**
```yaml
services:
  interval_minutes: 30  # 降低获取频率
  max_articles_per_fetch: 200  # 单次批量获取

network:
  timeout_seconds: 10
  retries: 3
  retry_delay: 5
```

**2. 存储优化**
```yaml
services:
  max_cached_articles: 800  # 限制缓存大小
  fetch_days: 2  # 只获取2天内的文章

display_scheduler:
  display_days: 2  # 只显示2天内的文章
```

**3. 显示优化**
```yaml
display_scheduler:
  interval_minutes: 1.0  # 降低刷新频率
  min_display_interval: 60  # 最小间隔60秒
```

---

## 🔧 运维管理

### Systemd服务

**服务文件位置**：
- `/etc/systemd/system/ai-rss-client-fetch.service`
- `/etc/systemd/system/ai-rss-client-display.service`

**常用命令**：
```bash
# 查看状态
sudo systemctl status ai-rss-client-fetch
sudo systemctl status ai-rss-client-display

# 启动/停止/重启
sudo systemctl start/stop/restart ai-rss-client-fetch
sudo systemctl start/stop/restart ai-rss-client-display

# 开机自启
sudo systemctl enable ai-rss-client-fetch
sudo systemctl enable ai-rss-client-display

# 查看日志
sudo journalctl -u ai-rss-client-fetch -f
sudo journalctl -u ai-rss-client-display -f

# 查看最近50条日志
sudo journalctl -u ai-rss-client-fetch -n 50
sudo journalctl -u ai-rss-client-display -n 50
```

### 日志文件

**位置**：`data/logs/service.log`

**日志级别**：
- INFO：正常运行信息
- WARNING：警告（如API超时）
- ERROR：错误（如硬件初始化失败）

**日志轮转**：
- 单文件最大：10MB
- 保留文件数：5个
- 总大小限制：约50MB

### 数据备份

**SQLite数据库**：`data/articles.db`
**JSON备份**：`data/offline_cache.json`

**备份策略**：
- 每次获取后自动更新JSON
- 启动时可从JSON恢复
- 建议定期手动备份整个data目录

**恢复方法**：
```bash
# 从JSON恢复
sqlite3 data/articles.db < backup.sql

# 或使用代码
python3 -c "
from src.processors import ArticleCache
cache = ArticleCache()
cache.restore_from_backup()
"
```

---

## 🐛 故障排查

### 常见问题

**1. 内容获取服务不工作**
- 症状：没有新文章
- 检查：网络连接、API服务器状态
- 日志：`journalctl -u ai-rss-client-fetch -n 50`
- 解决：手动触发 `python3 main.py fetch`

**2. 显示服务不更新**
- 症状：墨水屏内容不变
- 检查：缓存是否有文章、硬件是否初始化
- 日志：`journalctl -u ai-rss-client-display -n 50`
- 解决：测试显示 `python3 main.py test-display`

**3. 墨水屏显示异常**
- 症状：花屏、显示不全
- 原因：SPI冲突、硬件未正确初始化
- 解决：检查GPIO占用、重启服务

**4. 文章重复显示**
- 症状：总是显示同一篇文章
- 原因：缓存过期、display_days配置过小
- 解决：手动获取新文章、增加display_days

**5. 内存不足**
- 症状：系统卡顿、服务崩溃
- 原因：缓存过大、字体缓存过多
- 解决：降低max_cached_articles、重启服务

### 调试模式

**启用调试日志**：
```bash
python3 main.py run --debug --base-url http://8.134.202.27:8000
```

**查看详细错误**：
```bash
sudo journalctl -u ai-rss-client-display -f --no-pager | grep ERROR
```

**手动测试组件**：
```bash
# 测试API
python3 main.py test-api

# 测试显示硬件
python3 main.py test-display

# 查看状态
python3 main.py status
```

---

## 📈 性能指标

### 资源占用

**CPU使用**：
- ContentFetchService：启动时5%，空闲时<1%
- DisplayService：平均2-5%（渲染时）

**内存使用**：
- ContentFetchService：约50-80MB
- DisplayService：约80-120MB
- 总计：<200MB

**磁盘I/O**：
- SQLite写入：每次获取约1-2MB
- JSON备份：每次获取约5-10MB
- 日志文件：每日约1-5MB

### 性能优化

**1. 减少内存占用**
```yaml
services:
  max_cached_articles: 500  # 降低缓存上限
```

**2. 减少磁盘写入**
```python
# 修改代码，降低JSON备份频率
# 每5次获取备份一次，而不是每次
```

**3. 优化网络使用**
```yaml
services:
  incremental_fetch: true  # 启用增量获取
  interval_minutes: 30  # 降低获取频率
```

---

## 🔒 安全性

### API认证

**启用Token认证**：
```yaml
api:
  api_token: "YOUR_TOKEN_HERE"
```

**生成Token**（在AI-RSS-Hub后端）：
```bash
cd AI-RSS-Hub
python scripts/generate_token.py
```

### 网络安全

**建议**：
1. 使用HTTPS连接API服务器
2. 定期更换API Token
3. 限制Token权限（只读）
4. 监控异常访问日志

---

## 📝 附录

### 依赖包列表

```
requests          # HTTP客户端
Pillow            # 图像处理
PyYAML            # 配置文件解析
```

### 硬件要求

**最小配置**：
- Raspberry Pi 3B+
- 512MB RAM
- 4GB SD卡
- Waveshare 3.52" E-Paper

**推荐配置**：
- Raspberry Pi 4B
- 2GB RAM
- 16GB SD卡
- Waveshare 3.52" E-Paper

### 支持的墨水屏型号

- Waveshare 3.52英寸 E-Paper (240×360)
- 其他基于相同驱动芯片的型号

---

## 📚 相关文档

- **架构说明**：`SERVICES_ARCHITECTURE.md`
- **开发指南**：`DEVELOPMENT_GUIDE.md`
- **API指南**：`docs/API_GUIDE.md`
- **测试报告**：`docs/FINAL_TEST_REPORT.md`
- **快速开始**：`QUICKSTART.md`

---

## 🎯 总结

**AI-RSS-Client** 是一个功能完整、架构清晰的墨水屏RSS阅读器系统。通过双服务架构实现了关注点分离，提供稳定的新闻阅读体验。

**核心优势**：
✅ 双服务独立运行，故障隔离
✅ 本地缓存，离线可用
✅ AI增强摘要，中英双语
✅ 智能轮询，避免重复
✅ 灵活配置，易于维护

**适用场景**：
- 个人新闻阅读终端
- 办公室信息展示板
- 学习辅助设备（中英文对照）
- 物联网演示项目

---

**版本**：1.0
**最后更新**：2026-01-19
**代码行数**：~4300行
**文档页数**：本说明书约50页
