# AI-RSS-Client 服务架构重构说明

## 📋 概述

AI-RSS-Client已重构为**双服务架构**：
- **ContentFetchService** - 独立的内容获取服务
- **DisplayService** - 独立的显示服务

两个服务完全独立运行，可以单独启动、停止、重启和监控。

## 🏗️ 架构设计

### 核心理念
- **main.py** = 轻量级启动入口，根据命令启动对应服务
- **Service类** = 核心业务逻辑，各自独立运行
- **职责分离** = 每个Service只负责自己的业务

### 文件结构
```
src/services/
├── content_fetch_service.py   # 内容获取服务（新增）
├── display_service.py          # 显示服务（新增）
├── content_manager.py          # 内容管理器（保留）
└── display_scheduler.py        # 显示调度器（保留）

systemd/
├── ai-rss-client-fetch.service    # 内容获取服务配置
├── ai-rss-client-display.service  # 显示服务配置
└── ai-rss-client.service          # 旧版本（已弃用）
```

## 🚀 使用方法

### 命令行使用

#### 1. 内容获取服务

**手动获取一次（测试用）：**
```bash
python3 main.py fetch --base-url http://8.134.202.27:8000
```

**启动内容获取守护进程（每20分钟获取一次）：**
```bash
python3 main.py fetch-daemon --base-url http://8.134.202.27:8000
```

**运行指定次数：**
```bash
python3 main.py fetch-daemon --cycles 3  # 只获取3次后退出
```

#### 2. 显示服务

**启动显示服务（每30秒更新一次）：**
```bash
python3 main.py run --base-url http://8.134.202.27:8000
# 或使用完整命令名
python3 main.py display-daemon --base-url http://8.134.202.27:8000
```

**自定义显示间隔：**
```bash
python3 main.py run --interval 1.0  # 每1分钟更新一次
```

**运行指定次数：**
```bash
python3 main.py run --cycles 5  # 只显示5次后退出
```

**测试显示硬件：**
```bash
python3 main.py test-display --base-url http://8.134.202.27:8000
```

#### 3. 其他命令

**测试API连接：**
```bash
python3 main.py test-api --base-url http://8.134.202.27:8000
```

**查看系统状态：**
```bash
python3 main.py status --base-url http://8.134.202.27:8000
```

### Systemd服务使用

#### 安装服务

**停止并卸载旧服务（如果存在）：**
```bash
./manage_service.sh stop
./manage_service.sh uninstall
```

**安装新服务：**
```bash
# 安装内容获取服务
sudo cp systemd/ai-rss-client-fetch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-rss-client-fetch

# 安装显示服务
sudo cp systemd/ai-rss-client-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-rss-client-display
```

#### 管理服务

**内容获取服务：**
```bash
# 启动
sudo systemctl start ai-rss-client-fetch

# 停止
sudo systemctl stop ai-rss-client-fetch

# 重启
sudo systemctl restart ai-rss-client-fetch

# 查看状态
sudo systemctl status ai-rss-client-fetch

# 查看日志
sudo journalctl -u ai-rss-client-fetch -f

# 开机自启
sudo systemctl enable ai-rss-client-fetch

# 禁用开机自启
sudo systemctl disable ai-rss-client-fetch
```

**显示服务：**
```bash
# 启动
sudo systemctl start ai-rss-client-display

# 停止
sudo systemctl stop ai-rss-client-display

# 重启
sudo systemctl restart ai-rss-client-display

# 查看状态
sudo systemctl status ai-rss-client-display

# 查看日志
sudo journalctl -u ai-rss-client-display -f

# 开机自启
sudo systemctl enable ai-rss-client-display

# 禁用开机自启
sudo systemctl disable ai-rss-client-display
```

## 📊 配置文件

配置文件 `config.yml` 中的关键参数：

```yaml
services:
  enabled: true
  interval_minutes: 20              # 内容获取间隔（分钟）
  fetch_days: 3                     # 获取近3天的文章

display_scheduler:
  enabled: true
  interval_minutes: 0.5             # 显示更新间隔（30秒）
  display_days: 3                   # 循环播放近3天的文章
```

