# 墨水屏显示控制指南

## ✅ 验证完成

已确认可以**完全掌控**墨水屏显示。

**最新更新 (2025-12-26 16:35):**
- ✅ 主驱动已更新，内置完整的初始化序列
- ✅ 无需手动调用 `display_NUM()`, `lut_GC()`, `refresh()`
- ✅ 所有测试脚本现在都能正常更新屏幕

## 🎮 显示控制命令

### 1. 项目信息显示

```bash
sudo venv/bin/python tests/test_simple_display.py
```

**显示内容：**
- 标题：AI-RSS Client
- 项目状态：Ready, Driver Working, GPIO Controlled
- 阶段：Phase 1 Complete, Ready for Phase 2
- 更新时间

### 2. 测试图案显示

```bash
sudo venv/bin/python tests/test_driver.py --test basic
```

**显示内容：**
- 黑色边框
- 对角线 X 图案
- 标题：E-Paper Test
- 分辨率信息和时间

### 3. Mock 模式测试（仅生成图像）

```bash
# 当服务运行时使用
venv/bin/python tests/test_driver.py --test basic
```

生成调试图像：`data/debug_current_view.png`

---

## 📊 控制状态验证

### 当前资源状态

```
✅ GPIO: 已释放并可用
✅ SPI: 已释放并可用
✅ Systemd 服务: 已停止并禁用
✅ Crontab 任务: 已注释
✅ Python 进程: 无墨水屏进程运行
```

### 验证命令

```bash
# 检查服务状态
sudo systemctl status ai-news-* weather-poetry-display.service | grep Active

# 检查进程
ps aux | grep -E "epaper|weather|display" | grep -v grep

# 检查 GPIO 占用
sudo lsof | grep -E "spidev|gpiomem"
```

---

## 🔄 显示更新流程

### 标准流程

```bash
# 1. 停止所有墨水屏服务（如果运行中）
sudo systemctl stop ai-news-* weather-poetry-display.service

# 2. 运行显示脚本
sudo venv/bin/python tests/test_simple_display.py

# 3. 查看墨水屏确认更新
# （墨水屏会立即刷新显示新内容）
```

### 快速更新

```bash
# 一条命令更新显示
sudo venv/bin/python tests/test_simple_display.py
```

---

## 🎨 自定义显示内容

### 方法1：修改现有脚本

编辑 `tests/test_simple_display.py`，修改绘制内容：

```python
# 修改这些行来显示自定义内容
title = "Your Title"
info = [
    "Line 1",
    "Line 2",
    "Line 3"
]
```

### 方法2：创建新脚本

基于 `tests/test_simple_display.py` 创建新的显示脚本：

```python
#!/usr/bin/env python3
"""自定义显示"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import Config, setup_logging
from display.epaper_driver import create_driver
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    cfg = Config("config.yml")
    setup_logging(cfg)

    driver = create_driver()
    driver.init_display()

    # 创建图像
    img = Image.new('1', (240, 360), 255)
    draw = ImageDraw.Draw(img)

    # 绘制内容
    draw.rectangle([10, 10, 230, 350], outline=0, width=2)
    draw.text((20, 50), "Your Content", font=font, fill=0)

    # 显示
    driver.display_image(img)
    driver.sleep()

if __name__ == "__main__":
    main()
```

---

## 🔧 故障排查

### 如果墨水屏不更新

```bash
# 1. 检查是否有其他进程占用
ps aux | grep -E "python.*epaper|python.*weather"

# 2. 停止所有服务
sudo systemctl stop ai-news-* weather-poetry-display.service

# 3. 检查 GPIO
sudo lsof | grep -E "spidev|gpiomem"

# 4. 重新运行显示脚本
sudo venv/bin/python tests/test_simple_display.py
```

### 如果显示错误内容

可能是之前的程序还在运行，确保：

```bash
# 停止所有服务
sudo systemctl stop ai-news-* weather-poetry-display.service

# 等待几秒
sleep 3

# 运行你的显示脚本
sudo venv/bin/python tests/test_simple_display.py
```

---

## 📝 恢复原有服务

当开发测试完成后，恢复原有服务：

```bash
# 启用服务
sudo systemctl enable ai-news-display-scheduler.service
sudo systemctl enable weather-poetry-display.service

# 启动服务
sudo systemctl start ai-news-content-fetch.service
sudo systemctl start ai-news-display-scheduler.service
sudo systemctl start weather-poetry-display.service

# 验证状态
sudo systemctl status ai-news-display-scheduler.service
```

原有服务会恢复显示：
- 天气诗词（每5分钟更新）
- AI 新闻（根据配置更新）

---

## 🎯 最佳实践

### 开发期间

1. **保持服务停止**
   ```bash
   sudo systemctl stop ai-news-* weather-poetry-display.service
   ```

2. **使用测试脚本验证**
   ```bash
   sudo venv/bin/python tests/test_simple_display.py
   ```

3. **检查日志确认**
   ```bash
   tail -f data/logs/service.log
   ```

### 生产环境

1. **使用 systemd 管理服务**
   - 不要使用 crontab
   - 利用 systemd 的自动重启

2. **监控服务状态**
   ```bash
   sudo systemctl status ai-news-display-scheduler.service
   sudo journalctl -u ai-news-display-scheduler.service -f
   ```

3. **定期检查 GPIO 占用**
   ```bash
   sudo lsof | grep -E "spidev|gpiomem"
   ```

---

**最后更新:** 2025-12-26 16:14
**控制状态:** ✅ 完全掌控
**显示模式:** 硬件直接驱动
