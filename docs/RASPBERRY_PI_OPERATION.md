# AI-RSS-Client 树莓派运行说明

**项目位置**: `/home/admin/Github/AI-RSS-Client`
**服务名称**: `ai-rss-client.service`
**运行状态**: 🟢 正常运行

---

## 📊 当前运行状态

### 服务状态
```
状态: ✅ Active (running)
进程ID: 377708
运行时长: 34分钟
内存占用: 50.2 MB
开机自启: ✅ 已启用
```

### 缓存状态
```
总文章数: 186篇
未显示: 186篇（全部为新获取）
时间范围: 2026-01-02 ~ 2026-01-05（4天）
```

### 硬件状态
```
平台: Raspberry Pi (Linux 6.1.0-rpi7-rpi-v8)
Python: Python 3.11.2
SPI驱动: ✅ 已加载
墨水屏: Waveshare 3.52" (240x360)
```

### 网络状态
```
API服务器: ✅ 在线
地址: http://8.134.202.27:8000
IP地址: 192.168.0.5
```

---

## 🔄 运行机制

### 1. 服务启动（开机自启）

**systemd集成**:
- 服务文件: `/etc/systemd/system/ai-rss-client.service`
- 启动命令:
  ```bash
  /usr/bin/python3 /home/admin/Github/AI-RSS-Client/main.py run \
    --base-url http://8.134.202.27:8000
  ```
- 自动重启: 失败后10秒自动重启
- 开机自启: ✅ 已启用（`systemctl enabled ai-rss-client`）

**启动流程**:
1. 系统启动 → systemd自动启动服务
2. 加载配置文件 `config.yml`
3. 初始化SQLite缓存 (`data/articles.db`)
4. 连接墨水屏硬件（SPI驱动）
5. 启动显示调度循环
6. 后台运行，无需人工干预

### 2. 内容获取机制（每20分钟）

**获取策略**:
```
间隔: 20分钟
每次获取: 最多200篇
时间范围: 近3天
每日上限: 1000篇
本地缓存: 最多1000篇
```

**工作流程**:
```python
# 每20分钟自动执行
1. 检查API连接（http://8.134.202.27:8000）
2. 请求获取近3天文章
   - GET /api/articles?days=3&limit=200
3. 解析响应（JSON格式）
4. 写入SQLite数据库
   - 插入新文章
   - 更新已存在文章
5. 备份到JSON（data/offline_cache.json）
6. 记录日志（获取数量、成功/失败）
```

**当前缓存**:
- 数据库文件: `data/articles.db`
- JSON备份: `data/offline_cache.json`
- 文章总数: 186篇
- 覆盖天数: 4天

### 3. 显示调度机制（每30秒）

**显示配置**:
```
切换间隔: 30秒（0.5分钟）
文章池: 近3天文章（186篇）
循环方式: 轮询（FIFO）
循环周期: 约93分钟（186篇 × 30秒）
```

**轮换策略**:
```python
# 文章选择优先级
1. 优先选择从未显示的文章（displayed_at IS NULL）
2. 如果所有文章都显示过，选择最久未显示的（displayed_at ASC）
3. 显示后更新 displayed_at 时间戳
4. 实现真正的FIFO轮询队列
```

**显示流程**:
```python
每30秒执行一次：
1. 从缓存选择一篇未显示文章
2. 调用渲染器生成图像（240×360像素）
   - 绘制Header（时间+天气）
   - 绘制标题（14pt，2行）
   - 绘制中文摘要（14pt，精简）
   - 绘制英文摘要（13pt，10行）
   - 绘制Footer（时间+IP）
3. 通过SPI发送到墨水屏
4. 刷新墨水屏显示（约3秒）
5. 更新文章显示时间戳
6. 等待30秒后重复
```

**日志示例**:
```
15:50:51 - Selected article: US attack on Venezuela (Never)
15:50:51 - Rendering article...
15:50:54 - ✅ 图像已显示至墨水屏
15:50:54 - Display updated successfully (cycle #69)
15:50:54 - Next update in 26 seconds
```

### 4. 硬件驱动机制

**墨水屏型号**: Waveshare 3.52" E-Paper (240×360)

**初始化流程**:
```python
1. 加载SPI驱动（树莓派GPIO）
2. 复位墨水屏硬件
3. 发送初始化命令序列
4. 设置显示参数（分辨率、温度等）
5. 准备接收图像数据
```

