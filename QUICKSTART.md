# AI-RSS-Client Quick Start Guide

> 快速开始使用 AI-RSS-Client 墨水屏RSS阅读器

## 📋 前置要求

### 1. 硬件要求
- 树莓派 (Raspberry Pi 3B+ 或更高)
- Waveshare 3.52英寸墨水屏 (240×360)
- 5V 2A 电源适配器

### 2. 软件要求
- Python 3.7+
- AI-RSS-Hub 后端服务（必须先启动）

---

## 🚀 快速安装

### 方式1: 自动安装（推荐）

```bash
cd /home/admin/Github/AI-RSS-Client
./install.sh
```

安装脚本会自动：
- ✅ 安装Python依赖
- ✅ 创建数据目录
- ✅ 测试API连接
- ✅ 配置systemd服务（可选）
- ✅ 启动服务（可选）

### 方式2: 手动安装

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 创建数据目录
mkdir -p data logs

# 3. 测试API连接
python3 main.py test-api
```

---

## 🧪 测试系统

### 1. 测试API连接

```bash
python3 main.py test-api
```

期望输出：
```
Testing API connection...
✓ Health check: ok
✓ System status: running
✓ Fetched 5 articles
✓ Latest: [文章标题]

✓ API connection test PASSED
```

### 2. 获取内容

```bash
python3 main.py fetch
```

期望输出：
```
Fetching content from API...
✓ Content fetched successfully
  - Total summaries: 50
  - Undisplayed: 50
  - API connected: True
```

### 3. 查看状态

```bash
python3 main.py status
```

期望输出：
```
AI-RSS-Client Status
==================================================

[API Connection]
✓ API: Connected
  Status: running

[Cache]
  Total articles: 50
  Undisplayed: 50
  With summary: 45

[Content Manager]
  Last fetch: 2026-01-04T10:30:00
  Last count: 50
```

---

## 🖥️ 运行显示

### 测试显示（单次）

```bash
python3 main.py test-display
```

这会显示一个测试文章，验证墨水屏硬件工作正常。

### 运行显示调度器（生产模式）

```bash
# 运行5个显示周期（用于测试）
python3 main.py run --cycles 5

# 无限运行（生产环境）
python3 main.py run
```

显示调度器会：
- ✅ 每1分钟更新一次显示
- ✅ 优先显示未读文章
- ✅ 所有文章读完时随机显示
- ✅ 自动标记已读

### 自定义显示间隔

```bash
# 每2分钟更新一次
python3 main.py run --interval 2

# 每30秒更新一次（测试用）
python3 main.py run --interval 0.5
```

---

## 🔄 使用systemd服务（推荐）

### 启动服务

```bash
sudo systemctl start ai-rss-client
```

### 停止服务

```bash
sudo systemctl stop ai-rss-client
```

### 重启服务

```bash
sudo systemctl restart ai-rss-client
```

### 查看服务状态

```bash
sudo systemctl status ai-rss-client
```

### 查看实时日志

```bash
sudo journalctl -u ai-rss-client -f
```

### 开机自启

```bash
sudo systemctl enable ai-rss-client
```

### 禁用自启

```bash
sudo systemctl disable ai-rss-client
```

---

## 📊 日常维护

### 查看系统状态

```bash
python3 main.py status
```

### 手动刷新内容

```bash
python3 main.py fetch
```

### 清除缓存

```bash
rm -f data/articles.db data/offline_cache.json
```

### 查看日志

```bash
tail -f logs/*.log
```

### 更新代码

```bash
git pull origin main
pip3 install -r requirements.txt
sudo systemctl restart ai-rss-client
```

---

## 🔧 配置

### 配置文件

主配置文件：`config.yml`

```yaml
# API配置
api:
  base_url: "http://localhost:8000"
  timeout: 10
  retry_attempts: 3

# 显示配置
display_scheduler:
  interval_minutes: 1        # 显示刷新间隔
  random_on_empty: true      # 无未读时随机显示
  mark_as_read_after_display: true

# 缓存配置
cache:
  max_articles: 500          # 最大缓存文章数
  retention_days: 30         # 保留天数
```

### 环境变量

创建 `.env` 文件：

```bash
# API Token（如果后端需要认证）
AI_RSS_API_TOKEN="your_token_here"

# 自定义API URL
AI_RSS_API_URL="http://localhost:8000"
```

---

## 🐛 故障排查

### 问题1: API连接失败

```bash
# 检查AI-RSS-Hub是否运行
curl http://localhost:8000/api/health

# 查看后端日志
cd ../AI-RSS-Hub
# 查看后端日志输出
```

**解决方案**：确保AI-RSS-Hub后端正在运行

### 问题2: 墨水屏不显示

```bash
# 检查GPIO占用
sudo lsof /dev/gpiochip*

# 停止占用GPIO的服务
sudo systemctl stop ai-news-display-scheduler.service

# 重新运行
python3 main.py test-display
```

**解决方案**：确保没有其他服务占用GPIO

### 问题3: 内容无法获取

```bash
# 检查网络连接
ping -c 3 google.com

# 测试API
curl http://localhost:8000/api/articles?limit=10

# 查看详细日志
python3 main.py fetch --debug
```

**解决方案**：
- 检查网络连接
- 检查API端点配置
- 查看日志获取详细错误信息

### 问题4: 服务无法启动

```bash
# 查看详细错误
sudo journalctl -u ai-rss-client -n 50

# 手动运行测试
python3 main.py run --cycles 1
```

**解决方案**：
- 检查Python路径
- 检查依赖是否完整安装
- 查看日志获取详细错误

---

## 📈 性能优化

### 1. 调整获取频率

编辑 `config.yml`：

```yaml
services:
  content_fetch:
    interval_minutes: 30  # 增加到30分钟
```

### 2. 调整显示间隔

```bash
python3 main.py run --interval 2  # 每2分钟更新
```

### 3. 限制缓存大小

```yaml
cache:
  max_articles: 300  # 减少缓存数量
```

---

## 🔄 从 epaper-with-ai-news 迁移

如果你之前使用 `epaper-with-ai-news` 项目：

### 1. 停止旧服务

```bash
sudo systemctl stop ai-news-display-scheduler.service
sudo systemctl disable ai-news-display-scheduler.service
```

### 2. 启动新服务

```bash
sudo systemctl start ai-rss-client
```

### 3. 对比

| 特性 | epaper-with-ai-news | AI-RSS-Client |
|------|---------------------|---------------|
| 架构 | 单体应用 | 前后端分离 |
| RSS获取 | 内置 | 后端API |
| AI摘要 | 内置 | 后端API |
| 硬件驱动 | 相同 | 相同 |

---

## 📚 更多信息

- 完整文档：`docs/IMPLEMENTATION_PLAN.md`
- API文档：`docs/API_GUIDE.md`
- 开发指南：`DEVELOPMENT_GUIDE.md`
- 故障排查：`TROUBLESHOOTING_QUICK_REF.md`

---

## 💡 使用技巧

### 1. 定期检查状态

```bash
watch -n 10 "python3 main.py status"
```

### 2. 创建快捷别名

编辑 `~/.bashrc`：

```bash
alias ai-status='cd ~/Github/AI-RSS-Client && python3 main.py status'
alias ai-fetch='cd ~/Github/AI-RSS-Client && python3 main.py fetch'
alias ai-run='cd ~/Github/AI-RSS-Client && python3 main.py run'
```

### 3. 定时任务（cron）

```bash
# 每小时获取一次内容
0 * * * * cd ~/Github/AI-RSS-Client && python3 main.py fetch
```

---

**最后更新**: 2026-01-04
**项目版本**: v1.0.0
