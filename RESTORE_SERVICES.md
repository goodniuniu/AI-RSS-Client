# 墨水屏服务恢复指南

本文档说明如何恢复已暂停的墨水屏相关服务。

## 服务概述

系统中安装了三个墨水屏相关的 systemd 服务：

1. **ai-news-content-fetch.service** - AI 新闻内容获取服务
2. **ai-news-display-scheduler.service** - AI 新闻显示调度服务
3. **weather-poetry-display.service** - 天气与诗词墨水屏显示服务

## 当前状态

所有服务已暂停，状态如下：

```
ai-news-content-fetch.service:       inactive (dead)
ai-news-display-scheduler.service:   inactive (dead)
weather-poetry-display.service:      inactive (dead)
```

GPIO 和 SPI 资源已释放，可以用于测试新的墨水屏程序。

---

## 方法1：快速恢复（推荐）

### 一键恢复所有服务

```bash
sudo systemctl start ai-news-content-fetch.service \
                    ai-news-display-scheduler.service \
                    weather-poetry-display.service
```

### 验证服务状态

```bash
sudo systemctl status ai-news-content-fetch.service \
                    ai-news-display-scheduler.service \
                    weather-poetry-display.service
```

**预期输出：** 所有服务应显示 `active (running)` 状态。

---

## 方法2：单独恢复服务

### 选项 A：仅恢复天气诗词显示

```bash
sudo systemctl start weather-poetry-display.service
```

### 选项 B：仅恢复 AI 新闻显示

```bash
# 启动内容获取服务
sudo systemctl start ai-news-content-fetch.service

# 启动显示调度服务
sudo systemctl start ai-news-display-scheduler.service
```

### 选项 C：恢复全部（方法1的详细版本）

```bash
# 1. 启动天气诗词显示
sudo systemctl start weather-poetry-display.service
sleep 2

# 2. 启动 AI 新闻内容获取
sudo systemctl start ai-news-content-fetch.service
sleep 2

# 3. 启动 AI 新闻显示调度
sudo systemctl start ai-news-display-scheduler.service
```

---

## 方法3：启用并恢复（如果需要开机自启）

如果之前禁用了服务，需要重新启用：

```bash
# 启用服务（开机自启）
sudo systemctl enable ai-news-display-scheduler.service \
                     weather-poetry-display.service

# 启动服务
sudo systemctl start ai-news-content-fetch.service \
                    ai-news-display-scheduler.service \
                    weather-poetry-display.service
```

---

## 验证恢复结果

### 1. 检查服务状态

```bash
sudo systemctl status ai-news-content-fetch.service \
                    ai-news-display-scheduler.service \
                    weather-poetry-display.service
```

**预期结果：**
- `Active: active (running)`
- `Loaded: loaded (/etc/systemd/system/...)`
- 没有 `failed` 或 `inactive (dead)` 状态

### 2. 检查墨水屏更新

墨水屏应该会在服务启动后的 1-2 分钟内开始显示内容：

- **天气诗词服务**：约每 5 分钟更新一次
- **AI 新闻服务**：约每 1 分钟检查一次更新

### 3. 查看服务日志

如果需要确认服务是否正常工作：

```bash
# 查看天气诗词服务日志
sudo journalctl -u weather-poetry-display.service -f

# 查看 AI 新闻显示调度日志
sudo journalctl -u ai-news-display-scheduler.service -f

# 查看 AI 新闻内容获取日志
sudo journalctl -u ai-news-content-fetch.service -f
```

按 `Ctrl+C` 退出日志查看。

---

## 常见问题排查

### 问题1：服务启动失败

**检查方法：**
```bash
sudo systemctl status <service-name>.service
```

**常见原因和解决方案：**

1. **端口被占用**
   ```bash
   # 查找占用进程
   sudo ps aux | grep python | grep -E "weather|news|epaper"

   # 停止占用进程
   sudo kill -9 <PID>
   ```

2. **GPIO 资源被占用**
   ```bash
   # 停止测试程序
   sudo pkill -9 test_epaper

   # 重新启动服务
   sudo systemctl start <service-name>.service
   ```

3. **配置文件错误**
   ```bash
   # 检查服务配置
   sudo systemd-analyze verify <service-name>.service

   # 重新加载 systemd 配置
   sudo systemctl daemon-reload
   ```

### 问题2：墨水屏没有显示

**可能原因：**

1. **服务未正常启动**
   ```bash
   sudo systemctl status ai-news-display-scheduler.service
   ```

2. **测试程序仍在运行**
   ```bash
   # 查找并停止测试程序
   sudo ps aux | grep test_epaper
   sudo kill -9 <PID>
   ```

3. **SPI 未启用**
   ```bash
   # 检查 SPI 设备
   ls -la /dev/spidev*

   # 如果没有设备，运行 raspi-config 启用 SPI
   sudo raspi-config
   # 选择: Interface Options -> SPI -> Yes
   ```

### 问题3：服务频繁重启

**检查日志查看错误：**
```bash
sudo journalctl -u <service-name>.service -n 50
```

**常见解决方案：**
1. 检查 Python 代码是否有语法错误
2. 确认依赖包已安装
3. 检查文件权限

---

## 服务管理命令参考

### 基本命令

```bash
# 启动服务
sudo systemctl start <service-name>.service

# 停止服务
sudo systemctl stop <service-name>.service

# 重启服务
sudo systemctl restart <service-name>.service

# 查看状态
sudo systemctl status <service-name>.service

# 启用开机自启
sudo systemctl enable <service-name>.service

# 禁用开机自启
sudo systemctl disable <service-name>.service
```

### 批量操作

```bash
# 停止所有墨水屏服务
sudo systemctl stop ai-news-* weather-poetry-display.service

# 启动所有墨水屏服务
sudo systemctl start ai-news-* weather-poetry-display.service

# 重启所有墨水屏服务
sudo systemctl restart ai-news-* weather-poetry-display.service

# 查看所有墨水屏服务状态
sudo systemctl status ai-news-* weather-poetry-display.service
```

---

## 服务文件位置

服务配置文件位于：
```
/etc/systemd/system/ai-news-content-fetch.service
/etc/systemd/system/ai-news-display-scheduler.service
/etc/systemd/system/weather-poetry-display.service
```

项目代码位于：
```
/home/admin/Github/epaper-with-ai-news/
/home/admin/Github/epaper-with-raspberrypi/
```

---

## 恢复时间参考

| 操作 | 预期时间 |
|------|---------|
| 服务启动 | 2-5 秒 |
| 墨水屏首次显示 | 10-30 秒 |
| 定期更新间隔 | 1-5 分钟 |

---

## 联系信息

如果遇到恢复问题，请检查：

1. **服务日志**：`sudo journalctl -u <service-name> -n 100`
2. **系统日志**：`sudo journalctl -xe`
3. **GPIO 状态**：`ls -la /sys/class/gpio/`
4. **SPI 设备**：`ls -la /dev/spidev*`

---

## 快速参考卡片

### 立即恢复所有服务
```bash
sudo systemctl start ai-news-content-fetch.service \
                    ai-news-display-scheduler.service \
                    weather-poetry-display.service
```

### 验证服务运行
```bash
sudo systemctl status ai-news-content-fetch.service \
                    ai-news-display-scheduler.service \
                    weather-poetry-display.service | grep Active
```

### 查看实时日志
```bash
sudo journalctl -u ai-news-display-scheduler.service -f
```

---

**文档创建时间：** 2025-12-26 14:49
**服务暂停时间：** 2025-12-26 14:49
**适用系统：** Raspberry Pi OS (aarch64)