**显示流程**:
```python
1. 生成1位黑白图像（PIL.Image）
2. 转换为字节数组
3. 通过SPI发送到墨水屏
4. 触发刷新命令（3-5秒完成）
5. 墨水屏保持显示（断电不丢失）
```

**电源管理**:
- 刷新时: ~50mA（持续3秒）
- 待机时: <1mA（几乎不耗电）
- 断电保持: 图像永久保留（电子墨水特性）

---

## 🎛️ 服务管理

### 使用管理脚本

**位置**: `/home/admin/Github/AI-RSS-Client/manage_service.sh`

**常用命令**:
```bash
# 查看服务状态
./manage_service.sh status

# 查看系统信息
./manage_service.sh info

# 重启服务
./manage_service.sh restart

# 停止服务
./manage_service.sh stop

# 启动服务
./manage_service.sh start

# 查看日志（最近30行）
./manage_service.sh logs

# 手动获取文章
./manage_service.sh fetch

# 测试显示
./manage_service.sh test

# 禁用开机自启
./manage_service.sh disable

# 启用开机自启
./manage_service.sh enable
```

### 使用systemctl

```bash
# 查看服务状态
systemctl status ai-rss-client

# 启动服务
systemctl start ai-rss-client

# 停止服务
systemctl stop ai-rss-client

# 重启服务
systemctl restart ai-rss-client

# 查看实时日志
journalctl -u ai-rss-client -f

# 查看最近日志
journalctl -u ai-rss-client --since "10 minutes ago"

# 禁用开机自启
systemctl disable ai-rss-client

# 启用开机自启
systemctl enable ai-rss-client
```

---

## 📂 目录结构

```
/home/admin/Github/AI-RSS-Client/
├── main.py                      # 主程序入口
├── config.yml                   # 配置文件
├── manage_service.sh            # 服务管理脚本
├── systemd/
│   └── ai-rss-client.service   # systemd服务文件
├── src/                         # 源代码
│   ├── config.py               # 配置管理
│   ├── display/                # 显示模块
│   │   ├── epaper_driver.py   # 墨水屏驱动
│   │   ├── renderer.py        # 内容渲染器
│   │   ├── fonts.py           # 字体管理
│   │   └── layout_engine.py   # 排版引擎
│   ├── services/               # 服务模块
│   │   ├── content_manager.py # 内容管理
│   │   └── display_scheduler.py # 显示调度
│   ├── processors/             # 数据处理
│   │   └── cache.py           # 缓存管理
│   └── fetchers/              # API客户端
├── data/                       # 数据目录
│   ├── articles.db            # SQLite缓存（186篇）
│   ├── offline_cache.json     # JSON备份
│   └── logs/
│       └── service.log        # 运行日志
└── docs/                       # 文档
    ├── CACHE_OPTIMIZATION.md   # 缓存优化报告
    └── FINAL_TEST_REPORT.md    # 最终测试报告
```

---

## 🔧 配置文件

**位置**: `config.yml`

**关键配置**:
```yaml
# API服务器配置
api:
  base_url: "http://8.134.202.27:8000"

# 内容获取配置
services:
  interval_minutes: 20              # 每20分钟获取一次
  max_articles_per_fetch: 200       # 每次最多200篇
  fetch_days: 3                     # 获取近3天
  max_cached_articles: 1000         # 本地最多1000篇

# 显示调度配置
display_scheduler:
  interval_minutes: 0.5             # 30秒切换
  display_days: 3                   # 循环近3天文章
  mark_as_read_after_display: false # 支持循环播放

# 墨水屏配置
display:
  width: 240
  height: 360
  font_file: "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
```

---

## 📡 网络通信

### API请求

**获取文章**:
```bash
GET http://8.134.202.27:8000/api/articles?days=3&limit=200

# 响应（JSON）
[
  {
    "id": 1,
    "title": "文章标题",
    "summary": "中文摘要",
    "summary_en": "English summary",
    "published_at": "2026-01-05T10:30:00",
    ...
  },
  ...
]
```

**天气请求**:
```bash
GET https://wttr.in/Guangzhou?format=j1

# 每10分钟缓存一次，避免频繁请求
```

### 离线支持

**完全离线可用**:
- 本地缓存186篇文章
- 即使断网，墨水屏持续循环播放
- 网络恢复后自动获取新文章

---

## 🔍 日志监控

### 服务日志

**位置**:
- 系统日志: `journalctl -u ai-rss-client`
- 文件日志: `data/logs/service.log`

