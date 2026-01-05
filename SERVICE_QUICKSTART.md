# AI-RSS-Client 服务管理 - 快速开始

## ✅ 服务已安装并运行

```bash
服务名称: ai-rss-client
状态: ✅ 运行中
开机自启: ✅ 已启用
```

## 🎮 快速命令

### 查看服务状态
```bash
./manage_service.sh status
# 或
./manage_service.sh info
```

### 启动/停止/重启
```bash
./manage_service.sh start    # 启动
./manage_service.sh stop     # 停止
./manage_service.sh restart  # 重启
```

### 查看日志
```bash
./manage_service.sh logs     # 实时日志（Ctrl+C 退出）
./manage_service.sh all-logs # 所有日志
```

### 获取新文章
```bash
./manage_service.sh fetch
```

### 测试墨水屏
```bash
./manage_service.sh test
```

## 📋 交互式菜单

```bash
./manage_service.sh
```

然后使用数字选择操作：
- 1) Status - 查看状态
- 2) Start - 启动
- 3) Stop - 停止
- 4) Restart - 重启
- 5) Logs - 查看日志
- 11) Fetch News - 获取新闻
- 12) Test Display - 测试显示
- 13) System Info - 系统信息
- 0) Exit - 退出

## 🔄 服务特点

✅ **开机自启** - 系统启动后自动运行
✅ **自动重启** - 崩溃后10秒自动重启
✅ **日志管理** - 统一由 systemd 管理
✅ **便捷管理** - 提供友好的管理脚本

## 📖 更多信息

详细文档：[docs/SERVICE_MANAGEMENT.md](docs/SERVICE_MANAGEMENT.md)
