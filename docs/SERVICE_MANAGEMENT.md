# AI-RSS-Client 服务管理指南

## 📋 概述

AI-RSS-Client 已配置为 systemd 系统服务，支持开机自启和自动重启。

## 🚀 快速开始

### 使用管理脚本（推荐）

```bash
# 进入项目目录
cd /home/admin/Github/AI-RSS-Client

# 运行管理脚本（交互式菜单）
./manage_service.sh

# 或使用命令行参数
./manage_service.sh status    # 查看状态
./manage_service.sh start     # 启动服务
./manage_service.sh stop      # 停止服务
./manage_service.sh restart   # 重启服务
```

### 直接使用 systemctl 命令

```bash
# 查看服务状态
sudo systemctl status ai-rss-client

# 启动服务
sudo systemctl start ai-rss-client

# 停止服务
sudo systemctl stop ai-rss-client

# 重启服务
sudo systemctl restart ai-rss-client

# 查看日志
sudo journalctl -u ai-rss-client -f

# 查看所有日志
sudo journalctl -u ai-rss-client --no-pager | less
```

## 📊 服务状态说明

### 服务已安装并启用

```
Service:
   Status: ✅ Installed
   Running: ✅ Yes
   Auto-start: ✅ Enabled
```

这意味着：
- ✅ 服务已安装到 systemd
- ✅ 服务正在运行
- ✅ 开机自动启动
- ✅ 崩溃后自动重启

## 🎮 管理脚本功能

### 交互式菜单选项

运行 `./manage_service.sh` 进入交互式菜单：

```
1) Status        - 查看服务状态
2) Start         - 启动服务
3) Stop          - 停止服务
4) Restart       - 重启服务
5) Logs          - 查看实时日志
6) All Logs      - 查看所有日志
7) Enable        - 启用开机自启
8) Disable       - 禁用开机自启
9) Install       - 安装服务到 systemd
10) Uninstall     - 从 systemd 卸载服务
11) Fetch News    - 从 API 获取新文章
12) Test Display  - 测试墨水屏显示
13) System Info   - 显示系统信息
0) Exit          - 退出菜单
```

### 命令行模式

```bash
# 查看状态
./manage_service.sh status

# 启动服务
./manage_service.sh start

# 停止服务
./manage_service.sh stop

# 重启服务
./manage_service.sh restart

# 查看实时日志（Ctrl+C 退出）
./manage_service.sh logs

# 查看所有日志
./manage_service.sh all-logs

# 启用开机自启
./manage_service.sh enable

# 禁用开机自启
./manage_service.sh disable

# 安装服务
./manage_service.sh install

# 卸载服务
./manage_service.sh uninstall

# 获取新闻
./manage_service.sh fetch

# 测试显示
./manage_service.sh test

# 系统信息
./manage_service.sh info
```

## 📝 日志查看

### systemd 日志（推荐）

服务安装后，所有日志都由 journald 管理：

```bash
# 实时查看日志
sudo journalctl -u ai-rss-client -f

# 查看最近 100 行日志
sudo journalctl -u ai-rss-client -n 100

# 查看今天的日志
sudo journalctl -u ai-rss-client --since today

# 查看所有日志
sudo journalctl -u ai-rss-client --no-pager | less
```

### 传统日志文件（备用）

如果服务以手动方式运行，日志会写入：

```bash
# 查看手动运行的日志
tail -f /tmp/ai-rss-client-30s.log
```

## 🔧 故障排查

### 服务无法启动

1. **检查服务状态**
   ```bash
   ./manage_service.sh status
   ```

2. **查看错误日志**
   ```bash
   ./manage_service.sh all-logs
   ```

3. **检查端口占用**
   ```bash
   sudo systemctl stop ai-rss-client
   ps aux | grep "main.py run"
   ```

### 墨水屏不显示

1. **检查 SPI 驱动**
   ```bash
   lsmod | grep spi
   ```

2. **测试显示**
   ```bash
   ./manage_service.sh test
   ```

3. **查看日志中的错误**
   ```bash
   sudo journalctl -u ai-rss-client -n 50 | grep -i error
   ```

### 文章不更新

