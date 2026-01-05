# AI-RSS-Client 开发进度报告

**日期**: 2026-01-04
**当前状态**: 🚧 进行中

---

## ✅ 已完成工作

### 1. 文档创建

#### 📄 epaper-with-ai-news 重启文档
- **文件**: `/home/admin/Github/epaper-with-ai-news/docs/RESTART_GUIDE.md`
- **内容**: 完整的服务重启、维护和故障排查指南
- **包含**:
  - 服务重启方法（systemd、手动、直接运行）
  - 日志查看和监控
  - 常见问题排查（GPIO占用、显示不更新、内容获取失败等）
  - 配置修改指南
  - 日常维护命令

#### 📋 AI-RSS-Client 实现规划
- **文件**: `/home/admin/Github/AI-RSS-Client/docs/IMPLEMENTATION_PLAN.md`
- **内容**: 详细的实现方案和技术架构
- **包含**:
  - 系统架构设计（前后端分离）
  - 目录结构规划
  - 6个开发阶段的详细计划
  - 技术实现细节
  - 与 epaper-with-ai-news 的功能对比

### 2. 数据模型实现

#### 📦 Article 模型
- **文件**: `src/models/article.py`
- **功能**:
  - 与 AI-RSS-Hub 后端 API 对应
  - 支持摘要优先显示
  - 阅读状态追踪（NEW/DISPLAYED/FAVORITE）
  - 显示次数统计
  - JSON 序列化/反序列化
  - 数据验证和规范化

**核心特性**:
```python
@dataclass
class Article:
    # Backend fields
    id, feed_id, title, link, content, summary, published_at, created_at

    # Frontend fields
    displayed_at, display_count, is_favorite, status

    # Properties
    display_title, display_content, display_date, is_read, has_content

    # Methods
    mark_as_displayed(), mark_as_favorite(), to_dict(), from_dict()
```

#### 📦 Feed 模型
- **文件**: `src/models/feed.py`
- **功能**:
  - 与 AI-RSS-Hub 后端 API 对应
  - RSS 源信息管理
  - 类别和状态管理
  - JSON 序列化/反序列化

---

## 🚧 待实现模块

### Phase 1: API 客户端 (下一步)
**文件**: `src/fetchers/api_client.py`