## 🔍 服务特性

### ContentFetchService

- **职责**：定期从API获取新文章并更新本地缓存
- **运行间隔**：config.yml 中 `services.interval_minutes`（默认20分钟）
- **独立运行**：不依赖显示服务，可单独重启
- **优雅关闭**：支持SIGTERM信号，完成当前获取后退出

### DisplayService

- **职责**：定期从缓存选择文章并更新墨水屏显示
- **运行间隔**：config.yml 中 `display_scheduler.interval_minutes`（默认0.5分钟=30秒）
- **独立运行**：不依赖内容获取服务，即使获取服务停止也能继续显示缓存内容
- **优雅关闭**：支持SIGTERM信号，完成当前显示周期后退出

## ⚠️ 迁移说明

### 从旧版本迁移

如果您正在使用旧的单服务版本（`ai-rss-client.service`），请按以下步骤迁移：

1. **停止旧服务：**
   ```bash
   sudo systemctl stop ai-rss-client
   sudo systemctl disable ai-rss-client
   ```

2. **备份（可选）：**
   ```bash
   sudo cp /etc/systemd/system/ai-rss-client.service ~/ai-rss-client.service.bak
   ```

3. **安装新服务：**
   ```bash
   sudo cp systemd/ai-rss-client-fetch.service /etc/systemd/system/
   sudo cp systemd/ai-rss-client-display.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable ai-rss-client-fetch
   sudo systemctl enable ai-rss-client-display
   ```

4. **启动新服务：**
   ```bash
   sudo systemctl start ai-rss-client-fetch
   sudo systemctl start ai-rss-client-display
   ```

5. **验证状态：**
   ```bash
   sudo systemctl status ai-rss-client-fetch
   sudo systemctl status ai-rss-client-display
   ```

6. **清理旧服务（可选）：**
   ```bash
   sudo rm /etc/systemd/system/ai-rss-client.service
   ```

## 🐛 故障排查

### 问题1：内容获取服务不工作

**检查日志：**
```bash
sudo journalctl -u ai-rss-client-fetch -n 50
```

**可能原因：**
- 网络连接问题
- API服务器不可用
- 配置文件错误

**解决方法：**
```bash
# 测试API连接
python3 main.py test-api --base-url http://8.134.202.27:8000

# 手动触发一次获取
python3 main.py fetch --base-url http://8.134.202.27:8000
```

### 问题2：显示服务不更新

**检查日志：**
```bash
sudo journalctl -u ai-rss-client-display -n 50
```

**可能原因：**
- 缓存中没有新文章
- 硬件初始化失败
- GPIO冲突

**解决方法：**
```bash
# 查看缓存状态
python3 main.py status --base-url http://8.134.202.27:8000

# 测试显示硬件
python3 main.py test-display --base-url http://8.134.202.27:8000

# 手动触发一次显示（测试5个周期）
python3 main.py run --cycles 5 --base-url http://8.134.202.27:8000
```

### 问题3：两个服务都需要重启

**重启内容获取服务：**
```bash
sudo systemctl restart ai-rss-client-fetch
```

**重启显示服务：**
```bash
sudo systemctl restart ai-rss-client-display
```

**或同时重启：**
```bash
sudo systemctl restart ai-rss-client-fetch ai-rss-client-display
```

## 📝 总结

✅ **优点：**
- 两个服务完全独立，互不影响
- 可以单独重启、监控和调试
- 代码结构清晰，易于维护
- 向后兼容，保留原有命令

✅ **推荐配置：**
- ContentFetchService：每20分钟获取一次（可调整）
- DisplayService：每30秒更新一次（可调整）

✅ **最佳实践：**
- 两个服务都设置为开机自启
- 定期检查服务状态和日志
- 使用 `--cycles` 参数进行测试
- 保持配置文件的合理性