1. **检查网络连接**
   ```bash
   ping -c 3 8.134.202.27
   ```

2. **手动获取文章**
   ```bash
   ./manage_service.sh fetch
   ```

3. **查看文章数量**
   ```bash
   ./manage_service.sh info
   ```

## 🎯 日常维护

### 定期获取新文章

建议每天运行一次：

```bash
./manage_service.sh fetch
```

或设置 cron 定时任务：

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 3 点获取新闻
0 3 * * * cd /home/admin/Github/AI-RSS-Client && ./manage_service.sh fetch >> /var/log/ai-rss-fetch.log 2>&1
```

### 重启服务

如果遇到问题，可以重启服务：

```bash
./manage_service.sh restart
```

### 查看系统状态

定期检查服务状态：

```bash
./manage_service.sh info
```

输出示例：
```
System Information:
Service:
   Status: ✅ Installed
   Running: ✅ Yes
   Auto-start: ✅ Enabled

Process:
   PID: 303815
   Uptime: 00:17
   Memory: 45.8 MB

Articles:
   Total: 50
   Undisplayed: 11
   Date range: 2026-01-04|2026-01-04

Hardware:
   Python: Python 3.11.2
   SPI: ✅ Loaded

Network:
   API Server: ✅ Online
```

## 🔄 更新服务

### 修改代码后重启

```bash
# 1. 拉取最新代码
git pull

# 2. 重启服务应用更改
./manage_service.sh restart

# 3. 查看状态确认
./manage_service.sh status
```

### 修改配置文件

配置文件：`config.yml`

```bash
# 1. 编辑配置
vim config.yml

# 2. 重启服务
./manage_service.sh restart

# 3. 查看日志确认
./manage_service.sh logs
```

## 📂 文件位置

### systemd 配置

- **Service 文件**: `/etc/systemd/system/ai-rss-client.service`
- **源文件**: `systemd/ai-rss-client.service`

### 数据文件

- **数据库**: `data/articles.db`
- **日志文件**: `/tmp/ai-rss-client-30s.log`（手动运行时）
- **systemd 日志**: `journald`（服务运行时）

### 项目目录

- **项目根目录**: `/home/admin/Github/AI-RSS-Client`
- **管理脚本**: `/home/admin/Github/AI-RSS-Client/manage_service.sh`

## 🔐 权限说明

### 需要 sudo 的操作

- 安装/卸载服务
- 启动/停止服务
- 启用/禁用开机自启
- 查看 systemd 日志

### 不需要 sudo 的操作

- 查看服务状态（简化版）
- 获取新闻
- 测试显示
- 查看系统信息

## 🚨 应急处理

### 停止服务

```bash
./manage_service.sh stop
```

### 完全重置服务

```bash
# 1. 停止并禁用服务
./manage_service.sh disable
./manage_service.sh stop

# 2. 卸载服务
./manage_service.sh uninstall

# 3. 重新安装
./manage_service.sh install
./manage_service.sh start
```

### 手动运行（调试模式）

```bash
# 停止服务
./manage_service.sh stop

# 手动运行（查看详细输出）
cd /home/admin/Github/AI-RSS-Client
python3 main.py run --base-url http://8.134.202.27:8000
```

## 📞 获取帮助

### 查看服务管理脚本帮助

```bash
./manage_service.sh
# 将显示交互式菜单
```

### 查看 systemctl 帮助

```bash
systemctl --help
man systemctl
```

## ✅ 最佳实践

1. **使用管理脚本**：优先使用 `manage_service.sh` 而不是直接 systemctl
2. **定期检查状态**：使用 `./manage_service.sh info` 查看系统状态
3. **查看日志**：遇到问题时先查看日志 `./manage_service.sh logs`
4. **定期获取新闻**：建议每天运行 `./manage_service.sh fetch`
5. **保持更新**：定期更新代码并重启服务

## 🎉 总结

AI-RSS-Client 现在已完全集成到 systemd 系统服务中：

- ✅ 开机自启
- ✅ 自动重启（崩溃后）
- ✅ 统一日志管理
- ✅ 便捷的管理脚本
- ✅ 完整的系统集成

使用 `./manage_service.sh` 轻松管理所有服务功能！