**功能**:
- 连接到 AI-RSS-Hub (http://localhost:8000)
- 实现所有 API 端点：
  - GET /api/health - 健康检查
  - GET /api/status - 系统状态
  - GET /api/feeds - 获取 RSS 源列表
  - GET /api/articles - 获取文章列表
  - POST /api/feeds/fetch - 手动触发获取
- 错误处理和重试机制
- 超时控制

**依赖**: ⏸️ 等待 AI-RSS-Hub API 文档

### Phase 2: 缓存系统
**文件**: `src/processors/cache.py`

**功能**:
- SQLite 数据库存储
- JSON 文件备份（离线恢复）
- 多级缓存策略（内存 + 磁盘）
- 缓存过期和清理

### Phase 3: 内容管理器
**文件**: `src/services/content_manager.py`

**功能**:
- 定期从 API 获取新文章
- 本地缓存管理
- 阅读状态追踪
- 未读文章查询
- 离线内容支持

### Phase 4: 显示调度器
**文件**: `src/services/display_scheduler.py`

**功能**:
- 定时刷新墨水屏（默认 1 分钟）
- 智能文章选择（未读优先）
- 随机显示（所有读完时）
- 集成现有渲染系统
- 显示状态追踪

### Phase 5: 服务管理
**文件**: `scripts/display_service.py`

**功能**:
- systemd 服务脚本
- 开机自启配置
- 日志管理
- 状态监控

---

## 📊 当前后台运行状态

### epaper-with-ai-news (正常运行)
```
✅ 显示调度服务: PID 1396 (运行约 2 天)
✅ 内容获取服务: PID 1395
✅ 墨水屏显示: 正常更新（每 1 分钟）
⚠️  内容获取: 有 bug (desc 未定义错误)
```

**注意**: 不对运行中的 epaper-with-ai-news 进行任何修改，仅提供重启文档。

### AI-RSS-Client (开发中)
```
✅ 墨水屏驱动: 已完成
✅ 渲染系统: 已完成
✅ 数据模型: 已完成
🚧 API 客户端: 待实现
🚧 服务层: 待实现
```

---

## 🎯 下一步计划

### 立即行动
1. ⏸️ **等待用户提供 AI-RSS-Hub API 文档**
   - 需要确认 API 端点规范
   - 需要确认数据格式
   - 需要确认认证方式（如果有）

### 后续步骤（获得 API 文档后）
2. 🔨 **实现 API 客户端** (1-2 小时)
   - 创建 `src/fetchers/api_client.py`
   - 实现所有 API 端点
   - 添加错误处理和重试
   - 编写单元测试

3. 🗄️ **实现缓存系统** (2-3 小时)
   - 创建 `src/processors/cache.py`
   - 设计数据库 schema
   - 实现缓存操作
   - 添加离线备份

4. 📦 **实现内容管理器** (2-3 小时)
   - 创建 `src/services/content_manager.py`
   - 集成 API 和缓存
   - 实现定期获取逻辑
   - 添加阅读状态管理

5. 🖥️ **实现显示调度器** (2-3 小时)
   - 创建 `src/services/display_scheduler.py`
   - 集成现有渲染系统
   - 实现调度逻辑
   - 添加状态追踪

6. 🚀 **服务化部署** (1-2 小时)
   - 创建 systemd 服务文件
   - 编写安装脚本
   - 测试开机自启
   - 编写运维文档

---

## 💡 技术亮点

### 已实现的设计优点

1. **数据模型设计**
   - ✅ 清晰的前后端字段分离
   - ✅ 完整的数据验证
   - ✅ 灵活的序列化支持
   - ✅ 丰富的辅助方法

2. **状态管理**
   - ✅ 文章状态枚举（NEW/DISPLAYED/FAVORITE）
   - ✅ 显示次数追踪
   - ✅ 收藏功能预留

3. **显示优化**
   - ✅ 摘要优先显示（AI 生成 > 完整内容）
   - ✅ 自动文本截断
   - ✅ 多种日期格式支持

### 架构优势

1. **前后端分离** - 清晰的职责划分
2. **模块化设计** - 易于维护和测试
3. **可扩展性** - 预留扩展接口
4. **离线支持** - 多级缓存策略

---

## 📚 参考文档

### 项目文档
- AI-RSS-Client 实现方案: `docs/IMPLEMENTATION_PLAN.md`
- epaper-with-ai-news 重启指南: `/home/admin/Github/epaper-with-ai-news/docs/RESTART_GUIDE.md`
- AI-RSS-Client 开发指南: `DEVELOPMENT_GUIDE.md`

### 代码参考
- epaper-with-ai-news: `/home/admin/Github/epaper-with-ai-news/`
- 功能参考：内容管理、显示调度、缓存系统

---

## 🔧 开发环境

### 当前环境
- **Python**: 3.x
- **硬件**: Waveshare 3.52英寸墨水屏 (240×360)
- **OS**: Linux (Raspberry Pi)
- **后端**: AI-RSS-Hub (待启动)

### 依赖库
```
PyYAML>=6.0
Pillow>=9.0.0
requests>=2.28.0
spidev>=3.5
gpiozero>=2.0.0
```

---

## 📞 联系和协作

### 当前阻塞
- ⏸️ 等待 AI-RSS-Hub API 使用文档

### 需要确认
- 🔲 API 认证方式（是否需要 X-API-Token）
- 🔲 CORS 配置（前端访问后端的域名）
- 🔲 数据格式确认（特别是 Article.summary 字段）
- 🔲 API 速率限制（用于控制请求频率）

---

**最后更新**: 2026-01-04
**下次更新**: 收到 AI-RSS-Hub API 文档后
**当前进度**: 15% (数据模型完成)