**关键日志信息**:
```log
# 内容获取
INFO:src.services.content_manager:Fetching articles (limit=200, days=3)
INFO:src.fetchers.api_client:Fetched 186 articles (185 with summaries)
INFO:src.processors.cache:Added 186/186 articles to cache

# 显示调度
INFO:src.services.content_manager:Selected article: xxx (Never)
INFO:src.services.display_scheduler:Rendering article...
INFO:src.display.epaper_driver:✅ 图像已显示至墨水屏
INFO:src.services.display_scheduler:Display updated successfully (cycle #69)

# 错误日志
ERROR:src.services.content_manager:API connection failed
WARNING:src.display.renderer:获取天气失败
```

### 监控命令

```bash
# 实时查看日志
./manage_service.sh logs

# 或使用journalctl
journalctl -u ai-rss-client -f

# 查看最近100条
journalctl -u ai-rss-client -n 100

# 查看今天的日志
journalctl -u ai-rss-client --since today

# 查看错误日志
journalctl -u ai-rss-client -p err
```

---

## ⚡ 性能指标

### 系统资源

```
CPU使用:
  - 刷新时: 高（持续3秒，SPI通信）
  - 平时: 低（等待30秒）

内存使用:
  - 当前: 50.2 MB
  - 峰值: ~60 MB（渲染时）
  - 评估: 良好（树莓派4有4GB内存）

磁盘IO:
  - 读: 偶尔（读取缓存）
  - 写: 每20分钟（更新缓存）
```

### 显示性能

```
切换间隔: 30秒（精确）
渲染时间: ~3秒
刷新时间: ~3秒
总周期: 30秒（渲染3秒 + 等待27秒）
```

### 网络性能

```
API获取:
  - 频率: 每20分钟
  - 数据量: ~500KB/次（200篇）
  - 超时: 10秒
  - 重试: 3次

天气获取:
  - 频率: 每10分钟
  - 数据量: ~10KB/次
  - 缓存: 10分钟
```

---

## 🛠️ 故障排查

### 常见问题

**1. 文章不更新**
```bash
# 检查API连接
curl http://8.134.202.27:8000/api/health

# 手动触发获取
./manage_service.sh fetch

# 查看错误日志
journalctl -u ai-rss-client -p err -n 50
```

**2. 墨水屏不显示**
```bash
# 检查SPI驱动
lsmod | grep spi

# 测试显示
./manage_service.sh test

# 重启服务
./manage_service.sh restart
```

**3. 服务未运行**
```bash
# 查看服务状态
systemctl status ai-rss-client

# 启动服务
systemctl start ai-rss-client

# 查看启动失败原因
journalctl -u ai-rss-client -n 50
```

**4. 内存占用过高**
```bash
# 清理旧文章
sqlite3 data/articles.db "DELETE FROM articles WHERE published_at < date('now', '-7 days')"

# 优化数据库
sqlite3 data/articles.db "VACUUM"

# 重启服务
./manage_service.sh restart
```

---

## 📈 运行统计

### 当前统计

```
运行时间: 34分钟
显示循环: 69次
平均间隔: 30秒
显示文章: 69篇（不重复）
剩余文章: 117篇
```

### 预估统计

```
每日显示: 2,880篇（24小时 × 60分钟 ÷ 0.5分钟）
实际文章: 186篇（循环15次/天）
网络获取: 72次/天（20分钟/次）
数据流量: ~36MB/天
```

---

## 🎯 总结

### 核心特点

1. **完全自动化**
   - 开机自启（systemd）
   - 自动获取内容（20分钟）
   - 自动切换显示（30秒）
   - 自动重启（失败后）

2. **低功耗运行**
   - 墨水屏待机 <1mA
   - CPU平时低负载
   - 仅刷新时短时高耗电

3. **离线可用**
   - 本地缓存186篇
   - 断网不影响显示
   - 恢复后自动同步

4. **稳定可靠**
   - systemd守护进程
   - 自动重启机制
   - 日志完整记录

### 运行方式总结

```
开机 → systemd启动服务 → 连接API → 获取文章 → 缓存到本地
                                              ↓
                    每30秒选择文章 → 渲染图像 → 刷新墨水屏 → 更新时间戳 → 循环
```

---

**文档更新时间**: 2026-01-05 15:52
**项目状态**: 🟢 运行正常
**维护人员**: admin@raspberrypi
